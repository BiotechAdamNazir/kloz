# build.py: make English cloze pages from the one Kloz template plus a data file.
# Template: ../index.html (the live Kloz Karangan page, unchanged).
# Data:     src/<slug>.json (Kloz format, lang "en").
# Output:   <slug>.html (works online at /kloz/en/<slug>.html, and offline as a single file).
#           index.html = a short list of all sets.
# Run:      python en/build.py   (from the repo root, or anywhere)
import json, pathlib, html

HERE = pathlib.Path(__file__).resolve().parent
TEMPLATE = (HERE.parent / "index.html").read_text(encoding="utf-8")
BRAND = "Kloz · English Cloze"

# Branding swaps for English sets. Each must match exactly once, so a template change is caught.
SWAPS = [
    ('<html lang="ms">', '<html lang="en">'),
    ('<title>Kloz Karangan</title>', '<title>English Cloze</title>'),
    ('<div class="eyebrow">Kloz Karangan${D.lv', '<div class="eyebrow">' + BRAND + '${D.lv'),
    ('const txt=`*Kloz Karangan* – ${D.t}', 'const txt=`*English Cloze* – ${D.t}'),
    ('document.title=(D.t||"Kloz Karangan")+" · Kloz";', 'document.title=(D.t||"English Cloze")+" · Kloz";'),
    ('r.at.toLocaleString("ms-MY");', 'r.at.toLocaleString("en-GB");'),
]
EMBED = '<script id="kloz-embedded" type="application/json">null</script>'
KEEP = ["t", "q", "lv", "lang", "mode", "wb", "fb", "lab", "dr", "P", "A", "C", "CL", "N", "X", "ch"]


def check(d, name):
    n = len(d["A"])
    gaps = [x for p in d["P"] for x in p if isinstance(x, int)]
    assert gaps == list(range(n)), f"{name}: gaps out of order {gaps}"
    assert len(d["C"]) == n and len(d["N"]) == n, f"{name}: A/C/N lengths differ"
    main = [a[0].lower() for a in d["A"]]
    assert len(set(main)) == n, f"{name}: duplicate answer"
    assert not set(x.lower() for x in d["X"]) & set(main), f"{name}: decoy equals an answer"
    return n


def page(d):
    out = TEMPLATE
    for old, new in SWAPS:
        assert out.count(old) == 1, f"template changed: {old!r}"
        out = out.replace(old, new)
    data = {k: d[k] for k in KEEP if k in d}
    blob = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    assert out.count(EMBED) == 1
    return out.replace(EMBED, f'<script id="kloz-embedded" type="application/json">{blob}</script>')


sets = []
for f in sorted((HERE / "src").glob("*.json")):
    d = json.loads(f.read_text(encoding="utf-8"))
    slug = d.get("slug") or f.stem
    n = check(d, f.name)
    (HERE / f"{slug}.html").write_text(page(d), encoding="utf-8")
    sets.append((slug, d["t"], n, d.get("dr")))
    print(f"built en/{slug}.html  {n} gaps  draft={bool(d.get('dr'))}")

items = "\n".join(
    f'<li><a href="{s}.html">{html.escape(t)}</a> <span>{n} gaps{" · draft" if dr else ""}</span></li>'
    for s, t, n, dr in sets)
(HERE / "index.html").write_text(f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>English Cloze · Kloz</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Young+Serif&family=Atkinson+Hyperlegible:wght@400;700&display=swap">
<style>body{{margin:0;background:#eaeff6;color:#15213b;font:17px/1.5 "Atkinson Hyperlegible",system-ui,sans-serif}}
main{{max-width:640px;margin:40px auto;padding:24px 28px 24px 58px;background:#fff;border:1px solid #d3dbe8;border-radius:4px 16px 16px 4px;
background-image:linear-gradient(to right,transparent 40px,#d24a43 40px,#d24a43 41.5px,transparent 41.5px)}}
h1{{font:400 30px/1.1 "Young Serif",Georgia,serif;margin:4px 0 14px}}.e{{font-size:.72rem;letter-spacing:.12em;text-transform:uppercase;color:#56627c;font-weight:700}}
li{{margin:10px 0}}a{{color:#2348c4;font-weight:700}}span{{color:#56627c;font-size:.9rem}}</style></head>
<body><main><div class="e">Kloz · IGCSE English 0472</div><h1>English Cloze</h1><ul>
{items}
</ul></main></body></html>""", encoding="utf-8")
print("built en/index.html with", len(sets), "sets")
