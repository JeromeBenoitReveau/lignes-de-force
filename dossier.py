"""Pages « dossier » (site/<id>.html) : un conflit expliqué à quelqu'un qui n'y connaît rien.
Le récit vient de dossiers.yaml ; les camps, leurs soutiens et le « pourquoi » de chaque soutien viennent de
network.yaml, pour qu'un dossier ne puisse pas contredire le graphe. Le site n'affiche aucune probabilité."""
from html import escape as e
from pathlib import Path
from urllib.parse import urlparse
import json, re, shutil
import yaml
import brand, glossary, network, style

PATH = Path(__file__).with_name("dossiers.yaml")
URL = re.compile(r"https?://\S+")
TYPES_FR = {"arms": "armes", "financial": "argent", "training": "entraînement", "troops": "troupes",
            "intelligence": "renseignement", "political": "soutien politique", "economic": "soutien économique",
            "dual_use": "matériel à double usage", "service": "service stratégique"}
MONTHS = ["janv.", "févr.", "mars", "avr.", "mai", "juin", "juill.", "août", "sept.", "oct.", "nov.", "déc."]


CSS = """
header.doc{padding:72px 0 28px;max-width:760px}.doc .meta{margin:0 0 26px}
.hero-map{margin:8px 0 0}#dmap{height:min(68vh,620px);border-radius:3px;background:var(--ocean)}
.legend-map{display:flex;flex-wrap:wrap;gap:4px 22px;font-size:14px;color:var(--graphite);margin:14px 0 6px}
.legend-map span{display:inline-flex;align-items:center;gap:7px}.legend-map i{width:12px;height:12px;border-radius:2px;opacity:.8}
.legend-map .ln{width:20px;border-top:2px solid}.legend-map .ln.dot{border-top-style:dotted}
.map-note{font-size:14px;color:var(--graphite);margin:0 0 4px;max-width:64em}
.flag{width:22px;height:22px;border-radius:50%;box-shadow:0 0 0 2px var(--land)}
.leaflet-container{font:inherit;background:var(--ocean)}
.leaflet-popup-content-wrapper{border-radius:3px;box-shadow:0 2px 10px #0002}.leaflet-popup-content{font-size:14px;line-height:1.5;max-width:280px}
.leaflet-tooltip.pin-label{background:transparent;border:0;box-shadow:none;font:500 13px var(--sans);color:var(--ink);
  text-shadow:0 0 3px var(--land),0 0 3px var(--land),0 0 3px var(--land)}.leaflet-tooltip.pin-label::before{display:none}
.camps{display:grid;grid-template-columns:1fr 1fr;gap:16px;align-items:start}
/* les personnes qui comptent : médiations, dirigeants (filet de la couleur de leur camp), autres personnes */
h3.sub{font:500 17px/1.3 var(--serif);margin:0 0 10px}.meds{display:grid;gap:10px;margin-bottom:26px}
.med{display:flex;gap:12px;align-items:flex-start}.med>img,.med>span{width:28px;height:28px;border-radius:50%;flex:none;margin-top:2px}
.med p{margin:4px 0 0;font-size:15.5px}.med .quiet{margin-left:6px}
.people{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:12px}
.person{display:flex;gap:12px;align-items:flex-start;padding:12px 14px;border:1px solid var(--mist);border-left:3px solid var(--c,var(--mist));border-radius:6px;background:var(--land)}
.person img,.person .nopic{width:44px;height:44px;border-radius:50%;object-fit:cover;flex:none;background:var(--mist)}
.person b{display:block;font-weight:600}.person .quiet{display:block;font-size:13.5px}.person p{margin:6px 0 0;font-size:14.5px;line-height:1.45}
.camp{border-top:3px solid var(--c);border-radius:4px 4px 6px 6px}
.camp .who{display:flex;gap:14px;align-items:center;margin-bottom:12px}
.camp .who img{width:52px;height:52px;border-radius:50%;object-fit:cover}
.camp h3{font-size:21px;margin:0}.camp .lead{color:var(--graphite);font-size:15px}
.camp > p{margin:0 0 20px;font-size:16px}
.lever{grid-column:2;font-size:14px;color:var(--graphite);margin-top:4px;padding-left:10px;border-left:2px solid #b08968}
.backers-title{font-size:15px;color:var(--graphite);margin:0 0 4px}
.backer{display:grid;grid-template-columns:22px 1fr;gap:4px 12px;padding:12px 0;border-top:1px solid var(--mist)}
.backer img{width:22px;height:22px;border-radius:50%;margin-top:2px}
.backer .name{font-weight:600}.backer .kind{color:var(--graphite);font-size:14px;margin-left:6px}.backer .to{display:block;margin-left:0}
.backer .why{grid-column:2;font-size:15.5px;line-height:1.55}
.backer details{grid-column:2;font-size:14px;color:var(--graphite)}.backer summary{cursor:pointer;width:max-content}
.backer details p{margin:6px 0 0}
.alleged{font-size:13px;color:var(--c);border:1px solid currentColor;border-radius:9px;padding:0 6px;margin-left:6px}
.frac .intro{margin:-8px 0 14px}.frac .card{padding:6px 24px}.frac .row{padding:14px 0;border-top:1px solid var(--mist)}.frac .row:first-child{border-top:0}
.frac .row p{margin:4px 0 0;color:var(--graphite);font-size:15px}
.stakes{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:16px}
.stake h3{font-size:19px;margin-bottom:6px}.stake p{margin:0;font-size:16px}
.block p{margin:0;max-width:44em}.block p + p{margin-top:12px}.pair{display:grid;grid-template-columns:1fr 1fr;gap:16px}.pair>div{display:flex;flex-direction:column}.pair .card{flex:1}
.tl{list-style:none;margin:18px 0 0;padding:16px 0 0;border-top:1px solid var(--mist)}
.tl li{display:grid;grid-template-columns:104px 1fr;gap:16px;padding:7px 0}
.tl time{white-space:nowrap;color:var(--graphite);font-variant-numeric:tabular-nums;font-size:15px}
@media (max-width:760px){header.doc{padding:44px 0 22px}.camps,.pair{grid-template-columns:1fr}.card{padding:18px}
  .tl li{grid-template-columns:88px 1fr;gap:10px}#dmap{height:62vh}}
"""

