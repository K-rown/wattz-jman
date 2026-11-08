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
import datetime as dt, json, re, collections

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
def take(block, n):
    """the next n unused questions of a block, as (key, n) items"""
    items = [x for x in POOL[block] if x not in USED][:n]
    assert len(items) == n, (f"pool {block} short: wanted {n}, have {len(items)}")
    USED.update(items)
    return items
def ranges(items):
    out = []
    for key, n in items:
        if out and out[-1]["key"] == key and out[-1]["to"] == n - 1: out[-1]["to"] = n
        else: out.append({"key": key, "from": n, "to": n})
    return out
def quiz(key, lo=None, hi=None):
    assert key in Q, key
    N = len(Q[key]["questions"])
    if lo is None: lo, hi = 1, N
    assert 1 <= lo <= hi <= N, (key, lo, hi, N)
    used_range(key, lo, hi)
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
    4: [[("210", 15)], [("240", 11), ("242", 4)], [("358-374", 3), ("376-398", 12)], [("400-411", 15)], [("500-525", 8), ("680-695", 7)], [("720-830", 15)]],
}
DRILL_NAME = {1: ["Art 100–110", "Art 200–210", "Art 300", "Art 400–411", "Art 500–525", "Art 700–708"],
              2: ["Art 110", "Art 215–225", "Art 312–314", "Art 422–450", "Art 600–695", "Art 720–830"],
              3: ["Art 100", "Art 230", "Art 320–356", "Art 430–450", "Art 530–590", "Art 700–708"],
              4: ["Art 200–210", "Art 240–242", "Art 358–398", "Art 400–411", "Art 500 and 680", "Art 720–830"]}
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

# ---- Week 1 · Article 250 · the Bonding & Grounding videos, at 1.5x ----
A, B = "23UNECBGArticle250PartA", "23UNECBGArticle250PartB"
W1 = [
    ("Art 250 Part I · the effective ground-fault current path",
     [vid(A, sec(A, "250.1"), 4000, "Mike opens 250: scope, 250.4(A)(1)–(5) and (B), what grounding is for")],
     [pages("B&G", 127, 137, "Art 250 intro and Part I")],
     ["Highlight 250.4 and 250.6 in the 2020 book as he reads them: blue over the heading, yellow after shall, red highlighter under the numbers. Highlighter only, never pen."],
     quiz("B&G_Art_250", 1, 20)),
    ("Art 250 Part I · objectionable current, connections",
     [vid(A, 4000, sec(A, "250.24"), "250.6 objectionable current, 250.8 connection methods, 250.10, 250.12")],
     [pages("B&G", 134, 137, "250.6 to 250.12")],
     ["Finish highlighting Part I."],
     quiz("B&G_Art_250", 21, 40)),
    ("Art 250 Part II · service grounding, bonding jumpers, separately derived systems",
     [vid("GroundingandBondingServiceEquipment25024", 0, None, "250.24: where the grounded conductor lands and why nowhere else"),
      vid("TransformerSeparatelyDerivedSystems25030", 0, None, "250.30(A)(1)–(8)"),
      vid("BuildingsSuppliedbyaFeeder25032", 0, None, "250.32: a second building on a feeder")],
     [pages("B&G", 138, 153, "Part II")],
     ["Work five supply-side bonding jumper sizes from Table 250.102(C)(1). Highlight 250.24(A)(1), (A)(5), (B), (C); 250.28(D); 250.30(A); 250.32(A), (B)(1).", "The generator video (250.30 for generators, 19 min) is for the drive, not tonight."],
     quiz("B&G_Art_250", 41, 60)),
    ("Art 250 Part III · electrodes and the grounding electrode conductor",
     [vid(A, sec(A, "250.50"), None, "250.50 to 250.70: every electrode, the rod rules, 250.64, Table 250.66")],
     [pages("B&G", 154, 172, "Part III")],
     ["Work ten Table 250.66 problems, with the 6 AWG rod cap and the 4 AWG concrete-encased cap. Highlight 250.52(A), 250.53(A), 250.64, 250.66, 250.68."],
     quiz("B&G_Art_250", 61, 80)),
    ("Art 250 Parts IV–V · enclosures, bonding at the service, bonding jumper sizing",
     [vid(B, sec(B, "250.80"), sec(B, "250.109"), "250.80 to 250.106: service bonding, intersystem bonding, 250.102, piping and structural metal")],
     [pages("B&G", 173, 185, "Parts IV and V")],
     ["Video runs long tonight (74 min): skip the pages, keep the problems. Five bonding jumper sizes, supply side by 250.102(C)(1) and load side by 250.122. Highlight 250.92(B), 250.94, 250.97, 250.102(C), (D), 250.104(A), (B), (C)."],
     quiz("B&G_Art_250", 81, 100)),
    ("Art 250 Parts VI–VII · equipment grounding conductors and their connections",
     [vid(B, sec(B, "250.109"), None, "250.109 to 250.148: what counts as an EGC, Table 250.122, receptacles, boxes")],
     [pages("B&G", 186, 201, "Parts VI and VII")],
     ["Work ten Table 250.122 problems, including the proportional upsizing in (B). 250.140 in your 2020 book is the main paragraph and its exception, not an (A). Then redo every 250 miss from Sim #1 in the Missed questions fold."],
     mix("Theory · 20 timed", [quiz("Exam_Prep_Module_I_Practice_Exam", 41, 50), quiz("Theory_Final_Exam", 91, 100)], 30)),
]
for i, (title, video, pg, steps, q) in enumerate(W1):
    add(D(2026, 11, 9) + dt.timedelta(days=i), "study", title, video=video, stars=[A] if i < 4 else [B], pages=pg, steps=steps, drill=drill(1, i), quiz=q)

