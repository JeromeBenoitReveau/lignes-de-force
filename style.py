"""Feuille de style commune (site/style.css) et gabarit des pages éditoriales : un seul endroit pour les couleurs,
la typographie et l'en-tête. La couleur est réservée aux données (camps, soutiens, tensions) ; l'interface reste
en encre et gris, et l'espace sépare les sections plutôt que des cadres."""
from html import escape as e
from urllib.parse import quote
import brand

DARK = ("color-scheme:dark;--paper:#141821;--ink:#e8ebf0;--graphite:#9ba3b0;--mist:#29303b;"
        "--ocean:#0d131b;--land:#1b212b;--peach:#f4b393;--brand:#f4b393;--a:#3987e5;--b:#d95926")
# appliqué avant le premier affichage, pour éviter un flash du mauvais thème
THEME_INIT = '<script>try{const t=localStorage.getItem("theme");if(t)document.documentElement.dataset.theme=t}catch(_){}</script>'

FONTS = ("https://fonts.googleapis.com/css2?family=Newsreader:opsz,wght@6..72,400;6..72,500"
         "&family=Public+Sans:wght@400;500;600&display=swap")

CSS = """
:root{--paper:#f7f8f7;--ink:#16181d;--graphite:#5f6670;--mist:#e3e6e9;--ocean:#e6ebef;--land:#fdfdfc;
  --peach:#e3936c;--brand:var(--ink);--a:#2a78d6;--b:#eb6834;--line:var(--mist);--card:var(--land);--fg:var(--ink);--bg:var(--paper);--mute:var(--graphite);
  --serif:"Newsreader",Georgia,serif;--sans:"Public Sans",system-ui,sans-serif}
/* sombre : gris très légèrement bleutés ; la pêche s'éclaircit pour rester lisible.
   Thème du système par défaut ; l'interrupteur du menu le force (attribut data-theme, gardé dans le navigateur) */
:root{color-scheme:light}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){__DARK__}}
:root[data-theme=dark]{__DARK__}
/* la pêche est l'accent de l'interface (liens, onglet actif, survol, focus, logo) ; jamais une couleur de données */
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);font:17px/1.6 var(--sans);-webkit-font-smoothing:antialiased}
/* liens : souligné en tirets d'1 px ; au survol, même épaisseur mais trait plein (choix de Jérôme, 2026-10-02) */
a,.lk{color:inherit;text-decoration:underline dashed var(--peach) 1px;text-underline-offset:3px}
a:hover,.lk:hover{text-decoration-style:solid}
a:focus-visible,summary:focus-visible,button:focus-visible,input:focus-visible,select:focus-visible{outline:2px solid var(--peach);outline-offset:3px;border-radius:2px}
.wrap{max-width:1080px;margin:0 auto;padding:0 20px}
.top{display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap;padding:22px 0 0;font-size:15px}
.top a{text-decoration:none}
/* menus déroulants de l'en-tête */
.menus{display:flex;gap:26px;align-items:center}.menu{position:relative}
.menu summary{list-style:none;cursor:pointer;color:var(--graphite);padding:4px 0;border-bottom:2px solid transparent;display:flex;align-items:center;gap:6px}
.menu summary::-webkit-details-marker{display:none}
.menu summary::after{content:"";width:6px;height:6px;border:solid currentColor;border-width:0 1.5px 1.5px 0;transform:translateY(-2px) rotate(45deg);opacity:.7}
.menu[open] summary::after{transform:translateY(1px) rotate(-135deg)}
.menu summary:hover,.menu[open] summary,.menu[data-active] summary{color:var(--ink)}.menu[data-active] summary{border-bottom-color:var(--peach)}
.dd{position:absolute;right:0;top:calc(100% + 10px);z-index:2000;min-width:230px;background:var(--land);border:1px solid var(--mist);
  border-radius:6px;padding:6px;box-shadow:0 8px 24px #0000001a;display:flex;flex-direction:column}
.dd a{display:flex;align-items:center;gap:10px;padding:8px 10px;border-radius:4px;color:var(--ink);white-space:nowrap}
.dd a:hover,.dd a:focus-visible{background:color-mix(in srgb,var(--ink) 6%,var(--land))}.dd a[aria-current]{box-shadow:inset 2px 0 0 var(--peach)}
.dd .ico,.explore .ico{color:var(--peach);flex:none}
/* Relations, Vue d'ensemble : liens simples (le choix de la vue se fait dans la page) */
.menu-link{color:var(--graphite);padding:4px 0;border-bottom:2px solid transparent}.menu-link:hover{color:var(--ink)}
.menu-link[aria-current]{color:var(--ink);border-bottom-color:var(--peach)}
.theme{background:none;border:0;color:var(--graphite);cursor:pointer;padding:4px;border-radius:3px;display:flex;align-items:center}
.theme:hover{color:var(--ink)}.theme .sun{display:none}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]) .theme .sun{display:block}:root:not([data-theme=light]) .theme .moon{display:none}}
:root[data-theme=dark] .theme .sun{display:block}:root[data-theme=dark] .theme .moon{display:none}
.brand{font-family:var(--serif);font-size:20px;display:inline-flex;align-items:center;gap:9px;color:var(--brand)}.brand .logo{flex:none}
h1{font:400 44px/1.1 var(--serif);letter-spacing:-.01em;margin:0 0 14px}
h2{font:400 26px/1.25 var(--serif);margin:0 0 18px}
h3{font:500 19px/1.3 var(--serif);margin:0 0 4px}
.meta,.quiet{color:var(--graphite);font-size:15px}
.lede{font:400 21px/1.5 var(--serif);margin:0;max-width:40em}
.prose{max-width:40em}.prose p{margin:0 0 14px}
section.s{padding:56px 0 0}
/* cartes : bordure fine, pas d'ombre ; encart teinté pour un chiffre ou une donnée mise en avant */
.card{display:block;border:1px solid var(--mist);border-radius:6px;background:var(--land);padding:22px 24px;text-decoration:none}
a.card{transition:border-color .15s}a.card:hover{border-color:var(--peach)}
.tint{background:color-mix(in srgb,var(--ink) 5%,var(--land));border-radius:4px}
sup.fns{font:500 11px/1 var(--sans);color:var(--graphite);margin-left:1px;white-space:nowrap}
sup.fns a{text-decoration:none;padding:0 1px}sup.fns a:hover{color:var(--ink);text-decoration:underline solid 1px}
.dep-ico{vertical-align:-2px;flex:none}
abbr{text-decoration:underline dotted var(--graphite);text-underline-offset:3px;cursor:help}
/* termes du glossaire (glossary.py) : souligné pointillé, définition au survol ou au focus, clic vers glossaire.html */
a.term{color:inherit;text-decoration:underline dotted var(--graphite);text-decoration-thickness:1px;text-underline-offset:3px;cursor:help}
a.term:hover{text-decoration-color:var(--peach);text-decoration-style:solid}
a.term.q{display:inline-flex;align-items:center;justify-content:center;width:15px;height:15px;border-radius:50%;
  border:1px solid var(--graphite);font-size:10.5px;font-weight:600;line-height:1;text-decoration:none;color:var(--graphite);vertical-align:1px;margin-left:4px}
a.term.q:hover{border-color:var(--peach);color:var(--ink)}
#tip{position:fixed;z-index:3000;max-width:320px;background:var(--ink);color:var(--paper);font:13.5px/1.45 var(--sans);
  padding:9px 12px;border-radius:6px;box-shadow:0 6px 20px #0003;pointer-events:none;display:none}
#tip b{display:block;font-weight:600;margin-bottom:2px}#tip small{display:block;margin-top:5px;opacity:.7;font-size:12px}
.notes{padding:64px 0 72px;font-size:13.5px;color:var(--graphite)}
.notes h2{font-size:21px;color:var(--ink)}.notes ol{margin:0;padding-left:22px;columns:2;column-gap:48px}
.notes li{break-inside:avoid;margin:0 0 6px}.notes li:target{color:var(--ink)}.notes .fix{margin:28px 0 0;font-size:15px;color:var(--ink)}
footer{border-top:1px solid var(--mist);margin-top:64px;padding:20px 0 40px;font-size:13.5px;color:var(--graphite)}
@media (max-width:760px){h1{font-size:34px}.lede{font-size:19px}.notes ol{columns:1}.menus{gap:18px}}
/* téléphone : le menu tient sur une ligne, sans couper « Vue d'ensemble » ni « À propos » */
@media (max-width:480px){.menus{gap:11px;font-size:13.5px;flex-wrap:wrap}.menus .menu-link,.menu summary{white-space:nowrap}.menu summary{gap:4px}.top{position:relative}.top .theme{position:absolute;top:26px;right:0}}
@media (prefers-reduced-motion:reduce){*{scroll-behavior:auto!important;transition:none!important}}
"""