def load():
    return (yaml.safe_load(PATH.read_text(encoding="utf-8")) or {}).get("dossiers", [])

def registry():
    """Personnes citées dans les dossiers (clé people de dossiers.yaml) : {id: {name, wikidata | actor}}."""
    return (yaml.safe_load(PATH.read_text(encoding="utf-8")) or {}).get("people") or {}

def photo_key(pid, reg):
    """Clé de la photo dans data/people.json : l'acteur « person » du graphe, sinon « p:<id> »."""
    return reg[pid].get("actor") or f"p:{pid}"

def people_block(dos, d, g, cite):
    """« Les personnes qui comptent » : qui négocie (médiations entre les deux camps, lues dans network.yaml), puis
    les dirigeants des camps et les personnes du dossier. Une personne n'y figure que pour une action documentée."""
    sides = [set(s["actors"]) for s in dos["sides"]]
    both = sides[0] | sides[1]
    meds = [m for m in d.get("mediations", []) if m["status"] != "ended"
            and any(a in sides[0] for a in m["between"]) and any(a in sides[1] for a in m["between"])]
    name = lambda a: e(d["actors"][a]["name"])
    med_rows = "".join(f"""<div class="med">{flag(m["mediator"], d)}<div><b>{name(m["mediator"])}</b>
  <span class="quiet">{"mission de paix " if m.get("form") == "mission" else ""}entre {name(m["between"][0])} et {name(m["between"][1])}{f", depuis {e(fr_date(m['since']))}" if m.get("since") else ""}</span>
  <p>{glossed(m.get("why") or m.get("note", ""), g)}{cite(m["sources"])}</p>
  {f'<p class="quiet">{glossed(m["note"], g)}</p>' if m.get("why") and m.get("note") else ""}</div></div>""" for m in meds)
    cards, seen = [], set()
    def card(photo, who, role, text, side=None):
        pic = d["people"].get(photo)
        return f"""<div class="person"{f' style="--c:var(--{"ab"[side]})"' if side is not None else ""}>
  {f'<img src="{e(pic["thumb"])}" alt="">' if pic else '<span class="nopic"></span>'}<div><b>{e(who)}</b><span class="quiet">{e(role)}</span>
  {f"<p>{text}</p>" if text else ""}</div></div>"""
    for i, s in enumerate(dos["sides"]):
        for a in s["actors"]:
            ld = network.leader(d["actors"], a)
            if ld and ld["name"] not in seen:
                seen.add(ld["name"])
                role = ld.get("role") or f"Dirigeant : {d['actors'][a]['name']}"
                cards.append(card(ld["photo_key"], ld["name"], role, cite(ld["sources"]) if ld.get("sources") else "", i))
    reg = registry()
    for x in dos.get("people", []):
        r = reg[x["who"]]
        cards.append(card(photo_key(x["who"], reg), r["name"], x["role"], glossed(x["text"], g) + cite(x.get("sources"))))
    if not (med_rows or cards):
        return ""
    return f"""<section class="s"><h2>Les personnes qui comptent</h2>
{f'<h3 class="sub">Qui négocie</h3><div class="meds">{med_rows}</div>' if med_rows else ""}
<div class="people">{"".join(cards)}</div></section>"""

