"""python build.py → site/ : accueil, dossiers, explorateur (graphe, carte, organisations), méthode, manifeste,
et le graphe en données ouvertes (network.json, network.csv — CC BY 4.0). Publiable tel quel."""
from dotenv import load_dotenv; load_dotenv()
import csv, json, shutil
from pathlib import Path
import brand, cross, db, dossier, glossary, method, network, pages, presets, style

OUT = Path("site")
DATA_LICENSE = "CC BY 4.0 — https://creativecommons.org/licenses/by/4.0/ — Lignes de force, network.yaml"
TYPE_COLORS = {"arms": "#d64545", "troops": "#8b1e1e", "financial": "#2f8f5b", "training": "#c98a1b",
               "intelligence": "#6b4fbb", "political": "#3a6fd8", "economic": "#1f9aa5", "dual_use": "#b0569a", "service": "#0e7490"}

EXPLORER_DESC = ("Alliances, soutiens, tensions et dépendances d’un coup d’œil : une carte du monde, un graphe "
                 "et des cercles d’organisations. Données sourcées.")

# Anciennes adresses (avant le 2026-10-02) : une page de redirection garde les liens déjà partagés, avec leur sélection et leur ancre
MOVED = {"explorer.html": "vue-d-ensemble.html", "croiser.html": "relations.html"}
def redirects(out):
    for old, new in MOVED.items():
        (out / old).write_text(f"""<!doctype html><html lang="fr"><head><meta charset="utf-8"><title>{brand.NAME}</title>
<meta name="robots" content="noindex"><link rel="canonical" href="{brand.SITE}{new}">
<script>location.replace("{new}" + location.search + location.hash)</script>
<meta http-equiv="refresh" content="0; url={new}"></head><body><p><a href="{new}">Cette page a changé d'adresse.</a></p></body></html>
""", encoding="utf-8")

