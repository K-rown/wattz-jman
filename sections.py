#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Find where in each video Mike covers each NEC section the answer key cites.

The captions are machine-transcribed, so "90.2(A)" is heard as "90 that to A",
"110.26(A)(1)" as "110 that 26 a one", and so on. This walks every quiz section
in quizzes.json, hunts it in that unit's caption file, and writes sections.json:

    {"<video_id>": {"90.2(A)": 4116, ...}}   seconds into the video

Run from the wattz-jman folder. The captions live in the jmen checkout and are
never copied here, only the timestamps, which are facts about the recording.

    python3 sections.py            # rebuild sections.json
    python3 sections.py --check    # print what it found for Article 90
"""
import json, os, re, sys, glob

CAPS = r'C:\Users\Kymani\projects\jmen\MikeHolt'
OUT = 'sections.json'

# how the transcriber hears the punctuation and the letters
DOT = r'(?:\s*\.\s*|\s+(?:that|dot|not|the|point|point,)\s+|\s+)'
DIGIT = {'one': 1, 'two': 2, 'to': 2, 'too': 2, 'three': 3, 'four': 4, 'for': 4, 'five': 5,
         'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10, 'zero': 0}
LETTER = {'a': 'A', 'eight': 'A', 'hey': 'A', 'b': 'B', 'be': 'B', 'bee': 'B', 'c': 'C', 'see': 'C',
          'sea': 'C', 'd': 'D', 'dee': 'D', 'e': 'E', 'f': 'F', 'g': 'G'}

def cues(path):
    """[(seconds, text)] for a .vtt"""
    t = open(path, encoding='utf-8-sig').read()
    out = []
    for m in re.finditer(r'(\d\d):(\d\d):(\d\d)\.(\d+)\s+-->\s+\S+\s*\n(.*?)(?=\n\s*\n|\Z)', t, re.S):
        h, mi, se = int(m.group(1)), int(m.group(2)), int(m.group(3))
        out.append((h * 3600 + mi * 60 + se, ' '.join(m.group(5).split())))
    return out

def spoken(sec):
    """a regex that matches how the transcriber would have heard this section"""
    m = re.match(r'^(\d{2,3})(?:\.(\d+))?((?:\([A-Za-z0-9]+\))*)', sec)
    if not m: return None
    art, sub, parens = m.group(1), m.group(2), m.group(3)
    pat = r'\b' + art + r'\b'
    if sub:
        alts = [sub] + [w for w, d in DIGIT.items() if str(d) == sub]
        pat += DOT + r'(?:' + '|'.join(alts) + r')\b'
    for p in re.findall(r'\(([A-Za-z0-9]+)\)', parens):
        if p.isdigit():
            alts = [p] + [w for w, d in DIGIT.items() if str(d) == p]
        else:
            alts = [p.lower()] + [w for w, L in LETTER.items() if L == p.upper()]
        pat += r'[\s,]*(?:' + '|'.join(re.escape(a) for a in alts) + r')\b'
    return re.compile(pat, re.I)

def coarser(sec):
    """110.26(A)(1) -> 110.26(A) -> 110.26 : if he never says the whole thing, land on the part he does"""
    out = [sec]
    while out[-1].endswith(')'):
        out.append(re.sub(r'\([A-Za-z0-9]+\)$', '', out[-1]))
    return out

def find(secs, path):
    """first time each section is spoken, in seconds; falls back to the parent section"""
    cs = cues(path)
    joined = [(t, x) for t, x in cs if x]
    windows = [(t, txt + ' ' + (joined[i + 1][1] if i + 1 < len(joined) else '')) for i, (t, txt) in enumerate(joined)]
    # Mike walks an article in order, so each section must be spoken after the one before it.
    # That single rule throws out most of the false matches the loose transcription invites.
    def key(sec):
        m = re.match(r'^(\d{2,3})(?:\.(\d+))?', sec)
        parts = [int(m.group(1)), int(m.group(2) or 0)] if m else [0, 0]
        for p in re.findall(r'\(([A-Za-z0-9]+)\)', sec):
            parts.append(int(p) if p.isdigit() else ord(p.upper()[0]))
        return parts
    hits, floor = {}, 0
    for sec in sorted(secs, key=key):
        for form in coarser(sec):
            rx = spoken(form)
            if not rx: continue
            found = next((t for t, w in windows if t >= floor and rx.search(w)), None)
            if found is not None:
                hits[sec] = max(0, found - 4)   # back up a beat so you hear the lead-in
                floor = found
                break
    return hits

def main():
    Q = json.load(open('quizzes.json', encoding='utf-8'))
    C = json.load(open('curriculum.json', encoding='utf-8'))
    V = {u['video_id']: u for u in json.load(open(os.path.join(CAPS, 'videos.json'), encoding='utf-8'))['units']}
    # the video that covers each article, from the scheduled units
    art_video = {}
    for u in C['units']:
        m = re.match(r'^Art (\d+)', u['label'])
        if not m: continue
        v = V.get(u['id']); path = os.path.join(CAPS, v['transcript']) if v and v.get('transcript') else None
        size = os.path.getsize(path) if path and os.path.exists(path) else 0
        art = m.group(1)
        if art not in art_video or size > art_video[art][1]: art_video[art] = (u['id'], size)
    art_video = {a: v[0] for a, v in art_video.items()}
    # every section any quiz cites, filed under the article that owns it
    want = {}
    for quiz in Q.values():
        for q in quiz['questions']:
            r = (q.get('ref') or '').strip()
            m = re.match(r'^(?:Table\s+)?((\d{2,3})(?:\.\d+)?(?:\([A-Za-z0-9]+\))*)', r)
            if not m: continue
            sec, art = m.group(1), m.group(2)
            vid = art_video.get(art)
            if not vid: continue
            want.setdefault(vid, [])
            if sec not in want[vid]: want[vid].append(sec)
    out, miss, done = {}, [], 0
    for vid, secs in sorted(want.items()):
        v = V.get(vid)
        path = os.path.join(CAPS, v['transcript']) if v and v.get('transcript') else None
        if not path or not os.path.exists(path):
            miss.append(vid); continue
        hits = find(secs, path)
        if hits: out[vid] = dict(sorted(hits.items()))
        done += 1
        print(f'{vid:22} {len(hits):>3} of {len(secs):>3}  {os.path.basename(path)[:40]}')
    json.dump(out, open(OUT, 'w', encoding='utf-8'), indent=0, ensure_ascii=False)
    tot_f = sum(len(v) for v in out.values()); tot_w = sum(len(v) for v in want.values())
    print()
    print(f'{OUT}: {len(out)} videos, {tot_f} of {tot_w} sections timestamped ({round(100*tot_f/max(tot_w,1))}%)' + (f' | no captions for {len(miss)}' if miss else ''))

if __name__ == '__main__':
    if '--check' in sys.argv:
        Q = json.load(open('quizzes.json', encoding='utf-8'))
        V = {u['video_id']: u for u in json.load(open(os.path.join(CAPS, 'videos.json'), encoding='utf-8'))['units']}
        secs = []
        for q in Q['NEC_Vol_1_Art_90']['questions']:
            m = re.match(r'^(\d{2,3}(?:\.\d+)?(?:\([A-Za-z0-9]+\))*)', (q.get('ref') or ''))
            if m and m.group(1) not in secs: secs.append(m.group(1))
        path = os.path.join(CAPS, V['UN1A90']['transcript']) if 'UN1A90' in V else None
        print('sections wanted:', secs)
        if path: print('hits:', find(secs, path))
    else:
        main()