def fr_date(d):
    d = str(d)
    return f"{MONTHS[int(d[5:7]) - 1]} {d[:4]}" if len(d) >= 7 else d[:4]

def glossed(text, g):
    """Texte échappé, termes du glossaire du site expliqués (première occurrence dans la page) : voir glossary.py."""
    return g(text)

class Notes:
    """Sources → appels de note numérotés (dédoublonnés par URL), listés en bas de page."""
    def __init__(self):
        self.items, self.index = [], {}
    def __call__(self, srcs):
        marks = []
        for s in srcs or []:
            m = URL.search(s)
            key = m.group() if m else s
            if key not in self.index:
                self.items.append(s)
                self.index[key] = len(self.items)
            n = self.index[key]
            title = s[:m.start()].rstrip(" —") if m else s
            if not any(f'href="#n{n}"' in x for x in marks):
                marks.append(f'<a href="#n{n}" title="{e(title)}">{n}</a>')
        return f'<sup class="fns">{",".join(marks)}</sup>' if marks else ""
    def html(self):
        def item(i, s):
            m = URL.search(s)
            if not m:
                return f'<li id="n{i}">{e(s)}</li>'
            label = s[:m.start()].rstrip(" —")
            return f'<li id="n{i}">{e(label)}, <a href="{e(m.group())}" target="_blank" rel="noopener">{e(urlparse(m.group()).netloc.removeprefix("www."))}</a></li>'
        return "".join(item(i, s) for i, s in enumerate(self.items, 1))

def flag(aid, d):
    kind = d["actors"][aid]["kind"]
    ok = kind == "state" or aid == "EU"
    return f'<img src="{e(style.flag_url(aid, d["actors"][aid]))}" alt="">' if ok else '<span></span>'

def backers_block(bs, d, g, cite, multi=False):
    """Une ligne par soutien ; ceux qui partagent le même « pourquoi » sont regroupés sur une ligne."""
    groups = {}
    for x in bs:
        groups.setdefault(x.get("why") or x["from"], []).append(x)
    rows = []
    for why, xs in groups.items():
        names = list(dict.fromkeys(e(d["actors"][x["from"]]["name"]) for x in xs))   # un pays qui soutient deux acteurs d'un camp : cité une fois
        kinds = sorted({TYPES_FR.get(t, t) for x in xs for t in x["types"]})
        to = list(dict.fromkeys(d["actors"][x["to"]]["name"] for x in xs)) if multi else []   # camp à plusieurs acteurs : dire lequel est soutenu
        alleged = any(x["status"] == "alleged" for x in xs)
        notes = [x for x in xs if x.get("note")]
        srcs = [s for x in xs for s in x["sources"]]
        rows.append(f"""<div class="backer">{flag(xs[0]["from"], d) if len(xs) == 1 else flag("EU", d) if any(x["from"] == "EU" for x in xs) else flag(xs[0]["from"], d)}
  <div><span class="name">{", ".join(names)}</span><span class="kind">{e(", ".join(kinds))}</span>{f'<span class="kind to">{"bénéficiaires" if len(to) > 1 else "bénéficiaire"} : {e(", ".join(to))}</span>' if to else ""}{'<span class="alleged">allégué</span>' if alleged else ""}</div>
  <div class="why">{glossed(xs[0]["why"], g) if xs[0].get("why") else '<span style="color:var(--graphite)">Motivation pas encore documentée.</span>'}{cite(srcs)}</div>
  {"".join(f'<div class="lever">{style.dep_icon(dp["type"])} {e(d["actors"][dp["from"]]["name"])} : <b>{dp["share"]} %</b> de ses armes importées viennent de ce fournisseur ({e(d["actors"][dp["supplier"]]["name"])}, {e(dp.get("period") or str(dp["year"]))}){cite(dp["sources"])}{(" " + e(dp["note"]) + ".") if dp.get("note") else ""}</div>'
           for dp in d.get("dependencies", []) for x in xs
           if dp["type"] == "arms" and dp["supplier"] == x["from"] and dp["from"] == x["to"] and dp.get("status", "active") != "ended")}
  {f'<details><summary>Détails</summary>{"".join(f"<p>{glossed(x['note'], g)}</p>" for x in notes)}</details>' if notes else ""}</div>""")
    return "".join(rows)

