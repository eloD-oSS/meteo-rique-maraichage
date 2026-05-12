# Météo-Risque Maraîchage — Prototype V1

Ce prototype transforme l'Excel existant en **interface web locale**.

L'Excel n'est pas réécrit : il reste le moteur métier.  
L'application lit directement les onglets :

- `Paramètres climatiques`
- `maladies et ravageurs`

Puis elle récupère la météo via Open-Meteo et calcule un premier score de risque maladie.

## Installation sur PC Windows

1. Installer Python 3.11 ou 3.12 depuis python.org.
2. Ouvrir le dossier du prototype.
3. Double-cliquer sur `lancer_windows.bat`.

Ou en ligne de commande :

```bash
pip install -r requirements.txt
streamlit run app.py
```

L'application s'ouvre ensuite dans le navigateur.

## Ce que fait la V1

- lit l'Excel existant ;
- affiche la base maladies/ravageurs ;
- affiche la base des paramètres climatiques ;
- permet de choisir les cultures présentes ;
- récupère la météo horaire :
  - température ;
  - humidité relative ;
  - pluie ;
  - rosée / point de rosée ;
  - vent ;
- calcule un score de risque simple ;
- affiche une priorité terrain ;
- exporte les alertes au format CSV.

## Ce que la V1 ne fait pas encore

- comptes utilisateurs ;
- stockage par structure ;
- vraie gestion des parcelles ;
- notifications automatiques ;
- photos terrain ;
- historique saisonnier ;
- application mobile native.

Ces briques viennent après validation du cœur : météo + cultures + règles maladies = alerte utile.

## Source météo

Le prototype utilise Open-Meteo :
- Forecast API : https://open-meteo.com/en/docs
- Geocoding API : https://open-meteo.com/en/docs/geocoding-api

Open-Meteo indique proposer une API gratuite pour les usages non commerciaux et sans clé API.
