#!/usr/bin/env python3
"""Kymani's six weeks to the Maryland Journeyperson exam -> sixweeks.json.

The app (index.html) draws this as his plan when his record holds
{kind:'fixed', id:'six'}; the link #plan=six puts it there. Every quiz named
here is one of Mike's, already in quizzes.json, so it is taken and graded on
the page and every miss lands in the notebook the page keeps. Every video
stretch is a Mike Holt video the page plays, cut at the second a section is
taught (sections.json). Pages are given both ways: the number printed on the
page, and the number to type in Mike's digital viewer (printed + offset).

    python3 plan.py && python3 build.py
"""
import datetime as dt, json

OFF = {"NEC Vol 1": 20, "B&G": 14, "Calcs": 12, "Exam Prep": 20, "Sim": 8}   # viewer = printed + offset
URL = {"NEC Vol 1": "https://www.mikeholt.com/checkout/#/account/digital-books/book-viewer/23UNEC1-DB/5392",
       "Calcs": "https://www.mikeholt.com/checkout/#/account/digital-books/book-viewer/23FUNDCAL-DB/5383",
       "Exam Prep": "https://www.mikeholt.com/checkout/#/account/digital-books/book-viewer/23EP-DB/5382",
       "B&G": "https://www.mikeholt.com/checkout/#/account/digital-books/book-viewer/23UNECBG-DB/5380"}
S = json.load(open("sections.json", encoding="utf-8"))
V = {v["video_id"]: v for v in json.load(open("videos.json", encoding="utf-8"))["units"]}
Q = json.load(open("quizzes.json", encoding="utf-8"))

def sec(vid, s):
    """second a section is first taught in a video, from the captions"""
    t = S.get(vid, {}).get(s)
    assert t is not None, (vid, s)
    return t
def dur(vid): return V[vid]["duration_s"]
def pages(book, lo, hi=None, what=""):
    o = OFF[book]
    pr = f"{lo}–{hi}" if hi else str(lo)
    vw = f"{lo + o}–{hi + o}" if hi else str(lo + o)
    return {"book": book, "printed": pr, "viewer": vw, "what": what, "url": URL.get(book)}
def quiz(key, lo=None, hi=None):
    assert key in Q, key
    n = len(Q[key]["questions"])
    if lo is None: return {"key": key}
    assert 1 <= lo <= hi <= n, (key, lo, hi, n)
    return {"key": key, "from": lo, "to": hi}
def vid(id_, frm=0, to=None, say=""):
    assert id_ in V, id_
    return {"id": id_, "from": int(frm), "to": int(to if to is not None else dur(id_)), "say": say}

# the lookup drill: fifteen of Mike's Exam Prep NEC practice questions, code book only,
# 90 seconds each. One chapter a night, the week's fifteen moving on each week.
CH_N = {c: len(Q[f"Exam_Prep_Ch_{c}"]["questions"]) for c in range(1, 9)}
ROT = [1, 2, 3, 4, 5, 7]
def drill(week, dow):
    ch = ROT[dow]
    lo = 15 * (week - 1) + 1
    if week == 4 and dow == 5: ch, lo = 8, 1
    hi = min(lo + 14, CH_N[ch])
    return quiz(f"Exam_Prep_Ch_{ch}", lo, hi)

D = dt.date
days = []
def add(day, kind, title, **k):
    k.setdefault("steps", []); k.setdefault("video", []); k.setdefault("stars", []); k.setdefault("pages", [])
    days.append(dict(day=day.isoformat(), kind=kind, title=title, **k))

# ---- Sat Nov 7: the restart ----
add(D(2026, 11, 7), "setup", "Restart: tabs, pace, the notebook",
    steps=["Tab the 2020 code book: Ch 9 Table 1, 4, 5, 8; Annex C; Table 310.16; 310.15(B)(1) and (C)(1); 250.66; 250.122; 250.102(C)(1); 314.16; Table 220.55; 240.6; Table 430.52; 430.248 and 430.250; 450.3(B); the Index.",
           "Read the Sim Exams book, Ch 2 How to Use the NEC (viewer p15–24) and Ch 4 test-taking tips (viewer p67–70).",
           "The notebook is this page: every quiz you grade here keeps its misses, and the Notebook fold below collects them by article. Nothing to write out by hand."],
    drill=quiz("Exam_Prep_Art_90", 1, 13), quiz=quiz("Exam_Prep_Module_II_Practice_Exam", 1, 20),
    note="Light night. Tomorrow at 9 am is the baseline.")

