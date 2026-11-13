#!/usr/bin/env python3
"""Kymani's six weeks to the Maryland Journeyperson exam -> sixweeks.json.

The app (index.html) draws this as his plan when his record holds {kind:'fixed', id:'six'};
the link #plan=six puts it there. Every quiz named here is one of Mike's, already in
quizzes.json, so it is taken and graded on the page and every miss lands in the notebook
the page keeps. Every video stretch is a Mike Holt video the page plays, cut at the second
a section is taught (sections.json). Pages are given both ways: the number printed on the
page, and the number to type in Mike's digital viewer (printed + offset).

THE EXAM (PSI Maryland bulletin, read 2026-11-07): 70 questions, 210 minutes, 49 to pass.
Theory 20 · Wiring & Protection (Art 100–285) 20 · Wiring Methods (300–398) 12 ·
Equipment (400–490) 6 · Special Occupancies 4 · Special Equipment 2 · Communications 6.
No separate calculations section. So every lookup drill, nightly quiz and Sunday sim here
is drawn from POOLS of Mike's questions sorted by the article they cite, in the exam's own
proportions, and no question is handed out twice.

    python3 plan.py && python3 build.py
"""
import datetime as dt, json, re, collections, sys

OFF = {"NEC Vol 1": 20, "B&G": 14, "Calcs": 12, "Exam Prep": 20, "Sim": 8}   # viewer = printed + offset
URL = {"NEC Vol 1": "https://www.mikeholt.com/checkout/#/account/digital-books/book-viewer/23UNEC1-DB/5392",
       "Calcs": "https://www.mikeholt.com/checkout/#/account/digital-books/book-viewer/23FUNDCAL-DB/5383",
       "Exam Prep": "https://www.mikeholt.com/checkout/#/account/digital-books/book-viewer/23EP-DB/5382",
       "B&G": "https://www.mikeholt.com/checkout/#/account/digital-books/book-viewer/23UNECBG-DB/5380"}
S = json.load(open("sections.json", encoding="utf-8"))
V = {v["video_id"]: v for v in json.load(open("videos.json", encoding="utf-8"))["units"]}
Q = json.load(open("quizzes.json", encoding="utf-8"))

def sec(vid, s):
    t = S.get(vid, {}).get(s); assert t is not None, (vid, s); return t
def dur(vid): return V[vid]["duration_s"]
def pages(book, lo, hi=None, what=""):
    o = OFF[book]
    return {"book": book, "printed": f"{lo}–{hi}" if hi else str(lo), "viewer": f"{lo + o}–{hi + o}" if hi else str(lo + o), "what": what, "url": URL.get(book)}
def vid(id_, frm=0, to=None, say=""):
    assert id_ in V, id_
    return {"id": id_, "from": int(frm), "to": int(to if to is not None else dur(id_)), "say": say}

# ---------------- the question pools ----------------
# Every question in these banks, keyed by the article its answer cites; a block is a run of
# articles the bulletin names on one line. Handing out from a pool marks the question used.
BANKS = ["Exam_Prep_Ch_1", "Exam_Prep_Ch_2", "Exam_Prep_Ch_3", "Exam_Prep_Ch_4", "Exam_Prep_Ch_5", "Exam_Prep_Ch_6", "Exam_Prep_Ch_7", "Exam_Prep_Ch_8",
         "NEC_Vol_1_Ch_2", "NEC_Vol_1_Ch_3", "NEC_Vol_1_Ch_4", "NEC_Vol_2_Ch_5", "NEC_Vol_2_Ch_6", "NEC_Vol_2_Ch_7", "NEC_Vol_2_Ch_8"]
BLOCKS = {  # name: (low article, high article)
    "100": (100, 100), "110": (110, 110), "210": (200, 210), "215-225": (215, 225), "230": (230, 230), "240": (240, 240), "242": (242, 242), "250": (250, 285),
    "300": (300, 300), "310": (310, 310), "312-314": (312, 314), "320-330": (320, 330), "332-356": (332, 356), "358-374": (358, 374), "376-398": (376, 398),
    "400-411": (400, 411), "422-427": (422, 427), "430-450": (430, 450), "455-490": (455, 490),
    "500-525": (500, 525), "530-547": (530, 547), "550-590": (550, 590), "600-675": (600, 675), "680-695": (680, 695), "700-708": (700, 708), "720-830": (720, 830),
}
def art_of(q):
    m = re.match(r"^(?:Table\s+)?(\d{3})(?:\.|\b)", q.get("ref") or "")
    return int(m.group(1)) if m else None
ART2020 = set(json.load(open("nec2020_articles.json", encoding="utf-8"))["articles"]) | {460, 516, 640, 646, 650}
POOL = collections.defaultdict(list)   # block -> [(key, n), ...] in bank order
for key in BANKS:
    for q in Q[key]["questions"]:
        a = art_of(q)
        if a is None or a not in ART2020: continue   # a 2023-only article is not on his exam
        for name, (lo, hi) in BLOCKS.items():
            if lo <= a <= hi: POOL[name].append((key, q["n"])); break
USED = set()
def used_range(key, lo, hi):
    for n in range(lo, hi + 1):
        assert (key, n) not in USED, ("handed out twice", key, n); USED.add((key, n))
import difflib
QN = {(k, q["n"]): q for k in Q for q in Q[k]["questions"]}
def _sig(x): return re.sub(r"[^a-z0-9]+", " ", QN[x]["q"].lower()).strip()
# wording that is handed out by a fixed quiz built later in this file but sat earlier on the calendar
RESERVED = [(k, q["n"]) for k in ("Simulated_Exams_Exam_A", "Simulated_Exams_Exam_B", "Exam_Prep_Module_I_Practice_Exam") for q in Q[k]["questions"]]
NEW2023 = {s for d in json.load(open("book_changes.json", encoding="utf-8")).values() for s, v in d.items() if v == "new"}
NOT2020 = {("Exam_Prep_Ch_2", 87), ("Exam_Prep_Ch_2", 110), ("NEC_Vol_1_Ch_2", 21), ("NEC_Vol_1_Ch_2", 26), ("NEC_Vol_1_Ch_2", 31), ("Exam_Prep_Ch_2", 143),
           ("Exam_Prep_Ch_4", 35), ("Exam_Prep_Ch_4", 38), ("Exam_Prep_Ch_7", 38), ("Exam_Prep_Ch_7", 39), ("Exam_Prep_Ch_7", 40),
           ("NEC_Vol_1_Ch_4", 17), ("NEC_Vol_1_Ch_4", 14), ("NEC_Vol_1_Ch_4", 49), ("Exam_Prep_Ch_7", 79), ("Exam_Prep_Ch_7", 80), ("NEC_Vol_2_Ch_5", 161),
           ("Exam_Prep_Ch_2", 69), ("Exam_Prep_Ch_2", 76), ("Exam_Prep_Ch_2", 84), ("NEC_Vol_1_Ch_2", 33), ("Exam_Prep_Ch_7", 157), ("Exam_Prep_Ch_7", 158), ("Exam_Prep_Ch_7", 163)}
