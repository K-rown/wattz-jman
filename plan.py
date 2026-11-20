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
# Exam Prep Unit 6 Q10-12 are keyed to the 2023 floor-area rule that counts the garage (2020: 220.11 leaves it out);
# Q48 is 220.57, EV supply equipment, new in 2023. Unit 6 is in no pool, so naming them here changes no deal.
NOT2020 |= {("Exam_Prep_Unit_6", 10), ("Exam_Prep_Unit_6", 11), ("Exam_Prep_Unit_6", 12), ("Exam_Prep_Unit_6", 48)}
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
# THE PAPER WORK (2026-11-16): a night's problems are written out here, each with its answer, and the
# page shows them under the videos with the answer behind a tap. A step that only says "work five"
# gave him nothing to work. Keyed by the night's written date. Two minutes a problem in THE CHECK.
WORK = {
    "2026-11-16": [   # Table 250.66 and its caps; all GECs copper
        ("3/0 AWG copper service conductors. The GEC runs to the metal water pipe. What size GEC?", "4 AWG copper. Table 250.66: 2/0 or 3/0 copper."),
        ("500 kcmil copper service conductors. The GEC runs to building steel. What size GEC?", "1/0 AWG copper. Table 250.66: over 350 through 600 kcmil."),
        ("500 kcmil copper service conductors. The GEC runs to a ground rod and nothing else. What size GEC?", "6 AWG copper. The table says 1/0, but 250.66(A) caps a GEC to a rod, pipe or plate at 6 AWG copper."),
        ("400 kcmil copper service conductors. The GEC runs to a concrete-encased electrode and nothing else. What size GEC?", "4 AWG copper. The table says 1/0, but 250.66(B) caps a GEC to a concrete-encased electrode at 4 AWG copper."),
        ("4/0 AWG aluminum service conductors. The GEC runs to the metal water pipe. What size copper GEC?", "4 AWG copper. Table 250.66, aluminum column: 4/0 or 250 kcmil."),
    ],
    "2026-11-17": [   # Table 250.102(C)(1) and Table 250.122; all copper
        ("2/0 AWG copper service conductors. What size copper main bonding jumper?", "4 AWG copper. Table 250.102(C)(1): 2/0 or 3/0 copper."),
        ("600 kcmil copper service conductors. What size copper supply-side bonding jumper?", "1/0 AWG copper. Table 250.102(C)(1): over 350 through 600 kcmil."),
        ("Three parallel sets of 500 kcmil copper service conductors, and one main bonding jumper for all of them. What size?", "4/0 AWG copper. 3 × 500 = 1,500 kcmil, over 1,100, so Note 1 applies: 12.5% of 1,500 = 187.5 kcmil. The next size up in Chapter 9 Table 8 is 4/0 (211.6 kcmil)."),
        ("A feeder on a 100 A breaker. What size copper equipment grounding conductor?", "8 AWG copper. Table 250.122, by the rating of the breaker, not the size of the wire."),
        ("A feeder on a 400 A breaker. What size copper equipment grounding conductor?", "3 AWG copper. Table 250.122."),
        ("A 60 A circuit would normally be 6 AWG copper with a 10 AWG EGC. The circuit conductors are increased to 3 AWG for voltage drop. What size EGC now?", "6 AWG copper. 250.122(B): the EGC grows in the same proportion. 52,620 ÷ 26,240 = 2.005; 10,380 × 2.005 = 20,815 cmil; 8 AWG is 16,510, too small, so 6 AWG (26,240)."),
    ],
    "2026-11-19": [   # 314.16(B) box fill, Table 314.16(B) volumes; 314.28(A) pull boxes
        ("A box has four 12 AWG and two 14 AWG insulated conductors that come in and are spliced there, plus two 12 AWG EGCs. No clamps, no device. What volume does the box need?", "15.25 cu in. Table 314.16(B): 12 AWG = 2.25, 14 AWG = 2.00. Four 12s = 9.00, two 14s = 4.00, and all the EGCs together count once at the largest EGC: 2.25. 9 + 4 + 2.25 = 15.25."),
        ("A single-gang box with internal cable clamps holds one receptacle. Two 12/2 cables with ground come in: four 12 AWG insulated conductors and two 12 AWG EGCs. What volume does the box need?", "18.00 cu in. Count 8 at 2.25: four conductors, 1 for all the EGCs (314.16(B)(5)), 1 for the clamps (B)(2), 2 for the receptacle yoke (B)(4). 8 × 2.25 = 18."),
        ("A box holds a switch fed with 14 AWG. Two 12 AWG conductors pass straight through without a splice (less than 12 in. of loop). Four 14 AWG conductors come in and terminate. The EGCs are one 12 AWG and one 14 AWG. No clamps. What volume?", "18.75 cu in. Pass-throughs count 1 each: 2 × 2.25 = 4.50. Four 14s: 4 × 2.00 = 8.00. The EGCs count once at the largest, 12 AWG: 2.25. The switch yoke counts 2 at the largest conductor on the switch, 14 AWG: 4.00. 4.5 + 8 + 2.25 + 4 = 18.75."),
        ("A straight pull through a pull box. The largest raceway is 3 in. trade size. How long must the box be?", "24 in. at least. 314.28(A)(1): 8 × the largest raceway, 8 × 3 = 24."),
        ("An angle pull. On the wall where the conductors enter, in one row: one 3 in. raceway and two 2 in. raceways. How far must that wall be from the opposite wall? And how far apart must the entries of the 3 in. raceway be, if its conductors leave through the bottom wall?", "22 in. to the opposite wall: 314.28(A)(2), 6 × the largest (6 × 3 = 18) plus the others in the same row (2 + 2) = 22. The two entries of the 3 in. raceway: 6 × 3 = 18 in. apart at least."),
    ],
    # From here on (2026-11-19) a problem may name its own minutes as a third item; two if it does not.
    # Every value below was read off the 2020 tables and the arithmetic redone before it was written.
    "2026-11-20": [   # Table 220.12 and Table 220.42 (2020 numbers), 220.52, 220.54, Table 220.55
        ("A 2,000 sq ft house. What is the demand load for the general lighting, the two small-appliance circuits and the laundry circuit together?",
         "5,625 VA. Lighting 2,000 × 3 VA = 6,000. Two small-appliance circuits = 3,000. Laundry = 1,500. Total 10,500. Table 220.42: the first 3,000 at 100% = 3,000; the other 7,500 at 35% = 2,625. 3,000 + 2,625 = 5,625. (Mike's 2023 book calls these 220.41 and Table 220.45.)", 3),
        ("Table 220.55, Column C. What is the demand load for (a) one 12 kW range, (b) five 12 kW ranges, (c) one 16 kW range?",
         "(a) 8 kW. (b) 20 kW. (c) 9.6 kW: 16 kW is 4 kW over 12, and Note 1 adds 5% for each kW over 12, so 8 kW × 1.20 = 9.6.", 3),
        ("The whole standard method on one house: 1,500 sq ft, 120/240 V, one 12 kW range, one 5.5 kW dryer, nothing else. What is the service load in amperes?",
         "78 A. Lighting 1,500 × 3 = 4,500, plus 3,000 small-appliance, plus 1,500 laundry = 9,000; the first 3,000 at 100% and the other 6,000 at 35% = 5,100 VA. Range 8,000 (Table 220.55). Dryer 5,500 (220.54: 5,000 or the nameplate, whichever is larger). 5,100 + 8,000 + 5,500 = 18,600 VA ÷ 240 V = 77.5 A.", 4),
    ],
    "2026-11-25": [   # Annex C; Chapter 9 Tables 4 and 5, Notes 4 and 7
        ("How many 12 AWG THHN conductors fit in trade size ¾ EMT?", "16. All one size, so go straight to Annex C, Table C.1."),
        ("Three 4 AWG THHN and four 8 AWG THHN in one EMT. What trade size?", "Trade size 1¼. Table 5: 4 THHN = 0.0824 sq in., 8 THHN = 0.0366. 3 × 0.0824 = 0.2472; 4 × 0.0366 = 0.1464; together 0.3936 sq in. Table 4, EMT, 40% column: trade size 1 is 0.346, too small; 1¼ is 0.598.", 3),
        ("How many 6 AWG THHN conductors fit in a 20 in. nipple of trade size 1 RMC?", "10. A nipple 24 in. or shorter fills to 60% (Chapter 9, Note 4). Table 4, RMC trade size 1, 60% column: 0.532 sq in. Table 5: 6 THHN = 0.0507. 0.532 ÷ 0.0507 = 10.49. Note 7 rounds up only at 0.8 or more, so 10.", 3),
        ("By Tables 4 and 5, not Annex C: how many 10 AWG THHN fit in trade size ½ EMT?", "5. Table 4, EMT ½, 40% column: 0.122 sq in. Table 5: 10 THHN = 0.0211. 0.122 ÷ 0.0211 = 5.78. Under 0.8, so it stays 5. Annex C says 5 too."),
    ],
    "2026-11-27": [   # VD = 2 × K × I × D ÷ cmil, 1.732 in place of the 2 for three-phase; Chapter 9 Table 8
        ("A 24 A load, 120 V single-phase, 160 ft from the panel on 10 AWG copper. What is the voltage drop, in volts and in percent?", "9.54 V, 7.95%. Table 8: 10 AWG = 10,380 cmil. VD = 2 × 12.9 × 24 × 160 ÷ 10,380 = 99,072 ÷ 10,380 = 9.54 V. 9.54 ÷ 120 = 7.95%.", 3),
        ("A 40 A load, 208 V three-phase, 200 ft away on 8 AWG copper. Voltage drop in volts and in percent?", "10.83 V, 5.2%. Table 8: 8 AWG = 16,510 cmil. VD = 1.732 × 12.9 × 40 × 200 ÷ 16,510 = 178,742 ÷ 16,510 = 10.83 V. 10.83 ÷ 208 = 5.2%.", 3),
        ("A 16 A load, 120 V single-phase, 150 ft away. What size copper keeps the drop to 3%?", "6 AWG. 3% of 120 V = 3.6 V. cmil = 2 × 12.9 × 16 × 150 ÷ 3.6 = 17,200. Table 8: 8 AWG is 16,510, too small; 6 AWG is 26,240.", 3),
        ("What is the resistance of 300 ft of 12 AWG stranded copper?", "0.594 Ω. Chapter 9, Table 8: 12 AWG stranded, uncoated copper is 1.98 Ω per 1,000 ft. 1.98 × 0.3 = 0.594."),
    ],
    "2026-11-30": [   # 110.14(C), Table 310.16, Table 310.15(B)(1), Table 310.15(C)(1)
        ("A 100 A breaker with terminals rated 75°C, a 100 A load. What is the smallest copper THHN you can land on it?", "3 AWG. Size by the terminals: Table 310.16, 75°C column, 3 AWG = 100 A. THHN is 90°C wire, but 110.14(C) holds it to the terminal's column."),
        ("What is the ampacity of 8 AWG THHN copper in a 110°F ambient? Three current-carrying conductors.", "47.85 A. Table 310.16, 90°C column: 55 A. Table 310.15(B)(1), 105–113°F, 90°C wire: 0.87. 55 × 0.87 = 47.85."),
        ("Six current-carrying 12 AWG THHN copper conductors share one raceway, normal ambient. What is the ampacity of each?", "24 A. 90°C column: 30 A. Table 310.15(C)(1), 4 to 6 conductors: 80%. 30 × 0.80 = 24."),
        ("Eight current-carrying 10 AWG THHN copper conductors in one raceway at 100°F. What is the ampacity of each?", "25.48 A. 90°C column: 40 A. Correction for 96–104°F: 0.91. Adjustment for 7 to 9 conductors: 70%. 40 × 0.91 × 0.70 = 25.48.", 3),
    ],
    "2026-12-02": [   # Tables 430.248 and 430.250, 430.22
        ("A 3 hp, 230 V, single-phase motor. What is its FLC, and the smallest ampacity its branch-circuit conductors may have?", "17 A and 21.25 A. Table 430.248: 3 hp at 230 V = 17 A. 430.22: 17 × 1.25 = 21.25 A."),
        ("A 10 hp, 208 V, three-phase motor, terminals rated 75°C. What size copper branch-circuit conductors?", "8 AWG. Table 430.250: 10 hp at 208 V = 30.8 A. 30.8 × 1.25 = 38.5 A. Table 310.16, 75°C: 10 AWG is 35 A, too small; 8 AWG is 50 A.", 3),
        ("A 25 hp, 460 V, three-phase motor, terminals rated 75°C. What size copper branch-circuit conductors?", "8 AWG. Table 430.250: 25 hp at 460 V = 34 A. 34 × 1.25 = 42.5 A. Table 310.16, 75°C: 8 AWG = 50 A.", 3),
    ],
    "2026-12-03": [   # 430.32, Table 430.52 and 430.52(C)(1) Ex 1, Table 250.122
        ("A motor's nameplate reads 24 A, service factor 1.15. What is the largest overload setting?", "30 A. 430.32(A)(1): service factor 1.15 or more, 125% of the nameplate current. 24 × 1.25 = 30. Overloads are the one place the nameplate is used."),
        ("A 10 hp, 208 V, three-phase motor (FLC 30.8 A). What size inverse time breaker?", "80 A. Table 430.52: inverse time breaker, 250%. 30.8 × 2.5 = 77 A. That is not a standard size, so 430.52(C)(1) Exception 1 allows the next size up in 240.6(A): 80 A.", 3),
        ("The same motor on that 80 A breaker. What size copper equipment grounding conductor?", "8 AWG. Table 250.122, by the breaker: 80 A is over the 60 A row, so use the 100 A row."),
        ("The same motor on dual-element time-delay fuses instead. What size?", "60 A. Table 430.52: dual-element fuse, 175%. 30.8 × 1.75 = 53.9 A; next size up, 60 A."),
    ],
    "2026-12-04": [   # 430.24, 430.62(A)
        ("One feeder supplies three 460 V, three-phase motors: 10 hp, 15 hp and 25 hp. Terminals rated 75°C. What size copper feeder conductors?", "4 AWG. Table 430.250 at 460 V: 14 A, 21 A, 34 A. 430.24: 125% of the largest plus the others. 34 × 1.25 = 42.5; 42.5 + 21 + 14 = 77.5 A. Table 310.16, 75°C: 6 AWG is 65 A, too small; 4 AWG is 85 A.", 3),
        ("The same three motors, each on its own inverse time breaker. What is the largest feeder breaker?", "125 A. 430.62(A): the largest branch breaker plus the FLC of the other motors. Largest: 34 × 2.5 = 85, next size up 90 A. 90 + 21 + 14 = 125 A. A feeder may not round up; 125 A happens to be a standard size.", 3),
    ],
    "2026-12-08": [
        ("The standard method, start to finish: a 2,000 sq ft house, 120/240 V, with a 10 kW range, a 5 kW dryer, a 4.5 kW water heater and a 1.2 kW dishwasher. What is the service load in amperes?", "101 A. Lighting 6,000 + small-appliance 3,000 + laundry 1,500 = 10,500; 3,000 at 100% and 7,500 at 35% = 5,625 VA (Table 220.42). Water heater and dishwasher: only two appliances, so no 75% (220.53 needs four): 5,700. Dryer 5,000 (220.54). Range 8,000 (Table 220.55, Column C). 5,625 + 5,700 + 5,000 + 8,000 = 24,325 VA ÷ 240 V = 101 A.", 7),
    ],
    "2026-12-09": [
        ("How many 10 AWG THHN conductors fit in trade size 1 EMT?", "16. Annex C, Table C.1."),
        ("Four 6 AWG THHN and three 10 AWG THHN in one EMT. What trade size?", "Trade size 1. Table 5: 4 × 0.0507 = 0.2028; 3 × 0.0211 = 0.0633; together 0.2661 sq in. Table 4, EMT, 40% column: ¾ is 0.213, too small; 1 is 0.346.", 3),
        ("A 20 A load, 240 V single-phase, 120 ft away on 12 AWG copper. Voltage drop in volts and in percent?", "9.48 V, 3.95%. Table 8: 12 AWG = 6,530 cmil. VD = 2 × 12.9 × 20 × 120 ÷ 6,530 = 61,920 ÷ 6,530 = 9.48 V. 9.48 ÷ 240 = 3.95%.", 3),
        ("Four current-carrying 8 AWG THHN copper conductors in one raceway at 120°F. What is the ampacity of each?", "36.08 A. Table 310.16, 90°C column: 55 A. Correction for 114–122°F: 0.82. Adjustment for 4 to 6 conductors: 80%. 55 × 0.82 × 0.80 = 36.08.", 3),
    ],
    "2026-12-10": [
        ("One motor circuit, end to end: 15 hp, 230 V, three-phase, nameplate 40 A, service factor 1.15, terminals 75°C. Give the conductor, the overload setting, the inverse time breaker and the copper EGC.", "6 AWG, 50 A, 110 A, 6 AWG. FLC from Table 430.250: 42 A. Conductor: 42 × 1.25 = 52.5 A, so 6 AWG (65 A at 75°C). Overload, from the nameplate: 40 × 1.25 = 50 A. Breaker: 42 × 2.5 = 105 A, next size up 110 A. EGC by the 110 A breaker: over the 100 A row of Table 250.122, so the 200 A row, 6 AWG.", 7),
    ],
}
def add(day, kind, title, **k):
    k.setdefault("steps", []); k.setdefault("video", []); k.setdefault("stars", []); k.setdefault("pages", [])
    if day.isoformat() in WORK: k["work"] = [dict({"q": w[0], "a": w[1]}, **({"min": w[2]} if len(w) > 2 else {})) for w in WORK[day.isoformat()]]
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
     ["Highlight 250.52(A), 250.53(A), 250.64, 250.66, 250.68 in the 2020 book."],
     mix("Art 250 · electrodes and the GEC", [quiz("B&G_Art_250", 47, 58), quiz("B&G_Art_250", 62, 66), quiz("B&G_Art_250", 89, 91)], 30), [A]),
    (D(2026, 11, 17), (1, 5), "Art 250 Parts V–VI · the bonding jumper and the equipment grounding conductor",
     [vid(B, sec(B, "250.102"), sec(B, "250.104"), "250.102: bonding jumpers, Table 250.102(C)(1)"),
      vid(B, sec(B, "250.118"), sec(B, "250.119"), "250.118: what counts as an EGC"),
      vid(B, sec(B, "250.122"), sec(B, "250.138"), "250.122 and its table")],
     [pages("B&G", 173, 201, "Parts IV to VII: read 250.92, 250.94, 250.104, 250.146, 250.148 from the star list")],
     ["250.140 in your 2020 book is the main paragraph and its exception, not an (A). The rest of Parts IV to VII is lookup: highlight it from the star list, do not watch it."],
     mix("Art 250 · bonding jumpers and EGCs", [quiz("B&G_Art_250", 123, 127), quiz("B&G_Art_250", 141, 146), quiz("B&G_Art_250", 151, 158)], 30), [B]),
    (D(2026, 11, 18), (2, 0), "Theory II · series and parallel circuits",
     [vid("ETC6U14", 0, None, "Unit 14 series circuits"), vid("ETC6U15", 0, None, "Unit 15 parallel circuits")],
     [pages("Exam Prep", 31, 46, "Units 14–15")],
     ["On paper: resistors in series add; in parallel 1/R = 1/R1 + 1/R2 + 1/R3, and equal resistors in parallel are R ÷ n (three 5 Ω in parallel is 1.66 Ω). Voltage divides across series resistors by their share of the resistance."],
     mix("Theory · series and parallel", [quiz("Exam_Prep_Unit_14", 1, 10), quiz("Exam_Prep_Unit_15", 1, 10)], 30), []),
    (D(2026, 11, 19), (2, 1), "Box fill and pull boxes · 314.16, 314.28",
     [vid(U2, 0, None, "Unit 2 whole: Table 314.16(A), 314.16(B), then 8× straight, 6× angle and U pulls")],
     [pages("Exam Prep", 265, 278, "Unit 2")],
     ["Highlight 314.16(A), (B)(1)–(5), 314.28(A)(1)–(3)."],
     quiz("Exam_Prep_Unit_2", 1, 20), []),
    (D(2026, 11, 20), (2, 2), "Dwelling load · the standard method, Table 220.55",
     [vid(U6, 0, 4640, "Unit 6, first half")],
     [pages("Exam Prep", 369, 382, "Unit 6 Parts A and B")],
     ["In your 2020 book the lighting load is Table 220.12 and its demand table is Table 220.42; Mike's 2023 book calls them 220.41 and Table 220.45.",
      "Your 2020 book leaves garages out of the square footage, along with open porches (220.11). The 2023 Code counts the garage. If Mike adds a garage's square feet, the 2020 exam does not.",
      "PSI's own sample question is a range off Table 220.55. In your 2020 book the oven and cooktop rules are all in Note 4 under that table; Mike's 2023 book splits them into Notes 4, 5 and 6."],
     # 2026-11-19: Q1-14 of this unit are whole-house service calculations, five to ten minutes each, and Q10-12 are
     # keyed to the 2023 garage rule. Tonight's twenty are the one-step ones the first half of the video teaches:
     # appliances, dryers, ranges, cooking branch circuits, A/C against heat, the lighting demand. The old call
     # stays for what it marks as handed out, so nothing dealt after it changes.
     (quiz("Exam_Prep_Unit_6", 1, 20), mix("Dwelling load · 20 timed", [{"key": "Exam_Prep_Unit_6", "from": 15, "to": 33}, {"key": "Exam_Prep_Unit_6", "from": 43, "to": 43}], 30))[1], []),
    (D(2026, 11, 21), (2, 3), "Theory III · alternating current",
     [vid("ETC7U17", 0, None, "Unit 17 AC fundamentals: frequency, peak and RMS, phase")],
     [pages("Exam Prep", 55, 62, "Unit 17")],
     ["Two numbers to keep from tonight: RMS = peak × 0.707, peak = RMS × 1.414. The quiz is the rest of parallel circuits from the last theory night; Unit 17's own questions come on the next one."],
     quiz("Exam_Prep_Unit_15", 11, 22), []),
    (D(2026, 11, 23), (2, 4), "Article 230 · services", [],
     [pages("NEC Vol 1", 197, 222, "Art 230, no video tonight: read it with the book open")],
     ["230.2 number of services, 230.6 outside a building, 230.9 clearances, 230.24 overhead clearances, 230.42 sizing, 230.43 wiring methods, 230.70–230.72 the disconnect, 230.79 ratings, 230.85 emergency disconnect, 230.90 overload protection.",
      "Highlight the whole article from its ★ list."],
     pool_quiz("Art 230 · 15 timed", [("230", 15)], 25), ["23UNEC1Article230"]),
    (D(2026, 11, 24), (2, 5), "Theory IV · power factor, series-parallel",
     [vid("ETC7U20", 0, None, "Unit 20 true power, power factor, apparent power"), vid("ETC6U16", 0, None, "Unit 16 series-parallel circuits")],
     [pages("Exam Prep", 67, 73, "Unit 20"), pages("Exam Prep", 51, 52, "Unit 16")],
     ["The formulas tonight: PF = W ÷ VA; VA = E × I, × 1.732 for three-phase. The quiz is Unit 17, from the last theory night."],
     quiz("Exam_Prep_Unit_17", 1, 20), []),
    (D(2026, 11, 25), (3, 0), "Raceway fill · Chapter 9 and Annex C",
     [vid(U1, 0, 4318, "Unit 1, first half: Tables 1, 4, 5 and Annex C")],
     [pages("Exam Prep", 241, 258, "Unit 1")],
     ["The Chapter 9 notes that decide answers: Note 7, round up only at 0.8 or more; Note 4, a nipple 24 in. or shorter fills to 60%. Wireways are 20% (376.22). Tab Annex C by raceway type (permanent tabs)."],
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
     ["K is 12.9 for copper and 21.2 for aluminum; the circular mils are in Chapter 9, Table 8. The 3% and 5% are informational notes under 210.19 and 215.2: a recommendation, not a rule."],
     quiz("Exam_Prep_Unit_5", 1, 20), []),
    (D(2026, 11, 28), (3, 3), "Theory V · transformers and generators",
     [vid("ETC8U24", 0, 2820, "Unit 24 transformers, the first 47 minutes: ratios, kVA, primary and secondary current"), vid("ETC8U22", 0, None, "Unit 22 generators")],
     [pages("Exam Prep", 91, 96, "Unit 24"), pages("Exam Prep", 83, 84, "Unit 22")],
     ["Keep from tonight: a 4:1 transformer divides voltage by 4 and multiplies current by 4; I = VA ÷ (E × 1.732) for three-phase. The quiz is Unit 20, from the last theory night."],
     quiz("Exam_Prep_Unit_20", 1, 20), []),
    (D(2026, 11, 30), (3, 4), "Conductor sizing · insulation, terminals, ampacity, Art 310",
     [vid(U3, 0, 4431, "Unit 3, first half: 110.14(C), 240.4, Table 310.16, correction and adjustment")],
     [pages("Exam Prep", 283, 296, "Unit 3 Parts A and B to 3.9")],
     ["The method every time: size from the 75°C column for the terminals, then check that the corrected and adjusted 90°C ampacity still carries the load. In the 2020 book the insulation table is Table 310.4(A). Highlight Art 310 from its ★ list: 310.10, 310.12 and Table 310.12(A), 310.15(B), (C), (E), Table 310.16."],
     quiz("Exam_Prep_Unit_3", 1, 20), ["23UNEC1Article310"]),
    (D(2026, 12, 1), (3, 5), "Article 240 · overcurrent protection, feeders and taps",
     [vid("23UNEC1Article240", 0, None, "Art 240 whole"), vid(U3, sec(U3, "215.2"), None, "Unit 3, the end: 215.2, 215.3, the tap rules of 240.21(B)")],
     [pages("NEC Vol 1", 223, 246, "Art 240")],
     ["Memorize 240.6(A). Highlight the whole article from its ★ list; 240.4(B), 240.4(D), 240.21(B) and (C), 240.24 first."],
     quiz("Exam_Prep_Unit_3", 64, 78), ["23UNEC1Article240"]),
    (D(2026, 12, 2), (4, 0), "Motors · full-load current and conductors",
     [vid(U4, 0, 3150, "Unit 4, the first 52 minutes: the FLC tables 430.248 and 430.250, conductors by 430.22, duty cycle")],
     [pages("Exam Prep", 315, 334, "Unit 4 Part A")],
     ["FLC comes from the table, never the nameplate; the conductor is 125% of it by 430.22. Highlight Art 430 from its ★ list; tab Table 430.52 and the FLC tables."],
     quiz("Exam_Prep_Unit_4", 1, 19), ["23UNEC1Article430"]),
    (D(2026, 12, 3), (4, 1), "Motors · overloads, the breaker, the equipment grounding conductor",
     [vid(U4, 3150, 7254, "Unit 4, the middle: overloads 430.32, short-circuit and ground-fault protection by Table 430.52, the EGC by 250.122(D)")],
     [pages("Exam Prep", 315, 344, "Unit 4")],
     ["Overloads go by the nameplate (430.32). The breaker or fuse goes by the table FLC and Table 430.52, and 430.52(C)(1) Exception 1 allows the next size up. The EGC goes by the breaker (Table 250.122)."],
     quiz("Exam_Prep_Unit_4", 20, 39), []),
    (D(2026, 12, 4), (4, 2), "Motor feeders, air conditioning, transformers · Art 422, 424, 440",
     [vid(U4, 7254, None, "Unit 4, the end: feeders 430.24 and 430.62, air conditioning 440, transformers 450.3")],
     [pages("NEC Vol 1", 589, 600, "Art 422 and 424")],
     ["Highlight 422, 424 and 440 from their ★ lists: 422.10, 422.11, 422.16 cords, 422.31 disconnects, 424.3, 440.4(B), 440.14. Six of the seventy are Articles 400–490."],
     quiz("Exam_Prep_Unit_4", 40, 62), ["23UNEC1Article422", "23UNEC1Article424", "23UNEC1Article440"]),
]
for day, (wk, n), title, video, pg, steps, q, stars in NIGHTS:
    add(day, "study", title, video=video, pages=pg, steps=steps, drill=drill(wk, n), quiz=q, stars=stars)
