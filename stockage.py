"""
stockage.py
-----------
Sauvegarde et chargement des données dans un fichier JSON.
"""

import json
import os

from gestion import Cafeteria
from modeles import ErreurCafeteria


class ErreurFichier(Exception):
    """Le fichier JSON existe mais son contenu est invalide."""


def sauvegarder(cafeteria, chemin):
    """Écrit d'abord dans un fichier temporaire, puis le remplace d'un coup.
    Ainsi, si le programme s'arrête pendant l'écriture, l'ancien fichier reste intact."""
    donnees = cafeteria.vers_dict()
    chemin_temporaire = chemin + ".tmp"
    with open(chemin_temporaire, "w", encoding="utf-8") as fichier:
        json.dump(donnees, fichier, ensure_ascii=False, indent=2)
    os.replace(chemin_temporaire, chemin)


def charger(chemin):
    """Retourne une Cafeteria.
    - Fichier absent (premier lancement) : retourne une cafétéria vide.
    - Fichier invalide : lève ErreurFichier SANS toucher au fichier.""
    if not os.path.exists(chemin):
        return Cafeteria()
    try:
        with open(chemin, "r", encoding="utf-8") as fichier:
            donnees = json.load(fichier)
        return Cafeteria.depuis_dict(donnees)
    except (OSError, ValueError, KeyError, TypeError, AttributeError, ErreurCafeteria) as erreur:
        raise ErreurFichier(f"{type(erreur).__name__} : {erreur}")