# ---- the six Sunday sims, 100 questions, four hours ----
SIMS = [
    (D(2026, 11, 8), "Sim #1 · baseline", "Simulated_Exams_Exam_A", "Whatever the score, this is the starting line. Sort the misses by article in the Notebook fold tonight: that list is what the five weeks attack."),
    (D(2026, 11, 15), "Sim #2", "NEC_Vol_1_Final_Exam_A", "Code-wide, straight Code order. Count the Art 250 misses against Sim #1."),
    (D(2026, 11, 22), "Sim #3", "Calcs_Calcs_Final_Exam", "All calculations. Expect it to hurt. The Notebook keeps every miss with its section."),
    (D(2026, 11, 29), "Sim #4", "Exam_Prep_Module_II_Practice_Exam", "Code-wide. You did Q1–20 on Nov 7; sit all 100 again, timed."),
    (D(2026, 12, 6), "Sim #5 · benchmark 1", "Simulated_Exams_Exam_B", "80 or better. The first of the two scores that say ready."),
    (D(2026, 12, 13), "Sim #6 · benchmark 2", "NEC_Vol_1_Final_Exam_B", "80 or better. Two in a row and you book the exam. Under 80: the notebook week again, and the date moves."),
]
for day, title, key, note in SIMS:
    add(day, "sim", title, quiz=quiz(key), note=note,
        steps=["Start by 9 am. Four hours on the timer below, 2020 code book only, phone face down.",
               "Answer every question; flag the long calculations and come back to them.",
               "Grade when time is called, not before. Then read every miss and press Rewatch where it offers one."])

# ---- Week 1 · Article 250 · the Bonding & Grounding videos, at 1.5x ----
A, B = "23UNECBGArticle250PartA", "23UNECBGArticle250PartB"
W1 = [
    ("Art 250 Part I · the effective ground-fault current path",
     [vid(A, sec(A, "250.1"), 4000, "Mike opens 250: scope, 250.4(A)(1)–(5) and (B), what grounding is for")],
     [pages("B&G", 127, 137, "Art 250 intro and Part I")],
     ["Highlight 250.4 and 250.6 in the 2020 book as he reads them: blue heading, yellow after shall, red under the numbers."],
     quiz("B&G_Art_250", 1, 20)),
    ("Art 250 Part I · objectionable current, connections",
     [vid(A, 4000, sec(A, "250.24"), "250.6 objectionable current, 250.8 connection methods, 250.10, 250.12")],
     [pages("B&G", 134, 137, "250.6 to 250.12")],
     ["Finish highlighting Part I."],
     quiz("B&G_Art_250", 21, 40)),
    ("Art 250 Part II · service grounding, bonding jumpers, separately derived systems",
     [vid("GroundingandBondingServiceEquipment25024", 0, None, "250.24: where the grounded conductor lands and why nowhere else"),
      vid("TransformerSeparatelyDerivedSystems25030", 0, None, "250.30(A)(1)–(8)"),
      vid("GeneratorSeparatelyDerivedSystems25030", 0, None, "250.30 for generators"),
      vid("BuildingsSuppliedbyaFeeder25032", 0, None, "250.32: a second building on a feeder")],
     [pages("B&G", 138, 153, "Part II")],
     ["Work five supply-side bonding jumper sizes from Table 250.102(C)(1). Highlight 250.24(A)(1), (A)(5), (B), (C); 250.28(D); 250.30(A); 250.32(A), (B)(1)."],
     quiz("B&G_Art_250", 41, 60)),
    ("Art 250 Part III · electrodes and the grounding electrode conductor",
     [vid(A, sec(A, "250.50"), None, "250.50 to 250.70: every electrode, the rod rules, 250.64, Table 250.66")],
     [pages("B&G", 154, 172, "Part III")],
     ["Work ten Table 250.66 problems, with the 6 AWG rod cap and the 4 AWG concrete-encased cap. Highlight 250.52(A), 250.53(A), 250.64, 250.66, 250.68."],
     quiz("B&G_Art_250", 61, 80)),
    ("Art 250 Parts IV–V · enclosures, bonding at the service, bonding jumper sizing",
     [vid(B, sec(B, "250.80"), sec(B, "250.109"), "250.80 to 250.106: service bonding, intersystem bonding, 250.102, piping and structural metal")],
     [pages("B&G", 173, 185, "Parts IV and V")],
     ["Work five bonding jumper sizes, supply side by 250.102(C)(1) and load side by 250.122. Highlight 250.92(B), 250.94, 250.97, 250.102(C), (D), 250.104(A), (B), (C)."],
     quiz("B&G_Art_250", 81, 100)),
    ("Art 250 Parts VI–VII · equipment grounding conductors and their connections",
     [vid(B, sec(B, "250.109"), None, "250.109 to 250.148: what counts as an EGC, Table 250.122, receptacles, boxes")],
     [pages("B&G", 186, 201, "Parts VI and VII")],
     ["Work ten Table 250.122 problems, including the proportional upsizing in (B). 250.140 in your 2020 book is the main paragraph and its exception, not an (A). Then redo every 250 miss from Sim #1 in the Notebook fold."],
     quiz("B&G_Art_250", 101, 120)),
]
for i, (title, video, pg, steps, q) in enumerate(W1):
    add(D(2026, 11, 9) + dt.timedelta(days=i), "study", title, video=video, stars=[A] if i < 4 else [B], pages=pg, steps=steps, drill=drill(1, i), quiz=q)