# Logo « le méridien » : un globe traversé d'une ligne tendue, sur une pastille pêche (dessin fourni par Jérôme)
_MARK = ('<rect width="205" height="205" rx="52" fill="#F4B393"/>'
         '<circle cx="102.5" cy="102.5" r="61.1909" stroke="#2B313B" stroke-width="18"/>'
         '<path d="M156.857 81.9434C148.569 79.6244 139.83 78.3844 130.802 78.3844C95.6414 78.3844 64.8735 97.1899 48.0073 125.291" stroke="#2B313B" stroke-width="18"/>')
LOGO = f'<svg class="logo" viewBox="0 0 205 205" width="26" height="26" fill="none" aria-hidden="true">{_MARK}</svg>'
# icône d'onglet : le même dessin (couleurs fixes, lisible sur fond clair comme sombre)
FAVICON = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 205 205" fill="none">{_MARK}</svg>\n'

# Icônes des trois vues de l'explorateur (Lucide, ISC ; « orgs » dessiné pour le site : deux cercles qui se recoupent)
ICONS = {
    "orgs": '<circle cx="9" cy="12" r="6"/><circle cx="15" cy="12" r="6"/>',
    "map": '<circle cx="12" cy="12" r="10"/><path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20"/><path d="M2 12h20"/>',
    "graph": '<circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><line x1="8.59" x2="15.42" y1="13.51" y2="17.49"/><line x1="15.41" x2="8.59" y1="6.51" y2="10.49"/>',
}
# Pictogrammes des dépendances (Lucide, ISC), par type de levier : même dessin sur « Croiser », les fiches et les dossiers
DEP_ICONS = {
    "oil": '<path d="M12 22a7 7 0 0 0 7-7c0-2-1-3.9-3-5.5s-3.5-4-4-6.5c-.5 2.5-2 4.9-4 6.5C6 11.1 5 13 5 15a7 7 0 0 0 7 7z"/>',
    "gas": '<path d="M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.38-.5-2-1-3-1.072-2.143-.224-4.054 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 1 1-14 0c0-1.153.433-2.294 1-3a2.5 2.5 0 0 0 2.5 2.5z"/>',
    "arms": '<circle cx="12" cy="12" r="9"/><path d="M22 12h-5M7 12H2M12 7V2M12 22v-5"/>',
    "minerals": '<path d="M6 3h12l4 6-10 13L2 9Z"/><path d="M11 3 8 9l4 13 4-13-3-6M2 9h20"/>',
    "food": '<path d="M2 22 16 8M3.47 12.53 5 11l1.53 1.53a3.5 3.5 0 0 1 0 4.94L5 19l-1.53-1.53a3.5 3.5 0 0 1 0-4.94ZM7.47 8.53 9 7l1.53 1.53a3.5 3.5 0 0 1 0 4.94L9 15l-1.53-1.53a3.5 3.5 0 0 1 0-4.94ZM11.47 4.53 13 3l1.53 1.53a3.5 3.5 0 0 1 0 4.94L13 11l-1.53-1.53a3.5 3.5 0 0 1 0-4.94ZM20 2h2v2a4 4 0 0 1-4 4h-2V6a4 4 0 0 1 4-4Z"/>',
    "debt": '<path d="M3 22h18M6 18v-7M10 18v-7M14 18v-7M18 18v-7M12 2l8 5H4z"/>',
    "trade": '<path d="M8 3 4 7l4 4M4 7h16M16 21l4-4-4-4M20 17H4"/>',
    "electricity": '<path d="M4 14a1 1 0 0 1-.78-1.63l9.9-10.2a.5.5 0 0 1 .86.46l-1.92 6.02A1 1 0 0 0 13 10h7a1 1 0 0 1 .78 1.63l-9.9 10.2a.5.5 0 0 1-.86-.46l1.92-6.02A1 1 0 0 0 11 14z"/>',
    "transit": '<path d="M2 21c.6.5 1.2 1 2.5 1 2.5 0 2.5-2 5-2 1.3 0 1.9.5 2.5 1 .6.5 1.2 1 2.5 1 2.5 0 2.5-2 5-2 1.3 0 1.9.5 2.5 1"/><path d="M19.38 20A11.6 11.6 0 0 0 21 14l-9-4-9 4c0 2.9.94 5.34 2.81 7.76"/><path d="M19 13V7a2 2 0 0 0-2-2H7a2 2 0 0 0-2 2v6"/><path d="M12 10v4"/><path d="M12 2v3"/>',
    "chips": '<rect width="16" height="16" x="4" y="4" rx="2"/><rect width="6" height="6" x="9" y="9" rx="1"/><path d="M15 2v2M15 20v2M2 15h2M2 9h2M20 15h2M20 9h2M9 2v2M9 20v2"/>',
}
DEP_COLOR = "#b08968"
def dep_icon(t, size=14):
    return (f'<svg class="dep-ico" viewBox="0 0 24 24" width="{size}" height="{size}" fill="none" stroke="{DEP_COLOR}" '
            f'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{DEP_ICONS.get(t, "")}</svg>')