NOT2020 |= {("Exam_Prep_Ch_7", n) for n in range(23, 30)}   # 700.11, Class 2 emergency circuits: 2023 only
def _new2023(x):
    m = re.match(r"^(?:Table\s+)?(\d{3}\.\d+)((?:\([A-Za-z0-9]{1,4}\))*)", QN[x].get("ref") or "")
    if not m: return False
    g = re.findall(r"\([A-Za-z0-9]{1,4}\)", m.group(2))
    return any(m.group(1) + "".join(g[:i]) in NEW2023 for i in range(len(g) + 1))
_TOK = {}
def _tok(x):
    if x not in _TOK: s = _sig(x); _TOK[x] = (s, frozenset(s.split()), re.findall(r"\d+", s))
    return _TOK[x]
class Seen:
    """every wording handed out so far, by article; near-identical wording counts as seen"""
    def __init__(self, items):
        self.b = collections.defaultdict(list)
        for x in items: self.add(x)
    def add(self, x): self.b[art_of(QN[x])].append(_tok(x))
    def has(self, x):
        s, w, d = _tok(x)
        for t, v, e in self.b[art_of(QN[x])]:
            if t == s: return True
            if d == e and len(w & v) >= 0.6 * len(w | v) and difflib.SequenceMatcher(None, s, t).ratio() >= 0.88: return True
        return False
FROZEN = True   # the nights already sat are dealt exactly as they were; False from the first night not yet sat
def take(block, n, fresh=False, strict=True):
    """the next n unused questions of a block. fresh=True (the sims): no wording already handed
    out under any key, nothing new in 2023, spread across the block instead of its first sections"""
    if not fresh:
        items = [x for x in POOL[block] if x not in USED and (FROZEN or x not in NOT2020)][:n]
    else:
        seen = Seen(list(USED) + RESERVED); cand = []
        for x in POOL[block]:
            if x in USED or x in NOT2020 or _new2023(x) or seen.has(x): continue
            seen.add(x); cand.append(x)
        items = [cand[int((i + 0.5) * len(cand) / n)] for i in range(n)] if len(cand) >= n else cand
        if len(items) < n and not strict:   # a practice sim may fall back to the next unused ones
            items += [x for x in POOL[block] if x not in USED and x not in items][:n - len(items)]
    assert len(items) == n, (f"pool {block} short: wanted {n}, have {len(items)}")
    USED.update(items)
    return items
def ranges(items):
    out = []
    for key, n in items:
        if out and out[-1]["key"] == key and out[-1]["to"] == n - 1: out[-1]["to"] = n
        else: out.append({"key": key, "from": n, "to": n})
    return out
def quiz(key, lo=None, hi=None, retake=None):
    """retake=(lo, hi): questions already handed out that this quiz gives again on purpose"""
    assert key in Q, key
    N = len(Q[key]["questions"])
    if lo is None: lo, hi = 1, N
    assert 1 <= lo <= hi <= N, (key, lo, hi, N)
    if retake: assert lo == retake[0] and retake[1] < hi; used_range(key, retake[1] + 1, hi)
    else: used_range(key, lo, hi)
    return {"key": key, "from": lo, "to": hi} if (lo, hi) != (1, N) else {"key": key}
def mix(name, parts, minutes):
    """several ranges, one sitting, one score"""
    return {"mix": [dict(p, **({"from": 1, "to": len(Q[p["key"]]["questions"])} if "from" not in p else {})) for p in parts], "name": name, "minutes": minutes}
def pool_quiz(name, spec, minutes=30):
    """spec: [(block, n), ...] -> one mixed quiz from the pools"""
    items = []
    for block, n in spec: items += take(block, n)
    return mix(name, ranges(items), minutes)

# the lookup drill: fifteen of Mike's code questions a night, code book only, 90 s each;
# the week's six nights walk the whole Code the way the bulletin lists it
DRILL = {
    1: [[("100", 8), ("110", 7)], [("210", 15)], [("300", 15)], [("400-411", 15)], [("500-525", 15)], [("700-708", 15)]],
    2: [[("110", 15)], [("215-225", 15)], [("312-314", 15)], [("422-427", 7), ("430-450", 8)], [("600-675", 8), ("680-695", 7)], [("720-830", 15)]],
    3: [[("100", 15)], [("230", 15)], [("320-330", 3), ("332-356", 12)], [("430-450", 15)], [("530-547", 5), ("550-590", 10)], [("700-708", 15)]],
    4: [[("210", 3), ("240", 3), ("242", 1), ("376-398", 2), ("400-411", 3), ("500-525", 2), ("680-695", 1)],
        [("210", 3), ("240", 2), ("242", 1), ("358-374", 1), ("376-398", 2), ("400-411", 3), ("500-525", 2), ("680-695", 1)],
        [("210", 3), ("240", 2), ("242", 1), ("358-374", 1), ("376-398", 3), ("400-411", 3), ("500-525", 1), ("680-695", 1)],
        [("210", 4), ("240", 2), ("358-374", 1), ("376-398", 3), ("400-411", 3), ("500-525", 1), ("680-695", 1)],
        [("210", 3), ("240", 2), ("376-398", 2), ("400-411", 3), ("500-525", 2), ("680-695", 3)]],
}
DRILL_NAME = {1: ["Art 100–110", "Art 200–210", "Art 300", "Art 400–411", "Art 500–525", "Art 700–708"],
              2: ["Art 110", "Art 215–225", "Art 312–314", "Art 422–450", "Art 600–695", "Art 720–830"],
              3: ["Art 100", "Art 230", "Art 320–356", "Art 430–450", "Art 530–590", "Art 700–708"],
              4: ["mixed, say the article first"] * 5}
