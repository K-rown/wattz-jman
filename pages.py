#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Check every page number in the app against the book it points into.

The page numbers here are the DIGITAL BOOK VIEWER's count, which is the book
PDF's own page order. The number PRINTED at the foot of the page is smaller, by
the size of the front matter: 14 in Bonding and Grounding, 12 in Calculations,
20 in NEC Volume 1. Reading the printed number and calling it a page sends a man
twenty pages short of his quiz, so books.py measures each book's difference
against the pages Kymani had already checked and shifts the rest onto the same
count. This is the tool that proves it worked.

It opens each book PDF, finds where each quiz's own questions are actually
printed, and says so. Nothing is written; it only reports.

    python3 pages.py            # check every book that is on this machine
    python3 pages.py "B&G"      # check one

The books are not in this repo. They live in:
    C:\\Users\\Kymani\\projects\\jmen\\MikeHolt\\books

Reading a 700-page PDF takes a few minutes, so each book's text is cached in
paste2/text-<book>.json and reused.
"""
import json, os, re, sys, unicodedata

try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass

BOOKS = os.path.join("C:", os.sep, "Users", "Kymani", "projects", "jmen", "MikeHolt", "books")
PDF = {
    "Theory":    "1-understanding-electrical-theory-book.pdf",
    "NEC Vol 1": "2-understanding-the-nec-vol-1-book.pdf",
    "B&G":       "3-bonding-and-grounding-book.pdf",
    "NEC Vol 2": "4-understanding-the-nec-vol-2-book.pdf",
    "Calcs":     "5-fundamental-nec-calculations-book.pdf",
    "Exam Prep": "6-electrical-exam-preparation-book.pdf",
    "Simulated Exams": "7-journeyman-simulated-exams-book.pdf",
}
FULL = {"Theory": "Electrical Theory", "NEC Vol 1": "NEC Vol 1", "Calcs": "Fundamental NEC Calculations",
        "Exam Prep": "Exam Prep", "B&G": "Bonding & Grounding", "NEC Vol 2": "NEC Vol 2"}
CACHE = "paste2"
FRONT = 10          # the front matter and the table of contents are not the lesson


def norm(s):
    s = unicodedata.normalize("NFKD", s or "")
    for a, b in [("\u2019", "'"), ("\u2018", "'"), ("\u201c", '"'), ("\u201d", '"'), ("\u00a0", " ")]:
        s = s.replace(a, b)
    s = re.sub(r"[_\u2014\u2013-]+", " ", s)
    return re.sub(r"\s+", " ", s).strip().lower()


def page_text(book):
    """every page of one book as normalised text, cached because extraction is slow"""
    os.makedirs(CACHE, exist_ok=True)
    c = os.path.join(CACHE, "text-" + re.sub(r"\W+", "_", book) + ".json")
    if os.path.exists(c):
        return json.load(open(c, encoding="utf-8"))
    import pypdf
    print(f"  reading {PDF[book]} \u2014 this takes a few minutes the first time")
    r = pypdf.PdfReader(os.path.join(BOOKS, PDF[book]))
    pages = [norm(p.extract_text() or "") for p in r.pages]
    json.dump(pages, open(c, "w", encoding="utf-8"), ensure_ascii=False)
    return pages


def hits_for(pages, text, start=FRONT):
    """the viewer pages carrying this text, longest probe that still matches"""
    probe = norm(text)
    if len(probe) < 25: return []
    for n in (110, 80, 60):
        p = probe[:n]
        got = [i + 1 for i, t in enumerate(pages) if i >= start and p in t]
        if got: return got
    return []


def main():
    want = [a for a in sys.argv[1:] if not a.startswith("--")]
    Q = json.load(open("quizzes.json", encoding="utf-8"))
    P = json.load(open("program.json", encoding="utf-8")) if os.path.exists("program.json") else {}
    V = {v["video_id"]: v for v in json.load(open("videos.json", encoding="utf-8"))["units"]}
    total_ok = total_bad = total_none = 0

    for book in sorted(PDF):
        if want and book not in want: continue
        if not os.path.exists(os.path.join(BOOKS, PDF[book])):
            print(f"{book}: the PDF is not on this machine, skipped"); continue
        pages = page_text(book)

        ok = near = bad = none = 0
        wrong = []
        for k, q in sorted(Q.items()):
            if q["book"] != book: continue
            rec = q.get("page")
            hits = []
            for x in q["questions"][:6]: hits += hits_for(pages, x["q"])
            if not hits: none += 1; continue
            if rec in hits: ok += 1
            elif rec is not None and any(abs(h - rec) <= 3 for h in hits): near += 1
            else: bad += 1; wrong.append((k, rec, sorted(set(hits))[:4]))

        lok = lbad = 0
        lwrong = []
        for vid, row in P.items():
            v = V.get(vid)
            if not v or v["book"] != FULL.get(book) or not row.get("page"): continue
            art = v.get("article")
            if not art: continue
            i = row["page"] - 1
            t = pages[i] if 0 <= i < len(pages) else ""
            if f"article {art}" in t or f"{art}.1" in t: lok += 1
            else: lbad += 1; lwrong.append((vid, row["page"]))

        print(f"{book:<16} quizzes on the exact page: {ok:>3}  within three: {near:>2}  WRONG: {bad:>2}  "
              f"text not found: {none:>2}   |   lessons on their article: {lok:>3}  WRONG: {lbad:>2}")
        for w in wrong[:6]: print(f"     {w[0]:<34} says page {w[1]}, its questions are on {w[2]}")
        for w in lwrong[:6]: print(f"     {w[0]:<34} page {w[1]} does not open on its article")
        total_ok += ok + lok; total_bad += bad + lbad; total_none += none

    print()
    print(f"{total_ok} page numbers land where they should, {total_bad} do not, {total_none} could not be checked")
    sys.exit(1 if total_bad else 0)


if __name__ == "__main__":
    main()