def sitemap(out):
    """sitemap.xml : toutes les pages publiées, datées du jour de construction (à déclarer dans la Search Console)."""
    day = db.now()[:10]
    pages = sorted(p.name for p in out.glob("*.html") if p.name not in MOVED)
    urls = "".join(f"<url><loc>{brand.SITE}{'' if p == 'index.html' else p}</loc><lastmod>{day}</lastmod></url>" for p in pages)
    (out / "sitemap.xml").write_text(f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>\n', encoding="utf-8")

def export_data(actors, edges):
    (OUT / "network.json").write_text(json.dumps(
        {"license": DATA_LICENSE, "generated_at": db.now(), "actors": actors, "edges": edges,
         "tensions": network.tensions()},
        ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    with open(OUT / "network.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["from", "from_name", "to", "to_name", "types", "status", "confidence",
                    "sources", "verified", "note", "why"])
        for e in edges:
            w.writerow([e["from"], network.name(actors, e["from"]), e["to"], network.name(actors, e["to"]),
                        ";".join(e["types"]), e["status"], e["confidence"], " | ".join(e["sources"]),
                        e["verified"], e.get("note", ""), e.get("why", "")])

def build():
    actors, edges = network.load()
    c = db.conn()
    profiles = {}
    aligns = network.alignments()
    isos = {aid if a["kind"] in ("state", "bloc") else a.get("base") for aid, a in actors.items()} | network.org_countries(aligns)
    for iso in sorted(i for i in isos if i):
        p, fetched = db.get_profile(c, iso)
        if p:
            profiles[iso] = {**p, "fetched_at": fetched}
    OUT.mkdir(exist_ok=True)
    geo, unga = db.load_geo(), db.load_unga()
    if unga:  # le jeu Voeten est indexé en ISO3, le site en ISO2
        by3 = {v["iso3"]: k for k, v in geo.items() if v.get("iso3")}
        unga["countries"] = {by3[c]: v for c, v in unga["countries"].items() if c in by3}
        unga["by_year"] = {y: {by3[c]: v for c, v in d.items() if c in by3} for y, d in unga.get("by_year", {}).items()}
    data = {"actors": actors, "edges": edges, "profiles": profiles, "colors": TYPE_COLORS,
            "tensions": network.tensions(), "mediations": network.mediations(), "dependencies": network.dependencies(), "align": aligns, "influence": network.influence(actors, edges, aligns), "geo": geo, "people": db.load_people(), "unga": unga,
            "dossiers": [{"id": x["id"], "title": x["title"]} for x in dossier.load()], "built": db.now(),
            "glossary": glossary.for_js(), "presets": presets.load(), "correction": style.correction_url("Vue d'ensemble"), "dep_icons": style.DEP_ICONS}
    html = TEMPLATE.replace("__DATA__", json.dumps(data, ensure_ascii=False, default=str)
                            .replace("</", "<\\/"))
    (OUT / "vue-d-ensemble.html").write_text(html.replace("__NAME__", brand.NAME).replace("__FONTS__", style.FONTS).replace("__TOP__", style.top("vue-d-ensemble.html")).replace("__THEME__", style.THEME_INIT).replace("__DESC__", EXPLORER_DESC).replace("__SEO__", style.seo("vue-d-ensemble.html", f"Vue d'ensemble : carte, graphe, organisations — {brand.NAME}", EXPLORER_DESC)).replace("__VIEWS__", "".join(
        f'<a href="#{a}" data-view="{a}" title="{t}">{style.icon(k, 16)}<span>{t}</span></a>' for a, k, t in style.VIEWS)), encoding="utf-8")
    export_data(actors, edges)
    method.write(OUT, data)
    style.write(OUT)
    dossier.write(OUT, data)
    pages.write(OUT, data)
    cross.write(OUT, data)
    glossary.write(OUT)
    redirects(OUT)
    sitemap(OUT)
    for folder in ("photos", "flags"):  # vignettes et drapeaux hébergés sur le site, sans requête vers un tiers
        if (Path("data") / folder).exists():
            shutil.copytree(Path("data") / folder, OUT / folder, dirs_exist_ok=True)
    for png in Path("assets").glob("partage*.png"):  # images de partage (og:image) : site et dossiers, produites par share.py
        shutil.copy(png, OUT / png.name)
    print(f"→ {OUT}/ : index.html (accueil), vue-d-ensemble.html, relations.html, manifeste.html, glossaire.html, methode.html, dossiers, network.json, network.csv")
    return data

TEMPLATE = r"""<!doctype html><html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Vue d'ensemble : carte, graphe, organisations — __NAME__</title>
<meta name="description" content="__DESC__">
__SEO__
<script src="https://cdn.jsdelivr.net/npm/vis-network@10.1.2/standalone/umd/vis-network.min.js"></script>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/leaflet.css">
<script src="https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/leaflet.js"></script>
<script src="https://cdn.jsdelivr.net/npm/topojson-client@3/dist/topojson-client.min.js"></script>
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link rel="stylesheet" href="__FONTS__">
<link rel="stylesheet" href="style.css"><link rel="icon" href="favicon.svg" type="image/svg+xml">__THEME__
<style>
/* explorateur : mêmes jetons que style.css ; l'interface reste discrète, la couleur sert aux données */
:root{--land-hl:#e9ecef}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){--land-hl:#28303b}}:root[data-theme=dark]{--land-hl:#28303b}
body{font:14.5px/1.5 var(--sans);display:grid;grid-template-columns:auto minmax(0,1fr) auto;grid-template-rows:auto minmax(0,1fr);height:100vh}
.xhead{grid-column:1/-1;padding:0 18px 12px;border-bottom:1px solid var(--mist);position:relative;z-index:1500}.xhead .top{padding-top:14px}
#stage{position:relative;min-height:60vh;--bar:120px}#graph{position:absolute;inset:var(--bar) 0 0 0}
/* filtres : barre latérale gauche, repliable (état gardé dans le navigateur) */
#controls{width:260px;border-right:1px solid var(--mist);font-size:13.5px;overflow:auto;display:flex;flex-direction:column}
.ctl-head{display:flex;align-items:center;justify-content:space-between;gap:8px;padding:12px 10px 8px 16px}
.ctl-head span{color:var(--graphite)}
.toggle{background:none;border:0;color:var(--graphite);cursor:pointer;padding:4px;border-radius:3px;display:flex}
.toggle:hover{color:var(--ink);background:color-mix(in srgb,var(--ink) 6%,transparent)}
#ctl-body{padding:4px 16px 20px;display:flex;flex-direction:column;gap:12px}
#controls.closed{width:44px;cursor:pointer}#controls.closed #ctl-body{display:none}
#controls.closed .toggle svg,aside.closed .toggle svg{transform:scaleX(-1)}
.closed .ctl-head{padding:12px 6px;flex-direction:column;justify-content:flex-start;gap:12px}
.closed .ctl-head span{writing-mode:vertical-rl;transform:rotate(180deg);color:var(--ink);font-weight:500;letter-spacing:.02em}
.closed:hover .ctl-head span{color:var(--peach)}
#controls label{display:block}
#controls select{font:inherit;background:var(--paper);color:var(--ink);border:1px solid var(--mist);border-radius:3px;padding:1px 2px;max-width:100%}
#controls .ctl-t{color:var(--graphite);margin-bottom:4px}
/* légende = filtres : chaque ligne montre le trait tel qu'il est dessiné, et sa case l'affiche ou le masque */
.fg{margin-top:4px}.fg-h{display:flex;justify-content:space-between;align-items:baseline;margin:0 0 4px}
.fg-h b{font-weight:600}.fg-h span{font-size:12.5px;color:var(--graphite)}
.fg-h button{background:none;border:0;padding:0 2px;font:inherit;color:inherit;cursor:pointer;text-decoration:underline dashed var(--peach) 1px;text-underline-offset:3px}
.fg-h button:hover,#viewnote button:hover{text-decoration-style:solid}
#controls .fg label{display:flex;align-items:center;gap:8px;margin:2px 0}.fg svg{flex:none}
.fg .note,#map-key .note{display:flex;align-items:center;gap:8px;color:var(--graphite);font-size:12.5px;margin:2px 0 0 22px}
#map-key .note{margin-left:0}.fg .contour{color:var(--graphite);font-size:12.5px;margin-top:4px}.ramp{height:9px;border-radius:2px;margin:4px 0 2px}.ramp-l{display:flex;justify-content:space-between;font-size:12px;color:var(--graphite)}
#year{accent-color:var(--peach)}
#map{position:absolute;inset:var(--bar) 0 0 0;display:none;background:var(--ocean)}
body.map #map{display:block}body.map #graph,body.map .graph-only{display:none}
/* chaque vue n'affiche que ses filtres */
#controls .map-only,#controls .venn-only{display:none}body.map #controls .map-only,body.venn #controls .venn-only{display:block}
body.map #controls .graph-only,body.venn #controls .graph-only,body.map #controls .no-map,body.venn #controls .no-venn{display:none}

/* choix de la vue : contrôle segmenté centré en haut de la zone principale */
/* haut de la zone principale : choix de la vue, questions pour commencer (presets.yaml), état de la vue */
#stagebar{position:absolute;top:0;left:0;right:0;padding:10px 12px;border-bottom:1px solid var(--mist);background:var(--paper);z-index:1000;display:flex;flex-wrap:wrap;justify-content:center;align-items:center;gap:8px 12px;pointer-events:none}
#stagebar>*{pointer-events:auto}
#views{display:flex;padding:3px;gap:2px;
  background:var(--land);border:1px solid var(--mist);border-radius:8px;box-shadow:0 2px 10px #0000001a;max-width:100%}
/* menu « Questions » : les questions de l'onglet ouvert ; une question active remplace le libellé du bouton */
#qmenu{position:relative}#qmenu[hidden]{display:none}
.qbtns{display:flex;border:1px solid var(--mist);border-radius:8px;background:var(--land);box-shadow:0 2px 10px #0000001a;overflow:hidden}
#qbtn,#qclear{background:none;border:0;font:inherit;font-size:14px;color:var(--ink);cursor:pointer;padding:8px 12px;display:flex;align-items:center;gap:7px;max-width:340px}
#qbtn span{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
#qbtn::after{content:"";width:6px;height:6px;border:solid currentColor;border-width:0 1.5px 1.5px 0;transform:translateY(-2px) rotate(45deg);opacity:.7;flex:none}
#qbtn[aria-expanded="true"]::after{transform:translateY(1px) rotate(-135deg)}
#qbtn.on{box-shadow:inset 0 -2px 0 var(--peach)}#qclear[hidden]{display:none}#qclear{border-left:1px solid var(--mist);color:var(--graphite);padding:8px 10px}
#qbtn:hover,#qclear:hover{background:color-mix(in srgb,var(--ink) 6%,var(--land))}
#presets{position:absolute;top:calc(100% + 6px);left:50%;transform:translateX(-50%);z-index:2000;width:max-content;max-width:min(360px,90cqw);display:flex;flex-direction:column;padding:6px;
  background:var(--land);border:1px solid var(--mist);border-radius:8px;box-shadow:0 8px 24px #0000002a}
#presets[hidden]{display:none}
#presets a{padding:8px 10px;border-radius:5px;font-size:14px;color:var(--ink);
  text-decoration:none;box-shadow:0 1px 4px #00000012}
#presets a:hover,#presets a:focus-visible{background:color-mix(in srgb,var(--ink) 6%,var(--land))}#presets a[aria-current]{box-shadow:inset 2px 0 0 var(--peach)}
#viewnote{font-size:12.5px;color:var(--graphite);background:color-mix(in srgb,var(--paper) 88%,transparent);padding:2px 10px;border-radius:10px}
#viewnote:empty{display:none}
#viewnote button{background:none;border:0;padding:0;font:inherit;color:var(--ink);cursor:pointer;text-decoration:underline dashed var(--peach) 1px;text-underline-offset:3px}
#views a{display:flex;align-items:center;gap:7px;padding:6px 12px;border-radius:5px;color:var(--graphite);text-decoration:none;white-space:nowrap;font-size:14px}
#views a:hover{color:var(--ink)}#views a[aria-current]{background:color-mix(in srgb,var(--ink) 8%,var(--land));color:var(--ink)}
#views .ico{color:var(--peach)}
#stage{container-type:inline-size;overflow:hidden}
@container (max-width:520px){#views a{padding:6px 10px}#views a span{display:none}}
#venn{position:absolute;inset:var(--bar) 0 0 0;display:none;padding:12px 12px 28px}body.venn #venn{display:block}
body.venn #graph,body.venn .graph-only{display:none}#venn svg{width:100%;height:100%;overflow:visible}
#venn text{font-family:system-ui,sans-serif}.vc{cursor:pointer}.vc:hover circle{stroke:var(--fg)}
.venn-empty{max-width:380px;margin:120px auto;text-align:center}.venn-note{position:absolute;bottom:4px;left:12px;right:60px;margin:0}
.vsvg{position:absolute;inset:12px 12px 28px;cursor:grab}.vsvg:active{cursor:grabbing}.vsvg svg{width:100%;height:100%}
.vz{position:absolute;right:12px;bottom:12px;display:flex;flex-direction:column;border:1px solid var(--mist);border-radius:4px;overflow:hidden;background:var(--land);box-shadow:0 1px 5px #0002}
.vz button{width:30px;height:30px;border:0;border-bottom:1px solid var(--mist);background:none;color:var(--ink);font:16px/1 var(--sans);cursor:pointer}
.vz button:last-child{border-bottom:0}.vz button:hover{background:color-mix(in srgb,var(--ink) 8%,var(--land))}
.leaflet-container{background:var(--ocean);font:inherit}
.leaflet-bar a,.leaflet-tooltip{background:var(--card);color:var(--fg);border-color:var(--line)}
.mk{display:flex;align-items:center;justify-content:center;cursor:pointer}
.mk img{width:100%;height:100%;border-radius:50%;box-shadow:0 0 0 1.5px var(--card),0 1px 4px #0006}
.mk i{display:block;width:12px;height:12px;background:#6b4fbb;box-shadow:0 0 0 1.5px var(--card)}
.mk.non_state i{background:#d64545;transform:rotate(45deg)}.mk.party i{background:#6b4fbb}.mk.company i{background:#6b4fbb}
.mk.person i{background:#6b4fbb;clip-path:polygon(50% 0,100% 100%,0 100%);box-shadow:none;width:14px;height:13px}
aside{width:380px;overflow:auto;border-left:1px solid var(--mist)}aside a{color:inherit}#panel{padding:4px 24px 40px}
aside.closed{width:44px;overflow:hidden;cursor:pointer}aside.closed #panel{display:none}
aside.closed .ctl-head{flex-direction:column-reverse;justify-content:flex-end}
aside h1{font:400 26px/1.2 var(--serif);margin:0 0 6px}aside h2{font:400 18px/1.3 var(--serif);color:var(--ink);margin:26px 0 8px}
aside p{margin:0 0 10px}.keys{display:grid;grid-template-columns:78px 1fr;gap:6px 12px;margin:0;font-size:13.5px}
.keys dt{color:var(--graphite)}.keys dd{margin:0}.key{display:inline-flex;align-items:center;gap:5px;margin:0 10px 2px 0;white-space:nowrap}
.key i{width:9px;height:9px;border-radius:50%;display:inline-block}
.kv{display:grid;grid-template-columns:140px 1fr;gap:3px 10px}.kv span:nth-child(odd){color:var(--mute)}
.rel{padding:10px 0;border-bottom:1px solid var(--mist)}.rel b{cursor:pointer}.rel .mute{margin-top:2px}
.tag{display:inline-block;font-size:11px;padding:1px 6px;border-radius:9px;color:#fff;margin:2px 2px 0 0}
.mute{color:var(--mute);font-size:13px}.legend .tag{margin-right:4px}
#orgs .list{padding-right:4px}
#orgs .og{font-weight:600;color:var(--mute);margin-top:10px}#controls #orgs label{display:flex;align-items:center;gap:6px}
#orgs i,.sw{display:inline-block;width:11px;height:11px;border-radius:3px;flex:none;border:1px solid var(--line);vertical-align:-1px}
.future{opacity:.45}
.dep{padding:8px 0;border-bottom:1px solid var(--mist)}.dep-h{display:flex;justify-content:space-between;gap:10px;align-items:baseline}
.dep-h b{cursor:pointer}.dep-h span{font-size:13px;color:var(--graphite);text-align:right}
.bar{height:7px;border-radius:2px;background:color-mix(in srgb,var(--ink) 10%,transparent);margin:5px 0 4px}.bar i{display:block;height:100%;border-radius:2px;background:#b08968}
.dossiers{display:flex;flex-direction:column;gap:8px;margin:0 0 16px}
.btn-dossier{display:block;padding:11px 14px;border:1px solid var(--mist);border-radius:6px;background:var(--land);text-decoration:none;font:500 16px/1.3 var(--serif)}
.btn-dossier:hover{border-color:var(--peach)}.btn-dossier::after{content:"Lire le dossier";display:block;font:13px var(--sans);color:var(--graphite);margin-top:2px}
.fg .sub{margin:10px 0 2px 22px;font-size:12.5px;color:var(--ink)}
/* mobile : une colonne ; les filtres passent au-dessus de la vue, repliés en une ligne « Filtres » */
@media (max-width:800px){body{grid-template-columns:1fr;grid-template-rows:auto auto 60vh auto;height:auto}
  #controls{width:auto;border-right:0;border-bottom:1px solid var(--mist)}#controls.closed{width:auto}
  .closed .ctl-head,aside.closed .ctl-head{padding:12px 10px 12px 16px;flex-direction:row;justify-content:space-between}.closed .ctl-head span{writing-mode:horizontal-tb;transform:none}
  aside,aside.closed{width:auto;border-left:0;border-top:1px solid var(--mist)}
}
</style></head><body>
<header class="xhead">__TOP__</header>
<nav id="controls" aria-label="Filtres">
  <div class="ctl-head"><span>Filtres</span><button id="ctl-toggle" class="toggle" type="button" aria-expanded="true" aria-controls="ctl-body" title="Replier">
    <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect width="18" height="18" x="3" y="3" rx="2"/><path d="M9 3v18"/><path d="m16 15-3-3 3-3"/></svg></button></div>
  <div id="ctl-body">
  <label>Année <input type="range" id="year" min="2014" step="1" style="vertical-align:middle;width:130px"> <b id="year-label"></b></label>
  <label class="no-map"><span class="ctl-t" style="display:block">Taille des acteurs</span><select id="metric">
    <option value="military">dépenses militaires ($)</option><option value="gdp">PIB ($)</option>
    <option value="population">population</option>
    <option value="supports">nombre de soutiens accordés</option><option value="none">même taille pour tous</option></select></label>
  <div id="orgs" class="venn-only"><div class="ctl-t">Organisations <b id="orgs-n"></b></div><div class="list"></div></div>
  <label class="map-only"><span class="ctl-t" style="display:block">Couleur des pays</span><select id="colormode">
    <option value="formal">liens formels (traités, adhésions)</option><option value="votes">votes à l'ONU</option></select></label>
  <div id="map-key" class="map-only"></div>
  <div id="rel-filters" class="no-venn"></div>
  </div>
</nav>
<div id="stage"><div id="stagebar"><nav id="views" aria-label="Vues">__VIEWS__</nav>
<div id="qmenu"><div class="qbtns"><button type="button" id="qbtn" aria-haspopup="true" aria-expanded="false" aria-controls="presets"></button><button type="button" id="qclear" title="Revenir à la vue simplifiée" aria-label="Quitter la question, revenir à la vue simplifiée" hidden>✕</button></div>
<div id="presets" role="menu" aria-label="Questions pour cette vue" hidden></div></div><div id="viewnote"></div></div><div id="graph"></div><div id="map"></div><div id="venn"></div></div>
<aside id="side" aria-label="Détails"><div class="ctl-head"><span>Détails</span><button id="side-toggle" class="toggle" type="button" aria-expanded="true" aria-controls="panel" title="Replier">
    <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect width="18" height="18" x="3" y="3" rx="2"/><path d="M15 3v18"/><path d="m8 9 3 3-3 3"/></svg></button></div>
<div id="panel"></div></aside>
<script>
const D = __DATA__;
let map, groups, linkLayers = [], countries;  // carte Leaflet, créée à la première visite de la vue
const $ = s => document.querySelector(s);
const esc = v => String(v ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const safeUrl = u => /^(https?:\/\/|photos\/[\w.-]+$)/.test(u||"") ? esc(u) : "#";
const nm = id => esc((D.actors[id]||{}).name || id);
const KIND = {state:"État", non_state:"acteur armé non étatique", bloc:"bloc", party:"parti politique", person:"personnalité", company:"entreprise", passage:"point de passage"};
const SHAPE = {non_state:"diamond", party:"square", person:"triangle", company:"hexagon"};
const DETAIL = new Set(["party","person","company","passage"]);
// drapeau : champ flag de l'acteur (territoire sans code pays), sinon flag-icons d'après le code ISO2
const flag = id => (D.actors[id] || {}).flag || `https://cdn.jsdelivr.net/npm/flag-icons@7.2.3/flags/1x1/${id.toLowerCase()}.svg`;
const CONTESTED = "#c98a1b";
// Icônes Lucide (ISC) inlinées : épées = groupe armé, urne = parti, silhouette = personne sans photo
const GLYPH = {
  non_state: '<polyline points="14.5 17.5 3 6 3 3 6 3 17.5 14.5"/><line x1="13" x2="19" y1="19" y2="13"/><line x1="16" x2="20" y1="16" y2="20"/><line x1="19" x2="21" y1="21" y2="19"/><polyline points="14.5 6.5 18 3 21 3 21 6 17.5 9.5"/><line x1="5" x2="9" y1="14" y2="18"/><line x1="7" x2="4" y1="17" y2="20"/><line x1="3" x2="5" y1="19" y2="21"/>',
  party: '<path d="m9 12 2 2 4-4"/><path d="M5 7c0-1.1.9-2 2-2h10a2 2 0 0 1 2 2v12H5V7Z"/><path d="M22 19H2"/>',
  person: '<path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>',
  company: '<path d="M6 22V4a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v18Z"/><path d="M6 12H4a2 2 0 0 0-2 2v6a2 2 0 0 0 2 2h2"/><path d="M18 9h2a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2h-2"/><path d="M10 6h4"/><path d="M10 10h4"/><path d="M10 14h4"/><path d="M10 18h4"/>',
  passage: '<path d="M12 22V8"/><path d="M5 12H2a10 10 0 0 0 20 0h-3"/><circle cx="12" cy="5" r="3"/>'};
const badge = (kind, bg) => "data:image/svg+xml;charset=utf-8," + encodeURIComponent(
  `<svg xmlns="http://www.w3.org/2000/svg" viewBox="-6 -6 36 36"><circle cx="12" cy="12" r="18" fill="${bg}"/>` +
  `<g fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">${GLYPH[kind]}</g></svg>`);
const BLOCS = D.align.blocs, GROUPS = Object.fromEntries(D.align.groups.map(g => [g.id, g]));
const LEVEL = {3:"défense mutuelle", 2:"partenariat stratégique", 1:"lien formel partiel"};
const LEVEL_TERM = {3:"defense-mutuelle", 2:"partenariat-strategique", 1:"lien-partiel"};
const levelText = l => l > 0 ? `${T(LEVEL_TERM[l], LEVEL[l])} (${T("niveau", `niveau ${l} sur 3`)})` : "sans effet sur l'alignement";
const TINT = {3:.62, 2:.45, 1:.25};   // intensité de la couleur selon le niveau d'alignement
const inf = id => D.influence[id] || {role:"none", via:[], ties:[]};
const cname = iso => esc((D.actors[iso]||{}).name || (D.geo[iso]||{}).name || iso);
function blocColor(id){ const i = inf(id);
  return i.role==="contested" ? CONTESTED : i.bloc ? BLOCS[i.bloc].color : null; }
// Image d'un acteur : drapeau (État, bloc), photo Commons (personne), sinon pictogramme sur fond de couleur de bloc
function picOf(id){ const a = D.actors[id];
  if(a.kind==="state" || a.kind==="bloc") return flag(id);
  if(D.people[id]) return D.people[id].thumb;
  return badge(a.kind, blocColor(id) || (a.kind==="non_state" ? "#8a8a8a" : "#6b4fbb")); }
// Dirigeant (champ leader) : affiché sur la fiche, pas un nœud du graphe (sauf s'il a des relations propres)
const leaderKey = id => { const l = (D.actors[id]||{}).leader; return typeof l === "string" ? l : l ? "leader:" + id : null; };
function leaderLine(id){ const l = (D.actors[id]||{}).leader; if(!l) return "";
  const k = leaderKey(id), p = D.people[k], name = typeof l === "string" ? `<b data-id="${esc(l)}" style="cursor:pointer">${nm(l)}</b>` : `<b>${esc(l.name)}</b>`;
  const role = typeof l === "string" ? "" : l.role ? ` — ${esc(l.role)}` : "";
  return `<div class="rel" style="display:flex;gap:10px;align-items:center">${p ? `<img src="${safeUrl(p.thumb)}" alt=""
    style="width:40px;height:40px;border-radius:50%;object-fit:cover">` : ""}<div>Dirigeant : ${name}${role}</div></div>`; }
const credit = id => { const p = D.people[id]; return p ? `<p class="mute">Photo : ${esc(p.artist)}, ${esc(p.license)} —
  <a href="${safeUrl(p.page)}" target="_blank" rel="noopener">Wikimedia Commons</a></p>` : ""; };
function mix(a, b, t){ const h = x => [1,3,5].map(i => parseInt(x.slice(i,i+2),16));
  const [p,q] = [h(a), h(b)]; return "#"+p.map((v,i)=>Math.round(v*t+q[i]*(1-t)).toString(16).padStart(2,"0")).join(""); }
function blocLine(id){ const i = inf(id), nmv = i.via.map(nm).join(", ");
  const ties = i.ties.filter(t => GROUPS[t].level > 0).map(t => esc(GROUPS[t].name)).join(", ");
  if(i.role==="member") return `${T("bloc", "Bloc")} : <b style="color:${blocColor(id)}">${esc(BLOCS[i.bloc].name)}</b>, ${levelText(i.level)}, via ${ties}${nmv ? `. Soutenu par ${nmv}` : ""}`;
  if(i.role==="satellite") return `${T("bloc", "Bloc")} : <b style="color:${blocColor(id)}">${esc(BLOCS[i.bloc].name)}</b>, ${T("satellite")} : sans ${T("lien-formel")}, tous ses soutiens viennent de ce bloc (${nmv})`;
  if(i.role==="contested") return `${T("bloc", "Bloc")} : <b style="color:${CONTESTED}">${T("dispute", "disputé")}</b> entre ${i.blocs.map(b=>esc(BLOCS[b].name)).join(" et ")}${ties ? ` (${ties})` : ` (soutenu par ${nmv})`}`;
  return ""; }
// ---------- Organisations (groupes d'alignments.yaml) : calques superposables de la carte, fiches ----------
// Jusqu'à 6 calques, palette catégorielle validée (clair / sombre) ; une couleur reste attachée à son organisation
// tant qu'elle est cochée, pour que cocher ou décocher une autre ne repeigne pas la carte.
window.THEME_RELOAD = true;  // couleurs du graphe, de la carte et des organisations lues au chargement
const DARK = document.documentElement.dataset.theme ? document.documentElement.dataset.theme === "dark" : matchMedia("(prefers-color-scheme: dark)").matches;
const ORG_PAL = DARK
  ? ["#3987e5","#d95926","#199e70","#c98500","#d55181","#008300"]
  : ["#2a78d6","#eb6834","#1baf7a","#eda100","#e87ba4","#008300"];
const SEL = new Map();  // id du groupe → couleur
const yr = d => +String(d).slice(0,4);
// Membres l'année Y : adhésions (joined) et départs (left) datés depuis 2014 ; un membre sans date l'était déjà.
function membersAt(g, Y){ if(g.since && yr(g.since) > Y) return [];
  const j = g.joined || {}, l = g.left || {};
  return [...g.members.filter(m => !j[m] || yr(j[m]) <= Y), ...Object.keys(l).filter(m => yr(l[m]) > Y)]; }
function movesOf(g){ return [...(g.since ? [{g, d:g.since, t:"création"}] : []),
  ...Object.entries(g.joined||{}).filter(([m,d]) => d !== g.since).map(([m,d]) => ({g, m, d, t:"entrée"})),
  ...Object.entries(g.left||{}).map(([m,d]) => ({g, m, d, t:"sortie"}))]; }
(() => { const box = $("#orgs .list"), add = (label, gs) => { if(!gs.length) return;
    box.insertAdjacentHTML("beforeend", `<div class="og">${esc(label)}</div>` + gs.map(g =>
      `<label><input type="checkbox" autocomplete="off" value="${esc(g.id)}"><i></i>${esc(g.name)} <span class="mute">(${g.members.length})</span></label>`).join("")); };
  add("Forums économiques et politiques", D.align.groups.filter(g => g.kind==="forum"));
  Object.entries(BLOCS).forEach(([k,b]) => add(b.name, D.align.groups.filter(g => g.bloc===k)));
  box.addEventListener("change", syncOrgs);
  addEventListener("pageshow", () => SEL.size || document.querySelector("#orgs input:checked") ? syncOrgs() : null); })();
// Les cases cochées font foi (le navigateur peut les restaurer au rechargement) : SEL est réaligné sur elles.
function syncOrgs(){
  const on = new Set([...document.querySelectorAll("#orgs input:checked")].map(i => i.value));
  [...SEL.keys()].forEach(id => on.has(id) || SEL.delete(id));
  on.forEach(id => { if(!SEL.has(id) && SEL.size < ORG_PAL.length){ const used = new Set(SEL.values());
    SEL.set(id, ORG_PAL.find(c => !used.has(c))); } });
  document.querySelectorAll("#orgs input").forEach(i => i.checked = SEL.has(i.value));
  document.querySelectorAll("#orgs input").forEach(i => { i.nextElementSibling.style.background = SEL.has(i.value) ? tint(SEL.get(i.value)) : "transparent";
    i.disabled = !i.checked && SEL.size >= ORG_PAL.length; });
  $("#orgs-n").textContent = SEL.size ? `(${SEL.size}/${ORG_PAL.length})` : "";
  drawVenn();
  SEL.size ? showLayers() : legend(); }
// même teinte partout (carte, cases, panneau) : couleur de l'organisation légèrement adoucie vers le fond de carte
const tint = c => mix(c, css("--land"), .8);
const sw = c => `<span class="sw" style="background:${tint(c)}"></span>`;
const METRIC_FR = {military:"Dépenses militaires cumulées", gdp:"PIB cumulé", population:"Population cumulée", supports:"Soutiens accordés"};
const big = x => Math.abs(x)>=1e9 ? (x/1e9).toLocaleString("fr-FR",{maximumFractionDigits:0})+" Md" : Math.abs(x)>=1e6 ? (x/1e6).toLocaleString("fr-FR",{maximumFractionDigits:1})+" M" : x.toLocaleString("fr-FR",{maximumFractionDigits:0});
const unitOf = m => m==="population" ? " hab." : m==="supports" ? "" : " $";
const metricText = (iso, m) => { const v = metricOf(iso, m); return v ? big(v) + unitOf(m) : "pas de donnée"; };
// poids de chaque membre dans une organisation, pour la mesure choisie : total, part des 3 premiers, données manquantes
function weights(members, m){ if(m==="none") return "";
  const vs = members.map(iso => [iso, metricOf(iso, m)]), ok = vs.filter(([,v]) => v).sort((a,b) => b[1] - a[1]);
  const tot = ok.reduce((t,[,v]) => t + v, 0); if(!tot) return "";
  return `<div class="mute">${METRIC_FR[m]} : ${big(tot)}${unitOf(m)}, dont ${ok.slice(0,3).map(([iso,v]) =>
    `${cname(iso)} ${Math.round(100*v/tot)} %`).join(", ")}${ok.length < vs.length ? ` (sans donnée : ${vs.length - ok.length} pays)` : ""}</div>`; }
function showLayers(){ const Y = YEAR(), gs = [...SEL.keys()].map(id => GROUPS[id]), m = $("#metric").value;
  const at = Object.fromEntries(gs.map(g => [g.id, membersAt(g, Y)])), where = {};
  gs.forEach(g => at[g.id].forEach(m => (where[m] = where[m] || []).push(g.id)));
  const pivots = Object.entries(where).filter(([,v]) => v.length > 1)
    .sort((a,b) => b[1].length - a[1].length || cname(a[0]).localeCompare(cname(b[0])));
  const moves = gs.flatMap(movesOf).sort((a,b) => a.d < b.d ? -1 : a.d > b.d ? 1 : 0);
  $("#panel").innerHTML = `<div id="layers-panel"><h1>Organisations superposées</h1>
    <div class="mute">Situation en ${Y} — curseur « Année » pour voir les adhésions et les départs</div>
    ${gs.map(g => `<div class="rel">${sw(SEL.get(g.id))}<a href="#" data-group="${esc(g.id)}">${esc(g.name)}</a>
      <span class="mute">: ${at[g.id].length} pays, ${g.kind==="forum" ? T("forum") : `${esc(BLOCS[g.bloc].name)}, ${levelText(g.level)}`}</span>${weights(at[g.id], m)}</div>`).join("")}
    ${gs.length > 1 ? `<h2>Pays à la croisée (${pivots.length})</h2>` + (pivots.length ? pivots.map(([m,ids]) =>
        `<div class="rel"><a href="#" data-country="${esc(m)}">${cname(m)}</a> ${ids.map(id => sw(SEL.get(id))).join("")}
        <span class="mute">${ids.map(id => esc(GROUPS[id].name)).join(" · ")}</span></div>`).join("")
      : `<p class="mute">Aucun pays n'appartient à plusieurs de ces organisations en ${Y}.</p>`) : ""}
    <h2>Mouvements depuis 2014</h2>${moves.length ? moves.map(v => `<div class="rel${yr(v.d) > Y ? " future" : ""}">${sw(SEL.get(v.g.id))}
      <b>${esc(v.d)}</b> · ${v.m ? `<a href="#" data-country="${esc(v.m)}">${cname(v.m)}</a> ${v.t==="entrée" ? "entre dans" : "quitte"}` : "création de"}
      ${esc(v.g.name)}</div>`).join("") : `<p class="mute">Aucune adhésion ni départ daté depuis 2014 pour ces organisations.</p>`}
    <p class="mute">Chaque cercle est une organisation ; chaque pays se place à l'intersection de celles dont il est membre.
    La taille des drapeaux suit la mesure choisie dans les filtres (Banque mondiale, dernière année disponible), relative
    au plus grand pays affiché. Dates d'adhésion et de départ sourcées dans <code>alignments.yaml</code>.</p></div>`; }
const forumsOf = iso => D.align.groups.filter(g => g.kind==="forum" && g.members.includes(iso));
const forumLine = iso => { const f = forumsOf(iso);
  return f.length ? `Organisations : ${f.map(g => `<a href="#" data-group="${esc(g.id)}">${esc(g.name)}</a>`).join(", ")}` : ""; };
function showGroup(gid){ const g = GROUPS[gid]; if(!g) return;
  $("#panel").innerHTML = `<h1>${esc(g.name)}</h1><div class="mute">${g.kind==="forum" ? `${T("forum")}, sans effet sur les blocs d'influence`
      : `${esc(BLOCS[g.bloc].name)}, ${levelText(g.level)}`}. ${g.members.length} pays</div>
    <p>${g.members.map(m => `<a href="#" data-country="${esc(m)}">${cname(m)}</a>${(g.joined||{})[m] ? ` <span class="mute">(depuis ${esc(g.joined[m])})</span>` : ""}`).join(", ")}</p>
    ${Object.keys(g.left||{}).length ? `<p class="mute">Anciens membres : ${Object.entries(g.left).map(([m,d]) =>
      `<a href="#" data-country="${esc(m)}">${cname(m)}</a> (jusqu'en ${esc(d)})`).join(", ")}</p>` : ""}
    ${g.since ? `<p class="mute">Créée en ${esc(g.since)}.</p>` : ""}
    ${g.note ? `<p class="mute">${esc(g.note)}</p>` : ""}<p class="mute">${g.sources.map(src).join(", ")}</p>`; }
document.addEventListener("click", ev => {
  const gl = ev.target.closest("[data-group]"); if(gl){ ev.preventDefault(); showGroup(gl.dataset.group); }
  const cl = ev.target.closest("[data-country]"); if(cl){ ev.preventDefault(); D.actors[cl.dataset.country] ? show(cl.dataset.country) : showCountry(cl.dataset.country); } });

// ---------- Votes à l'ONU (Voeten) ----------
const U = D.unga || {}, UC = U.countries || {};
const pct = x => x == null ? "n/d" : Math.round(x*100) + " %";
function ungaLine(iso){ const v = UC[iso]; if(!v) return "";
  return `${T("vote-onu", "Votes à l'ONU")} (${U.agreement_year}) : vote comme France/Allemagne <b>${pct(v.west)}</b> des fois, comme
    Russie/Chine <b>${pct(v.axis)}</b>${iso==="US" ? "" : `, comme les États-Unis ${pct(v.usa)}`}. ${leanText(v.lean)}.`; }
// penchant = accord(France, Allemagne) − accord(Russie, Chine), entre −1 et +1 (sources/unga.py) : dit en points d'écart
const leanText = l => Math.abs(l) <= .05 ? "Entre les deux" : `Penche vers ${l > 0 ? "France/Allemagne" : "Russie/Chine"} (écart de ${Math.round(Math.abs(l)*100)} points)`;
const voteYear = () => Math.min(YEAR(), U.agreement_year);
const leanAt = iso => ((U.by_year || {})[voteYear()] || {})[iso];
function votesColor(iso){ const lean = leanAt(iso); if(lean == null) return null;
  const t = Math.min(1, Math.abs(lean) / .5) * .7;
  return mix(lean >= 0 ? BLOCS.west.color : BLOCS.axis.color, css("--land"), t); }
// Écart de vote États-Unis ↔ moyenne France/Allemagne (axe unique Voeten), comparé à l'écart France ↔ Allemagne
function driftBlock(){ const d = U.drift || []; if(d.length < 2) return "";
  const W = 260, H = 60, max = Math.max(...d.map(x => x.us_gap)), X = i => 8 + i*(W-16)/(d.length-1), Y = v => H-8 - v/max*(H-16);
  const line = k => d.map((x,i) => `${X(i).toFixed(1)},${Y(x[k]).toFixed(1)}`).join(" ");
  const a = d[d.length-2], b = d[d.length-1];
  return `<h2>Dérive transatlantique</h2><svg viewBox="0 0 ${W} ${H}" style="width:100%;max-width:${W}px" aria-hidden="true">
    <polyline points="${line("us_gap")}" fill="none" stroke="${BLOCS.west.color}" stroke-width="2"/>
    <polyline points="${line("fr_de_gap")}" fill="none" stroke="var(--mute)" stroke-width="1.5" stroke-dasharray="3 3"/></svg>
    <p class="mute">Écart de vote à l'ONU États-Unis ↔ France/Allemagne (trait plein) : <b>${a.us_gap} en ${a.year} → ${b.us_gap} en ${b.year}</b>,
    contre ${b.fr_de_gap} entre France et Allemagne (pointillés), ${d[0].year}–${b.year}. Mesure sur l'axe unique de Voeten,
    fiable pour un écart entre deux pays, pas pour placer un pays entre deux blocs.</p>`; }
function euCohesion(id){ const g = D.align.groups.find(x => x.entity===id && x.level===3); if(!g) return "";
  const vals = g.members.filter(m => UC[m]).map(m => [m, UC[m].west]).sort((a,b) => a[1]-b[1]);
  if(!vals.length) return "";
  const mean = vals.reduce((s,[,v]) => s+v, 0) / vals.length;
  return `<h2>Cohésion des votes (${U.agreement_year})</h2><p class="mute">Les membres votent comme France/Allemagne en moyenne
    <b>${pct(mean)}</b> des fois. Les plus éloignés : ${vals.slice(0,3).map(([m,v]) => `${cname(m)} ${pct(v)}`).join(", ")}.</p>`; }

// Groupes formels rattachés à une entité (ex. niveaux de l'UE : membres, candidats, zone euro, Schengen)
function tiers(id){ const gs = D.align.groups.filter(g => g.entity===id);
  return gs.length ? `<h2>Niveaux</h2>` + gs.map(g => `<div class="rel"><b>${esc(g.name)}</b>
    <span class="mute">(${g.members.length} pays, ${levelText(g.level)})</span><br>
    <span class="mute">${g.members.map(cname).join(", ")}${g.note ? "<br>"+esc(g.note) : ""}<br>${g.sources.map(src).join(", ")}</span></div>`).join("") : ""; }
const fg = getComputedStyle(document.body).color;
const outCount = id => D.edges.filter(e=>e.from===id && e.status!=="ended").length;
const layer = id => { const k = D.actors[id].kind; return k==="state"||k==="bloc" ? "core" : k==="company" || k==="passage" ? "person" : k; };   // les entreprises partagent le calque des personnalités  // core, non_state, party, person
const checked = (grp, v) => { const i = document.querySelector(`#rel-filters input[data-g="${grp}"][value="${v}"]`); return !i || i.checked; };
const visible = l => checked("kind", l);
const supportOn = e => e.types.some(t => checked("type", t));
const tensionOn = t => checked("tension", t.type);

// Taille = valeur mesurée (Banque mondiale) ou nombre de soutiens ; échelle en racine carrée
const METRIC_KEY = {military:"military_usd", gdp:"gdp_usd", population:"population"};
function metricOf(id, m){
  if(m==="none") return 1;
  if(m==="supports") return outCount(id);
  const p = D.profiles[id]; const v = p && p[METRIC_KEY[m]];
  return v ? v.value : null; }
function sizes(m){
  if(m==="none") return Object.fromEntries(Object.keys(D.actors).map(id => [id, 22]));
  const vals = Object.keys(D.actors).map(id=>metricOf(id,m)).filter(v=>v);
  const max = Math.max(...vals, 1);
  return Object.fromEntries(Object.keys(D.actors).map(id=>{ const v = metricOf(id,m);
    return [id, v ? 10 + 45*Math.sqrt(v/max) : 9]; })); }

function nodeFor(id, size){ const a = D.actors[id], pic = a.kind==="state" || a.kind==="bloc";
  if(!pic) size = Math.max(size, a.kind==="person" ? 18 : 14);
  return {id, label:a.name, size, shape: "circularImage", image: picOf(id),
    color: DETAIL.has(a.kind) ? {background:"#e7e2f5", border:"#6b4fbb"}
         : blocColor(id) ? {border: blocColor(id), background: blocColor(id)} : undefined,
    borderWidth: blocColor(id) ? 1 + (inf(id).level || 1) : pic ? 1 : 1.5, font:{color:fg, size: 11 + Math.round(size/7)},
    hidden: !shown(id)}; }
// ---------- Temps : une relation est affichée pour l'année Y si since ≤ Y ≤ until ----------
const NOW = +D.built.slice(0,4);
const YEAR = () => +($("#year") ? $("#year").value : NOW);
(() => { const y = $("#year"); y.max = NOW; y.value = NOW; })();
function activeAt(e, Y){
  const since = e.since ? +String(e.since).slice(0,4) : null, until = e.until ? +String(e.until).slice(0,4) : null;
  if(since && Y < since) return false;
  if(until && Y > until) return false;
  return Y < NOW || e.status !== "ended";  // aujourd'hui : on masque ce qui est terminé
}
const dated = e => e.since ? `depuis ${e.since}${e.until ? ` jusqu'à ${e.until}` : ""}` : "début non daté";
// soutien : `since` = plus ancienne date attestée par les sources, pas forcément le vrai début → « documenté depuis »
const datedDoc = e => e.since ? `documenté depuis ${e.since}${e.until ? `, jusqu'à ${e.until}` : ""}` : "début non daté";
// deux dimensions, deux codages : le STATUT par le tracé (plein = actif, tirets = en baisse ou allégué),
// la CONFIANCE par l'épaisseur (épais = documenté officiellement, moyen = sources concordantes, fin = allégations)
const DASHED = e => e.status !== "active", WIDTH = {high: 2.8, medium: 1.6, low: .8};
const edgeList = D.edges.map((e,i) => ({id:"e"+i, from:e.from, to:e.to, arrows:"to", hidden: !activeAt(e, NOW) || !supportOn(e),
  color:D.colors[e.types[0]]||"#888", dashes: DASHED(e), width: WIDTH[e.confidence] || 1.4, title:`${(D.actors[e.from]||{}).name||e.from} → ${(D.actors[e.to]||{}).name||e.to} : ${e.types.join(", ")} (${datedDoc(e)})`}));
// lien d'ancrage parti/personnalité → pays (calque détail)
const anchors = Object.entries(D.actors).filter(([id,a])=>DETAIL.has(a.kind) && D.actors[a.base])
  .map(([id,a]) => ({id:"b-"+id, from:id, to:a.base, dashes:[2,4], color:"#999", width:1, title:"rattaché à"}));

// ---------- Tensions : guerres, sanctions, revendications, rivalités, guerres commerciales — hors soutiens ----------
// Tracées sans effet sur la disposition du graphe (physics:false) ; atténuées si trêve ou cessez-le-feu.
const TENSION = {war:{label:"guerre", color:"#b91c1c", width:3.2, dashes:false, arrows:""},
  sanctions:{label:"sanctionne", color:"#7c3aed", width:1.8, dashes:[8,5], arrows:"to"},
  claims:{label:"revendique", color:"#d97706", width:1.8, dashes:[3,4], arrows:"to"},
  rivalry:{label:"rivalité", color:"#64748b", width:1.8, dashes:[10,6], arrows:""},
  trade_war:{label:"guerre commerciale", color:"#be185d", width:1.8, dashes:[12,4,2,4], arrows:""},
  blockade:{label:"entrave la navigation", color:"#0f766e", width:2.2, dashes:[2,5], arrows:"to"}};
const TS = D.tensions || [], BG = getComputedStyle(document.documentElement).getPropertyValue("--bg").trim();
const tensionTitle = t => `${(D.actors[t.from]||{}).name||t.from} ${t.type==="war"||t.type==="rivalry"||t.type==="trade_war" ? "⟷" : "→"} ${(D.actors[t.to]||{}).name||t.to} : ${TENSION[t.type].label}${t.status==="reduced" ? " (trêve ou cessez-le-feu)" : ""} (${dated(t)})`;
const tensionEdges = TS.map((t,i) => { const s = TENSION[t.type];
  return {id:"t"+i, from:t.from, to:t.to, arrows:s.arrows, physics:false, width:s.width, label:s.label,
    color:{color:s.color, opacity: t.status==="active" ? 1 : .55}, dashes: t.status==="active" ? s.dashes : [2,6],
    smooth:{type:"curvedCW", roundness:.18}, font:{size:10, color:s.color, strokeWidth:3, strokeColor:BG},
    hidden: !activeAt(t, NOW) || !tensionOn(t), title: tensionTitle(t)}; });
const tensionsVisible = () => TS.map((t,i) => ({id:"t"+i, hidden: !tensionOn(t) || !activeAt(t, YEAR())}));
// ---------- Médiations (clé mediations de network.yaml) : qui négocie entre qui ; ni soutien ni tension ----------
const MEDS = D.mediations || [], MED = {color: "#8e9aaf", dashes: [2, 5], width: 1.8};
const medOn = m => checked("med", "on") && activeAt(m, YEAR());
const medTitle = m => `${(D.actors[m.mediator]||{}).name} : ${m.form === "mission" ? "mission de paix" : "médiation"} entre ${m.between.map(b => (D.actors[b]||{}).name).join(" et ")} (${dated(m)})`;
const medEdges = MEDS.flatMap((m, i) => m.between.map(b => ({id: `m${i}-${b}`, from: m.mediator, to: b, arrows: "", physics: false,
  width: MED.width, dashes: MED.dashes, color: {color: MED.color, opacity: 1}, smooth: {type: "curvedCCW", roundness: .12},
  hidden: true, title: medTitle(m)})));
const medsVisible = () => MEDS.flatMap((m, i) => m.between.map(b => ({id: `m${i}-${b}`, hidden: !medOn(m)})));
// ---------- Leviers (clé dependencies) : part chiffrée d'une ressource tirée d'un fournisseur ; ni soutien ni tension ----------
const DEPS = D.dependencies || [], DEP = {color: "#b08968", dashes: [1, 4]};
const DEP_FR = {arms: "d'armes", gas: "de gaz", oil: "de pétrole"};
const depWhat = x => x.resource ? (/^[aeiouyéèh]/i.test(x.resource) ? "d'" : "de ") + x.resource : DEP_FR[x.type] || x.type;
const depOn = x => checked("dep", "on") && x.status !== "ended";
const depIcon = (t, size = 14) => `<svg class="dep-ico" viewBox="0 0 24 24" width="${size}" height="${size}" fill="none" stroke="${DEP.color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" style="vertical-align:-2px">${D.dep_icons[t] || ""}</svg>`;
const depText = x => `${String(x.share).replace(".", ",")} % ${x.type === "debt" ? "de sa dette publique extérieure"
  : x.type === "chips" ? "de la capacité mondiale de production des puces les plus avancées"
  : x.type === "trade" ? (x.direction === "exports" ? "de ses exportations" : "de ses importations de marchandises")
  : "de ses importations " + depWhat(x)} (${x.period || x.year})`;
const depEdges = DEPS.map((x, i) => ({id: "d" + i, from: x.supplier, to: x.from, arrows: {to: {enabled: true, scaleFactor: .9}}, physics: false,
  width: .6 + x.share/25, dashes: DEP.dashes, color: {color: DEP.color, opacity: .9}, smooth: {type: "curvedCW", roundness: .25}, hidden: true,
  title: `${(D.actors[x.from]||{}).name} dépend de ${(D.actors[x.supplier]||{}).name} : ${depText(x)}`}));
const depsVisible = () => DEPS.map((x, i) => ({id: "d" + i, hidden: !depOn(x)}));
const supportsVisible = () => D.edges.map((e,i) => ({id:"e"+i, hidden: !activeAt(e, YEAR()) || !supportOn(e)}));

// ---------- Glossaire : un terme, une définition (glossaire.yaml) ; infobulle commune à tout le site (style.py) ----------
const GL = D.glossary || {};
const T = (id, text) => GL[id] ? `<a class="term" href="glossaire.html#${id}" target="_blank" rel="noopener" data-term="${esc(GL[id].term)}" data-def="${esc(GL[id].def)}">${text ?? esc(GL[id].term)}</a>` : (text ?? id);
const Q = id => GL[id] ? `<a class="term q" href="glossaire.html#${id}" target="_blank" rel="noopener" aria-label="Définition : ${esc(GL[id].term)}" data-term="${esc(GL[id].term)}" data-def="${esc(GL[id].def)}">?</a>` : "";

// ---------- Légende-filtres (barre de gauche) : soutiens, tensions, acteurs ----------
const TYPES_FR = {arms:"armes", troops:"troupes", financial:"argent", training:"entraînement", intelligence:"renseignement",
  political:"politique", economic:"économique", dual_use:"double usage", service:"service stratégique"};
const TYPE_TERM = {dual_use:"double-usage"}, TENSION_TERM = {war:"guerre", sanctions:"sanctions", claims:"revendication", rivalry:"rivalite", trade_war:"guerre-commerciale", blockade:"entrave-navigation"};
// vue simplifiée par défaut (lisible au premier coup d'œil) ; « tout afficher » en un clic
// (moins de 15 relations : les guerres et les troupes engagées ; les questions en haut de la vue mènent plus loin)
const SIMPLE = {type: ["troops"], tension: ["war"], kind: ["core", "non_state"], med: [], dep: []};
// échantillon de trait : mêmes couleur, épaisseur, tirets et flèche que le dessin
const stroke = (color, {w=2, dash=null, arrow=true, op=1} = {}) => `<svg width="34" height="12" viewBox="0 0 34 12" aria-hidden="true">
  <line x1="2" y1="6" x2="${arrow ? 26 : 32}" y2="6" stroke="${color}" stroke-width="${w}" stroke-opacity="${op}" ${dash ? `stroke-dasharray="${dash}"` : ""}/>
  ${arrow ? `<path d="M25 2 32 6 25 10Z" fill="${color}" fill-opacity="${op}"/>` : ""}</svg>`;
const glyph = k => k==="core"
  ? '<svg width="34" height="16" viewBox="0 0 34 16" aria-hidden="true"><circle cx="17" cy="8" r="6.5" fill="none" stroke="currentColor" stroke-width="1.4"/><path d="M11 8h12" stroke="currentColor" stroke-width="1.2"/></svg>'
  : `<svg width="34" height="16" viewBox="-5 0 34 24" aria-hidden="true"><g fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">${GLYPH[k]}</g></svg>`;
(() => { const box = $("#rel-filters");
  const row = (g, v, sample, label, q="") => `<label><input type="checkbox" autocomplete="off" data-g="${g}" value="${v}"${SIMPLE[g].includes(v) ? " checked" : ""}>${sample}${esc(label)}${q}</label>`;
  const head = (title, g) => `<div class="fg-h"><b>${title}</b><span><button type="button" data-all="${g}">tout</button> · <button type="button" data-none="${g}">aucun</button></span></div>`;
  box.innerHTML = `<div class="fg">${head(`Soutiens${Q("soutien")}`, "type")}
    ${Object.keys(D.colors).map(k => row("type", k, stroke(D.colors[k]), TYPES_FR[k] || k, TYPE_TERM[k] ? Q(TYPE_TERM[k]) : "")).join("")}
    <div class="note">A ${stroke("currentColor")} B : A soutient B</div>
    <div class="sub">Statut${Q("statut")}</div>
    <div class="note">${stroke("currentColor")} actif</div>
    <div class="note">${stroke("currentColor", {dash:"4 3"})} en baisse ou ${T("allegue", "allégué")}</div>
    <div class="sub">Confiance${Q("confiance")}</div>
    <div class="note">${stroke("currentColor", {w: WIDTH.high})} élevée : documenté officiellement</div>
    <div class="note">${stroke("currentColor", {w: WIDTH.medium})} moyenne : sources concordantes</div>
    <div class="note">${stroke("currentColor", {w: WIDTH.low})} faible : allégations</div></div>
  <div class="fg" style="margin-top:14px">${head(`Tensions${Q("tension")}`, "tension")}
    ${Object.entries(TENSION).map(([k,t]) => row("tension", k, stroke(t.color, {w: Math.min(t.width, 3), dash: t.dashes ? t.dashes.join(" ") : null, arrow: !!t.arrows}), t.label, Q(TENSION_TERM[k]))).join("")}
    <div class="note">${stroke("currentColor", {dash:"2 5", arrow:false, op:.55})} pâle : ${T("cessez-le-feu", "trêve ou cessez-le-feu")}</div></div>
  <div class="fg" style="margin-top:14px"><div class="fg-h"><b>Leviers${Q("levier")}</b></div>
    ${row("dep", "on", stroke(DEP.color, {w: 2, dash: DEP.dashes.join(" ")}), "dépendance chiffrée (épaisseur = part)")}</div>
  <div class="fg" style="margin-top:14px"><div class="fg-h"><b>Médiations${Q("mediation")}</b></div>
    ${row("med", "on", stroke(MED.color, {w: MED.width, dash: MED.dashes.join(" "), arrow: false}), "négocie entre deux camps")}</div>
  <div class="fg" style="margin-top:14px">${head(`Acteurs${Q("acteur")}`, "kind")}
    ${row("kind", "core", glyph("core"), "États et blocs (drapeau)")}${row("kind", "non_state", glyph("non_state"), "groupes armés")}
    ${row("kind", "party", glyph("party"), "partis")}${row("kind", "person", glyph("person"), "personnalités, entreprises, passages")}
    <div class="contour graph-only">Couleur du contour : ${T("bloc", "bloc d'influence")}. ${Object.values(BLOCS).map(b =>
      `<span class="key"><i style="background:${b.color}"></i>${esc(b.name)}</span>`).join("")}<span class="key"><i style="background:${CONTESTED}"></i>${T("dispute", "disputé")}</span></div></div>`;
  box.addEventListener("click", ev => { const b = ev.target.closest("button[data-all],button[data-none]"); if(!b) return;
    const g = b.dataset.all || b.dataset.none;
    box.querySelectorAll(`input[data-g="${g}"]`).forEach(i => i.checked = !!b.dataset.all); userChanged(); });
  box.addEventListener("change", userChanged); })();
const setChecks = (g, vals) => document.querySelectorAll(`#rel-filters input[data-g="${g}"]`).forEach(i => i.checked = vals == null || vals.includes(i.value));
const isSimple = () => ["type", "tension", "kind", "med", "dep"].every(g => [...document.querySelectorAll(`#rel-filters input[data-g="${g}"]`)]
  .every(i => i.checked === SIMPLE[g].includes(i.value)));
// vue préréglée en cours (presets.yaml) : ne montrer qu'un groupe d'acteurs et leurs voisins directs
let PRESET = null, AROUND = null;
function computeAround(){ if(!PRESET || !PRESET.around) return AROUND = null;
  const base = new Set(PRESET.around), out = new Set(base), Y = YEAR();
  // question sur le soutien REÇU (panel: received) : on ne garde que ce qui va vers les acteurs de la question, pas ce qu'ils donnent
  const recv = PRESET.panel === "received";
  D.edges.forEach(e => { if(activeAt(e, Y) && supportOn(e) && (base.has(e.to) || (!recv && base.has(e.from)))){ out.add(e.from); out.add(e.to); } });
  TS.forEach(t => { if(activeAt(t, Y) && tensionOn(t) && (base.has(t.from) || base.has(t.to))){ out.add(t.from); out.add(t.to); } });
  // une médiation n'entre que si elle porte sur les acteurs de la question (ses deux parties y sont)
  MEDS.forEach(m => { if(medOn(m) && m.between.every(b => base.has(b))) [m.mediator, ...m.between].forEach(a => out.add(a)); });
  DEPS.forEach(x => { if(depOn(x) && base.has(x.from)){ out.add(x.from); out.add(x.supplier); } });
  return AROUND = out; }
// acteurs reliés par au moins une relation affichée : un acteur isolé par les filtres est masqué (graphe lisible)
let LINKED = null;
function computeLinked(){ const Y = YEAR(), out = new Set();
  D.edges.forEach(e => { if(activeAt(e, Y) && supportOn(e) && visible(layer(e.from)) && visible(layer(e.to))){ out.add(e.from); out.add(e.to); } });
  TS.forEach(t => { if(activeAt(t, Y) && tensionOn(t) && visible(layer(t.from)) && visible(layer(t.to))){ out.add(t.from); out.add(t.to); } });
  MEDS.forEach(m => { if(medOn(m)) [m.mediator, ...m.between].forEach(a => visible(layer(a)) && out.add(a)); });
  DEPS.forEach(x => { if(depOn(x) && visible(layer(x.from)) && visible(layer(x.supplier))){ out.add(x.from); out.add(x.supplier); } });
  return LINKED = out; }
const shown = id => visible(layer(id)) && (!AROUND || AROUND.has(id)) && (!LINKED || LINKED.has(id) || id === FOCUS);
function applyFilters(){
  if(typeof nodesDS === "undefined") return;
  computeAround(); computeLinked(); refresh(); edgesDS.update([...supportsVisible(), ...tensionsVisible(), ...medsVisible(), ...depsVisible()]);
  if(FOCUS) focusGraph(FOCUS);
  if(map && groups){ Object.entries(groups).forEach(([k, g]) => { if(!["core","non_state","party","person"].includes(k)) return;
    visible(k) ? g.addTo(map) : map.removeLayer(g); }); drawLinks(); }
  viewNote(); }
// un changement fait à la main détache l'URL du preset (elle ne décrirait plus la vue affichée)
function userChanged(){ if(PRESET) history.replaceState(null, "", location.pathname + location.hash); applyFilters(); }

const S0 = sizes("military");
const nodesDS = new vis.DataSet(Object.keys(D.actors).map(id=>nodeFor(id, S0[id])));
const edgesDS = new vis.DataSet([...edgeList, ...anchors, ...tensionEdges, ...medEdges, ...depEdges]);
// Disposition calculée UNE fois, hors écran, sur tout le graphe (tous les acteurs, tous les soutiens, toutes années),
// puis figée (physics:false) : un pays garde sa place quels que soient les filtres, rien ne bouge tout seul.
const net = new vis.Network($("#graph"), {nodes:nodesDS, edges:edgesDS},
  // physics:false → pas de courbes « dynamiques » (elles s'appuient sur des points invisibles que seul le moteur physique déplace) :
  // sans cette option, les soutiens passaient tous par un même point. Les tensions, médiations et leviers gardent leur propre courbure.
  {physics:false, interaction:{hover:true}, edges:{smooth:{enabled:true, type:"continuous", roundness:.35}}});
net.on("click", p => p.nodes.length ? show(p.nodes[0]) : legend());
$("#graph").style.visibility = "hidden";
(() => { const box = document.createElement("div");
  box.style.cssText = "position:absolute;left:-9999px;top:0;width:800px;height:600px;visibility:hidden";
  document.body.appendChild(box);
  const lay = new vis.Network(box, {nodes: nodesDS.get().map(n => ({id: n.id, size: n.size, shape: "dot"})),
      edges: [...edgeList, ...anchors].map(e => ({from: e.from, to: e.to}))},
    {layout:{randomSeed:7}, physics:{solver:"forceAtlas2Based", stabilization:{iterations:400, fit:false}}});
  lay.once("stabilizationIterationsDone", () => { const pos = lay.getPositions();
    lay.destroy(); box.remove();
    nodesDS.update(Object.entries(pos).map(([id, p]) => ({id, x: p.x, y: p.y})));
    $("#graph").style.visibility = "";
    net.fit({nodes: nodesDS.get({filter: n => !n.hidden}).map(n => n.id)}); }); })();
// Acteur sélectionné : ses relations (soutiens, tensions, ancrages) et leurs acteurs restent nets, le reste s'estompe.
// Couleurs d'origine gardées pour restaurer ; la couleur d'une relation ne change jamais, seule son opacité baisse.
const DIM = .12, ORIG = Object.fromEntries(edgesDS.get().map(e => [e.id, typeof e.color === "object" ? {...e.color} : {color: e.color, opacity: 1}]));
let FOCUS = null;
function focusGraph(id){ FOCUS = id;
  const core = id ? new Set([id, ...Object.keys(D.actors).filter(m => (D.actors[m].member_of||[]).includes(id))]) : null;
  const shown = edgesDS.get({filter: e => !e.hidden}), near = new Set(core || []);
  const hit = e => !core || core.has(e.from) || core.has(e.to);
  shown.forEach(e => { if(core && hit(e)){ near.add(e.from); near.add(e.to); } });
  edgesDS.update(edgesDS.get().map(e => { const o = ORIG[e.id], on = hit(e);
    return {id: e.id, color: {color: o.color, highlight: o.color, hover: o.color, opacity: on ? o.opacity : DIM},
      ...(e.label ? {font: {...e.font, color: on ? o.color : "transparent"}} : {})}; }));
  nodesDS.update(nodesDS.get().map(n => ({id: n.id, opacity: !core || near.has(n.id) ? 1 : DIM,
    font: {...n.font, color: !core || near.has(n.id) ? fg : "transparent"}}))); }

// ---------- Vue « Organisations » : diagramme d'ensembles (Euler) ----------
// Un cercle par organisation cochée, d'aire proportionnelle à son nombre de membres ; les cercles sont placés pour
// que leurs chevauchements suivent le nombre de membres communs. Chaque pays est posé dans la zone qui correspond
// exactement à ses appartenances (Chine : dans BRICS et OCS, hors OTAN). Contours sans remplissage : aucun mélange.
const VU = 26;
// « Organisation de coopération de Shanghai (OCS) » → « OCS » ; « OTAN (article 5) » → « OTAN »
const shortName = n => { const m = n.match(/^(.*) \(([^)]*)\)$/); return !m ? n : /^[A-ZÉ]{2,6}$/.test(m[2]) ? m[2] : m[1]; };  // côté de la place réservée à un pays, en unités du dessin
function lens(r1, r2, d){ if(d >= r1 + r2) return 0; if(d <= Math.abs(r1 - r2)) return Math.PI*Math.min(r1,r2)**2;
  const a = r1*r1*Math.acos((d*d + r1*r1 - r2*r2)/(2*d*r1)), b = r2*r2*Math.acos((d*d + r2*r2 - r1*r1)/(2*d*r2));
  return a + b - .5*Math.sqrt((-d+r1+r2)*(d+r1-r2)*(d-r1+r2)*(d+r1+r2)); }
function targetDist(r1, r2, area){ let lo = Math.abs(r1 - r2), hi = r1 + r2;   // lens() décroît avec d
  if(area <= 0) return {d: hi + VU*.6, kind: "apart"};
  if(area >= Math.PI*Math.min(r1,r2)**2*.999) return {d: Math.max(0, lo - VU*.6), kind: "inside"};
  for(let k = 0; k < 50; k++){ const m = (lo + hi)/2; lens(r1, r2, m) > area ? lo = m : hi = m; }
  return {d: (lo + hi)/2, kind: "exact"}; }
function eulerLayout(sets){  // sets : [{id, members:Set}]
  const n = sets.length, cell = VU*VU*2.4;
  const C = sets.map((s, i) => ({...s, r: Math.sqrt(Math.max(1, s.members.size)*cell/Math.PI),
    x: 200*Math.cos(2*Math.PI*i/n), y: 200*Math.sin(2*Math.PI*i/n)}));
  const T = [];
  for(let i = 0; i < n; i++) for(let j = i+1; j < n; j++){
    const common = [...C[i].members].filter(m => C[j].members.has(m)).length;
    T.push({i, j, ...targetDist(C[i].r, C[j].r, common*cell)}); }
  for(let it = 0; it < 600; it++){ const lr = .12*(1 - it/700);   // descente de gradient sur l'écart aux distances cibles
    for(const t of T){ const a = C[t.i], b = C[t.j], dx = b.x - a.x, dy = b.y - a.y, d = Math.hypot(dx, dy) || .01;
      // cercles disjoints : rapprochés doucement (pas d'espace perdu) ; inclus : libres à l'intérieur
      let e = d - t.d; if(t.kind==="apart" && e > 0) e *= .15; if(t.kind==="inside" && e < 0) e = 0;
      const ux = dx/d*e*lr, uy = dy/d*e*lr; a.x += ux; a.y += uy; b.x -= ux; b.y -= uy; } }
  return C; }
// Placement dans la zone EXACTE de chaque pays (cercle privé de ses intersections), en occupant toute la surface de
// cette zone : graines « le plus loin possible », puis relaxation de Lloyd (chaque pays glisse vers le centre de la part
// de zone la plus proche de lui). Ancienne version : l'écart entre pays était plafonné, d'où des pays entassés au centre
// de leur zone et des cercles à moitié vides.
function placeCountries(C, all, R){  // {iso: {x, y, ok, r}} ; ok = false si la zone exacte n'existe pas dans le dessin
  const minX = Math.min(...C.map(c => c.x - c.r)), maxX = Math.max(...C.map(c => c.x + c.r));
  const minY = Math.min(...C.map(c => c.y - c.r)), maxY = Math.max(...C.map(c => c.y + c.r));
  const pts = [], step = VU/4;
  for(let x = minX; x <= maxX; x += step) for(let y = minY; y <= maxY; y += step){
    const ins = C.map(c => Math.hypot(x - c.x, y - c.y) < c.r);
    if(!ins.some(Boolean)) continue;
    pts.push({x, y, sig: ins.map(Number).join(""), clear: Math.min(...C.map(c => Math.abs(Math.hypot(x - c.x, y - c.y) - c.r)))}); }
  const bySig = {}; all.forEach(iso => { const sig = C.map(c => c.members.has(iso) ? 1 : 0).join("");
    (bySig[sig] = bySig[sig] || []).push(iso); });
  const out = {}, regions = {};
  for(const [sig, isos] of Object.entries(bySig)){
    let cand = pts.filter(p => p.sig === sig && p.clear > VU*.2), ok = cand.length > 0;
    if(!ok) cand = pts.filter(p => p.sig === sig);
    if(!cand.length){ ok = false; const score = p => [...sig].filter((b, k) => b === p.sig[k]).length;   // zone absente : la plus proche
      const best = Math.max(...pts.map(score)); cand = pts.filter(p => score(p) === best && p.clear > VU*.2); }
    isos.sort((a, b) => R[b] - R[a] || cname(a).localeCompare(cname(b)));
    // zone trop petite pour ses drapeaux : on les réduit ensemble (le zoom permet de les lire)
    const need = isos.reduce((t, iso) => t + Math.PI*(R[iso] + VU*.12)**2, 0), have = cand.length*step*step*.78;
    const shrink = need > have ? Math.sqrt(have/need) : 1;
    isos.forEach(iso => R[iso] *= shrink);
    const seeds = [];
    for(const iso of isos){ let best = cand[0], bs = -Infinity;
      for(const p of cand){ const near = seeds.length ? Math.min(...seeds.map(q => Math.hypot(p.x - q.x, p.y - q.y) - q.r)) : VU*9;
        const sc = near + Math.min(p.clear - R[iso], VU)*.35; if(sc > bs){ bs = sc; best = p; } }
      seeds.push({iso, x: best.x, y: best.y, r: R[iso]}); }
    for(let it = 0; it < 12; it++){   // Lloyd pondéré : un grand drapeau garde une plus grande part de zone
      const acc = seeds.map(() => ({x: 0, y: 0, n: 0}));
      for(const p of cand){ let bi = 0, bd = Infinity;
        seeds.forEach((q, i) => { const d = (p.x - q.x)**2 + (p.y - q.y)**2 - q.r*q.r; if(d < bd){ bd = d; bi = i; } });
        acc[bi].x += p.x; acc[bi].y += p.y; acc[bi].n++; }
      seeds.forEach((q, i) => { if(acc[i].n){ q.x = acc[i].x/acc[i].n; q.y = acc[i].y/acc[i].n; } }); }
    seeds.forEach(q => out[q.iso] = {x: q.x, y: q.y, ok, r: q.r});
    regions[sig] = {isos, ok, shrink, x: seeds.reduce((t, q) => t + q.x, 0)/seeds.length, y: seeds.reduce((t, q) => t + q.y, 0)/seeds.length}; }
  return {P: out, regions}; }

// ---------- Rendu du diagramme, avec zoom et déplacement ----------
// Le calcul (cercles, placement) est fait une fois par sélection ; le rendu est refait à chaque zoom : les textes gardent
// une taille constante à l'écran, et les noms qui chevaucheraient un drapeau ou un autre nom sont masqués (nom au survol),
// jamais tronqués. Zone trop serrée (plus de VMAX pays, drapeaux réduits de plus de 40 %) : les plus petits sont regroupés
// en une pastille « +N », dont la liste s'ouvre dans le panneau de droite.
const VMAX = 24;
let VENN = null, VZ = {k: 1, x: 0, y: 0};
function drawVenn(){ const box = $("#venn"); if(!document.body.classList.contains("venn")) return;
  const Y = YEAR(), sets = [...SEL.keys()].map(id => ({id, members: new Set(membersAt(GROUPS[id], Y))}));
  if(sets.length < 2){ VENN = null; box.innerHTML = `<p class="venn-empty mute">Coche au moins deux organisations dans les filtres, à gauche :
    chacune devient un cercle, et chaque pays se place à l'intersection des organisations dont il est membre.</p>`; return; }
  const C = eulerLayout(sets), all = [...new Set(sets.flatMap(s => [...s.members]))];
  // taille des drapeaux : valeur choisie dans les filtres, relative au plus grand pays affiché (aire ∝ valeur)
  const m = $("#metric").value, V = Object.fromEntries(all.map(iso => [iso, metricOf(iso, m)]));
  const vmax = Math.max(...Object.values(V).filter(v => v), 1);
  const R = Object.fromEntries(all.map(iso => [iso, m==="none" ? VU*.36 : V[iso] ? VU*(.14 + .66*Math.sqrt(V[iso]/vmax)) : VU*.12]));
  const {P, regions} = placeCountries(C, all, R);
  const hidden = new Set(), pills = [];
  Object.entries(regions).forEach(([sig, r]) => { if(r.isos.length > VMAX && r.shrink < .6){ const rest = r.isos.slice(VMAX);
    rest.forEach(iso => hidden.add(iso)); pills.push({sig, n: rest.length, x: r.x, y: r.y, isos: r.isos}); } });
  const cross = new Set(all.filter(iso => sets.filter(s => s.members.has(iso)).length > 1));
  VENN = {sets, C, all, P, R, m, hidden, pills, cross};
  if(!box.querySelector(".vz")) box.innerHTML = `<div class="vsvg"></div>
    <div class="vz"><button type="button" data-z="in" title="Zoomer" aria-label="Zoomer">+</button><button type="button" data-z="out" title="Dézoomer" aria-label="Dézoomer">−</button>
    <button type="button" data-z="reset" title="Réinitialiser la vue" aria-label="Réinitialiser la vue">⤢</button></div><p class="venn-note mute"></p>`;
  VZ = {k: 1, x: 0, y: 0};
  renderVenn(); }
function renderVenn(){ const box = $("#venn"), svgBox = box.querySelector(".vsvg"); if(!VENN || !svgBox) return;
  const {sets, C, all, P, R, m, hidden, pills, cross} = VENN, hl = PRESET && PRESET.highlight === "crossing";
  const W = Math.max(200, box.clientWidth - 24), H = Math.max(200, box.clientHeight - 40);
  const bx0 = Math.min(...C.map(c => c.x - c.r)), bx1 = Math.max(...C.map(c => c.x + c.r));
  const by0 = Math.min(...C.map(c => c.y - c.r)), by1 = Math.max(...C.map(c => c.y + c.r));
  const pad = 70, k0 = Math.min(W/(bx1 - bx0 + 2*pad), H/(by1 - by0 + 2*pad)), k = k0*VZ.k, px = v => v/k;
  const cx = (bx0 + bx1)/2 + VZ.x, cy = (by0 + by1)/2 + VZ.y, vw = W/k, vh = H/k;
  const boxes = [];   // obstacles déjà posés (drapeaux, noms), en unités du dessin
  const hit = b => boxes.some(o => b.x0 < o.x1 && b.x1 > o.x0 && b.y0 < o.y1 && b.y1 > o.y0);
  const shownIsos = all.filter(iso => !hidden.has(iso)).sort((a, b) => R[b] - R[a]);
  shownIsos.forEach(iso => { const p = P[iso], f = R[iso]; boxes.push({x0: p.x - f, x1: p.x + f, y0: p.y - f, y1: p.y + f}); });
  // noms des organisations : sur l'arc extérieur, à l'angle le moins encombré (de préférence en haut)
  const tw = t => px(t.length*7.4 + 6);
  const orgLabels = [...C].sort((a, b) => b.r - a.r).map(c => { const text = `${shortName(GROUPS[c.id].name)} (${c.members.size})`, w = tw(text), h = px(16);
    let best = null, bs = Infinity;
    for(let a = -90; a < 270; a += 10){ const t = a*Math.PI/180, d = c.r + px(12);
      const x = c.x + Math.cos(t)*(d + w/2*Math.abs(Math.cos(t))), y = c.y + Math.sin(t)*(d + h/2*Math.abs(Math.sin(t)));
      const b = {x0: x - w/2, x1: x + w/2, y0: y - h/2, y1: y + h/2};
      const inside = C.filter(o => o !== c && Math.hypot(Math.max(b.x0 - o.x, 0, o.x - b.x1), Math.max(b.y0 - o.y, 0, o.y - b.y1)) < o.r).length;
      const sc = (hit(b) ? 100 : 0) + inside*40 + Math.abs(a + 90)/30;
      if(sc < bs){ bs = sc; best = {x, y, b}; } }
    boxes.push(best.b);
    return `<text x="${best.x.toFixed(1)}" y="${(best.y + px(5)).toFixed(1)}" fill="${SEL.get(c.id)}" font-weight="600" font-size="${px(13).toFixed(2)}"
      text-anchor="middle" stroke="var(--bg)" stroke-width="${px(4).toFixed(2)}" paint-order="stroke">${esc(text)}</text>`; }).join("");
  // noms des pays : sous le drapeau, seulement s'ils ne touchent rien (sinon au survol)
  const labelOf = {};
  shownIsos.forEach(iso => { const p = P[iso], f = R[iso], name = (D.actors[iso]||{}).name || (D.geo[iso]||{}).name || iso;
    const w = px(name.length*5.6 + 4), y = p.y + f + px(11), b = {x0: p.x - w/2, x1: p.x + w/2, y0: y - px(9), y1: y + px(3)};
    const own = boxes.findIndex(o => o.x0 === p.x - f && o.y0 === p.y - f);
    const others = boxes.filter((o, i) => i !== own);
    if(!others.some(o => b.x0 < o.x1 && b.x1 > o.x0 && b.y0 < o.y1 && b.y1 > o.y0)){ boxes.push(b); labelOf[iso] = y; } });
  const off = shownIsos.filter(iso => !P[iso].ok);
  svgBox.innerHTML = `<svg viewBox="${(cx - vw/2).toFixed(1)} ${(cy - vh/2).toFixed(1)} ${vw.toFixed(1)} ${vh.toFixed(1)}" preserveAspectRatio="xMidYMid meet" role="img"
      aria-label="Diagramme d'ensembles des organisations cochées">
    <defs><clipPath id="vclip" clipPathUnits="objectBoundingBox"><circle cx=".5" cy=".5" r=".5"/></clipPath></defs>
    ${C.map(c => `<circle cx="${c.x.toFixed(1)}" cy="${c.y.toFixed(1)}" r="${c.r.toFixed(1)}" fill="none" stroke="${SEL.get(c.id)}" stroke-width="${px(2.5).toFixed(2)}"/>`).join("")}
    ${shownIsos.map(iso => { const p = P[iso], f = R[iso], dim = hl && !cross.has(iso);
      return `<g class="vc" data-country="${esc(iso)}" transform="translate(${p.x.toFixed(1)},${p.y.toFixed(1)})"${dim ? ' opacity=".28"' : ""}><title>${cname(iso)} — ${
        sets.filter(s => s.members.has(iso)).map(s => esc(GROUPS[s.id].name)).join(", ")}${m==="none" ? "" : " — " + metricText(iso, m)}${p.ok ? "" : " (zone impossible à dessiner avec des cercles : placé au plus près)"}</title>
        <circle r="${(f + px(1.5)).toFixed(2)}" fill="var(--card)" stroke="${hl && cross.has(iso) ? "var(--fg)" : p.ok ? "var(--line)" : "var(--fg)"}" stroke-width="${px(hl && cross.has(iso) ? 2.5 : 1).toFixed(2)}" ${p.ok ? "" : `stroke-dasharray="${px(2).toFixed(2)} ${px(2).toFixed(2)}"`}/>
        <image href="${flag(iso)}" x="${-f}" y="${-f}" width="${2*f}" height="${2*f}" clip-path="url(#vclip)"/>
        ${labelOf[iso] ? `<text y="${(f + px(11)).toFixed(2)}" text-anchor="middle" font-size="${px(10).toFixed(2)}" fill="var(--fg)"
          stroke="var(--bg)" stroke-width="${px(3).toFixed(2)}" paint-order="stroke">${cname(iso)}</text>` : ""}</g>`; }).join("")}
    ${pills.map(q => `<g class="vc" data-region="${q.sig}" transform="translate(${q.x.toFixed(1)},${q.y.toFixed(1)})"><title>${q.n} autres pays : cliquer pour la liste</title>
      <rect x="${px(-20)}" y="${px(-11)}" width="${px(40)}" height="${px(22)}" rx="${px(11)}" fill="var(--ink)"/>
      <text y="${px(4.5)}" text-anchor="middle" font-size="${px(12).toFixed(2)}" font-weight="600" fill="var(--paper)">+${q.n}</text></g>`).join("")}
    ${orgLabels}
  </svg>`;
  box.querySelector(".venn-note").textContent = (off.length ? `${off.length} pays dans une combinaison que des cercles ne peuvent pas représenter (contour pointillé) : placés dans la zone la plus proche. ` : "")
    + "Molette ou boutons pour zoomer, glisser pour se déplacer."; }
// liste d'une zone regroupée (+N) dans le panneau de droite
function showRegion(sig){ const q = VENN && VENN.pills.find(x => x.sig === sig); if(!q) return;
  const names = VENN.C.filter((c, i) => sig[i] === "1").map(c => esc(GROUPS[c.id].name)).join(", ");
  $("#panel").innerHTML = `<h1>${q.isos.length} pays</h1><div class="mute">Membres de : ${names}</div>
    <p>${q.isos.map(iso => `<a href="#" data-country="${esc(iso)}">${cname(iso)}</a>`).join(", ")}</p>`; }
// zoom (molette, boutons) et déplacement (glisser) ; « ⤢ » revient à la vue d'ensemble
(() => { const box = $("#venn"); let drag = null;
  const zoom = (f, ex, ey) => { const r = box.querySelector("svg"); if(!r || !VENN) return;
    const b = r.getBoundingClientRect(), vb = r.viewBox.baseVal, k = Math.min(b.width/vb.width, b.height/vb.height);
    const mx = ex == null ? 0 : (ex - b.left - b.width/2)/k, my = ey == null ? 0 : (ey - b.top - b.height/2)/k;
    const nk = Math.min(12, Math.max(1, VZ.k*f)), g = 1 - VZ.k/nk;
    VZ = {k: nk, x: VZ.x + mx*g, y: VZ.y + my*g}; if(nk === 1) VZ = {k: 1, x: 0, y: 0}; renderVenn(); };
  box.addEventListener("wheel", ev => { if(!VENN) return; ev.preventDefault(); zoom(ev.deltaY < 0 ? 1.25 : 1/1.25, ev.clientX, ev.clientY); }, {passive: false});
  box.addEventListener("click", ev => { const b = ev.target.closest("button[data-z]");
    if(b){ b.dataset.z === "reset" ? (VZ = {k: 1, x: 0, y: 0}, renderVenn()) : zoom(b.dataset.z === "in" ? 1.5 : 1/1.5); return; }
    const r = ev.target.closest("[data-region]"); if(r) showRegion(r.dataset.region); });
  box.addEventListener("pointerdown", ev => { if(ev.target.closest("button,[data-country],[data-region]") || !VENN) return;
    const r = box.querySelector("svg"); if(!r) return; const b = r.getBoundingClientRect(), vb = r.viewBox.baseVal;
    drag = {x: ev.clientX, y: ev.clientY, vx: VZ.x, vy: VZ.y, k: Math.min(b.width/vb.width, b.height/vb.height)}; box.setPointerCapture(ev.pointerId); });
  box.addEventListener("pointermove", ev => { if(!drag) return;
    VZ = {...VZ, x: drag.vx - (ev.clientX - drag.x)/drag.k, y: drag.vy - (ev.clientY - drag.y)/drag.k}; renderVenn(); });
  box.addEventListener("pointerup", () => drag = null); })();
function refresh(){
  const S = sizes($("#metric").value);
  const sz = id => ["state","bloc"].includes(D.actors[id].kind) ? S[id] : Math.max(S[id], D.actors[id].kind==="person" ? 18 : 14);
  nodesDS.update(Object.keys(D.actors).map(id=>({id, size:sz(id), font:{color:fg, size:11+Math.round(sz(id)/7)},
    hidden: !shown(id)})));
  if(FOCUS) focusGraph(FOCUS); }
$("#metric").addEventListener("change", refresh);
function onYear(){ const Y = YEAR();
  $("#year-label").textContent = String(Y);
  applyFilters();
  drawVenn();
  if($("#layers-panel")) showLayers(); }
$("#year").addEventListener("input", onYear); onYear();
$("#metric").addEventListener("change", () => { drawVenn(); if($("#layers-panel")) showLayers(); });

// ---------- Vue carte : une couche Leaflet par type d'acteur, chacun dans son pays ----------
const WORLD = "https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json";  // Natural Earth, domaine public
const css = v => getComputedStyle(document.documentElement).getPropertyValue(v).trim();
const MAP_LAYERS = ["core", "non_state", "party", "person", "links", "tensions"];
const layerOf = layer;
// légende des couleurs de pays, selon le mode choisi
function mapKey(){ const box = $("#map-key");
  if($("#colormode").value === "votes"){
    box.innerHTML = `<div class="note" style="color:var(--ink)">${T("vote-onu", "Indice de vote à l'ONU")}</div><div class="ramp" style="background:linear-gradient(90deg,${mix(BLOCS.axis.color, css("--land"), .7)},${css("--land")},${mix(BLOCS.west.color, css("--land"), .7)})"></div>
      <div class="ramp-l"><span>vote comme Russie/Chine</span><span>comme France/Allemagne</span></div>
      <div class="note">Plus la couleur est franche, plus le pays penche d'un côté. Pays clairs : entre les deux ou sans donnée.</div>`; return; }
  box.innerHTML = `<div class="note" style="color:var(--ink)">Pays colorés selon leurs ${T("lien-formel", "liens formels")}</div>` + Object.values(BLOCS).map(b => `<div class="note" style="color:var(--ink)">${[3,2,1].map(l =>
      `<i style="display:inline-block;width:12px;height:12px;border-radius:2px;background:${mix(b.color, css("--land"), TINT[l])}"></i>`).join("")} ${esc(b.name)}</div>`).join("")
    + `<div class="note" style="color:var(--ink)"><i style="display:inline-block;width:12px;height:12px;border-radius:2px;background:${mix(CONTESTED, css("--land"), .45)}"></i> ${T("dispute", "disputé")}</div>
      <div class="note"><span>Du plus foncé au plus clair : ${T("defense-mutuelle")}, ${T("partenariat-strategique")}, ${T("lien-partiel", "lien partiel")} (${T("niveau", "niveaux")} 3, 2, 1).</span></div>`; }

// Position : coords explicites (bloc), sinon coordonnées Wikidata du pays ; les acteurs rattachés
// à un même pays sont disposés en couronne autour de lui pour ne pas se superposer.
const POS = (() => {
  const geo = iso => { const g = D.geo[iso]; return g ? [g.lat, g.lon] : null; };
  const pos = {}, around = {};
  for(const [id,a] of Object.entries(D.actors)){
    if(a.coords) pos[id] = a.coords;
    else if(a.kind==="state") pos[id] = geo(id);
    else if(a.base) (around[a.base] = around[a.base] || []).push(id); }
  for(const [iso, ids] of Object.entries(around)){ const c = geo(iso); if(!c) continue;
    ids.forEach((id,i) => { const t = 2*Math.PI*i/ids.length - Math.PI/2, r = 3.2 + ids.length*0.3;
      pos[id] = [c[0] + r*Math.sin(t), c[1] + r*Math.cos(t)/Math.cos(c[0]*Math.PI/180)]; }); }
  return pos; })();

// Un contour qui franchit le 180e méridien (Russie, Fidji) est tracé d'un bord à l'autre de la carte :
// on décale ses longitudes négatives de +360° pour qu'il reste d'un seul tenant.
function fixAntimeridian(f){
  const fixRing = r => r.some((p,i) => i && Math.abs(p[0]-r[i-1][0]) > 180) ? r.map(([x,y]) => [x<0 ? x+360 : x, y]) : r;
  const g = f.geometry;
  if(g.type==="Polygon") g.coordinates = g.coordinates.map(fixRing);
  if(g.type==="MultiPolygon") g.coordinates = g.coordinates.map(poly => poly.map(fixRing));
  return f; }
function icon(id, px){ const a = D.actors[id], c = DETAIL.has(a.kind) ? "#6b4fbb" : blocColor(id);
  const ring = c ? `box-shadow:0 0 0 ${a.kind==="person" ? 2 : 1 + (inf(id).level || 1)}px ${c},0 1px 4px #0006` : "";
  return L.divIcon({className:"", iconSize:[px,px], iconAnchor:[px/2,px/2],
    html: `<div class="mk ${a.kind}" style="width:${px}px;height:${px}px"><img src="${picOf(id)}" alt="" style="object-fit:cover;${ring}"></div>`}); }
function drawMarkers(){
  const S = sizes("military");  // carte : taille = dépenses militaires (le choix de taille est propre au graphe)
  for(const k of ["core","non_state","party","person"]) groups[k].clearLayers();
  for(const [id, p] of Object.entries(POS)){ if(!p) continue;
    const k = D.actors[id].kind, px = ["state","bloc"].includes(k) ? Math.round(S[id]*0.9) : k==="person" ? 30 : 22;
    L.marker(p, {icon: icon(id, px), riseOnHover:true}).bindTooltip(D.actors[id].name, {direction:"top", offset:[0,-px/2]})
      .on("click", () => show(id)).addTo(groups[layerOf(id)]); } }
// Liens courbes (Bézier quadratique) ; un lien n'est tracé que si ses deux extrémités sont affichées
function curve(a, b){ const mx=(a[0]+b[0])/2, my=(a[1]+b[1])/2, dx=b[0]-a[0], dy=b[1]-a[1];
  const c = [mx - dy*0.18, my + dx*0.18];
  return Array.from({length:25}, (_,i) => { const t=i/24, u=1-t;
    return [u*u*a[0]+2*u*t*c[0]+t*t*b[0], u*u*a[1]+2*u*t*c[1]+t*t*b[1]]; }); }
function drawLinks(){
  drawTensions();
  groups.links.clearLayers(); linkLayers = [];
  const on = k => map.hasLayer(groups[k]);
  D.edges.filter(e => activeAt(e, YEAR())).forEach(e => {
    const a = POS[e.from], b = POS[e.to];
    if(!a || !b || !supportOn(e) || !on(layerOf(e.from)) || !on(layerOf(e.to))) return;
    const l = L.polyline(curve(a,b), {color: D.colors[e.types[0]]||"#888", weight: WIDTH[e.confidence] || 1.4,
      opacity:.8, dashArray: DASHED(e) ? "5 5" : null})
      .bindTooltip(`${D.actors[e.from].name} → ${D.actors[e.to].name} : ${e.types.join(", ")} (${datedDoc(e)})`, {sticky:true})
      .addTo(groups.links);
    // flèche : petit cercle plein côté bénéficiaire
    const tip = L.circleMarker(b, {radius:3, color: D.colors[e.types[0]]||"#888", fillOpacity:1, weight:0, interactive:false}).addTo(groups.links);
    linkLayers.push({e, l, tip}); }); }
// Tensions sur la carte : traits droits, distincts des liens de soutien (courbes)
function drawTensions(){ groups.tensions.clearLayers();
  const on = k => map.hasLayer(groups[k]);
  TS.filter(t => activeAt(t, YEAR())).forEach(t => { const a = POS[t.from], b = POS[t.to], s = TENSION[t.type];
    if(!a || !b || !tensionOn(t) || !on(layerOf(t.from)) || !on(layerOf(t.to))) return;
    L.polyline([a, b], {color:s.color, weight: s.width + .6, opacity: t.status==="active" ? .9 : .45,
      dashArray: t.status!=="active" ? "2 6" : s.dashes ? s.dashes.join(" ") : null})
      .bindTooltip(tensionTitle(t), {sticky:true}).addTo(groups.tensions); }); }
function highlightLinks(id){ linkLayers.forEach(({e,l}) => { const hit = !id || e.from===id || e.to===id;
  l.setStyle({opacity: hit ? .9 : .12, weight: (WIDTH[e.confidence] || 1.4) + (hit && id ? 1.2 : 0)}); }); }

async function initMap(){
  map = L.map("map", {worldCopyJump:true, minZoom:2, maxZoom:7, zoomSnap:0.5, zoomControl:false})
    .setView([30, 25], 2.5);
  L.control.zoom({position:"bottomright"}).addTo(map);
  map.attributionControl.setPrefix(false).addAttribution("Fonds de carte : Natural Earth (domaine public) via world-atlas");
  const topo = await fetch(WORLD).then(r => r.json());
  const world = topojson.feature(topo, topo.objects.countries);
  world.features = world.features.filter(f => f.id !== "010").map(fixAntimeridian);  // sans l'Antarctique
  const byNum = Object.fromEntries(Object.entries(D.geo).filter(([_,g]) => g.iso_numeric)
    .map(([iso,g]) => [String(+g.iso_numeric), iso]));
  const formalTip = iso => `${cname(iso)}${blocColor(iso) ? " — " + (inf(iso).role==="contested" ? "disputé" : esc(BLOCS[inf(iso).bloc].name) + (inf(iso).role==="member" ? `, niveau ${inf(iso).level}/3` : ", satellite")) : ""}`;
  const votesTip = iso => leanAt(iso) == null ? `${cname(iso)} — pas de données de vote pour ${voteYear()}`
    : voteYear() === U.agreement_year && UC[iso] ? `${cname(iso)} — vote comme France/Allemagne ${pct(UC[iso].west)}, comme Russie/Chine ${pct(UC[iso].axis)} (${U.agreement_year})`
    : `${cname(iso)} — ${leanText(leanAt(iso)).toLowerCase()} en ${voteYear()}`;
  const style = f => { const iso = byNum[String(+f.id)], votes = $("#colormode").value==="votes";
    const c = iso && (votes ? votesColor(iso) : blocColor(iso) && mix(blocColor(iso), css("--land"), TINT[inf(iso).level] || .25));
    return {color: css("--line"), weight: .6, fillOpacity: 1,
            fillColor: c || (iso && D.actors[iso] ? css("--land-hl") : css("--land"))}; };
  countries = L.geoJSON(world, {style,
    onEachFeature: (f, l) => { const iso = byNum[String(+f.id)];
      if(!iso) return;
      l.bindTooltip(() => ($("#colormode").value==="votes" ? votesTip : formalTip)(iso), {sticky:true});
      l.on("click", () => D.actors[iso] ? show(iso) : showCountry(iso)); }
  }).addTo(map);
  $("#colormode").addEventListener("change", () => { countries.setStyle(style); mapKey(); }); mapKey();
  $("#year").addEventListener("input", () => { countries.setStyle(style); drawLinks(); });
  // calques : acteurs selon les cases « Acteurs » ; soutiens et tensions filtrés trait par trait dans drawLinks
  groups = Object.fromEntries(MAP_LAYERS.map(k => [k, L.layerGroup()]));
  MAP_LAYERS.forEach(k => (k==="links" || k==="tensions" || visible(k)) && groups[k].addTo(map));
  drawMarkers(); drawLinks(); }

function setView(v){
  document.body.classList.toggle("map", v==="map"); document.body.classList.toggle("venn", v==="venn");
  // vue courante signalée dans le contrôle segmenté (seul moyen de changer de vue)
  const anchor = {graph:"graphe", map:"carte", venn:"organisations"}[v];
  document.querySelectorAll("#views a").forEach(a => a.dataset.view === anchor ? a.setAttribute("aria-current", "page") : a.removeAttribute("aria-current"));
  if(v!=="venn" && $("#layers-panel")) legend();
  const sup = $('#metric option[value="supports"]'); sup.hidden = sup.disabled = v==="venn";
  if(v==="venn" && $("#metric").value==="supports"){ $("#metric").value = "military"; refresh(); }
  if(v==="map"){ if(!map) initMap(); else map.invalidateSize(); }
  if(v==="venn"){
    // première visite : une sélection parlante plutôt qu'une liste vide
    if(!SEL.size) document.querySelectorAll("#orgs input").forEach(i => i.checked = ["nato","eu","brics","sco"].includes(i.value));
    if(!SEL.size) syncOrgs(); else { drawVenn(); showLayers(); } } }
// barres latérales repliables (filtres à gauche, détails à droite) ; la carte, le graphe et les cercles se recalent
function sidebar(box, btn, key, def=false){
  const set = closed => { box.classList.toggle("closed", closed); btn.setAttribute("aria-expanded", String(!closed));
    btn.title = closed ? "Déplier" : "Replier";
    try { localStorage.setItem(key, closed ? "1" : "0"); } catch(_) {}
    if(map) map.invalidateSize(); drawVenn(); };
  let closed = def; try { const v = localStorage.getItem(key); if(v === "1" || v === "0") closed = v === "1"; } catch(_) {}
  if(closed) set(true);
  btn.addEventListener("click", ev => { ev.stopPropagation(); set(!box.classList.contains("closed")); });
  box.addEventListener("click", () => { if(box.classList.contains("closed")) set(false); });  // bande repliée : cliquable en entier
  return set; }
sidebar($("#controls"), $("#ctl-toggle"), "filters-closed", true);
const openSide = sidebar($("#side"), $("#side-toggle"), "details-closed");


function f(v, unit="", d=1){ if(!v) return "n/d"; let x=v.value, s;
  s = Math.abs(x)>=1e9 ? (x/1e9).toFixed(d)+" Md" : Math.abs(x)>=1e6 ? (x/1e6).toFixed(d)+" M" : x.toLocaleString("fr-FR",{maximumFractionDigits:d});
  return `${s}${unit} <span class="mute">(${v.year})</span>`; }
const tags = t => t.map(x=>`<span class="tag" style="background:${D.colors[x]||'#888'}">${esc(x)}</span>`).join("");
// source → lien court vers le site (texte complet au survol) ; sans URL, le texte tel quel
const src = s => { const m = String(s).match(/https?:\/\/[^\s<]+/); if(!m) return esc(s);
  let host = m[0]; try { host = new URL(m[0]).hostname.replace(/^www\./, ""); } catch(_) {}
  return `<a href="${esc(m[0])}" target="_blank" rel="noopener" title="${esc(String(s).slice(0, m.index).replace(/[\s—]+$/, ""))}">${esc(host)}</a>`; };
const STATUS_FR = {active:"actif", reduced:"en baisse", ended:"terminé", alleged:"allégué"};
const CONF_FR = {high:"documenté officiellement", medium:"sources concordantes", low:"allégations"};
const rel = (e, other) => `<div class="rel"><b data-id="${esc(other)}">${nm(other)}</b> <span class="mute">${e.types.map(t => TYPE_TERM[t] ? T(TYPE_TERM[t], esc(TYPES_FR[t])) : esc(TYPES_FR[t] || t)).join(", ")}</span>
  ${e.why ? `<div>${esc(e.why)}</div>` : ""}
  <div class="mute">${T("statut", esc(STATUS_FR[e.status] || e.status))}, ${T("confiance", esc(CONF_FR[e.confidence] || e.confidence))}, ${esc(datedDoc(e))}. ${e.note ? esc(e.note) + ". " : ""}Sources : ${(e.sources||[]).map(src).join(", ")}</div></div>`;
document.addEventListener("click", ev => { const b = ev.target.closest("[data-id]"); if(b) show(b.dataset.id); });


function show(id){
  const a = D.actors[id]||{};
  if(AROUND && !AROUND.has(id)) clearPreset();
  if(!visible(layer(id))){ document.querySelector(`#rel-filters input[data-g="kind"][value="${layer(id)}"]`).checked = true; applyFilters(); }  // ouvrir le calque de l'acteur demandé
  const members = Object.keys(D.actors).filter(m=>(D.actors[m].member_of||[]).includes(id));
  focusGraph(id); if((nodesDS.get(id) || {}).hidden) refresh();   // un acteur choisi reste visible, même sans relation affichée
  net.selectNodes([id, ...members]);
  if($("#side").classList.contains("closed")) openSide(false);
  if(map) highlightLinks(id);
  const iso = (a.kind==="state" || a.kind==="bloc") ? id : a.base;
  const p = D.profiles[iso];
  let h = `<h1>${nm(id)}</h1><div class="mute">${esc(a.kind_label||KIND[a.kind]||a.kind)}${a.base&&a.kind!=="state"?" · "+nm(a.base)+" ("+esc(a.base)+")":""}${(a.member_of||[]).length?" · membre : "+a.member_of.map(nm).join(", "):""}</div>`;
  if(D.people[id]) h = `<img src="${safeUrl(D.people[id].thumb)}" alt="" style="width:72px;height:72px;border-radius:50%;object-fit:cover;float:right;margin-left:10px">` + h;
  h += leaderLine(id);
  if(blocLine(id)) h += `<p class="mute">${blocLine(id)}</p>`;
  if(ungaLine(id)) h += `<p class="mute">${ungaLine(id)}</p>`;
  if(forumLine(id)) h += `<p class="mute">${forumLine(id)}</p>`;
  h += tiers(id) + euCohesion(id) + (id==="US" || id==="EU" ? driftBlock() : "");
  if(a.note) h += `<p>${esc(a.note)}${(a.sources||[]).length?`<br><span class="mute">${a.sources.map(src).join(", ")}</span>`:""}</p>`;
  h += credit(id) + credit(leaderKey(id));
  if(members.length){
    h += `<h2>Membres suivis (${members.length})</h2><p class="mute">Surlignés sur le graphe.</p>` + members.map(m => {
      const out = D.edges.filter(e=>e.from===m && e.status!=="ended");
      return `<div class="rel"><b data-id="${esc(m)}">${nm(m)}</b> <span class="mute">→ ${out.length ? out.map(e=>nm(e.to)).join(", ") : "aucun soutien recensé"}</span></div>`; }).join(""); }
  const local = Object.keys(D.actors).filter(x=>DETAIL.has(D.actors[x].kind) && D.actors[x].base===id);
  if(local.length) h += `<h2>Partis & personnalités</h2>` + local.map(x=>`<div class="rel"><b data-id="${esc(x)}">${nm(x)}</b> <span class="mute">${esc(KIND[D.actors[x].kind])}</span></div>`).join("");
  const out = D.edges.filter(e=>e.from===id&&e.status!=="ended"), inn = D.edges.filter(e=>e.to===id&&e.status!=="ended");
  const hOut = out.length ? `<h2>Soutient</h2>` + out.map(e=>rel(e,e.to)).join("") : "";
  const hIn = inn.length ? `<h2>Soutenu par${Q("soutien")}</h2>` + inn.map(e=>rel(e,e.from)).join("") : "";
  h += PRESET && PRESET.panel === "received" ? hIn + hOut : hOut + hIn;   // la question règle l'ordre : soutien reçu d'abord si elle porte dessus
  const deps = DEPS.filter(x => x.from === id).sort((a, b) => b.share - a.share);
  if(deps.length) h += `<h2>Dépend de${Q("levier")}</h2>` + deps.map(x => `<div class="dep"><div class="dep-h"><b data-id="${esc(x.supplier)}">${nm(x.supplier)}</b>
    <span>${depIcon(x.type)} ${esc(depText(x))}</span></div><div class="bar"><i style="width:${Math.min(100, x.share)}%"></i></div>
    <div class="mute">${x.note ? esc(x.note) + ". " : ""}Source : ${(x.sources||[]).map(src).join(", ")}</div></div>`).join("");
  const supplied = DEPS.filter(x => x.supplier === id).sort((a, b) => b.share - a.share);
  if(supplied.length) h += `<h2>Pays qui dépendent de lui</h2><p class="mute">${supplied.map(x => `<b data-id="${esc(x.from)}">${nm(x.from)}</b> ${depIcon(x.type, 13)} ${esc(depText(x))}`).join(" ; ")}.</p>`;
  const tens = TS.filter(t => (t.from===id || t.to===id) && t.status!=="ended");
  const meds = MEDS.filter(m => m.mediator === id || m.between.includes(id));
  if(meds.length) h += `<h2>Médiations${Q("mediation")}</h2>` + meds.map(m => `<div class="rel">${m.mediator === id
      ? `${m.form === "mission" ? "Mission de paix" : "Médiateur"} entre ${m.between.map(b => `<b data-id="${esc(b)}">${nm(b)}</b>`).join(" et ")}`
      : `<b data-id="${esc(m.mediator)}">${nm(m.mediator)}</b> ${m.form === "mission" ? "déploie une mission de paix, face à" : "négocie avec"} ${m.between.filter(b => b !== id).map(b => `<b data-id="${esc(b)}">${nm(b)}</b>`).join("")}`}
    ${m.why ? `<div>${esc(m.why)}</div>` : ""}<div class="mute">${esc(dated(m))}. ${m.note ? esc(m.note) + ". " : ""}Sources : ${(m.sources||[]).map(src).join(", ")}</div></div>`).join("");
  if(tens.length) h += `<h2>Tensions${Q("tension")}</h2>` + tens.map(t => { const other = t.from===id ? t.to : t.from, s = TENSION[t.type];
    const verb = t.type==="sanctions" ? (t.from===id ? "sanctionne" : "sanctionné par") : t.type==="claims" ? (t.from===id ? "revendique un territoire de" : "territoire revendiqué par")
      : t.type==="blockade" ? (t.from===id ? "entrave la navigation dans" : "navigation entravée par") : s.label + " avec";
    return `<div class="rel"><b style="color:${s.color}">■</b> ${esc(verb[0].toUpperCase() + verb.slice(1))} <b data-id="${esc(other)}">${nm(other)}</b>
      <div class="mute">${t.status==="reduced" ? "trêve ou cessez-le-feu · " : ""}${esc(dated(t))} · ${(t.sources||[]).map(src).join(", ")}${t.note ? "<br>"+esc(t.note) : ""}</div></div>`; }).join("");
  if(p){ const g=p.government||{}, t=p.population_trend, wb=!!p.population;
    if(a.kind!=="state" && a.kind!=="bloc") h += `<h2>Pays d'ancrage : ${nm(iso)}</h2>`;
    if(a.kind!=="bloc") h += `<h2>Régime</h2><div class="kv"><span>Forme</span><span>${esc((g.forms||[]).join(", "))||"n/d"}</span>
      <span>Chef d'État</span><span>${esc((g.head_of_state||[]).join(", "))||"n/d"}</span></div>`;
    h += `${wb ? "" : `<p class="mute">Aucune donnée Banque mondiale pour ce territoire (Taïwan n'y figure pas).</p>`}
    ${!wb ? "" : `<h2>Démographie</h2><div class="kv"><span>Population</span><span>${f(p.population)}</span>
      <span>Tendance</span><span>${t?`${esc(t.label)} (${t.annual_rate_pct>0?"+":""}${t.annual_rate_pct} %/an, ${t.period})${t.below_replacement?"<br>fécondité sous le renouvellement":""}`:"n/d"}</span>
      <span>Fécondité</span><span>${f(p.fertility,"",2)}</span><span>65 ans et +</span><span>${f(p.age65_pct," %")}</span></div>
    <h2>Économie & ressources</h2><div class="kv"><span>PIB</span><span>${f(p.gdp_usd," $")}</span>
      <span>PIB / hab</span><span>${f(p.gdp_per_capita_usd," $",0)}</span>
      <span>Rentes ressources</span><span>${f(p.resource_rents_pct_gdp," % PIB")}</span>
      <span>· pétrole</span><span>${f(p.oil_rents_pct_gdp," %")}</span><span>· gaz</span><span>${f(p.gas_rents_pct_gdp," %")}</span>
      <span>· minerais</span><span>${f(p.mineral_rents_pct_gdp," %")}</span>
      <span>Terres arables</span><span>${f(p.arable_land_pct," %")}</span>
      <span>Eau douce</span><span>${f(p.freshwater_m3_per_capita," m³/hab",0)}</span></div>
    <h2>Technologie & défense</h2><div class="kv"><span>R&D</span><span>${f(p.rd_pct_gdp," % PIB",2)}</span>
      <span>Export high-tech</span><span>${f(p.hightech_exports_pct," %")}</span>
      <span>Internet</span><span>${f(p.internet_users_pct," %")}</span>
      <span>Défense</span><span>${f(p.military_pct_gdp," % PIB")} · ${f(p.military_usd," $")}</span></div>`}
    <p class="mute">Profil du ${esc(p.fetched_at.slice(0,10))} — ${esc(a.kind==="bloc" ? "Banque mondiale WDI (agrégat)" : wb ? p.sources.join(", ") : "Wikidata")}</p>`;
  } else if(iso) h += `<p class="mute">Pas de profil pour ${esc(iso)}.</p>`;
  $("#panel").innerHTML = h;
}
function showCountry(iso){
  if(map) highlightLinks(null);
  const i = inf(iso);
  $("#panel").innerHTML = `<h1>${cname(iso)}</h1><div class="mute">État — hors du graphe de soutiens</div>
    ${blocLine(iso) ? `<p class="mute">${blocLine(iso)}</p>` : ""}
    ${ungaLine(iso) ? `<p class="mute">${ungaLine(iso)}</p>` : ""}
    ${forumLine(iso) ? `<p class="mute">${forumLine(iso)}</p>` : ""}
    ${i.ties.some(t => GROUPS[t].kind!=="forum") ? "<h2>Liens formels</h2>" : ""}` + i.ties.filter(t => GROUPS[t].kind!=="forum").map(t => { const g = GROUPS[t];
      return `<div class="rel"><b>${esc(g.name)}</b> <span class="mute">${g.level ? `niveau ${g.level}/3` : "sans effet sur l'alignement"}
        ${g.note ? "<br>"+esc(g.note) : ""}<br>${g.sources.map(src).join(", ")}</span></div>`; }).join("")
    + `<p class="mute">Ce pays n'a ${i.ties.some(t => GROUPS[t].kind!=="forum") ? "encore" : "ni lien formel dans alignments.yaml, ni"} aucune relation de soutien sourcée dans network.yaml.</p>`; }
function legend(){
  if(map) highlightLinks(null);
  if(FOCUS){ focusGraph(null); refresh(); }
  $("#panel").innerHTML = `<h1>Vue d'ensemble</h1>
  <p>Les ${T("influence", "réseaux d'influence")} : alliances, soutiens et dépendances.</p>
  <p>Pour commencer simplement, lisez un dossier : il raconte un conflit, ses camps et leurs soutiens.</p>
  <div class="dossiers">${(D.dossiers||[]).map(x => `<a class="btn-dossier" href="${esc(x.id)}.html">${esc(x.title)}</a>`).join("")}</div>
  <p>Ou choisissez une question en haut de la vue. Cliquez sur un ${T("acteur")}, un pays ou un lien pour voir ce qui
  les relie, avec les sources.</p>
  <p class="mute">La légende est dans les filtres, à gauche : chaque case affiche ou masque un type de ${T("relation")} ou
  d'acteur. Taille des acteurs : au choix sur le graphe (${T("depenses-militaires")}, ${T("pib")}, population…) ; dépenses
  militaires sur la carte. Les mots soulignés en pointillés renvoient au <a href="glossaire.html" target="_blank" rel="noopener">glossaire</a>.</p>
  <p class="mute" style="margin-top:26px">Blocs, votes à l'ONU, curseur Année, organisations : tout est expliqué dans la
  <a href="methode.html">méthode</a>. Données réutilisables : <a href="network.json">JSON</a>, <a href="network.csv">CSV</a>
  (CC BY 4.0). Mis à jour le ${esc(D.built.slice(0,10).split("-").reverse().join("/"))}.</p>
  <p class="mute">Une erreur, une source manquante ? <a href="${safeUrl(D.correction)}" target="_blank" rel="noopener">Proposer une correction</a>
  (formulaire guidé, sans connaître le code ; compte GitHub gratuit).</p>`; }
legend();
new ResizeObserver(() => { $("#stage").style.setProperty("--bar", $("#stagebar").offsetHeight + "px");
  if(map) map.invalidateSize(); }).observe($("#stagebar"));
// ---------- Vues préréglées (presets.yaml) : une question, un état complet, une URL (?vue=<id>) ----------
const PRESETS = D.presets || [], VIEW_OF = {carte:"map", organisations:"venn", graphe:"graph"};
// chaque question appartient à un onglet et ne s'affiche que dans celui-ci : elle ne change jamais d'onglet
const TAB = () => document.body.classList.contains("map") ? "carte" : document.body.classList.contains("venn") ? "organisations" : "graphe";
function renderPresets(){ const tab = TAB(), list = PRESETS.filter(p => p.view === tab), on = PRESET && PRESET.view === tab;
  $("#qmenu").hidden = !list.length;
  $("#presets").innerHTML = list.map(p => `<a role="menuitem" href="?vue=${esc(p.id)}#${esc(p.view)}" data-preset="${esc(p.id)}"${PRESET && PRESET.id === p.id ? ' aria-current="true"' : ""}>${esc(p.question)}</a>`).join("");
  $("#qbtn").innerHTML = `<span>${on ? esc(PRESET.question) : `Questions (${list.length})`}</span>`;
  $("#qbtn").classList.toggle("on", !!on); $("#qclear").hidden = !on; }
const qOpen = open => { $("#presets").hidden = !open; $("#qbtn").setAttribute("aria-expanded", String(open)); };
$("#qbtn").addEventListener("click", () => { qOpen($("#presets").hidden); if(!$("#presets").hidden) ($("#presets a[aria-current]") || $("#presets a")).focus(); });
$("#qclear").addEventListener("click", () => { clearPreset(); legend(); renderPresets(); viewNote(); });
$("#presets").addEventListener("click", ev => { const a = ev.target.closest("a[data-preset]"); if(!a) return; ev.preventDefault();
  qOpen(false); history.pushState(null, "", a.getAttribute("href")); route(); });
$("#presets").addEventListener("keydown", ev => { const items = [...$("#presets").querySelectorAll("a")], i = items.indexOf(document.activeElement);
  if(ev.key === "ArrowDown"){ ev.preventDefault(); items[(i + 1) % items.length].focus(); }
  if(ev.key === "ArrowUp"){ ev.preventDefault(); items[(i - 1 + items.length) % items.length].focus(); }
  if(ev.key === "Escape"){ qOpen(false); $("#qbtn").focus(); } });
document.addEventListener("click", ev => { if(!ev.target.closest("#qmenu")) qOpen(false); });
function applyPreset(p){ PRESET = p;
  setChecks("type", p.types); setChecks("tension", p.tensions); setChecks("kind", p.kinds || SIMPLE.kind); setChecks("med", p.mediations ? ["on"] : []); setChecks("dep", p.dependencies ? ["on"] : []);
  if(p.colormode){ $("#colormode").value = p.colormode; $("#colormode").dispatchEvent(new Event("change")); }
  if(p.orgs){ document.querySelectorAll("#orgs input").forEach(i => i.checked = p.orgs.includes(i.value)); SEL.clear(); syncOrgs(); }
  setView(VIEW_OF[p.view]); applyFilters(); renderPresets();
  document.querySelectorAll("#presets a").forEach(a => a.dataset.preset === p.id ? a.setAttribute("aria-current", "true") : a.removeAttribute("aria-current"));
  if(p.focus && D.actors[p.focus]) show(p.focus); else legend();
  viewNote();
  // cadrage sur les acteurs affichés, une fois le graphe stabilisé
  const fit = () => net.fit({nodes: nodesDS.get({filter: n => !n.hidden}).map(n => n.id), animation: {duration: 500}});
  if(p.view === "graphe"){ fit(); setTimeout(fit, 900); }
  if(p.view === "carte" && map) map.setView([30, 20], 2); }
// quitter une vue préréglée : ses filtres n'étaient pas des choix du lecteur, on revient à la vue simplifiée
function clearPreset(){ if(!PRESET) return; PRESET = null; AROUND = null;
  ["type", "tension", "kind", "med", "dep"].forEach(g => setChecks(g, SIMPLE[g]));
  document.querySelectorAll("#presets a[aria-current]").forEach(a => a.removeAttribute("aria-current"));
  history.replaceState(null, "", location.pathname + location.hash); applyFilters(); drawVenn(); renderPresets(); }
// ce qui est affiché, et comment en sortir en un clic
function viewNote(){ const box = $("#viewnote"); if(!box) return;
  if(PRESET){ box.innerHTML = ""; return; }   // la question active est affichée dans le bouton, avec sa croix
  if(document.body.classList.contains("venn")){ box.innerHTML = ""; return; }
  box.innerHTML = isSimple() ? `Vue simplifiée : guerres et troupes. <button type="button" data-note="all">Tout afficher</button>`
    : `<button type="button" data-note="simple">Revenir à la vue simplifiée</button>`; }
$("#viewnote").addEventListener("click", ev => { const b = ev.target.closest("button[data-note]"); if(!b) return;
  if(b.dataset.note === "all"){ setChecks("type", null); setChecks("tension", null); setChecks("med", null); setChecks("dep", null); userChanged(); return; }
  clearPreset(); ["type", "tension", "kind", "med", "dep"].forEach(g => setChecks(g, SIMPLE[g])); legend(); applyFilters(); });

// Liens directs (accueil, dossiers, contrôle segmenté) : #graphe, #carte, #organisations, #graphe:<id acteur>,
// et ?vue=<preset> ; aussi quand on est déjà sur la page (l'ancre change sans recharger)
function route(){ const q = new URLSearchParams(location.search).get("vue"), p = q && PRESETS.find(x => x.id === q);
  document.querySelectorAll("details.menu[open]").forEach(d => d.open = false);
  if(p){ if(PRESET !== p || location.hash.slice(1).split(":")[0] === p.view) return applyPreset(p); }
  const [v, id] = decodeURIComponent(location.hash.slice(1)).split(":");
  if(PRESET && v !== PRESET.view) clearPreset();   // changer de vue quitte la vue préréglée
  setView(VIEW_OF[v] || "graph");
  if(id && D.actors[id]) show(id);
  renderPresets(); viewNote(); }
route();
addEventListener("hashchange", route);
addEventListener("popstate", route);
</script></body></html>"""

if __name__ == "__main__":
    build()
