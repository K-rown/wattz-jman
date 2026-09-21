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

def articles_in_play(C):
    """the NEC articles this course teaches, so a stray number is not read as a section"""
    arts = {'90', '100'}
    for u in C['units']:
        m = re.match(r'^Art (\d+)', u['label'])
        if m: arts.add(m.group(1))
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
    C = json.load(open('curriculum.json', encoding='utf-8'))
    V = {u['video_id']: u for u in json.load(open(os.path.join(CAPS, 'videos.json'), encoding='utf-8'))['units']}
    arts = articles_in_play(C)
    out, total = {}, 0
    for u in C['units']:
        v = V.get(u['id'])
        path = os.path.join(CAPS, v['transcript']) if v and v.get('transcript') else None
        if not path or not os.path.exists(path): continue
        m = re.match(r'^Art (\d+)', u['label'])
        hits = index(path, arts, m.group(1) if m else None)
        if hits:
            out[u['id']] = dict(sorted(hits.items(), key=lambda kv: kv[1]))
            total += len(hits)
            print(f"{u['id']:22} {len(hits):>4} sections  {u['label'][:44]}")
    json.dump(out, open(OUT, 'w', encoding='utf-8'), indent=0, ensure_ascii=False)
    print()
    print(f'{OUT}: {len(out)} videos, {total} section mentions indexed')

if __name__ == '__main__':
    if len(sys.argv) > 1:
        C = json.load(open('curriculum.json', encoding='utf-8'))
        V = {u['video_id']: u for u in json.load(open(os.path.join(CAPS, 'videos.json'), encoding='utf-8'))['units']}
        v = V[sys.argv[1]]
        m = re.match(r'^Art (\d+)', next((x['label'] for x in C['units'] if x['id'] == sys.argv[1]), ''))
        h = index(os.path.join(CAPS, v['transcript']), articles_in_play(C), m.group(1) if m else None)
        for sec, t in sorted(h.items(), key=lambda kv: kv[1]):
            print(f'  {t // 60:>3}:{t % 60:02d}  {sec}')
    else:
        main()
