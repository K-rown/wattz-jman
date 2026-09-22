#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Find the page in the digital book where each quiz and each lesson begins.

The page numbers this app shows are the DIGITAL BOOK VIEWER's page count, which
is the book PDF's own page order. The number PRINTED at the foot of the page is
smaller — by 13 in the Theory book, by about 20 in NEC Vol 1 — because of the
front matter, and it shifts again at some chapter breaks. Reading the printed
number and calling it a page sends a person twenty pages short of the quiz.

So nothing here is converted. Every page is FOUND and then read back:

  * a quiz's page is the page its own first question is printed on
  * a lesson's page is the page where that article or unit opens

    python3 pages.py           # correct quizzes.json and program.json in place
    python3 pages.py --dry     # say what it would change, write nothing
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
FRONT = 10          # never look for a lesson inside the front matter or the contents


def norm(s):
    s = unicodedata.normalize("NFKD", s or "")
    for a, b in [("’", "'"), ("‘", "'"), ("“", '"'), ("”", '"'), (" ", " ")]:
        s = s.replace(a, b)
    s = re.sub(r"[_—–-]+", " ", s)
    return re.sub(r"\s+", " ", s).strip().lower()


def page_text(book):
    """every page of one book as normalised text, cached because extraction is slow"""
    os.makedirs(CACHE, exist_ok=True)
    c = os.path.join(CACHE, "text-" + re.sub(r"\W+", "_", book) + ".json")
    if os.path.exists(c):
        return json.load(open(c, encoding="utf-8"))
    import pypdf
    r = pypdf.PdfReader(os.path.join(BOOKS, PDF[book]))
    pages = [norm(p.extract_text() or "") for p in r.pages]
    json.dump(pages, open(c, "w", encoding="utf-8"), ensure_ascii=False)
    return pages


def find(pages, probe, start=FRONT):
    """the first page past the front matter that carries this text"""
    probe = norm(probe)
    if len(probe) < 20: return None
    for n in (90, 70, 50):
        p = probe[:n]
        hits = [i for i, t in enumerate(pages) if i >= start and p in t]
        if len(hits) == 1: return hits[0]
        if hits: return hits[0]
    return None


def quiz_page(pages, q):
    """the page the quiz starts on: where its own first question is printed"""
    for x in q["questions"][:3]:
        i = find(pages, x["q"])
        if i is not None: return i
    return None


def lesson_page(pages, v):
    """the page the lesson opens on"""
    art = v.get("article") or (re.search(r"\[(\d{2,3})\.\d+\]", v.get("title", "")) or [None, None])[1]
    if art:
        for probe in (f"article {art} " + norm(v["title"].split("-", 1)[-1])[:40],
                      f"{art}.1 scope", f"article {art} scope", f"article {art} "):
            i = find(pages, probe)
            if i is not None: return i
        return None
    if v.get("kind") == "unit" and v.get("unit"):
        return find(pages, f"{v['unit']}.1 introduction")
    return None


def main():
    dry = "--dry" in sys.argv
    V = json.load(open("videos.json", encoding="utf-8"))["units"]
    Q = json.load(open("quizzes.json", encoding="utf-8"))
    P = json.load(open("program.json", encoding="utf-8")) if os.path.exists("program.json") else {}

    moved, lost, lmoved, llost = [], [], [], []
    for book in sorted({q["book"] for q in Q.values()} | {b for b in PDF}):
        if book not in PDF: continue
        if not os.path.exists(os.path.join(BOOKS, PDF[book])):
            print(f"  {book}: no PDF on this machine, left alone"); continue
        pages = page_text(book)

        for k, q in sorted(Q.items()):
            if q["book"] != book: continue
            i = quiz_page(pages, q)
            if i is None: lost.append(k); continue
            if q.get("page") != i: moved.append((k, q.get("page"), i))
            if not dry: q["page"] = i

        full = FULL.get(book)
        for v in V:
            if v["book"] != full: continue
            i = lesson_page(pages, v)
            row = P.get(v["video_id"], {})
            if i is None:
                if row.get("page"): llost.append(v["video_id"])
                continue
            if row.get("page") != i: lmoved.append((v["video_id"], row.get("page"), i))
            if not dry:
                row["page"] = i
                P[v["video_id"]] = row

    # a quiz's page also rides on the library row, so keep those in step
    if not dry:
        for vid, row in P.items():
            if row.get("quiz") and row["quiz"].get("key") in Q:
                pg = Q[row["quiz"]["key"]].get("page")
                if pg: row["quiz"]["page"] = pg

    print(f"quiz pages corrected: {len(moved)}")
    for k, a, b in moved[:12]: print(f"   {k:<30} {a} -> {b}")
    if len(moved) > 12: print(f"   ... and {len(moved) - 12} more")
    if lost: print(f"quizzes whose first question could not be found ({len(lost)}): {lost[:8]}")
    print(f"lesson pages set or corrected: {len(lmoved)}")
    for k, a, b in lmoved[:10]: print(f"   {k:<30} {a} -> {b}")
    if len(lmoved) > 10: print(f"   ... and {len(lmoved) - 10} more")
    if llost: print(f"lessons whose opening page could not be found ({len(llost)}): {llost[:8]}")

    if dry: print("\n--dry: nothing written"); return
    json.dump(Q, open("quizzes.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    json.dump(P, open("program.json", "w", encoding="utf-8"), indent=0, ensure_ascii=False)
    print("\nquizzes.json and program.json written")


if __name__ == "__main__":
    main()
