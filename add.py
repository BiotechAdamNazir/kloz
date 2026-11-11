"""Add a Kloz to the repo in ONE step, or refresh the catalogue.

    python3 add.py <file> [<file> ...] [--made 2026-11-11] [--note "one line"] [--artifact <claude.ai link>]
    python3 add.py                 just re-sync catalog.json from essays/ and rebuild

<file> is either
  - a Kloz Studio page (.html) saved from a Claude artifact: every essay inside it is taken, or
  - an essay in Kloz bank format (.json).

What it does, in order:
  1. checks each essay (every unit used once, lesson spans in range, labels known)
  2. writes essays/<id>.json and merges any new class labels into studio/base-data.json
  3. gives each new essay two hosted sheets in worksheets.json: <id> (self-check) and <id>-skema (with answers)
  4. updates catalog.json, the list the teacher page (rak/) reads
  5. runs publish.py studio, which rebuilds w/*.json and the hosted Studio
  6. prints the links and the two git commands left to run

Nothing is pushed by this script. No student names anywhere: this repo is public.
"""
import datetime, glob, json, os, re, subprocess, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
BASE = "https://biotechadamnazir.github.io/kloz/"
TODAY = datetime.date.today().isoformat()


def load(p):
    return json.load(open(p, encoding="utf-8"))


def save(p, d, indent=None):
    json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=indent)


def read_source(path):
    """Return (essays, labels) from a Studio .html or an essay .json."""
    raw = open(path, encoding="utf-8").read()
    if path.lower().endswith((".html", ".htm")):
        m = re.search(r'<script type="application/json" id="kloz-data">(.*?)</script>', raw, re.S)
        if not m:
            sys.exit(f"{path}: no Kloz Studio data found (expected a <script id=\"kloz-data\"> block)")
        d = json.loads(m.group(1))
        return d["essays"], d.get("labels", {})
    d = json.loads(raw)
    if isinstance(d, dict) and "essays" in d:
        return d["essays"], d.get("labels", {})
    return (d if isinstance(d, list) else [d]), {}


def check(e, labels):
    for k in ("id", "lang", "title", "level", "jenis", "paras", "units"):
        assert e.get(k), f"{e.get('id', '?')}: missing '{k}'"
    assert re.fullmatch(r"[a-z0-9-]{3,70}", e["id"]), f"{e['id']}: id must be lowercase letters, digits and hyphens"
    idx = sorted(x for p in e["paras"] for x in p if isinstance(x, int))
    assert idx == list(range(len(e["units"]))), f"{e['id']}: every unit must be used exactly once"
    for l in e.get("lens", []):
        assert 0 <= l["a"] <= l["b"] < len(e["units"]), f"{e['id']}: lesson span out of range {l}"
    missing = {u["k"] for u in e["units"]} - set(labels)
    assert not missing, f"{e['id']}: no label for {sorted(missing)}; add them to studio/base-data.json"


def words(e):
    return sum(len(u["t"].split()) for u in e["units"])


