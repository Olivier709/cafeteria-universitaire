"""
main.py
-------
Point d'entrée du programme : menus interactifs de la cafétéria universitaire.
Lancer avec :  python main.py
"""

import os

from modeles import ErreurCafeteria, DEVISE, STATUTS
from stockage import charger, sauvegarder, ErreurFichier

# Le fichier de données est toujours cherché à côté de main.py
FICHIER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "donnees.json")


# ===========================================================================
# Les Fonctions de saisie (contrôle des entrées)
# ===========================================================================
def lire_texte(message):
    while True:
        texte = input(message).strip()
        if texte:
            return texte
        print("Erreur : ce champ ne peut pas être vide.")


def lire_entier(message, minimum=None):
    while True:
        saisie = input(message).strip()
        try:
            valeur = int(saisie)
        except ValueError:
            print("Erreur : entrez un nombre entier.")
            continue
        if minimum is not None and valeur < minimum:
            print(f"Erreur : la valeur doit être au moins {minimum}.")
            continue
        return valeur


def lire_nombre(message, minimum=None):
    """Nombre avec virgule possible (ex. 12,5)."""
    while True:
        saisie = input(message).strip().replace(",", ".")
        try:
            valeur = float(saisie)
        except ValueError:
            print("Erreur : entrez un nombre.")
            continue
        if minimum is not None and valeur < minimum:
            print(f"Erreur : la valeur doit être au moins {minimum}.")
            continue
        return valeur


def confirmer(message):
    return input(message + " (o/n) : ").strip().lower() in ("o", "oui")


def sauver(cafe):
    try:
        sauvegarder(cafe, FICHIER)
    except OSError as erreur:
        print("ATTENTION : la sauvegarde a échoué :", erreur)


# ===========================================================================
# Fonctions d'affichage
# ===========================================================================
def afficher_ingredients(liste):
    if not liste:
        print("Aucun ingrédient.")
        return
    print(f"{'N°':<4}{'Nom':<20}{'Stock':>8} {'Unité':<8}{'Seuil':>8}")
    for ing in liste:
        alerte = "   <-- ALERTE" if ing.est_en_alerte() else ""
        print(f"{ing.identifiant:<4}{ing.nom:<20}{ing.stock:>8} {ing.unite:<8}{ing.seuil_alerte:>8}{alerte}")


def afficher_produits(cafe, liste):
    if not liste:
        print("Aucun produit.")
        return
    for p in liste:
        recette = ", ".join(
            f"{cafe.ingredients[i].nom} {q}{cafe.ingredients[i].unite}" for i, q in p.recette.items())
        print(f"{p.identifiant:<4}{p.nom:<22}{p.prix:>8.2f} {DEVISE}   [{recette}]")


def afficher_clients(liste):
    if not liste:
        print("Aucun client.")
        return
    for c in liste:
        print(f"{c.identifiant:<4}{c.nom:<25}{c.type_client:<11}{c.description_tarif()}")


def afficher_commandes(cafe, liste):
    if not liste:
        print("Aucune commande.")
        return
    print(f"{'N°':<4}{'Client':<22}{'Statut':<16}{'Total':>10}  Date")
    for c in liste:
        client = cafe.clients[c.client_id].nom
        total = cafe.total_commande(c)
        print(f"{c.identifiant:<4}{client:<22}{c.statut:<16}{total:>10.2f}  {c.date}")


def afficher_detail_commande(cafe, commande):
    client = cafe.clients[commande.client_id]
    print(f"\nCommande n°{commande.identifiant} - {client.nom} ({client.type_client})")
    print(f"Statut : {commande.statut}   Date : {commande.date}")
    if not commande.lignes:
        print("  (aucun produit)")
    for produit_id, quantite in commande.lignes.items():
        produit = cafe.produits[produit_id]
        print(f"  {quantite} x {produit.nom:<22} {produit.prix * quantite:>8.2f} {DEVISE}")
    print(f"Sous-total : {cafe.sous_total(commande):.2f} {DEVISE}")
    etiquette = "Total estimé" if commande.statut == "brouillon" else "Total"
    print(f"{etiquette} ({client.description_tarif()}) : {cafe.total_commande(commande):.2f} {DEVISE}")


# ===========================================================================
# Actions : ingrédients
# ===========================================================================
def ui_lister_ingredients(cafe):
    print("Trier par : 1. nom   2. stock (du plus petit au plus grand)")
    tri = "stock" if lire_entier("Choix : ", 1) == 2 else "nom"
    afficher_ingredients(cafe.lister_ingredients(tri))


