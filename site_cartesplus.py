"""Lecture de cartesplus.fr : catégorie "Pokémon - Produits neufs", paginée."""
import re
import sys

import requests
from bs4 import BeautifulSoup

from commun import HEADERS

# ---- À MODIFIER -------------------------------------------------------------
PAGES = [
    "https://cartesplus.fr/categorie-produit/pokemon/pokemon-produits-neuf/",
]
# Mots-clés (en minuscules). Cette catégorie ne contient déjà que des produits
# Pokémon, donc aucun filtre n'est nécessaire par défaut. Liste vide = tout.
MOTS_CLES = []
# Nombre maximum de pages à parcourir (sécurité anti-boucle infinie).
MAX_PAGES = 20
# -----------------------------------------------------------------------------


def garder(nom):
    return not MOTS_CLES or any(m in nom.lower() for m in MOTS_CLES)


def lire_page_unique(url):
    """Retourne {url_produit: {"nom": ..., "prix": ..., "en_stock": bool}} pour UNE page,
    ou None si la page n'existe pas (404)."""
    r = requests.get(url, headers=HEADERS, timeout=30)
    if r.status_code == 404:
        return None
    r.raise_for_status()
    soupe = BeautifulSoup(r.text, "html.parser")
    produits = {}
    for li in soupe.select("li.product"):
        lien_titre = li.select_one("h3 a")
        if not lien_titre or not lien_titre.get("href"):
            continue
        classes = li.get("class", [])
        # Le statut est directement dans la classe du <li> : "instock" ou "outofstock".
        en_stock = "instock" in classes
        prix = li.select_one(".price")
        produits[lien_titre["href"]] = {
            "nom": lien_titre.get_text(" ", strip=True),
            "prix": prix.get_text(" ", strip=True) if prix else "?",
            "en_stock": en_stock,
        }
    return produits


def lire_categorie(url_base):
    """Parcourt une catégorie sur toutes ses pages (méthode A : /page/2/, /page/3/, ...)."""
    url_base = url_base.rstrip("/") + "/"
    produits = {}
    for num_page in range(1, MAX_PAGES + 1):
        url = url_base if num_page == 1 else f"{url_base}page/{num_page}/"
        page = lire_page_unique(url)
        if page is None or not page:  # 404, ou page vide : fin de la pagination
            break
        produits.update(page)
    return produits


def lire():
    """Point d'entrée appelé par monitor.py."""
    produits = {}
    for page in PAGES:
        produits.update(lire_categorie(page))
    return {url: p for url, p in produits.items() if garder(p["nom"])}


def lire_quantite(url_produit):
    """Stock exact pour ce site : cartesplus.fr affiche le stock en clair sur
    la fiche produit, ex. <p class="stock in-stock">24 en stock</p>."""
    try:
        r = requests.get(url_produit, headers=HEADERS, timeout=30)
        r.raise_for_status()
        soupe = BeautifulSoup(r.text, "html.parser")
        champ = soupe.select_one("p.stock")
        if champ:
            m = re.search(r"(\d+)\s*en stock", champ.get_text(" ", strip=True))
            if m:
                return int(m.group(1))
    except Exception as e:
        print(f"[ERREUR] lecture quantité sur {url_produit} : {e}", file=sys.stderr)
    return None
