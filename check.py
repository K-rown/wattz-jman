#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Read the built page the way a person would and fail loudly on anything wrong.

Run this after every build, before every push. It opens index.html, pulls the
data the app actually ships, and checks the things a reader would notice:

  * every quiz a page links to exists, and every question has a key that is
    one of its own choices
  * every video in the program is listed, named, and playable
  * every section jump lands inside its video
  * every video the old 52-day plan scheduled is still reachable in the library

    python3 check.py
"""
import json, os, re, sys

try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass

def load():
    s = open("index.html", encoding="utf-8").read()
    m = re.search(r"const DATA = (\{.*?\});\n", s, re.S)
    if not m: sys.exit("index.html carries no DATA block — run build.py first")
    return json.loads(m.group(1)), s

def js_parses(page):
    """A stray apostrophe in one string turns the whole page blank. Ask node.
    No node on this machine means this check is skipped, and it says so."""
    import shutil, subprocess, tempfile
    node = shutil.which("node")
    if not node: return None
    m = re.findall(r"<script>(.*?)</script>", page, re.S)
    if not m: return "index.html has no inline script"
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as f:
        f.write(m[-1]); path = f.name
    try:
        r = subprocess.run([node, "--check", path], capture_output=True, text=True)
        if r.returncode:
            head = [l for l in (r.stderr or "").splitlines() if "SyntaxError" in l or ".js:" in l][:2]
            return "the page's javascript does not parse: " + " / ".join(head)
    finally:
        try: os.unlink(path)
        except OSError: pass
    return None


def main():
    D, page = load()
    bad, notes = [], []
    def no(*w): bad.append(" ".join(str(x) for x in w))
    def note(*w): notes.append(" ".join(str(x) for x in w))

    js = js_parses(page)
    if js: no(js)
    if os.path.exists("artifact.html"):
        js2 = js_parses(open("artifact.html", encoding="utf-8").read())
        if js2: no("artifact.html: " + js2)

    Q = D.get("quizzes", {})
    units = {u["id"]: u for u in D.get("units", [])}
    lib = [u for b in D.get("library", []) for c in b["chapters"] for u in c["units"]]

    # --- the library is the whole program ---
    allv = json.load(open("videos.json", encoding="utf-8"))["units"]
    listed = {u["id"] for u in lib}
    for v in allv:
        if v["video_id"] not in listed: no("video missing from the library:", v["video_id"], v["title"])
    for u in lib:
        for f in ("id", "label", "book", "dur"):
            if not u.get(f): no("library row has no", f + ":", u.get("id"))
        if u["id"] not in units: no("library row is not in units:", u["id"])

    # --- quizzes ---
    nq = 0
    for u in lib:
        if u.get("quiz") and u["quiz"]["key"] not in Q:
            no("library links a quiz that does not exist:", u["id"], u["quiz"]["key"])
    for k, q in Q.items():
        ns = [x["n"] for x in q["questions"]]
        if len(set(ns)) != len(ns): no("quiz", k, "has two questions with the same number")
        if ns != sorted(ns): no("quiz", k, "is not in question order")
        for x in q["questions"]:
            nq += 1
            if not x.get("q", "").strip(): no("quiz", k, "question", x["n"], "has no text")
            if len(x.get("choices", {})) < 2: no("quiz", k, "question", x["n"], "has fewer than two choices")
            vals = [str(v).strip().lower() for v in x.get("choices", {}).values()]
            dupes = {v for v in vals if vals.count(v) > 1}
            if dupes: note("quiz", k, "question", x["n"], "prints the same choice twice:", "; ".join(sorted(dupes))[:60])
            if not x.get("answer"): no("quiz", k, "question", x["n"], "has no answer")
            elif x["answer"] not in x.get("choices", {}):
                no("quiz", k, "question", x["n"], "keys", x["answer"], "which is not one of its choices")

    # --- section jumps ---
    ns = 0
    for vid, secs in D.get("sectime", {}).items():
        u = units.get(vid)
        if not u: no("sections for a video that is not in the program:", vid); continue
        for sec, t in secs.items():
            ns += 1
            if not re.match(r"^\d{2,3}\.\d+", sec): no(vid, "has an odd section number:", sec)
            if not (0 <= t <= u["dur"]): no(vid, "section", sec, "jumps to", t, "s in a", u["dur"], "s video")

    # --- a quiz is printed after the lesson it belongs to, never before ---
    for u in lib:
        lp, q = u.get("page"), u.get("quiz") or {}
        if lp and q.get("page") and q["page"] < lp:
            no("quiz page", q["page"], "comes before the lesson page", lp, "for", u["id"])

    # --- the library follows Mike's own checklist order (Theory, the Code volumes
    #     with bonding and grounding in its place, then calculations and exam prep) ---
    MIKE = ["Theory", "NEC Vol 1", "B&G", "NEC Vol 2", "Calcs", "Exam Prep"]
    lib_order = [b["book"] for b in D.get("library", []) if b.get("chapters")]
    if lib_order[:len(MIKE)] != MIKE:
        no("the library is not in Mike Holt's order:", " > ".join(lib_order),
           "against", " > ".join(MIKE))

    # --- a device that still holds finished days must be able to convert them ---
    known = {u["id"] for u in lib}
    dm = D.get("daymap", {})
    if not dm: no("there is no daymap, so a device holding finished days cannot convert them")
    for day, vids in dm.items():
        for v in vids:
            if v not in known: no("day", day, "maps to a video the library does not list:", v)


    print(f"{len(lib)} videos, {len(Q)} quizzes, {nq} questions, {ns} section jumps, "
          f"{sum(1 for u in lib if u.get('page'))} book pages")
    if not __import__("shutil").which("node"): print("(node not installed — the javascript was not parsed)")
    if notes:
        print(f"\n{len(notes)} worth knowing, not failures")
        for t in notes[:20]: print("  ~", t)
    if bad:
        print(f"\n{len(bad)} problems")
        for b in bad[:40]: print("  -", b)
        sys.exit(1)
    print("nothing wrong")

if __name__ == "__main__":
    main()
