#!/usr/bin/env python3
"""What a Sunday sim showed -> one note on the next study night's card (simnotes.json).

Kymani asked (2026-11-20) for each Sunday sim to be read that evening and the week adjusted
from it. The graded sim lives in the browser's saved record on the live site, so the run has
three parts:

    python -X utf8 simreview.py --which            the sim day to review, or "nothing to review"
    python -X utf8 simreview.py --js DAY           two JavaScript expressions to run on the live page
    python -X utf8 simreview.py DAY "A" "B" --write   the review, and the note written to simnotes.json
    python -X utf8 simreview.py --prove            after plan.py: nothing but the note changed

The note is built from the numbers by fixed sentences, so an unattended run cannot say more than
the record does. plan.py lays it on the card as `coach` and refuses a note that is not on a study
night. Nothing else in the plan moves: no question, video, minute or row.
"""
import collections, datetime as dt, json, math, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
def load(name, default=None):
    p = os.path.join(HERE, name)
    if not os.path.exists(p): return default
    return json.load(open(p, encoding="utf-8"))

SIX = load("sixweeks.json")
DAYS = SIX["days"]
DAY = {d["day"]: d for d in DAYS}
OFF = SIX.get("off") or {}
NOTES_PATH = os.path.join(HERE, "simnotes.json")

def notes(): return load("simnotes.json", {}) or {}
def sim_key(d): return "mix:" + d["day"] if "mix" in d["quiz"] else d["quiz"]["key"]
def next_night(day):
    for d in DAYS:
        if d["day"] > day and d["kind"] != "sim" and d["day"] not in OFF: return d["day"]
    return None

def which(today=None):
    today = today or dt.date.today().isoformat()
    done = {n.get("sim") for n in notes().values()}
    sims = [d for d in DAYS if d["kind"] == "sim" and d["day"] <= today]
    if not sims:
        return None, "nothing to review: no sim has come up yet"
    last = sims[-1]
    age = (dt.date.fromisoformat(today) - dt.date.fromisoformat(last["day"])).days
    if last["day"] in done: return None, "nothing to review: the note for the %s sim is already written" % last["day"]
    if age > 2:
        later = [d for d in DAYS if d["kind"] == "sim" and d["day"] > today]
        return None, "nothing to review: the last sim was %s, %d days ago%s" % (last["day"], age, "" if later else "; the plan has no more sims, so this task can be turned off")
    if not next_night(last["day"]): return None, "nothing to review: no study night follows the %s sim" % last["day"]
    return last["day"], ""

# ---- the two expressions the run evaluates on the live page; what they return has no : = ? & in it ----
def js(day):
    k = sim_key(DAY[day])
    head = "(() => { const s = JSON.parse(localStorage.getItem('ptj.v2') || '{}'); const sc = (s.scores || {})[%s]; if (!sc) return 'none'; " % json.dumps(k)
    a = head + ("return ['v1 right ' + sc.right + ' total ' + sc.total + ' secs ' + (sc.secs || 0) + ' allot ' + (sc.allot || 0) + ' when ' + String(sc.when || '').slice(0, 10), "
                "'misses ' + (sc.misses || []).join(' '), 'blanks ' + (sc.blanks || []).join(' '), 'marks ' + (Array.isArray(sc.marks) ? sc.marks.join(' ') : 'x')].join(' | '); })()")
    b = head + "const t = sc.times || {}; return 'times ' + Object.keys(t).map(n => n + '.' + t[n]).join(' '); })()"
    return a, b

def parse(a, b):
    assert a.strip().startswith("v1 "), "the first string does not start with 'v1': %r" % a[:60]
    parts = [x.strip() for x in a.split("|")]
    w = parts[0].split(); head = {w[i]: w[i + 1] for i in range(1, len(w) - 1, 2)}
    sec = {}
    for x in parts[1:]:
        t = x.split(); sec[t[0]] = t[1:]
    marks = None if sec.get("marks") == ["x"] else [int(n) for n in sec.get("marks", [])]
    times = {}
    bt = b.split()
    assert bt and bt[0] == "times", "the second string does not start with 'times': %r" % b[:60]
    for tok in bt[1:]:
        n, t = tok.split("."); times[int(n)] = int(t)
    return {"right": int(head["right"]), "total": int(head["total"]), "secs": int(head["secs"]), "allot": int(head["allot"]), "when": head.get("when", ""),
            "misses": [int(n) for n in sec.get("misses", [])], "blanks": [int(n) for n in sec.get("blanks", [])], "marks": marks, "times": times}