def ui_ajouter_ingredient(cafe):
    nom = lire_texte("Nom de l'ingrédient : ")
    unite = lire_texte("Unité (g, ml, unité...) : ")
    stock = lire_entier("Stock initial : ", 0)
    seuil = lire_entier("Seuil d'alerte : ", 0)
    ing = cafe.ajouter_ingredient(nom, unite, stock, seuil)
    print(f"Ingrédient ajouté avec le n°{ing.identifiant}.")


def ui_reapprovisionner(cafe):
    afficher_ingredients(cafe.lister_ingredients())
    ing_id = lire_entier("N° de l'ingrédient : ", 1)
    quantite = lire_entier("Quantité à ajouter : ", 1)
    cafe.reapprovisionner(ing_id, quantite)
    print("Stock mis à jour.")


# ===========================================================================
# Actions : produits et recettes
# ===========================================================================
def saisir_recette(cafe):
    recette = {}
    afficher_ingredients(cafe.lister_ingredients())
    print("Composez la recette (quantité d'ingrédient pour UN produit).")
    while True:
        ing_id = lire_entier("N° de l'ingrédient (0 = terminer) : ", 0)
        if ing_id == 0:
            break
        if ing_id not in cafe.ingredients:
            print("Erreur : cet ingrédient n'existe pas.")
            continue
        ing = cafe.ingredients[ing_id]
        recette[ing_id] = lire_entier(f"Quantité de {ing.nom} ({ing.unite}) : ", 1)
    return recette


def ui_lister_produits(cafe):
    print("Trier par : 1. nom   2. prix")
    tri = "prix" if lire_entier("Choix : ", 1) == 2 else "nom"
    afficher_produits(cafe, cafe.lister_produits(tri))


def ui_rechercher_produit(cafe):
    texte = lire_texte("Texte à chercher dans le nom : ")
    afficher_produits(cafe, cafe.rechercher_produits(texte))


def ui_ajouter_produit(cafe):
    nom = lire_texte("Nom du produit : ")
    prix = lire_nombre(f"Prix ({DEVISE}) : ", 0.01)
    recette = saisir_recette(cafe)
    produit = cafe.ajouter_produit(nom, prix, recette)
    print(f"Produit ajouté avec le n°{produit.identifiant}.")


def ui_modifier_recette(cafe):
    afficher_produits(cafe, cafe.lister_produits())
    produit_id = lire_entier("N° du produit : ", 1)
    if produit_id not in cafe.produits:
        raise ErreurCafeteria(f"Le produit n°{produit_id} n'existe pas.")
    print("La nouvelle recette REMPLACE l'ancienne.")
    recette = saisir_recette(cafe)
    cafe.modifier_recette(produit_id, recette)
    print("Recette modifiée.")


def ui_modifier_prix(cafe):
    afficher_produits(cafe, cafe.lister_produits())
    produit_id = lire_entier("N° du produit : ", 1)
    prix = lire_nombre(f"Nouveau prix ({DEVISE}) : ", 0.01)
    cafe.modifier_prix(produit_id, prix)
    print("Prix modifié.")


# ===========================================================================
# Actions : clients
# ===========================================================================
def ui_lister_clients(cafe):
    afficher_clients(cafe.lister_clients())


def ui_rechercher_client(cafe):
    texte = lire_texte("Texte à chercher dans le nom : ")
    afficher_clients(cafe.rechercher_clients(texte))


def ui_ajouter_client(cafe):
    nom = lire_texte("Nom du client : ")
    print("Type : 1. étudiant   2. personnel")
    choix = lire_entier("Choix : ", 1)
    if choix not in (1, 2):
        raise ErreurCafeteria("Choix invalide.")
    type_client = "etudiant" if choix == 1 else "personnel"
    client = cafe.ajouter_client(type_client, nom)
    print(f"Client ajouté avec le n°{client.identifiant}.")


# ===========================================================================
# Actions : commandes
# ===========================================================================
def choisir_commande(cafe, statut=None):
    """Affiche les commandes (filtrées par statut) et demande un numéro."""
    liste = cafe.lister_commandes(statut=statut)
    if not liste:
        raise ErreurCafeteria("Aucune commande disponible pour cette action.")
    afficher_commandes(cafe, liste)
    commande_id = lire_entier("N° de la commande : ", 1)
    if commande_id not in [c.identifiant for c in liste]:
        raise ErreurCafeteria(f"La commande n°{commande_id} n'est pas dans la liste proposée.")
    return commande_id