def flag_url(aid, actor=None):
    """Drapeau d'un acteur : champ `flag` (territoire sans code pays, ex. Somaliland), sinon flag-icons d'après le code ISO2."""
    return (actor or {}).get("flag") or f"https://cdn.jsdelivr.net/npm/flag-icons@7.2.3/flags/1x1/{aid.lower()}.svg"

def icon(k, size=18):
    return (f'<svg class="ico" viewBox="0 0 24 24" width="{size}" height="{size}" fill="none" stroke="currentColor" '
            f'stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{ICONS[k]}</svg>')
# les trois vues de l'explorateur : (ancre, icône, libellé) — mêmes entrées dans le menu, l'explorateur et l'accueil
VIEWS = [("organisations", "orgs", "Organisations"), ("carte", "map", "Carte du monde"), ("graphe", "graph", "Graphe des soutiens")]

def clip(text, n=158):
    """Description pour les moteurs de recherche : une ligne, coupée à un mot entier vers 158 caractères."""
    t = " ".join(str(text).split())
    return t if len(t) <= n else t[:n].rsplit(" ", 1)[0].rstrip(",;:") + "…"

def seo(path, title, desc, kind="website", ld=None, image="partage.png"):
    """Balises de référencement et de partage : adresse canonique, Open Graph, carte Twitter, données structurées (JSON-LD).
    path = nom du fichier (« » pour l'accueil). Image de partage : assets/partage.png par défaut, assets/partage-<id>.png pour un dossier (share.py)."""
    import json
    url = brand.SITE + ("" if path in ("", "index.html") else path)
    tags = [f'<link rel="canonical" href="{e(url)}">',
            f'<meta property="og:type" content="{kind}">', f'<meta property="og:site_name" content="{e(brand.NAME)}">',
            f'<meta property="og:title" content="{e(title)}">', f'<meta property="og:description" content="{e(desc)}">',
            f'<meta property="og:url" content="{e(url)}">', '<meta property="og:locale" content="fr_FR">',
            f'<meta property="og:image" content="{brand.SITE}{image}">', '<meta property="og:image:width" content="1200">',
            '<meta property="og:image:height" content="630">', f'<meta property="og:image:alt" content="{e(brand.NAME)} — {e(brand.BASELINE)}">',
            '<meta name="twitter:card" content="summary_large_image">', f'<meta name="twitter:image" content="{brand.SITE}{image}">', f'<meta name="twitter:title" content="{e(title)}">',
            f'<meta name="twitter:description" content="{e(desc)}">']
    if ld:
        tags.append('<script type="application/ld+json">' + json.dumps(ld, ensure_ascii=False).replace("</", "<\\/") + "</script>")
    return "\n".join(tags)