def fractures(dos, d, g, cite):
    """Tensions (network.yaml) qui touchent un camp, hors la guerre entre les deux camps : sanctions, autres fronts…"""
    sides = [set(s["actors"]) for s in dos["sides"]]
    main = lambda t: t["type"] == "war" and any(t["from"] in a and t["to"] in b for a in sides for b in sides if a is not b)
    ts = [t for t in d.get("tensions", []) if t["status"] != "ended" and not main(t)
          and ({t["from"], t["to"]} & set().union(*sides))]
    if not ts:
        return ""
    name = lambda a: e(d["actors"][a]["name"])
    label = {"war": "Guerre", "sanctions": "Sanctions", "claims": "Revendication territoriale", "rivalry": "Rivalité", "trade_war": "Guerre commerciale", "blockade": "Entrave à la navigation"}
    link = lambda t: f"{name(t['from'])} {'→' if t['type'] in ('sanctions', 'claims') else 'et'} {name(t['to'])}"
    when = lambda t: ", ".join(x for x in (f"depuis {fr_date(t['since'])}" if t.get("since") else "",
                                            "trêve ou cessez-le-feu" if t["status"] == "reduced" else "") if x)
    rows = "".join(f"""<div class="row"><div><b>{label[t["type"]]}</b> {link(t)}{f'<span class="quiet">, {e(when(t))}</span>' if when(t) else ""}</div>
  {f'<p>{glossed(t["note"], g)}{cite(t["sources"])}</p>' if t.get("note") else cite(t["sources"])}</div>""" for t in ts)
    return f"""<h2>Les autres lignes de fracture</h2>
<p class="quiet intro">Guerres, sanctions, revendications, rivalités et guerres commerciales qui touchent aussi les deux camps.</p><div class="card">{rows}</div>"""

SIDE_COLORS = ["#2a78d6", "#eb6834"]   # camp 1, camp 2 (palette catégorielle du site)
CONTESTED = "#9ca3af"
MAPS = Path(__file__).with_name("data") / "maps"

def side_countries(ids, d):
    """Pays d'un camp : l'État lui-même, le pays d'ancrage d'un groupe ou d'une personne, les membres d'un bloc
    (groupe d'alignments.yaml rattaché au bloc, le plus haut niveau)."""
    out = set()
    for i in ids:
        a = d["actors"].get(i, {})
        if a.get("kind") == "state":
            out.add(i)
        elif a.get("kind") == "bloc":
            gs = [g for g in d["align"]["groups"] if g.get("entity") == i]
            if gs:
                out |= set(max(gs, key=lambda g: g.get("level") or 0)["members"])
        elif a.get("base"):
            out.add(a["base"])
    return out

