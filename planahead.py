"""Never-ahead checker. Each question is mapped to the moment it is taught (video id + real second,
taken from the transcripts with the Unit 4/6 caption offset fixed, and sections.json/slides for Art 250),
then to the first plan day whose video stretch reaches that second. python planahead.py [sixweeks.json]. plan.py runs it and will not write a plan that fails"""
import json, re, sys, collections
sys.stdout.reconfigure(encoding='utf-8')
R = ''
args = [a for a in sys.argv[1:] if not a.startswith('-')]
six = json.load(open(args[0] if args else R + 'sixweeks.json', encoding='utf-8'))
Q = json.load(open(R + 'quizzes.json', encoding='utf-8'))
SEC = json.load(open(R + 'sections.json', encoding='utf-8'))
DAYS = [d for d in six['days'] if d['day'] < six['exam_week']]
A, B = '23UNECBGArticle250PartA', '23UNECBGArticle250PartB'
U1, U2, U3, U4, U5, U6 = '23EPUnit1', '23EPUnit2', '23EPUnit3edit', '23EPUnit4', '23EPUnit5', '23EPUnit6'

def day_of(vid, t=None):
    for i, d in enumerate(DAYS):
        for v in d['video']:
            if v['id'] == vid and (t is None or (v['from'] <= t <= v['to'])): return i
    return None

def read_day(pat):   # a reading-only night, found by its title
    for i, d in enumerate(DAYS):
        if re.search(pat, d['title']): return i
    return None

def rng(n, table):
    for lo, hi, x in table:
        if lo <= n <= hi: return x

UNIT_Q = {  # (video, second by which that block of the unit quiz has been taught)
    'Exam_Prep_Unit_2': [(1, 12, (U2, 2772)), (13, 22, (U2, 4700))],
    'Exam_Prep_Unit_6': [(1, 4, (U6, 1377)), (5, 20, (U6, 4225)), (21, 31, (U6, 3598)), (32, 37, (U6, 4225)), (38, 53, (U6, 4341)), (54, 57, (U6, 7346))],
    'Exam_Prep_Unit_1': [(1, 15, (U1, 1751)), (16, 45, (U1, 4300)), (46, 59, (U1, 8600))],   # past 30 min unverified: captions stop
    'Exam_Prep_Unit_5': [(1, 40, (U5, 3800))],
    'Exam_Prep_Unit_3': [(1, 12, (U3, 2700)), (13, 24, (U3, 3600)), (25, 39, (U3, 5100)), (40, 43, (U3, 5700)), (44, 48, (U3, 6100)), (49, 63, (U3, 6900)), (64, 78, (U3, 8700))],
    'Exam_Prep_Unit_4': [(1, 6, (U4, 1314)), (7, 17, (U4, 2394)), (18, 19, (U4, 3100)), (20, 28, (U4, 4800)), (29, 37, (U4, 6200)), (38, 39, (U4, 6700)), (40, 43, (U4, 8278)), (44, 48, (U4, 8500)), (49, 54, (U4, 9186)), (55, 60, (U4, 9950)), (61, 62, (U4, 10150))],
}
TH_VID = {12: 'ETC5U12', 13: 'ETC5U13', 29: 'ETC10U29', 14: 'ETC6U14', 15: 'ETC6U15', 20: 'ETC7U20'}
TFE_NONE = {1: 1, 2: 1, 3: 1, 4: 2, 5: 2, 6: 2, 7: 3, 8: 3, 9: 4, 10: 4, 11: 5, 15: 6, 16: 6, 17: 6, 18: 6, 19: 6, 20: 6,
            25: 10, 26: 10, 27: 10, 28: 10, 29: 10, 31: 12, 33: 12, 34: 12, 35: 12, 39: 12, 40: 13, 42: 14, 43: 14, 44: 14, 46: 15, 92: 26, 93: 26}