def sync_catalog(extra=None):
    """Refresh the essay-backed entries of catalog.json. Hand-written fields are kept."""
    extra = extra or {}
    cat = load(f"{ROOT}/catalog.json")
    by = {i["id"]: i for i in cat["items"]}
    sheets = load(f"{ROOT}/worksheets.json")["worksheets"]
    for p in sorted(glob.glob(f"{ROOT}/essays/*.json")):
        e = load(p)
        it = by.get(e["id"])
        if not it:
            it = {"id": e["id"], "kind": "studio", "made": TODAY, "log": []}
            cat["items"].append(it)
            by[e["id"]] = it
        mine = [w for w in sheets if w["essay"] == e["id"]]
        gaps = 0
        for w in mine:
            f = f"{ROOT}/w/{w['id']}.json"
            if os.path.exists(f):
                gaps = max(gaps, len(load(f)["A"]))
        it.update({
            "kind": "studio", "home": "github", "title": e["title"], "lang": e["lang"], "level": e["level"],
            "jenis": e["jenis"], "status": e.get("status", "draf"), "source": e.get("sumber", ""),
            "words": words(e), "gaps": gaps,
        })
        links = it.setdefault("links", {})
        links["studio"] = f"{BASE}studio/kloz-studio.html#e={e['id']}"
        check_s = next((w for w in mine if w.get("mode", "check") == "check"), None)
        key_s = next((w for w in mine if w.get("mode") == "key"), None)
        if check_s:
            links["student"] = f"{BASE}#w={check_s['id']}"
        if key_s:
            links["key"] = f"{BASE}#w={key_s['id']}"
        x = extra.get(e["id"], {})
        if x.get("made"):
            it["made"] = x["made"]
        if x.get("note"):
            it["note"] = x["note"]
        if x.get("artifact"):
            links["artifact"] = x["artifact"]
    known = {l["id"] for l in cat["levels"]}
    for it in cat["items"]:
        if it.get("level") and it["level"] not in known:
            print(f"   NOTE: level '{it['level']}' ({it['id']}) is not in catalog.json 'levels'; add it so the page can sort it")
    cat["updated"] = TODAY
    save(f"{ROOT}/catalog.json", cat, indent=1)
    return cat


def main():
    args, opt, files = sys.argv[1:], {}, []
    i = 0
    while i < len(args):
        if args[i] in ("--made", "--note", "--artifact"):
            opt[args[i][2:]] = args[i + 1]
            i += 2
        else:
            files.append(args[i])
            i += 1
    base = load(f"{ROOT}/studio/base-data.json")
    ws = load(f"{ROOT}/worksheets.json")
    added, extra = [], {}
    for f in files:
        essays, labels = read_source(f)
        for k, v in labels.items():
            base["labels"].setdefault(k, v)
        for e in essays:
            e.setdefault("status", "draf")
            for k in ("umpan", "nogap", "lens"):
                e.setdefault(k, [])
            e.setdefault("cabaran", "")
            check(e, base["labels"])
            path = f"{ROOT}/essays/{e['id']}.json"
            state = "updated" if os.path.exists(path) else "new"
            if state == "updated" and load(path).get("status") == "disahkan" and e.get("status") != "disahkan":
                e["status"] = "disahkan"   # never silently un-approve an essay Adam has checked
            save(path, e)
            if not any(w["essay"] == e["id"] for w in ws["worksheets"]):
                n = 20 if words(e) >= 140 else 10
                for suf, mode in (("", "check"), ("-skema", "key")):
                    ws["worksheets"].append({
                        "id": e["id"] + suf, "essay": e["id"], "pref": [], "lens": ["pw", "pb", "kt", "tb"],
                        "count": n, "seed": 1, "mode": mode, "wb": True, "lab": False,
                        "note": "Default sheet: lesson gaps." + (" With Tunjuk jawapan." if suf else ""),
                    })
            added.append((e["id"], state))
            extra[e["id"]] = opt
    save(f"{ROOT}/studio/base-data.json", base)
    save(f"{ROOT}/worksheets.json", ws, indent=1)
    r = subprocess.run([sys.executable, f"{ROOT}/publish.py", "studio"], capture_output=True, text=True)
    if r.returncode:
        sys.exit("publish.py failed:\n" + r.stdout + r.stderr)
    cat = sync_catalog(extra)
    by = {i["id"]: i for i in cat["items"]}
    print(f"Catalogue: {len(cat['items'])} Kloz, {sum(1 for i in cat['items'] if i.get('home') == 'github')} on GitHub.")
    for eid, state in added:
        it = by[eid]
        print(f"\n{state.upper()}: {it['title']}  [{it['level']}, {it['lang']}, {it['status']}, {it['gaps']} gaps]")
        print("  student link :", it["links"].get("student"))
        print("  with answers :", it["links"].get("key"))
        print("  Studio       :", it["links"]["studio"])
    print(f"\nTeacher page: {BASE}rak/")
    print("Now run:  git add -A && git commit -m \"Add Kloz: <topic>\" && git push")
    print("Then open one student link on a phone before sending it (GitHub Pages takes about a minute).")


if __name__ == "__main__":
    main()
