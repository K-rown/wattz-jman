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

SEP = r'(?:\s*\.\s*|\s*,?\s+(?:that|dot|not|the|point|at)\s+|\s+)'
NUM = {'one': 1, 'two': 2, 'to': 2, 'too': 2, 'three': 3, 'four': 4, 'for': 4, 'five': 5, 'six': 6,
       'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10, 'eleven': 11, 'twelve': 12, 'thirteen': 13,
       'fourteen': 14, 'fifteen': 15, 'sixteen': 16, 'seventeen': 17, 'eighteen': 18, 'nineteen': 19,
       'twenty': 20, 'thirty': 30, 'forty': 40, 'fifty': 50, 'sixty': 60, 'seventy': 70, 'eighty': 80, 'ninety': 90}
TENS = 'twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety'
UNITS = 'one|two|three|four|five|six|seven|eight|nine'
# "twenty one", "twenty-one" as well as the single words
WORD = r'(?:(?:' + TENS + r')(?:[\s-]+(?:' + UNITS + r'))?|' + '|'.join(sorted(NUM, key=len, reverse=True)) + r')'

def num_word(w):
    """'six' -> 6, 'twenty one' -> 21, '14' -> 14"""
    w = w.lower()
    if w.isdigit(): return int(w)
    parts = re.split(r'[\s-]+', w)
    return sum(NUM[p] for p in parts)

# the letter after a section, as the captions spell it: "200 at six be" is 200.6(B).
# Words that are also plain English ("a", "be", "see", ...) count only when nothing
# but a stop, an exception or a number follows them; a bare capital B..H counts as is.
LETTER = {'a': 'A', 'eh': 'A', 'b': 'B', 'be': 'B', 'bee': 'B', 'c': 'C', 'see': 'C', 'sea': 'C',
          'd': 'D', 'dee': 'D', 'e': 'E', 'f': 'F', 'g': 'G', 'gee': 'G'}
LET = r'(?:\s*,?\s*\(?\s*)(?P<let>' + '|'.join(sorted(LETTER, key=len, reverse=True)) + r")\)?(?![\w'])"
LET_FOLLOW = re.compile(r'\s*(?:$|[.,;:?!)]|(?:exception|except|says|talks|requires|goes|is|has|covers|applies|gives|and|or|through|which|number)\b|\d|(?:'
                        + '|'.join(NUM) + r')\b)', re.I)
# a number followed by one of these is a quantity, not a section ("240 at 30 amps")
UNIT = re.compile(r'\s*(?:-\s*)?(?:amps?|amperes?|volts?|v\b|feet|foot|ft\b|inch|inches|percent|%|degrees?|gauge|awg|kcmil|watts?|va\b|kva|hertz|hz|mils?|years?|minutes?|hours?|seconds?|times)\b', re.I)

# heard, checked against the transcript, and wrong: never a button. Keyed by the
# caption file's name.
NOT_SAID = {
    # a Q&A about 300.5(E)/(G): "something at 300 at seven G", "isn't there 307 E / not seven";
    # 300.7 has no (E) or (G)
    '17 - Article 300 - General Requirements for Wiring Methods and Materials.vtt': {'300.7(E)', '300.7(G)', '300.15', '300.15(G)'},
    # "Look at 330 at 100 330. That 104." - he is reaching for 330.104
    '22 - Article 330 - Metal-Clad Cable (Type MC).vtt': {'330.100'},
    # held back until checked against the book: a confused Q&A ("what 300 at 15. G is
    # saying"), a probable mishearing of 240.21(C) ("secondary conductors, 250.24C"), and
    # a flanged-inlet rule whose 2023 number is not certain
    '38 - Transformer Separately Derived Systems [250.30].vtt': {'250.24', '250.24(C)'},
    '42 - Article 406 - Receptacles, Attachment Plugs, and Flanged Inlets.vtt': {'406.7', '406.7(D)'},
}