# ---- Week 2 · calculations I · Exam Prep Units 2, 6, 7, 8 ----
U2, U6 = "23EPUnit2", "23EPUnit6"
W2 = [
    ("Box fill · 314.16", [vid(U2, 0, 2900, "Unit 2 Part A: Table 314.16(A), the volume rules of 314.16(B), worked examples")],
     [pages("Exam Prep", 265, 272, "Unit 2 Part A")],
     ["Work ten box-fill problems with mixed sizes, a device yoke and an EGC. Highlight 314.16(A) and (B)(1)–(5)."], quiz("Exam_Prep_Unit_2", 1, 20)),
    ("Pull and junction boxes · 314.28", [vid(U2, 2900, None, "Unit 2 Part B: 8× straight, 6× plus the rest for angle and U pulls")],
     [pages("Exam Prep", 273, 278, "Unit 2 Part B")],
     ["Work six pull-box problems: two straight, two angle, two with several raceways on one wall. Highlight 314.28(A)(1)–(3)."], quiz("Exam_Prep_Unit_2", 21, 22)),
    ("Dwelling load · standard and optional, first half", [vid(U6, 0, 4640, "Unit 6, first half")],
     [pages("Exam Prep", 369, 382, "Unit 6 Parts A and B")],
     ["Work example 6.13 start to finish on paper before Mike finishes it. In the 2020 book the lighting load is 220.12 and the demand table is Table 220.42; pencil those beside Mike's numbers."], quiz("Exam_Prep_Unit_6", 1, 20)),
    ("Dwelling load · second half, neutral", [vid(U6, 4640, None, "Unit 6, second half: ranges, dryers, AC vs heat, 310.12, the neutral")],
     [pages("Exam Prep", 383, 386, "Unit 6 Part C")],
     ["Work the same house both ways, standard and optional, and compare the service sizes. Highlight 220.52–220.61 and 220.82."], quiz("Exam_Prep_Unit_6", 21, 40)),
    ("Multifamily · 220.84 and 220.85", [],
     [pages("Exam Prep", 403, 426, "Unit 7, no video: read it")],
     ["7.1–7.2 optional Table 220.84 by number of units; 7.3–7.10 standard method with several ranges and dryers; 7.12 duplex; 7.13–7.14 neutral.", "Work example 7.2 and one six-unit building the standard way."],
     quiz("Exam_Prep_Unit_6", 41, 57)),
    ("Commercial loads · 220 Part III", [],
     [pages("Exam Prep", 435, 447, "Unit 8 Parts A and B, no video: read it")],
     ["Lighting by occupancy (2020: Table 220.12), lighting demand (2020: 220.42), receptacles 180 VA and the demand in 2020's 220.44, show windows 200 VA/ft, sign 1,200 VA, kitchen equipment 220.56, the office example 8.9.",
      "Copy the 2020 crosswalk at the foot of this card onto an index card and keep it in the code book. Then redo the week's calc misses in the Notebook fold."],
     quiz("Exam_Prep_Unit_8", 1, 20)),
]
for i, (title, video, pg, steps, q) in enumerate(W2):
    add(D(2026, 11, 16) + dt.timedelta(days=i), "study", title, video=video, pages=pg, steps=steps, drill=drill(2, i), quiz=q)

