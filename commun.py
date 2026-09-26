"""Fonctions communes à tous les sites surveillés : alerte Discord,
mémoire (etat.json), lecture du stock exact sur une fiche produit."""
import json
import os
import sys
from pathlib import Path

import requests
from bs4 import BeautifulSoup

WEBHOOK = os.environ.get("DISCORD_WEBHOOK", "")
ETAT = Path("etat.json")
HEADERS = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) Chrome/124.0 Safari/537.36"}


def charger_etat():
    """Lit etat.json. Si absent, vide ou corrompu, repart de zéro (comme au
    tout premier passage) plutôt que de planter."""
    if not ETAT.exists():
        return None
    try:
        contenu = ETAT.read_text().strip()
        if not contenu:
            print("[ATTENTION] etat.json est vide, on repart de zéro (pas d'alerte ce passage-ci).")
            return None
        return json.loads(contenu)
    except json.JSONDecodeError as e:
        print(f"[ATTENTION] etat.json corrompu ({e}), on repart de zéro (pas d'alerte ce passage-ci).")
        return None


def sauvegarder_etat(etat):
    ETAT.write_text(json.dumps(etat, ensure_ascii=False, indent=2))


def alerter(message):
    print(message)
    if WEBHOOK:
        requests.post(WEBHOOK, json={"content": message}, timeout=30)


def lire_quantite_max_woocommerce(url_produit):
    """Aide réutilisable pour les sites WooCommerce qui exposent le stock via
    l'attribut max du champ quantité de la fiche produit (ex. lechoppedeslegendes.fr).
    NE CONVIENT PAS À TOUS LES SITES : chaque module de site (site_xxx.py)
    doit fournir sa propre fonction lire_quantite(url), qui peut soit appeler
    celle-ci, soit lire le stock autrement (ex. affiché directement en texte,
    comme sur cartesplus.fr). Retourne un entier, ou None si introuvable."""
    try:
        r = requests.get(url_produit, headers=HEADERS, timeout=30)
        r.raise_for_status()
        soupe = BeautifulSoup(r.text, "html.parser")
        champ = soupe.select_one("input[name='quantity']")
        if champ and champ.get("max"):
            return int(champ["max"])
    except Exception as e:
        print(f"[ERREUR] lecture quantité sur {url_produit} : {e}", file=sys.stderr)
    return None