def head(title, desc=brand.BASELINE, extra="", path=None, kind="website", ld=None, image="partage.png"):
    desc = clip(desc)
    return f"""<!doctype html><html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
{seo(path, title, desc, kind, ld, image) if path is not None else ""}
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link rel="stylesheet" href="{FONTS}">
<link rel="stylesheet" href="style.css"><link rel="icon" href="favicon.svg" type="image/svg+xml">{THEME_INIT}{extra}</head>"""

def top(current=""):
    """En-tête commun, tout en noms : Conflits (menu), Relations (relations.html), Vue d'ensemble (vue-d-ensemble.html), À propos (menu).
    current = nom du fichier de la page, pour signaler la rubrique et la page actives."""
    import dossier  # import tardif : dossier importe style
    conflicts = [(f"{x['id']}.html", x["title"]) for x in dossier.load()]
    about = [("manifeste.html", "Manifeste"), ("glossaire.html", "Glossaire"), ("methode.html", "Méthode et sources")]
    here = lambda h: ' aria-current="page"' if h == current else ""
    def menu(label, items, active):
        links = "".join(f'<a href="{h}"{here(h)}>{t}</a>' for h, t in items)
        return f'<details class="menu"{" data-active" if active else ""}><summary>{label}</summary><div class="dd">{links}</div></details>'
    return f"""<div class="top"><a class="brand" href="index.html">{LOGO}{e(brand.NAME)}</a><nav class="menus">
{menu("Conflits", conflicts, current in dict(conflicts))}
<a class="menu-link" href="relations.html"{' aria-current="page"' if current == "relations.html" else ""}>Relations</a>
<a class="menu-link" href="vue-d-ensemble.html"{' aria-current="page"' if current == "vue-d-ensemble.html" else ""}>Vue d'ensemble</a>
{menu("À propos", about, current in dict(about))}
<button class="theme" id="theme-toggle" type="button" title="Mode clair / mode sombre" aria-label="Basculer entre mode clair et mode sombre">
<svg class="moon" viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z"/></svg>
<svg class="sun" viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41"/></svg></button></nav></div>
<script>
// un seul menu ouvert à la fois ; un clic ailleurs ou Échap les ferme
document.addEventListener("click", ev => document.querySelectorAll("details.menu[open]").forEach(d => {{ if(!d.contains(ev.target) || ev.target.closest(".dd a")) d.open = false; }}));
// thème : bascule entre clair et sombre ; les pages qui calculent leurs couleurs en JS (cartes, graphe) se rechargent
document.getElementById("theme-toggle").addEventListener("click", () => {{ const r = document.documentElement;
  const dark = r.dataset.theme ? r.dataset.theme === "dark" : matchMedia("(prefers-color-scheme: dark)").matches;
  r.dataset.theme = dark ? "light" : "dark"; try {{ localStorage.setItem("theme", r.dataset.theme); }} catch(_) {{}}
  if(window.THEME_RELOAD) location.reload(); }});
document.addEventListener("keydown", ev => {{ if(ev.key === "Escape") document.querySelectorAll("details.menu[open]").forEach(d => d.open = false); }});
// infobulle des termes du glossaire, commune à tout le site (délégation : marche aussi sur les contenus ajoutés en JS)
(() => {{ const tip = document.createElement("div"); tip.id = "tip"; tip.setAttribute("role", "tooltip"); document.body.appendChild(tip);
  const esc = s => String(s).replace(/[&<>"]/g, c => ({{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}}[c]));
  const showTip = a => {{ tip.innerHTML = `<b>${{esc(a.dataset.term)}}</b>${{esc(a.dataset.def)}}<small>Cliquer pour ouvrir le glossaire</small>`;
    tip.style.display = "block"; const r = a.getBoundingClientRect(), w = tip.offsetWidth, h = tip.offsetHeight;
    let x = Math.min(Math.max(8, r.left + r.width/2 - w/2), innerWidth - w - 8), y = r.bottom + 8;
    if(y + h > innerHeight - 8) y = r.top - h - 8;
    tip.style.left = x + "px"; tip.style.top = y + "px"; }};
  const hide = () => tip.style.display = "none";
  document.addEventListener("mouseover", ev => {{ const a = ev.target.closest && ev.target.closest("a.term[data-def]"); a ? showTip(a) : hide(); }});
  document.addEventListener("focusin", ev => {{ const a = ev.target.closest && ev.target.closest("a.term[data-def]"); a ? showTip(a) : hide(); }});
  document.addEventListener("scroll", hide, true); }})();
// à l'ouverture : on ferme les autres menus et on garde la liste dans l'écran, quelle que soit sa largeur
document.querySelectorAll("details.menu").forEach(d => d.addEventListener("toggle", () => {{ if(!d.open) return;
  document.querySelectorAll("details.menu[open]").forEach(o => {{ if(o !== d) o.open = false; }});
  const dd = d.querySelector(".dd"); dd.style.left = "auto"; dd.style.right = "0";
  if(dd.getBoundingClientRect().left < 8){{ dd.style.left = "0"; dd.style.right = "auto"; }}
  const r = dd.getBoundingClientRect(); if(r.right > innerWidth - 8) dd.style.left = (innerWidth - 8 - r.width - d.getBoundingClientRect().left) + "px"; }}));
</script>"""