# ---- Week 3 · calculations II · Exam Prep Units 1, 5, 3 ----
U1, U5, U3 = "23EPUnit1", "23EPUnit5", "23EPUnit3edit"
W3 = [
    ("Raceway fill · Chapter 9, first half", [vid(U1, 0, 4318, "Unit 1, first half: Tables 1, 4, 5 and Annex C")],
     [pages("Exam Prep", 241, 258, "Unit 1")],
     ["Work eight fills: four straight from Annex C, four with mixed sizes through Tables 4 and 5. Note 7: round up at 0.8. Note 4: nipples at 60%."], quiz("Exam_Prep_Unit_1", 1, 20)),
    ("Raceway fill · second half, wireways, cables", [vid(U1, 4318, None, "Unit 1, second half")],
     [pages("Exam Prep", 241, 258, "Unit 1, 1.4–1.7")],
     ["Highlight the notes to Ch 9 Table 1 and the heads of Tables 4, 5 and 8; tab Annex C by raceway type. Wireways are 20% (376.22)."], quiz("Exam_Prep_Unit_1", 21, 40)),
    ("Voltage drop · the formula", [vid(U5, 0, None, "Unit 5 whole: circular mils, Table 8, 2KID/CM and the three-phase 1.732")],
     [pages("Exam Prep", 351, 364, "Unit 5")],
     ["Work six: three single-phase, three three-phase, in volts and in percent. 3% and 5% are informational notes under 210.19 and 215.2."], quiz("Exam_Prep_Unit_5", 1, 20)),
    ("Voltage drop · sizing the conductor (Thanksgiving, still on)", [],
     [pages("Exam Prep", 360, 364, "5.7 and 5.8")],
     ["CM = 2 × K × I × D ÷ VD, then up to the next Table 8 size. Distance is one way. Work four.", "Then redo every calc miss in the Notebook fold, cold."], quiz("Exam_Prep_Unit_5", 21, 40)),
    ("Conductor sizing · insulation, terminals, ampacity", [vid(U3, 0, 4431, "Unit 3, first half: 110.14(C), 240.4, Table 310.16, correction and adjustment")],
     [pages("Exam Prep", 283, 296, "Unit 3 Parts A and B to 3.9")],
     ["Work eight: pick from the 75°C column, then check against the corrected 90°C ampacity. In the 2020 book the insulation table is Table 310.4(A)."], quiz("Exam_Prep_Unit_3", 1, 20)),
    ("Conductor sizing · branch circuits, feeders, taps", [vid(U3, 4431, None, "Unit 3, second half: 210.19, 210.20, 215.2, 215.3, the tap rules of 240.21(B)")],
     [pages("Exam Prep", 297, 306, "3.10–3.16")],
     ["Highlight 210.19(A)(1), 210.20(A), 215.2(A)(1), 240.4(B), 240.4(D), 240.21(B)."], quiz("Exam_Prep_Unit_3", 21, 40)),
]
for i, (title, video, pg, steps, q) in enumerate(W3):
    add(D(2026, 11, 23) + dt.timedelta(days=i), "study", title, video=video, pages=pg, steps=steps, drill=drill(3, i), quiz=q)