# ---- Week 2 · box fill, dwelling loads, Art 230, cables and raceways ----
U2, U6 = "23EPUnit2", "23EPUnit6"
W2 = [
    ("Box fill · 314.16", [vid(U2, 0, 2900, "Unit 2 Part A: Table 314.16(A), the volume rules of 314.16(B), worked examples")],
     [pages("Exam Prep", 265, 272, "Unit 2 Part A")],
     ["Work ten box-fill problems with mixed sizes, a device yoke and an EGC. Highlight 314.16(A) and (B)(1)–(5)."], quiz("Exam_Prep_Unit_2", 1, 20), []),
    ("Pull and junction boxes · 314.28", [vid(U2, 2900, None, "Unit 2 Part B: 8× straight, 6× plus the rest for angle and U pulls")],
     [pages("Exam Prep", 273, 278, "Unit 2 Part B")],
     ["Work six pull-box problems: two straight, two angle, two with several raceways on one wall. Highlight 314.28(A)(1)–(3)."],
     pool_quiz("Art 312–314 · 20 timed", [("312-314", 20)], 30), []),
    ("Dwelling load · standard and optional, first half", [vid(U6, 0, 4640, "Unit 6, first half")],
     [pages("Exam Prep", 369, 382, "Unit 6 Parts A and B")],
     ["Work example 6.13 start to finish on paper before Mike finishes it. In the 2020 book the lighting load is 220.12 and the demand table is Table 220.42; pencil those in the Exam Prep margin."], quiz("Exam_Prep_Unit_6", 1, 20), []),
    ("Dwelling load · second half, neutral", [vid(U6, 4640, None, "Unit 6, second half: ranges, dryers, AC vs heat, 310.12, the neutral")],
     [pages("Exam Prep", 383, 386, "Unit 6 Part C")],
     ["Work the same house both ways, standard and optional, and compare the service sizes. Highlight 220.52–220.61 and 220.82."], quiz("Exam_Prep_Unit_6", 21, 40), []),
    ("Article 230 · services", [],
     [pages("NEC Vol 1", 217, 242, "Art 230, no video tonight: read it with the book open")],
     ["230.2 number of services, 230.6 outside a building, 230.9 clearances, 230.24 overhead clearances, 230.42 sizing, 230.43 wiring methods, 230.70–230.72 the disconnect, 230.79 ratings, 230.85 emergency disconnect, 230.90 overload protection.",
      "Highlight the whole article from its ★ list. Art 230 is three of the twenty Wiring & Protection questions."],
     pool_quiz("Art 215–230 · 20 timed", [("230", 15), ("215-225", 5)], 30), ["23UNEC1Article230"]),
    ("Theory I · Ohm's law, Watt's law, the formula wheel",
     [vid("ETC5U12", 0, None, "Unit 12 Ohm's law"), vid("ETC5U13", 0, None, "Unit 13 Watt's law"), vid("ETC10U29", 0, None, "Unit 29 the formula wheel")],
     [pages("Exam Prep", 19, 28, "Units 12–13"), pages("Exam Prep", 105, 107, "Unit 29")],
     ["Sim #1 said theory 2 of 10, and theory is 20 of the 70 on the real exam. Pen and paper the whole hour: every example Mike works, you work first. E = I × R, P = E × I, and the wheel for the rest.",
      "Also tonight, no video needed: highlight 320, 330, 334, 344, 352, 358 from their ★ lists (uses permitted and not, support spacing). Twelve of the seventy are wiring methods, and they are lookups."],
     mix("Theory · Ohm's and Watt's law", [quiz("Exam_Prep_Unit_12", 1, 11), quiz("Exam_Prep_Unit_13", 1, 9)], 30), ["23UNEC1Article334", "23UNEC1Article358", "23UNEC1Article320", "23UNEC1Article330", "23UNEC1Article344", "23UNEC1Article352"]),
]
for i, (title, video, pg, steps, q, stars) in enumerate(W2):
    add(D(2026, 11, 16) + dt.timedelta(days=i), "study", title, video=video, pages=pg, steps=steps, drill=drill(2, i), quiz=q, stars=stars)