def drill(week, dow): return pool_quiz("Lookup drill · " + DRILL_NAME[week][dow], DRILL[week][dow], 30)

D = dt.date
days = []
def add(day, kind, title, **k):
    k.setdefault("steps", []); k.setdefault("video", []); k.setdefault("stars", []); k.setdefault("pages", [])
    days.append(dict(day=day.isoformat(), kind=kind, title=title, **k))

# ---- Sat Nov 7: the restart ----
add(D(2026, 11, 7), "setup", "Restart night",
    steps=["Sim Exams book, Ch 2 How to Use the NEC (printed p7–8). Read it once, 15 min.",
           "Sim Exams book, Ch 4 test-taking tips (printed p59–62). 5 min.",
           "Check the code book against PSI's rules: tabs must be permanent plastic (Avery Swift Tabs or Redi-Tag), not Post-it flags; highlighter is fine, pen anywhere in the book is not; nothing loose inside."],
    drill=quiz("Exam_Prep_Art_90", 1, 13), quiz=quiz("Exam_Prep_Module_II_Practice_Exam", 1, 20),
    note="Light night. Sim A tomorrow, 4 hours, start by 9 am.")

# ---- Week 1 (written dates Nov 9-12; the first three are done and must not change) ----
A, B = "23UNECBGArticle250PartA", "23UNECBGArticle250PartB"
U1, U2, U3, U4, U5, U6 = "23EPUnit1", "23EPUnit2", "23EPUnit3edit", "23EPUnit4", "23EPUnit5", "23EPUnit6"
W1 = [
    ("Art 250 Part I · the effective ground-fault current path",
     [vid(A, sec(A, "250.1"), 4000, "Mike opens 250: scope, 250.4(A)(1)–(5) and (B), what grounding is for")],
     [pages("B&G", 127, 137, "Art 250 intro and Part I")],
     ["Highlight 250.4 and 250.6 in the 2020 book as he reads them: blue over the heading, yellow after shall, red highlighter under the numbers. Highlighter only, never pen."],
     quiz("B&G_Art_250", 1, 20), [A]),
    ("Art 250 Part I · objectionable current, connections",
     [vid(A, 4000, sec(A, "250.24"), "250.6 objectionable current, 250.8 connection methods, 250.10, 250.12")],
     [pages("B&G", 134, 137, "250.6 to 250.12")],
     ["Finish highlighting Part I."],
     quiz("B&G_Art_250", 21, 40), [A]),
    ("Art 250 Part II · service grounding, bonding jumpers, separately derived systems",
     [vid("GroundingandBondingServiceEquipment25024", 0, None, "250.24: where the grounded conductor lands and why nowhere else"),
      vid("TransformerSeparatelyDerivedSystems25030", 0, None, "250.30(A)(1)–(8)"),
      vid("BuildingsSuppliedbyaFeeder25032", 0, None, "250.32: a second building on a feeder")],
     [pages("B&G", 138, 153, "Part II")],
     ["The quiz is last night's twenty again, now that the video has taught them, plus the six that finish Part II. Each night's quiz covers that night's video or earlier, never ahead of it.",
      "Work five supply-side bonding jumper sizes from Table 250.102(C)(1). Highlight 250.24(A)(1), (A)(5), (B), (C); 250.28(D); 250.30(A); 250.32(A), (B)(1).", "The generator video (250.30 for generators, 19 min) is for the drive, not tonight."],
     quiz("B&G_Art_250", 21, 46, retake=(21, 40)), [A]),
    # Fri Nov 13 (written Nov 12): theory comes forward, ahead of Sunday's twenty theory questions
    ("Theory I · Ohm's law, Watt's law, the formula wheel",
     [vid("ETC5U12", 0, None, "Unit 12 Ohm's law"), vid("ETC5U13", 0, None, "Unit 13 Watt's law"), vid("ETC10U29", 0, None, "Unit 29 the formula wheel")],
     [pages("Exam Prep", 19, 28, "Units 12–13"), pages("Exam Prep", 105, 107, "Unit 29")],
     ["Sim #1 said theory 2 of 10, and theory is 20 of the 70 on the real exam; the next sim has twenty of them. Pen and paper the whole hour: every example Mike works, you work first. E = I × R, P = E × I, and the wheel for the rest."],
     mix("Theory · Ohm's and Watt's law", [quiz("Exam_Prep_Unit_12", 1, 11), quiz("Exam_Prep_Unit_13", 1, 9)], 30), []),
]
for i, (title, video, pg, steps, q, stars) in enumerate(W1):
    add(D(2026, 11, 9) + dt.timedelta(days=i), "study", title, video=video, stars=stars, pages=pg, steps=steps, drill=drill(1, i), quiz=q)
FROZEN = False