# ---- Week 4 · 240 / 310 / 430 · the NEC Vol 1 videos and Exam Prep Unit 4 ----
U4 = "23EPUnit4"
W4 = [
    ("Article 240 · overcurrent protection", [vid("23UNEC1Article240", 0, None, "Art 240 whole")],
     [pages("NEC Vol 1", 223, 245, "Art 240")],
     ["Memorize 240.6(A). Highlight the whole article from its ★ list; 240.21(B) and (C), 240.24 first."], quiz("NEC_Vol_1_Ch_2", 1, 20), ["23UNEC1Article240"]),
    ("Article 310 · conductors for general wiring", [vid("23UNEC1Article310", 0, None, "Art 310 whole")],
     [pages("NEC Vol 1", 367, 386, "Art 310")],
     ["Highlight from the ★ list: 310.10, 310.12 and Table 310.12(A), 310.15(B), (C), (E), Table 310.16."], quiz("Exam_Prep_Unit_3", 41, 60), ["23UNEC1Article310"]),
    ("Motors · FLC, conductors, the breaker", [vid(U4, 0, 3405, "Unit 4 Part A: Tables 430.248/250, 430.22, Table 430.52, 250.122(D)")],
     [pages("Exam Prep", 315, 334, "Unit 4 Part A")],
     ["Work four complete motor circuits: conductor, overload, breaker, feeder (430.24, 430.62)."], quiz("Exam_Prep_Unit_4", 1, 20), []),
    ("Motors · overloads, AC, transformers; Article 430 itself", [vid(U4, 3405, 6810, "Unit 4: 430.32 overloads, 440.4(B), 440.22, 440.33, Table 450.3(B)"), vid("23UNEC1Article430", 0, None, "Art 430: disconnects 430.102, 430.107, 430.109, 430.110")],
     [pages("NEC Vol 1", 599, 618, "Art 430"), pages("Exam Prep", 336, 344, "Unit 4 Parts B and C")],
     ["Highlight Art 430 from its ★ list; tab Table 430.52 and the FLC tables."], quiz("Exam_Prep_Unit_4", 21, 40), ["23UNEC1Article430"]),
    ("Unit 4 finish · Articles 440 and 450", [vid(U4, 6810, None, "Unit 4, last part: 240.21(C) secondary conductors"), vid("23UNEC1Article440", 0, None, "Art 440"), vid("23UNEC1Article450", 0, None, "Art 450")],
     [pages("Calcs", 145, 151, "Calcs book Art 440, 445, 450")],
     ["Work three transformer problems: primary breaker by Table 450.3(B), secondary conductor, secondary conductor by 240.21(C)(6). Highlight 440.4(B), 440.22, Table 450.3(B)."], quiz("Exam_Prep_Unit_4", 41, 62), ["23UNEC1Article440", "23UNEC1Article450"]),
    ("Rework 240 / 310 / 430; finish the highlighting", [],
     [],
     ["Redo every 240, 310, 430, 440, 450 miss in the Notebook fold, cold.", "Any ★ list on this page still open (225, 408, 410 included): close it tonight.", "Sim Exams book Ch 4 tips once more (viewer p67–70). Tomorrow is benchmark 1."],
     quiz("NEC_Vol_1_Ch_4", 1, 20), ["23UNEC1Article225", "23UNEC1Article408", "23UNEC1Article410"]),
]
for i, (title, video, pg, steps, q, stars) in enumerate(W4):
    add(D(2026, 11, 30) + dt.timedelta(days=i), "study", title, video=video, pages=pg, steps=steps, drill=drill(4, i), quiz=q, stars=stars)

