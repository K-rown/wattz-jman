#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""How often each section a video covers is the answer to a quiz or exam question.

Every question in quizzes.json carries Mike Holt's own answer-key reference
("210.8(B)(2)", "Table 310.16", "250.53(A)(4)"). A section that keeps coming up as
the answer is a section worth finding fast in an open-book exam, so it is the one
to highlight first.

Each reference is counted once, against the MOST SPECIFIC section in a video's
book list that holds it (210.8(B)(2) counts for 210.8(B), not again for 210.8).
Questions from the Exam Prep and Simulated Exams books are counted apart too:
they are written the way the real exam is.

    python3 exam_refs.py        # writes exam_refs.json

Output: {video_id: {section: [all_questions, exam_style_questions]}}
"""
import json, re

REF = re.compile(r'(?<![\d.])(\d{2,3})\.(\d{1,3})((?:\s?\([A-Za-z0-9]{1,4}\))*)')
EXAM_BOOKS = ('Exam', 'Simulated')


def norm(art, sec, parens):
    """'210', '8', '(b)(2)' -> '210.8(B)(2)'; the first level is a capital letter in the code"""
    groups = re.findall(r'\(([A-Za-z0-9]{1,4})\)', parens or '')
    if groups and groups[0].isalpha():
        groups[0] = groups[0].upper()
    return f'{art}.{sec}' + ''.join(f'({g})' for g in groups)


def refs_in(text):
    """the NEC sections a key reference names; theory units (14.3) and annexes are not code sections"""
    out = []
    if not text or text.strip().lower().startswith('theory'):
        return out
    for m in REF.finditer(text):
        art = int(m.group(1))
        if art < 90 or art > 840:
            continue
        out.append(norm(m.group(1), m.group(2), m.group(3)))
    return out


def best(book, ref):
    """the most specific entry of a video's book list that holds this reference"""
    hit = None
    for x in book:
        if ref == x or ref.startswith(x + '('):
            if hit is None or len(x) > len(hit):
                hit = x
    return hit


def main():
    quizzes = json.load(open('quizzes.json', encoding='utf-8'))
    books = json.load(open('book_sections.json', encoding='utf-8'))
    out, total, placed = {}, 0, 0
    for key, quiz in quizzes.items():
        exam_style = key.startswith(EXAM_BOOKS)
        for q in quiz['questions']:
            for r in set(refs_in(q.get('ref', ''))):
                total += 1
                landed = False
                for vid, book in books.items():
                    x = best(book, r)
                    if not x:
                        continue
                    c = out.setdefault(vid, {}).setdefault(x, [0, 0])
                    c[0] += 1
                    if exam_style:
                        c[1] += 1
                    landed = True
                placed += landed
    out = {v: dict(sorted(s.items(), key=lambda kv: books[v].index(kv[0]))) for v, s in out.items()}
    json.dump(out, open('exam_refs.json', 'w', encoding='utf-8'), indent=0, ensure_ascii=False)
    print(f'exam_refs.json: {total} section references in the answer keys, {placed} land on a video\'s section, '
          f'{sum(len(s) for s in out.values())} sections tested across {len(out)} videos')


if __name__ == '__main__':
    main()
