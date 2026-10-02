#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Which sections Mike Holt's 2023 textbooks mark as CHANGED or NEW for 2023.

The student studies the 2023 books but sits a 2020 exam with a 2020 code book, so
he needs to know where the 2023 text he reads is not the text in his book.

THE BOOK'S OWN CONVENTION (the "How to Use This Textbook" page: Vol 1 page index
16, B&G 11, Vol 2 13): "Underlined text denotes changes to the Code for the 2023
NEC." Underline is the only mark Mike uses; there is no separate "new" icon (the
shaded "N" the same front matter describes is the NFPA code book's convention, not
this textbook's). In the PDF an underline is a 0.5 pt stroke in the CHAPTER'S
colour (Chapter 2 blue, Chapter 3 purple, ...) drawn about 2 pt under the baseline
of body text. The table grid lines are grey or black, the yellow behind a
subsection label is a 12 pt stroke, a hyperlink ("Figure 210-6") is blue TEXT
with no stroke under it, so none of them is taken for a change.

What counts: only the code text - the section and subsection paragraphs, their
exceptions, their numbered lists, their Notes, a table's title. Not counted:
"According to Article 100" definition paragraphs, Author's Comment boxes and
their bullets, figure captions and the words inside figures (other fonts), the
worked examples, the headers. Commentary is told apart by how its PARAGRAPH
starts, not by its face: Volume 2 sets code text in the regular face too.

  new       the section (or subsection) heading itself is underlined AND nearly all
            of its code text is: a rule that did not exist in 2020 (or was moved
            here, which the NEC treats the same way).
  changed   some of its code text (or its heading) is underlined.
A section is changed when any of its subsections is. Unmarked sections are left
out of the output.

Writes book_changes.json: {video_id: {"210.4": "changed", "215.18": "new", ...}}
    python book_changes.py          # write
    python book_changes.py --dry    # report only
Needs the book PDFs and PyMuPDF; reads book_sections.json and videos.json and
uses book_sections.py's page reading (article tags, headings) unchanged.
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import book_sections as bs  # noqa: E402  (it strips HERE from sys.path before PyMuPDF)
pymupdf = bs.pymupdf

NEW_SHARE = 0.85      # share of a rule's code text underlined for it to read as new
MIN_CHARS = 3         # fewer underlined characters than this is a stray stroke
BODY = bs.BODY


def is_mark(color, width):
    """A change underline: a thin stroke in a saturated colour (the chapter's)."""
    if not color or len(color) < 3: return False
    if width is None or width > 0.8: return False
    return max(color) - min(color) > 0.25


def page_marks(page):
    out = []
    for dr in page.get_cdrawings():
        items = dr.get("items") or []
        if not items or any(it[0] != "l" for it in items): continue
        r = pymupdf.Rect(dr["rect"])
        if r.height < 1.2 and r.width > 2 and is_mark(dr.get("color"), dr.get("width")):
            out.append((r.x0, r.x1, (r.y0 + r.y1) / 2))
    return out


def covered(span, marks):
    """How much of a span's width has a change stroke just under its baseline."""
    x0, _, x1, _ = span["bbox"]
    oy = span["origin"][1]
    w = 0.0
    for a, b, y in marks:
        if 0.3 <= y - oy <= 4.0:
            w += max(0.0, min(b, x1) - max(a, x0))
    return min(1.0, w / max(1e-6, x1 - x0))


def lines_of(page, marks):
    """[(col, y, x, font, size, color, text, frac)] in book_sections' reading order."""
    mid = page.rect.width / 2
    rows = []
    for s in bs.spans_of(page):
        t = s["text"].replace("\x03", " ").strip()
        x, y = s["bbox"][0], s["bbox"][1]
        frac = covered(s, marks) if marks else 0.0
        rows.append((0 if x < mid else 1, round(y, 1), x, s["font"], s["size"], s["color"], t, frac, s["bbox"][3]))
    rows.sort(key=lambda r: (r[0], r[1], r[2]))
    return rows


