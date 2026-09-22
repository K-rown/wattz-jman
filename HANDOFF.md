> **DONE — kept only as a record.** All three jobs in this brief were finished on
> 21 September 2026: GitHub Pages is serving from `main`, every quiz is in the app
> (135 of them now, not 58, read out of the books themselves), and the app has been
> through a full pass for accuracy and clarity. Since then it has become a library
> for the whole crew rather than one person's calendar. **Read `README.md` for what
> the app is today, and `QUIZZES.md` for where the quizzes come from.** Nothing
> below needs doing again.

# HANDOFF — finish the quizzes, restore the app, leave it ready to study

Run this on Kymani's PC in a Claude Code session with Claude in Chrome connected
(`/chrome`), signed in to mikeholt.com and GitHub. Work in this repo. Do the three
jobs below in order, all of them, without stopping to ask unless something in
"Stop and ask" happens. Push after each job. When everything below is green, say
"ready to study" and stop.

The app is `index.html` (built by `python3 build.py` from `curriculum.json`,
`videos.json`, `quizzes.json`, `overrides.json`). Never hand-edit `index.html`.
The crew page is served by GitHub Pages at https://k-rown.github.io/wattz-jman/.

## Job 1 — restore the app (5 minutes)

GitHub Pages was switched off when the repo went private and did not come back
when it went public. Enable it, from a branch:

    gh api -X POST repos/K-rown/wattz-jman/pages -f build_type=legacy -f source[branch]=main -f source[path]=/

If that returns 409 it already exists; then `gh api repos/K-rown/wattz-jman/pages`
must show `"status": "built"` or `"building"`. If the API refuses, do it in the
browser: Settings → Pages → Source: Deploy from a branch → main → / (root) → Save.

Then push an empty change (`python3 build.py && git commit -am "rebuild" && git push`)
and confirm:
- `https://k-rown.github.io/wattz-jman/` returns 200 and its footer "Generated" time
  matches the build you just pushed;
- in Chrome, open it, tap Watch on Day 1 — the video plays in the page;
- `.github/workflows/pages.yml` runs green (it deploys the same files; harmless
  alongside branch deploys — if it fights the branch deploy, delete the workflow).

## Job 2 — every quiz, with Mike Holt's answers (the long one)

`quizzes.todo.json` lists all 58 quizzes: book, quiz, digital-book viewer URL,
and the page the quiz starts on. `quizzes.json` already has Theory Units 24–27.
Do every remaining entry, in list order.

For each quiz:
1. Open `viewer_url` in Chrome, go to `page` (the viewer's page box, NOT the
   printed page number). Read the quiz through its last question — a quiz runs
   2–4 viewer pages.
2. Transcribe every question in order, word for word, with every choice.
3. Open My Digital Products → Answer Keys → the same book, find that unit or
   chapter, and take the answer letters from there.
4. Append the quiz to a file `paste/<key>.json` in the shape below, then run
   `python3 addquiz.py paste/<key>.json`. The script merges it into
   `quizzes.json` and prints a check line: question count, answered count,
   numbering gaps, choices missing, answers not among the choices. Fix anything
   it names before moving on.

Shape (one object per file; `key` is the todo entry's `key`):

    {"key":"NEC_Vol_1_Ch_1","unit":"Chapter 1—General Rules","questions":[
      {"number":1,"section":"100","question":"…","choices":{"a":"…","b":"…","c":"…","d":"…"},"answer":"b"}]}

Rules that are not negotiable:
- Never invent a question. Every question comes from the book page.
- Never guess an answer. `answer` comes from the answer key only. If the key is
  for a different printing and its answer is not among the book's choices, leave
  `answer` out and put the key's exact text in `"keysays"`. Then, ONLY if the
  question is pure arithmetic or a plain NEC table lookup, add the worked answer
  to `overrides.json` under that key and question number as
  `{"answer":"d","computed":"the arithmetic or table value, shown"}` (see the
  existing entries). Anything that is not arithmetic stays unanswered and goes in
  the report.
- NEC Vol 1, Vol 2 and B&G quizzes are per chapter or per article and can be
  long (100+ questions). Do them whole. Do not sample.
- Commit and push after every five quizzes: `git add -A && git commit -m "quizzes: …" && git push`.

When all 58 are in: `python3 build.py`, then confirm every day's card in the app
shows its quiz box (`Take quiz`) — open `index.html` locally and check Days 1, 4,
8, 13, 20, 30, 37 at least. Push.

## Job 3 — tidy so tomorrow is just studying

- `python3 build.py` runs clean and `index.html` loads with no console errors.
- The GitHub page and the video both work (Job 1).
- `README.md`: keep it to what the app is and the one link. Remove anything about
  Supabase and the name card if Kymani never set those up (he didn't — the page
  saves per browser; that is fine for one laptop). Leave `progress.sql` and
  `SYNC` in place but make no promises about them in the README.
- Delete `paste/` once its files are merged.
- Leave `QUIZZES.md`, `quizzes.todo.json`, `addquiz.py`, `overrides.json`,
  `curriculum.json`, `videos.json`, `build.py`, `artifact.html` alone.
- Final commit message: "ready to study".

## Report, at the end, in the chat

- Quizzes done: N of 58, total questions, how many answers came from the key,
  how many were worked (overrides), and the list of any still unanswered with
  the key's text.
- The GitHub page URL and the "Generated" time on it.
- Anything in "Stop and ask" you hit.

## Stop and ask only if

- The Mike Holt login is gone or the viewer refuses a book.
- A quiz page in `quizzes.todo.json` is not actually the quiz (wrong page).
- The answer key for a whole book is missing from the account.
Otherwise keep going. Kymani wants to open the page tomorrow and study.
