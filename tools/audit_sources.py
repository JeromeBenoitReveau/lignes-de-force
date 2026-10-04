"""Contrôle des sources : chaque chiffre d'un fait (note, pourquoi, texte) doit se retrouver dans au moins une de ses pages.

    python tools/audit_sources.py fetch   # télécharge les pages citées dans .audit-cache/ (une fois)
    python tools/audit_sources.py         # liste les faits dont un chiffre est absent de ses sources
    python tools/audit_sources.py dossier # seulement les dossiers (filtre sur la catégorie)

Ne vérifie que les chiffres et les dates, pas les noms ni les liens de cause. Beaucoup de signalements sont de faux positifs
(numéro de mois d'un « since », conversion de milles en kilomètres, nombre écrit en lettres) : chaque cas se relit à la main.
Sites qui refusent la lecture directe : France 24, Euronews, USDA, canada.ca, press.un.org, kmu.gov.ua."""
import sys, re, html, json, hashlib, subprocess, pathlib, concurrent.futures as cf
ROOT = pathlib.Path(__file__).resolve().parent.parent; sys.path.insert(0, str(ROOT))
import yaml
CACHE = ROOT / ".audit-cache"; CACHE.mkdir(exist_ok=True)
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36"
URL = re.compile(r"https?://\S+")
def key(u): return hashlib.md5(u.encode()).hexdigest()
def fetch(u):
    f = CACHE / key(u)
    if f.exists(): return
    r = subprocess.run(["curl", "-sL", "--compressed", "--max-time", "45", "-A", UA, "-H", "Accept: text/html,application/xhtml+xml,application/pdf,*/*", "-o", str(f) + ".raw", "-w", "%{http_code} %{content_type}", u], capture_output=True)
    meta = r.stdout.decode().strip(); raw = pathlib.Path(str(f) + ".raw"); txt = ""
    try:
        b = raw.read_bytes()
        if b[:4] == b"%PDF":
            import pypdf, io, logging; logging.disable(logging.CRITICAL)
            txt = " ".join((p.extract_text() or "") for p in pypdf.PdfReader(io.BytesIO(b)).pages)
        else:
            t = b.decode("utf-8", "replace"); t = re.sub(r"<script.*?</script>|<style.*?</style>", " ", t, flags=re.S); txt = html.unescape(re.sub(r"<[^>]+>", " ", t))
    except Exception as ex: meta += f" ERR {ex}"
    f.write_text(meta + "\n" + re.sub(r"\s+", " ", txt), encoding="utf-8"); raw.unlink(missing_ok=True)
def page(u):
    f = CACHE / key(u)
    if not f.exists(): return "000", ""
    meta, _, txt = f.read_text(encoding="utf-8").partition("\n"); return meta.split(" ")[0], txt
WORDS = {1:"one",2:"two",3:"three",4:"four",5:"five",6:"six",7:"seven",8:"eight",9:"nine",10:"ten",11:"eleven",12:"twelve",13:"thirteen",14:"fourteen",15:"fifteen",20:"twenty",30:"thirty",40:"forty",50:"fifty"}
def numbers(text):
    """Chiffres du texte français, chacun avec ses écritures possibles dans une source en anglais."""
    out = []
    for m in re.finditer(r"\d[\d   ]*\d(?:,\d+)?|\d(?:,\d+)?", text):
        tok = m.group().strip(); n = re.sub(r"[   ]", "", tok)
        if "," in n: whole, dec = n.split(","); forms = {f"{whole}.{dec}", f"{whole},{dec}"}
        else:
            forms = {n}
            if len(n) > 3: forms |= {f"{int(n):,}", f"{int(n):,}".replace(",", " "), f"{int(n):,}".replace(",", ".")}
            if int(n) in WORDS: forms.add(WORDS[int(n)])
        out.append((tok, forms))
    return out