# ---- Week 3 · Chapter 9 fill, voltage drop, conductor sizing ----
U1, U5, U3 = "23EPUnit1", "23EPUnit5", "23EPUnit3edit"
W3 = [
    ("Raceway fill · Chapter 9, first half", [vid(U1, 0, 4318, "Unit 1, first half: Tables 1, 4, 5 and Annex C")],
     [pages("Exam Prep", 241, 258, "Unit 1")],
     ["Work eight fills: four straight from Annex C, four with mixed sizes through Tables 4 and 5. Note 7: round up at 0.8. Note 4: nipples at 60%."], quiz("Exam_Prep_Unit_1", 1, 20)),
    ("Raceway fill · second half, wireways, cables", [vid(U1, 4318, None, "Unit 1, second half")],
     [pages("Exam Prep", 241, 258, "Unit 1, 1.4–1.7")],
     ["Highlight the notes to Ch 9 Table 1 and the heads of Tables 4, 5 and 8; tab Annex C by raceway type (permanent tabs). Wireways are 20% (376.22)."], quiz("Exam_Prep_Unit_1", 21, 40)),
    ("Voltage drop · the formula", [vid(U5, 0, None, "Unit 5 whole: circular mils, Table 8, 2KID/CM and the three-phase 1.732")],
     [pages("Exam Prep", 351, 364, "Unit 5")],
     ["Work six: three single-phase, three three-phase, in volts and in percent. 3% and 5% are informational notes under 210.19 and 215.2."], quiz("Exam_Prep_Unit_5", 1, 20)),
    ("Theory II · series and parallel circuits (Thanksgiving)",
     [vid("ETC6U14", 0, None, "Unit 14 series circuits"), vid("ETC6U15", 0, None, "Unit 15 parallel circuits")],
     [pages("Exam Prep", 31, 50, "Units 14–15")],
     ["On paper: resistors in series add; in parallel 1/R = 1/R1 + 1/R2 + 1/R3, and equal resistors in parallel are R ÷ n (three 5 Ω in parallel is 1.66 Ω). Voltage divides across series resistors by their share of the resistance.",
      "Voltage drop sizing from last night, four problems: CM = 2 × K × I × D ÷ VD, then up to the next Table 8 size."], quiz("Exam_Prep_Unit_14", 1, 20)),
    ("Conductor sizing · insulation, terminals, ampacity", [vid(U3, 0, 4431, "Unit 3, first half: 110.14(C), 240.4, Table 310.16, correction and adjustment")],
     [pages("Exam Prep", 283, 296, "Unit 3 Parts A and B to 3.9")],
     ["Work eight: pick from the 75°C column, then check against the corrected 90°C ampacity. In the 2020 book the insulation table is Table 310.4(A)."], quiz("Exam_Prep_Unit_3", 1, 20)),
    ("Conductor sizing · branch circuits, feeders, taps", [vid(U3, 4431, None, "Unit 3, second half: 210.19, 210.20, 215.2, 215.3, the tap rules of 240.21(B)")],
     [pages("Exam Prep", 297, 306, "3.10–3.16")],
     ["Highlight 210.19(A)(1), 210.20(A), 215.2(A)(1), 240.4(B), 240.4(D), 240.21(B)."], quiz("Exam_Prep_Unit_3", 44, 63)),
]
for i, (title, video, pg, steps, q) in enumerate(W3):
    add(D(2026, 11, 23) + dt.timedelta(days=i), "study", title, video=video, pages=pg, steps=steps, drill=drill(3, i), quiz=q)

