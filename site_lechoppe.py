"""Lecture de lechoppedeslegendes.fr : catégorie paginée, filtrée sur Pokémon."""
import sys

import requests
from bs4 import BeautifulSoup

from commun import HEADERS, lire_quantite_max_woocommerce

# ---- À MODIFIER -------------------------------------------------------------
PAGES = [
    "https://www.lechoppedeslegendes.fr/categorie-produit/jeux/cartes-a-collectionner/",
]
# Mots-clés (en minuscules). IMPORTANT sur une page qui mélange plusieurs
# jeux (comme "Cartes/TCG") : sans mot-clé, vous seriez alerté sur tout,
# Pokémon compris mais aussi Magic, Yu-Gi-Oh, etc.
MOTS_CLES = ["pokemon", "pokémon","one piece"]
# Nombre maximum de pages à parcourir par catégorie (sécurité anti-boucle infinie).
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
        lien = li.select_one("a[href*='/produit/']")
        titre = li.select_one("h2, h3")
        if not lien or not titre:
            continue
        texte = li.get_text(" ", strip=True).lower()
        a_bouton_panier = li.select_one("a[href*='add-to-cart']") is not None
        en_stock = a_bouton_panier and "non disponible" not in texte
        prix = li.select_one(".price")
        produits[lien["href"]] = {
            "nom": titre.get_text(" ", strip=True),
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
    """Point d'entrée appelé par monitor.py : lit toutes les pages configurées
    pour ce site et ne garde que les produits filtrés par MOTS_CLES."""
    produits = {}
    for page in PAGES:
        produits.update(lire_categorie(page))
    return {url: p for url, p in produits.items() if garder(p["nom"])}


def lire_quantite(url_produit):
    """Stock exact pour ce site : lechoppedeslegendes.fr expose le stock via
    l'attribut max du champ quantité (méthode WooCommerce standard)."""
    return lire_quantite_max_woocommerce(url_produit)