# ---- Nov 16 to Dec 5: every night on its own date; (week, night) names its lookup drill ----
NIGHTS = [
    (D(2026, 11, 16), (1, 4), "Art 250 Part III · electrodes and the grounding electrode conductor",
     [vid(A, sec(A, "250.50"), sec(A, "250.54"), "250.50 to 250.53: every electrode, the rod rules"),
      vid(A, sec(A, "250.64"), sec(A, "250.70"), "250.64 the GEC, Table 250.66, 250.68")],
     [pages("B&G", 154, 172, "Part III")],
     ["Work five Table 250.66 problems, with the 6 AWG rod cap and the 4 AWG concrete-encased cap. Highlight 250.52(A), 250.53(A), 250.64, 250.66, 250.68."],
     mix("Art 250 · electrodes and the GEC", [quiz("B&G_Art_250", 47, 58), quiz("B&G_Art_250", 62, 66), quiz("B&G_Art_250", 89, 91)], 30), [A]),
    (D(2026, 11, 17), (1, 5), "Art 250 Parts V–VI · the bonding jumper and the equipment grounding conductor",
     [vid(B, sec(B, "250.102"), sec(B, "250.104"), "250.102: bonding jumpers, Table 250.102(C)(1)"),
      vid(B, sec(B, "250.118"), sec(B, "250.119"), "250.118: what counts as an EGC"),
      vid(B, sec(B, "250.122"), sec(B, "250.138"), "250.122 and its table")],
     [pages("B&G", 173, 201, "Parts IV to VII: read 250.92, 250.94, 250.104, 250.146, 250.148 from the star list")],
     ["Five bonding jumper sizes, supply side by 250.102(C)(1); five EGCs by Table 250.122, two with the proportional upsizing in (B). 250.140 in your 2020 book is the main paragraph and its exception, not an (A). The rest of Parts IV to VII is lookup: highlight it from the star list, do not watch it."],
     mix("Art 250 · bonding jumpers and EGCs", [quiz("B&G_Art_250", 123, 127), quiz("B&G_Art_250", 141, 146), quiz("B&G_Art_250", 151, 158)], 30), [B]),
    (D(2026, 11, 18), (2, 0), "Theory II · series and parallel circuits",
     [vid("ETC6U14", 0, None, "Unit 14 series circuits"), vid("ETC6U15", 0, None, "Unit 15 parallel circuits")],
     [pages("Exam Prep", 31, 46, "Units 14–15")],
     ["On paper: resistors in series add; in parallel 1/R = 1/R1 + 1/R2 + 1/R3, and equal resistors in parallel are R ÷ n (three 5 Ω in parallel is 1.66 Ω). Voltage divides across series resistors by their share of the resistance."],
     mix("Theory · series and parallel", [quiz("Exam_Prep_Unit_14", 1, 10), quiz("Exam_Prep_Unit_15", 1, 10)], 30), []),
    (D(2026, 11, 19), (2, 1), "Box fill and pull boxes · 314.16, 314.28",
     [vid(U2, 0, None, "Unit 2 whole: Table 314.16(A), 314.16(B), then 8× straight, 6× angle and U pulls")],
     [pages("Exam Prep", 265, 278, "Unit 2")],
     ["Work five box fills with mixed sizes, a device yoke and an EGC, and three pull boxes: straight, angle, several raceways on one wall. Highlight 314.16(A), (B)(1)–(5), 314.28(A)(1)–(3)."],
     quiz("Exam_Prep_Unit_2", 1, 20), []),
    (D(2026, 11, 20), (2, 2), "Dwelling load · the standard method, Table 220.55",
     [vid(U6, 0, 4640, "Unit 6, first half")],
     [pages("Exam Prep", 369, 382, "Unit 6 Parts A and B")],
     ["Work example 6.13 start to finish on paper before Mike finishes it. In the 2020 book the lighting load is 220.12 and the demand table is Table 220.42. PSI's own sample question is a range off Table 220.55: do three of those."],
     quiz("Exam_Prep_Unit_6", 1, 20), []),
    (D(2026, 11, 21), (2, 3), "Theory III · alternating current",
     [vid("ETC7U17", 0, None, "Unit 17 AC fundamentals: frequency, peak and RMS, phase")],
     [pages("Exam Prep", 55, 62, "Unit 17")],
     ["On paper: RMS = peak × 0.707, peak = RMS × 1.414. The quiz is the rest of parallel circuits from the last theory night; Unit 17's own questions come on the next one."],
     quiz("Exam_Prep_Unit_15", 11, 22), []),
    (D(2026, 11, 23), (2, 4), "Article 230 · services", [],
     [pages("NEC Vol 1", 197, 222, "Art 230, no video tonight: read it with the book open")],
     ["230.2 number of services, 230.6 outside a building, 230.9 clearances, 230.24 overhead clearances, 230.42 sizing, 230.43 wiring methods, 230.70–230.72 the disconnect, 230.79 ratings, 230.85 emergency disconnect, 230.90 overload protection.",
      "Highlight the whole article from its ★ list."],
     pool_quiz("Art 230 · 15 timed", [("230", 15)], 25), ["23UNEC1Article230"]),
    (D(2026, 11, 24), (2, 5), "Theory IV · power factor, series-parallel",
     [vid("ETC7U20", 0, None, "Unit 20 true power, power factor, apparent power"), vid("ETC6U16", 0, None, "Unit 16 series-parallel circuits")],
     [pages("Exam Prep", 67, 73, "Unit 20"), pages("Exam Prep", 51, 52, "Unit 16")],
     ["On paper: PF = W ÷ VA; VA = E × I, × 1.732 for three-phase. Work every example before Mike does. The quiz is Unit 17, from the last theory night."],
     quiz("Exam_Prep_Unit_17", 1, 20), []),
    (D(2026, 11, 25), (3, 0), "Raceway fill · Chapter 9 and Annex C",
     [vid(U1, 0, 4318, "Unit 1, first half: Tables 1, 4, 5 and Annex C")],
     [pages("Exam Prep", 241, 258, "Unit 1")],
     ["Work six fills: three straight from Annex C, three with mixed sizes through Tables 4 and 5. Note 7: round up at 0.8. Note 4: nipples at 60%. Wireways are 20% (376.22). Tab Annex C by raceway type (permanent tabs)."],
     quiz("Exam_Prep_Unit_1", 1, 20), []),
    (D(2026, 11, 26), (3, 1), "Wiring methods · Art 300 and the cable and raceway articles (no video)", [],
     [pages("NEC Vol 1", 339, 366, "Art 300: 300.4, 300.5 and its table, 300.11, 300.14")],
     ["Every 3xx article is numbered alike: .10 uses permitted, .12 not permitted, .24 bends, .30 support. Learn that once and twelve of the seventy are lookups.",
      "Highlight 300, 320, 330, 334, 344, 352, 358 from their ★ lists."],
     pool_quiz("Art 300–356 · 20 timed", [("300", 10), ("332-356", 10)], 30),
     ["23UNEC1Article300", "23UNEC1Article334", "23UNEC1Article358", "23UNEC1Article320", "23UNEC1Article330", "23UNEC1Article344", "23UNEC1Article352"]),
    (D(2026, 11, 27), (3, 2), "Voltage drop · the formula",
     [vid(U5, 0, None, "Unit 5 whole: circular mils, Table 8, 2KID/CM and the three-phase 1.732")],
     [pages("Exam Prep", 351, 364, "Unit 5")],
     ["Work six: three single-phase, three three-phase, in volts and in percent. 3% and 5% are informational notes under 210.19 and 215.2."],
     quiz("Exam_Prep_Unit_5", 1, 20), []),
    (D(2026, 11, 28), (3, 3), "Theory V · transformers and generators",
     [vid("ETC8U24", 0, 2820, "Unit 24 transformers, the first 47 minutes: ratios, kVA, primary and secondary current"), vid("ETC8U22", 0, None, "Unit 22 generators")],
     [pages("Exam Prep", 91, 96, "Unit 24"), pages("Exam Prep", 83, 84, "Unit 22")],
     ["On paper: a 4:1 transformer divides voltage by 4 and multiplies current by 4; I = VA ÷ (E × 1.732) for three-phase. The quiz is Unit 20, from the last theory night."],
     quiz("Exam_Prep_Unit_20", 1, 20), []),
    (D(2026, 11, 30), (3, 4), "Conductor sizing · insulation, terminals, ampacity, Art 310",
     [vid(U3, 0, 4431, "Unit 3, first half: 110.14(C), 240.4, Table 310.16, correction and adjustment")],
     [pages("Exam Prep", 283, 296, "Unit 3 Parts A and B to 3.9")],
     ["Work six: pick from the 75°C column, then check against the corrected 90°C ampacity. In the 2020 book the insulation table is Table 310.4(A). Highlight Art 310 from its ★ list: 310.10, 310.12 and Table 310.12(A), 310.15(B), (C), (E), Table 310.16."],
     quiz("Exam_Prep_Unit_3", 1, 20), ["23UNEC1Article310"]),
    (D(2026, 12, 1), (3, 5), "Article 240 · overcurrent protection, feeders and taps",
     [vid("23UNEC1Article240", 0, None, "Art 240 whole"), vid(U3, sec(U3, "215.2"), None, "Unit 3, the end: 215.2, 215.3, the tap rules of 240.21(B)")],
     [pages("NEC Vol 1", 223, 246, "Art 240")],
     ["Memorize 240.6(A). Highlight the whole article from its ★ list; 240.4(B), 240.4(D), 240.21(B) and (C), 240.24 first."],
     quiz("Exam_Prep_Unit_3", 64, 78), ["23UNEC1Article240"]),
    (D(2026, 12, 2), (4, 0), "Motors · full-load current and conductors",
     [vid(U4, 0, 3150, "Unit 4, the first 52 minutes: the FLC tables 430.248 and 430.250, conductors by 430.22, duty cycle")],
     [pages("Exam Prep", 315, 334, "Unit 4 Part A")],
     ["Work three motors on paper: FLC from the table, never the nameplate, then the conductor at 125% by 430.22. Highlight Art 430 from its ★ list; tab Table 430.52 and the FLC tables."],
     quiz("Exam_Prep_Unit_4", 1, 19), ["23UNEC1Article430"]),
    (D(2026, 12, 3), (4, 1), "Motors · overloads, the breaker, the equipment grounding conductor",
     [vid(U4, 3150, 7254, "Unit 4, the middle: overloads 430.32, short-circuit and ground-fault protection by Table 430.52, the EGC by 250.122(D)")],
     [pages("Exam Prep", 315, 344, "Unit 4")],
     ["Finish the three motors from the last motor night: the overload by 430.32, the breaker by Table 430.52 and 430.52(C)(1) Ex 1, the EGC."],
     quiz("Exam_Prep_Unit_4", 20, 39), []),
    (D(2026, 12, 4), (4, 2), "Motor feeders, air conditioning, transformers · Art 422, 424, 440",
     [vid(U4, 7254, None, "Unit 4, the end: feeders 430.24 and 430.62, air conditioning 440, transformers 450.3")],
     [pages("NEC Vol 1", 589, 600, "Art 422 and 424")],
     ["One feeder for three motors, conductor and breaker. Then highlight 422, 424 and 440 from their ★ lists: 422.10, 422.11, 422.16 cords, 422.31 disconnects, 424.3, 440.4(B), 440.14. Six of the seventy are Articles 400–490."],
     quiz("Exam_Prep_Unit_4", 40, 62), ["23UNEC1Article422", "23UNEC1Article424", "23UNEC1Article440"]),
]
for day, (wk, n), title, video, pg, steps, q, stars in NIGHTS:
    add(day, "study", title, video=video, pages=pg, steps=steps, drill=drill(wk, n), quiz=q, stars=stars)