THEORY_RE = r"^(Theory\b|\d{1,2}\.\d)"
add(D(2026, 12, 5), "notebook", "Theory VI · every theory miss, then twenty mixed", redo=THEORY_RE,
    what="Your theory misses from Sims #1 to #4 and the theory nights, redone below. Twenty of benchmark 1's seventy are theory.",
    steps=[],
    drill=drill(4, 3), quiz=mix("Theory · 20 timed", [quiz("Exam_Prep_Module_I_Practice_Exam", 41, 50), quiz("Exam_Prep_Unit_24", 1, 10)], 30))

# ---- Week 5 · the notebook, and one night of lookups ----
W5 = [
    ("All sim misses, cold", r"^", "Your misses from Sims #1–#5, the newest first. Redo them below without looking at the old answer; anything missed twice comes back on the twice-missed night.",
     [],
     quiz("Exam_Prep_Module_III_Practice_Exam", 1, 20)),
    ("250, 220 and 314 misses", r"^(Table\s+)?(250|220|314)\.", "Your grounding, load-calc and box-fill misses. For each one you miss again, read the whole section in the 2020 book, not just the line. Then the one whole dwelling calculation written out under them.",
     [],
     mix("Art 250 · the grounding electrode conductor", [quiz("B&G_Art_250", 76, 87), quiz("B&G_Art_250", 92, 99)], 30)),
    ("Chapter 9, voltage drop and 310 misses", r"^(Table\s+)?(310\.|Chapter 9|Ch\.? 9|Annex|Table [1458]\b)", "Your conduit-fill, voltage-drop and ampacity misses, then the four problems written out under them.",
     [],
     pool_quiz("Art 310 · 20 timed", [("310", 20)], 30)),
    ("240, 430, 440 misses", r"^(Table\s+)?(240|430|440|450)\.", "Your overcurrent, motor and air-conditioning misses, then one whole motor circuit written out under them.",
     [],
     quiz("Exam_Prep_Module_III_Practice_Exam", 21, 40)),
    ("Twice-missed, and theory", r"^", "Whatever you have missed twice comes first. Then the theory questions: 20 of the 70 are theory, the biggest block on the exam.",
     [], quiz("Theory_Final_Exam", 21, 40)),
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
    ("Taper, one hour", []),
    ("Taper, one hour", []),
    ("Taper, one hour", ["Call PSI once: arrival time, what ID they want. The bulletin gives an on-screen calculator and nothing else: use the computer's calculator on every quiz from today."]),
    ("Taper, one hour", ["Pack: the 2020 NEC, tabbed with permanent plastic tabs only (no Post-it flags, no paper inserts, nothing written in it, nothing loose), two forms of ID with the name on the application, the PSI confirmation."]),
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
        add(d, "notebook", "Holding week · about an hour", redo=r"^", redo_max=10, redo_sort="twice", what="Until PSI gives a date: ten of the misses still red, then twenty timed questions. No new material; the book does not get thicker.",
            drill_note="Ten sections from the Missed questions list, book shut to start, 60 seconds each to find.", quiz=hold_q.pop(0))
    d += dt.timedelta(days=1)

days.sort(key=lambda x: x["day"])

# ---------------- THE NIGHT AS HE REALLY STUDIES IT (2026-11-19) ----------------
# Four nights running he had to stop studying and ask: a problem set the card named but did not show, a
# figure question with no figure, a video labelled 54 minutes that takes him 67 (so he stopped before the
# pull boxes and the quiz asked them), and whether to skip the lookup drill at 8:45 after the gym.
# Everything here is laid over the days after they are dealt, so no question changes hands and what was
# sat stays what it was. THE CHECK below refuses a plan that brings any of the four back.
DAY = {d["day"]: d for d in days}
PACE = 1.2   # seconds of video he gets through per second of evening, pauses included; measured Nov 16-18
# 1. No lookup drill on a weeknight that has a video. The drills are his main work on Chapters 5-8, so none
#    is dropped: each goes, with its own questions and its own score key, to a night that has the room.
#    The five he skipped (written Nov 11, 16, 17, 18, 19) go to the holding weeks.
DRILL_TO = {"2026-11-20": "2026-12-07", "2026-11-23": "2026-12-08", "2026-11-24": "2026-12-09", "2026-11-25": "2026-12-10", "2026-11-27": "2026-12-11",
            "2026-11-30": "2026-12-14", "2026-12-01": "2026-12-15", "2026-12-02": "2026-12-16", "2026-12-03": "2026-12-17", "2026-12-04": "2026-12-17",
            "2026-12-05": "2026-12-21", "2026-11-11": "2026-12-22", "2026-11-16": "2026-12-23", "2026-11-17": "2026-12-26", "2026-11-18": "2026-12-28", "2026-11-19": "2026-12-29"}
for src, dst in DRILL_TO.items():
    assert "mix" in DAY[src]["drill"] and dst > src and DAY[dst]["kind"] in ("notebook", "taper"), (src, dst)
    DAY[src]["drill_at"] = dst
    DAY[dst].setdefault("drills_in", []).append(src)
    DAY[dst].pop("drill_note", None)
# 2. What a night left behind gets a night of its own, and the card says which.
CARRY_FROM = 3200   # he stopped the box fill video at 53:52 (3232 s); the stretch starts half a minute before
DAY["2026-11-23"]["carry"] = [{"day": "2026-11-19", "from": "Thu Nov 19", "say": "the last 23 minutes of the box fill video and the rest of its 20 questions",
                               "video": [vid(U2, CARRY_FROM, None, "Pull boxes: 8× for a straight pull, 6× for angle and U pulls, the distance between raceways holding the same conductor")], "quiz": True}]
assert round((dur(U2) - CARRY_FROM) / 60 / PACE) == 23
DAY["2026-11-19"]["carried_to"] = "2026-11-23"
DAY["2026-12-05"]["carry"] = [{"day": "2026-11-12", "from": "Fri Nov 13", "say": "the Ohm's and Watt's law quiz that was never taken", "quiz": True}]
DAY["2026-11-12"]["carried_to"] = "2026-12-05"
# 3. Minutes that are true. A question that is a whole calculation gets two minutes; a reading night says how
#    long the reading is; a notebook night redoes only as many misses as the night holds.
for _day, _m in {"2026-12-01": 2, "2026-12-04": 2, "2026-12-07": 2, "2026-12-10": 2}.items(): DAY[_day]["minq"] = _m
for _day, _m in {"2026-11-23": 25, "2026-11-26": 30}.items(): DAY[_day]["read_min"] = _m
for _day, _m in {"2026-12-05": 36, "2026-12-07": 26, "2026-12-08": 28, "2026-12-09": 26, "2026-12-10": 22, "2026-12-11": 30}.items(): DAY[_day]["redo_max"] = _m
DAY["2026-12-07"]["redo_sort"] = "new"; DAY["2026-12-11"]["redo_sort"] = "twice"
# 4. Exam week is rows to press, like every other night: twenty of the misses, then a drill.
for _day, _re, _sort, _what in [
        ("2026-12-14", r"^", "new", "Sunday's benchmark misses come first. No new material this week."),
        ("2026-12-15", THEORY_RE, "twice", "Theory tonight. What you have missed twice comes first."),
        ("2026-12-16", r"^", "twice", "Any article. What you have missed twice comes first.")]:
    DAY[_day].update(redo=_re, redo_max=20, redo_sort=_sort, what=_what)
DAY["2026-12-16"]["tick_name"] = "Call PSI"
DAY["2026-12-17"]["tick_name"] = "Pack the bag"
# 7. THE SIM IS SAT IN TWO PASSES (2026-11-19). Sim #2 was 46 of 70, three short of 49, graded with 45 of its
#    210 minutes unused; 16 of the 23 wrong answers had been given in under two minutes, without the book.
#    Sim #1 was graded with 30 blanks and 91 minutes left. The points he is missing are on the clock he hands
#    back. From Sim #3 on the card says how to sit it, and the app has the mark and the second pass it names
#    (quizBlock in index.html). Laid over the sims still to come; the two already sat keep their words.
def SIM_STEPS2(mins, n):
    first = round(mins * 2 / 3 / 5) * 5
    return [
        "Start by 9 am. " + ("Four hours" if mins == 240 else "3½ hours") + " on the clock, 2020 code book only, phone face down. No scheduled break; the clock runs if you leave the room.",
        f"First pass, done by the {first}-minute mark: answer all {n}. Any answer you did not check in the book, tap ⚑ under it and keep moving. Past 3 minutes on one question: best guess, tap ⚑, next. Never leave a blank.",
        f"Second pass, the last {mins - first} minutes: tap Second pass at the top. It shows only what you marked. Open the book on each one, code lookups first, calculations after. Tap ⚑ again when the book agrees with your answer.",
        "Do not grade while the clock has time and marks are left. Sim #2 was 46 of 70, three short of passing, graded with 45 minutes unused. 16 of its 23 wrong answers were given in under two minutes.",
        "After grading, read every miss and press Rewatch where it offers one. Mike writes to the 2023 code and your exam is the 2020: a miss on a rule that changed between them says so. Review stops at 60 min; the redo nights bring the misses back."]
for d in days:
    if d["kind"] == "sim" and d["day"] >= "2026-11-22":
        q = d["quiz"]
        d["steps"] = SIM_STEPS2(d["minutes"], sum(x["to"] - x["from"] + 1 for x in q["mix"]) if "mix" in q else len(Q[q["key"]]["questions"]))

CROSSWALK = [
    ("220.41 dwelling general lighting", "220.14(J)"), ("Table 220.42(A) lighting unit loads", "Table 220.12"),
    ("220.42(B) energy-code exception", "220.12 Exception"), ("220.43 office receptacle load", "220.14(K)"),
    ("220.44 banks and offices", "220.14(M)"), ("220.45 lighting demand factors", "220.42"),
    ("220.46 show windows and track", "220.43"), ("220.47 receptacle demand", "220.44"),
    ("220.11 maximum load", "220.18"), ("220.5(C) floor area (2023 counts the garage)", "220.11 (garage left out)"),
    ("Table 220.55 Notes 4, 5, 6 cooking branch circuits", "Table 220.55 Note 4"),
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
# 2026-11-19: from NEW on, a night is measured the way he really spends it (PACE, his problems, his reading, a
# carried quiz in full, the redo at its cap) and held to less than the old two hours, because he starts near
# nine after the gym. Before NEW the nights are sat and keep the sums they were checked with.
NEW = "2026-11-20"
WEEKNIGHT, SATURDAY, TAPER, HOLDING = 105, 125, 60, 75
FIGS = {k: v for k, v in json.load(open("figures.json", encoding="utf-8")).items() if not k.startswith("_")}
# words that send him to work the page does not show; a night's problems go in WORK, a drill is a drill row
INVISIBLE = re.compile(r"on paper|\bWork (example|six|three|five|every|\w+ fills)|do three of|Finish the three|One feeder for three|fresh (fills|drops)|full motor circuit|formula-wheel questions|blind and timed|any sim you have not|Lookup drill|written out:|\bSame\.", re.I)
def night_minutes(d):
    """the whole night at his pace, counting the most it can ask"""
    t = sum(v["to"] - v["from"] for v in d["video"]) / 60 / PACE + d.get("read_min", 0) + sum(w.get("min", 2) for w in d.get("work", []))
    if d.get("quiz"): t += count(d["quiz"]) * d.get("minq", MIN_Q)
    if d.get("drill") and not d.get("drill_at"): t += count(d["drill"]) * MIN_Q
    t += sum(count(DAY[x]["drill"]) * MIN_Q for x in d.get("drills_in", []))
    for c in d.get("carry", []):
        t += sum(v["to"] - v["from"] for v in c.get("video", [])) / 60 / PACE
        if c.get("quiz"): t += count(DAY[c["day"]]["quiz"]) * DAY[c["day"]].get("minq", MIN_Q)
    if d.get("redo"): t += d.get("redo_max", 40) * MIN_Q
    if d.get("drill_note"): t += 20
    return t
def set_with_next(key, n):
    """question n and n+1 of a bank share one scenario or one figure: a range may not end between them"""
    a, b = QN.get((key, n)), QN.get((key, n + 1))
    if not a or not b: return False
    fa = FIGS.get("%s#%d" % (key, n))
    if fa and fa == FIGS.get("%s#%d" % (key, n + 1)): return True
    pat = r"applies to the next \w+ questions?"
    if not (re.search(pat, a["q"], re.I) and re.search(pat, b["q"], re.I)): return False
    c = 0
    for x, y in zip(a["q"], b["q"]):
        if x != y: break
        c += 1
    return c >= 0.6 * min(len(a["q"]), len(b["q"]))
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
    if d["day"] < FIRST: continue
    if d["day"] >= NEW and d["kind"] in ("study", "notebook", "taper"):
        t = night_minutes(d); d["minutes_real"] = round(t)
        wd = dt.date.fromisoformat(d["day"]).weekday()
        cap = TAPER if d["kind"] == "taper" else HOLDING if d["day"] >= "2026-12-20" else SATURDAY if wd == 5 else WEEKNIGHT
        if t > cap: bad.append((d["day"], "night is %d min at his pace, over %d" % (t, cap)))
        if d["kind"] == "study" and wd < 5 and d["video"] and d.get("drill") and not d.get("drill_at"): bad.append((d["day"], "a lookup drill on a weeknight that has a video"))
        m = INVISIBLE.search(" ".join(list(d.get("steps", [])) + [d.get("what") or ""]))
        if m: bad.append((d["day"], "asks for work the page does not show: '%s'" % m.group(0)))
        for w in d.get("work", []):
            if not (w["q"].strip() and w["a"].strip()): bad.append((d["day"], "a problem without its answer"))
    if d["day"] >= NEW:
        for spec in (d.get("drill"), d.get("quiz")):
            for p in ((spec["mix"] if "mix" in spec else [spec]) if spec else []):
                lo, hi = p.get("from", 1), p.get("to", len(Q[p["key"]]["questions"]))
                if d["kind"] != "sim" and (set_with_next(p["key"], lo - 1) or set_with_next(p["key"], hi)): bad.append((d["day"], "%s %d-%d cuts a set of questions that share one scenario or figure" % (p["key"], lo, hi)))
                for n in range(lo, hi + 1):
                    if re.search(r"\bFigure \d", QN.get((p["key"], n), {}).get("q", "")) and "%s#%d" % (p["key"], n) not in FIGS: bad.append((d["day"], "%s #%d names a figure the page does not have" % (p["key"], n)))
    if not (FIRST <= d["day"] < "2026-12-14"): continue
    if d["kind"] in ("study", "notebook") and d["day"] < NEW:
        t = round(count(d.get("drill")) * MIN_Q) + sum(v["to"] - v["from"] for v in d["video"]) / 90 + round(count(d.get("quiz")) * MIN_Q)
        d["minutes_real"] = round(t)
        w = 2 * len(d.get("work", []))
        d["minutes_real"] = round(t + w)
        if t > NIGHT - 10 or t + w > NIGHT: bad.append((d["day"], "night is %d min, %d of it the written problems" % (t + w, w)))
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
out["checked"] = "Plan checked " + dt.date.today().strftime("%b %d").replace(" 0", " ") + ": every weeknight from Nov 20 fits 1 h 45 and every Saturday 2 h 05 at the pace you really watch, every count and minute shown is the real one, every problem a night asks for is written on its card, page ranges match the books' contents, no quiz asks ahead of its video, and the two benchmarks hold no question seen before."
out["pace"] = PACE
json.dump(out, open("sixweeks.check.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
import subprocess, os
r = subprocess.run([sys.executable, "planahead.py", "sixweeks.check.json"], capture_output=True, text=True, encoding="utf-8")
if r.returncode:
    os.remove("sixweeks.check.json")
    sys.exit(chr(10).join(l for l in r.stdout.split(chr(10)) if "AHEAD   " in l or (l[:2] == "20" and "AHEAD= 0" not in l)) + chr(10) + (r.stderr or ""))
os.replace("sixweeks.check.json", "sixweeks.json")
vm = sum((v["to"] - v["from"]) / PACE for d in days for v in d["video"]) / 60
print(f"sixweeks.json: {len(days)} days, {vm:.0f} min of video at his {PACE}x, {sum(count(d.get('quiz')) for d in days)} quiz questions + {sum(count(d.get('drill')) for d in days)} drill questions, {len(USED)} distinct")
print("left in the pools:", {b: len([x for x in POOL[b] if x not in USED]) for b in BLOCKS})