# ---- Week 5 · the notebook only ----
W5 = [
    ("All sim misses, cold", r"^", "Every miss from Sims #1–#5. Redo them below without looking at the old answer; anything missed twice is red and comes back Saturday.",
     ["Lookup drill: shut the book, then find the section of each sim miss in under 60 seconds. Time every one."], quiz("B&G_Art_250", 121, 140)),
    ("Article 250 misses", r"^(Table\s+)?250\.", "Every 250 miss. For each, read the whole section in the 2020 book, not just the line.",
     ["Lookup drill: the 250 sections in the notebook, 60 seconds each, then Table 250.66 and Table 250.122 blind."], quiz("B&G_Art_250", 141, 160)),
    ("220 and 314 misses", r"^(Table\s+)?(220|314)\.", "Every load-calc and box-fill miss. Then Exam Prep 6.13 and 6.2 once more, on paper.",
     ["Lookup drill: Table 220.55 and its notes, Table 220.54, Table 220.42, 314.16(B), 314.28(A), timed."], quiz("B&G_Art_250", 161, 172)),
    ("Chapter 9, voltage drop and 310 misses", r"^(Table\s+)?(310\.|Chapter 9|Ch\.? 9|Annex|Table [1458]\b)", "Every conduit-fill, voltage-drop and ampacity miss. Two fresh fills, two fresh drops, two corrections with both factors.",
     ["Lookup drill: Ch 9 Tables 1, 4, 5, 8, Annex C, Table 310.16, 310.15(B)(1), 310.15(C)(1), blind and timed."], quiz("Exam_Prep_Unit_1", 41, 59)),
    ("240, 430, 440, 450 misses", r"^(Table\s+)?(240|430|440|450)\.", "Every overcurrent, motor, AC and transformer miss. One full motor circuit and one transformer, end to end.",
     ["Lookup drill: 240.6(A), 240.21(B), Table 430.52, 430.248, 430.250, 430.110, 440.4(B), Table 450.3(B), blind and timed."], quiz("NEC_Vol_1_Ch_2", 21, 40)),
    ("Twice-missed, and theory if it showed", r"^", "Everything red. If theory misses were a pattern on the sims, the Exam Prep Module I unit they came from, review questions only.",
     ["Lookup drill: twenty random index words from the 2020 book, 60 seconds each."], quiz("NEC_Vol_1_Ch_2", 41, 50)),
]
for i, (title, redo, what, steps, q) in enumerate(W5):
    add(D(2026, 12, 7) + dt.timedelta(days=i), "notebook", title, redo=redo, what=what, steps=steps, quiz=q)

# ---- exam week ----
for i, (title, steps) in enumerate([
    ("Taper, one hour", ["30 min lookup drill from the notebook, then 20 timed questions from any sim you have not re-sat. No new material."]),
    ("Taper, one hour", ["Same. Rework only what is still red in the Notebook fold."]),
    ("Taper, one hour", ["Same. Read the PSI candidate bulletin: which code book edition, tabs, highlighting, calculator type."]),
    ("Taper, one hour", ["Lookup drill only. Pack: 2020 NEC tabbed and highlighted, approved calculator, two forms of ID, the PSI confirmation."]),
    ("Night before", ["Sim Exams book Ch 4 (viewer p67–70). Nothing else. In bed early."]),
    ("Exam day", ["Breakfast. Arrive 30 minutes early. Read every question twice before touching the book. Flag the long calculations and come back."]),
]):
    add(D(2026, 12, 14) + dt.timedelta(days=i), "taper", title, steps=steps)

days.sort(key=lambda d: d["day"])

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
    ("Week 2", "2026-11-16", "2026-11-22", "Calculations I: box fill and Article 220 loads"),
    ("Week 3", "2026-11-23", "2026-11-29", "Calculations II: Chapter 9 fill, voltage drop, conductor sizing"),
    ("Week 4", "2026-11-30", "2026-12-06", "Articles 240, 310, 430 (and 440, 450)"),
    ("Week 5", "2026-12-07", "2026-12-13", "The notebook only"),
    ("Exam week", "2026-12-14", "2026-12-19", "Taper. Sit it when PSI gives the date."),
]
out = {"id": "six", "title": "Six weeks to the exam", "start": "2026-11-07", "exam_week": "2026-12-14",
       "offsets": OFF, "weeks": [dict(zip(("label", "from", "to", "theme"), w)) for w in WEEKS],
       "crosswalk": CROSSWALK, "days": days}
json.dump(out, open("sixweeks.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
vm = sum((v["to"] - v["from"]) / 1.5 for d in days for v in d["video"]) / 60
qn = sum((d["quiz"]["to"] - d["quiz"]["from"] + 1) if "from" in d["quiz"] else len(Q[d["quiz"]["key"]]["questions"]) for d in days if d.get("quiz"))
dn = sum(d["drill"]["to"] - d["drill"]["from"] + 1 for d in days if d.get("drill"))
print(f"sixweeks.json: {len(days)} days, {vm:.0f} min of video at 1.5x, {qn} quiz questions + {dn} drill questions")