def code_span(font, size, color, t):
    """Is this span set as code text (body ink, body size)?"""
    if color != BODY: return False
    if not (10.8 <= size <= 11.2): return False
    return not font.startswith("Wingdings")


def commentary_lead(font, size, color, t):
    """Does a paragraph starting with this span belong to Mike rather than the Code?"""
    if t.startswith("According to Article 100"): return True
    if t.startswith("Author’s Comment") or t.startswith("Author's Comment"): return True
    if font.startswith("Wingdings"): return True                 # a bullet in a comment box
    if color != BODY: return True                                # captions, callouts, coloured leads
    if not (10.8 <= size <= 11.2): return True                   # examples (10.5), small print
    if t.startswith(("Example", "Question:", "Solution:", "Answer:")): return True
    return False


def scan(book, doc):
    """{(article, label, topic): {chars, under, head, headfull}} per rule."""
    pages = bs.read_book(doc)
    stats = {}
    sec = sub = topic = prev = None
    letters, lastnum = [], 0

    def unit(label):
        return stats.setdefault((art, label, topic), {"chars": 0.0, "under": 0.0, "head": False, "headfull": False})

    for i, (art, _) in enumerate(pages):
        if art != prev:
            sec = sub = topic = None
            prev = art
        if not art: continue
        page = doc[i]
        marks = page_marks(page)
        para_comment, last_col, last_bottom = False, None, None
        in_comment = False      # inside an Author's Comment box: its bullets are indented
        rows = lines_of(page, marks)
        left = {}
        for r in rows:
            if r[5] == BODY and 10.8 <= r[4] <= 11.2 and 45 < r[1] < 735:
                left[r[0]] = min(left.get(r[0], 1e9), r[2])
        for col, y, x, font, size, color, t, frac, bottom in rows:
            if y < 45 or y > 735: continue
            # a heading bar: the section starts here
            if font.endswith("-Hea") and size >= 11.5:
                m = bs.SEC.match(t)
                if m and size < 13.5:
                    sec, sub, topic, letters, lastnum = f"{m.group(1)}.{m.group(2)}", None, None, [], 0
                    u = unit(sec)
                    u["head"] = u["head"] or frac > 0.5
                    u["headfull"] = frac > 0.8
                elif size >= 13.5 and not t.startswith("Part "):
                    topic, letters = bs.SEC.sub("", t).strip(), []
                para_comment, last_col, last_bottom = False, None, None
                in_comment = False
                continue
            # a second line of a two-line heading bar
            if font.endswith("-Hea") and color == 0xFFFFFF:
                if sec and frac > 0.5: unit(sec)["head"] = True
                continue
            # paragraph bookkeeping: a gap of more than a line's leading starts a new one
            newpara = (col != last_col) or last_bottom is None or (y - last_bottom > 6.5)
            if newpara:
                para_comment = commentary_lead(font, size, color, t)
                if t.startswith(("Author’s Comment", "Author's Comment")):
                    in_comment = True
                elif in_comment and x > left.get(col, 0) + 12:
                    para_comment = True
                elif x > left.get(col, 0) + 20 and font.endswith("-Reg"):
                    para_comment = in_comment = True     # a comment box carried over a page
                elif not font.startswith("Wingdings"):
                    in_comment = False
            last_col, last_bottom = col, bottom
            if not sec: continue
            bold = font.endswith("-Bol") or font.endswith("-SemBolIt")
            label_here = None
            if bold and abs(size - 11) < 0.3 and color == BODY:
                m = bs.LETTER.match(t)
                if m and font.endswith("-Bol"):
                    fix = next((v for (b, k), v in bs.MISSING_HEADING.items() if b == book and t.startswith(k)), None)
                    if fix and fix != sec:
                        sec, letters = fix, []
                    letters.append(m.group(1))
                    sub, lastnum = f"{sec}({m.group(1)})", 0
                    label_here = sub
                else:
                    m = bs.NUMBER.match(t)
                    if m:
                        n = int(m.group(1))
                        if n > lastnum:
                            lastnum = n
                            if not sub or not re.search(r"\([A-Z]\)$", sub):
                                sub = f"{sec}({n})"
                                label_here = sub
                            # an (A)(1) stays counted under its (A)
                if label_here:
                    para_comment = False
                    u = unit(label_here)
                    u["head"] = u["head"] or frac > 0.5
                    u["headfull"] = frac > 0.8
            # a table title in the chapter's colour ("Table 310.16 ...") is code
            if font.endswith("-Bol") and abs(size - 12) < 0.3 and color != BODY and t.startswith("Table"):
                n = len(t)
                u = unit(sec); u["chars"] += n; u["under"] += n * frac
                continue
            if para_comment or not code_span(font, size, color, t): continue
            n = len(re.sub(r"\s", "", t))
            if not n: continue
            u = unit(sub or sec)
            u["chars"] += n
            u["under"] += n * frac
    return stats