# ---- Week 4 · 240 / 310 / 430 / 422 ----
U4 = "23EPUnit4"
W4 = [
    ("Article 240 · overcurrent protection", [vid("23UNEC1Article240", 0, None, "Art 240 whole")],
     [pages("NEC Vol 1", 223, 245, "Art 240")],
     ["Memorize 240.6(A). Highlight the whole article from its ★ list; 240.21(B) and (C), 240.24 first."], quiz("Exam_Prep_Unit_3", 64, 78), ["23UNEC1Article240"]),
    ("Article 310 · conductors for general wiring", [vid("23UNEC1Article310", 0, None, "Art 310 whole")],
     [pages("NEC Vol 1", 367, 386, "Art 310")],
     ["Highlight from the ★ list: 310.10, 310.12 and Table 310.12(A), 310.15(B), (C), (E), Table 310.16."], pool_quiz("Art 310 · 20 timed", [("310", 20)], 30), ["23UNEC1Article310"]),
    ("Motors · FLC, conductors, the breaker", [vid(U4, 0, 3405, "Unit 4 Part A: Tables 430.248/250, 430.22, Table 430.52, 250.122(D)")],
     [pages("Exam Prep", 315, 334, "Unit 4 Part A")],
     ["Work four complete motor circuits: conductor, overload, breaker, feeder (430.24, 430.62)."], quiz("Exam_Prep_Unit_4", 1, 20), []),
    ("Motors · overloads, AC; Article 430 itself", [vid(U4, 3405, 6810, "Unit 4: 430.32 overloads, 440.4(B), 440.22, 440.33, Table 450.3(B)"), vid("23UNEC1Article430", 0, None, "Art 430: disconnects 430.102, 430.107, 430.109, 430.110")],
     [pages("NEC Vol 1", 599, 618, "Art 430")],
     ["Highlight Art 430 from its ★ list; tab Table 430.52 and the FLC tables."], quiz("Exam_Prep_Unit_4", 21, 40), ["23UNEC1Article430"]),
    ("Appliances, heating, air conditioning · 422, 424, 440", [vid(U4, 6810, None, "Unit 4, last part: transformers 450.3(B), 240.21(C)"), vid("23UNEC1Article422", 0, None, "Art 422"), vid("23UNEC1Article424", 0, None, "Art 424")],
     [pages("NEC Vol 1", 561, 575, "Art 422 and 424")],
     ["Highlight 422, 424, 440 from their ★ lists: 422.10, 422.11, 422.16 cords, 422.31 disconnects, 424.3, 440.4(B), 440.14. One transformer problem by Table 450.3(B) and that is enough transformers."],
     mix("Unit 4 AC and Art 422–427 · 20 timed", [quiz("Exam_Prep_Unit_4", 41, 55)] + ranges(take("422-427", 5)), 30), ["23UNEC1Article422", "23UNEC1Article424", "23UNEC1Article440"]),
    ("Theory III · AC, power factor, transformers",
     [vid("ETC7U20", 0, None, "Unit 20 true power, power factor, apparent power"), vid("ETC8U24", 0, 2400, "Unit 24 transformers, the first 40 minutes: ratios, kVA, primary and secondary current")],
     [pages("Exam Prep", 83, 93, "Unit 20"), pages("Exam Prep", 117, 123, "Unit 24")],
     ["On paper: RMS = peak × 0.707; PF = W ÷ VA; I = VA ÷ (E × 1.732) for three-phase; a 4:1 transformer divides voltage by 4. Work every example before Mike does.",
      "Then redo every 240, 310, 430 miss in the Missed questions fold, and close any ★ list still open (225, 408, 410). Tomorrow is benchmark 1."],
     quiz("Theory_Final_Exam", 1, 20), ["23UNEC1Article225", "23UNEC1Article408", "23UNEC1Article410"]),
]
for i, (title, video, pg, steps, q, stars) in enumerate(W4):
    add(D(2026, 11, 30) + dt.timedelta(days=i), "study", title, video=video, pages=pg, steps=steps, drill=drill(4, i), quiz=q, stars=stars)