# ---- the sim's questions, numbered the way the page numbers them ----
def questions(day):
    Q = load("quizzes.json"); q = DAY[day]["quiz"]; out = {}
    if "mix" in q:
        n = 0
        for p in q["mix"]:
            for x in Q[p["key"]]["questions"]:
                if p["from"] <= x["n"] <= p["to"]:
                    n += 1; out[n] = dict(x, _key=p["key"])
    else:
        for x in Q[q["key"]]["questions"]: out[x["n"]] = dict(x, _key=q["key"])
    return out

AREAS = [(90, 285, "Wiring and Protection"), (300, 398, "Wiring Methods"), (400, 490, "Equipment"), (500, 590, "Special Occupancies"),
         (600, 695, "Special Equipment"), (700, 840, "Communications and special conditions")]
TOK = re.compile(r"\b\d{2,3}\.\d+[A-Za-z]?(?:\([A-Za-z0-9]+\))*")
def article(q):
    for t in TOK.findall((q.get("ref") or "").split(" · in the 2020 book")[0]):
        a = int(t.split(".")[0])
        if a >= 90: return a
    return None
def area(q):
    a = article(q)
    if a is None:
        return "Chapter 9 tables" if re.search(r"Chapter 9|Annex|Table [1458]\b", q.get("ref") or "") else "Theory and calculations"
    for lo, hi, name in AREAS:
        if lo <= a <= hi: return name
    return "Other"

# the same rule the page uses for its 2020-or-2023 line under a miss (note2023 in index.html)
def changed2023(q):
    ch = {}
    for o in (load("book_changes.json", {}) or {}).values():
        for s, v in o.items():
            if ch.get(s) != "new": ch[s] = v
    mv = {}
    for u, o in (load("moved2020.json", {}) or {}).items():
        if u[0] != "_": mv.update(o)
    arts = set((load("nec2020_articles.json", {}) or {}).get("articles", [])) | {460, 516, 640, 646, 650}
    ref = q.get("ref") or ""
    said = "in the 2020 book" in ref
    for t in TOK.findall(ref.split(" · in the 2020 book")[0]):
        a = int(t.split(".")[0])
        if a < 90: continue
        if arts and a not in arts: return True
        p = t
        while True:
            if p in mv and not said: return True
            if ch.get(p) == "new": return True
            if ch.get(p) == "changed" and p == t: return True
            if "(" not in p: break
            p = p[:p.rindex("(")]
    return False