def hero_map(dos, d, backers, cite):
    """Carte d'ouverture : zones de contrôle par région, soutiens étrangers en flèches vers chaque camp, lieux clés,
    routes d'approvisionnement et flux. Tout est sourcé ; les textes sont insérés côté navigateur sans HTML."""
    m = dos.get("map")
    if not m:
        return ""
    geo = d["geo"]
    (s_lat, w_lon), (n_lat, e_lon) = m["bounds"]
    # marges et décalages proportionnels au cadre (1,5° sur une grande carte, bien moins sur Gaza)
    in_lat, in_lon = min(1.5, (n_lat - s_lat)*.08), min(1.5, (e_lon - w_lon)*.06)
    def place(aid):
        """Position d'un soutien : son pays (Wikidata) ou les coords d'un bloc ; ramenée au bord du cadre si elle en sort,
        pour garder la région du conflit lisible (le nom le signale alors « hors carte »)."""
        g = geo.get(aid) or {}
        lat, lon = (g.get("lat"), g.get("lon")) if g.get("lat") else (d["actors"][aid].get("coords") or [None, None])
        if lat is None:
            return None, False
        c = [min(max(lat, s_lat + in_lat), n_lat - in_lat), min(max(lon, w_lon + in_lon), e_lon - in_lon)]
        return c, c != [lat, lon]
    arrows, taken = [], []
    for side, bs in enumerate(backers):
        seen = set()
        for x in bs:
            if x["from"] in seen:   # un même pays qui soutient deux acteurs d'un camp : une seule flèche
                continue
            seen.add(x["from"])
            at, off = place(x["from"])
            if not at:
                continue
            # deux drapeaux ramenés au même endroit du bord : on décale le second le long du bord
            while off and any(abs(at[0] - t[0]) < in_lat*1.3 and abs(at[1] - t[1]) < in_lon*2 for t in taken):
                at = ([at[0], at[1] - in_lon*2.3] if at[0] <= s_lat + in_lat*1.1 or at[0] >= n_lat - in_lat*1.1
                      else [at[0] - in_lat*1.7, at[1]])
            taken.append(at)
            flag = x["from"].lower() if d["actors"][x["from"]]["kind"] == "state" else ("eu" if x["from"] == "EU" else "")
            arrows.append({"side": side, "at": at, "iso": flag,
                           "name": d["actors"][x["from"]]["name"] + (" (hors carte)" if off else ""), "alleged": x["status"] == "alleged",
                           "types": ", ".join(TYPES_FR.get(t, t) for t in x["types"]), "why": x.get("why", ""),
                           "source": x["sources"]})
    flows = [{**f, "to": [geo[f["to_actor"]]["lat"], geo[f["to_actor"]]["lon"]]} for f in m.get("flows", [])
             if geo.get(f.get("to_actor"), {}).get("lat")]
    # sans zones de contrôle régionales : les pays de chaque camp sont colorés (codes numériques ISO de Natural Earth)
    num = lambda isos: sorted(str(int(geo[i]["iso_numeric"])) for i in isos if geo.get(i, {}).get("iso_numeric"))
    # (map.countries : liste explicite par camp, quand le pays entier ne correspond pas au camp — Gaza n'est pas la Cisjordanie)
    camps = [] if m.get("regions") else [num(m["countries"][i] if "countries" in m else side_countries(sd["actors"], d))
                                          for i, sd in enumerate(dos["sides"])]
    payload = {"bounds": m["bounds"], "regions": m.get("regions"), "anchors": m["anchors"], "camps": camps,
               "sides": [s["name"] for s in dos["sides"]], "sides_mid": [style.mid(s["name"]) for s in dos["sides"]], "colors": SIDE_COLORS, "contested": CONTESTED,
               "arrows": arrows, "pins": m.get("pins", []), "routes": m.get("routes", []), "flows": flows}
    data = json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")
    reg = m.get("regions") or {}
    names = [e(s["name"]) for s in dos["sides"]]
    return f"""<section class="hero-map"><div id="dmap" role="img" aria-label="Carte du conflit : zones de contrôle, soutiens étrangers et lieux clés"></div>
<div class="legend-map">
  <span><i style="background:{SIDE_COLORS[0]}"></i>{names[0]}</span><span><i style="background:{SIDE_COLORS[1]}"></i>{names[1]}</span>
  {f'<span><i style="background:{CONTESTED}"></i>{e(reg.get("contested_label", "Disputé / ligne de front"))}</span>' if reg.get("contested") else ""}
  <span><b class="ln" style="border-color:{SIDE_COLORS[0]}"></b>Soutien étranger (pointillé : allégué)</span>
  {f'<span><b class="ln dot" style="border-color:{SIDE_COLORS[1]}"></b>Route d\'approvisionnement</span>' if m.get("routes") else ""}
  {'<span><b class="ln" style="border-color:#b7791f"></b>Flux (or)</span>' if m.get("flows") else ""}
</div>
<p class="map-note">Cliquez sur un élément pour son explication et ses sources. {glossed(reg.get("note", ""), glossary.Glosser())}{cite(reg.get("sources"))}</p>
<p class="map-note">Fond de carte Natural Earth{" ; " + e(reg["credit"]) if reg.get("credit") else ""} ; lieux : Wikidata.</p>
</section>
<script src="https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/leaflet.js"></script>
<script src="https://cdn.jsdelivr.net/npm/topojson-client@3/dist/topojson-client.min.js"></script>
<script>
(async () => {{
const M = {data};
window.THEME_RELOAD = true;  // couleurs de la carte lues au chargement
const css = v => getComputedStyle(document.documentElement).getPropertyValue(v).trim();
const map = L.map("dmap", {{zoomSnap:.25, scrollWheelZoom:false, attributionControl:false}});
map.fitBounds(M.bounds);
// fenêtre explicative : texte + lien vers la source, construits sans HTML venant des données
const pop = (title, text, source) => {{ const div = document.createElement("div"), b = document.createElement("b");
  b.textContent = title; div.append(b);
  if(text){{ const p = document.createElement("p"); p.style.margin = "4px 0"; p.textContent = text; div.append(p); }}
  const urls = [].concat(source || []).map(x => (x.match(/https?:\\/\\/\\S+/) || [])[0]).filter(Boolean);
  if(urls.length){{ const p = document.createElement("div"); p.textContent = urls.length > 1 ? "Sources : " : "Source : ";
    urls.forEach((u, i) => {{ const a = document.createElement("a"); a.href = u; a.target = "_blank"; a.rel = "noopener";
      a.textContent = new URL(u).hostname.replace(/^www\\./, ""); p.append(a); if(i < urls.length - 1) p.append(", "); }});
    div.append(p); }}
  return div; }};
const world = await fetch("https://cdn.jsdelivr.net/npm/world-atlas@2/countries-50m.json").then(r => r.json());
L.geoJSON(topojson.feature(world, world.objects.countries), {{interactive:false,
  style: {{color: css("--line"), weight:.8, fillColor: css("--land"), fillOpacity:1}}}}).addTo(map);
// pas de zones de contrôle : chaque pays d'un camp prend sa couleur (dans les deux camps : couleur « disputé »)
if(M.camps.length){{ const inC = (k, id) => M.camps[k].includes(String(+id));
  L.geoJSON(topojson.feature(world, world.objects.countries), {{filter: f => inC(0, f.id) || inC(1, f.id),
    style: f => ({{color: css("--card"), weight:1, fillOpacity:.5, fillColor: inC(0, f.id) && inC(1, f.id) ? M.contested : M.colors[inC(0, f.id) ? 0 : 1]}}),
    onEachFeature: (f, l) => l.bindTooltip(inC(0, f.id) && inC(1, f.id) ? "dans les deux camps" : "camp : " + M.sides_mid[inC(0, f.id) ? 0 : 1], {{sticky:true}})
  }}).addTo(map); }}
if(M.regions){{
  const control = n => M.regions.sides[0].includes(n) ? 0 : M.regions.sides[1].includes(n) ? 1 : M.regions.contested.includes(n) ? 2 : -1;
  const reg = await fetch("maps/" + M.regions.file + ".geojson").then(r => r.json());
  L.geoJSON(reg, {{style: f => {{ const c = control(f.properties.name);
      return {{color: css("--card"), weight:1, fillOpacity: c < 0 ? 0 : .55, fillColor: c === 2 ? M.contested : M.colors[c] || "transparent"}}; }},
    onEachFeature: (f, l) => {{ const c = control(f.properties.name);
      if(c >= 0) l.bindTooltip(f.properties.name + " — " + (c === 2 ? (M.regions.contested_label || "disputé").toLowerCase() : "tenu par " + M.sides_mid[c]), {{sticky:true}}); }}
  }}).addTo(map); }}
const curve = (a, b, k = .2) => {{ const mx = (a[0]+b[0])/2, my = (a[1]+b[1])/2, dx = b[0]-a[0], dy = b[1]-a[1], c = [mx - dy*k, my + dx*k];
  return Array.from({{length:30}}, (_, i) => {{ const t = i/29, u = 1-t; return [u*u*a[0]+2*u*t*c[0]+t*t*b[0], u*u*a[1]+2*u*t*c[1]+t*t*b[1]]; }}); }};
const head = (a, b, color) => L.circleMarker(b, {{radius:4, color, fillColor:color, fillOpacity:1, weight:0, interactive:false}}).addTo(map);
for(const f of M.flows){{
  L.polyline(curve(f.from, f.to, -.15), {{color:"#b7791f", weight:3, dashArray:"1 7", lineCap:"round"}}).bindPopup(pop(f.label, f.text, f.source)).addTo(map);
  head(f.from, f.to, "#b7791f"); }}
for(const r of M.routes){{
  const to = M.anchors[r.to];
  L.polyline(curve(r.from, to, .1), {{color:M.colors[r.to], weight:2, dashArray:"2 5"}}).bindPopup(pop(r.label, r.text, r.source)).addTo(map); }}
for(const a of M.arrows){{
  const to = M.anchors[a.side], color = M.colors[a.side];
  L.polyline(curve(a.at, to), {{color, weight: a.alleged ? 2 : 3, opacity:.9, dashArray: a.alleged ? "6 6" : null}})
    .bindPopup(pop(a.name + " → " + M.sides[a.side] + (a.alleged ? " (allégué)" : ""), a.types + (a.why ? " — Pourquoi ? " + a.why : ""), a.source)).addTo(map);
  head(a.at, to, color);
  L.marker(a.at, {{icon: L.divIcon({{className:"", iconSize:[26,26], iconAnchor:[13,13],
    html:'<img src="https://cdn.jsdelivr.net/npm/flag-icons@7.2.3/flags/1x1/' + a.iso + '.svg" alt="" class="flag">'}})}})
    .bindTooltip(a.name, {{direction:"top", offset:[0,-12]}}).bindPopup(pop(a.name + " → " + M.sides[a.side], a.types + (a.why ? " — Pourquoi ? " + a.why : ""), a.source)).addTo(map)
    .getElement().setAttribute("aria-label", a.name + ", soutien de : " + M.sides[a.side]); }}
for(const p of M.pins){{
  L.circleMarker(p.at, {{radius:5, color:css("--fg"), weight:2, fillColor:css("--card"), fillOpacity:1}})
    .bindTooltip(p.label, {{permanent:true, direction: p.dir || "right", offset:[p.dir === "left" ? -6 : 6, 0], className:"pin-label"}})
    .bindPopup(pop(p.label, p.text, p.source)).addTo(map); }}
}})();
</script>"""

