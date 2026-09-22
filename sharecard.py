#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Draw icons/share.png — the picture that shows up when the link is texted.

Its numbers are read out of the built page, so they can never drift from what
the app actually holds. build.py calls this at the end of every build; it is
skipped with a printed note if Pillow is not installed, because a missing
picture must never fail a build.

    python3 sharecard.py
"""
import json, os, re, sys

try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass

W, H = 1200, 630
OUT = os.path.join("icons", "share.png")


def totals():
    s = open("index.html", encoding="utf-8").read()
    m = re.search(r"const DATA = (\{.*?\});\n", s, re.S)
    t = json.loads(m.group(1))["totals"] if m else {}
    return t


def font(size, bold=False):
    from PIL import ImageFont
    for name in (("arialbd.ttf" if bold else "arial.ttf"),
                 ("seguisb.ttf" if bold else "segoeui.ttf"),
                 ("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf")):
        p = os.path.join("C:", os.sep, "Windows", "Fonts", name)
        if os.path.exists(p):
            try: return ImageFont.truetype(p, size)
            except Exception: pass
    return ImageFont.load_default()


def main():
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        print("sharecard: Pillow is not installed, icons/share.png left as it is")
        return

    T = totals()
    card = Image.new("RGB", (W, H), "#0c0c0e")
    d = ImageDraw.Draw(card)
    d.rectangle([0, H - 14, W, H], fill="#1e7a3a")

    logo = Image.open(os.path.join("icons", "logo.png")).convert("RGBA")
    lw = 760
    lh = round(logo.height * lw / logo.width)
    logo = logo.resize((lw, lh), Image.LANCZOS)
    card.paste(logo, ((W - lw) // 2, 92), logo)

    def centre(txt, y, f, fill):
        d.text(((W - d.textbbox((0, 0), txt, font=f)[2]) // 2, y), txt, font=f, fill=fill)

    def n(x): return f"{x:,}" if isinstance(x, int) else str(x)

    centre("a WATTZ LED crew page", 92 + lh + 6, font(30), "#8a8f96")
    centre("Every Mike Holt video and every quiz in the", 92 + lh + 64, font(40, True), "#ffffff")
    centre("2023 Journeyman program, in one place, in order.", 92 + lh + 116, font(40, True), "#ffffff")
    centre(f"{n(T.get('videos', 0))} videos  ·  {n(T.get('hours', 0))} hours  ·  "
           f"{n(T.get('books', 0))} books  ·  {n(T.get('quizzes', 0))} quizzes  ·  "
           f"{n(T.get('questions', 0))} questions", H - 96, font(31), "#e0b400")

    card.save(OUT, optimize=True)
    print(f"{OUT} redrawn from the built page ({os.path.getsize(OUT)} bytes)")


if __name__ == "__main__":
    main()
