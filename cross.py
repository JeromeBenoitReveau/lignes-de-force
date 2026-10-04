"""Page « Croiser » (site/relations.html) : on choisit au moins deux entités (pays, groupe, conflit) et la page dessine
ce que le graphe contient ENTRE elles — tensions, soutiens, médiations, leviers. Aucun texte rédigé : chaque trait
est un fait de network.yaml, affiché avec sa date, son statut et ses sources. Un conflit apporte les acteurs de ses camps.
État dans l'URL (relations.html?e=US,d:ukraine,CN), donc partageable."""
from html import escape as e
import json
import brand, dossier, glossary, style

CSS = """
/* page plus large que le reste du site : le schéma et son panneau de détail tiennent côte à côte */
.wrap{max-width:1280px}
.cross{padding:40px 0 0}.cross h1{margin-bottom:8px}
/* une sélection est en cours : l'en-tête se resserre pour que le schéma tienne dans la fenêtre */
.cross.has{padding-top:18px}.cross.has h1{font-size:26px;margin:0}.cross.has .lede{display:none}.cross.has .pick{margin-top:10px}
.cols{display:grid;grid-template-columns:minmax(0,1fr);gap:0 28px}
@media (min-width:1000px){.cols{grid-template-columns:minmax(0,1fr) 340px}
  .side{position:sticky;top:10px;align-self:start;max-height:calc(100vh - 20px);overflow:auto}
  .side #detail{border-top:0;border-left:1px solid var(--mist);padding:2px 0 0 20px;margin-top:14px;min-height:240px}}
.pick{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin:22px 0 6px}
.chip{display:inline-flex;align-items:center;gap:7px;padding:5px 6px 5px 10px;border:1px solid var(--mist);border-radius:4px;background:var(--land);font-size:15px}
.chip .dep-ico,#groups .dep-ico{flex:none}
.chip img,.fact img,.ex img{width:16px;height:16px;border-radius:50%;object-fit:cover;box-shadow:0 0 0 1px var(--mist);flex:none}
.chip button{background:none;border:0;color:var(--graphite);cursor:pointer;font-size:16px;line-height:1;padding:2px 4px;border-radius:3px}
.chip button:hover{color:var(--ink)}
#reset{font:14px var(--sans);color:var(--graphite);background:none;border:0;padding:5px 4px;cursor:pointer;text-decoration:underline dashed var(--peach) 1px;text-underline-offset:3px}
#reset:hover{color:var(--ink);text-decoration-style:solid}#reset[hidden]{display:none}
/* choix des entités : UN champ avec propositions au fil de la frappe ; la liste complète par catégorie reste derrière « Voir toute la liste » */
.picker{position:relative}.pick{position:relative;z-index:1002}
#panel{position:absolute;left:0;right:0;top:100%;z-index:1002;border:1px solid var(--mist);border-radius:6px;background:var(--land);padding:14px 16px 6px;margin:8px 0 4px;
  max-height:70vh;overflow:auto;box-shadow:0 12px 32px #0003}
/* voile derrière le panneau ouvert : le reste de la page s'efface, la sélection reste lisible au-dessus */
#veil{position:fixed;inset:0;z-index:1001;background:color-mix(in srgb,var(--paper) 78%,transparent)}
#q{font:15px var(--sans);color:var(--ink);background:var(--paper);border:1px solid var(--graphite);border-radius:4px;padding:6px 10px;flex:1 1 230px;min-width:200px;max-width:360px}
#q:focus{border-color:var(--peach);outline:2px solid color-mix(in srgb,var(--peach) 45%,transparent);outline-offset:1px}
#groups .hits{display:flex;flex-direction:column;gap:2px;margin:0 0 8px}
#groups .hits button{border-color:transparent;padding:7px 9px;font-size:15px;justify-content:flex-start}#groups .hits button small{margin-left:auto;color:var(--graphite);font-size:12.5px;padding-left:12px}
#groups .hits button:hover,#groups .hits button.on{background:color-mix(in srgb,var(--ink) 6%,var(--land));border-color:transparent}
#groups .more{border:0;padding:4px 0;margin:2px 0 8px;color:var(--graphite);text-decoration:underline dashed var(--peach) 1px;text-underline-offset:3px}
/* « En bref » : compte rendu assemblé par gabarits à partir des faits du graphe, chaque morceau ouvre sa fiche */
.brief{margin:16px 0 0;max-width:46em}.brief:empty{display:none}
.brief p{margin:0 0 7px;font-size:15.5px;line-height:1.55}
.brief .bf{cursor:pointer;text-decoration:underline dotted var(--graphite) 1px;text-underline-offset:3px}
.brief .bf:hover,.brief .bf:focus-visible{text-decoration:underline solid var(--peach) 1px}.brief .why{color:var(--graphite)}
/* grand écran : « En bref » vit dans le panneau de DROITE, pour laisser la largeur au schéma ; un clic sur un trait le remplace par la fiche du fait.
   Écran étroit : il reste au-dessus du schéma, et le panneau (sous le schéma) ne le répète pas. */
#detail .brief{margin:0 0 14px}#detail .brief p{font-size:15px}
.back{font:14px var(--sans);color:var(--graphite);background:none;border:0;padding:0;margin:0 0 12px;cursor:pointer;text-decoration:underline dashed var(--peach) 1px;text-underline-offset:3px}
.back::before{content:"‹ "}.back:hover{color:var(--ink);text-decoration-style:solid}
@media (min-width:1000px){.main > #brief{display:none}}
@media (max-width:999px){#detail .brief,.back{display:none}}
#groups h3{font:500 13.5px var(--sans);color:var(--graphite);margin:14px 0 7px}
#groups .g{display:flex;flex-wrap:wrap;gap:6px;margin:0 0 6px}
#groups button{display:inline-flex;align-items:center;gap:6px;text-align:left;font:14px var(--sans);color:var(--ink);background:none;border:1px solid var(--mist);border-radius:4px;padding:4px 9px;cursor:pointer}
#groups button:hover{border-color:var(--peach)}#groups button:disabled{color:var(--graphite);opacity:.45;cursor:default;border-color:var(--mist)}
#groups img{width:15px;height:15px;border-radius:50%;object-fit:cover;box-shadow:0 0 0 1px var(--mist)}
.scope{font-size:13.5px;color:var(--graphite);margin:0;min-height:1.6em}
.scope button{display:inline;text-align:left;background:none;border:0;padding:0;font:inherit;color:inherit;cursor:pointer;text-decoration:underline dashed var(--peach) 1px;text-underline-offset:3px}
.scope button:hover{text-decoration-style:solid}
/* Une forme par rôle : étiquette PLEINE = ce que j'ai choisi ; lien « + » = ce que je peux ajouter ; contrôle segmenté = changer de vue (le seul de la page) */
.chip.res{border-style:dashed;border-color:var(--graphite)}.chip .how{color:var(--graphite);font-size:13.5px}
.chip select{font:13.5px var(--sans);color:var(--ink);background:none;border:0;border-bottom:1px dashed var(--peach);padding:1px 2px;cursor:pointer;max-width:13.5em}
.chip .dep-ico{color:var(--graphite)}
#more{margin:26px 0 0;padding:16px 0 0;border-top:1px solid var(--mist)}#more[hidden]{display:none}
#more h2,.brief h2{font:500 19px/1.3 var(--serif);margin:0 0 8px}
#widen .row{display:grid;grid-template-columns:92px 1fr;gap:2px 10px;align-items:baseline;margin:0 0 4px}
#widen .k{font-size:13.5px;color:var(--graphite)}
.add{display:inline-flex;align-items:center;gap:6px;text-align:left;font:15px var(--sans);color:var(--ink);background:none;border:0;padding:4px 0;margin:0 18px 0 0;cursor:pointer}
.add::before{content:"+";color:var(--peach);font-weight:600}.add:hover{text-decoration:underline solid var(--peach) 1px;text-underline-offset:3px}
.add img{width:15px;height:15px;border-radius:50%;object-fit:cover;box-shadow:0 0 0 1px var(--mist)}.add small{color:var(--graphite);font-size:12.5px}.add .dep-ico{flex:none}
@media (max-width:599px){#widen .row{grid-template-columns:1fr}}
.ex{display:flex;flex-direction:column;gap:10px;margin:28px 0 0;font-size:16px}
.ex a{display:inline-flex;align-items:center;gap:8px;flex-wrap:wrap}
#schema{display:block;width:100%;height:auto;margin:10px 0 0;overflow:visible}
#schema text{font-family:var(--sans);fill:var(--ink)}
#schema .lab{font-size:14px}#schema .val{font-size:12px;fill:var(--ink);font-variant-numeric:tabular-nums}#schema .pill{fill:var(--paper);stroke:var(--mist)}
#schema .hit{stroke:transparent;stroke-width:16;fill:none;cursor:pointer}
#schema .node{cursor:pointer}#schema .ring{fill:var(--land);stroke:var(--mist);stroke-width:1.5}
#schema .node.extra .ring{stroke-dasharray:3 3}#schema .node.on .ring{stroke:var(--peach);stroke-width:2.5}
#schema .ini{font-size:13px;font-weight:600;fill:var(--paper)}
#schema.ghosted .rel{opacity:.18}#schema .gl{font-size:13px;paint-order:stroke;stroke:var(--paper);stroke-width:4px;stroke-linejoin:round}
#schema .rel{transition:opacity .15s}#schema.focus .rel:not(.on){opacity:.14}#schema.focus .node:not(.on){opacity:.35}
.bar{display:flex;justify-content:space-between;align-items:flex-end;gap:12px;margin:14px 0 0;min-height:30px}
/* contrôle segmenté Schéma / Carte : même dessin que celui de la vue d'ensemble (vue-d-ensemble.html) */
.seg{display:inline-flex;flex-wrap:wrap;padding:3px;gap:2px;border:1px solid var(--mist);border-radius:7px;background:var(--land)}
.seg button{display:flex;align-items:center;gap:7px;padding:6px 12px;border:0;border-radius:5px;background:none;font:14px var(--sans);color:var(--graphite);cursor:pointer;white-space:nowrap}
.seg button:hover{color:var(--ink)}.seg button[aria-pressed=true]{background:color-mix(in srgb,var(--ink) 8%,var(--land));color:var(--ink)}
#sens{margin:6px 0 2px}#sens[hidden]{display:none}#sens button{padding:4px 11px;font-size:13.5px}#sens button:disabled{opacity:.45;cursor:default}
.seg .ico{color:var(--peach)}.seg[data-busy] button{cursor:progress}
.stage{position:relative}
#communs{margin:18px 0 6px}#communs h3{margin:22px 0 10px}#communs h3:first-child{margin-top:6px}
.cap{font-size:13.5px;color:var(--graphite);margin:0 0 10px;max-width:46em}
.tw{overflow-x:auto}
.pc{border-collapse:collapse;font-size:14px}
.pc th{font-weight:400;text-align:left;padding:7px 14px 7px 0;white-space:nowrap}
.pc th small{display:block;color:var(--graphite);font-size:12px}
.pc th.c{padding:0 4px 8px;text-align:center;vertical-align:bottom;font-size:12.5px;min-width:74px;white-space:normal}
.pc th.c span{display:flex;flex-direction:column;align-items:center;gap:4px}.pc .rw{display:inline-flex;align-items:center;gap:7px}
.pc img{width:16px;height:16px;border-radius:50%;object-fit:cover;box-shadow:0 0 0 1px var(--mist)}
.pc td{text-align:center;border-top:1px solid var(--mist);padding:7px 4px;font-variant-numeric:tabular-nums}
.pc td.v{border:2px solid var(--paper);border-radius:4px}.pc td.x{color:var(--graphite)}
.pc .dot{display:inline-block;width:11px;height:11px;border-radius:50%;background:var(--ink)}
@media (max-width:599px){.bar{flex-wrap:wrap}#seg{flex-wrap:nowrap}#seg button{padding:6px 9px}
.pc{font-size:13px}.pc th{white-space:normal;padding-right:8px}.pc th.c{min-width:50px;padding:0 2px 8px}.pc td{padding:7px 2px}}
.fr{display:grid;grid-template-columns:minmax(0,300px) minmax(0,1fr);gap:0 18px;align-items:center}
.fr .track{position:relative;height:100%;min-height:38px}
.fr.axis .track{min-height:22px}.fr .yr{position:absolute;top:0;transform:translateX(-50%);font-size:12px;color:var(--graphite);font-variant-numeric:tabular-nums}
.fr .tk{position:absolute;top:0;bottom:0;width:1px;background:var(--mist)}
.fr.row{cursor:pointer;border-top:1px solid var(--mist)}.fr.row:hover .lbl{color:var(--ink)}
.fr .lbl{padding:7px 0;font-size:14px;min-width:0}.fr .lbl .who{display:flex;align-items:center;gap:6px;flex-wrap:wrap;font-weight:600}
.fr .lbl .who .k{font-weight:400;color:var(--graphite)}.fr .lbl img{width:15px;height:15px;border-radius:50%;object-fit:cover;box-shadow:0 0 0 1px var(--mist)}
.fr .lbl small{color:var(--graphite);font-size:12.5px}
.fr .span{position:absolute;right:0;top:50%;height:5px;margin-top:-2.5px;border-radius:3px 0 0 3px}
.fr .span b{position:absolute;left:-5px;top:-3.5px;width:12px;height:12px;border-radius:50%;box-shadow:0 0 0 2px var(--paper)}
#grp{font:14px var(--sans);color:var(--graphite);background:none;border:1px solid var(--mist);border-radius:4px;padding:5px 11px;cursor:pointer;display:inline-flex;align-items:center;gap:7px}
#grp[hidden]{display:none}#grp::before{content:"";width:9px;height:9px;border-radius:50%;border:1.5px solid var(--graphite)}
#grp:hover{border-color:var(--peach);color:var(--ink)}#grp[aria-pressed=true]{color:var(--ink)}#grp[aria-pressed=true]::before{background:var(--peach);border-color:var(--peach)}
#schema .camp .ring{stroke-dasharray:none;stroke-width:2}#schema .more{font-size:11.5px;fill:var(--graphite)}
#zoom{display:flex;gap:4px}#zoom[hidden]{display:none}
#zoom button{font:14px var(--sans);min-width:30px;height:30px;padding:0 9px;color:var(--ink);background:var(--land);border:1px solid var(--mist);border-radius:4px;cursor:pointer}
#zoom button:hover{border-color:var(--peach)}
#schema.map{cursor:grab;touch-action:pan-y;overflow:hidden;background:var(--ocean);border:1px solid var(--mist);border-radius:6px}
#schema .land .c{fill:var(--land);stroke:var(--mist);stroke-width:.6}#schema .land .c.on{fill:color-mix(in srgb,var(--ink) 20%,var(--land))}
#schema.map .lab{font-size:12.5px;paint-order:stroke;stroke:var(--land);stroke-width:3.5px;stroke-linejoin:round}
.legend{display:flex;flex-wrap:wrap;gap:6px 18px;font-size:13px;color:var(--graphite);margin:4px 0 14px}
.legend span{display:inline-flex;align-items:center;gap:7px}.fact p svg{vertical-align:-2px}
#detail{border-top:1px solid var(--mist);padding:16px 0 0;min-height:92px}
.fact{padding:0 0 14px;font-size:15.5px;max-width:46em}
.fact .who{display:flex;align-items:center;gap:7px;flex-wrap:wrap;font-weight:600}
.fact .who .k{font-weight:400;color:var(--graphite)}
.fact p{margin:3px 0 0}.fact .m{font-size:13.5px;color:var(--graphite)}
.all{margin:26px 0 0;border-top:1px solid var(--mist);padding:16px 0 0}
.all summary{cursor:pointer;font:500 19px/1.3 var(--serif)}
.all h3{margin:22px 0 10px}
.none{font-size:15px;color:var(--graphite);margin:18px 0 0;max-width:46em}
"""

