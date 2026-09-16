#!/usr/bin/env python3
"""Packs the Mike Holt curriculum (curriculum.json, in watch order) into
weekday sessions of about ninety minutes at 1.5x and writes the DATA block
into index.html. Run it again whenever the plan changes:

    python3 build.py                # start on the next weekday
    python3 build.py 2026-09-21     # start on that day

Rules it follows:
  * Monday to Friday only. Saturday and Sunday are catch-up days: the page
    prints them, but nothing is scheduled on them.
  * Holidays are off (HOLIDAYS below).
  * A day is TARGET_S of video (at 1.5x that is ~90 min). A unit that
    does not fit is split, unless finishing it runs the day to CAP_S.
  * A quiz lands on the day its unit or chapter closes.
  * Three simulated exams on the three Saturdays after the last video.
"""
import json, re, sys, datetime as dt

TARGET_S = 8100    # 2h15 of video = 90 min at 1.5x
CAP_S = 10800      # 3h of video = 2h at 1.5x, the hard ceiling
TAIL_S = 600       # a leftover under 10 min is not worth its own day
SPEED = 1.5
HOLIDAYS = {
    "2026-11-26": "Thanksgiving", "2026-11-27": "Thanksgiving",
    "2026-12-24": "Holidays", "2026-12-25": "Holidays", "2026-12-31": "Holidays", "2027-01-01": "Holidays",
}

C = json.load(open("curriculum.json"))
units = C["units"]
today = dt.date.today()
start = dt.date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else today + dt.timedelta(days=1)
while start.weekday() >= 5 or start.isoformat() in HOLIDAYS:
    start += dt.timedelta(days=1)

# ---- pack the units into days ----
cursor = {"i": 0, "t": C["position"]["at"] if units[0]["id"] == C["position"]["id"] else 0}
days = []
while cursor["i"] < len(units):
    parts, used = [], 0
    while cursor["i"] < len(units):
        u = units[cursor["i"]]
        left = u["dur"] - cursor["t"]
        room = TARGET_S - used
        if left <= room or used + left <= CAP_S and left - room < TAIL_S:
            parts.append({"unit": u, "t": cursor["t"], "end": None, "complete": True})
            used += left; cursor["i"] += 1; cursor["t"] = 0
            if used >= TARGET_S - TAIL_S: break
        else:
            if room < TAIL_S: break
            end = cursor["t"] + room
            parts.append({"unit": u, "t": cursor["t"], "end": end, "complete": False})
            used += room; cursor["t"] = end
            break
    days.append({"parts": parts, "used": used})

# ---- the calendar: a slot per weekday, holidays skipped ----
def next_weekday(d):
    while d.weekday() >= 5 or d.isoformat() in HOLIDAYS:
        d += dt.timedelta(days=1)
    return d

d = next_weekday(start)
for day in days:
    day["date"] = d.isoformat()
    d = next_weekday(d + dt.timedelta(days=1))
last_video = dt.date.fromisoformat(days[-1]["date"])

# ---- words on each card ----
BOOK_FULL = {"Theory": "Electrical Theory", "Calcs": "Fundamental NEC Calculations", "B&G": "Bonding & Grounding"}
def chapter_words(u):
    b, ch, title = u["book"], u["chapter"], u["chapter_title"]
    if b == "Exam Prep":
        return "Exam Prep" if ch in ("intro", "summary") else f"Exam Prep Unit {ch}"
    if b == "Calcs":
        return f"Calcs Ch {ch}"
    if ch == "intro": return f"{b} intro"
    if ch == "ADV": return "B&G advanced 250"
    return title or f"{b} Ch {ch}"

def gh(u):
    b, ch = u["book"], u["chapter"]
    tag = " · Intro" if ch == "intro" else " · Summary" if ch == "summary" else "" if b == "Exam Prep" else f" · Ch {ch}"
    return b + tag + (f" {u['chapter_title']}" if u["chapter_title"] else "") + (f" (pg {u['page']})" if u["page"] else "")

book_last = {}
for i, u in enumerate(units): book_last[u["book"]] = i
BANNER = {"Theory": "THEORY DONE", "NEC Vol 1": "NEC VOL 1 DONE", "Calcs": "CALCS DONE", "Exam Prep": "EXAM PREP DONE", "B&G": "B&G DONE", "NEC Vol 2": "ALL VIDEO DONE"}

sessions = []
idx = 0
for n, day in enumerate(days, 1):
    groups = []
    for p in day["parts"]:
        u = p["unit"]
        key = (u["book"], u["chapter"])
        if not groups or groups[-1]["_key"] != key:
            groups.append({"_key": key, "book": u["book"], "chapter": u["chapter"], "chapter_title": u["chapter_title"], "page": u["page"], "parts": []})
        groups[-1]["parts"].append({"unit": {k: u[k] for k in ("id", "book", "label", "dur", "kind")}, "t": p["t"], "end": p["end"], "complete": p["complete"]})
    for g in groups: del g["_key"]
    heads = []
    for p in day["parts"]:
        w = chapter_words(p["unit"])
        if w not in heads: heads.append(w)
    head = heads[0] if len(heads) == 1 else heads[0] + ", then " + heads[-1]
    quizzes = [p["unit"]["quiz"] for p in day["parts"] if p["complete"] and "quiz" in p["unit"]]
    quiz = "Quiz: " + ", ".join(q["label"].replace(" quiz", "") for q in quizzes) if quizzes else "No quiz today — the chapter continues"
    banner = None
    for p in day["parts"]:
        if p["complete"] and units.index(p["unit"]) == book_last[p["unit"]["book"]]:
            banner = BANNER.get(p["unit"]["book"])
    stop = None
    lp = day["parts"][-1]
    if not lp["complete"]:
        stop = {"unit": lp["unit"] and {k: lp["unit"][k] for k in ("id", "book", "label", "dur", "kind")}, "at": lp["end"]}
    elif n < len(days):
        nu = days[n]["parts"][0]
        stop = {"unit": {k: nu["unit"][k] for k in ("id", "book", "label", "dur", "kind")}, "at": nu["t"]}
    sessions.append({
        "n": n, "date": day["date"], "banner": banner,
        "minutes": round(day["used"] / SPEED / 60),
        "head": head, "note": "on paper" if any(p["unit"]["book"] == "Calcs" for p in day["parts"]) else None,
        "quiz": quiz, "quiz_links": quizzes, "groups": groups, "stop": stop,
    })

