# Gestion d'une cafétéria universitaire

Mini-projet Python : application de gestion en console (programmation orientée objet, sauvegarde JSON).

## Fonctionnalités

- Gestion des ingrédients, des stocks, du réapprovisionnement et des alertes de stock.
- Gestion des produits et de leurs recettes (ajout, modification de la recette et du prix).
- Clients étudiants (20 % de remise) et personnel (5 % de remise, 10 % dès 500), grâce à l'héritage.
- Commandes à plusieurs produits, modifiables tant qu'elles sont en brouillon.
- Validation avec vérification des besoins cumulés : si un ingrédient manque, aucun stock n'est débité.
- Suivi des statuts : brouillon, en préparation, prête, livrée, annulée.
- Recherche, tri, chiffre d'affaires, produits les plus demandés, historique des opérations.
- Sauvegarde automatique dans `donnees.json`.


## Fichiers du projet

| Fichier                 | Rôle                                                                           |
| ----------------------- | ------------------------------------------------------------------------------ |
| `main.py`               | Menus interactifs, saisies et affichage                                        |
| `gestion.py`            | Classe `Cafeteria` : règles de gestion et indicateurs                          |
| `modeles.py`            | Classes `Ingredient`, `Produit`, `Client`, `Etudiant`, `Personnel`, `Commande` |
| `stockage.py`           | Sauvegarde et chargement JSON                                                  |
| `donnees.json`          | Données de démonstration                                                       |
| `rapport_cafeteria.pdf` | Document de présentation (2 à 3 pages)                                         |

## Exemple d'utilisation

1. Menu `4. Commandes` puis `1. Nouvelle commande` : choisir un client, ajouter des produits, puis taper `0`.
2. `5. Valider une commande` : si le stock est suffisant, la commande passe « en préparation » et le stock est débité ; sinon elle est refusée et rien n'est modifié.
3. `6. Marquer une commande prête`, puis `7. Marquer une commande livrée`.
4. `8. Annuler une commande` : une commande en préparation est annulée et son stock est remis.
5. Menu principal, `5. Ventes et statistiques` et `6. Alertes de stock` pour consulter les indicateurs.

## Règles de gestion

- Passages de statut autorisés : brouillon -> en préparation -> prête -> livrée.
- Annulation possible seulement depuis « brouillon » (stock inchangé) ou « en préparation » (stock recrédité). Une commande prête, livrée ou déjà annulée ne peut plus être annulée.
- Une commande validée n'est plus modifiable. Changer une recette ou un prix n'affecte pas les commandes déjà validées.
- Ventes (chiffre d'affaires) = total des commandes livrées. Produits les plus demandés = commandes validées et non annulées.
- Alerte de stock quand le stock est inférieur ou égal au seuil d'alerte.