def letter_after(txt, pos):
    """the (X) spoken right after a section that ended at txt[pos], else None"""
    m = re.compile(LET, re.I).match(txt, pos)
    if not m: return None
    raw = m.group('let')
    if len(raw) == 1 and raw.isupper() and raw != 'A':
        return LETTER[raw.lower()]
    return LETTER[raw.lower()] if LET_FOLLOW.match(txt, m.end()) else None

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
    own = the article this video is about; other articles are cross-references, not the lesson.

    Heard forms: "200.6", "200 six", "200 at six", "200 dot six", "200, that 63",
    "200 at twenty one", each with an optional letter after ("200 at six be" = 200.6(B)).
    In the video's own article, a run-together number with a letter or an exception
    after it is read too: in Article 200, "206 E exception" is 200.6(E)."""
    rx = re.compile(r'\b(' + '|'.join(sorted(arts, key=len, reverse=True)) + r')\b' + SEP + r'(\d{1,3}|' + WORD + r')\b', re.I)
    glued = re.compile(r'\b(' + '|'.join(sorted(arts, key=len, reverse=True)) + r')\b'
                       + r'(?:\s*\.\s*|\s*,?\s+(?:that|dot|at)\s+)(\d{1,3})([a-gA-G])\d?\b')
    fused = re.compile(r'(?<![\d.,/])\b(\d{3,5})\b(?![.,/]\d)')
    hits = {}
    def hit(sec, t):
        if sec not in hits: hits[sec] = max(0, t - 4)   # back up a beat for the lead-in
    for t, txt in cues(path):
        for m in rx.finditer(txt):
            art = m.group(1)
            if UNIT.match(txt, m.end()): continue    # "240 at 30 amps" is a quantity
            sub = str(num_word(m.group(2)))
            if sub == '0' or len(sub) > 3: continue
            if int(sub) > 200: continue          # no NEC section runs that high: "110 911" is "110.11" misheard
            if own and art != own: continue      # keep the article being taught, not passing mentions
            sec = art + '.' + sub
            if sec in NOT_SAID.get(os.path.basename(path), ()): continue
            hit(sec, t)
            L = letter_after(txt, m.end())
            # "250 to a five" is 250.52(A)(5) misheard: a homophone ("to", "for") with no
            # "that"/"at"/"dot" before it carries a letter only when the sentence ends on
            # the letter ("404 to see" is 404.2(C))
            if L and m.group(2).lower() in ('to', 'too', 'for') and not txt[m.end(1):m.start(2)].strip():
                if not re.match(LET + r'\s*(?:[.,;:?!]|$)', txt[m.end():], re.I): L = None
            if L and f'{sec}({L})' not in NOT_SAID.get(os.path.basename(path), ()): hit(f'{sec}({L})', t)
        # "240 that 4g2" is 240.4(G)(2): a letter glued to the number, after a spoken "that"/"at"/"dot"
        for m in glued.finditer(txt):
            art, sub = m.group(1), str(int(m.group(2)))
            if own and art != own: continue
            sec = art + '.' + sub
            if sub == '0' or int(sub) > 200 or f'{sec}({m.group(3).upper()})' in NOT_SAID.get(os.path.basename(path), ()): continue
            hit(sec, t)
            hit(f'{sec}({m.group(3).upper()})', t)
        if not own or len(own) != 3: continue
        for m in fused.finditer(txt):
            n = m.group(1)
            if n in arts: continue               # "210" in Article 200 is its own article, not 200.10
            if len(n) == 3:
                # "two oh six" in Article 200. Only a round hundred runs on like this:
                # in Article 250, "253 C" is 250.53(C), not 250.3(C)
                if not own.endswith('00') or n[:2] != own[:2] or n[2] == '0': continue
                sub = n[2]
            else:
                if not n.startswith(own): continue
                sub = n[len(own):]
                if sub.startswith('0') or len(sub) > 2: continue
            # the run-together form is only trusted with a letter or an exception on it
            L = letter_after(txt, m.end())
            exc = re.match(r'\s*,?\s*exception\b', txt[m.end():], re.I)
            if not L and not exc: continue
            if UNIT.match(txt, m.end()): continue
            sec = own + '.' + sub
            if sec in NOT_SAID.get(os.path.basename(path), ()): continue
            hit(sec, t)
            if L and f'{sec}({L})' not in NOT_SAID.get(os.path.basename(path), ()): hit(f'{sec}({L})', t)
    return hits

# Part B's caption file is a byte-for-byte copy of Part A's; 406 and 680 in Bonding &
# Grounding stream shorter than their captions run (a different cut: 680's captions
# name 680.40 past the stream's end), so their times come from the slides alone
CAPTION_COPIES = {'23UNECBGArticle250PartB', '23UNECBGArticle406', '23UNECBGArticle680'}

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
        # captions that do not belong to the stream that plays (see CAPTION_COPIES)
        if vid in CAPTION_COPIES: continue
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