# Article de chaque acteur, pour les phrases du compte rendu « En bref » (« les États-Unis dépendent du Canada »).
# Écrit à la main : il ne se devine pas (« Israël », « Cuba », « Taïwan » n'en prennent pas). validate.py signale un acteur absent.
ART = {**dict.fromkeys(("GB DK VE QA GY CA MX BR YE MA somaliland SD RW ML BF NE PK rn hezbollah hamas pij kataib_hezbollah jnim "
                        "polisario fla").split(), "le"),
       **dict.fromkeys("RU CN KP FR SE TR LY SY SO CD MM".split(), "la"),
       **dict.fromkeys("IR UA IN DE AR DZ EG SA ER ET EU UN afd lna m23".split(), "l'"),
       **dict.fromkeys("US NL AE rsf houthis".split(), "les"),
       **dict.fromkeys("IL TW CU OM DJ trump vance musk spacex palantir alshabab".split(), ""),
       "ormuz": "le", "bab_el_mandeb": "le"}

def forms(k, a):
    """Nom court (sans parenthèse) avec son article, et ses formes après « de » et « à »."""
    short, art = a["name"].split(" (")[0], ART.get(k, "")
    if a["kind"] == "passage":   # « le détroit d'Ormuz » : nom commun, minuscule dans une phrase
        short = short[0].lower() + short[1:]
    the = art + short if art.endswith("'") else f"{art} {short}".strip()
    return {"the": the, "de": style.de(the), "a": style.a(the), "pl": art == "les"}

def data(d):
    live = lambda xs: [x for x in xs if x.get("status") != "ended"]
    people = {k: v.get("thumb") for k, v in (d.get("people") or {}).items() if k in d["actors"] and v.get("thumb")}
    # carte : position = le pays (data/geo.json), les coordonnées explicites d'un bloc, ou le pays de rattachement (base)
    pos, num = {}, {}
    for k, a in d["actors"].items():
        g = d["geo"].get(k) or d["geo"].get(a.get("base") or "")
        if a.get("coords"):
            pos[k] = [a["coords"][1], a["coords"][0]]
        elif g:
            pos[k] = [g["lon"], g["lat"]]
        if g and g.get("iso_numeric"):
            num[k] = int(g["iso_numeric"])
    # points communs : organisations (alignments.yaml) et accord de vote deux à deux à l'ONU (sources/unga.py), en ISO2
    states = {k for k, a in d["actors"].items() if a["kind"] == "state"}
    orgs = [{"name": g["name"].split(" (")[0], "full": g["name"], "forum": g.get("kind") == "forum",
             "members": [m for m in g["members"] if m in states]} for g in d["align"]["groups"]]
    by3 = {v["iso3"]: k for k, v in d["geo"].items() if v.get("iso3")}
    unga = d.get("unga") or {}
    agree = {f"{min(by3[a], by3[b])}|{max(by3[a], by3[b])}": v for a, row in (unga.get("pairs") or {}).items()
             for b, v in row.items() if a in by3 and b in by3}
    return {"actors": {k: {"name": a["name"], "kind": a["kind"], **forms(k, a), **({"riparian": a["riparian"], "note": a.get("note"), "sources": a.get("sources")} if a.get("riparian") else {}), **({"flag": a["flag"]} if a.get("flag") else {})} for k, a in d["actors"].items()}, "pos": pos, "num": num,
            "orgs": [o for o in orgs if len(o["members"]) >= 2], "agree": agree, "agree_year": unga.get("agreement_year"),
            "edges": live(d["edges"]), "tensions": live(d["tensions"]), "mediations": live(d["mediations"]),
            "dependencies": live(d["dependencies"]), "colors": d["colors"], "people": people,
            "dossiers": [{"id": x["id"], "title": x["title"], "sides": [s["actors"] for s in x["sides"]], "names": [s["name"] for s in x["sides"]]}
                         for x in dossier.load()]}

