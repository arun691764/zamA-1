#!/usr/bin/env python3
"""
Improved Zama explainer video generator (free TTS -> enhanced audio + logo + Season 4 + moving credit).
Usage: python zama_video_improved.py --url "https://www.zama.org/blog" --output zama_final.mp4
Put a file named logo.png in repo root for logo overlay.
"""

import os, sys, requests, textwrap, subprocess, tempfile
from bs4 import BeautifulSoup
from PIL import Image, ImageDraw, ImageFont
from gtts import gTTS

# ---------- Settings ----------
URL_DEFAULT = "https://www.zama.org/blog"
IMG_W, IMG_H = 1920, 1080
MARGIN = 120
BG_COLOR = (11, 18, 32)
TEXT_COLOR = (255, 255, 255)
TITLE_FONT_SIZE = 64
BODY_FONT_SIZE = 44
MAX_WORDS_PER_SLIDE = 40
SLIDE_DURATION = 6
FONT_PATHS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
]

LOGO_FILENAME = "logo.png"
CREDIT_TEXT = "Created by my X handle - @AmitKum955"
SEASON_TEXT = "Season 4"

# ---------- Font Helper ----------
def choose_font(size):
    for p in FONT_PATHS:
        if os.path.exists(p):
            return ImageFont.truetype(p, size=size)
    return ImageFont.load_default()

# ---------- Fetch Blog Text ----------
def fetch_page_text(url):
    print("Fetching:", url)
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    blocks = []
    for tag in soup.find_all(["h1", "h2", "h3", "p", "li"]):
        text = tag.get_text(" ", strip=True)
        if text and len(text) > 40:
            blocks.append(text)

    seen, cleaned = set(), []
    for t in blocks:
        k = t.lower()
        if k not in seen:
            cleaned.append(t)
            seen.add(k)
    print(f"Extracted {len(cleaned)} blocks.")
    return cleaned

# ---------- Group into Slides ----------
def group_slides(blocks):
    slides = []
    buf, count = [], 0

    for blk in blocks:
        words = blk.split()
        if count + len(words) <= MAX_WORDS_PER_SLIDE:
            buf.append(blk)
            count += len(words)
        else:
            slides.append(" ".join(buf))
            buf, count = [blk], len(words)

    if buf:
        slides.append(" ".join(buf))

    print(f"Built {len(slides)} slides.")
    return slides

# ---------- Render Slide ----------
def render_slide(text, idx, outdir, logo_path):
    title_font = choose_font(TITLE_FONT_SIZE)
    body_font = choose_font(BODY_FONT_SIZE)

    img = Image.new("RGB", (IMG_W, IMG_H), BG_COLOR)
    draw = ImageDraw.Draw(img)

    # Season 4 badge top-left
    badge_x, badge_y = MARGIN, 25
    bw, bh = 260, 60
    draw.rectangle([badge_x, badge_y, badge_x+bw, badge_y+bh], fill=(220, 50, 50))
    draw.text((badge_x+15, badge_y+12), SEASON_TEXT, fill=(255,255,255), font=choose_font(32))

    # Title
    y = badge_y + bh + 40
    draw.text((MARGIN, y), "Zama — Explained", fill=TEXT_COLOR, font=title_font)
    y += TITLE_FONT_SIZE + 30

    # Body text
    lines = textwrap.wrap(text, width=44)
    if len(lines) > 12:
        body_font = choose_font(36)

    for line in lines:
        draw.text((MARGIN, y), line, fill=TEXT_COLOR, font=body_font)
        y += body_font.getsize(line)[1] + 8
        if y > IMG_H - MARGIN - 80:
            break

    # Logo top-right
    if logo_path and os.path.exists(logo_path):
        try:
            logo = Image.open(logo_path).convert("RGBA")
            max_w = 200
            w, h = logo.size
            ratio = min(max_w / w, 1.0)
            logo = logo.resize((int(w*ratio), int(h*ratio)), Image.ANTIALIAS)
            img.paste(logo, (IMG_W - logo.size[0] - 40, 25), logo)
        except Exception as e:
            print("Logo load failed:", e)

    # Moving credit (position changes)
    positions = [
        (MARGIN, IMG_H - 90),
        (IMG_W//2 - 300, IMG_H - 90),
        (IMG_W - 600, IMG_H - 90),
        (MARGIN, IMG_H - 150),
    ]
    cx, cy = positions[idx % len(positions)]
    draw.text((cx, cy), CREDIT_TEXT, fill=(190,190,190), font=choose_font(28))

    outpath = os.path.join(outdir, f"slide_{idx:03d}.png")
    img.save(outpath)
    return outpath

# ---------- TTS + Audio Enhancement ----------
def generate_audio(text, out_audio):
    raw = out_audio + ".raw.mp3"
    gTTS(text, lang="en").save(raw)

    filters = (
        "volume=1.3,"
        "highpass=f=120,"
        "lowpass=f=6500,"
        "dynaudnorm=f=150:g=15,"
        "aresample=44100"
    )

    subprocess.run([
        "ffmpeg", "-y", "-i", raw,
        "-af", filters,
        out_audio
    ], check=True)

    os.remove(raw)

# ---------- Make video ----------
def make_video(slides, audio, output):
    work = tempfile.mkdtemp()
    listfile = os.path.join(work, "list.txt")

    with open(listfile, "w") as f:
        for s in slides:
            f.write(f"file '{s}'\n")
            f.write(f"duration {SLIDE_DURATION}\n")
        f.write(f"file '{slides[-1]}'\n")

    tmp = os.path.join(work, "tmp.mp4")

    subprocess.run([
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", listfile,
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        tmp
    ], check=True)

    subprocess.run([
        "ffmpeg", "-y",
        "-i", tmp, "-i", audio,
        "-c:v", "copy", "-c:a", "aac",
        "-shortest", output
    ], check=True)

# ---------- MAIN ----------
def main():
    blocks = fetch_page_text(URL_DEFAULT)
    slides = group_slides(blocks)

    work = tempfile.mkdtemp()
    logo_path = LOGO_FILENAME if os.path.exists(LOGO_FILENAME) else None

    slide_paths = []
    for i, s in enumerate(slides, 1):
        slide_paths.append(render_slide(s, i, work, logo_path))

    short_text = " ".join(slides[:10])
    audio = os.path.join(work, "voice.mp3")
    generate_audio(short_text, audio)

    make_video(slide_paths, audio, "zama_final.mp4")
    print("DONE: zama_final.mp4")

if __name__ == "__main__":
    main()
