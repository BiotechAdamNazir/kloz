# English cloze sets (kloz/en)

Student pages: https://biotechadamnazir.github.io/kloz/en/

One template, many data files. `../index.html` is the shared Kloz page (it is also the live BM Kloz Karangan page).
`build.py` copies it, swaps in English branding, embeds one data file, and writes `<slug>.html`.

## Add a set

1. Put a data file in `src/<slug>.json` (format below).
2. `python en/build.py`
3. Commit and push. GitHub Pages republishes in about a minute.
4. Test the live link on desktop and phone widths before sending it to students.

## Data format

| Key | Meaning |
|---|---|
| `t`, `q`, `lv` | title, instruction line, level tag |
| `lang` | `"en"` |
| `mode` | `"key"` = self-check plus Show answers |
| `wb` / `fb` | word box on / floating word-box bubble on |
| `lab` | show class labels (Grammar, Vocabulary) under gaps |
| `dr` | draft banner; `true` until Adam approves |
| `P` | paragraphs: strings plus gap numbers 0..n-1, in order |
| `A` | answers per gap: main answer first, then accepted alternatives |
| `C`, `CL` | class per gap; class labels and colour slots |
| `N` | answer-key note per gap |
| `X` | decoys (words in the box that are not needed) |
| `ch` | challenge writing task |

Other keys (`slug`, `review`, `decoy_notes`, `source_notes`) stay in `src/` and are not published in the page.

## Rules

- Template changes must be switched on by a data flag (like `fb`), so the BM page does not change by accident.
- No student data in this public repo. Students' answers and names stay in their own browser.
- Full workflow: Hermes skill `kloz-cloze-sets`.