# ---- Week 5 · the notebook only ----
W5 = [
    ("All sim misses, cold", r"^", "Every miss from Sims #1–#5. Redo them below without looking at the old answer; anything missed twice is red and comes back Saturday.",
     ["Lookup drill: shut the book, then find the section of each sim miss in under 60 seconds. Time every one."],
     quiz("B&G_Art_250", 101, 120)),
    ("Article 250 misses", r"^(Table\s+)?250\.", "Every 250 miss. For each, read the whole section in the 2020 book, not just the line.",
     ["Lookup drill: the 250 sections in the notebook, 60 seconds each, then Table 250.66 and Table 250.122 blind."], quiz("B&G_Art_250", 121, 140)),
    ("220 and 314 misses", r"^(Table\s+)?(220|314)\.", "Every load-calc and box-fill miss. Then Exam Prep 6.13 and 6.2 once more, on paper.",
     ["Lookup drill: Table 220.55 and its notes, Table 220.54, Table 220.42, 314.16(B), 314.28(A), timed."], mix("Unit 6 and Unit 2 · 20 timed", [quiz("Exam_Prep_Unit_6", 41, 57), quiz("Exam_Prep_Unit_2", 21, 22)], 30)),
    ("Chapter 9, voltage drop and 310 misses", r"^(Table\s+)?(310\.|Chapter 9|Ch\.? 9|Annex|Table [1458]\b)", "Every conduit-fill, voltage-drop and ampacity miss. Two fresh fills, two fresh drops, two corrections with both factors.",
     ["Lookup drill: Ch 9 Tables 1, 4, 5, 8, Annex C, Table 310.16, 310.15(B)(1), 310.15(C)(1), blind and timed."], quiz("B&G_Art_250", 141, 160)),
    ("240, 430, 440 misses", r"^(Table\s+)?(240|430|440|450)\.", "Every overcurrent, motor and AC miss. One full motor circuit, end to end.",
     ["Lookup drill: 240.6(A), 240.21(B), Table 430.52, 430.248, 430.250, 430.110, 440.4(B), blind and timed."], quiz("Exam_Prep_Module_III_Practice_Exam", 1, 20)),
    ("Twice-missed, and theory", r"^", "Everything red. Then the Theory questions below: 20 of the 70 are theory, the biggest block on the exam.",
     ["Lookup drill: twenty random index words from the 2020 book, 60 seconds each."], quiz("Theory_Final_Exam", 21, 40)),
]
for i, (title, redo, what, steps, q) in enumerate(W5):
    add(D(2026, 12, 7) + dt.timedelta(days=i), "notebook", title, redo=redo, what=what, steps=steps, quiz=q)

# ---- the Sunday sims: Mike's two mixed exams, four in Maryland's own shape ----
def md_mix(k, theory):
    """70 questions in the bulletin's proportions, from the pools; nothing shared with any other night"""
    parts = list(theory)
    for block, n in [("100", 2), ("110", 2), ("210", 3), ("215-225", 3), ("230", 3), ("240", 3), ("250", 4),
                     ("300", 2), ("310", 2), ("312-314", 1), ("320-330", 1), ("332-356", 3), ("358-374", 1), ("376-398", 2),
                     ("400-411", 2), ("422-427", 1), ("430-450", 3),
                     ("500-525", 2), ("530-547", 1), ("550-590", 1), ("600-675", 1), ("680-695", 1), ("700-708", 3), ("720-830", 3)]:
        parts += ranges(take(block, n))
    assert sum(p["to"] - p["from"] + 1 for p in parts) == 70, sum(p["to"] - p["from"] + 1 for p in parts)
    return mix(f"Maryland mix {k}", parts, 210)
SIM_STEPS = lambda mins: [
    "Start by 9 am. " + ("Four hours" if mins == 240 else "3½ hours") + " on the clock, 2020 code book only, phone face down.",
    "Checkpoints: at 60 min you are past Q20; at 120 min past Q40. Behind that, best-guess the flagged ones and move. No scheduled break; the clock runs if you leave the room.",
    "Grade when time is called, not before. Then read every miss; press Rewatch where it offers one. Theory misses first: open the Exam Prep unit the reference names and work that example on paper. Review stops at 60 min: the misses are in the notebook and Saturday redoes them."]
