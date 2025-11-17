from PIL import Image, ImageDraw, ImageFont
import requests
from bs4 import BeautifulSoup
import textwrap
import os
import subprocess

BLOG_URL = "https://www.zama.org/blog"

def fetch_blog():
    print(f"Fetching: {BLOG_URL}")
    r = requests.get(BLOG_URL)
    soup = BeautifulSoup(r.text, "html.parser")

    blocks = soup.find_all(["h1", "h2", "p"])
    content = []

    for b in blocks:
        text = b.get_text().strip()
        if len(text) > 5:
            content.append(text)

    print(f"Extracted {len(content)} blocks.")
    return content[:9]

def create_slide(text, slide_no, logo_path):
    W, H = 1280, 720
    img = Image.new("RGB", (W, H), (12, 12, 12))
    draw = ImageDraw.Draw(img)

    title_font = ImageFont.truetype("DejaVuSans-Bold.ttf", 55)
    body_font = ImageFont.truetype("DejaVuSans.ttf", 40)

    # Wrap text
    wrapper = textwrap.TextWrapper(width=30)
    lines = wrapper.wrap(text=text)

    # Draw text
    y = 170
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=body_font)
        w = bbox[2] - bbox[0]

        draw.text(((W - w) / 2, y), line, fill="white", font=body_font)
        y += 60

    # Slide number bottom-right
    draw.text((1150, 650), f"{slide_no}", fill="white", font=body_font)

    # Logo top-right
    logo = Image.open(logo_path).resize((140, 140))
    img.paste(logo, (W - 170, 20), mask=logo.convert("RGBA"))

    out = f"slide_{slide_no}.png"
    img.save(out)
    return out

def text_to_audio(lines):
    txt = " ".join(lines)
    with open("voice.txt", "w") as f:
        f.write(txt)

    os.system("espeak -f voice.txt -w voice.wav --stdout | ffmpeg -i - -af 'volume=1.3,highpass=120,lowpass=6500,dynaudnorm' voice_fixed.wav")

def generate_video():
    slides = sorted([f for f in os.listdir() if f.startswith("slide_") and f.endswith(".png")])

    with open("slides.txt", "w") as f:
        for s in slides:
            f.write(f"file {s}\n")
            f.write("duration 2.5\n")

    cmd = (
        "ffmpeg -y -f concat -safe 0 -i slides.txt -i voice_fixed.wav "
        "-vf scale=1280:720 -preset veryfast -shortest zama_final.mp4"
    )
    os.system(cmd)

def main():
    if not os.path.exists("logo.png"):
        print("ERROR: logo.png missing")
        exit(1)

    blocks = fetch_blog()
    slides = []

    for i, t in enumerate(blocks):
        sfile = create_slide(t, i + 1, "logo.png")
        slides.append(sfile)

    text_to_audio(blocks)
    generate_video()
    print("Video Generated!")

if __name__ == "__main__":
    main()
