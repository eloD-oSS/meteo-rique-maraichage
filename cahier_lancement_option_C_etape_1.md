# Cahier de lancement — Option C, étape 1

## Objectif

Créer une première application web locale qui conserve l'Excel comme moteur métier.

L'application doit permettre de vérifier une chose simple :

> Est-ce que le croisement entre cultures présentes, météo locale et paramètres climatiques produit une alerte maladie utile pour l'encadrant ?

## Périmètre V1

### Inclus

- Lecture de l'Excel existant.
- Lecture de l'onglet `Paramètres climatiques`.
- Lecture de l'onglet `maladies et ravageurs`.
- Choix manuel des cultures suivies.
- Récupération météo via Open-Meteo.
- Calcul d'un score de risque.
- Affichage des priorités terrain.
- Export CSV des alertes.

### Non inclus

- Gestion multi-structures.
- Authentification.
- Application mobile native.
- Notifications.
- Base de données permanente.
- Historique détaillé par parcelle.

## Logique de risque V1

Le score est volontairement simple :

- température dans la plage favorable ;
- température dans l'optimum ;
- humidité au-dessus du seuil ;
- durée d'humidité critique ;
- pluie récente ;
- probabilité d'eau libre / rosée ;
- bonus vigilance sous abri.

Le résultat est classé en :

- Faible ;
- Moyen ;
- Élevé.

## Point de vigilance

Une alerte ne signifie pas que la maladie est présente.  
Elle signifie que les conditions météo deviennent favorables.

L'outil doit donc rester un outil d'aide à l'observation, pas un diagnostic automatique.

## Prochaine étape après test

Si la V1 est cohérente sur le terrain :

1. ajout de parcelles ;
2. dates de plantation ;
3. stades de culture ;
4. historique des observations ;
5. tableau de bord multi-sites ;
6. transformation en PWA utilisable sur smartphone.
