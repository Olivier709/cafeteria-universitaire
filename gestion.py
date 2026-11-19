"""
gestion.py
----------
La classe Cafeteria : elle contient toutes les données (ingrédients, produits,
clients, commandes, historique) et applique les règles de gestion.
Aucun print / input ici : l'affichage est fait dans main.py.
"""

from modeles import (
    ErreurCafeteria, Ingredient, Produit, Etudiant, Personnel, Commande,
    client_depuis_dict, maintenant, STATUTS_VALIDES,
)


def _ajouter_sans_doublon(dictionnaire, objet):
    """Ajoute un objet dans un dictionnaire, en refusant les identifiants en double."""
    if objet.identifiant in dictionnaire:
        raise ValueError(f"Identifiant en double dans le fichier : {objet.identifiant}")
    dictionnaire[objet.identifiant] = objet


class Cafeteria:
    def __init__(self):
        self.ingredients = {}   # {identifiant: Ingredient}
        self.produits = {}      # {identifiant: Produit}
        self.clients = {}       # {identifiant: Client / Etudiant / Personnel}
        self.commandes = {}     # {identifiant: Commande}
        self.historique = []    # liste de {"date": ..., "message": ...}
        self._compteurs = {"ingredient": 1, "produit": 1, "client": 1, "commande": 1}

    # ------------------------------------------------------------------
    # Outils internes
    # ------------------------------------------------------------------
    def _nouvel_id(self, categorie):
        numero = self._compteurs[categorie]
        self._compteurs[categorie] += 1
        return numero

    def enregistrer(self, message):
        """Ajoute une ligne dans l'historique."""
        self.historique.append({"date": maintenant(), "message": message})

    def _ingredient(self, identifiant):
        if identifiant not in self.ingredients:
            raise ErreurCafeteria(f"L'ingrédient n°{identifiant} n'existe pas.")
        return self.ingredients[identifiant]

    def _produit(self, identifiant):
        if identifiant not in self.produits:
            raise ErreurCafeteria(f"Le produit n°{identifiant} n'existe pas.")
        return self.produits[identifiant]

    def _client(self, identifiant):
        if identifiant not in self.clients:
            raise ErreurCafeteria(f"Le client n°{identifiant} n'existe pas.")
        return self.clients[identifiant]

    def _commande(self, identifiant):
        if identifiant not in self.commandes:
            raise ErreurCafeteria(f"La commande n°{identifiant} n'existe pas.")
        return self.commandes[identifiant]

    def _verifier_recette(self, recette):
        if not recette:
            raise ErreurCafeteria("Une recette doit contenir au moins un ingrédient.")
        for ingredient_id, quantite in recette.items():
            self._ingredient(ingredient_id)
            if quantite <= 0:
                raise ErreurCafeteria("Les quantités d'une recette doivent être positives.")

    # ------------------------------------------------------------------
    # Ingrédients et stocks
    # ------------------------------------------------------------------
    def ajouter_ingredient(self, nom, unite, stock, seuil_alerte):
        nom = nom.strip()
        if not nom or not unite.strip():
            raise ErreurCafeteria("Le nom et l'unité sont obligatoires.")
        if stock < 0 or seuil_alerte < 0:
            raise ErreurCafeteria("Le stock et le seuil ne peuvent pas être négatifs.")
        for ing in self.ingredients.values():
            if ing.nom.lower() == nom.lower():
                raise ErreurCafeteria(f"L'ingrédient '{nom}' existe déjà.")
        ingredient = Ingredient(self._nouvel_id("ingredient"), nom, unite.strip(), stock, seuil_alerte)
        self.ingredients[ingredient.identifiant] = ingredient
        self.enregistrer(f"Ingrédient ajouté : {nom} (stock {stock} {ingredient.unite})")
        return ingredient

    def reapprovisionner(self, ingredient_id, quantite):
        ingredient = self._ingredient(ingredient_id)
        if quantite <= 0:
            raise ErreurCafeteria("La quantité doit être positive.")
        ingredient.stock = ingredient.stock + quantite
        self.enregistrer(f"Réapprovisionnement : +{quantite} {ingredient.unite} de {ingredient.nom}")

    def lister_ingredients(self, tri="nom"):
        liste = list(self.ingredients.values())
        if tri == "stock":
            liste.sort(key=lambda ing: ing.stock)
        else:
            liste.sort(key=lambda ing: ing.nom.lower())
        return liste

    def alertes_stock(self):
        return [ing for ing in self.ingredients.values() if ing.est_en_alerte()]

    # ------------------------------------------------------------------
    # Produits et recettes
    # ------------------------------------------------------------------
    def ajouter_produit(self, nom, prix, recette):
        nom = nom.strip()
        if not nom:
            raise ErreurCafeteria("Le nom du produit est obligatoire.")
        if prix <= 0:
            raise ErreurCafeteria("Le prix doit être strictement positif.")
        for p in self.produits.values():
            if p.nom.lower() == nom.lower():
                raise ErreurCafeteria(f"Le produit '{nom}' existe déjà.")
        self._verifier_recette(recette)
        produit = Produit(self._nouvel_id("produit"), nom, prix, recette)
        self.produits[produit.identifiant] = produit
        self.enregistrer(f"Produit ajouté : {nom} ({prix})")
        return produit

    def modifier_recette(self, produit_id, recette):
        """Remplace la recette. Les commandes déjà validées ne sont pas touchées :
        elles gardent en mémoire ce qui a été débité."""
        produit = self._produit(produit_id)
        self._verifier_recette(recette)
        produit.recette = dict(recette)
        self.enregistrer(f"Recette modifiée : {produit.nom}")

    def modifier_prix(self, produit_id, prix):
        """Le nouveau prix ne change pas le total des commandes déjà validées."""
        produit = self._produit(produit_id)
        if prix <= 0:
            raise ErreurCafeteria("Le prix doit être strictement positif.")
        produit.prix = prix
        self.enregistrer(f"Prix modifié : {produit.nom} -> {prix}")

    def lister_produits(self, tri="nom"):
        liste = list(self.produits.values())
        if tri == "prix":
            liste.sort(key=lambda p: p.prix)
        else:
            liste.sort(key=lambda p: p.nom.lower())
        return liste

    def rechercher_produits(self, texte):
        texte = texte.strip().lower()
        return [p for p in self.lister_produits() if texte in p.nom.lower()]

    # ------------------------------------------------------------------
    # Clients
    # ------------------------------------------------------------------
    def ajouter_client(self, type_client, nom):
        nom = nom.strip()
        if not nom:
            raise ErreurCafeteria("Le nom du client est obligatoire.")
        classes = {"etudiant": Etudiant, "personnel": Personnel}
        if type_client not in classes:
            raise ErreurCafeteria("Type de client inconnu (etudiant ou personnel).")
        client = classes[type_client](self._nouvel_id("client"), nom)
        self.clients[client.identifiant] = client
        self.enregistrer(f"Client ajouté : {nom} ({type_client})")
        return client

    def lister_clients(self):
        return sorted(self.clients.values(), key=lambda c: c.nom.lower())

    def rechercher_clients(self, texte):
        texte = texte.strip().lower()
        return [c for c in self.lister_clients() if texte in c.nom.lower()]

    # ------------------------------------------------------------------
    # Commandes
    # ------------------------------------------------------------------
    def creer_commande(self, client_id):
        self._client(client_id)
        commande = Commande(self._nouvel_id("commande"), client_id)
        self.commandes[commande.identifiant] = commande
        self.enregistrer(f"Commande n°{commande.identifiant} créée pour {self.clients[client_id].nom}")
        return commande

    def ajouter_ligne(self, commande_id, produit_id, quantite):
        commande = self._commande(commande_id)
        self._produit(produit_id)
        commande.ajouter_produit(produit_id, quantite)

    def retirer_ligne(self, commande_id, produit_id, quantite=None):
        self._commande(commande_id).retirer_produit(produit_id, quantite)

    def sous_total(self, commande):
        """Somme des prix des produits, avant remise."""
        somme = 0
        for produit_id, quantite in commande.lignes.items():
            somme += self.produits[produit_id].prix * quantite
        return round(somme, 2)

    def calculer_total(self, commande):
        """Total après la remise du client (étudiant ou personnel)."""
        client = self.clients[commande.client_id]
        return client.calculer_prix(self.sous_total(commande))

    def total_commande(self, commande):
        """Total estimé pour un brouillon, total figé pour les autres."""
        if commande.statut == "brouillon":
            return self.calculer_total(commande)
        return commande.total

    def calculer_besoins(self, commande):
        """Besoins CUMULÉS en ingrédients de tous les produits de la commande."""
        besoins = {}
        for produit_id, quantite in commande.lignes.items():
            for ingredient_id, par_unite in self.produits[produit_id].recette.items():
                besoins[ingredient_id] = besoins.get(ingredient_id, 0) + par_unite * quantite
        return besoins

    def valider_commande(self, commande_id):
        """Règle centrale : on vérifie TOUS les besoins avant de débiter quoi que ce soit."""
        commande = self._commande(commande_id)
        if commande.statut != "brouillon":
            raise ErreurCafeteria(
                f"La commande n°{commande_id} ne peut pas être validée (statut : {commande.statut}).")
        if not commande.lignes:
            raise ErreurCafeteria("Impossible de valider une commande vide.")

        besoins = self.calculer_besoins(commande)

        # 1) Vérification (aucune modification pour l'instant)
        manques = []
        for ingredient_id, besoin in besoins.items():
            ing = self.ingredients[ingredient_id]
            if ing.stock < besoin:
                manques.append(f"{ing.nom} : besoin {besoin} {ing.unite}, disponible {ing.stock} {ing.unite}")
        if manques:
            raise ErreurCafeteria("Stock insuffisant, aucun stock débité :\n  - " + "\n  - ".join(manques))

        # 2) Tout est bon : on débite, on fige le total et on change le statut
        for ingredient_id, besoin in besoins.items():
            ing = self.ingredients[ingredient_id]
            ing.stock = ing.stock - besoin
        commande.besoins_debites = besoins
        commande.total = self.calculer_total(commande)
        commande.changer_statut("en_preparation")
        self.enregistrer(f"Commande n°{commande_id} validée (total {commande.total})")
        return commande

    def marquer_prete(self, commande_id):
        commande = self._commande(commande_id)
        commande.changer_statut("prete")
        self.enregistrer(f"Commande n°{commande_id} prête")

    def marquer_livree(self, commande_id):
        commande = self._commande(commande_id)
        commande.changer_statut("livree")
        self.enregistrer(f"Commande n°{commande_id} livrée")

    def annuler_commande(self, commande_id):
        """Annulation possible seulement pour un brouillon ou une commande en préparation.
        En préparation : les ingrédients débités sont remis en stock."""
        commande = self._commande(commande_id)
        if commande.statut == "brouillon":
            commande.changer_statut("annulee")
            self.enregistrer(f"Commande n°{commande_id} annulée (brouillon, stock inchangé)")
        elif commande.statut == "en_preparation":
            for ingredient_id, quantite in commande.besoins_debites.items():
                ing = self.ingredients[ingredient_id]
                ing.stock = ing.stock + quantite
            commande.changer_statut("annulee")
            self.enregistrer(f"Commande n°{commande_id} annulée (stock recrédité)")
        else:
            raise ErreurCafeteria(
                f"Annulation impossible : la commande est '{commande.statut}'.")

    def lister_commandes(self, statut=None, client_id=None, tri="identifiant"):
        resultat = []
        for c in self.commandes.values():
            if statut is not None and c.statut != statut:
                continue
            if client_id is not None and c.client_id != client_id:
                continue
            resultat.append(c)
        if tri == "total":
            resultat.sort(key=lambda c: self.total_commande(c))
        elif tri == "date":
            resultat.sort(key=lambda c: c.date)
        else:
            resultat.sort(key=lambda c: c.identifiant)
        return resultat

    # ------------------------------------------------------------------
    # Indicateurs
    # ------------------------------------------------------------------
    def chiffre_affaires(self):
        """Ventes = somme des totaux des commandes LIVRÉES."""
        return round(sum(c.total for c in self.commandes.values() if c.statut == "livree"), 2)

    def nombre_par_statut(self):
        compte = {}
        for c in self.commandes.values():
            compte[c.statut] = compte.get(c.statut, 0) + 1
        return compte

    def produits_populaires(self, n=5):
        """Produits les plus demandés (commandes validées, annulées exclues)."""
        compteur = {}
        for c in self.commandes.values():
            if c.statut in STATUTS_VALIDES:
                for produit_id, quantite in c.lignes.items():
                    compteur[produit_id] = compteur.get(produit_id, 0) + quantite
        classement = sorted(compteur.items(), key=lambda element: element[1], reverse=True)
        return [(self.produits[pid].nom, quantite) for pid, quantite in classement[:n]]

    # ------------------------------------------------------------------
    # Conversion vers / depuis le JSON
    # ------------------------------------------------------------------
    def vers_dict(self):
        return {
            "compteurs": dict(self._compteurs),
            "ingredients": [i.vers_dict() for i in self.ingredients.values()],
            "produits": [p.vers_dict() for p in self.produits.values()],
            "clients": [c.vers_dict() for c in self.clients.values()],
            "commandes": [c.vers_dict() for c in self.commandes.values()],
            "historique": list(self.historique),
        }

    @staticmethod
    def depuis_dict(d):
        if not isinstance(d, dict):
            raise ValueError("Le fichier doit contenir un objet JSON.")
        cafe = Cafeteria()
        for x in d["ingredients"]:
            _ajouter_sans_doublon(cafe.ingredients, Ingredient.depuis_dict(x))
        for x in d["produits"]:
            _ajouter_sans_doublon(cafe.produits, Produit.depuis_dict(x))
        for x in d["clients"]:
            _ajouter_sans_doublon(cafe.clients, client_depuis_dict(x))
        for x in d["commandes"]:
            _ajouter_sans_doublon(cafe.commandes, Commande.depuis_dict(x))
        for ligne in d["historique"]:
            cafe.historique.append({"date": ligne["date"], "message": ligne["message"]})

        # Les compteurs ne doivent jamais redonner un identifiant déjà utilisé.
        existants = {
            "ingredient": cafe.ingredients, "produit": cafe.produits,
            "client": cafe.clients, "commande": cafe.commandes,
        }
        for categorie, dictionnaire in existants.items():
            plus_grand = max(dictionnaire) if dictionnaire else 0
            sauvegarde = d.get("compteurs", {}).get(categorie, 1)
            cafe._compteurs[categorie] = max(sauvegarde, plus_grand + 1)

        cafe._verifier_coherence()
        return cafe

    def _verifier_coherence(self):
        """Vérifie que les liens entre objets pointent vers des objets existants."""
        for p in self.produits.values():
            for ingredient_id in p.recette:
                if ingredient_id not in self.ingredients:
                    raise ValueError(f"Produit n°{p.identifiant} : ingrédient {ingredient_id} inconnu.")
        for c in self.commandes.values():
            if c.client_id not in self.clients:
                raise ValueError(f"Commande n°{c.identifiant} : client {c.client_id} inconnu.")
            for produit_id in c.lignes:
                if produit_id not in self.produits:
                    raise ValueError(f"Commande n°{c.identifiant} : produit {produit_id} inconnu.")
            for ingredient_id in c.besoins_debites:
                if ingredient_id not in self.ingredients:
                    raise ValueError(f"Commande n°{c.identifiant} : ingrédient {ingredient_id} inconnu.")