"""Veille coffrets Pokémon : alerte Discord sur nouvelle fiche ou retour en stock."""
import json
import os
import sys
from pathlib import Path

import requests
from bs4 import BeautifulSoup

# ---- À MODIFIER -------------------------------------------------------------
PAGES = [
    "https://www.lechoppedeslegendes.fr/categorie-produit/jeux/cartes-a-collectionner/pokemon/",
    # Étape 2 : à tester ensuite (le site peut bloquer le script) :
    # "https://cartesplus.fr/categorie-produit/pokemon/pokemon-produits-neuf/",
]
# Mots-clés (en minuscules). Liste vide = tous les produits de la page.
MOTS_CLES = []  # exemple : ["ultra-premium", "display", "mentali"]
# -----------------------------------------------------------------------------

WEBHOOK = os.environ.get("DISCORD_WEBHOOK", "")
ETAT = Path("etat.json")
HEADERS = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) Chrome/124.0 Safari/537.36"}


def lire_page(url):
    """Retourne {url_produit: {"nom": ..., "prix": ..., "en_stock": bool}}."""
    r = requests.get(url, headers=HEADERS, timeout=30)
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


def garder(nom):
    return not MOTS_CLES or any(m in nom.lower() for m in MOTS_CLES)


def alerter(message):
    print(message)
    if WEBHOOK:
        requests.post(WEBHOOK, json={"content": message}, timeout=30)


def main():
    ancien = json.loads(ETAT.read_text()) if ETAT.exists() else None
    nouveau = dict(ancien or {})
    for page in PAGES:
        try:
            produits = lire_page(page)
        except Exception as e:  # site bloqué, panne, etc. : on continue
            print(f"[ERREUR] {page} : {e}", file=sys.stderr)
            continue
        if not produits:
            print(f"[ATTENTION] aucun produit lu sur {page} (structure changée ou blocage ?)")
        for url, p in produits.items():
            if not garder(p["nom"]):
                continue
            avant = (ancien or {}).get(url)
            if ancien is not None:  # pas d'alerte au tout premier passage
                if avant is None:
                    alerter(f"🆕 Nouvelle fiche : **{p['nom']}** ({p['prix']})\n{url}")
                elif p["en_stock"] and not avant["en_stock"]:
                    alerter(f"✅ De retour en stock : **{p['nom']}** ({p['prix']})\n{url}")
            nouveau[url] = p
    ETAT.write_text(json.dumps(nouveau, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