SCRIPT = r"""<script>
const D = __DATA__;
const $ = s => document.querySelector(s);
const esc = v => String(v ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const nm = id => esc((D.actors[id] || {}).name || id);
const isFlag = id => ["state", "bloc"].includes((D.actors[id] || {}).kind);
const flag = id => (D.actors[id] || {}).flag || `https://cdn.jsdelivr.net/npm/flag-icons@7.2.3/flags/1x1/${id.toLowerCase()}.svg`;
// Sans drapeau ni photo : même pictogramme que dans la vue d'ensemble (Lucide, ISC) — épées = groupe armé, urne = parti, silhouette = personne
const GLYPH = {
  non_state: '<polyline points="14.5 17.5 3 6 3 3 6 3 17.5 14.5"/><line x1="13" x2="19" y1="19" y2="13"/><line x1="16" x2="20" y1="16" y2="20"/><line x1="19" x2="21" y1="21" y2="19"/><polyline points="14.5 6.5 18 3 21 3 21 6 17.5 9.5"/><line x1="5" x2="9" y1="14" y2="18"/><line x1="7" x2="4" y1="17" y2="20"/><line x1="3" x2="5" y1="19" y2="21"/>',
  party: '<path d="m9 12 2 2 4-4"/><path d="M5 7c0-1.1.9-2 2-2h10a2 2 0 0 1 2 2v12H5V7Z"/><path d="M22 19H2"/>',
  person: '<path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>',
  company: '<path d="M6 22V4a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v18Z"/><path d="M6 12H4a2 2 0 0 0-2 2v6a2 2 0 0 0 2 2h2"/><path d="M18 9h2a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2h-2"/><path d="M10 6h4"/><path d="M10 10h4"/><path d="M10 14h4"/><path d="M10 18h4"/>',
  passage: '<path d="M12 22V8"/><path d="M5 12H2a10 10 0 0 0 20 0h-3"/><circle cx="12" cy="5" r="3"/>'};
const badge = (kind, bg) => "data:image/svg+xml;charset=utf-8," + encodeURIComponent(
  `<svg xmlns="http://www.w3.org/2000/svg" viewBox="-6 -6 36 36"><circle cx="12" cy="12" r="18" fill="${bg}"/>` +
  `<g fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">${GLYPH[kind]}</g></svg>`);
const pic = id => isFlag(id) ? flag(id) : D.people[id] || (D.actors[id] ? badge(D.actors[id].kind, D.actors[id].kind === "non_state" ? "#8a8a8a" : "#6b4fbb") : null);
const img = id => pic(id) ? `<img src="${esc(pic(id))}" alt="">` : "";
const who = id => `${img(id)}<span>${nm(id)}</span>`;
const DOS = Object.fromEntries(D.dossiers.map(x => ["d:" + x.id, x]));
const label = t => DOS[t] ? esc(DOS[t].title) : RES[t] ? esc(RES_FR[RES[t]]) : nm(t);
const SWORDS = `<svg class="dep-ico" viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${GLYPH.non_state}</svg>`;   // étiquette d'un conflit
const mark = t => DOS[t] ? "" : RES[t] ? depIcon(RES[t], 15) : img(t);   // drapeau, photo ou pictogramme devant le nom
// source → lien court vers le site (texte complet au survol) ; sans URL, le texte tel quel
const src = s => { const m = String(s).match(/https?:\/\/[^\s<]+/); if(!m) return esc(s);
  let host = m[0]; try { host = new URL(m[0]).hostname.replace(/^www\./, ""); } catch(_) {}
  return `<a href="${esc(m[0])}" target="_blank" rel="noopener" title="${esc(String(s).slice(0, m.index).replace(/[\s—]+$/, ""))}">${esc(host)}</a>`; };
const TYPES_FR = {arms:"armes", troops:"troupes", financial:"argent", training:"entraînement", intelligence:"renseignement",
  political:"politique", economic:"économique", dual_use:"double usage", service:"service stratégique"};
const TENSION = {war:{label:"Guerre", color:"#b91c1c", width:4, dash:null, arrow:false},
  sanctions:{label:"Sanctions", color:"#7c3aed", width:2, dash:"8 5", arrow:true},
  claims:{label:"Revendication", color:"#d97706", width:2, dash:"3 4", arrow:true},
  rivalry:{label:"Rivalité", color:"#64748b", width:2, dash:"10 6", arrow:false},
  trade_war:{label:"Guerre commerciale", color:"#be185d", width:2, dash:"12 4 2 4", arrow:false},
  blockade:{label:"Entrave à la navigation", color:"#0f766e", width:2.4, dash:"2 5", arrow:true}};
const STATUS_FR = {active:"actif", reduced:"en baisse", alleged:"allégué"};
const CONF_FR = {high:"documenté officiellement", medium:"sources concordantes", low:"allégations"};
const WIDTH = {high: 3.2, medium: 2.2, low: 1.3}, DEP = "#b08968";
const DEP_FR = {arms: "d'armes", gas: "de gaz", oil: "de pétrole"};
const depWhat = x => x.resource ? (/^[aeiouyéèh]/i.test(x.resource) ? "d'" : "de ") + x.resource : DEP_FR[x.type] || x.type;
const pct = x => String(x.share).replace(".", ",") + " %";
const depText = x => `${pct(x)} ${x.type === "debt" ? "de sa dette publique extérieure"
  : x.type === "chips" ? "de la capacité mondiale de production des puces les plus avancées"
  : x.type === "trade" ? (x.direction === "exports" ? "de ses exportations" : "de ses importations de marchandises")
  : "de ses importations " + depWhat(x)} (${esc(x.period || x.year)})`;
// pictogrammes des dépendances (Lucide, ISC) : la ressource se lit d'un coup d'œil, le chiffre reste à côté
const DEP_ICON = __DEP_ICONS__;
const DEP_NAME = {oil: "pétrole", gas: "gaz", arms: "armes", minerals: "minerais", food: "denrées", debt: "dette", trade: "commerce", chips: "puces", electricity: "électricité"};
const depIcon = (t, size = 14) => `<svg viewBox="0 0 24 24" width="${size}" height="${size}" fill="none" stroke="${DEP}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${DEP_ICON[t] || ""}</svg>`;
const depShort = x => `${x.type === "debt" ? "dette" : x.type === "trade" ? (x.direction === "exports" ? "exportations" : "importations")
  : x.resource || {arms:"armes", gas:"gaz", oil:"pétrole"}[x.type] || x.type} ${pct(x)}`;
const MONTHS = ["janvier","février","mars","avril","mai","juin","juillet","août","septembre","octobre","novembre","décembre"];
const when = d => { const [y, m] = String(d).split("-"); return m && MONTHS[+m - 1] ? `${MONTHS[+m - 1]} ${y}` : y; };
const since = x => x.since ? `Depuis ${esc(when(x.since))}. ` : "";
// soutien : `since` est la plus ancienne date attestée par les sources, pas forcément le vrai début → « documenté depuis »
const sinceDoc = x => x.since ? `Documenté depuis ${esc(when(x.since))}. ` : "";
const tail = x => `<p class="m">${x.note ? esc(x.note) + ". " : ""}Sources : ${(x.sources || []).map(src).join(", ")}</p>`;
const ARROW = '<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-label="vers"><path d="M5 12h14M13 6l6 6-6 6"/></svg>';

// ---------- Sélection : jetons « US » (acteur) ou « d:ukraine » (conflit), gardés dans l'URL ----------
// Ressource (« r:oil ») : ajoute les pays liés aux acteurs choisis par une dépendance de ce type, et seulement ces dépendances-là
const RES_FR = {arms: "Armes", gas: "Gaz", oil: "Pétrole", minerals: "Minerais", food: "Denrées", debt: "Dette", trade: "Commerce", chips: "Puces", electricity: "Électricité"};
const RES = Object.fromEntries(Object.keys(RES_FR).filter(t => D.dependencies.some(x => x.type === t)).map(t => ["r:" + t, t]));
let SEL = (new URLSearchParams(location.search).get("e") || "").split(",").filter(t => D.actors[t] || DOS[t] || RES[t]);
// sens des dépendances, PAR ressource : « &s=oil:four,arms:dep » ; l'ancienne forme « &s=four » vaut pour toutes (clé « * »)
let SENS = {}; (new URLSearchParams(location.search).get("s") || "").split(",").forEach(x => { const [k, v] = x.includes(":") ? x.split(":") : ["*", x];
  if(["dep", "four", "tout"].includes(v)) SENS[k] = v; });
let PICK = null;   // trait ou acteur mis en avant
let VIEW = {carte: "map", communs: "communs"}[new URLSearchParams(location.search).get("v")] || "schema", WORLD = null;
function scope(){ const ids = [];
  SEL.forEach(t => (DOS[t] ? DOS[t].sides.flat() : [t]).forEach(id => { if(D.actors[id] && !ids.includes(id)) ids.push(id); }));
  return ids; }

// ---------- Faits entre les acteurs du périmètre : un fait = un trait (deux pour une médiation) ----------
function facts(ids){ const S = new Set(ids), F = [], extra = [];   // extra : pays apportés par une ressource choisie (contour pointillé)
  D.tensions.forEach(t => { if(!S.has(t.from) || !S.has(t.to)) return; const s = TENSION[t.type];
    F.push({group: "tension", links: [[t.from, t.to]], color: s.color, width: s.width, dash: s.dash, arrow: s.arrow, nodes: [t.from, t.to], since: t.since, kind: s.label + (t.status === "reduced" ? ", trêve" : ""), faded: t.status === "reduced", raw: t,
      html: `<div class="who">${who(t.from)}${s.arrow ? ARROW : '<span class="k">et</span>'}${who(t.to)}</div>
        <p>${s.label}. ${since(t)}${t.status === "reduced" ? "Trêve ou cessez-le-feu en cours." : ""}</p>${tail(t)}`}); });
  D.edges.forEach(x => { if(!S.has(x.from) || !S.has(x.to)) return;
    F.push({group: "support", links: [[x.from, x.to]], color: D.colors[x.types[0]] || "#888", width: WIDTH[x.confidence] || 2,
      dash: x.status === "active" ? null : "9 5", arrow: true, nodes: [x.from, x.to], since: x.since, kind: "Soutien" + (x.status === "active" ? "" : ", " + (STATUS_FR[x.status] || x.status)), faded: x.status !== "active", raw: x,
      html: `<div class="who">${who(x.from)}${ARROW}${who(x.to)}</div>
        <p>Soutien : ${x.types.map(t => esc(TYPES_FR[t] || t)).join(", ")}. ${sinceDoc(x)}Statut : ${esc(STATUS_FR[x.status] || x.status)} ; ${esc(CONF_FR[x.confidence] || x.confidence)}.</p>
        ${x.why ? `<p>Pourquoi : ${esc(x.why)}</p>` : ""}${tail(x)}`}); });
  D.mediations.forEach(m => { if(!m.between.every(b => S.has(b))) return;
    const out = !S.has(m.mediator);   // médiateur hors sélection : pas de nœud en plus, le fait reste listé et signalé sous le schéma
    F.push({group: "mediation", out, links: out ? [] : m.between.map(b => [m.mediator, b]), color: "var(--graphite)", width: 1.6, dash: "3 5", arrow: false,
      nodes: out ? m.between : [m.mediator, ...m.between], mediator: m.mediator, since: m.since, kind: m.form === "mission" ? "Mission de paix" : "Médiation", raw: m,
      html: `<div class="who">${who(m.mediator)}<span class="k">${m.form === "mission" ? "mission de paix entre" : "médiation entre"}</span>${who(m.between[0])}<span class="k">et</span>${who(m.between[1])}</div>
        <p>${since(m)}${m.why ? "Pourquoi : " + esc(m.why) : ""}</p>${tail(m)}`}); });
  ids.forEach(p => (D.actors[p].riparian || []).forEach(r => { if(!S.has(r)) return; const a = D.actors[p];
    F.push({group: "riparian", links: [[r, p]], color: "var(--graphite)", width: 1.4, dash: null, arrow: false, nodes: [r, p], kind: "Riverain", raw: {state: r, passage: p},
      html: `<div class="who">${who(r)}<span class="k">borde</span>${who(p)}</div><p>État riverain : il borde le passage, sans le posséder.</p>${tail(a)}`}); }));
  const res = new Set(SEL.filter(t => RES[t]).map(t => RES[t]));
  // Sens des dépendances apportées par une ressource : « dep » = ce dont la sélection dépend, « four » = qui dépend d'elle, « tout »
  const sens = {}; res.forEach(t => { const br = D.dependencies.filter(x => x.type === t && S.has(x.from) !== S.has(x.supplier));
    const nDep = br.filter(x => S.has(x.from)).length, nFour = br.length - nDep, want = SENS[t] || SENS["*"];
    sens[t] = {nDep, nFour, mode: want === "four" && nFour ? "four" : want === "tout" || !nDep ? "tout" : "dep"}; });
  D.dependencies.forEach(x => { const a = S.has(x.from), b = S.has(x.supplier);
    if(!(a && b) && !(res.has(x.type) && (a || b))) return;
    const mode = (sens[x.type] || {}).mode;
    if(a !== b && (mode === "dep" && !a || mode === "four" && !b)) return;
    [x.from, x.supplier].forEach(id => { if(!S.has(id) && !extra.includes(id)) extra.push(id); });
    F.push({group: "lever", links: [[x.supplier, x.from]], color: DEP, width: 1 + x.share / 14, dash: "1.5 6", round: true, arrow: true,
      nodes: [x.from, x.supplier], value: depShort(x), dep: x.type, raw: x, tip: `${(D.actors[x.from] || {}).name} dépend de ${(D.actors[x.supplier] || {}).name} : ${depShort(x)}`,
      html: `<div class="who">${who(x.from)}<span class="k">dépend de</span>${who(x.supplier)}</div>
        <p>${depIcon(x.type, 15)} ${depText(x)}.</p>${tail(x)}`}); });
  F.forEach((f, i) => f.id = i);
  return {F, extra, sens}; }

// ---------- « En bref » : compte rendu par GABARITS, sans modèle de langage — chaque morceau de phrase est un fait du graphe et ouvre sa fiche.
// Ordre fixe : ce qui oppose, qui soutient qui (et pourquoi), qui négocie, qui dépend de qui. Rien n'est écrit qui ne soit dans network.yaml.
const the = id => esc(D.actors[id].the), deN = id => esc(D.actors[id].de), cap = s => s.charAt(0).toUpperCase() + s.slice(1);
const vb = (id, sing, plur) => D.actors[id].pl ? plur : sing;
const et = xs => xs.length < 2 ? xs.join("") : xs.slice(0, -1).join(", ") + " et " + xs[xs.length - 1];
const bf = (f, html) => `<span class="bf" role="button" tabindex="0" data-fact="${f.id}">${html}</span>`;   // un span, pas un bouton : le texte doit pouvoir passer à la ligne
function brief(F){ const P = [], by = g => F.filter(f => f.group === g), dp = y => y ? " depuis " + esc(when(y)) : "", MAXT = 4;
  const T = by("tension"), S = by("support"), M = by("mediation"), L = by("lever");
  if(T.length){ const ss = T.slice(0, MAXT).map(f => { const t = f.raw, a = t.from, b = t.to, both = cap(the(a)) + " et " + the(b);
      return bf(f, t.type === "war" ? (t.status === "reduced" ? `${both} observent une trêve${t.since ? ", après une guerre commencée en " + esc(when(t.since)) : ""}` : `${both} sont en guerre${dp(t.since)}`)
        : t.type === "trade_war" ? `${both} sont en guerre commerciale${dp(t.since)}` : t.type === "rivalry" ? `${both} sont en rivalité${dp(t.since)}`
        : t.type === "blockade" ? `${cap(the(a))} ${vb(a, "entrave", "entravent")} la navigation dans ${the(b)}${dp(t.since)}`
        : t.type === "sanctions" ? `${cap(the(a))} ${vb(a, "sanctionne", "sanctionnent")} ${the(b)}${dp(t.since)}`
        : `${cap(the(a))} ${vb(a, "revendique", "revendiquent")} tout ou partie du territoire ${deN(b)}${dp(t.since)}`) + "."; });
    if(T.length > MAXT) ss.push(`${T.length - MAXT} autre${T.length - MAXT > 1 ? "s tensions sont" : " tension est"} sur le schéma.`);
    P.push(ss.join(" ")); }
  if(S.length && S.length <= 4) P.push(S.map(f => { const x = f.raw;
      return bf(f, `${cap(the(x.from))} ${vb(x.from, "soutient", "soutiennent")} ${the(x.to)}`) + ` (${x.types.map(t => esc(TYPES_FR[t] || t)).join(", ")}${x.status === "alleged" ? " ; soutien allégué" : x.status === "reduced" ? " ; soutien en baisse" : ""}).`
        + (x.why ? ` <span class="why">Pourquoi : ${esc(x.why)}.</span>` : ""); }).join(" "));
  else if(S.length){ const g = {}; S.forEach(f => (g[f.raw.to] = g[f.raw.to] || []).push(f));
    const tos = Object.keys(g).sort((a, b) => g[b].length - g[a].length), shown = tos.slice(0, 4);
    P.push(shown.map(to => `Soutiens ${deN(to)} : ${et(g[to].map(f => bf(f, the(f.raw.from))))}.`).join(" ")
      + (tos.length > 4 ? ` D'autres soutiens sont sur le schéma.` : "") + ` <span class="why">Le pourquoi de chaque soutien s'affiche au clic.</span>`); }
  const R = by("riparian"); if(R.length){ const g = {}; R.forEach(f => (g[f.raw.passage] = g[f.raw.passage] || []).push(f));
    P.push(Object.entries(g).map(([p, fs]) => `${fs.length > 1 ? "Riverains" : "Riverain"} ${deN(p)} : ${et(fs.map(f => bf(f, the(f.raw.state))))}.`).join(" ")); }
  if(M.length){ const g = {}; M.forEach(f => { const k = (f.raw.form || "") + "|" + f.raw.between.join("|"); (g[k] = g[k] || []).push(f); });   // plusieurs médiateurs pour une même paire : une seule phrase
    P.push(Object.values(g).map(fs => `${fs[0].raw.form === "mission" ? "Mission de paix" : "Médiation"} entre ${the(fs[0].raw.between[0])} et ${the(fs[0].raw.between[1])} : ${et(fs.map(f => bf(f, the(f.raw.mediator))))}.`).join(" ")); }
  if(L.length){ const g = {}; L.forEach(f => { const x = f.raw; ((g[x.from] = g[x.from] || {})[x.supplier] = g[x.from][x.supplier] || []).push(f); });
    const top = fs => Math.max(...fs.map(f => f.raw.share)), froms = Object.keys(g).sort((a, b) => Object.keys(g[b]).length - Object.keys(g[a]).length), shown = froms.slice(0, 4);
    P.push(shown.map(a => { const sup = Object.keys(g[a]).sort((x, y) => top(g[a][y]) - top(g[a][x])), keep = sup.slice(0, 3);
        return `${cap(the(a))} ${vb(a, "dépend", "dépendent")} ${et(keep.map(b => `${deN(b)} (${g[a][b].sort((x, y) => y.raw.share - x.raw.share).map(f => bf(f, esc(depShort(f.raw)))).join(", ")})`))}`
          + (sup.length > 3 ? ` et de ${sup.length - 3} autre${sup.length - 3 > 1 ? "s fournisseurs" : " fournisseur"}` : "") + "."; }).join(" ")
      + (froms.length > 4 ? " D'autres dépendances sont sur le schéma." : "")); }
  if(!P.length) P.push("Aucune relation n'est documentée entre ces acteurs dans le graphe.");
  return `<h2>En bref</h2>${P.map(x => `<p>${x}</p>`).join("")}`; }

// ---------- Schéma : acteurs sur une ellipse, fixes ; plusieurs faits entre deux acteurs = traits écartés ----------
// écran étroit : cadre plus étroit et plus haut, pour que les noms restent lisibles
const NARROW = innerWidth < 600, W = NARROW ? 400 : 760, CX = W / 2;
// hauteur du dessin : celle qui reste dans la fenêtre sous la barre des vues, ramenée à l'échelle du dessin — le schéma
// s'aplatit au lieu de rétrécir, les textes gardent leur taille
let H = 470, CY = H / 2 - 4;
function stageH(n = 4){ const svg = $("#schema"), w = svg.parentNode.clientWidth || W, room = innerHeight - (svg.getBoundingClientRect().top + scrollY) - 64;
  // beaucoup d'acteurs : on garde de la hauteur (quitte à défiler un peu) plutôt que d'écraser le schéma
  H = NARROW ? 470 : Math.round(Math.max(Math.min(470, 300 + Math.max(0, n - 4) * 45), Math.min(470, W * room / w))); CY = H / 2 - 4; }
// Carte : mêmes traits, acteurs posés sur leur pays (Natural Earth, sans tuiles). Cadre ajusté aux acteurs choisis, zoom plafonné ;
// deux acteurs au même endroit (un groupe armé et son pays) sont écartés juste assez pour rester lisibles.
let ZM = null, BASE = null, LAST = null, GEO = null, BR = [], RELS = [], CAMPS = {}, DISP = id => id;
// Regroupement des camps (schéma seulement) : chaque camp d'un conflit choisi devient UN rond, ses faits internes sortent du dessin
// et les traits de même nature vers un même voisin fusionnent (« ×3 »). Par défaut au-delà de 6 acteurs ; l'URL garde le choix (g=1 / g=0).
let GRP = {1: true, 0: false}[new URLSearchParams(location.search).get("g")];
function camps(ids){ const solo = new Set(SEL.filter(t => D.actors[t])), taken = new Set(), out = {};
  SEL.filter(t => DOS[t]).forEach(t => DOS[t].sides.forEach((side, i) => { const m = side.filter(id => ids.includes(id) && !solo.has(id) && !taken.has(id));
    if(m.length < 2) return; m.forEach(id => taken.add(id)); out[`g:${t.slice(2)}:${i}`] = {name: DOS[t].names[i], members: m}; }));
  return out; }
function mapLayout(all, R){ const pts = all.map(id => D.pos[id]), mp = {type: "MultiPoint", coordinates: pts}, CAP = NARROW ? 420 : 700;
  let proj = d3.geoMercator().fitExtent([[70, 56], [W - 70, H - 64]], mp);
  if(!(proj.scale() < CAP)) proj = d3.geoMercator().scale(CAP).center(d3.geoCentroid(mp)).translate([W / 2, H / 2]);
  BASE = {k: proj.scale(), T: proj([0, 0])}; const z = ZM || BASE; proj = d3.geoMercator().scale(z.k).translate(z.T);   // zoom et déplacement : même projection, recalculée
  const P = {}; all.forEach((id, i) => P[id] = proj(pts[i]).slice());
  for(let k = 0; k < 80; k++) all.forEach((a, i) => all.slice(i + 1).forEach(b => { const dx = P[b][0] - P[a][0] || .5 - i % 2, dy = P[b][1] - P[a][1] || .3, d = Math.hypot(dx, dy), min = 2 * R + 14;
    if(d < min){ const m = (min - d) / 2 / d; P[a][0] -= dx * m; P[a][1] -= dy * m; P[b][0] += dx * m; P[b][1] += dy * m; } }));
  all.forEach(id => { P[id][0] = Math.max(52, Math.min(W - 52, P[id][0])); P[id][1] = Math.max(R + 8, Math.min(H - R - 26, P[id][1])); });
  const on = new Set(all.map(id => D.num[id])), path = d3.geoPath(proj);
  const land = WORLD.map(f => `<path d="${path(f)}" class="${on.has(+f.id) ? "c on" : "c"}"/>`).join("");
  return {P, land}; }
function draw(ids, extra, F){ const MAP = VIEW === "map" && WORLD && [...ids, ...extra].every(id => D.pos[id]), R = MAP ? 17 : 27;
  const possible = camps(ids), grouped = !MAP && VIEW === "schema" && (GRP ?? ids.length + extra.length > 6) && Object.keys(possible).length > 0;
  CAMPS = grouped ? possible : {}; const of = {}; Object.entries(CAMPS).forEach(([g, c]) => c.members.forEach(id => of[id] = g)); DISP = id => of[id] || id;
  $("#grp").hidden = MAP || VIEW !== "schema" || !Object.keys(possible).length; $("#grp").setAttribute("aria-pressed", grouped);
  const all = [...new Set([...ids, ...extra].map(DISP))], n = all.length, rad = id => CAMPS[id] ? 38 : R; let P = {}, land = "";
  stageH(n);
  // traits affichés : un par fait, ou un par groupe de faits de même nature entre les deux mêmes ronds
  RELS = []; const idx = {};
  F.forEach(f => f.links.forEach(l => { const u = DISP(l[0]), v = DISP(l[1]); if(u === v) return;
    const k = [f.group, f.color, f.dash || "", f.dep || "", ...(f.arrow ? [u, v] : [u, v].sort())].join("|") + (grouped || f.dep === "minerals" ? "" : "|" + f.id);   // les minerais d'une même paire ne font qu'un trait, même sans regroupement
    if(idx[k] == null){ idx[k] = RELS.length; RELS.push({id: RELS.length, fids: [], l: [u, v], color: f.color, width: 0, dash: f.dash, round: f.round, arrow: f.arrow, dep: f.dep, value: f.value, tip: f.tip, vals: []}); }
    const r = RELS[idx[k]]; if(!r.fids.includes(f.id)){ r.fids.push(f.id); if(f.value) r.vals.push(f.value); } r.width = Math.max(r.width, f.width); }));
  RELS.forEach(r => { if(r.fids.length < 2) return; r.tip = r.vals.length ? r.vals.join(", ") : r.fids.length + " faits de même nature";
    const pc = v => parseFloat(((v.match(/([\d,]+) %$/) || [])[1] || "0").replace(",", "."));
    if(r.dep === "minerals") r.lines = r.vals.slice().sort((x, y) => pc(y) - pc(x));   // une ligne par minerai, avec sa part (demande de Jérôme : ne pas perdre le chiffre)
    r.value = r.dep === "minerals" ? "minerais ×" + r.fids.length : r.dep ? r.value.replace(/ [\d,]+ %$/, "") + " ×" + r.fids.length : "×" + r.fids.length; });
  if(MAP) ({P, land} = mapLayout(all, R)); else {
  // étoile : si un acteur porte TOUS les traits d'un schéma chargé, il va au centre et les autres l'entourent (sinon ses traits vers ses voisins sont trop courts pour leurs pastilles)
  const hub = n >= 6 && RELS.length ? all.find(id => RELS.every(r => r.l.includes(id))) : null, ring = all.filter(id => id !== hub), m = ring.length;
  if(NARROW && n > 6){ H = hub ? 70 + m * 84 : 150 + n * 52; CY = H / 2 - 4; }   // écran étroit : on allonge le dessin, la page défile
  if(NARROW && hub){ P[hub] = [44, CY]; ring.forEach((id, i) => P[id] = [W - 62, 62 + 84 * i]); }   // étoile sur écran étroit : le centre à gauche, les autres en colonne à droite
  else { const rx = NARROW ? 125 : n === 2 ? 230 : 285, ry = n === 2 ? 0 : NARROW ? Math.max(180, H / 2 - 75) : Math.min(165, H / 2 - 72), a0 = m % 2 === 0 ? -90 - 180 / m : -90;
    if(hub) P[hub] = [CX, CY];
    ring.forEach((id, i) => { const a = (a0 + 360 * i / m) * Math.PI / 180; P[id] = [CX + rx * Math.cos(a), CY + ry * Math.sin(a)]; }); } }
  const byPair = {}; RELS.forEach(f => { const l = f.l, k = [...l].sort().join("|"); (byPair[k] = byPair[k] || []).push([f, l]); });
  // pointe de flèche propre à chaque trait, proportionnelle à son épaisseur (18 px au moins) : le sens doit se lire d'un coup d'œil
  const tip = f => Math.max(18, f.width * 3.4);
  let s = `<defs>${RELS.filter(f => f.arrow).map(f => `<marker id="mk${f.id}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="${tip(f).toFixed(1)}" markerHeight="${tip(f).toFixed(1)}" markerUnits="userSpaceOnUse" orient="auto"><path d="M0 0.6L10 5L0 9.4z" fill="${f.color}" stroke="var(--paper)" stroke-width=".7"/></marker>`).join("")}
    <clipPath id="cp"><circle r="${R - 3}"/></clipPath></defs>${land ? `<g class="land">${land}</g>` : ""}`;
  const placed = all.map(id => ({x: P[id][0] - rad(id) - 4, y: P[id][1] - rad(id) - 4, w: 2 * rad(id) + 8, h: 2 * rad(id) + 8}));
  Object.entries(byPair).forEach(([k, list]) => { const [u, v] = k.split("|"), [x1, y1] = P[u], [x2, y2] = P[v];
    const dx = x2 - x1, dy = y2 - y1, len = Math.hypot(dx, dy), nx = -dy / len, ny = dx / len;
    list.forEach(([f, l], i) => { const off = (i - (list.length - 1) / 2) * Math.min(38, len / 5);
      const mx = (x1 + x2) / 2 + nx * off * 2, my = (y1 + y2) / 2 + ny * off * 2;      // point de contrôle
      const end = (px, py, q) => { const ex = mx - px, ey = my - py, d = Math.hypot(ex, ey) || 1; return [px + ex / d * (rad(q) + 5), py + ey / d * (rad(q) + 5)]; };
      const [fa, fb] = l[0] === u ? [end(x1, y1, u), end(x2, y2, v)] : [end(x2, y2, v), end(x1, y1, u)];
      const path = `M${fa[0].toFixed(1)} ${fa[1].toFixed(1)}Q${mx.toFixed(1)} ${my.toFixed(1)} ${fb[0].toFixed(1)} ${fb[1].toFixed(1)}`;
      s += `<g class="rel" data-r="${f.id}"><path d="${path}" fill="none" stroke="${f.color}" stroke-width="${f.width.toFixed(1)}"${f.dash ? ` stroke-dasharray="${f.dash}"` : ""}${f.round ? ' stroke-linecap="round"' : ""}${f.arrow ? ` marker-end="url(#mk${f.id})"` : ""}/>
        ${f.value ? (() => { const L = f.lines || [f.value], w = Math.max(...L.map(t => t.length)) * 6.3 + (f.dep ? 30 : 18), h = 4 + 16 * L.length;
          // la pastille est posée SUR son trait, vers le pays qui dépend (côté flèche), à la première place libre de toute autre pastille et de tout rond
          const on = t => [(1 - t) ** 2 * fa[0] + 2 * (1 - t) * t * mx + t * t * fb[0], (1 - t) ** 2 * fa[1] + 2 * (1 - t) * t * my + t * t * fb[1]];
          const box = t => { const [cx, cy] = on(t); return {x: cx - w / 2 - 3, y: cy - h / 2 - 3, w: w + 6, h: h + 6, cx, cy}; };
          const free = b => !placed.some(p => b.x < p.x + p.w && b.x + b.w > p.x && b.y < p.y + p.h && b.y + b.h > p.y);
          const b = (f.dep ? [.66, .56, .76, .46, .36, .86, .26] : [.5, .4, .6, .3, .7]).map(box).find(free) || box(f.dep ? .66 : .5);
          placed.push(b); const lx = b.cx, ly = b.cy;
          return `<g transform="translate(${(lx - w / 2).toFixed(1)} ${(ly - h / 2).toFixed(1)})"><title>${esc(f.tip)}</title><rect class="pill" width="${w.toFixed(1)}" height="${h}" rx="10"/>
            ${f.dep ? `<svg x="8" y="4.5" width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="${DEP}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">${DEP_ICON[f.dep] || ""}</svg>` : ""}
            ${L.map((t, i) => `<text class="val" x="${f.dep ? 23 : 9}" y="${14.2 + 16 * i}">${esc(t)}</text>`).join("")}</g>`; })() : ""}
        <path class="hit" d="${path}"/></g>`; }); });
  all.forEach(id => { const [x, y] = P[id], up = y < CY - 1, name = (D.actors[id] || {}).name || id;
    if(CAMPS[id]){ const c = CAMPS[id], m = c.members, show = m.slice(0, m.length > 4 ? 3 : 4), q = 15, cell = (i, k) => { const a = (-90 + 360 * i / k) * Math.PI / 180, d = k === 1 ? 0 : k === 2 ? 15 : 18; return [d * Math.cos(a), d * Math.sin(a)]; };
      const k = show.length + (m.length > show.length ? 1 : 0);
      s += `<g class="node camp" data-n="${esc(id)}" transform="translate(${x.toFixed(1)} ${y.toFixed(1)})" tabindex="0" role="button" aria-label="${esc(c.name)}"><circle class="ring" r="38"/>
        ${show.map((a, i) => { const [ax, ay] = cell(i, k); return `<clipPath id="cc${esc(id.replace(/\W/g, ""))}${i}"><circle cx="${ax.toFixed(1)}" cy="${ay.toFixed(1)}" r="${q - 2}"/></clipPath><image href="${esc(pic(a))}" x="${(ax - q + 2).toFixed(1)}" y="${(ay - q + 2).toFixed(1)}" width="${2 * q - 4}" height="${2 * q - 4}" clip-path="url(#cc${esc(id.replace(/\W/g, ""))}${i})" preserveAspectRatio="xMidYMid slice"><title>${esc(D.actors[a].name)}</title></image>`; }).join("")}
        ${m.length > show.length ? (() => { const [ax, ay] = cell(k - 1, k); return `<text class="more" text-anchor="middle" x="${ax.toFixed(1)}" y="${(ay + 4).toFixed(1)}">+${m.length - show.length}</text>`; })() : ""}
        <text class="lab" text-anchor="middle" y="${up ? -38 - 9 : 38 + 20}">${esc(c.name)}</text></g>`; return; }
    s += `<g class="node${extra.includes(id) ? " extra" : ""}" data-n="${esc(id)}" transform="translate(${x.toFixed(1)} ${y.toFixed(1)})" tabindex="0" role="button" aria-label="${esc(name)}">
      <circle class="ring" r="${R}"/>${pic(id) ? `<image href="${esc(pic(id))}" x="${-R + 3}" y="${-R + 3}" width="${2 * R - 6}" height="${2 * R - 6}" clip-path="url(#cp)" preserveAspectRatio="xMidYMid slice"/>`
        : `<circle r="${R - 3}" fill="var(--graphite)"/><text class="ini" text-anchor="middle" y="4.5">${esc(name.slice(0, 2).toUpperCase())}</text>`}
      <text class="lab" text-anchor="${MAP && x > W - 90 ? "end" : MAP && x < 90 ? "start" : "middle"}" x="${MAP && x > W - 90 ? R : MAP && x < 90 ? -R : 0}" y="${up && !MAP ? -R - 9 : R + (MAP ? 16 : 20)}">${esc(name)}</text></g>`; });
  const svg = $("#schema"); svg.setAttribute("viewBox", MAP ? `0 0 ${W} ${H}` : `0 ${n === 2 ? CY - 100 : -14} ${W} ${n === 2 ? 200 : H + 6}`);
  svg.classList.toggle("map", !!MAP); svg.innerHTML = s; GEO = {P, R, MAP, n}; $("#zoom").hidden = !MAP; LAST = [ids, extra, F]; }
// zoom autour d'un point, déplacement à la souris ; les ronds et les textes gardent leur taille, un acteur hors cadre reste au bord
function redraw(){ if(LAST){ draw(...LAST); detail(); } }
// Le schéma (ou la carte) tient dans la hauteur de la fenêtre : on borne sa hauteur à ce qui reste sous lui, légende comprise
function fitStage(){ const svg = $("#schema"); if(svg.style.display === "none" || $("#out").hidden) return;
  const top = svg.getBoundingClientRect().top + scrollY; svg.style.maxHeight = NARROW ? "none" : Math.max(320, innerHeight - top - 64) + "px"; }   // écran étroit : la page défile, on ne rétrécit pas le dessin
addEventListener("resize", () => { redraw(); fitStage(); });
// écran étroit : le détail est sous le schéma, on y fait défiler ; écran large : il est à côté, rien à faire
function reveal(){ if(PICK && innerWidth < 1000) $("#detail").scrollIntoView({behavior: "smooth", block: "nearest"}); }
function zoomBy(r, c = [W / 2, H / 2]){ if(!BASE) return; const z = ZM || BASE, k = Math.max(BASE.k * .6, Math.min(9000, z.k * r)), q = k / z.k;
  ZM = {k, T: [c[0] + (z.T[0] - c[0]) * q, c[1] + (z.T[1] - c[1]) * q]}; redraw(); }
(() => { const svg = $("#schema"); let drag = null, raf = 0;
  const pt = ev => { const m = svg.getScreenCTM().inverse(); return [ev.clientX * m.a + m.e, ev.clientY * m.d + m.f]; };
  svg.addEventListener("pointerdown", ev => { if(svg.classList.contains("map") && BASE) drag = {p: pt(ev), T: (ZM || BASE).T.slice(), k: (ZM || BASE).k, moved: false}; });
  addEventListener("pointermove", ev => { if(!drag) return; const p = pt(ev), dx = p[0] - drag.p[0], dy = p[1] - drag.p[1];
    if(!drag.moved && Math.hypot(dx, dy) < 5) return; drag.moved = true; ZM = {k: drag.k, T: [drag.T[0] + dx, drag.T[1] + dy]};
    cancelAnimationFrame(raf); raf = requestAnimationFrame(redraw); });
  addEventListener("pointercancel", () => drag = null);
  addEventListener("pointerup", () => { if(drag && drag.moved) svg.dataset.dragged = 1; drag = null; });
  svg.addEventListener("wheel", ev => { if(!svg.classList.contains("map") || !ev.ctrlKey) return; ev.preventDefault(); zoomBy(Math.exp(-ev.deltaY / 120), pt(ev)); }, {passive: false});
  $("#zoom").addEventListener("click", ev => { const z = ev.target.dataset.z; if(z === "in") zoomBy(1.6); if(z === "out") zoomBy(1 / 1.6); if(z === "fit"){ ZM = null; redraw(); } }); })();
// fond de carte chargé à la première bascule (même source que les miniatures de l'accueil)
function setView(v){ VIEW = v; PICK = null; ZM = null;
  if(v === "map" && !WORLD){ $("#seg").dataset.busy = 1;
    return fetch("https://cdn.jsdelivr.net/npm/world-atlas@2/countries-50m.json").then(r => r.json()).then(w => {
      WORLD = topojson.feature(w, w.objects.countries).features.filter(f => f.id !== "010"); delete $("#seg").dataset.busy; render(); })
      .catch(() => { VIEW = "schema"; delete $("#seg").dataset.busy; render(); }); }
  render(); }

// ---------- Suggestions : les entités qui apportent le plus de faits RELIÉS à la sélection (comptés, jamais choisis à la main) ----------
function suggest(ids){ const old = new Set(ids), out = [];
  [...Object.keys(DOS), ...Object.keys(D.actors)].forEach(t => { if(SEL.includes(t)) return;
    const add = (DOS[t] ? DOS[t].sides.flat() : [t]).filter(id => D.actors[id] && !old.has(id)); if(!add.length) return;
    const fresh = new Set(add), n = facts([...ids, ...add]).F.filter(f => f.nodes.some(x => fresh.has(x)) && f.nodes.some(x => old.has(x))).length;
    if(n) out.push({t, n, dos: !!DOS[t]}); });
  const rs = Object.keys(RES).filter(t => !SEL.includes(t)).map(t => ({t, n: D.dependencies.filter(x => x.type === RES[t] && old.has(x.from) !== old.has(x.supplier)).length}))
    .filter(x => x.n).sort((a, b) => b.n - a.n).slice(0, 2);
  const dos = out.filter(x => x.dos).sort((a, b) => b.n - a.n), covered = new Set(dos.flatMap(x => DOS[x.t].sides.flat()));
  // un acteur déjà apporté par un conflit suggéré n'est pas proposé en double
  return [...dos, ...rs, ...out.filter(x => !x.dos && !covered.has(x.t)).sort((a, b) => b.n - a.n).slice(0, 3)].slice(0, 7); }

// ---------- Intermédiaires : acteurs HORS sélection liés à au moins deux acteurs choisis (médiations exclues, déjà signalées).
// D'abord ceux qui relient une paire sans aucun fait direct ; comptés, jamais choisis à la main. ----------
function bridges(ids, extra, F){ const S = new Set(ids), seen = new Set([...ids, ...extra]), out = [];
  const direct = (a, b) => F.some(f => f.nodes.includes(a) && f.nodes.includes(b));
  Object.keys(D.actors).forEach(c => { if(seen.has(c)) return;
    const fs = facts([...ids, c]).F.filter(f => f.group !== "mediation" && f.nodes.includes(c)), near = [...new Set(fs.flatMap(f => f.nodes.filter(x => x !== c && S.has(x))))];
    if(near.length < 2) return;
    let gap = 0; near.forEach((a, i) => near.slice(i + 1).forEach(b => { if(!direct(a, b)) gap++; }));
    out.push({c, fs, near, gap}); });
  return out.sort((a, b) => b.gap - a.gap || b.near.length - a.near.length || b.fs.length - a.fs.length).slice(0, 5); }
const bridgeWhy = (x, a) => x.fs.filter(f => f.nodes.includes(a)).map(f => (f.kind || f.value || "dépendance").toLowerCase()).join(", ");
// aperçu au survol (schéma seulement) : l'intermédiaire au centre, ses liens en tirets de la couleur du fait
function ghost(x){ const svg = $("#schema"); unghost(); if(!GEO || GEO.MAP || VIEW !== "schema") return;
  const R = 22, gx = CX, gy = GEO.n === 2 ? CY - 58 : CY, name = D.actors[x.c].name;
  const lines = x.fs.flatMap(f => f.nodes.filter(a => a !== x.c && GEO.P[DISP(a)]).map(a => `<line x1="${gx}" y1="${gy}" x2="${GEO.P[DISP(a)][0].toFixed(1)}" y2="${GEO.P[DISP(a)][1].toFixed(1)}" stroke="${f.color}" stroke-width="2.2" stroke-dasharray="5 5"/>`)).join("");
  const g = document.createElementNS("http://www.w3.org/2000/svg", "g"); g.setAttribute("class", "ghost");
  g.innerHTML = `${lines}<circle cx="${gx}" cy="${gy}" r="${R}" class="ring" stroke-dasharray="3 3"/><clipPath id="cpg"><circle cx="${gx}" cy="${gy}" r="${R - 3}"/></clipPath>
    <image href="${esc(pic(x.c))}" x="${gx - R + 3}" y="${gy - R + 3}" width="${2 * R - 6}" height="${2 * R - 6}" clip-path="url(#cpg)" preserveAspectRatio="xMidYMid slice"/>
    <text class="lab gl" text-anchor="middle" x="${gx}" y="${gy + R + 17}">${esc(name)}</text>`;
  svg.insertBefore(g, svg.querySelector(".node")); svg.classList.add("ghosted"); }
function unghost(){ const g = $("#schema .ghost"); if(g) g.remove(); $("#schema").classList.remove("ghosted"); }

const stroke = (c, o = {}) => `<svg width="30" height="8" aria-hidden="true"><path d="M1 4H29" stroke="${c}" stroke-width="${o.w || 2.5}"${o.dash ? ` stroke-dasharray="${o.dash}"` : ""} stroke-linecap="${o.round ? "round" : "butt"}"/></svg>`;
const GROUPS = [["riparian", "Qui borde quoi"], ["tension", "Qui s'affronte"], ["support", "Qui soutient qui, et pourquoi"], ["mediation", "Qui négocie"], ["lever", "Qui dépend de qui"]];
const card = f => `<div class="fact">${f.html}</div>`;

function render(){ const ids = scope(), {F, extra, sens} = facts(ids), ok = ids.length >= 1 && ids.length + extra.length >= 2;
  const rs = SEL.filter(t => RES[t]);
  // Sélection : une étiquette pleine par entité. Un conflit dit au survol qui il apporte ; une ressource porte SON réglage de sens.
  const rm = (t, i) => `<button type="button" data-rm="${i}" aria-label="Retirer ${label(t)}">×</button>`;
  $("#chips").innerHTML = SEL.map((t, i) => { if(DOS[t]) return `<span class="chip" title="${esc("Apporte ses camps : " + DOS[t].sides.flat().map(id => D.actors[id].name).join(", "))}">${SWORDS}${label(t)}${rm(t, i)}</span>`;
    if(!RES[t]) return `<span class="chip">${mark(t)}${label(t)}${rm(t, i)}</span>`;
    const x = sens[RES[t]] || {nDep: 0, nFour: 0}, cur = x.nDep && x.nFour ? x.mode : x.nDep ? "dep" : "four", opt = (v, txt, on) => `<option value="${v}"${cur === v ? " selected" : ""}${on ? "" : " disabled"}>${txt}</option>`;
    return `<span class="chip res">${mark(t)}${label(t)}<span class="how">${!ids.length ? "ajoutez un pays" : !(x.nDep || x.nFour) ? "aucune donnée pour cette sélection"
      : `<select data-sens="${RES[t]}" aria-label="Sens des dépendances pour ${label(t)}">${opt("dep", "dont la sélection dépend", x.nDep)}${opt("four", "que la sélection fournit", x.nFour)}${opt("tout", "dans les deux sens", x.nDep && x.nFour)}</select>`}</span>${rm(t, i)}</span>`; }).join("");
  panel();
  $("#reset").hidden = SEL.length < 2;
  // Élargir : UNE zone sous le résultat pour tout ce qu'on peut ajouter, rangé par nature (les deux anciennes rangées « À croiser aussi » et « Reliés aussi par »)
  const sug = ids.length ? suggest(ids) : [];
  const widen = () => { const add = (t, small, more = "") => `<button type="button" class="add" data-add="${esc(t)}"${more}>${mark(t)}${label(t)}<small>${small}</small></button>`, nf = n => `${n} fait${n > 1 ? "s" : ""}`;
    const seen = new Set(sug.map(x => x.t)), acts = [...sug.filter(x => !x.dos && !RES[x.t]).map(x => add(x.t, nf(x.n))),
      ...BR.map((x, i) => seen.has(x.c) ? "" : add(x.c, "relie " + x.near.map(nm).join(", "), ` data-bridge="${i}" title="${esc(x.near.map(a => D.actors[a].name + " (" + bridgeWhy(x, a) + ")").join(" ; "))}"`))].filter(Boolean).slice(0, 6);
    const rows = [["Conflits", sug.filter(x => x.dos).map(x => add(x.t, nf(x.n)))], ["Acteurs", acts], ["Ressources", sug.filter(x => RES[x.t]).map(x => add(x.t, nf(x.n)))]].filter(([, xs]) => xs.length);
    $("#more").hidden = !rows.length; $("#more h2").textContent = ok ? "Élargir" : "Croiser avec";   // un seul acteur choisi : c'est l'étape suivante, pas un supplément
    $("#widen").innerHTML = rows.map(([k, xs]) => `<div class="row"><span class="k">${k}</span><div>${xs.join("")}</div></div>`).join(""); };
  BR = []; widen();
  $("#empty").hidden = SEL.length > 0; $("#none").innerHTML = ""; $("#all").hidden = !ok; $("#out").hidden = !ok; $(".cross").classList.toggle("has", ok);
  history.replaceState(null, "", location.pathname + (SEL.length ? "?e=" + SEL.join(",") + (VIEW === "map" ? "&v=carte" : VIEW === "communs" ? "&v=communs" : "") + (GRP == null ? "" : "&g=" + (GRP ? 1 : 0)) + (rs.some(t => SENS[RES[t]] || SENS["*"]) ? "&s=" + rs.filter(t => SENS[RES[t]] || SENS["*"]).map(t => RES[t] + ":" + (SENS[RES[t]] || SENS["*"])).join(",") : "") : ""));
  document.querySelectorAll("#seg button").forEach(b => b.setAttribute("aria-pressed", b.dataset.v === VIEW));
  window.BRIEF = ok ? brief(F) : ""; $("#brief").innerHTML = window.BRIEF;
  if(!ok) return;
  draw(ids, extra, F); communs(ids);
  const flat2 = VIEW === "communs";
  $("#schema").style.display = flat2 ? "none" : ""; $("#communs").hidden = VIEW !== "communs"; if(flat2) $("#zoom").hidden = true;
  $("#legend").style.display = VIEW === "communs" ? "none" : "";   // le panneau de droite reste : il porte « En bref »
  BR = bridges(ids, extra, F); widen();
  const has = g => F.some(f => f.group === g && !f.out), sup = [...new Set(F.filter(f => f.group === "support").map(f => f.color))];
  $("#legend").innerHTML = [has("tension") && [...new Set(F.filter(f => f.group === "tension").map(f => f.color))].map(c => { const t = Object.values(TENSION).find(x => x.color === c);
      return `<span>${stroke(c, {w: Math.min(t.width, 3), dash: t.dash})}${t.label.toLowerCase()}</span>`; }).join(""),
    has("support") && `<span>${sup.map(c => stroke(c)).join("")}__SOUTIEN__ (tirets : en baisse ou allégué)</span>`,
    has("mediation") && `<span>${stroke("var(--graphite)", {w: 1.6, dash: "3 5"})}__MEDIATION__</span>`,
    has("lever") && `<span>${stroke(DEP, {w: 3, dash: "1.5 6", round: true})}__LEVIER__ (épaisseur : part mesurée)</span>`
      + [...new Set(F.filter(f => f.dep).map(f => f.dep))].map(t => `<span>${depIcon(t)}${DEP_NAME[t] || t}</span>`).join(""),
    extra.length && `<span><svg width="16" height="16" aria-hidden="true"><circle cx="8" cy="8" r="6" fill="none" stroke="var(--graphite)" stroke-width="1.5" stroke-dasharray="2.5 2.5"/></svg>pays apporté par une ressource</span>`].filter(Boolean).join("");
  const pairs = [], isP = id => D.actors[id].kind === "passage";   // un passage n'a pas de « relation » à attendre avec chaque pays
  ids.forEach((a, i) => ids.slice(i + 1).forEach(b => { if(!isP(a) && !isP(b) && !F.some(f => f.nodes.includes(a) && f.nodes.includes(b))) pairs.push(`${nm(a)} et ${nm(b)}`); }));
  $("#none").innerHTML = pairs.length ? `Ce que le graphe ne contient pas : aucune relation documentée entre ${pairs.join(" ; ")}. Cela ne prouve pas qu'il n'y en a pas, seulement qu'aucune n'est sourcée ici.` : "";
  $("#all").innerHTML = `<summary>Tous les faits (${F.length}) et leurs sources</summary>` + (F.length ? GROUPS.filter(([g]) => F.some(f => f.group === g)).map(([g, t]) =>
    `<h3>${t}</h3>` + F.filter(f => f.group === g).map(card).join("")).join("") : '<p class="none">Aucun fait entre ces acteurs dans le graphe.</p>');
  window.FACTS = F; if(PICK && !(PICK.r != null ? RELS[PICK.r] : PICK.f != null ? F[PICK.f] : ids.concat(extra).includes(PICK.n) || CAMPS[PICK.n])) PICK = null;
  detail(); fitStage(); }

// ---------- Points communs : ce que les PAYS choisis partagent sans se le devoir — organisations et votes à l'ONU.
// Mesures et appartenances sourcées (alignments.yaml, Voeten) ; un groupe armé, un parti ou un bloc n'y figure pas. ----------
function communs(ids){ const st = ids.filter(id => D.actors[id].kind === "state"), others = ids.filter(id => !st.includes(id));
  const skip = others.length ? `<p class="none">Sans objet pour ${others.map(nm).join(", ")} : seuls les pays sont membres d'organisations et votent à l'ONU.</p>` : "";
  if(st.length < 2){ $("#communs").innerHTML = '<p class="none" style="margin:0">Il faut au moins deux pays dans la sélection pour comparer leurs organisations et leurs votes.</p>' + skip; return; }
  const cols = st.map(id => `<th class="c"><span>${img(id)}${nm(id)}</span></th>`).join("");
  const orgs = D.orgs.map(o => ({...o, n: st.filter(id => o.members.includes(id)).length})).filter(o => o.n >= 2).sort((a, b) => b.n - a.n || a.forum - b.forum);
  let h = `<h3>Organisations en commun</h3>` + (orgs.length ? `<div class="tw"><table class="pc"><thead><tr><th></th>${cols}</tr></thead><tbody>${orgs.map(o =>
      `<tr><th title="${esc(o.full)}">${esc(o.name)}<small>${o.forum ? "forum" : "alliance ou traité"}</small></th>${st.map(id => `<td>${o.members.includes(id) ? '<i class="dot" title="membre"></i>' : ""}</td>`).join("")}</tr>`).join("")}</tbody></table></div>`
    : `<p class="none" style="margin:0">Aucune organisation suivie par le site ne réunit au moins deux de ces pays.</p>`);
  const val = (a, b) => D.agree[[a, b].sort().join("|")], any = st.some((a, i) => st.slice(i + 1).some(b => val(a, b) != null));
  const cell = (a, b) => { const v = val(a, b); if(a === b) return '<td class="x"></td>'; if(v == null) return '<td class="x" title="pas de donnée">–</td>';
    const p = Math.round(v * 100), k = Math.round(6 + v * 62);
    return `<td class="v" style="background:color-mix(in srgb,var(--ink) ${k}%,var(--land));color:${k > 40 ? "var(--paper)" : "var(--ink)"}" title="${nm(a)} et ${nm(b)} : ${p} % de votes identiques">${p} %</td>`; };
  h += `<h3>Votes à l'ONU${D.agree_year ? " en " + D.agree_year : ""}</h3>` + (any ? `<p class="cap">__ACCORD__ : part des votes où deux pays ont voté pareil à l'Assemblée générale. Plus la case est marquée, plus ils votent ensemble.</p>
    <div class="tw"><table class="pc"><thead><tr><th></th>${cols}</tr></thead><tbody>${st.map(a => `<tr><th><span class="rw">${img(a)}${nm(a)}</span></th>${st.map(b => cell(a, b)).join("")}</tr>`).join("")}</tbody></table></div>`
    : `<p class="none" style="margin:0">Pas de données de vote pour ces pays.</p>`);
  $("#communs").innerHTML = h + skip; }

function detail(){ const F = window.FACTS, svg = $("#schema"), box = $("#detail");
  const camp = PICK && PICK.n ? CAMPS[PICK.n] : null, rel = PICK && PICK.r != null ? RELS[PICK.r] : null;
  const on = !PICK ? [] : F.filter(f => rel ? rel.fids.includes(f.id) : PICK.f != null ? f.id === PICK.f : camp ? f.nodes.some(x => camp.members.includes(x)) : f.nodes.includes(PICK.n));
  svg.classList.toggle("focus", !!PICK);
  svg.querySelectorAll(".rel").forEach(g => g.classList.toggle("on", RELS[+g.dataset.r] && RELS[+g.dataset.r].fids.some(i => on.some(f => f.id === i))));
  const near = new Set(on.flatMap(f => f.nodes).map(DISP)); if(PICK && PICK.n) near.add(PICK.n);
  svg.querySelectorAll(".node").forEach(g => g.classList.toggle("on", near.has(g.dataset.n)));
  if(!PICK){ box.innerHTML = `<div class="brief">${window.BRIEF || ""}</div><p class="none" style="margin:0">${F.length ? "Cliquez un trait ou un acteur pour lire le fait, sa date et ses sources." : "Aucun fait entre ces acteurs dans le graphe."}</p>`; return; }
  box.innerHTML = `<button type="button" class="back" data-back="1">Retour au résumé</button>` + (camp ? `<p class="none" style="margin:0 0 12px">${esc(camp.name)} : ${camp.members.map(nm).join(", ")}. Les faits entre eux sont listés ici, pas dessinés.</p>` : "")
    + (on.length ? on.map(card).join("") : `<p class="none" style="margin:0 0 12px">Aucun fait entre ${camp ? "ce camp" : nm(PICK.n)} et les autres acteurs choisis.</p>`)
    + (PICK.n && !camp ? `<p class="fact m"><a href="vue-d-ensemble.html#graphe:${esc(PICK.n)}">Voir toutes les relations de ${nm(PICK.n)} dans la vue d'ensemble</a></p>` : ""); }

// ---------- Panneau de choix : catégories visibles d'un coup, champ qui filtre (sans accents ni casse) ----------
const flat = v => String(v).normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();
const byName = ks => ks.sort((a, b) => D.actors[a].name.localeCompare(D.actors[b].name, "fr"));
const kindIs = (...k) => byName(Object.keys(D.actors).filter(id => k.includes(D.actors[id].kind)));
const CATS = [["Conflits", Object.keys(DOS)], ["Pays et blocs", kindIs("state", "bloc")], ["Groupes armés", kindIs("non_state")], ["Détroits et passages", kindIs("passage")], ["Partis, personnalités et entreprises", kindIs("party", "person", "company")],
  ["Ressources et leviers", Object.keys(RES)]];
const plain = k => DOS[k] ? DOS[k].title : RES[k] ? RES_FR[RES[k]] : D.actors[k].name;
const CAT_OF = Object.fromEntries(CATS.flatMap(([t, items]) => items.map(k => [k, t])));
// autres mots qui mènent à la même entité (« usa », « ue »…)
const ALIAS = {US: "usa etats unis amerique", GB: "angleterre grande bretagne uk", EU: "ue europe", AE: "eau emirats", CD: "congo rdc", KP: "coree", NL: "hollande",
  spacex: "starlink musk", rsf: "fsr", jnim: "al qaida sahel", MM: "myanmar", "r:chips": "semi-conducteurs puces tsmc", "r:minerals": "terres rares potasse uranium lithium", "r:food": "ble cereales", UN: "nations unies casques bleus conseil de securite", ormuz: "hormuz golfe persique", bab_el_mandeb: "mer rouge suez aden"};
const hay = k => flat(plain(k)) + " " + (ALIAS[k] || "");
// sans rien taper : quelques entrées courantes, pas les 80 — la liste complète est derrière « Voir toute la liste »
const COMMON = [...Object.keys(DOS), "US", "CN", "RU", "EU", "IR", "IL", "r:arms", "r:oil"].filter(k => DOS[k] || RES[k] || D.actors[k]);
let FULL = false, HIT = 0;
const pickBtn = (k, extra = "", cls = "") => `<button type="button" data-add="${esc(k)}"${cls ? ` class="${cls}"` : ""}${SEL.includes(k) ? " disabled" : ""}>${mark(k)}${label(k)}${extra}</button>`;
function panel(){ const q = flat($("#q").value.trim()), all = CATS.flatMap(([, items]) => items); let html = "", shown = 1;
  if(q){ const code = k => flat(k) === q, hits = all.filter(k => code(k) || hay(k).includes(q))   // le code pays exact (« us », « fr ») passe devant, puis les noms qui commencent par la saisie
      .sort((a, b) => (code(b) - code(a)) || (flat(plain(b)).startsWith(q) - flat(plain(a)).startsWith(q)) || plain(a).localeCompare(plain(b), "fr")).slice(0, 8);
    shown = hits.length; const free = hits.filter(k => !SEL.includes(k)); HIT = Math.min(HIT, Math.max(0, free.length - 1));
    html = `<div class="hits">${hits.map(k => pickBtn(k, `<small>${esc(CAT_OF[k])}</small>`, free[HIT] === k ? "on" : "")).join("")}</div>`; }
  else if(FULL) html = CATS.map(([t, items]) => `<h3>${t}</h3><div class="g">${items.map(k => pickBtn(k)).join("")}</div>`).join("");
  else html = `<h3>Souvent consultés</h3><div class="g">${COMMON.map(k => pickBtn(k)).join("")}</div><button type="button" class="more" data-full="1">Voir toute la liste</button>`;
  $("#groups").innerHTML = html; $("#noq").hidden = shown > 0; }
function toggle(open){ $("#panel").hidden = !open; $("#veil").hidden = !open; $("#q").setAttribute("aria-expanded", open); if(!open){ $("#q").value = ""; FULL = false; HIT = 0; } else panel(); }
$("#q").addEventListener("focus", () => toggle(true));
$("#q").addEventListener("input", () => { HIT = 0; toggle(true); });
$("#q").addEventListener("keydown", ev => { if(ev.key === "Escape"){ toggle(false); $("#q").blur(); }
  if(ev.key === "ArrowDown" || ev.key === "ArrowUp"){ ev.preventDefault(); HIT = Math.max(0, HIT + (ev.key === "ArrowDown" ? 1 : -1)); panel(); }
  if(ev.key === "Enter"){ const b = $("#groups .hits button.on") || $("#groups .hits button:not(:disabled)"); if(b){ b.click(); } } });
document.addEventListener("click", ev => { const t = ev.target;
  if(t.dataset && t.dataset.rm != null){ ZM = null; SEL.splice(+t.dataset.rm, 1); PICK = null; return render(); }
  if($("#schema").dataset.dragged){ delete $("#schema").dataset.dragged; if(t.closest && t.closest("#schema")) return; }
  const add = t.closest && t.closest("[data-add]"); if(add){ ZM = null; if(!SEL.includes(add.dataset.add)) SEL.push(add.dataset.add); PICK = null; $("#q").value = ""; HIT = 0; return render(); }
  if(t.dataset && t.dataset.full){ FULL = true; return panel(); }
  if(t.dataset && t.dataset.back){ PICK = null; return detail(); }
  if(!$("#panel").hidden && !(t.closest && (t.closest("#panel") || t.closest(".pick") || t.closest("#more")))) toggle(false);
  if(t.id === "reset"){ SEL = []; PICK = null; ZM = null; GRP = undefined; SENS = {}; toggle(false); return render(); }
  const ex = t.closest && t.closest("[data-ex]"); if(ex){ ev.preventDefault(); ZM = null; SEL = ex.dataset.ex.split(","); PICK = null; return render(); }
  if(t.dataset && t.dataset.fact != null){ PICK = {f: +t.dataset.fact}; detail(); return reveal(); }
  const rel = t.closest && t.closest(".rel"), node = t.closest && t.closest(".node");
  if(rel){ PICK = PICK && PICK.r === +rel.dataset.r ? null : {r: +rel.dataset.r}; detail(); return reveal(); }
  if(t.closest && t.closest("#grp")){ GRP = $("#grp").getAttribute("aria-pressed") !== "true"; PICK = null; return render(); }
  if(node){ PICK = PICK && PICK.n === node.dataset.n ? null : {n: node.dataset.n}; detail(); return reveal(); }
  if(t.closest && t.closest("#schema") && PICK){ PICK = null; detail(); } });
["mouseover", "focusin"].forEach(e => document.addEventListener(e, ev => { const b = ev.target.closest && ev.target.closest("[data-bridge]"); b && BR[+b.dataset.bridge] ? ghost(BR[+b.dataset.bridge]) : unghost(); }));
document.addEventListener("keydown", ev => { const node = ev.target.closest && ev.target.closest(".node, .bf");
  if(node && (ev.key === "Enter" || ev.key === " ")){ ev.preventDefault(); node.dispatchEvent(new MouseEvent("click", {bubbles: true})); } });
document.querySelectorAll("#seg button").forEach(b => b.addEventListener("click", () => setView(b.dataset.v)));
document.addEventListener("change", ev => { const t = ev.target; if(t.dataset && t.dataset.sens){ delete SENS["*"]; SENS[t.dataset.sens] = t.value; PICK = null; ZM = null; render(); } });
VIEW === "map" ? setView("map") : render();
</script>"""

