# Planche · maraîchage 🌱

Application web mobile pour le maraîchage biologique et la pépinière.

👉 **App en ligne : https://elod-oss.github.io/meteo-rique-maraichage/**

## Ce que fait l'app

- **Fiches détaillées** pour 47 espèces (semis, plantation, fertilisation, maladies, ravageurs, paramètres climatiques)
- **Calculateur Plants** : combien de plants pour une planche selon ses dimensions, en mode bio-intensif ou Agrosemens
- **Calculateur Fertilisation** : besoins N · P · K et compost par planche, calculés depuis les références hectare
- **Alertes maladies météo** : croisement automatique des prévisions Open-Meteo (7 jours) avec les seuils climatiques de 40 maladies (T° optimale, humidité critique, eau libre, durée d'incubation)

## Caractéristiques techniques

- **App web 100 % statique** (un seul fichier HTML autonome ~150 Ko)
- **Pas de serveur**, pas de base de données, pas de compte
- **Hors-ligne** sauf pour l'onglet Météo (qui interroge Open-Meteo, ~15 Ko/actualisation)
- **Installable** sur l'écran d'accueil du téléphone comme une PWA
- **Position confidentielle** : stockée uniquement dans le navigateur (localStorage)

## Sources

- Base maraîchage : AgroBio Bretagne, GRAB, GAB, FNAB, Agrosemens
- Base maladies & climatique : INRAE Ephytia, ITAB, ARVALIS, MAB16 2024, GECO Ecophytopic
- Météo : [Open-Meteo](https://open-meteo.com) (gratuit, sans clé API)
- Fichier source de référence : `Tableau_semis_densite_calculateur.xlsx`

## Limites connues

- L'humidité Open-Meteo est mesurée à 2 m d'altitude, pas au niveau du feuillage → la durée d'humectation foliaire est estimée, pas mesurée comme avec un capteur de terrain (type Mileos®)
- Les virus (CMV, TSWV, TMV…) sans seuil T°/HR ne génèrent pas d'alerte automatique
- Les seuils de risque (faible / modéré / élevé) sont volontairement prudents

## Utilisation hors-ligne

Une fois le site chargé une première fois, **toutes les fiches espèces et les calculateurs marchent sans internet**. Seul l'onglet Météo réactualise les données via l'API (~15-20 Ko par actualisation).

Pour l'installer sur le téléphone : ouvrir le site, puis menu navigateur → "Ajouter à l'écran d'accueil".

## Évolutions envisagées

- Ajout de fruitiers insolites et légumes vivaces (pépinière)
- Calendrier de semis local selon saison et zone climatique
- Carnet d'observations terrain (parcelles, dates, photos)
- Historique des alertes pour comparaison saisonnière
