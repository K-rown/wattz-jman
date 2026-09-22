#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fold Mike Holt's seven books into the app's data.

The app began as one person's plan, so it only carried the quizzes that person
had left. A crew does not start in the middle: somebody opening Theory Unit 1
needs Unit 1's quiz and Unit 1's page, the same as everybody else.

Every quiz and every page number here was read out of the PDFs of the books
themselves (paste2/*.json). Where a quiz was already in quizzes.json, checked by
hand against the printed answer key, THAT version is kept — the two agree on
every answer, and the hand-checked ones carry worked arithmetic the book does not.

Writes:
  quizzes.json   every quiz in the program
  program.json   {video_id: {page, quiz}} for every video, so the library can
                 show a page and a quiz beside a video nobody has scheduled

    python3 books.py            # merge and report
    python3 books.py --dry      # report only, write nothing
"""
import glob, json, os, re, sys

try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass

BOOK_URL = {
    "Theory":     "https://www.mikeholt.com/checkout/#/account/digital-books/book-viewer/TH-DB/1964",
    "NEC Vol 1":  "https://www.mikeholt.com/checkout/#/account/digital-books/book-viewer/23UNEC1-DB/5392",
    "Calcs":      "https://www.mikeholt.com/checkout/#/account/digital-books/book-viewer/23FUNDCAL-DB/5383",
    "Exam Prep":  "https://www.mikeholt.com/checkout/#/account/digital-books/book-viewer/23EP-DB/5382",
    "B&G":        "https://www.mikeholt.com/checkout/#/account/digital-books/book-viewer/23UNECBG-DB/5380",
    "NEC Vol 2":  "https://www.mikeholt.com/checkout/#/account/digital-books/book-viewer/23UNEC2-DB/5393",
}
FULL = {"Theory": "Electrical Theory", "NEC Vol 1": "NEC Vol 1", "Calcs": "Fundamental NEC Calculations",
        "Exam Prep": "Exam Prep", "B&G": "Bonding & Grounding", "NEC Vol 2": "NEC Vol 2"}


def quiz_key(book, quiz):
    return (book + " " + quiz).replace(" ", "_")


def video_for(book, quiz, V):
    """the video a quiz follows, or None when the quiz stands on its own
    (a final exam, or theory reprinted inside another book)"""
    full = FULL.get(book)
    if not full: return None
    pool = [v for v in V if v["book"] == full]

    m = re.match(r"^Art (\d{2,3})$", quiz)
    if m:
        hits = [v for v in pool if str(v.get("article")) == m.group(1)]
        return hits[-1]["video_id"] if hits else None      # Part B follows Part A

    m = re.match(r"^Unit (\d+)$", quiz)
    if m:
        hits = [v for v in pool if v.get("unit") == int(m.group(1)) and v.get("kind") == "unit"]
        return hits[-1]["video_id"] if hits else None

    m = re.match(r"^(?:Calcs )?Ch (\d+)$", quiz)
    # In every book but Exam Prep a "Chapter N" quiz closes the videos of NEC
    # chapter N. Exam Prep is laid out by module, and its Chapter N review covers
    # NEC chapter N with no video of its own, so it must not latch onto a module.
    if m and book != "Exam Prep":
        hits = [v for v in pool if str(v.get("chapter")) == m.group(1)]
        return hits[-1]["video_id"] if hits else None      # a chapter quiz closes the chapter
    return None


def page_for(v, pages):
    """the page in the book where this video's lesson starts"""
    def find(*pats):
        for pat in pats:
            for title, pg in pages.items():
                if re.search(pat, title, re.I) and "review question" not in title.lower():
                    return pg
        return None
    if v.get("article"):
        return find(r"^Article\s+" + str(v["article"]) + r"\b")
    m = re.search(r"\[(\d{2,3})\.\d+\]", v.get("title", ""))
    if m:
        return find(r"^Article\s+" + m.group(1) + r"\b")
    # try the unit, then the chapter: a calculations video is a chapter that
    # happens to carry a unit number, and stopping at the unit lost its page
    if v.get("kind") == "unit" and v.get("unit"):
        pg = find(r"^Unit\s+" + str(v["unit"]) + r"\b")
        if pg: return pg
    if v.get("chapter") is not None:
        return find(r"^Chapter\s+" + str(v["chapter"]) + r"\b")
    return None


def main():
    dry = "--dry" in sys.argv
    V = json.load(open("videos.json", encoding="utf-8"))["units"]
    Q = json.load(open("quizzes.json", encoding="utf-8")) if os.path.exists("quizzes.json") else {}
    before = len(Q)

    # measured by pages.py against the book's own pages, for a book with no
    # hand-checked quiz to compare against
    MEASURED_SHIFT = {"Simulated Exams": 8}
    shifts = {}
    # lesson pages read off the books themselves, for videos whose book indexes
    # only its review questions (see pages.py)
    LESSON = json.load(open("lesson-pages.json", encoding="utf-8")) if os.path.exists("lesson-pages.json") else {}
    RESOLVED = {}
    if os.path.exists("resolved.json"):
        for r in json.load(open("resolved.json", encoding="utf-8")):
            RESOLVED[f"{r['key']}:{r['n']}"] = r

    # how far this book's printed numbers sit from the viewer's, measured against
    # the quizzes that were already here with a checked page
    def page_shift(book, quizzes):
        import collections
        seen = collections.Counter()
        for k, e in quizzes.items():
            old = Q.get(k)
            if old and old.get("page") and e.get("page"): seen[old["page"] - e["page"]] += 1
        if not seen:
            # No quiz of this book was ever in the app by hand, so there is no pair to
            # measure. pages.py read the book itself and found the gap; it is checked
            # there on every run, so a wrong number here cannot go quiet.
            return MEASURED_SHIFT.get(book)
        if len(seen) > 1: return None                 # the pairs disagree: do not touch a page
        return next(iter(seen))

    books, added, kept, orphan = {}, [], [], []
    for f in sorted(glob.glob(os.path.join("paste2", "*.json"))):
        d = json.load(open(f, encoding="utf-8"))
        if not isinstance(d, dict) or "quizzes" not in d: continue   # page caches and notes live here too
        books[os.path.basename(f)] = d
        bk = next(iter(d["quizzes"].values()))["book"] if d["quizzes"] else None
        shift = page_shift(bk, d["quizzes"])
        if shift is None:
            shifts[bk] = "not measurable"
        else:
            shifts[bk] = shift
            if shift:
                for q in d["quizzes"].values():
                    if q.get("page"): q["page"] += shift
                d["pages"] = {t: pg + shift for t, pg in (d.get("pages") or {}).items()}
        for k, q in d["quizzes"].items():
            key = quiz_key(q["book"], q["quiz"])
            if key in Q:
                kept.append(key)
                for x in Q[key]["questions"]:
                    fix = RESOLVED.get(f"{key}:{x['n']}")
                    if fix and (fix.get("override") or not x.get("answer")):
                        x["answer"] = fix["answer"]
                        if fix.get("evidence"): x["computed"] = fix["evidence"]
                continue
            for x in q["questions"]:
                fix = RESOLVED.get(f"{key}:{x['n']}")
                # a plain entry fills an answer the printed key never settled;
                # one marked override REPLACES a keyed answer the corpus disproves
                if fix and (fix.get("override") or not x.get("answer")):
                    x["answer"] = fix["answer"]
                    if fix.get("evidence"): x["computed"] = fix["evidence"]
            bad = [x["n"] for x in q["questions"] if not x.get("answer") or x["answer"] not in x.get("choices", {})]
            if bad:
                # a question whose answer nobody could settle is left out of the quiz,
                # said out loud, rather than quietly guessed or the whole quiz dropped
                q = dict(q, questions=[x for x in q["questions"] if x["n"] not in bad],
                         source=(q.get("source", "") + f" Q{', Q'.join(str(b) for b in bad)} left out: the printed key does not settle "
                                 + ("them." if len(bad) > 1 else "it.")).strip())
                orphan.append(f"{key}: Q{', Q'.join(str(b) for b in bad)} left out, the rest of the quiz kept")
            if not q["questions"]:
                orphan.append(f"{key}: nothing usable, skipped entirely"); continue
            Q[key] = q
            added.append(key)

    # a question printed twice, once with its section named and once without,
    # can lend the name to its twin
    import collections
    seen = collections.defaultdict(collections.Counter)
    for q in Q.values():
        for x in q["questions"]:
            if x.get("ref"): seen[re.sub(r"\s+", " ", x["q"].strip().lower())][x["ref"].strip()] += 1
    borrowed = 0
    for q in Q.values():
        for x in q["questions"]:
            if x.get("ref"): continue
            c = seen.get(re.sub(r"\s+", " ", x["q"].strip().lower()))
            if not c: continue
            top = c.most_common(2)
            if len(top) > 1 and top[0][1] == top[1][1]: continue   # two books disagree: leave it alone
            x["ref"] = top[0][0]
            x["reffrom"] = "the same question, printed with its section elsewhere in these books"
            borrowed += 1

    # which video each quiz follows, and which page each video starts on
    program, pageless, quizpage = {}, [], []
    by_book_pages = {}
    for d in books.values():
        for k, q in d["quizzes"].items():
            by_book_pages.setdefault(q["book"], {}).update(d.get("pages", {}))
    for d in books.values():
        bk = next(iter(d["quizzes"].values()))["book"] if d["quizzes"] else None
        if bk: by_book_pages.setdefault(bk, {}).update(d.get("pages", {}))

    quiz_of = {}
    for key, q in Q.items():
        vid = video_for(q["book"], q["quiz"], V)
        if vid: quiz_of.setdefault(vid, key)

    for v in V:
        short = next((s for s, f in FULL.items() if f == v["book"]), None)
        row = {}
        # a page found in the book by hand wins: some books index only their
        # review-question pages, which is not where the lesson is
        pg = LESSON.get(v["video_id"], {}).get("page") or page_for(v, by_book_pages.get(short, {}))
        key0 = quiz_of.get(v["video_id"])
        # Some books index only their review-question pages. A "lesson page" that
        # lands exactly on this video's own quiz is that, not the lesson, so it is
        # dropped rather than sent somebody to the wrong page.
        if pg and key0 and Q[key0].get("page") == pg:
            pg = None; quizpage.append(v["video_id"])
        if pg: row["page"] = pg
        else: pageless.append(v["video_id"])
        key = key0
        if key:
            q = Q[key]
            row["quiz"] = {"label": q["quiz"] + " quiz", "book": q["book"], "key": key,
                           **({"url": BOOK_URL[short]} if short in BOOK_URL else {}),
                           **({"page": q["page"]} if q.get("page") else {})}
        if row: program[v["video_id"]] = row

    # quizzes that follow no video at all — final exams and the simulated exams
    standalone = sorted(k for k, q in Q.items() if not video_for(q["book"], q["quiz"], V))

    print(f"books read: {len(books)}")
    print("page numbers shifted onto the viewer's count: "
          + ", ".join(f"{b} {v:+d}" if isinstance(v, int) else f"{b} ({v})" for b, v in sorted(shifts.items()) if b))
    print(f"section references borrowed from an identical question elsewhere: {borrowed}")
    print(f"quizzes: {before} before, {len(Q)} now ({len(added)} added, {len(kept)} already there and kept as they were)")
    if added: print("  added:", ", ".join(sorted(added)))
    if orphan:
        print(f"  QUESTIONS LEFT OUT ({len(orphan)}):")
        for o in orphan: print("   -", o)
    print(f"videos with a page: {sum(1 for r in program.values() if 'page' in r)} of {len(V)}")
    print(f"videos with a quiz: {sum(1 for r in program.values() if 'quiz' in r)} of {len(V)}")
    if pageless: print(f"  no page found for {len(pageless)}: {pageless[:8]}{' ...' if len(pageless) > 8 else ''}")
    if quizpage: print(f"  {len(quizpage)} of those only had their quiz's page in the book index, not the lesson's")
    if standalone: print(f"quizzes that follow no video ({len(standalone)}): {', '.join(standalone)}")

    if dry: print("\n--dry: nothing written"); return
    json.dump(Q, open("quizzes.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    json.dump(program, open("program.json", "w", encoding="utf-8"), indent=0, ensure_ascii=False)
    print("\nquizzes.json and program.json written")


if __name__ == "__main__":
    main()