def facts():
    n = yaml.safe_load((ROOT / "network.yaml").read_text()); d = yaml.safe_load((ROOT / "dossiers.yaml").read_text())
    F = []
    for k, a in n["actors"].items():
        t = " ".join(str(x) for x in [a.get("note"), (a.get("leader") or {}).get("role") if isinstance(a.get("leader"), dict) else ""] if x)
        src = list(a.get("sources") or []) + (list((a.get("leader") or {}).get("sources") or []) if isinstance(a.get("leader"), dict) else [])
        if t and src: F.append(("acteur", k, t, src))
    for e in n["edges"]: F.append(("soutien", f"{e['from']}→{e['to']}", " ".join(str(x) for x in [e.get("since"), e.get("note"), e.get("why")] if x), e.get("sources") or []))
    for e in n["tensions"]: F.append(("tension", f"{e['from']}–{e['to']} {e['type']}", " ".join(str(x) for x in [e.get("since"), e.get("note")] if x), e.get("sources") or []))
    for e in n.get("mediations") or []: F.append(("médiation", f"{e['mediator']} entre {e['between']}", " ".join(str(x) for x in [e.get("since"), e.get("note"), e.get("why")] if x), e.get("sources") or []))
    for e in n["dependencies"]: F.append(("dépendance", f"{e['from']}←{e['supplier']} {e['type']} {e.get('resource') or e.get('direction') or ''}", " ".join(str(x) for x in [str(e["share"]).replace(".", ","), e.get("note")] if x), e.get("sources") or []))
    for x in d["dossiers"]:
        i = x["id"]
        F.append((f"dossier {i}", "chapeau", x["lede"], x.get("lede_sources") or []))
        for sec in ("origins", "toll", "now", "history"):
            if x.get(sec): F.append((f"dossier {i}", sec, x[sec]["text"], x[sec].get("sources") or []))
        for s in x["sides"]: F.append((f"dossier {i}", "camp " + s["name"], s["text"], s.get("sources") or []))
        for s in x.get("stakes") or []: F.append((f"dossier {i}", "enjeu " + s["label"], s["text"], s.get("sources") or []))
        for s in (x.get("timeline") or []) + (x.get("council") or []): F.append((f"dossier {i}", "date " + str(s["date"]), str(s["date"])[:4] + " " + s["text"], [s["source"]]))
        for s in x.get("people") or []: F.append((f"dossier {i}", "personne " + s["who"], s["text"], s.get("sources") or []))
        for s in (x.get("map") or {}).get("pins") or []: F.append((f"dossier {i}", "lieu " + s["label"], s["text"], [s["source"]]))
    return F
if __name__ == "__main__":
    F = facts(); urls = sorted({m.group().rstrip('",)') for _, _, _, src in F for s in src for m in URL.finditer(str(s))})
    if sys.argv[1:] == ["fetch"]:
        with cf.ThreadPoolExecutor(10) as ex: list(ex.map(fetch, urls))
        codes = {}
        for u in urls: c, t = page(u); codes.setdefault((c, len(t) > 1500), []).append(u)
        for k, us in sorted(codes.items()): print(k, len(us))
        print("total", len(urls)); sys.exit()
    want = sys.argv[1] if len(sys.argv) > 1 else ""
    bad = unread = ok = 0
    for kind, name, text, src in F:
        if want and want not in kind: continue
        us = [m.group().rstrip('",)') for s in src for m in URL.finditer(str(s))]
        pages = [page(u) for u in us]; readable = [t for c, t in pages if c == "200" and len(t) > 1500]
        nums = numbers(text)
        if not readable: unread += 1; print(f"⛔ {kind} | {name} : aucune source lisible ({', '.join(c for c, _ in pages)})"); continue
        blob = " ".join(readable)
        miss = [tok for tok, forms in nums if not any(re.search(r"(?<![\d.,])" + re.escape(f) + r"(?![\d])", blob, re.I) for f in forms)]
        if miss: bad += 1; print(f"❓ {kind} | {name} : absents des sources lues → {', '.join(dict.fromkeys(miss))}   [{len(readable)}/{len(us)} sources lues]")
        else: ok += 1
    print(f"\n{ok} faits dont tous les chiffres sont retrouvés, {bad} à regarder, {unread} sans source lisible")
