# wattz-jman

**Path to Journeyman** — the whole Mike Holt 2023 Journeyman program in one page.

https://k-rown.github.io/wattz-jman/

Every video and every quiz from the seven books, in the order Mike teaches them,
by book and chapter. Tap a chapter, tap a video, it plays in the page. Tick what
you finish and it remembers, on that device, with nothing to sign up for. Where a
video's NEC sections are known, each one is a button that jumps the video to the
moment Mike teaches it.

Kymani's own dated run at it is still there, one press away under **My pace**.

Not for sharing outside the crew: the quizzes are Mike Holt's, and everyone using
this should own the books.

## How it is built

`index.html` is generated. **Never hand-edit the data block inside it.**

```
python3 sections.py     # NEC section timestamps, from the captions and the slides
python3 books.py        # quizzes and page numbers, out of the seven book PDFs
python3 build.py        # write index.html
python3 check.py        # read the built page back and fail on anything wrong
```

| file | what it is |
|---|---|
| `curriculum.json` | the 52-day plan: units, the day it starts, what is already done |
| `videos.json` | all 169 videos: book, chapter, article, length, stream id |
| `quizzes.json` | every quiz in the program, question by question, with the key |
| `program.json` | each video's page in the book and the quiz that follows it |
| `sections.json` | `{video: {section: seconds}}` — where each NEC section is taught |
| `overrides.json` | hand corrections to durations and labels |

`books.py` reads `paste2/*.json`, which is what was pulled out of the book and
answer-key PDFs. Those PDFs are not in this repo and neither is that folder.

`slides.py` pulls a frame every few seconds from a video, keeps the title strip
where every Mike Holt slide prints its section, drops repeats, and lays the rest
out on contact sheets to be read by eye. What is read goes in `slides/<video>.json`
and `sections.py` folds it in, ahead of the transcript, because the slide is exact
and the machine transcription is not.

Run `check.py` before every push. It parses the page's javascript, follows every
quiz link, checks every answer is one of its own choices, checks every section
jump lands inside its video, and checks every day falls on the weekday it claims.