THEORY_RE = r"^(Theory\b|\d{1,2}\.\d)"
add(D(2026, 12, 5), "notebook", "Theory VI · every theory miss, then twenty mixed", redo=THEORY_RE,
    what="Every theory miss from Sims #1 to #4 and the theory nights, redone on paper. Twenty of benchmark 1's seventy are theory.",
    steps=["", "Then ten formula-wheel questions from Exam Prep Unit 29 (printed p105–107), each one written out: what is given, what is asked, which formula."],
    drill=drill(4, 3), quiz=mix("Theory · 20 timed", [quiz("Exam_Prep_Module_I_Practice_Exam", 41, 50), quiz("Exam_Prep_Unit_24", 1, 10)], 30))

# ---- Week 5 · the notebook, and one night of lookups ----
W5 = [
    ("All sim misses, cold", r"^", "Every miss from Sims #1–#5. Redo them below without looking at the old answer; anything missed twice is red and comes back on the twice-missed night.",
     ["Lookup drill: shut the book, then find the section of each sim miss in under 60 seconds. Time every one."],
     quiz("Exam_Prep_Module_III_Practice_Exam", 1, 20)),
    ("250, 220 and 314 misses", r"^(Table\s+)?(250|220|314)\.", "Every grounding, load-calc and box-fill miss. For each, read the whole section in the 2020 book, not just the line. Then Exam Prep 6.13 once more, on paper.",
     ["Lookup drill: Table 250.66, Table 250.102(C)(1), Table 250.122, Table 220.55 and its notes, Table 220.42, 314.16(B), 314.28(A), blind and timed."],
     mix("Art 250 · the grounding electrode conductor", [quiz("B&G_Art_250", 76, 87), quiz("B&G_Art_250", 92, 99)], 30)),
    ("Chapter 9, voltage drop and 310 misses", r"^(Table\s+)?(310\.|Chapter 9|Ch\.? 9|Annex|Table [1458]\b)", "Every conduit-fill, voltage-drop and ampacity miss. Two fresh fills, two fresh drops, two corrections with both factors.",
     ["Lookup drill: Ch 9 Tables 1, 4, 5, 8, Annex C, Table 310.16, 310.15(B)(1), 310.15(C)(1), blind and timed."],
     pool_quiz("Art 310 · 20 timed", [("310", 20)], 30)),
    ("240, 430, 440 misses", r"^(Table\s+)?(240|430|440|450)\.", "Every overcurrent, motor and AC miss. One full motor circuit, end to end.",
     ["Lookup drill: 240.6(A), 240.21(B), Table 430.52, 430.248, 430.250, 430.110, 440.4(B), blind and timed."],
     quiz("Exam_Prep_Module_III_Practice_Exam", 21, 40)),
    ("Twice-missed, and theory", r"^", "Everything red. Then the Theory questions below: 20 of the 70 are theory, the biggest block on the exam.",
     ["Lookup drill: twenty random index words from the 2020 book, 60 seconds each."], quiz("Theory_Final_Exam", 21, 40)),
]
for i, (title, redo, what, steps, q) in enumerate(W5):
    add(D(2026, 12, 7) + dt.timedelta(days=i), "notebook", title, redo=redo, what=what, steps=steps, quiz=q)
