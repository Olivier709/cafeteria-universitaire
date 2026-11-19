"""
modeles.py
----------
Les classes du projet : Ingredient, Produit, Client (avec Etudiant et Personnel)
et Commande, ainsi que l'erreur personnalisée ErreurCafeteria.
"""

from datetime import datetime

DEVISE = "HTG"  # monnaie affichée (modifiable)

# Etats d'une commande et passages autorisés d'un état à un autre.
TRANSITIONS = {
    "brouillon": ["en_preparation", "annulee"],
    "en_preparation": ["prete", "annulee"],
    "prete": ["livree"],
    "livree": [],
    "annulee": [],
}
STATUTS = list(TRANSITIONS.keys())

# Une commande "validée" a été acceptée (stock débité) et n'est pas annulée.
STATUTS_VALIDES = ["en_preparation", "prete", "livree"]


class ErreurCafeteria(Exception):
    """Erreur levée quand une opération est refusée (règle de gestion non respectée)."""


def maintenant():
    """Retourne la date et l'heure actuelles sous forme de texte."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ---------------------------------------------------------------------------
# INGREDIENT
# ---------------------------------------------------------------------------
class Ingredient:
    """Un ingrédient en stock (ex. : Pain, Lait, Café moulu)."""

    def __init__(self, identifiant, nom, unite, stock, seuil_alerte):
        self.identifiant = identifiant
        self.nom = nom
        self.unite = unite
        self.seuil_alerte = seuil_alerte
        self._stock = 0          # attribut protégé (encapsulation)
        self.stock = stock       # passe par le "setter" qui vérifie la valeur

    @property
    def stock(self):
        return self._stock

    @stock.setter
    def stock(self, valeur):
        if valeur < 0:
            raise ErreurCafeteria(f"Le stock de {self.nom} ne peut pas être négatif.")
        self._stock = valeur

    def est_en_alerte(self):
        """Vrai si le stock est inférieur ou égal au seuil d'alerte."""
        return self._stock <= self.seuil_alerte

    def vers_dict(self):
        return {
            "identifiant": self.identifiant,
            "nom": self.nom,
            "unite": self.unite,
            "stock": self._stock,
            "seuil_alerte": self.seuil_alerte,
        }

    @staticmethod
    def depuis_dict(d):
        return Ingredient(d["identifiant"], d["nom"], d["unite"], d["stock"], d["seuil_alerte"])


# ---------------------------------------------------------------------------
# PRODUIT (avec sa recette)
# ---------------------------------------------------------------------------
class Produit:
    """Un produit vendu. Sa recette indique la quantité de chaque ingrédient
    nécessaire pour fabriquer UNE unité : {identifiant_ingredient: quantité}."""

    def __init__(self, identifiant, nom, prix, recette):
        self.identifiant = identifiant
        self.nom = nom
        self._prix = 0
        self.prix = prix
        self.recette = dict(recette)

    @property
    def prix(self):
        return self._prix

    @prix.setter
    def prix(self, valeur):
        if valeur <= 0:
            raise ErreurCafeteria("Le prix doit être strictement positif.")
        self._prix = valeur

    def vers_dict(self):
        return {
            "identifiant": self.identifiant,
            "nom": self.nom,
            "prix": self._prix,
            "recette": {str(i): q for i, q in self.recette.items()},
        }

    @staticmethod
    def depuis_dict(d):
        recette = {int(i): q for i, q in d["recette"].items()}
        return Produit(d["identifiant"], d["nom"], d["prix"], recette)


# ---------------------------------------------------------------------------
# CLIENTS : classe mère + deux classes filles (héritage)
# ---------------------------------------------------------------------------
class Client:
    """Classe mère : un client sans remise."""

    type_client = "client"

    def __init__(self, identifiant, nom):
        self.identifiant = identifiant
        self.nom = nom

    def calculer_prix(self, montant):
        """Prix à payer pour un montant donné (ici : aucune remise)."""
        return round(montant, 2)

    def description_tarif(self):
        return "aucune remise"

    def vers_dict(self):
        return {"type": self.type_client, "identifiant": self.identifiant, "nom": self.nom}


