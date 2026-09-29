#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Every NEC section Mike Holt's textbook covers, per video, in book order.

sections.json says where in a video a section is TAUGHT, read off the captions and
the slides, so it only holds what was said out loud. The code book has to be
highlighted from the textbook, which covers more. This reads the textbook itself.

It does not guess from the plain-text dump. It opens the book PDFs and reads the
TYPE: a section heading is set in the heavy face on a coloured bar ("210.4
Multiwire Branch Circuits"), a first-level subsection in bold at the head of its
paragraph ("(A) General."). A citation in the body ("in accordance with
200.4(B)", "[240.15(B)(1)]") is set in the body face, so it can never be taken
for a heading, and a list item such as "(1) A continuous white outer finish." is
not bold, so it is never taken for one either. The text dump (paste2/text-*.json)
lost both the case and the weight, which is why it is not used to build this.
The pages are read left column then right column, top to bottom, because the
PDF's own text order is not reading order and a subsection belongs to the last
section heading ABOVE it on the page, not the last one in the file.

Writes book_sections.json: {video_id: ["210.1", "210.3", "210.4", "210.4(A)", ...]}

    python book_sections.py          # sections + first-level subsections
    python book_sections.py --deep   # also the bold second-level headings, (A)(1)
    python book_sections.py --dry    # report, write nothing

What each kind of video gets:
  an Article video       every section of that article's chapter in its own book,
                         with its (A), (B) ... subsections. A section whose first
                         level is numbered rather than lettered in the book
                         ("400.12 (1) Substitute for Fixed Wiring.") gets its (1),
                         (2) ... instead. The two tables Article 430 prints under
                         their own heading bars are its sections 430.248 and 430.250.
  B&G Article 250        split at Part IV: Part A is 250.1 up to 250.80, Part B is
                         250.80 on. The Part A captions end "we are now moving into
                         Part IV, enclosures, raceways and service cable
                         connections". (The Part B caption file is a byte-for-byte
                         copy of Part A's, so it cannot say where Part B starts.)
  B&G topic videos       "Generator Separately Derived Systems [250.30]": that one
                         section, WITH its bold second-level headings, because for
                         a one-section lesson 250.30(A)(1) through (A)(7) are the
                         lesson. The book teaches 250.30 twice, transformer then
                         generator, and each video gets its own half.
  no list                the Theory, Calculations and Exam Prep videos, the chapter
                         and team introductions, Article 100 (definitions, which
                         have no numbered sections), and Articles 726 and 750,
                         which Volume 2 does not print.

Needs the book PDFs (see pages.py for where they live) and PyMuPDF.
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
# this folder has a fractions.py of its own, which shadows the standard library's
# and breaks PyMuPDF's import of statistics
sys.path = [p for p in sys.path if os.path.abspath(p or ".") != HERE]
import pymupdf  # noqa: E402

try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass

BOOKS = os.path.join("C:", os.sep, "Users", "Kymani", "projects", "jmen", "MikeHolt", "books")
PDF = {
    "NEC Vol 1": "2-understanding-the-nec-vol-1-book.pdf",
    "Bonding & Grounding": "3-bonding-and-grounding-book.pdf",
    "NEC Vol 2": "4-understanding-the-nec-vol-2-book.pdf",
}
SEC = re.compile(r"^(?:Table\s+)?(\d{2,3})\.(\d{1,3})(?!\d)")
LETTER = re.compile(r"^\(([A-Z])\)")
NUMBER = re.compile(r"^\((\d{1,2})\)")
BODY = 0x404041          # the body ink; a bold heading in any other colour is a callout

# Where the book prints a subsection with its section's heading left out. Found by
# the letters starting over inside one section. Page 188 of Volume 1 runs 225.6(B)
# Festoon Lighting straight into "(A) Point of Attachment" and "(B) Means of
# Attachment to Buildings", which are 225.16(A) and (B) in the Code (225.16
# Attachment to Buildings). The book's own table of contents skips 225.16 too.
MISSING_HEADING = {("NEC Vol 1", "(A) Point of Attachment"): "225.16"}

# a topic video that is one half of a section the book teaches twice
HALF = {
    "TransformerSeparatelyDerivedSystems25030": ("before", "Generator Separately Derived"),
    "GeneratorSeparatelyDerivedSystems25030": ("from", "Generator Separately Derived"),
}


def spans_of(page):
    return [s for b in page.get_text("dict", flags=pymupdf.TEXTFLAGS_TEXT)["blocks"]
            for l in b.get("lines", []) for s in l["spans"] if s["text"].strip()]


def read_book(doc):
    """[(article tag, lines in reading order)] per page.

    The tag is the article a page belongs to: set by 'Introduction to Article N',
    carried by the running header, cleared by a chapter introduction, the review
    questions and anything else whose header is not a section."""
    pages = []
    for page in doc:
        mid = page.rect.width / 2
        intro = head = None
        lines = []
        for s in spans_of(page):
            t = s["text"].replace("\x03", " ").strip()
            x, y = s["bbox"][0], s["bbox"][1]
            if s["font"].endswith("-Hea") and s["size"] > 15:
                m = re.match(r"Introduction to\s+Article\s+(\d{2,3})", t)
                if m: intro = m.group(1)
                elif t.startswith("Introduction to"): intro = "-"
            if s["font"].endswith("-Bol") and abs(s["size"] - 12) < 0.3 and y < 45:
                m = re.match(r"^(\d{2,3})(?:\.\d+)?$", t)
                head = m.group(1) if m else "-"
            lines.append((0 if x < mid else 1, round(y, 1), x, s["font"], s["size"], s["color"], t))
        lines.sort(key=lambda r: (r[0], r[1], r[2]))
        pages.append((intro, head, lines))
    tags, cur = [], None
    for intro, head, _ in pages:
        if intro: cur = None if intro == "-" else intro
        elif head and head != cur: cur = None
        tags.append(cur)
    # a page with no header inside an article (a full-page figure) keeps its tag
    # only if the article goes on after it
    last = {}
    for i, t in enumerate(tags):
        if t: last[t] = i
    return [(t if t and i <= last[t] else None, pages[i][2]) for i, t in enumerate(tags)]


def headings(book, pages):
    """{article: [(level, label, page, topic)]} in reading order.

    level 0 a section, 1 its (A) or its (1) when it has no letters, 2 an (A)(1).
    topic is the book's last free-standing heading ("Generator Separately Derived
    Systems"), so a section taught twice can be cut in half."""
    out, warn = {}, []
    sec = sub = topic = prev = None
    letters, lastnum = [], 0
    for i, (art, lines) in enumerate(pages):
        if art != prev:
            sec = sub = topic = None
            prev = art
        if not art: continue
        hs = out.setdefault(art, [])
        for col, y, x, font, size, color, t in lines:
            if y < 45 or y > 735: continue                       # running header and foot
            if font.endswith("-Hea") and size >= 11.5:
                m = SEC.match(t)
                if m and size < 13.5:
                    sec, sub, topic, letters, lastnum = f"{m.group(1)}.{m.group(2)}", None, None, [], 0
                    hs.append((0, sec, i + 1, topic))
                elif size >= 13.5 and not t.startswith("Part "):
                    # a heading of the book's own inside a section ("Generator Separately
                    # Derived Systems"): the Code's lettering may start over under it
                    topic, letters = SEC.sub("", t).strip(), []
                continue
            bold = font.endswith("-Bol") or font.endswith("-SemBolIt")
            if not (bold and abs(size - 11) < 0.3 and color == BODY and sec): continue
            m = LETTER.match(t)
            if m and font.endswith("-Bol"):
                fix = next((v for (b, k), v in MISSING_HEADING.items() if b == book and t.startswith(k)), None)
                if fix and fix != sec:
                    sec, letters = fix, []
                    hs.append((0, sec, i + 1, topic))
                if m.group(1) in letters:
                    warn.append(f"{book} p{i + 1}: {sec}({m.group(1)}) comes round again after {letters}"
                                " - is a section heading missing?")
                letters.append(m.group(1))
                sub, lastnum = f"{sec}({m.group(1)})", 0
                hs.append((1, sub, i + 1, topic))
                continue
            m = NUMBER.match(t)
            if m:
                n = int(m.group(1))
                if n <= lastnum: continue          # a deeper list restarting, 250.52(A)(3)'s "(1) Rebar."
                lastnum = n
                if sub: hs.append((2, f"{sub}({n})", i + 1, topic))
                else: hs.append((1, f"{sec}({n})", i + 1, topic))
    return out, warn


def natkey(label):
    m = re.match(r"^(\d+)\.(\d+)(.*)$", label)
    parts = re.findall(r"\(([^)]+)\)", m.group(3))
    return (int(m.group(1)), int(m.group(2)),
            tuple((0, int(p)) if p.isdigit() else (1, p) for p in parts))


def pick(hs, maxlevel, lo=None, hi=None, only=None, half=None):
    seen, out = set(), []
    for level, label, page, topic in hs:
        if level > maxlevel: continue
        base = label.split("(")[0]
        if only and base != only: continue
        if lo and natkey(base) < natkey(lo): continue
        if hi and natkey(base) >= natkey(hi): continue
        if half:
            inside = bool(topic and topic.startswith(half[1]))
            if (half[0] == "from") != inside and level > 0: continue
        if label not in seen:
            seen.add(label); out.append(label)
    return out


def main():
    deep = "--deep" in sys.argv
    dry = "--dry" in sys.argv
    os.chdir(HERE)
    V = json.load(open("videos.json", encoding="utf-8"))["units"]
    S = json.load(open("sections.json", encoding="utf-8")) if os.path.exists("sections.json") else {}

    found, notes = {}, []
    for book, fn in PDF.items():
        hs, warn = headings(book, read_book(pymupdf.open(os.path.join(BOOKS, fn))))
        notes += warn
        for art, h in hs.items():
            found[(book, art)] = h
            stray = sorted({x[1] for x in h if x[1].split(".")[0] != art})
            if stray: notes.append(f"{book} Art {art}: a heading from another article {stray}")

    result, skipped = {}, []
    lv = 2 if deep else 1
    for v in V:
        vid, book, art = v["video_id"], v["book"], v.get("article")
        topic = re.search(r"\[(\d{2,3}\.\d+)\]", v["title"])
        if book == "Bonding & Grounding" and topic:
            sec = topic.group(1)
            got = pick(found.get((book, sec.split(".")[0]), []), 2, only=sec, half=HALF.get(vid))
        elif art and (book, str(art)) in found:
            hs = found[(book, str(art))]
            if book == "Bonding & Grounding" and art == 250 and vid.endswith("PartA"):
                got = pick(hs, lv, hi="250.80")
            elif book == "Bonding & Grounding" and art == 250 and vid.endswith("PartB"):
                got = pick(hs, lv, lo="250.80")
            else:
                got = pick(hs, lv)
        else:
            skipped.append(vid); continue
        if not got:
            skipped.append(vid); continue
        order = [natkey(x) for x in got]
        if order != sorted(order):
            notes.append(f"{vid}: the book's order is not the Code's: "
                         + ", ".join(f"{got[i]} before {got[i + 1]}"
                                     for i in range(len(got) - 1) if order[i] > order[i + 1]))
        result[vid] = got

    # every section the transcript says was taught should be in the book's list
    # (compared at the depth the list is written to: 110.26(A)(1) is looked for as 110.26(A))
    missing = {}
    for vid, secs in S.items():
        if vid not in result: continue
        have = set(result[vid])
        miss = []
        for s in secs:
            m = re.match(r"^(\d+\.\d+)((?:\([A-Z0-9]+\))?)", s)
            if not m: continue
            sec, first = m.group(1), m.group(2)
            # a numbered item the book does not head ("334.10(1)", a list item) is
            # covered when its section is
            ok = (sec + first in have) or (first[1:2].isdigit() and sec in have) or (not first and sec in have)
            if not ok: miss.append(s)
        if miss: missing[vid] = miss

    print(f"videos with a list: {len(result)} of {len(V)}")
    for vid, got in result.items():
        n0 = sum(1 for x in got if "(" not in x)
        print(f"  {vid:<44} {len(got):>4}  ({n0} sections)")
    print(f"no list ({len(skipped)}): {', '.join(skipped)}")
    for n in notes: print("NOTE", n)
    if missing:
        print("sections the transcript names that are not in the book's list for that video:")
        for vid, miss in missing.items(): print(f"  {vid}: {miss}")
    if dry:
        out = os.environ.get("BS_OUT")
        if out: json.dump(result, open(os.path.join(out, "book_sections.dry.json"), "w", encoding="utf-8"), indent=1)
        print("--dry: book_sections.json not written"); return
    json.dump(result, open("book_sections.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print("book_sections.json written")


if __name__ == "__main__":
    main()
