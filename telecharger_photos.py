#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Télécharge les photos des monuments marocains reproduits dans le monde.
Usage : python telecharger_photos.py
"""

import time
from pathlib import Path
import requests

# ----------------------------------------------------------------------
# CONFIGURATION
# ----------------------------------------------------------------------
DOSSIER_IMAGES = Path("images")
TIMEOUT = 30  # secondes
DELAI_ENTRE_TELECHARGEMENTS = 2  # secondes
MAX_TENTATIVES = 4
# Wikimedia exige un User-Agent descriptif (pas un faux navigateur)
USER_AGENT = "MonumentsMarocCarrousel/1.0 (script personnel de telechargement d'images)"

# Dictionnaire : nom de fichier local -> URL directe de l'image
# Les URLs Wikimedia Commons pointent vers les fichiers originaux (haute résolution).
IMAGES = {
    # Giralda de Séville (Wikimedia Commons)
    "giralda.jpg": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/44/Giralda%2C_Sevilla%2C_Espa%C3%B1a%2C_2015-12-06%2C_DD_92.JPG/1280px-Giralda%2C_Sevilla%2C_Espa%C3%B1a%2C_2015-12-06%2C_DD_92.JPG",

    # Madison Square Garden (1890) - Wikimedia Commons (image d'archive)
    # Note : l'URL exacte peut varier ; on utilise une image de la catégorie Commons.
    "msg_1890.jpg": "https://upload.wikimedia.org/wikipedia/commons/4/44/Madison-square2.jpg",

    # Pavillon du Maroc à Epcot (Wikimedia Commons)
    "epcot_maroc.jpg": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d4/Epcot_Maroco1.JPG/1280px-Epcot_Maroco1.JPG",

    # Mosquée maure de Kapurthala (Wikimedia Commons)
    "kapurthala.jpg": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/28/Moorish_Mosque.JPG/1280px-Moorish_Mosque.JPG",

    # Mezquita de Coquimbo (Wikimedia Commons)
    # URL construite à partir du nom de fichier ; si elle échoue, on pourra utiliser une miniature.
    "coquimbo.jpg": "https://thumb.wikimedia.org/wikipedia/commons/thumb/c/c1/Mezquita_Musulmana_Coquimbo.JPG/1280px-Mezquita_Musulmana_Coquimbo.JPG",

    # Porte du Maroc au Vietnam (pas de fichier Wikimedia Commons fiable)
    # On utilise une image d'illustration issue d'un article de presse.
    # Tu peux remplacer cette URL par une photo personnelle si tu en as une.
    "vietnam.jpg": "https://vietnamtimes.thoidai.com.vn/uploads/image/2018/11/13/morocco-gate.jpg",
}

# ----------------------------------------------------------------------
# FONCTIONS
# ----------------------------------------------------------------------
def verifier_et_creer_dossier():
    """Crée le dossier 'images' s'il n'existe pas."""
    DOSSIER_IMAGES.mkdir(exist_ok=True)
    print(f"📁 Dossier de destination : {DOSSIER_IMAGES.resolve()}")


def telecharger_image(url, chemin_destination):
    """
    Télécharge une image depuis une URL et l'enregistre localement.
    Retourne True si succès, False sinon.
    """
    try:
        headers = {"User-Agent": USER_AGENT}
        reponse = None
        for tentative in range(1, MAX_TENTATIVES + 1):
            reponse = requests.get(url, headers=headers, timeout=TIMEOUT, stream=True)
            if reponse.status_code != 429:
                break
            # Respecte Retry-After s'il est fourni, sinon backoff exponentiel
            try:
                attente = int(reponse.headers.get("Retry-After", ""))
            except ValueError:
                attente = 5 * 2 ** (tentative - 1)
            attente = min(attente, 120)
            print(f"   ⏳ 429 reçu, nouvelle tentative {tentative}/{MAX_TENTATIVES} dans {attente}s...")
            reponse.close()
            time.sleep(attente)
        reponse.raise_for_status()  # Lève une exception pour les codes 4xx/5xx

        # Vérifier que le contenu est bien une image (type MIME)
        content_type = reponse.headers.get("Content-Type", "")
        if not content_type.startswith("image/"):
            print(f"   ⚠️  Le lien ne renvoie pas une image (Content-Type: {content_type})")
            return False

        # Écriture du fichier par blocs (utile pour les gros fichiers)
        with open(chemin_destination, "wb") as fichier:
            for bloc in reponse.iter_content(chunk_size=8192):
                if bloc:
                    fichier.write(bloc)

        # Vérification finale : le fichier existe et n'est pas vide
        if chemin_destination.exists() and chemin_destination.stat().st_size > 0:
            taille_ko = chemin_destination.stat().st_size / 1024
            print(f"   ✅ Téléchargé : {chemin_destination.name} ({taille_ko:.1f} Ko)")
            return True
        else:
            print(f"   ⚠️  Fichier vide ou introuvable : {chemin_destination.name}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"   ❌ Erreur réseau pour {chemin_destination.name} : {e}")
        return False
    except Exception as e:
        print(f"   ❌ Erreur inattendue pour {chemin_destination.name} : {e}")
        return False


# ----------------------------------------------------------------------
# PROGRAMME PRINCIPAL
# ----------------------------------------------------------------------
def main():
    verifier_et_creer_dossier()

    print(f"\n🚀 Début du téléchargement de {len(IMAGES)} images...\n")

    succes = 0
    echecs = 0

    for i, (nom_fichier, url) in enumerate(IMAGES.items()):
        if i > 0:
            time.sleep(DELAI_ENTRE_TELECHARGEMENTS)
        chemin_destination = DOSSIER_IMAGES / nom_fichier
        print(f"📥 Téléchargement de {nom_fichier}...")

        if telecharger_image(url, chemin_destination):
            succes += 1
        else:
            echecs += 1
            print(f"   🔗 URL source : {url}\n")

    # Bilan final
    print("\n" + "=" * 50)
    print(f"📊 Bilan : {succes} image(s) téléchargée(s) avec succès, {echecs} échec(s).")
    if echecs > 0:
        print("   💡 Si certaines URLs ne fonctionnent plus, tu peux les remplacer")
        print("      manuellement dans le dictionnaire IMAGES du script.")
        print("      Pour Wikimedia Commons, clique sur « Original file » sur la page")
        print("      du fichier pour obtenir l'URL directe.")
    print("=" * 50)


if __name__ == "__main__":
    main()