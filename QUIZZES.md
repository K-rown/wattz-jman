# Bringing the quizzes into the app

Run this from a Claude Code session on the laptop with Claude in Chrome
connected (`/chrome`), signed in to the Mike Holt account. This sandbox
cannot reach mikeholt.com, so the transcription has to happen there.

`quizzes.todo.json` lists all 58 quizzes: book, quiz name, the digital book
viewer URL and the page the quiz starts on. Answer keys are under
My Digital Products → Answer Keys in the same account.

Write `quizzes.json` at the repo root in exactly this shape and push it:

```json
{
  "Theory_Unit_24": {
    "book": "Theory",
    "quiz": "Unit 24",
    "page": 224,
    "questions": [
      {
        "n": 1,
        "q": "The primary winding of a transformer is the winding that ____.",
        "choices": { "a": "receives the power", "b": "delivers the power", "c": "…", "d": "…" },
        "answer": "a",
        "ref": "Unit 24.2"
      }
    ]
  }
}
```

Rules:
- The key is the `key` field from `quizzes.todo.json`.
- Transcribe every question in the quiz, in order, with every choice, word for word.
- `answer` is the letter from Mike Holt's answer key. `ref` is whatever the key cites (a section, an NEC article), or omit it.
- Do one quiz, stop, and let Kymani check it against the book before doing the rest.
- Never guess an answer. If a key is missing for a quiz, leave `answer` out and say which one.
- This repo is private. The quizzes are Mike Holt's copyrighted text for Kymani's own study; never make the repo public with this file in it.

Suggested first prompt for that session:

> Read QUIZZES.md and quizzes.todo.json. Use Chrome to open the first quiz
> (Theory Unit 24, page 224 in the Theory book viewer) and its answer key,
> transcribe it into quizzes.json in the shape QUIZZES.md shows, then stop
> so I can check it.
