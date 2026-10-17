#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The name of every NEC section and subsection the textbook heads, read off the book.

The highlight list shows a section's number; this gives it its name, so a tick can be
checked against the page before it is made: "210.8 Ground-Fault Circuit-Interrupter
Protection for Personnel", "210.8(A) Dwelling Units". The words are the book's own
heading, never a guess — it reads the same type book_sections.py reads (the heavy face
on the coloured bar for a section, the bold "(A) General." at the head of a paragraph
for a subsection) and keeps the words printed after the number.

Writes book_titles.json: {"210.8": "Ground-Fault Circuit-Interrupter Protection for Personnel", ...}

    python book_titles.py          # write book_titles.json
    python book_titles.py --dry    # report, write nothing

Needs the book PDFs (book_sections.BOOKS) and PyMuPDF. Then run build.py.
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import book_sections as bs  # noqa: E402  (it drops HERE from the path for pymupdf; put it back after)
if HERE not in sys.path: sys.path.insert(0, HERE)

MAXLEN = 120


def tidy(s):
    s = re.sub(r"\s+", " ", s.replace("\x03", " ")).strip()
    s = re.sub(r"(?<=[a-z])- (?=[a-z])", "", s)         # "Replace- ments" was one word, broken at the line end
    s = re.sub(r"(?<=[a-z])- (?=[A-Z])", "-", s)         # "Service- Entrance" was the hyphenated pair
    s = re.sub(r"\s*\.$", "", s)            # "(A) General." -> "General"
    return s[:MAXLEN].strip()


def whole_fractions(lines):
    """Set a heading's fraction (a slash with its small numerator and denominator spans) as one span."""
    small = [r for r in lines if r[4] < 8 and r[6].isdigit()]
    for r in [r for r in lines if r[6] == "⁄" and r[4] >= 8]:
        nu = [q for q in small if q[0] == r[0] and abs(q[1] - r[1]) < 6 and 0 < r[2] - q[2] < 12]
        de = [q for q in small if q[0] == r[0] and abs(q[1] - r[1]) < 6 and 0 < q[2] - r[2] < 12]
        if nu and de:
            used = (nu[0], de[0])
            lines = [q for q in lines if not any(q is u for u in used)]
            lines = [(*q[:6], nu[0][6] + "⁄" + de[0][6]) if q is r else q for q in lines]
    return lines


def titles(book, pages):
    """{label: name} for every heading headings() would find, in that book."""
    out = {}
    sec = sub = prev = None
    letters, lastnum = [], 0
    open_ = None                             # [label, col, y, words, kind] still collecting
    def close():
        nonlocal open_
        if open_ and open_[3]:
            name = tidy(" ".join(open_[3]))
            if name and open_[0] not in out: out[open_[0]] = name
        open_ = None
    for i, (art, lines) in enumerate(pages):
        close()
        if art != prev:
            sec = sub = None
            prev = art
        if not art: continue
        lines = whole_fractions(lines)
        for col, y, x, font, size, color, t in lines:
            if y < 45 or y > 735: continue
            hea = font.endswith("-Hea")
            bold = font.endswith("-Bol") or font.endswith("-SemBolIt")
            # a heading carried onto the next span: the same face, the same column, the
            # same line or the line just under it
            if open_ and col == open_[1]:
                same = abs(y - open_[2]) < 1.5
                # an italic word in the heading ("of the NEC") rides on the same line
                if same and (font.endswith("-HeaIta") if open_[4] == "sec" else font.endswith("-BolIta"))                         and abs(size - (12 if open_[4] == "sec" else 11)) < 0.3:
                    open_[3].append(t); continue
                below = 0 < y - open_[2] < 18
                if open_[4] == "sec" and hea and 11.5 <= size < 13.5 and (same or below) and not bs.SEC.match(t):
                    open_[3].append(t); open_[2] = y; continue
                if open_[4] == "sub" and bold and abs(size - 11) < 0.3 and color == bs.BODY \
                        and (same or below) and (not open_[3] or not open_[3][-1].rstrip().endswith(".")) \
                        and not bs.LETTER.match(t) and not bs.NUMBER.match(t):
                    open_[3].append(t); open_[2] = y; continue
            if hea and size >= 11.5:
                m = bs.SEC.match(t)
                if m and size < 13.5:
                    close()
                    sec, sub, letters, lastnum = f"{m.group(1)}.{m.group(2)}", None, [], 0
                    rest = bs.SEC.sub("", t).strip()
                    open_ = [sec, col, y, [rest] if rest else [], "sec"]
                elif size >= 13.5 and not t.startswith("Part "):
                    close(); letters = []
                continue
            if not (bold and abs(size - 11) < 0.3 and color == bs.BODY and sec): continue
            m = bs.LETTER.match(t)
            if m and font.endswith("-Bol"):
                close()
                fix = next((v for (b, k), v in bs.MISSING_HEADING.items() if b == book and t.startswith(k)), None)
                if fix and fix != sec: sec, letters = fix, []
                letters.append(m.group(1))
                sub, lastnum = f"{sec}({m.group(1)})", 0
                rest = t[m.end():].strip()
                open_ = [sub, col, y, [rest] if rest else [], "sub"]
                continue
            m = bs.NUMBER.match(t)
            if m:
                n = int(m.group(1))
                if n <= lastnum: continue
                lastnum = n
                close()
                label = f"{sub}({n})" if sub else f"{sec}({n})"
                rest = t[m.end():].strip()
                open_ = [label, col, y, [rest] if rest else [], "sub"]
    close()
    return out


def main():
    dry = "--dry" in sys.argv
    os.chdir(HERE)
    want = set(x for v in json.load(open("book_sections.json", encoding="utf-8")).values() for x in v)
    got = {}
    for book, fn in bs.PDF.items():
        t = titles(book, bs.read_book(bs.pymupdf.open(os.path.join(bs.BOOKS, fn))))
        for k, v in t.items(): got.setdefault(k, v)
    named = {k: got[k] for k in sorted(want, key=bs.natkey) if k in got}
    miss = sorted(want - set(named), key=bs.natkey)
    print(f"named {len(named)} of the {len(want)} sections in the highlight lists")
    for k in list(named)[:25]: print(f"  {k:<14} {named[k]}")
    if miss: print(f"no name found ({len(miss)}): {', '.join(miss[:60])}{' ...' if len(miss) > 60 else ''}")
    if dry: print("--dry: book_titles.json not written"); return
    json.dump(named, open("book_titles.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print("book_titles.json written — now run build.py")


if __name__ == "__main__":
    main()
