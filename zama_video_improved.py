import requests
from bs4 import BeautifulSoup
from PIL import Image, ImageDraw, ImageFont
import os
import subprocess
import random

BLOG_URL = "https://www.zama.ai/blog"
LOGO_PATH = "logo.png"
OUTPUT_VIDEO = "zama_final.mp4"
HANDLE = "@AmitKum955"

# ---------------------------
# Fetch blog text
# ---------------------------
def fetch_blog():
    r = requests.get(BLOG_URL, timeout=10)
    soup = BeautifulSoup(r.text, "html.parser")
    paragraphs = soup.find_all("p")
    text_blocks = [p.text.strip() for p in paragraphs if len(p.text.strip()) > 50]
    return text_blocks[:10]

# ---------------------------
# Create slide images
# ---------------------------
def create_slides(text_blocks):
    slides = []
    font_title = ImageFont.truetype("DejaVuSans.ttf", 48)
    font_body = ImageFont.truetype("DejaVuSans.ttf", 36)
    font_handle = ImageFont.truetype("DejaVuSans.ttf", 32)

    for i, block in enumerate(text_blocks):
        img = Image.new("RGB", (1280, 720), (15, 15, 15))
        draw = ImageDraw.Draw(img)

        # Logo
        if os.path.exists(LOGO_PATH):
            logo = Image.open(LOGO_PATH).resize((140, 140))
            img.paste(logo, (1100, 20))

        draw.text((50, 40), f"Zama — Season 4", font=font_title, fill=(255, 255, 0))

        y = 140
        for line in block.split(". "):
            draw.text((50, y), line.strip(), font=font_body, fill=(255,255,255))
            y += 60

        # Moving X-handle
        xpos = random.randint(50, 900)
        ypos = random.randint(600, 660)
        draw.text((xpos, ypos), f"Created by: {HANDLE}", font=font_handle, fill=(0,255,255))

        fname = f"slide_{i}.png"
        img.save(fname)
        slides.append(fname)

    return slides

# ---------------------------
# Generate audio WITHOUT API
# ---------------------------
def generate_audio(text_blocks):
    full_text = ". ".join(text_blocks)
    with open("tts.txt", "w") as f:
        f.write(full_text)

    cmd = [
        "ffmpeg",
        "-f", "lavfi",
        "-i", "sine=frequency=0:duration=0.1",  # dummy input
        "-f", "lavfi",
        "-i", "aresample=async=1",
        "-f", "lavfi",
        "-i", "anoisesrc=d=0.1",
        "-filter_complex",
        f"flite=textfile='tts.txt':voice='kal16',volume=1.5",
        "voice.wav",
        "-y",
    ]
    subprocess.run(cmd)

    # Improve clarity
    cmd2 = [
        "ffmpeg", "-i", "voice.wav",
        "-af", "highpass=f=150,lowpass=f=5000,volume=1.3",
        "voice_fixed.wav",
        "-y"
    ]
    subprocess.run(cmd2)

# ---------------------------
# Combine into final video
# ---------------------------
def combine(slides):
    with open("slides.txt", "w") as f:
        for s in slides:
            f.write(f"file '{s}'\n")
            f.write("duration 3\n")

    cmd = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", "slides.txt",
        "-i", "voice_fixed.wav",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        OUTPUT_VIDEO
    ]
    subprocess.run(cmd)

# ---------------------------
# Main
# ---------------------------
def main():
    print("Fetching blog text...")
    blocks = fetch_blog()

    print("Creating slides...")
    slides = create_slides(blocks)

    print("Generating audio...")
    generate_audio(blocks)

    print("Combining final video...")
    combine(slides)

    print("VIDEO READY:", OUTPUT_VIDEO)

if __name__ == "__main__":
    main()