def theory(unit, sec=None):
    if unit in TH_VID: return day_of(TH_VID[unit]), 'Theory U%d' % unit
    if unit == 24:
        t = 2800 if sec and sec >= 11 else 2430 if sec and sec >= 7 else 1300
        return day_of('ETC8U24', t), 'Theory U24.%s' % (sec or '?')
    if unit <= 23: return 'PRIOR', 'Theory U%d (watched before this plan, not in it)' % unit
    return None, 'Theory U%d (never taught)' % unit

def teach(k, n, q):
    r = (q.get('ref') or '').strip()
    if k in UNIT_Q:
        vid, t = rng(n, UNIT_Q[k]); return day_of(vid, t), '%s @%ds' % (k[10:], t)
    m = re.match(r'^Theory (\d+)\.(\d+)', r) or re.match(r'^(\d{1,2})\.(\d+) [A-Z]', r)
    if m and (k.startswith(('Theory', 'Exam_Prep_Module_I_', 'Exam_Prep_Unit_1', 'Exam_Prep_Unit_2', 'Simulated')) or r.startswith('Theory')):
        return theory(int(m.group(1)), int(m.group(2)))
    if k == 'Theory_Final_Exam' and not r:
        u = TFE_NONE.get(n); return theory(u) if u else (None, 'Theory ?')
    if k == 'Exam_Prep_Module_III_Practice_Exam':   # refs are unit section titles
        if re.search(r'Annex C|1\.[456] |392\.22', r): return day_of(U1, 8600 if re.search(r'1\.[456] |392', r) else 4300), 'Unit 1'
        if re.search(r'314\.16', r): return day_of(U2, 2772), 'Unit 2'
        if re.search(r'3\.[67] ', r): return day_of(U3, 5100), 'Unit 3'
    if re.match(r'^(NEC )?(Chapter 9|Annex)', r): return day_of(U1, 4300), 'Ch 9 / Annex C'
    m = re.match(r'^(?:Table\s+)?(\d{3})\.(\d+)', r)
    if not m:
        m2 = re.match(r'^(\d{3}) ', r)
        return (None, 'Art %s definitions (lookup only)' % m2.group(1)) if m2 else (None, '?? ' + r[:30])
    a, s = int(m.group(1)), int(m.group(2))
    if a == 250:
        if s <= 4: return day_of(A, 4000), '250 Part I (to 250.4)'
        if s <= 12: return day_of(A, 8015), '250.6-250.12'
        if s <= 36: return day_of('TransformerSeparatelyDerivedSystems25030'), '250 Part II'
        # Parts III to VII: the second Mike reaches that section (sections.json), or the nearest one before it
        for v in (A, B):
            st = sorted((int(k.split('.')[1]), t) for k, t in SEC.get(v, {}).items() if re.match(r'^250\.\d+$', k) and isinstance(t, (int, float)) and (int(k.split('.')[1]) <= 70) == (v == A))   # Part A teaches to 250.70, Part B from 250.80
            if not st or not (st[0][0] <= s <= st[-1][0] + 3): continue
            t = [x for n, x in st if n <= s][-1]
            return day_of(v, t + 30), '250.%d @%ds' % (s, t)
        return None, '250.%d (no stamp)' % s
    if a == 314 and s == 16: return day_of(U2, 2772), '314.16'
    if a == 314 and s == 28: return day_of(U2, 4700), '314.28'
    if a == 220:
        if s == 61: return day_of(U6, 7346), '220.61 neutral'
        if s in (11, 12, 41, 42, 45, 50, 51, 52, 53, 54, 55, 60, 82): return day_of(U6, 4341), '220 dwelling'
        return None, '220.%d (not in the dwelling video)' % s
    if a == 310 and s == 12: return day_of(U6, 4341), '310.12'
    if a == 230: return read_day(r'^Article 230'), 'Art 230 (reading night)'
    if a == 110 and s == 14: return day_of(U3, 2700), '110.14'
    cand = []
    if a == 240:
        if s in (4, 6): cand.append(day_of(U3, 2700))
        if s == 21: cand.append(day_of(U3, 8700))
        cand.append(day_of('23UNEC1Article240'))
    if a == 310:
        if s in (15, 16): cand.append(day_of(U3, 5100))
        cand.append(day_of('23UNEC1Article310'))
    if a == 210 and s in (19, 20): cand.append(day_of(U3, 6900))
    if a == 215 and s in (2, 3): cand.append(day_of(U3, 6900))
    if (a, s) in ((422, 13), (424, 4)): cand.append(day_of(U3, 6900))
    if a == 430:
        if s in (6, 22, 247, 248, 249, 250): cand.append(day_of(U4, 3100))
        elif s in (31, 32): cand.append(day_of(U4, 4800))
        elif s in (52, 55): cand.append(day_of(U4, 6200))
        elif s == 24: cand.append(day_of(U4, 8278))
        elif s == 62: cand.append(day_of(U4, 8500))
        else: cand.append(day_of('23UNEC1Article430'))
    if a == 440: cand.append(day_of(U4, 9186))
    if a == 450 and s == 3: cand.append(day_of(U4, 9950))
    if a == 422: cand.append(day_of('23UNEC1Article422'))
    if a == 424: cand.append(day_of('23UNEC1Article424'))
    cand = [c for c in cand if c is not None]
    return (min(cand), '%d.%d' % (a, s)) if cand else (None, 'Art %d (no video or reading in the plan)' % a)

