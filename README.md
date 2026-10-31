# Kloz Karangan (live student pages)

Live: https://biotechadamnazir.github.io/kloz/ · English sets: https://biotechadamnazir.github.io/kloz/en/

## Three kinds of student link

| Link | Where the worksheet lives | Can a fix reach it later? |
|---|---|---|
| `…/kloz/#w=<id>` **(use this)** | `w/<id>.json` in this repo | **Yes.** Fix, rebuild, push: every link already sent shows the fix. |
| `…/kloz/#k=…` (Studio "Salin pautan") | packed inside the link itself | No. The link is a frozen copy. |
| `.html` file (Studio "Fail murid") | inside the file | No. Offline backup only. |

## Publish or fix a BM worksheet

1. Essays live in `essays/<essay-id>.json` (Kloz bank format, `status: "draf"` until Adam approves).
2. Worksheets live in `worksheets.json`: essay id + Studio settings (word classes, lesson lenses, gap count, mode).
3. `python3 publish.py` rebuilds every `w/<id>.json` and prints each link. It reports when a fix changed any answers.
4. Commit and push. GitHub Pages republishes in about a minute. Open the link once on a phone before sending it.

`python3 publish.py studio` also writes `studio/kloz-studio.html`, the teacher Studio with every essay loaded.

## How it behaves for students

- Answers save in the student's own browser. A fix to wording keeps them; a change to the gaps or answers starts the sheet fresh.
- `status: "draf"` shows a draft banner. Set `"disahkan"` once Adam has reviewed the essay, then rebuild.
- Answers are inside the worksheet file so the page can mark them. A curious student can find them in the page source.

## Rules

- **No student names or results in this public repo.** Name worksheets by topic, not by student.
- Fix mistakes in `essays/`, never by hand-editing `w/` files (the next rebuild would undo it).
- Lessons for writing essays: Google Drive, *Kloz Karangan – Lessons Learned (baca dahulu / read first)*.
