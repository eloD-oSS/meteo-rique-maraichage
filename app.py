import re
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import requests
import streamlit as st


APP_TITLE = "Météo-Risque Maraîchage — Prototype V1"
DEFAULT_EXCEL = Path(__file__).parent / "Tableau_semis_densite_calculateur.xlsx"


st.set_page_config(
    page_title="Météo-Risque Maraîchage",
    page_icon="🌦️",
    layout="wide",
)


def normalize_text(value):
    if pd.isna(value):
        return ""
    return str(value).strip()


def parse_temp_optimum(value):
    """Extrait une plage de température depuis des cellules de type '17–20', '15-20', '20 à 25'."""
    text = normalize_text(value).replace("–", "-").replace("—", "-")
    nums = re.findall(r"-?\d+(?:[,.]\d+)?", text)
    nums = [float(n.replace(",", ".")) for n in nums]
    if len(nums) >= 2:
        return nums[0], nums[1]
    if len(nums) == 1:
        return nums[0], nums[0]
    return None, None


def parse_threshold_number(value, default=None):
    """Extrait le premier nombre d'un texte du type '> 90 % pendant > 12h'."""
    text = normalize_text(value)
    nums = re.findall(r"\d+(?:[,.]\d+)?", text)
    if not nums:
        return default
    return float(nums[0].replace(",", "."))


def parse_duration_hours(value, default=0):
    """Extrait une durée en heures depuis un texte libre."""
    text = normalize_text(value).lower().replace("–", "-")
    nums = re.findall(r"\d+(?:[,.]\d+)?", text)
    if not nums:
        return default
    # Dans '> 90 % pendant > 12h', on veut souvent le 2e nombre.
    if "%" in text and len(nums) >= 2:
        return float(nums[1].replace(",", "."))
    return float(nums[0].replace(",", "."))


@st.cache_data(show_spinner=False)
def load_workbook(uploaded_file=None):
    """Charge les onglets utiles depuis l'Excel existant."""
    source = uploaded_file if uploaded_file is not None else DEFAULT_EXCEL

    clim = pd.read_excel(source, sheet_name="Paramètres climatiques", header=3)
    clim = clim.dropna(how="all")
    clim = clim[~clim["Maladie"].astype(str).str.contains("──", na=False)]
    clim = clim[clim["Maladie"].notna()].copy()

    maladies = pd.read_excel(source, sheet_name="maladies et ravageurs")
    maladies[["Famille", "Espèce"]] = maladies[["Famille", "Espèce"]].ffill()
    maladies = maladies.dropna(subset=["Espèce"], how="all").copy()

    return clim, maladies


def enrich_climate_rules(clim):
    """Ajoute des colonnes calculables sans modifier le fichier source."""
    rules = clim.copy()
    rules["t_opt_min"], rules["t_opt_max"] = zip(*rules["T° optimale (°C)"].map(parse_temp_optimum))
    rules["hr_seuil"] = rules["Humidité critique"].map(lambda x: parse_threshold_number(x, default=85))
    rules["duree_hr_h"] = rules["Humidité critique"].map(lambda x: parse_duration_hours(x, default=6))
    rules["eau_libre_oui"] = rules["Eau libre nécessaire"].astype(str).str.upper().str.contains("OUI|OBLIGATOIRE|RECOMMAND", regex=True)
    return rules


def geocode_city(city):
    """Recherche latitude/longitude via Open-Meteo Geocoding API."""
    url = "https://geocoding-api.open-meteo.com/v1/search"
    params = {"name": city, "count": 5, "language": "fr", "format": "json"}
    response = requests.get(url, params=params, timeout=15)
    response.raise_for_status()
    data = response.json()
    return data.get("results", [])


def fetch_weather(latitude, longitude, past_days=2, forecast_days=7):
    """Récupère météo horaire passée + prévisionnelle via Open-Meteo."""
    url = "https://api.open-meteo.com/v1/forecast"
    hourly = [
        "temperature_2m",
        "relative_humidity_2m",
        "precipitation",
        "rain",
        "dew_point_2m",
        "wind_speed_10m",
    ]
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": ",".join(hourly),
        "past_days": past_days,
        "forecast_days": forecast_days,
        "timezone": "Europe/Paris",
    }
    response = requests.get(url, params=params, timeout=25)
    response.raise_for_status()
    data = response.json()

    hourly_data = pd.DataFrame(data["hourly"])
    hourly_data["time"] = pd.to_datetime(hourly_data["time"])
    return hourly_data