# Sat Dec 12: the last night, and the one that falls off if another night is lost
add(D(2026, 12, 12), "study", "Chapters 7 and 8 · emergency systems, fire alarm, where the rest lives",
    video=[vid("23UNEC2Article700", 0, sec("23UNEC2Article700", "700.12"), "Art 700 to 700.12: tests, transfer equipment, wiring kept apart"), vid("23UNEC2Article760", 0, None, "Art 760 fire alarm")], pages=[],
    steps=["Six of the seventy are Articles 700–830. In the 2020 book find, by the index and without the contents page: 700.10(B), 700.12, 701.12, 702.5, 725.121, 725.136, 760.41, 760.121, 800.24, 810.21. Mike's video is the 2023 Code: where a number differs, yours is the 2020 one in the book.",
      "Read the scope (.1) of 700, 701, 702, 725, 760, 770, 800, 810, 820: one line each, so a question names its article."],
    drill=drill(4, 4), quiz=pool_quiz("Art 700–830 · 20 timed", [("700-708", 10), ("720-830", 10)], 30))

# ---- the Sunday sims: Mike's two mixed exams, four in Maryland's own shape ----
def md_mix(k, theory):
    """70 questions in the bulletin's proportions, from the pools; nothing shared with any other night"""
    parts = list(theory)
    for block, n in [("100", 2), ("110", 2), ("210", 3), ("215-225", 3), ("230", 3), ("240", 3), ("250", 4),
                     ("300", 2), ("310", 2), ("312-314", 1), ("320-330", 1), ("332-356", 3), ("358-374", 1), ("376-398", 2),
                     ("400-411", 2), ("422-427", 1), ("430-450", 3),
                     ("500-525", 2), ("530-547", 1), ("550-590", 1), ("600-675", 1), ("680-695", 1), ("700-708", 3), ("720-830", 3)]:
        parts += ranges(take(block, n, fresh=True, strict=k >= 3))
    assert sum(p["to"] - p["from"] + 1 for p in parts) == 70, sum(p["to"] - p["from"] + 1 for p in parts)
    return mix(f"Maryland mix {k}", parts, 210)
SIM_STEPS = lambda mins, n=70: [
    "Start by 9 am. " + ("Four hours" if mins == 240 else "3½ hours") + " on the clock, 2020 code book only, phone face down.",
    f"Checkpoints: {n} questions in {mins} minutes is {mins / n:.1f} minutes each. At 60 min you have answered {round(60 * n / mins)}; at 120 min, {round(120 * n / mins)}. Behind that, best-guess the flagged ones and move. No scheduled break; the clock runs if you leave the room.",
    "Grade when time is called, not before. Then read every miss; press Rewatch where it offers one. Theory misses first: open the Exam Prep unit the reference names and work that example on paper. Review stops at 60 min: the misses are in the notebook, and the notebook nights redo them."]