def ajouter_produits_a_commande(cafe, commande_id):
    afficher_produits(cafe, cafe.lister_produits())
    while True:
        produit_id = lire_entier("N° du produit (0 = terminer) : ", 0)
        if produit_id == 0:
            break
        quantite = lire_entier("Quantité : ", 1)
        try:
            cafe.ajouter_ligne(commande_id, produit_id, quantite)
            sauver(cafe)
            print("Produit ajouté à la commande.")
        except ErreurCafeteria as erreur:
            print("Opération refusée :", erreur)


def ui_nouvelle_commande(cafe):
    afficher_clients(cafe.lister_clients())
    client_id = lire_entier("N° du client : ", 1)
    commande = cafe.creer_commande(client_id)
    sauver(cafe)
    print(f"Commande n°{commande.identifiant} créée (brouillon).")
    ajouter_produits_a_commande(cafe, commande.identifiant)


def ui_ajouter_produit_commande(cafe):
    commande_id = choisir_commande(cafe, "brouillon")
    ajouter_produits_a_commande(cafe, commande_id)


def ui_retirer_produit_commande(cafe):
    commande_id = choisir_commande(cafe, "brouillon")
    afficher_detail_commande(cafe, cafe.commandes[commande_id])
    produit_id = lire_entier("N° du produit à retirer : ", 1)
    quantite = lire_entier("Quantité à retirer (0 = tout retirer) : ", 0)
    cafe.retirer_ligne(commande_id, produit_id, None if quantite == 0 else quantite)
    print("Commande modifiée.")


def ui_detail_commande(cafe):
    commande_id = choisir_commande(cafe)
    afficher_detail_commande(cafe, cafe.commandes[commande_id])


def ui_valider_commande(cafe):
    commande_id = choisir_commande(cafe, "brouillon")
    afficher_detail_commande(cafe, cafe.commandes[commande_id])
    if not confirmer("Valider cette commande ?"):
        print("Validation annulée.")
        return
    commande = cafe.valider_commande(commande_id)
    print(f"Commande validée. Total à payer : {commande.total:.2f} {DEVISE}")


def ui_marquer_prete(cafe):
    commande_id = choisir_commande(cafe, "en_preparation")
    cafe.marquer_prete(commande_id)
    print("Commande prête.")


def ui_marquer_livree(cafe):
    commande_id = choisir_commande(cafe, "prete")
    cafe.marquer_livree(commande_id)
    print("Commande livrée.")


def ui_annuler_commande(cafe):
    commande_id = choisir_commande(cafe)
    if not confirmer("Confirmer l'annulation ?"):
        print("Annulation abandonnée.")
        return
    cafe.annuler_commande(commande_id)
    print("Commande annulée.")


def ui_lister_commandes(cafe):
    print("Filtrer : 0. Tous   " + "   ".join(f"{i}. {s}" for i, s in enumerate(STATUTS, start=1)))
    choix = lire_entier("Choix : ", 0)
    if choix > len(STATUTS):
        raise ErreurCafeteria("Choix invalide.")
    statut = None if choix == 0 else STATUTS[choix - 1]
    print("Trier par : 1. numéro   2. total   3. date")
    tri = {1: "identifiant", 2: "total", 3: "date"}.get(lire_entier("Choix : ", 1), "identifiant")
    afficher_commandes(cafe, cafe.lister_commandes(statut=statut, tri=tri))


# ===========================================================================
# Actions : indicateurs, alertes, historique
# ===========================================================================
def ui_ventes(cafe):
    print(f"\nChiffre d'affaires (commandes livrées) : {cafe.chiffre_affaires():.2f} {DEVISE}")
    print("\nNombre de commandes par statut :")
    for statut, nombre in cafe.nombre_par_statut().items():
        print(f"  {statut:<16}{nombre}")
    print("\nProduits les plus demandés (commandes validées) :")
    populaires = cafe.produits_populaires()
    if not populaires:
        print("  Aucune vente pour le moment.")
    for rang, (nom, quantite) in enumerate(populaires, start=1):
        print(f"  {rang}. {nom} : {quantite}")


