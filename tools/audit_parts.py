"""Recalcule les parts de commerce (WITS) et de dette (IDS) depuis les données de la Banque mondiale et les compare au graphe.

    python tools/audit_parts.py
"""
import sys, re, json, subprocess, yaml, time, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
n = yaml.safe_load(open(ROOT / "network.yaml"))
geo = json.load(open(ROOT / "data" / "geo.json"))
iso3 = lambda k: (geo.get(k) or {}).get("iso3")
EU27 = "AUT BEL BGR HRV CYP CZE DNK EST FIN FRA DEU GRC HUN IRL ITA LVA LTU LUX MLT NLD POL PRT ROU SVK SVN ESP SWE".split()
URL = re.compile(r"https?://[^\s\"]+")
cache = {}
def get(u):
    if u not in cache:
        for _ in range(3):
            r = subprocess.run(["curl", "-sL", "--max-time", "60", u], capture_output=True).stdout.decode("utf-8", "replace")
            if len(r) > 300: break
            time.sleep(3)
        cache[u] = r
    return cache[u]
ok = bad = 0
for d in n["dependencies"]:
    us = [u for s in d["sources"] for u in URL.findall(str(s))]
    if d["type"] == "trade" and any("wits.worldbank.org" in u for u in us):
        x = get(next(u for u in us if "wits" in u))
        vals = {m.group(1): float(m.group(2)) for m in re.finditer(r'PARTNER="([A-Z0-9]+)"[^>]*>\s*<Obs[^>]*OBS_VALUE="([\d.]+)"', x)}
        sup = d["supplier"]; v = sum(vals.get(c, 0) for c in EU27) if sup == "EU" else vals.get(iso3(sup))
        good = v is not None and abs(round(v, 1) - d["share"]) <= 0.11
    elif d["type"] == "debt":
        try:
            vs = [json.loads(get(u))["source"]["data"][0]["value"] for u in us[:2]]; v = 100 * vs[0] / vs[1]; good = abs(round(v, 1) - d["share"]) <= 0.11
        except Exception as ex: v = f"ERR {ex}"; good = False
    else: continue
    ok += good; bad += not good
    if not good: print(f"✗ {d['from']}←{d['supplier']} {d['type']} {d.get('direction','')} : graphe {d['share']} / recalculé {v if isinstance(v,str) or v is None else round(v,2)}")
print(f"{ok} parts recalculées identiques, {bad} différentes")
