# -*- coding: utf-8 -*-
"""Fractions the way they are written on a tape measure.

The books mix three styles — 1/4 as a vulgar glyph, 1/16 as a superscript one
over a plain sixteen, and 2-1/8 squashed to 21/8 with a fraction slash. On a
phone the last two read as 116 and 21/8, which is a wrong box and a wrong plate.
"""
import json, re, sys

try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass

VULGAR = {"¼": (1, 4), "½": (1, 2), "¾": (3, 4), "⅐": (1, 7), "⅑": (1, 9),
          "⅒": (1, 10), "⅓": (1, 3), "⅔": (2, 3), "⅕": (1, 5), "⅖": (2, 5),
          "⅗": (3, 5), "⅘": (4, 5), "⅙": (1, 6), "⅚": (5, 6), "⅛": (1, 8),
          "⅜": (3, 8), "⅝": (5, 8), "⅞": (7, 8)}
SUP = {"⁰": "0", "¹": "1", "²": "2", "³": "3", "⁴": "4",
       "⁵": "5", "⁶": "6", "⁷": "7", "⁸": "8", "⁹": "9"}
SUB = {"₀": "0", "₁": "1", "₂": "2", "₃": "3", "₄": "4",
       "₅": "5", "₆": "6", "₇": "7", "₈": "8", "₉": "9"}
SLASH = "⁄"


def fix(t):
    if not t: return t
    out = t

    # a vulgar glyph, hyphenated onto a whole number in front of it
    def v(m):
        n, d = VULGAR[m.group(2)]
        return f"{m.group(1)}-{n}/{d}" if m.group(1) else f"{n}/{d}"
    out = re.sub(r"(\d*)([" + "".join(VULGAR) + r"])", v, out)

    # a superscript numerator over a fraction slash: 1/16, 4/18
    def s(m):
        num = "".join(SUP[c] for c in m.group(2))
        return f"{m.group(1)}-{num}/{m.group(3)}" if m.group(1) else f"{num}/{m.group(3)}"
    out = re.sub(r"(\d*)([" + "".join(SUP) + r"]+)" + SLASH + r"(\d+)", s, out)

    # a plain fraction slash. An improper fraction with a two-digit numerator is a
    # mixed number that lost its space in the PDF: 21/8 is 2-1/8, never twenty-one eighths.
    def p(m):
        num, den = m.group(1), m.group(2)
        if len(num) > 1 and int(num) >= int(den):
            return f"{num[:-1]}-{num[-1]}/{den}"
        return f"{num}/{den}"
    out = re.sub(r"(\d+)" + SLASH + r"(\d+)", p, out)

    # a lone superscript that is not a fraction stays (cm2, 4 squared, I2 x R are
    # correct notation an electrician reads every day) — nothing to do.
    return out


def ambiguous(t):
    """only the forms that misread on a phone: a superscript numerator over a plain
    denominator (1/16 looks like 116) and a mixed number squashed together (2-1/8
    printed as 21/8). A vulgar glyph like 1/2 or 3/8 reads correctly at any size and
    is what the book prints, so it is left alone."""
    return SLASH in (t or "")


def walk(Q, apply=False):
    changes = []
    for k, q in Q.items():
        for x in q["questions"]:
            parts = [x["q"]] + list(x.get("choices", {}).values())
            # one question is read as a set, so if any part of it needs fixing the
            # whole question is made to match rather than mixing two styles in one list
            if not any(ambiguous(t) for t in parts): continue
            a = fix(x["q"])
            if a != x["q"]:
                changes.append((k, x["n"], "question", x["q"], a))
                if apply: x["q"] = a
            for L, val in list(x.get("choices", {}).items()):
                b = fix(val)
                if b != val:
                    changes.append((k, x["n"], "choice " + L, val, b))
                    if apply: x["choices"][L] = b
    return changes


if __name__ == "__main__":
    Q = json.load(open("quizzes.json", encoding="utf-8"))
    ch = walk(Q, apply="--apply" in sys.argv)
    print(f"{len(ch)} pieces of text change")
    for k, n, where, before, after in ch:
        print(f"  {k} Q{n} {where}")
        print(f"      was  {before[:96]}")
        print(f"      now  {after[:96]}")
    if "--apply" in sys.argv:
        json.dump(Q, open("quizzes.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
        print("\nquizzes.json written")
