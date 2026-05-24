# Outil d'aide au maraîchage

Outil web de poche pour maraîchers et jardiniers en agriculture biologique. Anticipe les risques de maladies fongiques sur vos cultures à partir des prévisions météo locales sur 7 jours.

## Fonctionnalités

- **Alertes maladies** — score de risque calculé jour par jour (mildiou, oïdium, fonte de semis…) selon les conditions hygrométriques et thermiques prévues
- **Calculateur ferti** — dose d'apport N·P·K et compost ramenée à la surface de votre planche à partir des besoins/ha
- **Fiches espèces** — sémiologie, densités de semis, maladies, ravageurs et solutions biocontrôle pour 40+ légumes

## Données météo

Prévisions 7 jours via [Open-Meteo](https://open-meteo.com/) — API gratuite, sans inscription. La position GPS est conservée uniquement en `localStorage` sur l'appareil de l'utilisateur.

## Sources agronomiques

INRAE Ephytia · AgroBio Bretagne · GRAB · GAB · FNAB · Bayer-agri

## Installation (PWA)

L'application est installable sur mobile et desktop. Un bandeau d'installation apparaît automatiquement sur les navigateurs compatibles, ou utilisez le menu natif du navigateur.

## Développement

Projet HTML/CSS/JS monofichier, sans build, hébergé sur GitHub Pages.

```sh
git clone https://github.com/elod-oss/meteo-rique-maraichage.git
cd meteo-rique-maraichage

# Serveur local (requis pour le service worker)
npx serve .
# ou
python -m http.server 8000
```

> Le service worker ne fonctionne qu'avec `https://` ou `localhost` — ouvrir `index.html` directement (`file://`) ne suffit pas.

## Licence

[MIT](LICENSE)