def compute_risk_for_rule(rule, weather_window, culture_mode="Plein champ"):
    """Calcule un score simple et lisible pour une règle maladie."""
    if weather_window.empty:
        return 0, "Pas de données météo"

    temp = weather_window["temperature_2m"]
    hr = weather_window["relative_humidity_2m"]
    rain_sum = weather_window["precipitation"].fillna(0).sum()

    t_min = float(rule["T° min (°C)"]) if pd.notna(rule["T° min (°C)"]) else None
    t_max = float(rule["T° max (°C)"]) if pd.notna(rule["T° max (°C)"]) else None
    opt_min = rule.get("t_opt_min")
    opt_max = rule.get("t_opt_max")
    hr_seuil = rule.get("hr_seuil") or 85

    score = 0
    reasons = []

    temp_mean = temp.mean()
    if t_min is not None and t_max is not None and t_min <= temp_mean <= t_max:
        score += 2
        reasons.append(f"T° moyenne favorable ({temp_mean:.1f} °C)")

    if pd.notna(opt_min) and pd.notna(opt_max) and opt_min <= temp_mean <= opt_max:
        score += 3
        reasons.append(f"T° dans l'optimum ({opt_min:g}–{opt_max:g} °C)")

    hr_hours = int((hr >= hr_seuil).sum())
    if hr_hours > 0:
        score += 2
        reasons.append(f"HR ≥ {hr_seuil:g} % pendant {hr_hours} h")

    duree_seuil = rule.get("duree_hr_h") or 6
    if hr_hours >= duree_seuil:
        score += 3
        reasons.append(f"Durée d'humidité critique atteinte ({hr_hours} h)")

    if rain_sum >= 1:
        score += 2
        reasons.append(f"Pluie cumulée {rain_sum:.1f} mm")

    if bool(rule.get("eau_libre_oui")) and (rain_sum >= 0.2 or hr_hours >= duree_seuil):
        score += 1
        reasons.append("Conditions compatibles avec eau libre / rosée")

    if culture_mode == "Sous abri":
        score += 1
        reasons.append("Sous abri : vigilance condensation/aération")

    if score >= 8:
        risk = "Élevé"
    elif score >= 4:
        risk = "Moyen"
    else:
        risk = "Faible"

    return score, " ; ".join(reasons) if reasons else "Conditions peu favorables"


def recommendations_from_rule(rule, risk):
    base = normalize_text(rule.get("Conditions d'alerte", ""))
    if risk == "Élevé":
        return "Surveillance prioritaire sous 24 h. " + base
    if risk == "Moyen":
        return "Surveillance à programmer. " + base
    return "Pas d'action prioritaire. Maintenir l'observation régulière."