def theory_fresh():
    seen = Seen(list(USED) + RESERVED); cand = []
    for n in range(41, 91):
        x = ("Theory_Final_Exam", n)
        if x in USED or seen.has(x): continue
        seen.add(x); cand.append(x)
    # the theory nights use up some of that wording; the rest comes one at a time from Mike's
    # unit banks, round the units the exam leans on, until there are forty
    units = [12, 14, 15, 17, 20, 21, 24, 25, 13, 16, 22]; i = 0
    while len(cand) < 40 and i < 400:
        k = "Theory_Unit_%d" % units[i % len(units)]; i += 1
        qs = [(k, q["n"]) for q in Q[k]["questions"]]
        for x in qs[len(qs) // 2:] + qs[:len(qs) // 2]:
            if x in USED or x in cand or seen.has(x): continue
            seen.add(x); cand.append(x); break
    assert len(cand) >= 40, len(cand)
    cand = cand[:40]
    return cand[0:40:2], cand[1:40:2]
_T1, _T2 = theory_fresh(); USED.update(_T1 + _T2)
_B1 = md_mix(3, ranges(_T1)); _B2 = md_mix(4, ranges(_T2))   # the benchmarks draw first: they get the unseen questions
SIMS = [
    (D(2026, 11, 8), "Sim #1 · baseline", quiz("Simulated_Exams_Exam_A"), 240, "Mike's Exam A, 100 questions, 4 hours. Whatever the score, it is the starting line. On paper, note the clock at every tenth question: your real pace, from day one."),
    (D(2026, 11, 15), "Sim #2 · Maryland shape", md_mix(1, [quiz("Exam_Prep_Module_I_Practice_Exam", 1, 20)]), 210, "70 questions in PSI Maryland's own proportions, 3½ hours. 49 right passes the real one. Twenty of them are theory, mixed in with the rest."),
    (D(2026, 11, 22), "Sim #3", quiz("Simulated_Exams_Exam_B"), 240, "Mike's Exam B, 100 questions, 4 hours: the one code-wide stress test. Heavier on Chapters 5–8 than Maryland is."),
    (D(2026, 11, 29), "Sim #4 · Maryland shape", md_mix(2, [quiz("Exam_Prep_Module_I_Practice_Exam", 21, 40)]), 210, "70 questions, 3½ hours, Maryland's proportions."),
    (D(2026, 12, 6), "Sim #5 · benchmark 1", _B1, 210, "Benchmark 1, in the exam's shape. 80 or better (56 of 70): on track. 74–79: sit it and taper. Under 72 (50): this score alone moves the date, today, while a reschedule is still free."),
    (D(2026, 12, 13), "Sim #6 · benchmark 2", _B2, 210, "Benchmark 2, same shape. Both benchmarks 80 or better: sit it. Both 74–79: sit it; Mike's questions run harder than PSI's. Either under 72: the holding weeks below, and the date moves."),
]
for day, title, q, mins, note in SIMS:
    add(day, "sim", title, quiz=q, minutes=mins, note=note, steps=SIM_STEPS(mins, sum(p["to"] - p["from"] + 1 for p in q["mix"]) if "mix" in q else len(Q[q["key"]]["questions"])))

# ---- exam week, and the holding weeks if PSI's date comes later ----
for i, (title, steps) in enumerate([
    ("Taper, one hour", ["30 min lookup drill from the notebook, then 20 timed questions from any sim you have not re-sat. No new material."]),
    ("Taper, one hour", ["Same. Rework only what is still red in the Missed questions fold."]),
    ("Taper, one hour", ["Same. Call PSI once: arrival time, what ID they want. The bulletin gives an on-screen calculator and nothing else: use the computer's calculator on every quiz from today."]),
    ("Taper, one hour", ["Lookup drill only. Pack: the 2020 NEC, tabbed with permanent plastic tabs only (no Post-it flags, no paper inserts, nothing written in it, nothing loose), two forms of ID with the name on the application, the PSI confirmation."]),
    ("Night before", ["Sim Exams book Ch 4 (printed p59–62). Nothing else. No swim in the morning, or a short easy one done two hours before the slot. In bed early."]),
    ("Exam day", ["Breakfast. Arrive 30 minutes early. Read every question twice before touching the book. Flag the long ones and come back. 49 right is a pass."]),
]):
    add(D(2026, 12, 14) + dt.timedelta(days=i), "taper", title, steps=steps)
# PSI approval can run past mid-December. Until the date is in hand, nothing is lost:
# a Sunday sim and an hour a night of drill and redo, from banks not yet touched.
HOLD_SIMS = {D(2026, 12, 20): ("NEC_Vol_1_Final_Exam_A", 240), D(2026, 12, 27): ("B&G_Final_Exam_A", 240), D(2027, 1, 3): ("NEC_Vol_1_Final_Exam_B", 240), D(2027, 1, 10): ("B&G_Final_Exam_B", 240)}
OFF_DAYS = {D(2026, 12, 24): "Christmas Eve", D(2026, 12, 25): "Christmas", D(2026, 12, 31): "New Year's Eve", D(2027, 1, 1): "New Year's Day"}
hold_q = [quiz("Exam_Prep_Module_II_Practice_Exam", lo, lo + 19) for lo in (21, 41, 61, 81)] + [quiz("NEC_Vol_2_Final_Exam_A", lo, lo + 19) for lo in range(1, 100, 20)] + [quiz("NEC_Vol_2_Final_Exam_B", lo, lo + 19) for lo in range(1, 100, 20)] + [quiz("Exam_Prep_Module_IV_Practice_Exam", 1, 20)]
d = D(2026, 12, 20)
while d <= D(2027, 1, 10):
    if d in HOLD_SIMS:
        key, mins = HOLD_SIMS[d]
        add(d, "sim", "Holding sim", quiz=quiz(key), minutes=mins, note="Only if PSI has not given you a date yet. Same conditions, same clock.", steps=SIM_STEPS(mins))
    elif d in OFF_DAYS:
        add(d, "taper", OFF_DAYS[d] + " · off", steps=["Day off. The plan says so."])
    else:
        add(d, "notebook", "Holding week · one hour", redo=r"^", what="Until PSI gives a date: every miss still red, then twenty timed questions. No new material; the book does not get thicker.",
            steps=["Lookup drill: ten sections from the notebook, blind, 60 seconds each."], quiz=hold_q.pop(0))
    d += dt.timedelta(days=1)

days.sort(key=lambda x: x["day"])

CROSSWALK = [
    ("220.41 dwelling general lighting", "220.14(J)"), ("Table 220.42(A) lighting unit loads", "Table 220.12"),
    ("220.42(B) energy-code exception", "220.12 Exception"), ("220.43 office receptacle load", "220.14(K)"),
    ("220.44 banks and offices", "220.14(M)"), ("220.45 lighting demand factors", "220.42"),
    ("220.46 show windows and track", "220.43"), ("220.47 receptacle demand", "220.44"),
    ("220.11 maximum load", "220.18"), ("220.5(C) floor area", "220.11"),
    ("Table 310.4(1) insulation", "Table 310.4(A)"), ("242.12 uses not permitted", "242.6"),
    ("242.13(A) Type 1 SPDs", "242.12(A)"), ("250.140(A) ranges and dryers", "250.140 main paragraph"),
    ("410.71 LED drivers", "410.130(G)"), ("220.120 shore power", "555.6"),
]
WEEKS = [
    ("Week 0", "2026-11-07", "2026-11-08", "Restart and baseline"),
    ("Week 1", "2026-11-09", "2026-11-15", "Article 250 Parts I–II, and the first theory night"),
    ("Week 2", "2026-11-16", "2026-11-22", "Electrodes and equipment grounding, theory, box fill, the dwelling load"),
    ("Week 3", "2026-11-23", "2026-11-29", "Art 230, raceway fill, wiring methods, voltage drop, theory"),
    ("Week 4", "2026-11-30", "2026-12-06", "Conductor sizing, Art 240, motors, theory review"),
    ("Week 5", "2026-12-07", "2026-12-13", "The notebook, then Chapters 7 and 8"),
    ("Exam week", "2026-12-14", "2026-12-19", "Taper. Sit it when PSI gives the date."),
    ("Holding", "2026-12-20", "2027-01-10", "Only if the date comes later: a sim a Sunday, an hour a night"),
]
# Nights off, named from the chat. The page also keeps the ones he taps (Skip tonight, Take
# this day off). A night off moves the plan, it never deletes a day: the page draws every day
# after it one free night later, keeps the sims on their Sundays, and lists anything pushed
# past Dec 13. Days keep their written date as their name, so ticks and scores stay put.
OFF_NIGHTS = {"2026-11-11": "Skipped · admin and the Germantown drive", "2026-11-14": "Day off"}
out = {"id": "six", "title": "Six weeks to the exam", "start": "2026-11-07", "exam_week": "2026-12-14", "off": OFF_NIGHTS,
       "chat": "https://claude.ai/code/session_01StANTDh1Xk6D1iJErq86dB",   # the Claude chat that keeps this plan: a press after grading lands back in it
       "exam": {"questions": 70, "minutes": 210, "pass": 49, "shape": "Theory 20 · Wiring & Protection (100–285) 20 · Wiring Methods (300–398) 12 · Equipment (400–490) 6 · Special Occupancies 4 · Special Equipment 2 · Communications (700–830) 6", "source": "PSI Maryland Master and Journeyperson Electrician bulletin, read 2026-11-07"},
       "ready": "Ready is both benchmarks (Dec 6 and Dec 13, in the exam's shape) at 80% or better. Both 74–79: sit it anyway and taper. Either under 72: move the date.",
       "offsets": OFF, "weeks": [dict(zip(("label", "from", "to", "theme"), w)) for w in WEEKS],
       "crosswalk": CROSSWALK, "days": days}
def count(spec):
    if not spec: return 0
    if "mix" in spec: return sum(p["to"] - p["from"] + 1 for p in spec["mix"])
    return (spec["to"] - spec["from"] + 1) if "from" in spec else len(Q[spec["key"]]["questions"])

# ---------------- THE CHECK (2026-11-12): a plan that fails any of these is not written ----------------
# Kymani budgets each night to the minute. On Nov 10 a quiz ran ahead of its video and on Nov 12 a row
# said 20 questions for a quiz of 26. So: every night fits two hours at the page's own pace, every name
# that states a count states the real one, every page range starts where the book's own contents say
# that article or unit starts, nothing from the 2023-only list is handed out, and no question is asked
# before the night that teaches it (planahead.py).
MIN_Q, NIGHT = 1.5, 120
FIRST = "2026-11-12"   # the first written day not yet sat
BOOKP = {"NEC Vol 1": json.load(open("paste2/2-NEC_Vol_1.json", encoding="utf-8"))["pages"], "Exam Prep": json.load(open("paste2/6-Exam_Prep.json", encoding="utf-8"))["pages"]}
def starts(book, what):
    """the printed pages the book's contents give for the articles or units `what` opens with: (first page, last page)"""
    m = re.match(r"(Art|Units?) (\d+)((?:(?:–| and |, )\d+)*)", what)
    if not m or book not in BOOKP: return None
    pre = "Article %s—" if m.group(1) == "Art" else "Unit %s—"
    keys = list(BOOKP[book]); P = BOOKP[book]
    lesson = lambda n: next((k for k in keys if k.startswith(pre % n) and "Review" not in k), None)
    first, last = lesson(m.group(2)), lesson((re.findall(r"\d+", m.group(3)) or [m.group(2)])[-1])
    if not first or not last: return None
    nxt = [P[k] for k in keys[keys.index(last) + 1:] if P[k] > P[last] and "Review" not in k]
    return P[first], (nxt[0] - 1 if nxt else 10 ** 6)
bad = []
for d in days:
    if not (FIRST <= d["day"] < "2026-12-14"): continue
    if d["kind"] in ("study", "notebook"):
        t = round(count(d.get("drill")) * MIN_Q) + sum(v["to"] - v["from"] for v in d["video"]) / 90 + round(count(d.get("quiz")) * MIN_Q)
        d["minutes_real"] = round(t)
        if t > NIGHT - 10: bad.append((d["day"], "night is %d min before any paper work" % t))
    for spec in (d.get("drill"), d.get("quiz")):
        if not spec: continue
        m = re.search(r"(\d+) timed", spec.get("name") or "")
        if m and int(m.group(1)) != count(spec): bad.append((d["day"], "'%s' is %d questions" % (spec["name"], count(spec))))
        for p in (spec["mix"] if "mix" in spec else [spec]):
            for n in range(p.get("from", 1), p.get("to", len(Q[p["key"]]["questions"])) + 1):
                if (p["key"], n) not in QN: bad.append((d["day"], "no such question %s #%d" % (p["key"], n)))
                elif (p["key"], n) in NOT2020 and d["kind"] != "sim": bad.append((d["day"], "2023-only question %s #%d" % (p["key"], n)))
    for p in d.get("pages", []):
        r = starts(p["book"], p["what"])
        lo = int(re.split("[–-]", p["printed"])[0])
        hi = int(re.split("[–-]", p["printed"])[-1])
        if r and not (lo == r[0] and hi <= r[1]): bad.append((d["day"], "pages %s %s for '%s': the book has it on %d–%d" % (p["book"], p["printed"], p["what"][:30], r[0], r[1])))
    if d["kind"] == "sim" and d["day"] >= "2026-11-15" and "mix" in d["quiz"] and count(d["quiz"]) != 70: bad.append((d["day"], "sim is %d questions" % count(d["quiz"])))
assert not bad, "\n" + "\n".join("%s  %s" % b for b in bad)
out["checked"] = "Plan checked " + dt.date.today().strftime("%b %d").replace(" 0", " ") + ": every night through Dec 13 fits two hours, every count and minute shown is the real one, page ranges match the books' contents, no quiz asks ahead of its video, and the two benchmarks hold no question seen before."
json.dump(out, open("sixweeks.check.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
import subprocess, os
r = subprocess.run([sys.executable, "planahead.py", "sixweeks.check.json"], capture_output=True, text=True, encoding="utf-8")
if r.returncode:
    os.remove("sixweeks.check.json")
    sys.exit(chr(10).join(l for l in r.stdout.split(chr(10)) if "AHEAD   " in l or (l[:2] == "20" and "AHEAD= 0" not in l)) + chr(10) + (r.stderr or ""))
os.replace("sixweeks.check.json", "sixweeks.json")
vm = sum((v["to"] - v["from"]) / 1.5 for d in days for v in d["video"]) / 60
print(f"sixweeks.json: {len(days)} days, {vm:.0f} min of video at 1.5x, {sum(count(d.get('quiz')) for d in days)} quiz questions + {sum(count(d.get('drill')) for d in days)} drill questions, {len(USED)} distinct")
print("left in the pools:", {b: len([x for x in POOL[b] if x not in USED]) for b in BLOCKS})
