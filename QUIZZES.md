# Where the quizzes come from

Every quiz in the app was read out of Mike Holt's own books. There are 135 of
them and 5,270 questions: every unit review, every chapter review, every final
exam, and the two Journeyman Simulated Exams.

## The shape

`quizzes.json` at the repo root, keyed `<Book>_<Quiz>` with spaces as underscores
(`Theory_Unit_24`, `NEC_Vol_1_Ch_1`, `B&G_Art_250`, `Simulated_Exams_Exam_A`):

```json
{
  "Theory_Unit_24": {
    "book": "Theory",
    "quiz": "Unit 24",
    "page": 224,
    "questions": [
      {
        "n": 1,
        "q": "The primary winding of a transformer is the winding that _____.",
        "choices": { "a": "receives the power", "b": "delivers the power", "c": "…", "d": "…" },
        "answer": "a",
        "ref": "24.2 Primary versus Secondary",
        "computed": "optional: the working, shown to somebody who got it wrong"
      }
    ]
  }
}
```

`n` is the number printed in the book, so a gap is allowed and honest — it means
that question was left out, and the quiz's `source` line says why.

## How they got there

The books and their answer keys are PDFs on the shop machine, outside this repo:

```
C:\Users\Kymani\projects\jmen\MikeHolt\books\
C:\Users\Kymani\projects\jmen\MikeHolt\answer-keys\
```

One agent per book read its PDF with `pypdf`, wrote `paste2/<n>-<book>.json`, and
had to reproduce the hand-checked quizzes exactly where they overlapped. They did:
across the 58 quizzes that already existed, every answer agreed. `books.py` then
folds the result into `quizzes.json`, keeping the hand-checked version wherever
there is one, because those carry worked arithmetic the book does not.

`resolved.json` holds answers for the handful of questions whose printed key did
not settle them, each with the working or the rule behind it. One question,
Theory Unit 10 Q23, is still unsettled and is left out rather than guessed.

The earlier route — transcribing quizzes by eye through the book viewer in
Chrome — is finished and not needed again.

## Rules, unchanged

- **Never guess an answer.** Leave the question out and say so in `source`.
- `answer` must be one of that question's own choice letters. `check.py` fails otherwise.
- This repo is private. The questions are Mike Holt's copyrighted text, kept here
  for a crew who own the books. Never make it public with this file in it.