def main():
    st.title("🌦️ Météo-Risque Maraîchage")
    st.caption("Prototype V1 — l'Excel reste le moteur métier, l'application devient l'interface météo/alerte.")

    with st.sidebar:
        st.header("1. Source de données")
        uploaded = st.file_uploader("Charger un autre Excel si besoin", type=["xlsx"])
        st.caption("Par défaut, l'application utilise l'Excel fourni avec le prototype.")

    try:
        clim, maladies = load_workbook(uploaded)
        rules = enrich_climate_rules(clim)
    except Exception as exc:
        st.error(f"Impossible de lire le fichier Excel : {exc}")
        st.stop()

    tab1, tab2, tab3, tab4 = st.tabs([
        "📘 Base Excel",
        "🌱 Cultures suivies",
        "🌦️ Météo",
        "🚨 Risques maladies",
    ])

    with tab1:
        st.subheader("Onglets lus depuis l'Excel")
        col_a, col_b = st.columns(2)
        with col_a:
            st.metric("Règles climatiques", len(rules))
            st.dataframe(rules[[
                "Maladie", "Cultures affectées", "T° min (°C)", "T° optimale (°C)",
                "T° max (°C)", "Humidité critique", "Eau libre nécessaire", "Conditions d'alerte"
            ]], use_container_width=True)
        with col_b:
            st.metric("Lignes maladies/ravageurs", len(maladies))
            st.dataframe(maladies.head(80), use_container_width=True)

    with tab2:
        st.subheader("Choix des cultures à suivre")
        all_cultures = sorted(set(
            c.strip()
            for cell in rules["Cultures affectées"].dropna().astype(str)
            for c in cell.split(",")
            if c.strip()
        ))

        selected_cultures = st.multiselect(
            "Cultures présentes sur le site",
            options=all_cultures,
            default=[c for c in ["Tomate", "Courgette", "Ail", "Laitue"] if c in all_cultures],
        )

        culture_mode = st.radio("Mode de culture dominant", ["Plein champ", "Sous abri"], horizontal=True)

        st.info("Dans cette V1, les cultures sont cochées manuellement. La prochaine version pourra gérer des parcelles, dates de plantation et stades.")

    with tab3:
        st.subheader("Relevé météo automatique")
        mode = st.radio("Localisation", ["Commune", "Coordonnées GPS"], horizontal=True)
        lat = lon = None

        if mode == "Commune":
            city = st.text_input("Commune", value="Saint-Junien")
            if st.button("Rechercher la commune"):
                try:
                    results = geocode_city(city)
                    st.session_state["geocode_results"] = results
                except Exception as exc:
                    st.error(f"Recherche impossible : {exc}")

            results = st.session_state.get("geocode_results", [])
            if results:
                labels = [
                    f"{r.get('name')} — {r.get('admin1', '')} — {r.get('country', '')} ({r['latitude']:.4f}, {r['longitude']:.4f})"
                    for r in results
                ]
                choice = st.selectbox("Choisir le site", range(len(labels)), format_func=lambda i: labels[i])
                lat = results[choice]["latitude"]
                lon = results[choice]["longitude"]
        else:
            col1, col2 = st.columns(2)
            lat = col1.number_input("Latitude", value=45.8880, format="%.6f")
            lon = col2.number_input("Longitude", value=0.9010, format="%.6f")

        col1, col2 = st.columns(2)
        past_days = col1.slider("Jours passés à analyser", 1, 7, 2)
        forecast_days = col2.slider("Jours de prévision", 1, 16, 7)

        if lat is not None and lon is not None:
            if st.button("Récupérer la météo"):
                try:
                    weather = fetch_weather(lat, lon, past_days=past_days, forecast_days=forecast_days)
                    st.session_state["weather"] = weather
                    st.session_state["latlon"] = (lat, lon)
                    st.success("Météo récupérée.")
                except Exception as exc:
                    st.error(f"Récupération météo impossible : {exc}")

        weather = st.session_state.get("weather")
        if isinstance(weather, pd.DataFrame):
            st.dataframe(weather.tail(120), use_container_width=True)
            st.line_chart(weather.set_index("time")[["temperature_2m", "relative_humidity_2m"]])

    with tab4:
        st.subheader("Calcul des risques")
        weather = st.session_state.get("weather")
        if not selected_cultures:
            st.warning("Sélectionne au moins une culture dans l'onglet Cultures suivies.")
            return
        if not isinstance(weather, pd.DataFrame):
            st.warning("Récupère d'abord la météo dans l'onglet Météo.")
            return

        now = pd.Timestamp.now(tz=None)
        horizon = st.selectbox("Fenêtre d'analyse", ["Dernières 48 h", "Prochaines 48 h", "Prochains 7 jours"])
        if horizon == "Dernières 48 h":
            window = weather[(weather["time"] >= now - pd.Timedelta(hours=48)) & (weather["time"] <= now)]
        elif horizon == "Prochaines 48 h":
            window = weather[(weather["time"] >= now) & (weather["time"] <= now + pd.Timedelta(hours=48))]
        else:
            window = weather[(weather["time"] >= now) & (weather["time"] <= now + pd.Timedelta(days=7))]

        rows = []
        for _, rule in rules.iterrows():
            affected = normalize_text(rule["Cultures affectées"])
            if not any(c.lower() in affected.lower() for c in selected_cultures):
                continue

            score, cause = compute_risk_for_rule(rule, window, culture_mode=culture_mode)
            risk = "Élevé" if score >= 8 else "Moyen" if score >= 4 else "Faible"
            rows.append({
                "Maladie": rule["Maladie"],
                "Cultures affectées": rule["Cultures affectées"],
                "Score": score,
                "Risque": risk,
                "Pourquoi": cause,
                "Recommandation": recommendations_from_rule(rule, risk),
                "Sources": rule.get("Sources", ""),
            })

        result = pd.DataFrame(rows).sort_values(["Score", "Maladie"], ascending=[False, True])
        if result.empty:
            st.info("Aucune règle climatique ne correspond aux cultures sélectionnées.")
        else:
            st.dataframe(result, use_container_width=True)
            top = result.head(3)
            st.markdown("### Priorités terrain")
            for _, row in top.iterrows():
                if row["Risque"] == "Élevé":
                    st.error(f"**{row['Maladie']} — risque élevé**  \n{row['Pourquoi']}  \n\n{row['Recommandation']}")
                elif row["Risque"] == "Moyen":
                    st.warning(f"**{row['Maladie']} — risque moyen**  \n{row['Pourquoi']}  \n\n{row['Recommandation']}")
                else:
                    st.success(f"**{row['Maladie']} — risque faible**  \n{row['Pourquoi']}")

            csv = result.to_csv(index=False).encode("utf-8-sig")
            st.download_button(
                "Exporter les alertes en CSV",
                data=csv,
                file_name="alertes_meteo_maladies.csv",
                mime="text/csv",
            )


if __name__ == "__main__":
    main()
