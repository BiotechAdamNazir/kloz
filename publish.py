"""Build hosted BM worksheets: w/<id>.json, opened at https://biotechadamnazir.github.io/kloz/#w=<id>

    python3 publish.py           rebuild every worksheet in worksheets.json from essays/*.json
    python3 publish.py studio    also write studio/kloz-studio.html (Studio page with all essays)

Fix an essay in essays/, run this, commit and push: every link already sent shows the fix
(after GitHub Pages republishes, about a minute). Needs Playwright with Chromium.
"""
import asyncio, glob, hashlib, json, os, sys
from playwright.async_api import async_playwright

ROOT = os.path.dirname(os.path.abspath(__file__))
BASE = "https://biotechadamnazir.github.io/kloz/"

def studio_html():
    data = json.load(open(f"{ROOT}/studio/base-data.json", encoding="utf-8"))
    data["essays"] = [json.load(open(p, encoding="utf-8")) for p in sorted(glob.glob(f"{ROOT}/essays/*.json"))]
    for e in data["essays"]:
        idx = sorted(x for p in e["paras"] for x in p if isinstance(x, int))
        assert idx == list(range(len(e["units"]))), f"{e['id']}: every unit must be used exactly once"
        for l in e.get("lens", []):
            assert 0 <= l["a"] <= l["b"] < len(e["units"]), f"{e['id']}: lens out of range {l}"
        missing = {u["k"] for u in e["units"]} - set(data["labels"])
        assert not missing, f"{e['id']}: add labels for {missing} in studio/base-data.json"
    js = json.dumps(data, ensure_ascii=False).replace("<", "\\u003c")
    page = open(f"{ROOT}/studio/studio.html", encoding="utf-8").read().replace("__KLOZ_DATA__", js)
    return data, page

async def main():
    data, page = studio_html()
    if "studio" in sys.argv:
        open(f"{ROOT}/studio/kloz-studio.html", "w", encoding="utf-8").write(page)
    order = [e["id"] for e in data["essays"]]
    sheets = json.load(open(f"{ROOT}/worksheets.json", encoding="utf-8"))["worksheets"]
    os.makedirs(f"{ROOT}/w", exist_ok=True)
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page()
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        await pg.route("**/*", lambda r: r.abort() if r.request.url.startswith("http") else r.continue_())
        await pg.set_content("<!doctype html><html><head><meta charset=utf-8></head><body>" + page + "</body></html>")
        await pg.wait_for_timeout(300)
        assert not errs, errs
        for w in sheets:
            ei = order.index(w["essay"])
            d = await pg.evaluate("""([ei,w])=>{
                document.querySelectorAll('#essays .essay-btn')[ei].click();
                const S=window.__kloz.S;
                S.pref=new Set(w.pref||[]); S.lens=new Set(w.lens||[]); S.count=w.count||20; S.seed=w.seed||1;
                S.fin=new Set(w.fin||[]); S.fout=new Set(w.fout||[]); S.wb=w.wb!==false; S.lab=!!w.lab;
                if(w.decoys!==undefined) S.decoys=w.decoys.join(", ");
                window.__kloz.update();
                return window.__kloz.student(w.mode||"check");
            }""", [ei, w])
            assert d["A"], f"{w['id']}: no gaps"
            # rev changes only when the gaps or answers change, so a text fix keeps students' saved work
            d["rev"] = hashlib.sha1(json.dumps([d["A"], d["B"]], ensure_ascii=False).encode()).hexdigest()[:10]
            body = json.dumps(d, ensure_ascii=False, sort_keys=True)
            path = f"{ROOT}/w/{w['id']}.json"
            old = json.load(open(path, encoding="utf-8")) if os.path.exists(path) else None
            json.dump(d, open(path, "w", encoding="utf-8"), ensure_ascii=False)
            note = "new" if not old else ("unchanged" if json.dumps(old, ensure_ascii=False, sort_keys=True) == body else "UPDATED")
            print(f"{w['id']}: {len(d['A'])} gaps, {note}  ->  {BASE}#w={w['id']}")
            if old and old.get("rev") != d["rev"]:
                oa, na = [a[0] for a in old["A"]], [a[0] for a in d["A"]]
                if oa != na:
                    print("   answers changed:", [f"{i+1}: {x} -> {y}" for i, (x, y) in enumerate(zip(oa, na)) if x != y] or f"{len(oa)} -> {len(na)} gaps")
                    print("   students who saved answers on this sheet will start fresh")
        await b.close()

asyncio.run(main())