# ---- exams: the three Saturdays after the last video ----
sat = last_video + dt.timedelta(days=(5 - last_video.weekday()) % 7 or 7)
exams = []
for k, lines in enumerate([
    ["Timed. Permitted NEC only. No notes, no phones.", "Score together — every miss is a rewatch."],
    ["Same conditions.", "Rewatch every unit missed on Exam 1 first."],
    ["Same conditions.", "80%+ here books PSI. Under, one more week of rewatch and a fourth sitting."],
]):
    exams.append({"n": len(sessions) + k + 1, "date": (sat + dt.timedelta(days=7 * k)).isoformat(), "exam": f"Simulated Exam {k + 1}", "lines": lines})

fmt = lambda d: d.strftime("%b %-d")

# ---- the printed checklist, resolved: how many seconds the stream list holds per row, and which days carry it ----
CAT = {u["video_id"]: u for u in json.load(open("videos.json"))["units"]}
CATBOOK = {"Theory": "Electrical Theory", "NEC Vol 1": "NEC Vol 1", "B&G": "Bonding & Grounding", "NEC Vol 2": "NEC Vol 2", "Calcs": "Fundamental NEC Calculations", "Exam Prep": "Exam Prep"}
checklist = []
for book in C["checklist"]:
    rows = []
    for r in book["rows"]:
        chs = r["ch"] if isinstance(r["ch"], list) else [r["ch"]]
        if book["key"] == "Exam":
            rows.append(dict(r, ours=None, days=[e["n"] for e in exams], done_before=False)); continue
        vids = [v for v in CAT.values() if v["book"] == CATBOOK[book["key"]] and ((v["unit"] if book["key"] == "Exam Prep" else v["chapter"]) in chs or ("intro" in chs and v["kind"] == "intro" and v["chapter"] is None))]
        ours = sum(v["duration_s"] for v in vids)
        ids = {v["video_id"] for v in vids}
        days_ = sorted({s["n"] for s in sessions for g in s["groups"] for p in g["parts"] if p["unit"]["id"] in ids})
        scheduled = {p["unit"]["id"] for s in sessions for g in s["groups"] for p in g["parts"]}
        rows.append(dict(r, ours=ours, days=days_, done_before=bool(ids) and not (ids & scheduled)))
    checklist.append(dict(book, rows=rows))
DATA = {
    "player": C["player"], "books": C["books"], "generated": today.isoformat(),
    "position": C["position"], "done": C["done"], "colors": C["colors"],
    "start": days[0]["date"], "holidays": HOLIDAYS,
    "sessions": sessions, "exams": exams, "checklist": checklist,
    "footer": {
        "how": [
            ["0:00", "Warm-up: 5 timed code lookups (2 calc reps on a calcs day)"],
            ["0:05", "The day's block at 1.5x with captions, NEC open, tabbing as you go"],
            ["Chapter day", "The quiz, on your own, scored before you put the book down"],
            ["Last minute", "Write the stop point on this wall"],
        ],
        "rules": [
            "An hour or two, every weekday. The days are the days.",
            "Miss a day? Saturday and Sunday are for catching up, nothing else. On pace, the weekend is yours.",
            "Never more than two days in the hole. Say so on Friday and the crew watches with you Saturday.",
            "Bring your NEC every day and tab it as you go. Tabs are the only thing you can take into the exam.",
            "Calcs are done on paper, before Mike shows the answer.",
        ],
        "ends": [
            [fmt(last_video), "all video done"],
            [", ".join(fmt(dt.date.fromisoformat(e["date"])) for e in exams), "three simulated exams, Saturdays, real conditions"],
            ["80%+ on Exam 3", "book PSI. Not before."],
            [(sat + dt.timedelta(days=14 + 28)).strftime("%B %Y"), "journeyman exam, for everyone eligible"],
        ],
    },
}

html = open("index.html").read()
new = "const DATA = " + json.dumps(DATA, ensure_ascii=False, separators=(",", ":")) + ";\n"
html, k = re.subn(r"const DATA = \{.*?\};\n", lambda m: new, html, count=1, flags=re.S)
assert k == 1
open("index.html", "w").write(html)

total = sum(d["used"] for d in days)
print(f"{len(days)} weekdays, {days[0]['date']} → {days[-1]['date']}, "
      f"{total / 3600:.1f} h of video = {total / SPEED / 3600:.1f} h at 1.5x, "
      f"avg {total / len(days) / SPEED / 60:.0f} min/day; exams {[e['date'] for e in exams]}")