def review(day, sc):
    d = DAY[day]; qs = questions(day); total = sc["total"]
    assert total == len(qs), "the record says %d questions and the plan's sim has %d" % (total, len(qs))
    assert not sc["when"] or sc["when"] >= (dt.date.fromisoformat(day) - dt.timedelta(days=1)).isoformat(), "this score is dated %s, before the %s sim" % (sc["when"], day)
    need = math.ceil(0.7 * total); wrong = sc["misses"]; blanks = sc["blanks"]; lost = wrong + blanks
    allot = sc["allot"] or d.get("minutes", 0) * 60
    unused = (allot - sc["secs"]) // 60 if allot and sc["secs"] else None
    marks = sc["marks"]
    marked_right = None if marks is None else len([n for n in marks if n not in lost])
    fast = [n for n in wrong if sc["times"].get(n) is not None and sc["times"][n] < 120 and n not in (marks or [])]
    asked = collections.Counter(area(q) for q in qs.values()); miss = collections.Counter(area(qs[n]) for n in lost if n in qs)
    arts = collections.Counter(a for a in (article(qs[n]) for n in lost if n in qs) if a)
    c23 = [n for n in lost if n in qs and changed2023(qs[n])]
    cand = [(miss[a], miss[a] / asked[a], a) for a in asked if miss[a] >= 2]   # the most points lost, not the worst rate on a handful
    worst = max(cand)[2] if cand else None

    # the note: fixed sentences, in the order he needs them, dropped from the end if it runs long
    name = d["title"].split(" · ")[0]
    bits = ["%s: %d of %d. PSI's bar is %d, so you are %s." % (name, sc["right"], total, need, "%d over" % (sc["right"] - need) if sc["right"] >= need else "%d short" % (need - sc["right"]))]
    if blanks: bits.append("%d left blank." % len(blanks))
    if unused is not None and unused >= 10: bits.append("Graded with %d min unused." % unused)
    if marks is not None:
        bits.append("Nothing was marked for a second pass." if not marks else "You marked %d; %d of them came out right." % (len(marks), marked_right))
    if len(fast) >= 3: bits.append("%d wrong answers went in under two minutes, unmarked." % len(fast))
    if blanks: do = "Next Sunday: no blanks. Guess, mark it, move on."
    elif (marks is not None and not marks) or len(fast) >= 5: do = "Next Sunday: mark every answer you did not check in the book, and give the whole second pass to those."
    elif unused is not None and unused >= 10: do = "Next Sunday: the clock is points. Stay until it runs out."
    elif sc["right"] >= need: do = "That passes. Sit the next one the same way."
    else: do = "The method held. The misses come back on the redo nights."
    extra = []
    if worst: extra.append("Most misses: %s, %d of %d." % (worst, miss[worst], asked[worst]))
    if c23: extra.append("%d of the misses cite a rule that changed in 2023: check your book before you count %s." % (len(c23), "it" if len(c23) == 1 else "them"))
    text = " ".join(bits + extra + [do])
    while len(text) > 480 and extra:
        extra.pop(); text = " ".join(bits + extra + [do])
    assert len(text) <= 480, "the note came out %d characters" % len(text)

    rep = ["%s (%s), key %s" % (d["title"], day, sim_key(d)),
           "score %d of %d (%d%%), need %d; wrong %d, blank %d" % (sc["right"], total, round(100 * sc["right"] / total), need, len(wrong), len(blanks)),
           "clock: used %s of %d min%s" % ("%d" % (sc["secs"] // 60) if sc["secs"] else "?", allot // 60, "" if unused is None else ", %d unused" % unused),
           "marks: " + ("not recorded (graded on an older build)" if marks is None else "%d marked, %d of them right, %d of them wrong" % (len(marks), marked_right, len(marks) - marked_right)),
           "wrong in under two minutes and never marked: %d of %d wrong" % (len(fast), len(wrong)),
           "by area (lost of asked): " + "; ".join("%s %d of %d" % (a, miss[a], asked[a]) for a in sorted(asked, key=lambda a: -miss[a])),
           "articles missed most: " + (", ".join("%d x%d" % t for t in arts.most_common(6)) or "none"),
           "misses on a rule that changed in 2023: " + (" ".join("Q%d" % n for n in c23) or "none")]
    if "benchmark" in d["title"].lower():
        pct = 100 * sc["right"] / total
        rep.append("BENCHMARK: %.0f%%. The plan's rule: 80 or better on track; 74 to 79 sit it and taper; under 72 this score alone moves the date. Say which it is at the top of your report." % pct)
    return text, rep

def prove():
    old = json.loads(subprocess.run(["git", "show", "HEAD:sixweeks.json"], cwd=HERE, capture_output=True, text=True, encoding="utf-8", check=True).stdout)
    new = load("sixweeks.json"); bad = []
    A = {d["day"]: d for d in old["days"]}; B = {d["day"]: d for d in new["days"]}
    if list(A) != list(B): bad.append("the days themselves changed")
    for k in A:
        if k in B:
            for f in set(A[k]) | set(B[k]):
                if f != "coach" and A[k].get(f) != B[k].get(f): bad.append("%s: %s changed" % (k, f))
    for f in set(old) | set(new):
        if f not in ("days", "checked") and old.get(f) != new.get(f): bad.append("top level: %s changed" % f)
    if bad: print("NOT ONLY THE NOTE:\n  " + "\n  ".join(bad)); sys.exit(1)
    print("only the note changed: " + (", ".join(k for k in B if B[k].get("coach") != A.get(k, {}).get("coach")) or "no card differs from the last commit"))

if __name__ == "__main__":
    a = sys.argv[1:]
    if a[:1] == ["--which"]:
        day, why = which(a[1] if len(a) > 1 else None)
        print(day if day else why)
    elif a[:1] == ["--js"]:
        x, y = js(a[1]); print("A:\n" + x + "\n\nB:\n" + y)
    elif a[:1] == ["--prove"]:
        prove()
    else:
        day = a[0]; assert day in DAY and DAY[day]["kind"] == "sim", "%s is not a sim day" % day
        if a[1].strip() == "none": print("the sim is not graded yet: nothing written"); sys.exit(2)
        text, rep = review(day, parse(a[1], a[2]))
        night = next_night(day)
        print("\n".join(rep)); print("\nNOTE for %s (%d characters):\n%s" % (night, len(text), text))
        if "--write" in a:
            n = {k: v for k, v in notes().items() if v.get("sim") != day}
            n[night] = {"sim": day, "text": text}
            json.dump(dict(sorted(n.items())), open(NOTES_PATH, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
            print("\nwritten to simnotes.json")