def page(dos, d):
    g, cite = glossary.Glosser(), Notes()
    sides = [set(s["actors"]) for s in dos["sides"]]
    backers = [[x for x in d["edges"] if x["to"] in ids and x["from"] not in ids and x["status"] != "ended"] for ids in sides]
    for bs in backers:
        bs.sort(key=lambda x: ({"high": 0, "medium": 1, "low": 2}[x["confidence"]], d["actors"][x["from"]]["name"]))

    def camp(i, s, bs):
        lead = next((ld for a in s["actors"] if (ld := network.leader(d["actors"], a))), None)
        pic = d["people"].get(lead["photo_key"]) if lead else None
        return f"""<div class="card camp" style="--c:var(--{'ab'[i]})">
  <div class="who">{f'<img src="{e(pic["thumb"])}" alt="">' if pic else ""}<div><h3>{glossed(s["name"], g)}</h3>
  {f'<div class="lead">{e(lead["name"])}</div>' if lead else ""}</div></div>
  <p>{glossed(s["text"], g)}{cite(s.get("sources"))}</p>
  <p class="backers-title">{(n := len({x["from"] for x in bs}))} soutien{"s" if n > 1 else ""} étranger{"s" if n > 1 else ""}</p>
  {backers_block(bs, d, g, cite, len(s["actors"]) > 1) or '<p style="color:var(--graphite)">Aucun soutien documenté.</p>'}</div>"""

    events = [(str(t["date"]), glossed(t["text"], g) + cite([t["source"]])) for t in dos.get("timeline", [])]
    council = sorted(((str(t["date"]), glossed(t["text"], g) + cite([t["source"]])) for t in dos.get("council", [])), key=lambda ev: ev[0])
    events.sort(key=lambda ev: ev[0])

    frac = fractures(dos, d, g, cite)
    ppl = people_block(dos, d, g, cite)
    reg = registry()
    keys = [ld["photo_key"] for s in dos["sides"] for a in s["actors"] if (ld := network.leader(d["actors"], a))]
    keys += [photo_key(x["who"], reg) for x in dos.get("people", [])]
    credits = [d["people"][k] for k in dict.fromkeys(keys) if k in d["people"]]

    body = f"""<div class="wrap">
{style.top(f"{dos['id']}.html")}

<header class="doc"><h1>{e(dos["title"])}</h1>
<p class="meta">Depuis {e(fr_date(dos["since"]))}. Dossier vérifié en {e(fr_date(dos["verified"]))}. Les mots soulignés en pointillés ont une définition au survol.</p>
<p class="lede">{glossed(dos["lede"], g)}{cite(dos.get("lede_sources"))}</p></header>

{hero_map(dos, d, backers, cite)}

<section class="s"><h2>Qui s'affronte, et qui les soutient</h2>
<div class="camps">{camp(0, dos["sides"][0], backers[0])}{camp(1, dos["sides"][1], backers[1])}</div>
<p class="quiet" style="margin:16px 0 0"><a href="relations.html?e=d:{e(dos["id"])}">Croiser ce conflit avec d'autres acteurs</a> : schéma, carte et points communs.</p></section>

{ppl}

{f'<section class="s frac">{frac}</section>' if frac else ""}

<section class="s"><h2>Ce qui est en jeu</h2><div class="stakes">{"".join(
  f'<div class="card stake"><h3>{e(s["label"])}</h3><p>{glossed(s["text"], g)}{cite(s.get("sources"))}</p></div>' for s in dos.get("stakes", []))}</div></section>

<section class="s pair">
<div><h2>Le coût humain</h2><div class="card block"><p>{glossed(dos["toll"]["text"], g)}{cite(dos["toll"].get("sources"))}</p></div></div>
<div><h2>Où en est-on</h2><div class="card block"><p>{glossed(dos["now"]["text"], g)}{cite(dos["now"].get("sources"))}</p></div></div>
</section>

{f'<section class="s"><h2>Au Conseil de sécurité de l’ONU</h2><div class="card block"><p class="quiet" style="margin:0 0 8px">Les cinq membres permanents (États-Unis, Russie, Chine, France, Royaume-Uni) peuvent chacun bloquer une décision : c’est le veto.</p><ol class="tl">{"".join(f"<li><time>{e(fr_date(dt))}</time><span>{txt}</span></li>" for dt, txt in council)}</ol></div></section>' if council else ""}

<section class="s"><h2>Comment on en est arrivé là</h2>
<div class="card block"><p>{glossed(dos["origins"]["text"], g)}{cite(dos["origins"].get("sources"))}</p>
<ol class="tl">{"".join(f"<li><time>{e(fr_date(dt))}</time><span>{txt}</span></li>" for dt, txt in events)}</ol></div></section>

{f'<section class="s"><h2>Ce que l’histoire éclaire, et ses limites</h2><div class="card block"><p>{glossed(dos["history"]["text"], g)}{cite(dos["history"].get("sources"))}</p></div></section>' if dos.get("history") else ""}

<section class="notes"><h2>Sources</h2><ol>{cite.html()}</ol>
<p class="fix">Une erreur, une source manquante, une information dépassée ? {style.correction(dos["title"])}</p></section>
</div>
{style.foot(f'Photos {"; ".join(f"""<a href="{e(c['page'])}">{e(c['artist'] or 'auteur inconnu')}</a>, {e(c['license'])}""" for c in credits)}, via Wikimedia Commons. ' if credits else "", dos["title"], fix=False)}"""
    extra = f'<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/leaflet.css"><style>{CSS}</style>'
    desc = style.clip(dos["lede"])
    ld = {"@context": "https://schema.org", "@type": "Article", "headline": dos["title"], "description": desc, "inLanguage": "fr",
          "dateModified": f"{dos['verified']}-01" if len(str(dos["verified"])) == 7 else str(dos["verified"]),
          "isAccessibleForFree": True, "license": "https://creativecommons.org/licenses/by/4.0/",
          "author": {"@type": "Organization", "name": brand.NAME, "url": brand.SITE},
          "publisher": {"@type": "Organization", "name": brand.NAME, "url": brand.SITE},
          "mainEntityOfPage": f"{brand.SITE}{dos['id']}.html"}
    # titre de l'onglet : on ajoute la promesse du dossier tant que l'ensemble reste court (les moteurs coupent vers 60 caractères)
    tail = " : qui s'affronte, qui soutient qui" if len(dos["title"]) <= 24 else ""
    return style.head(f"{dos['title']}{tail} — {brand.NAME}", desc, extra, path=f"{dos['id']}.html", kind="article", ld=ld,
                      image=f"partage-{dos['id']}.png" if (Path("assets") / f"partage-{dos['id']}.png").exists() else "partage.png") + f"<body>{body}</body></html>"

def write(out, data):
    dossiers = load()
    if MAPS.exists():  # contours régionaux utilisés par les cartes des dossiers
        (out / "maps").mkdir(exist_ok=True)
        for f in MAPS.glob("*.geojson"):
            shutil.copy(f, out / "maps" / f.name)
    for dos in dossiers:
        (out / f"{dos['id']}.html").write_text(page(dos, data), encoding="utf-8")
    return dossiers