LIBS = ('<script src="https://cdn.jsdelivr.net/npm/d3-array@3/dist/d3-array.min.js"></script>'
        '<script src="https://cdn.jsdelivr.net/npm/d3-geo@3/dist/d3-geo.min.js"></script>'
        '<script src="https://cdn.jsdelivr.net/npm/topojson-client@3/dist/topojson-client.min.js"></script>')

EXAMPLES = [("US,d:ukraine,CN", "Les États-Unis, la Chine et la guerre en Ukraine"),
            ("d:iran,RU,CN", "La Russie, la Chine et la guerre avec l'Iran"),
            ("EU,RU,US", "L'Union européenne, la Russie et les États-Unis"),
            ("IN,r:arms", "L'Inde et ses fournisseurs d'armes")]

def page(d):
    x = data(d)
    valid = set(x["actors"]) | {"d:" + t["id"] for t in x["dossiers"]} | {"r:" + t["type"] for t in x["dependencies"]}
    examples = "".join(f'<a href="relations.html?e={e(q)}" data-ex="{e(q)}">{e(t)}</a>' for q, t in EXAMPLES
                       if all(tok in valid for tok in q.split(",")))
    script = (SCRIPT.replace("__DATA__", json.dumps(x, ensure_ascii=False, default=str).replace("</", "<\\/"))
              .replace("__DEP_ICONS__", json.dumps(style.DEP_ICONS))
              .replace("__SOUTIEN__", glossary.term("soutien", "soutien")).replace("__MEDIATION__", glossary.term("mediation", "médiation"))
              .replace("__LEVIER__", glossary.term("levier", "dépendance"))
              .replace("__ACCORD__", glossary.term("taux-accord", "Taux d'accord")))
    body = f"""<main class="cross">
<h1>Croiser des acteurs</h1>
<p class="lede">Tapez un pays, un groupe, un conflit ou une ressource : un compte rendu et un schéma montrent ce qui les relie, fait par fait.</p>
<div class="picker"><div id="veil" hidden></div><div class="pick"><span id="chips" style="display:contents"></span>
<input type="search" id="q" role="combobox" aria-expanded="false" aria-controls="panel" aria-label="Ajouter un pays, un groupe, un conflit ou une ressource" placeholder="Ajouter : pays, conflit, ressource…" autocomplete="off">
<button type="button" id="reset" hidden>Tout effacer</button></div>
<div id="panel" hidden><div id="groups"></div><p class="none" id="noq" hidden>Aucun acteur ne correspond.</p></div></div>
<div id="empty"><div class="ex"><span class="quiet">Pour commencer :</span>{examples}</div></div>
<div id="out" hidden>
<div class="cols"><div class="main">
<div id="brief" class="brief" aria-live="polite"></div>
<div class="bar"><div class="seg" id="seg" role="group" aria-label="Affichage"><button type="button" data-v="schema">__ICO_GRAPH__<span>Schéma</span></button><button type="button" data-v="map">__ICO_MAP__<span>Carte</span></button><button type="button" data-v="communs">__ICO_ORGS__<span>Points communs</span></button></div>
<button type="button" id="grp" aria-pressed="false" hidden>Regrouper les camps</button>
<div id="zoom" hidden><button type="button" data-z="in" aria-label="Zoomer">+</button><button type="button" data-z="out" aria-label="Dézoomer">−</button><button type="button" data-z="fit">Recadrer</button></div></div>
<div class="stage"><div id="communs" hidden></div><svg id="schema" role="group" aria-label="Schéma des relations entre les acteurs choisis"></svg></div>
<div class="legend" id="legend"></div></div>
<aside class="side"><div id="detail" aria-live="polite"></div></aside></div>
</div>
<section id="more" hidden><h2>Élargir</h2><div id="widen"></div></section>
<p class="none" id="none"></p>
<details class="all" id="all" hidden></details>
</main>"""
    body = body.replace("__ICO_GRAPH__", style.icon("graph", 16)).replace("__ICO_MAP__", style.icon("map", 16)).replace("__ICO_ORGS__", style.icon("orgs", 16))
    title = f"Croiser des acteurs : ce qui relie deux pays — {brand.NAME}"
    return (style.head(title, "Choisissez des pays, des groupes ou un conflit : ce qui les relie, fait par fait, avec les sources.",
                       f"<style>{CSS}</style>", path="relations.html")
            + f'<body><div class="wrap">{style.top("relations.html")}\n{body}</div>{style.foot(page="Croiser des acteurs")}{LIBS}{script}</body></html>')

def write(out, d):
    (out / "relations.html").write_text(page(d), encoding="utf-8")
