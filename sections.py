#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Index every NEC section Mike names in every video, with the second he says it.

The captions are machine-transcribed, so "90.2(A)" is heard as "90 that to A"
and "110.7" as "110 seven". This walks each video's transcript, finds every
mention of a real NEC article, and writes sections.json:

    {"<video_id>": {"90.2": 212, "90.3": 3022, ...}}   seconds into the video

The app shows a day's sections from the videos scheduled that day, within the
stretch you actually watch, each one a button that jumps the video there.

Run from the wattz-jman folder. The captions live in the jmen checkout and are
never copied here, only the timestamps, which are facts about the recording.

    python3 sections.py                    # rebuild sections.json
    python3 sections.py 23UNEC1Article90   # print one video's index
"""
import json, os, re, sys

CAPS = r'C:\Users\Kymani\projects\jmen\MikeHolt'
OUT = 'sections.json'

SEP = r'(?:\s*\.\s*|\s+(?:that|dot|not|the|point)\s+|\s+)'
NUM = {'one': 1, 'two': 2, 'to': 2, 'too': 2, 'three': 3, 'four': 4, 'for': 4, 'five': 5, 'six': 6,
       'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10, 'eleven': 11, 'twelve': 12, 'thirteen': 13,
       'fourteen': 14, 'fifteen': 15, 'sixteen': 16, 'seventeen': 17, 'eighteen': 18, 'nineteen': 19,
       'twenty': 20, 'thirty': 30, 'forty': 40, 'fifty': 50, 'sixty': 60, 'seventy': 70, 'eighty': 80, 'ninety': 90}
WORD = '|'.join(sorted(NUM, key=len, reverse=True))

def cues(path):
    t = open(path, encoding='utf-8-sig').read()
    out = []
    for m in re.finditer(r'(\d\d):(\d\d):(\d\d)\.\d+\s+-->\s+\S+\s*\n(.*?)(?=\n\s*\n|\Z)', t, re.S):
        out.append((int(m.group(1)) * 3600 + int(m.group(2)) * 60 + int(m.group(3)), ' '.join(m.group(4).split())))
    return out

def own_article(v):
    """the article this video teaches: the field when it is set, else the number
    Mike puts in the title ("Objectionable Current Prevention [250.6]")"""
    if v.get('article'): return str(v['article'])
    m = re.search(r'\[(\d{2,3})\.\d+\]', v.get('title', ''))
    return m.group(1) if m else None

def key_sections(vid, C):
    """the NEC sections the answer key for this video's own quiz cites.
    A video that teaches no single article (a calculations chapter, an exam-prep
    unit) names dozens of articles in passing. Only the ones Mike's own key cites
    are kept, so a misheard number never becomes a jump."""
    q = next((u.get('quiz') for u in C['units'] if u['id'] == vid and u.get('quiz')), None)
    if not q: return set()
    k = (q['book'] + ' ' + q['label'].replace(' quiz', '')).replace(' ', '_')
    Q = json.load(open('quizzes.json', encoding='utf-8')) if os.path.exists('quizzes.json') else {}
    out = set()
    for x in Q.get(k, {}).get('questions', []):
        m = re.match(r'^(?:Table\s+)?(\d{2,3}\.\d+)', (x.get('ref') or '').strip())
        if m: out.add(m.group(1))
    return out

def articles_in_play(V):
    """the NEC articles this course teaches, so a stray number is not read as a section.
    Read off every video in the program, not just the ones still ahead of one person."""
    arts = {'90', '100'}
    for v in V.values():
        a = own_article(v)
        if a: arts.add(a)
    return arts

def index(path, arts, own=None):
    """{section: first second it is spoken} for one transcript.
    own = the article this video is about; other articles are cross-references, not the lesson."""
    rx = re.compile(r'\b(' + '|'.join(sorted(arts, key=len, reverse=True)) + r')\b' + SEP + r'(\d{1,3}|' + WORD + r')\b', re.I)
    hits = {}
    for t, txt in cues(path):
        for m in rx.finditer(txt):
            art, sub = m.group(1), m.group(2).lower()
            sub = str(NUM[sub]) if sub in NUM else sub
            if sub == '0' or len(sub) > 3: continue
            if int(sub) > 200: continue          # no NEC section runs that high: "110 911" is "110.11" misheard
            if own and art != own: continue      # keep the article being taught, not passing mentions
            sec = art + '.' + sub
            if sec not in hits: hits[sec] = max(0, t - 4)   # back up a beat for the lead-in
    return hits

def main():
    """Walk EVERY video in the program, not only the ones left in one person's plan:
    a coworker starting at Unit 1 needs the sections in the videos he starts with."""
    V = {u['video_id']: u for u in json.load(open(os.path.join(CAPS, 'videos.json'), encoding='utf-8'))['units']}
    arts = articles_in_play(V)
    out, total = {}, 0
    C = json.load(open('curriculum.json', encoding='utf-8'))
    for vid, v in sorted(V.items(), key=lambda kv: kv[1]['seq']):
        path = os.path.join(CAPS, v['transcript']) if v.get('transcript') else None
        if not path or not os.path.exists(path): continue
        own = own_article(v)
        hits = index(path, arts, own)
        if not own:
            # no single article to anchor on: keep only what Mike's own answer key cites
            allowed = key_sections(vid, C)
            hits = {k: t for k, t in hits.items() if k in allowed}
        if hits:
            out[vid] = dict(sorted(hits.items(), key=lambda kv: kv[1]))
            total += len(hits)
    json.dump(out, open(OUT, 'w', encoding='utf-8'), indent=0, ensure_ascii=False)
    print(f'{OUT}: {len(out)} videos, {total} section mentions from the spoken word')
    # the slides are read by eye and are more exact than the transcript: they win
    for f in sorted(os.listdir('slides')):
        if f.endswith('.json'): merge_slides(os.path.splitext(f)[0])
    S = json.load(open(OUT, encoding='utf-8'))
    print(f'{OUT}: {len(S)} videos, {sum(len(x) for x in S.values())} sections in all')

def merge_slides(vid):
    """fold a hand-read slides/<vid>.json into sections.json (see slides.py)"""
    read = json.load(open(os.path.join('slides', vid + '.json'), encoding='utf-8'))
    S = json.load(open(OUT, encoding='utf-8'))
    cur = S.get(vid, {})
    for t, sec in read.items():
        m = re.match(r'^(\d{2,3}\.\d+(?:\([A-Za-z0-9]+\))*[a-z]?)', sec.strip())
        if not m: continue
        sec = m.group(1)
        if sec not in cur or int(t) < cur[sec]: cur[sec] = int(t)
    S[vid] = dict(sorted(cur.items(), key=lambda kv: kv[1]))
    json.dump(S, open(OUT, 'w', encoding='utf-8'), indent=0, ensure_ascii=False)
    print(f'  slides {vid}: {len(S[vid])} sections')

if __name__ == '__main__':
    if len(sys.argv) > 1:
        V = {u['video_id']: u for u in json.load(open(os.path.join(CAPS, 'videos.json'), encoding='utf-8'))['units']}
        v = V[sys.argv[1]]
        h = index(os.path.join(CAPS, v['transcript']), articles_in_play(V), own_article(v))
        for sec, t in sorted(h.items(), key=lambda kv: kv[1]):
            print(f'  {t // 60:>3}:{t % 60:02d}  {sec}')
    else:
        main()