def correction_url(page=""):
    """Formulaire de signalement GitHub pré-rempli (.github/ISSUE_TEMPLATE/correction.yml), titré avec la page."""
    return f"{brand.REPO}/issues/new?template=correction.yml&title={quote('Correction : ' + page)}&page={quote(page)}"

def correction(page=""):
    where = f" sur « {e(page)} »" if page else ""
    return (f'<a href="{e(correction_url(page))}">Proposer une correction</a>{where} : un formulaire guidé, '
            f'sans connaître le code (il faut un compte GitHub, gratuit).')

def foot(extra="", page="", fix=True):
    """fix=False quand la page porte déjà son propre « Proposer une correction » (dossiers) : pas de doublon en pied de page."""
    return f"""<footer><div class="wrap">{extra}{e(brand.NAME)} est un projet indépendant et open source. Code sous licence MIT,
textes et données sous licence CC BY 4.0.{" " + correction(page) if fix else ""}</div></footer>"""

# ---------- Français des phrases générées : un nom au milieu d'une phrase, et les contractions à/de + article ----------
import re as _re
_ART = _re.compile(r"^(Les|Le|La|L['’])(?=\s|\w)")

def mid(name):
    """Nom placé au milieu d'une phrase : seul un ARTICLE initial perd sa majuscule (« Le Hamas » → « le Hamas »),
    jamais un nom propre (« Israël » reste « Israël »)."""
    return _ART.sub(lambda m: m.group().lower(), name, count=1)

def _contract(prep, name):
    """Chaque terme d'une coordination reprend la préposition : « au Hamas et au Jihad islamique », « à Israël et aux États-Unis »."""
    def one(n):
        if n.startswith("les "):
            return {"à": "aux ", "de": "des "}[prep] + n[4:]
        if n.startswith("le "):
            return {"à": "au ", "de": "du "}[prep] + n[3:]
        if prep == "de" and _re.match(r"[aeiouyhéèêàâîôûAEIOUYHÉÈ]", n) and not n.startswith(("la ", "l'", "l’")):
            return "d'" + n
        return f"{prep} {n}"
    return " et ".join(one(p) for p in mid(name).split(" et "))

def a(name):
    """« à » + nom, avec contraction : à + le → au, à + les → aux (« au Hamas », « aux Forces de soutien rapide », « à Israël »)."""
    return _contract("à", name)

def de(name):
    """« de » + nom, avec contraction et élision : du Hamas, des Forces…, d'Israël, de l'Iran, de la Russie."""
    return _contract("de", name)

def write(out):
    (out / "style.css").write_text(CSS.replace("__DARK__", DARK).strip() + "\n", encoding="utf-8")
    (out / "favicon.svg").write_text(FAVICON, encoding="utf-8")
