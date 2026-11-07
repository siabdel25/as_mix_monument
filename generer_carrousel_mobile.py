#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Générateur carrousel vidéo 9:16 pour WhatsApp / Snapchat, avec musique MP3.
Usage :
  python generer_carrousel_mobile.py                           # sans musique
  python generer_carrousel_mobile.py --music musique.mp3       # avec musique
  python generer_carrousel_mobile.py -m musique.mp3 --volume 0.6
  python generer_carrousel_mobile.py -m musique.mp3 -o sortie.mp4 --fade-in 1.5 --fade-out 3
"""

import argparse
import os
import subprocess
import textwrap
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# ----------------------------------------------------------------------
# CONFIGURATION PAR DÉFAUT (modifiable via CLI)
# ----------------------------------------------------------------------
LARGEUR, HAUTEUR = 1080, 1920
DUREE_PAR_SLIDE = 2.5
TRANSITION_DUREE = 0.8
FPS = 30
CRF = 24
PRESET = "medium"
DOSSIER_IMAGES = Path("images")
DOSSIER_TEMP = Path("temp_slides")
FICHIER_SORTIE_DEFAUT = Path("carrousel_whatsapp_snapchat.mp4")

# Audio
VOLUME_DEFAUT = 0.8        # 0.0 à 1.0
FADE_IN_DEFAUT = 1.0       # secondes
FADE_OUT_DEFAUT = 2.0      # secondes

MONUMENTS = [
    {"titre": "[ES] Giralda, Séville", "sous_titre": "La sœur de la Koutoubia (1184)",
     "description": "Inspirée du minaret almohade de Marrakech,\nelle forme les « trois tours sœurs » avec\nla Koutoubia et la Tour Hassan.",
     "fichier": "giralda.jpg"},
    {"titre": "[US] Madison Square Garden", "sous_titre": "Un minaret à Manhattan (1890)",
     "description": "Réplique de la Giralda de Séville,\nelle-même copie de la Koutoubia.\n148 mètres de style almohade.",
     "fichier": "msg_1890.jpg"},
    {"titre": "[US] Pavillon du Maroc, Epcot", "sous_titre": "Floride, Disney World",
     "description": "Réplique de la Koutoubia, de la fontaine\nNejjarine et de Bab Boujeloud.\n19 artisans marocains y ont travaillé.",
     "fichier": "epcot_maroc.jpg"},
    {"titre": "[IN] Kapurthala, Pendjab", "sous_titre": "La Koutoubia en Inde (1930)",
     "description": "Commandée par le Maharaja Jagatjit Singh\naprès un voyage à Marrakech.\nQuasi-réplique de la Koutoubia.",
     "fichier": "kapurthala.jpg"},
    {"titre": "[CL] Koutoubia de Coquimbo", "sous_titre": "Chili, face au Pacifique (2007)",
     "description": "Minaret de 40 mètres, copie fidèle\nde la Koutoubia de Marrakech.\nRéalisé par des artisans de Fès.",
     "fichier": "coquimbo.jpg"},
    {"titre": "[VN] Porte du Maroc, Vietnam", "sous_titre": "Ba Vì, près de Hanoï (1960)",
     "description": "Bâtie par d'anciens soldats marocains.\nInspirée de Bab Mansour ou Bab Boujloud.\nRénovée en 2018.",
     "fichier": "vietnam.jpg"},
]

# ----------------------------------------------------------------------
# UTILITAIRES IMAGE
# ----------------------------------------------------------------------
def preparer_dossiers():
    DOSSIER_TEMP.mkdir(exist_ok=True)

def trouver_police(taille):
    for chemin in [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ]:
        if os.path.exists(chemin):
            return ImageFont.truetype(chemin, taille)
    return ImageFont.load_default()

def recadrer_9_16(img):
    ratio_cible = LARGEUR / HAUTEUR
    ratio_img = img.width / img.height
    resample = Image.Resampling.LANCZOS if hasattr(Image, "Resampling") else Image.LANCZOS
    if ratio_img > ratio_cible:
        nw = int(HAUTEUR * ratio_img)
        img = img.resize((nw, HAUTEUR), resample)
        d = (nw - LARGEUR) // 2
        img = img.crop((d, 0, d + LARGEUR, HAUTEUR))
    else:
        nh = int(LARGEUR / ratio_img)
        img = img.resize((LARGEUR, nh), resample)
        d = (nh - HAUTEUR) // 2
        img = img.crop((0, d, LARGEUR, d + HAUTEUR))
    return img

def creer_slide(src, dst, titre, sous_titre, description):
    img = recadrer_9_16(Image.open(src).convert("RGBA"))
    degrade = Image.new("RGBA", (LARGEUR, HAUTEUR), (0, 0, 0, 0))
    p = ImageDraw.Draw(degrade)
    hd = 600
    for y in range(hd):
        a = int(210 * (y / hd))
        p.line([(0, HAUTEUR - hd + y), (LARGEUR, HAUTEUR - hd + y)], fill=(0, 0, 0, a))
    img = Image.alpha_composite(img, degrade)

    d = ImageDraw.Draw(img)
    pt, pst, pd = trouver_police(52), trouver_police(38), trouver_police(30)
    mg = 60
    y = HAUTEUR - 560
    d.text((mg, y), titre, font=pt, fill=(255, 255, 255, 255)); y += 72
    d.text((mg, y), sous_titre, font=pst, fill=(255, 225, 140, 255)); y += 90
    for ligne in description.split("\n"):
        for l in textwrap.wrap(ligne, width=36):
            d.text((mg, y), l, font=pd, fill=(235, 235, 235, 255)); y += 40
    img.convert("RGB").save(dst, quality=92)

def creer_clip(src, dst, duree):
    n_frames = int(duree * FPS)
    vf = (
        f"scale=1440:-1,"
        f"zoompan=z='min(zoom+0.0006,1.10)':d={n_frames}:s={LARGEUR}x{HAUTEUR}:fps={FPS},"
        f"setpts=PTS-STARTPTS"
    )
    subprocess.run([
        "ffmpeg", "-y", "-i", str(src),
        "-vf", vf,
        "-c:v", "libx264", "-profile:v", "main", "-level", "4.0",
        "-preset", PRESET, "-crf", str(CRF), "-pix_fmt", "yuv420p",
        "-an", str(dst),
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)

# ----------------------------------------------------------------------
# ASSEMBLAGE VIDÉO + AUDIO
# ----------------------------------------------------------------------
def assembler(clips, dst, music_path=None, volume=VOLUME_DEFAUT,
              fade_in=FADE_IN_DEFAUT, fade_out=FADE_OUT_DEFAUT):
    n = len(clips)
    duree_totale = n * DUREE_PAR_SLIDE - (n - 1) * TRANSITION_DUREE
    cmd = ["ffmpeg", "-y"]

    # 1. Entrées vidéo
    for c in clips:
        cmd.extend(["-i", str(c)])

    # 2. Entrée audio : bouclée à l'infini pour couvrir la durée totale
    has_music = music_path is not None and Path(music_path).exists()
    if has_music:
        cmd.extend(["-stream_loop", "-1", "-i", str(music_path)])

    # 3. Chaîne de filtres vidéo (inchangée)
    if n == 1:
        # Cas dégénéré : pas de xfade
        vf_complex = "[0:v]format=yuv420p[outv]"
    else:
        filtres = []
        for i in range(n - 1):
            offset = (i + 1) * (DUREE_PAR_SLIDE - TRANSITION_DUREE)
            prev = f"[v{i}]" if i > 0 else "[0:v]"
            filtres.append(
                f"{prev}[{i+1}:v]xfade=transition=fade:duration={TRANSITION_DUREE}:offset={offset}[v{i+1}]"
            )
        vf_complex = ";".join(filtres) + f";[v{n-1}]format=yuv420p[outv]"

    # 4. Chaîne de filtres audio (nouveau)
    if has_music:
        # Sécurité : fade_out ne doit pas dépasser la durée totale
        fo = min(fade_out, duree_totale / 2)
        fi = min(fade_in, duree_totale / 2)
        audio_filter = (
            f"[{n}:a]"
            f"atrim=0:{duree_totale:.3f},asetpts=PTS-STARTPTS,"
            f"volume={volume},"
            f"afade=t=in:st=0:d={fi:.2f},"
            f"afade=t=out:st={duree_totale - fo:.3f}:d={fo:.2f}"
            f"[outa]"
        )
        filter_complex = vf_complex + ";" + audio_filter
    else:
        filter_complex = vf_complex

    cmd.extend(["-filter_complex", filter_complex, "-map", "[outv]"])

    # 5. Encodage vidéo
    cmd.extend([
        "-c:v", "libx264", "-profile:v", "main", "-level", "4.0",
        "-preset", PRESET, "-crf", str(CRF), "-r", str(FPS),
        "-pix_fmt", "yuv420p", "-movflags", "+faststart",
    ])

    # 6. Encodage audio
    if has_music:
        cmd.extend([
            "-map", "[outa]",
            "-c:a", "aac",
            "-b:a", "128k",
            "-ar", "44100",
            "-ac", "2",
            "-t", f"{duree_totale:.3f}",   # coupe pile à la durée vidéo
        ])
    else:
        cmd.extend(["-an"])

    cmd.append(str(dst))
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)

# ----------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------
def parse_args():
    p = argparse.ArgumentParser(
        description="Génère un carrousel vidéo 9:16 pour WhatsApp / Snapchat, avec musique MP3 optionnelle."
    )
    p.add_argument("-m", "--music", type=Path, default=None,
                   help="Chemin vers le fichier MP3 (ou .m4a, .aac, .wav).")
    p.add_argument("-o", "--output", type=Path, default=FICHIER_SORTIE_DEFAUT,
                   help=f"Fichier de sortie (défaut: {FICHIER_SORTIE_DEFAUT}).")
    p.add_argument("--volume", type=float, default=VOLUME_DEFAUT,
                   help=f"Volume audio 0.0-1.0 (défaut: {VOLUME_DEFAUT}).")
    p.add_argument("--fade-in", type=float, default=FADE_IN_DEFAUT,
                   help=f"Fondu d'entrée en secondes (défaut: {FADE_IN_DEFAUT}).")
    p.add_argument("--fade-out", type=float, default=FADE_OUT_DEFAUT,
                   help=f"Fondu de sortie en secondes (défaut: {FADE_OUT_DEFAUT}).")
    p.add_argument("--no-music", action="store_true",
                   help="Force la génération sans audio.")
    return p.parse_args()

# ----------------------------------------------------------------------
# MAIN
# ----------------------------------------------------------------------
def main():
    args = parse_args()

    # Validation musique
    music = None if args.no_music else args.music
    if music is not None:
        if not music.exists():
            raise SystemExit(f"❌ Musique introuvable : {music}")
        if music.suffix.lower() not in {".mp3", ".m4a", ".aac", ".wav", ".ogg", ".flac"}:
            raise SystemExit(f"❌ Format audio non supporté : {music.suffix}")
        print(f"🎵 Musique : {music}")

    preparer_dossiers()
    clips = []

    print("🎬 Génération des slides 9:16...")
    for i, m in enumerate(MONUMENTS, 1):
        src = DOSSIER_IMAGES / m["fichier"]
        if not src.exists():
            print(f"⚠️  Manquant : {src}"); continue
        slide = DOSSIER_TEMP / f"slide_{i:02d}.jpg"
        creer_slide(src, slide, m["titre"], m["sous_titre"], m["description"])
        clip = DOSSIER_TEMP / f"clip_{i:02d}.mp4"
        creer_clip(slide, clip, DUREE_PAR_SLIDE)
        clips.append(clip)
        print(f"   ✅ Slide {i}/{len(MONUMENTS)} : {m['titre']}")

    if not clips:
        raise SystemExit("❌ Aucun clip généré.")

    print("\n🎞️  Assemblage final" + (" + audio..." if music else " (sans audio)..."))
    assembler(
        clips, args.output,
        music_path=music,
        volume=max(0.0, min(1.0, args.volume)),
        fade_in=args.fade_in,
        fade_out=args.fade_out,
    )

    mo = args.output.stat().st_size / (1024 * 1024)
    print(f"\n🎉 {args.output.resolve()}")
    print(f"   📦 {mo:.2f} Mo {'✅ OK (<16 Mo)' if mo <= 16 else '⚠️  >16 Mo : augmente CRF'}")
    if music:
        print(f"   🎵 Audio : AAC 128 kbps, volume {args.volume}, "
              f"fade in {args.fade_in}s / fade out {args.fade_out}s")

if __name__ == "__main__":
    main()