#!/usr/bin/env python3
"""Merge a pasted quiz (the shape Claude in Chrome returns) into quizzes.json and check it.
   python3 addquiz.py pasted.json            # one or several JSON objects in the file
Each object: {"key": "...", "unit": "...", "questions": [{"number", "section", "question", "choices", "answer"?, "keysays"?}]}
Overrides for questions the key could not settle go in overrides.json: {"KEY": {"n": {"answer": "d", "computed": "why"}}}."""
import json, re, sys
Q = json.load(open("quizzes.json")) if __import__("os").path.exists("quizzes.json") else {}
OV = json.load(open("overrides.json")) if __import__("os").path.exists("overrides.json") else {}
todo = {t["key"]: t for t in json.load(open("quizzes.todo.json"))}
raw = open(sys.argv[1]).read()
objs = [json.loads(m) for m in re.findall(r"\{\s*\"key\".*?\n\}", raw, re.S)]
for o in objs:
    key = o["key"]; t = todo.get(key, {})
    qs = []
    for q in o["questions"]:
        r = {"n": q["number"], "q": q["question"], "choices": q["choices"], "ref": q.get("section", "")}
        if "answer" in q: r["answer"] = q["answer"]
        if "keysays" in q: r["keysays"] = q["keysays"]
        ov = OV.get(key, {}).get(str(q["number"]))
        if ov: r.update(ov)
        qs.append(r)
    Q[key] = {"book": t.get("book", o.get("book", "")), "quiz": t.get("quiz", o.get("unit", key)), "page": t.get("page"), "unit": o.get("unit", ""), "questions": qs}
    # checks
    nums = [q["n"] for q in qs]; problems = []
    if nums != list(range(1, len(nums) + 1)): problems.append("numbering gap: " + str(nums))
    for q in qs:
        if len(q["choices"]) < 4: problems.append(f"Q{q['n']} has {len(q['choices'])} choices")
        if "answer" in q and q["answer"] not in q["choices"]: problems.append(f"Q{q['n']} answer {q['answer']} not a choice")
    missing = [q["n"] for q in qs if "answer" not in q]
    print(f"{key}: {len(qs)} questions, {len(qs) - len(missing)} answered" + (f", MISSING answers {missing}" if missing else "") + ("; " + "; ".join(problems) if problems else ""))
json.dump(Q, open("quizzes.json", "w"), indent=1, ensure_ascii=False)
print("quizzes.json:", len(Q), "quizzes")