def verdict(s):
    if s["under"] < MIN_CHARS and not s["head"]: return None
    share = s["under"] / s["chars"] if s["chars"] else (1.0 if s["head"] else 0.0)
    if s["head"] and share >= NEW_SHARE: return "new"
    return "changed"


def main():
    dry = "--dry" in sys.argv
    os.chdir(HERE)
    V = json.load(open("videos.json", encoding="utf-8"))["units"]
    S = json.load(open("book_sections.json", encoding="utf-8"))
    per_book = {}
    for book, fn in bs.PDF.items():
        print("reading", book, flush=True)
        per_book[book] = scan(book, pymupdf.open(os.path.join(bs.BOOKS, fn)))

    result, report = {}, {}
    for v in V:
        vid, book = v["video_id"], v["book"]
        if vid not in S: continue
        stats = per_book[book]
        half = bs.HALF.get(vid)

        def merged(label, own_only):
            """Totals for a label (and, unless own_only, everything inside it)."""
            tot = {"chars": 0.0, "under": 0.0, "head": False, "headfull": False}
            kids = []
            for (art, lab, topic), s in stats.items():
                if half:
                    inside = bool(topic and topic.startswith(half[1]))
                    if (half[0] == "from") != inside and "(" in lab: continue
                if lab == label or (not own_only and lab.startswith(label + "(")):
                    if lab == label:
                        tot["head"] = tot["head"] or s["head"]
                        tot["headfull"] = tot["headfull"] or s["headfull"]
                    else:
                        kids.append(s)
                    tot["chars"] += s["chars"]; tot["under"] += s["under"]
            return tot, kids

        out = {}
        for label in S[vid]:
            tot, kids = merged(label, own_only=False)
            vd = verdict(tot)
            if vd == "new" and kids and any(verdict(k) != "new" and k["chars"] > 20 for k in kids):
                vd = "changed"
            # a section whose own lines are unmarked but a subsection is: changed
            if vd is None and any(verdict(k) for k in kids): vd = "changed"
            if vd: out[label] = vd
        if out: result[vid] = out
        report[vid] = out

    for vid, out in result.items():
        n = sum(1 for x in out.values() if x == "new"); c = len(out) - n
        print(f"  {vid:<44} new {n:>3}  changed {c:>3}")
    if dry:
        out = os.environ.get("BC_OUT")
        if out:
            json.dump(result, open(os.path.join(out, "book_changes.dry.json"), "w", encoding="utf-8"), indent=1)
            json.dump({b: {"|".join(map(str, k)): s for k, s in st.items()} for b, st in per_book.items()},
                      open(os.path.join(out, "book_changes.stats.json"), "w", encoding="utf-8"))
        print("--dry: book_changes.json not written"); return
    json.dump(result, open("book_changes.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print("book_changes.json written")


if __name__ == "__main__":
    main()