def parts(spec):
    if not spec: return []
    if 'mix' in spec: return [(p['key'], p['from'], p['to']) for p in spec['mix']]
    return [(spec['key'], spec.get('from', 1), spec.get('to', len(Q[spec['key']]['questions'])))]

def qs(spec):
    out = []
    for k, a, b in parts(spec):
        byn = {q['n']: q for q in Q[k]['questions']}
        out += [(k, n, byn[n]) for n in range(a, b + 1)]
    return out

def runs(items):
    out = []
    for k, n in items:
        if out and out[-1][0] == k and out[-1][2] == n - 1: out[-1][2] = n
        else: out.append([k, n, n])
    return ', '.join('%s Q%d' % (k, a) + ('-%d' % b if b != a else '') for k, a, b in out)

tot = collections.Counter()
for i, d in enumerate(DAYS):
    if not ('2026-11-13' <= d['day'] <= '2026-12-13') or d['kind'] == 'sim' or not d.get('quiz'): continue
    L = qs(d['quiz']); buckets = collections.defaultdict(list)
    for k, n, q in L:
        j, label = teach(k, n, q)
        v = 'OK' if isinstance(j, int) and j <= i else 'AHEAD' if isinstance(j, int) else 'PRIOR' if j == 'PRIOR' else 'UNTAUGHT'
        # a video night whose own unit quiz reaches past where the video was cut is the same failure
        if v == 'UNTAUGHT' and d['kind'] == 'study' and (k in UNIT_Q or k == 'B&G_Art_250'): v = 'AHEAD'; label += ' (past every video cut in the plan)'
        buckets[v].append((k, n, label, DAYS[j]['day'] if isinstance(j, int) else None))
    c = {v: len(buckets[v]) for v in ('OK', 'AHEAD', 'PRIOR', 'UNTAUGHT')}; tot.update(c)
    same = sum(1 for k, n, l, dy in buckets['OK'] if dy == d['day'])
    print("%s %-5s n=%2d ok=%2d (tonight's video %2d) AHEAD=%2d prior=%2d untaught=%2d | %s" % (d['day'], d['kind'][:5], len(L), c['OK'], same, c['AHEAD'], c['PRIOR'], c['UNTAUGHT'], d['title'][:48]))
    for v in ('AHEAD', 'UNTAUGHT', 'PRIOR'):
        by = collections.defaultdict(list)
        for k, n, l, dy in buckets[v]: by[(l, dy)].append((k, n))
        for (l, dy), items in by.items(): print('      %-8s %s  <- %s' % (v, runs(items), l) + (', taught %s' % dy if dy else ''))
print('TOTAL', dict(tot))
if tot['AHEAD']: sys.exit('planahead: %d questions are asked before the night that teaches them' % tot['AHEAD'])
