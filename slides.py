#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Read the section number off every slide Mike puts on screen.

Every Mike Holt slide carries its NEC section in the title, top centre
("Purpose of the NEC / Protect People and Property / 90.2(A)"). The spoken
transcript misses plenty of those, so this walks the video itself:

  1. pull a frame every few seconds straight from the stream (no download)
  2. keep only the title strip at the top
  3. drop frames whose title is the same as the one before (one slide, many frames)
  4. lay the unique titles out on contact sheets for reading

    python3 slides.py 23UNEC1Article90          # sheets for one video
    python3 slides.py 23UNEC1Article90 --every 4

The sheets land in slides/<video_id>/. Read them, then write what you read into
slides/<video_id>.json as {"seconds": "section"} and run merge() to fold it into
sections.json beside the spoken index.
"""
import json, os, re, subprocess, sys

STREAM = 'https://vod.mikeholt.com/{v}/HLS/{v}_720.m3u8'
OUTDIR = 'slides'
EVERY = 6          # seconds between frames
COLS, ROWS = 4, 6  # tiles per contact sheet

def frames(vid, every=EVERY, seconds=None):
    """crop the title strip out of the stream, one tile every `every` seconds"""
    d = os.path.join(OUTDIR, vid, 'raw')
    os.makedirs(d, exist_ok=True)
    for f in os.listdir(d): os.remove(os.path.join(d, f))
    vf = f'fps=1/{every},crop=iw:ih*0.22:0:0,scale=560:-1'
    cmd = ['ffmpeg', '-loglevel', 'error', '-i', STREAM.format(v=vid)]
    if seconds: cmd += ['-t', str(seconds)]
    cmd += ['-vf', vf, '-q:v', '4', os.path.join(d, '%05d.jpg')]
    subprocess.run(cmd, check=True)
    return sorted(os.listdir(d))

def ahash(path):
    from PIL import Image
    im = Image.open(path).convert('L').resize((32, 8))
    px = list(im.getdata()); avg = sum(px) / len(px)
    return ''.join('1' if p > avg else '0' for p in px)

def dist(a, b):
    return sum(1 for x, y in zip(a, b) if x != y)

def unique(vid, every=EVERY):
    """[(seconds, path)] one per distinct slide title"""
    d = os.path.join(OUTDIR, vid, 'raw')
    keep, last = [], None
    for i, name in enumerate(sorted(os.listdir(d))):
        p = os.path.join(d, name)
        h = ahash(p)
        if last is None or dist(h, last) > 22:   # a new title, not the same slide again
            keep.append(((i) * every, p)); last = h
    return keep

def sheets(vid, keep):
    """lay the unique titles out, numbered, for reading"""
    from PIL import Image, ImageDraw
    out = os.path.join(OUTDIR, vid)
    for f in os.listdir(out):
        if f.startswith('sheet'): os.remove(os.path.join(out, f))
    per = COLS * ROWS
    made = []
    for s in range(0, len(keep), per):
        chunk = keep[s:s + per]
        tiles = [Image.open(p) for _, p in chunk]
        w, h = tiles[0].size
        sheet = Image.new('RGB', (COLS * w, ROWS * (h + 22)), 'white')
        d = ImageDraw.Draw(sheet)
        for k, (t, _) in enumerate(chunk):
            x, y = (k % COLS) * w, (k // COLS) * (h + 22)
            sheet.paste(tiles[k], (x, y + 22))
            d.rectangle([x, y, x + w, y + 21], fill='black')
            d.text((x + 4, y + 5), f'#{s + k}  {t // 60}:{t % 60:02d}', fill='white')
        path = os.path.join(out, f'sheet{s // per:02d}.jpg')
        sheet.save(path, quality=88)
        made.append(path)
    return made

def merge(vid):
    """fold slides/<vid>.json {"seconds": "section"} into sections.json"""
    read = json.load(open(os.path.join(OUTDIR, vid + '.json'), encoding='utf-8'))
    S = json.load(open('sections.json', encoding='utf-8')) if os.path.exists('sections.json') else {}
    cur = S.get(vid, {})
    added = 0
    for t, sec in read.items():
        m = re.match(r'^(\d{2,3}\.\d+(?:\([A-Za-z0-9]+\))*[a-z]?)', sec.strip())
        if not m: continue
        sec = m.group(1)
        if sec not in cur or int(t) < cur[sec]:
            cur[sec] = int(t); added += 1
    S[vid] = dict(sorted(cur.items(), key=lambda kv: kv[1]))
    json.dump(S, open('sections.json', 'w', encoding='utf-8'), indent=0, ensure_ascii=False)
    print(f'{vid}: {added} from the slides, {len(S[vid])} sections now')

if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    every = int(sys.argv[sys.argv.index('--every') + 1]) if '--every' in sys.argv else EVERY
    secs = int(sys.argv[sys.argv.index('--secs') + 1]) if '--secs' in sys.argv else None
    vid = args[0]
    if '--merge' in sys.argv:
        merge(vid)
    else:
        print('pulling frames...'); frames(vid, every, secs)
        keep = unique(vid, every)
        print(f'{len(keep)} distinct slides')
        for p in sheets(vid, keep): print('  ', p)