SIMS = [
    (D(2026, 11, 8), "Sim #1 · baseline", quiz("Simulated_Exams_Exam_A"), 240, "Mike's Exam A, 100 questions, 4 hours. Whatever the score, it is the starting line. On paper, note the clock at every tenth question: your real pace, from day one."),
    (D(2026, 11, 15), "Sim #2 · Maryland shape", md_mix(1, [quiz("Exam_Prep_Module_I_Practice_Exam", 1, 20)]), 210, "70 questions in PSI Maryland's own proportions, 3½ hours. 49 right passes the real one. The first 20 are theory: under 15 of them means theory joins every Saturday from here."),
    (D(2026, 11, 22), "Sim #3", quiz("Simulated_Exams_Exam_B"), 240, "Mike's Exam B, 100 questions, 4 hours: the one code-wide stress test. Heavier on Chapters 5–8 than Maryland is."),
    (D(2026, 11, 29), "Sim #4 · Maryland shape", md_mix(2, [quiz("Exam_Prep_Module_I_Practice_Exam", 21, 40)]), 210, "70 questions, 3½ hours, Maryland's proportions, none seen before."),
    (D(2026, 12, 6), "Sim #5 · benchmark 1", md_mix(3, [quiz("Theory_Final_Exam", 51, 70)]), 210, "Benchmark 1, in the exam's shape. 80 or better (56 of 70): on track. 74–79: sit it and taper. Under 72 (50): this score alone moves the date, today, while a reschedule is still free."),
    (D(2026, 12, 13), "Sim #6 · benchmark 2", md_mix(4, [quiz("Theory_Final_Exam", 71, 90)]), 210, "Benchmark 2, same shape. Both benchmarks 80 or better: sit it. Both 74–79: sit it; Mike's questions run harder than PSI's. Either under 72: the holding weeks below, and the date moves."),
]
for day, title, q, mins, note in SIMS:
    add(day, "sim", title, quiz=q, minutes=mins, note=note, steps=SIM_STEPS(mins))

# ---- exam week, and the holding weeks if PSI's date comes later ----
for i, (title, steps) in enumerate([
    ("Taper, one hour", ["30 min lookup drill from the notebook, then 20 timed questions from any sim you have not re-sat. No new material."]),
    ("Taper, one hour", ["Same. Rework only what is still red in the Missed questions fold."]),
    ("Taper, one hour", ["Same. Call PSI once: calculator rules (the bulletin does not say), arrival time, what ID they want. Use that calculator on every quiz from today."]),
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
    ("Week 1", "2026-11-09", "2026-11-15", "Article 250, the Bonding & Grounding videos"),
    ("Week 2", "2026-11-16", "2026-11-22", "Box fill, dwelling loads, Art 230, cables and raceways"),
    ("Week 3", "2026-11-23", "2026-11-29", "Chapter 9 fill, voltage drop, conductor sizing"),
    ("Week 4", "2026-11-30", "2026-12-06", "Articles 240, 310, 430, 422–440"),
    ("Week 5", "2026-12-07", "2026-12-13", "The notebook only"),
    ("Exam week", "2026-12-14", "2026-12-19", "Taper. Sit it when PSI gives the date."),
    ("Holding", "2026-12-20", "2027-01-10", "Only if the date comes later: a sim a Sunday, an hour a night"),
]
out = {"id": "six", "title": "Six weeks to the exam", "start": "2026-11-07", "exam_week": "2026-12-14",
       "chat": "https://claude.ai/code/session_01StANTDh1Xk6D1iJErq86dB",   # the Claude chat that keeps this plan: a press after grading lands back in it
       "exam": {"questions": 70, "minutes": 210, "pass": 49, "shape": "Theory 20 · Wiring & Protection (100–285) 20 · Wiring Methods (300–398) 12 · Equipment (400–490) 6 · Special Occupancies 4 · Special Equipment 2 · Communications (700–830) 6", "source": "PSI Maryland Master and Journeyperson Electrician bulletin, read 2026-11-07"},
       "ready": "Ready is both benchmarks (Dec 6 and Dec 13, in the exam's shape) at 80% or better. Both 74–79: sit it anyway and taper. Either under 72: move the date.",
       "offsets": OFF, "weeks": [dict(zip(("label", "from", "to", "theme"), w)) for w in WEEKS],
       "crosswalk": CROSSWALK, "days": days}
json.dump(out, open("sixweeks.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
def count(spec):
    if not spec: return 0
    if "mix" in spec: return sum(p["to"] - p["from"] + 1 for p in spec["mix"])
    return (spec["to"] - spec["from"] + 1) if "from" in spec else len(Q[spec["key"]]["questions"])
vm = sum((v["to"] - v["from"]) / 1.5 for d in days for v in d["video"]) / 60
print(f"sixweeks.json: {len(days)} days, {vm:.0f} min of video at 1.5x, {sum(count(d.get('quiz')) for d in days)} quiz questions + {sum(count(d.get('drill')) for d in days)} drill questions, {len(USED)} distinct")
print("left in the pools:", {b: len([x for x in POOL[b] if x not in USED]) for b in BLOCKS})