class Etudiant(Client):
    """Les étudiants ont 20 % de remise."""

    type_client = "etudiant"

    def calculer_prix(self, montant):  # redéfinition de la méthode
        return round(montant * 0.80, 2)

    def description_tarif(self):
        return "20 % de remise"


class Personnel(Client):
    """Le personnel a 5 % de remise, et 10 % si le montant atteint 500."""

    type_client = "personnel"

    def calculer_prix(self, montant):  # redéfinition de la méthode
        taux = 0.10 if montant >= 500 else 0.05
        return round(montant * (1 - taux), 2)

    def description_tarif(self):
        return "5 % de remise (10 % dès 500)"


def client_depuis_dict(d):
    """Recrée le bon type de client (Etudiant, Personnel...) à partir du JSON."""
    classes = {"client": Client, "etudiant": Etudiant, "personnel": Personnel}
    if d["type"] not in classes:
        raise ValueError(f"Type de client inconnu : {d['type']}")
    return classes[d["type"]](d["identifiant"], d["nom"])


# ---------------------------------------------------------------------------
# COMMANDE
# ---------------------------------------------------------------------------
class Commande:
    """Une commande : plusieurs produits pour un client, avec un statut."""

    def __init__(self, identifiant, client_id, lignes=None, statut="brouillon",
                 total=0.0, besoins_debites=None, date=None):
        if statut not in TRANSITIONS:
            raise ErreurCafeteria(f"Statut inconnu : {statut}")
        self.identifiant = identifiant
        self.client_id = client_id
        self.lignes = dict(lignes) if lignes else {}   # {identifiant_produit: quantité}
        self._statut = statut                          # attribut protégé
        self.total = total                             # total figé à la validation
        # Quantités d'ingrédients réellement débitées à la validation.
        # Elles servent à recréditer le stock exactement si on annule.
        self.besoins_debites = dict(besoins_debites) if besoins_debites else {}
        self.date = date or maintenant()

    @property
    def statut(self):
        return self._statut

    def changer_statut(self, nouveau):
        """Change le statut seulement si le passage est autorisé."""
        if nouveau not in TRANSITIONS[self._statut]:
            raise ErreurCafeteria(
                f"Passage impossible de '{self._statut}' à '{nouveau}'.")
        self._statut = nouveau

    def _verifier_modifiable(self):
        if self._statut != "brouillon":
            raise ErreurCafeteria(
                f"La commande n°{self.identifiant} n'est plus modifiable "
                f"(statut : {self._statut}).")

    def ajouter_produit(self, produit_id, quantite):
        self._verifier_modifiable()
        if quantite <= 0:
            raise ErreurCafeteria("La quantité doit être positive.")
        self.lignes[produit_id] = self.lignes.get(produit_id, 0) + quantite

    def retirer_produit(self, produit_id, quantite=None):
        """Retire une quantité (ou tout le produit si quantite vaut None)."""
        self._verifier_modifiable()
        if produit_id not in self.lignes:
            raise ErreurCafeteria("Ce produit n'est pas dans la commande.")
        if quantite is None or quantite == self.lignes[produit_id]:
            del self.lignes[produit_id]
        elif quantite > self.lignes[produit_id]:
            raise ErreurCafeteria(
                f"Impossible de retirer {quantite} : il n'y en a que {self.lignes[produit_id]}.")
        else:
            self.lignes[produit_id] -= quantite

    def vers_dict(self):
        return {
            "identifiant": self.identifiant,
            "client_id": self.client_id,
            "lignes": {str(p): q for p, q in self.lignes.items()},
            "statut": self._statut,
            "total": self.total,
            "besoins_debites": {str(i): q for i, q in self.besoins_debites.items()},
            "date": self.date,
        }

    @staticmethod
    def depuis_dict(d):
        return Commande(
            d["identifiant"],
            d["client_id"],
            {int(p): q for p, q in d["lignes"].items()},
            d["statut"],
            d["total"],
            {int(i): q for i, q in d["besoins_debites"].items()},
            d["date"],
        )