def ui_alertes(cafe):
    alertes = cafe.alertes_stock()
    if not alertes:
        print("Aucune alerte : tous les stocks sont au-dessus du seuil.")
    else:
        print("Ingrédients à réapprovisionner :")
        afficher_ingredients(alertes)


def ui_historique(cafe):
    if not cafe.historique:
        print("Historique vide.")
        return
    dernieres = cafe.historique[-20:]
    print(f"Les {len(dernieres)} dernières opérations (sur {len(cafe.historique)}) :")
    for ligne in dernieres:
        print(f"  {ligne['date']}  {ligne['message']}")


# ===========================================================================
# Menus
# ===========================================================================
def executer_menu(cafe, titre, options, libelle_zero="Retour"):
    """Affiche un menu. Chaque option = (libellé, fonction, modifie_les_données).
    Après une action qui modifie les données, on sauvegarde dans le JSON."""
    while True:
        print(f"\n=== {titre} ===")
        for numero, (libelle, _, _) in enumerate(options, start=1):
            print(f"{numero}. {libelle}")
        print(f"0. {libelle_zero}")
        choix = lire_entier("Votre choix : ", 0)
        if choix == 0:
            return
        if choix > len(options):
            print("Choix invalide.")
            continue
        _, fonction, modifie = options[choix - 1]
        try:
            fonction(cafe)
            if modifie:
                sauver(cafe)
        except ErreurCafeteria as erreur:
            print("Opération refusée :", erreur)


def menu_ingredients(cafe):
    executer_menu(cafe, "INGRÉDIENTS ET STOCKS", [
        ("Lister les ingrédients", ui_lister_ingredients, False),
        ("Ajouter un ingrédient", ui_ajouter_ingredient, True),
        ("Réapprovisionner un ingrédient", ui_reapprovisionner, True),
    ])


def menu_produits(cafe):
    executer_menu(cafe, "PRODUITS ET RECETTES", [
        ("Lister les produits", ui_lister_produits, False),
        ("Rechercher un produit", ui_rechercher_produit, False),
        ("Ajouter un produit", ui_ajouter_produit, True),
        ("Modifier la recette d'un produit", ui_modifier_recette, True),
        ("Modifier le prix d'un produit", ui_modifier_prix, True),
    ])


def menu_clients(cafe):
    executer_menu(cafe, "CLIENTS", [
        ("Lister les clients", ui_lister_clients, False),
        ("Rechercher un client", ui_rechercher_client, False),
        ("Ajouter un client", ui_ajouter_client, True),
    ])


def menu_commandes(cafe):
    executer_menu(cafe, "COMMANDES", [
        ("Nouvelle commande", ui_nouvelle_commande, True),
        ("Ajouter des produits à un brouillon", ui_ajouter_produit_commande, True),
        ("Retirer un produit d'un brouillon", ui_retirer_produit_commande, True),
        ("Voir le détail d'une commande", ui_detail_commande, False),
        ("Valider une commande", ui_valider_commande, True),
        ("Marquer une commande prête", ui_marquer_prete, True),
        ("Marquer une commande livrée", ui_marquer_livree, True),
        ("Annuler une commande", ui_annuler_commande, True),
        ("Lister / filtrer / trier les commandes", ui_lister_commandes, False),
    ])


def menu_principal(cafe):
    executer_menu(cafe, "CAFÉTÉRIA UNIVERSITAIRE", [
        ("Ingrédients et stocks", menu_ingredients, False),
        ("Produits et recettes", menu_produits, False),
        ("Clients", menu_clients, False),
        ("Commandes", menu_commandes, False),
        ("Ventes et statistiques", ui_ventes, False),
        ("Alertes de stock", ui_alertes, False),
        ("Historique des opérations", ui_historique, False),
    ], libelle_zero="Quitter")


def main():
    if not os.path.exists(FICHIER):
        print("Premier lancement : aucun fichier de données trouvé, on démarre à vide.")
    try:
        cafe = charger(FICHIER)
    except ErreurFichier as erreur:
        print("Impossible de charger le fichier de données.")
        print("Détail :", erreur)
        print("Le fichier n'a PAS été modifié. Corrigez-le (ou renommez-le), puis relancez.")
        return
    try:
        menu_principal(cafe)
    except (KeyboardInterrupt, EOFError):
        print()
    print("Au revoir ! Les données sont sauvegardées.")


if __name__ == "__main__":
    main()
