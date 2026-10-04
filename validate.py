"""python validate.py  → vérifie network.yaml. Code de sortie 1 s'il y a des erreurs.
Tourne aussi en CI (.github/workflows/validate.yml) sur chaque changement du graphe."""
import re, sys
from datetime import date
import network

KINDS = {"state", "non_state", "bloc", "party", "person", "company", "passage"}
TYPES = {"arms", "financial", "training", "troops", "intelligence", "political", "economic", "dual_use", "service"}
STATUSES = {"active", "reduced", "ended", "alleged"}
CONFIDENCES = {"high", "medium", "low"}
STALE_MONTHS = 6

def months_since(ym, today=None):
    t = today or date.today()
    y, m = map(int, ym.split("-"))
    return (t.year - y) * 12 + t.month - m

def check(actors, edges, today=None, aligns=None):
    errors, warnings = [], []
    for aid, a in actors.items():
        if not a.get("name"):
            errors.append(f"acteur {aid} : name manquant")
        if a.get("kind") not in KINDS:
            errors.append(f"acteur {aid} : kind « {a.get('kind')} » invalide ({', '.join(sorted(KINDS))})")
        # un territoire sans code pays (Somaliland) est admis s'il fournit lui-même son drapeau et ses coordonnées
        if a.get("kind") == "state" and not re.fullmatch(r"[A-Z]{2}", aid) and not (a.get("flag") and a.get("coords")):
            errors.append(f"acteur {aid} : un État doit avoir un id ISO2 en majuscules, ou des champs flag et coords")
        if a.get("flag") is not None and not re.fullmatch(r"(https://\S+|flags/[\w.-]+)", str(a["flag"])):
            errors.append(f"acteur {aid} : flag doit être une URL https ou un fichier de data/flags/ (« flags/nom.svg »)")
        if a.get("kind") == "non_state" and not re.fullmatch(r"[A-Z]{2}", str(a.get("base", ""))):
            warnings.append(f"acteur {aid} : non étatique sans base ISO2 (pas de fiche pays hôte)")
        if a.get("kind") in ("party", "person", "company") and not re.fullmatch(r"[A-Z]{2}", str(a.get("base", ""))):
            errors.append(f"acteur {aid} : un parti, une personne ou une entreprise doit avoir une base ISO2 (pays d'ancrage)")
        if a.get("kind") == "passage":
            if a.get("coords") is None:
                errors.append(f"acteur {aid} : un passage doit avoir des coords [lat, lon]")
            for r in a.get("riparian") or []:
                if actors.get(r, {}).get("kind") != "state":
                    errors.append(f"acteur {aid} : riverain « {r} » n'est pas un État de actors")
            if not (a.get("sources") and all("http" in str(x) for x in a["sources"])):
                errors.append(f"acteur {aid} : un passage doit citer ses sources avec URL")
        if a.get("wikidata") is not None and not re.fullmatch(r"Q\d+", str(a["wikidata"])):
            errors.append(f"acteur {aid} : wikidata doit être un identifiant Qxxx")
        c = a.get("coords")
        if c is not None and not (isinstance(c, list) and len(c) == 2
                                  and all(isinstance(x, (int, float)) for x in c)
                                  and -90 <= c[0] <= 90 and -180 <= c[1] <= 180):
            errors.append(f"acteur {aid} : coords doit être [lat, lon]")
        if a.get("kind") == "bloc" and c is None:
            warnings.append(f"acteur {aid} : bloc sans coords, absent de la carte")
        for bloc in a.get("member_of") or []:
            if actors.get(bloc, {}).get("kind") != "bloc":
                errors.append(f"acteur {aid} : member_of « {bloc} » n'est pas un bloc de actors")
        if a.get("note") and a.get("kind") in ("party", "person") and a["note"] and "sources" in a \
                and not all(isinstance(x, str) and "http" in x for x in a["sources"]):
            warnings.append(f"acteur {aid} : source de la note sans URL")

    # compte rendu « En bref » de la page Relations : chaque acteur a son article, écrit à la main dans cross.ART
    import cross as _cross
    for aid in actors:
        if aid not in _cross.ART:
            warnings.append(f"acteur {aid} : pas d'article dans cross.ART (« le », « la », « l' », « les » ou vide) — phrases du compte rendu fausses")

    # dirigeants et personnes : une personne n'est un nœud que si elle a une relation PROPRE (cf. network.yaml)
    involved = {x.get("from") for x in edges} | {x.get("to") for x in edges}
    for aid, a in actors.items():
        ld = a.get("leader")
        if isinstance(ld, str):
            if actors.get(ld, {}).get("kind") != "person":
                errors.append(f"acteur {aid} : leader « {ld} » n'est pas un acteur person")
        elif isinstance(ld, dict):
            if not ld.get("name"):
                errors.append(f"acteur {aid} : leader sans name")
            if ld.get("wikidata") is not None and not re.fullmatch(r"Q\d+", str(ld["wikidata"])):
                errors.append(f"acteur {aid} : leader.wikidata doit être un identifiant Qxxx")
        elif ld is not None:
            errors.append(f"acteur {aid} : leader doit être un id de personne ou {{name, wikidata, role}}")
        if a.get("kind") == "person" and aid not in involved:
            warnings.append(f"acteur {aid} : personne sans relation propre — en faire le leader de son institution ?")

    seen = set()
    for i, e in enumerate(edges, 1):
        where = f"arête {i} ({e.get('from')} → {e.get('to')})"
        for end in ("from", "to"):
            if e.get(end) not in actors:
                errors.append(f"{where} : {end} « {e.get(end)} » absent de actors")
        if e.get("from") == e.get("to"):
            errors.append(f"{where} : un acteur ne peut pas se soutenir lui-même")
        if (e.get("from"), e.get("to")) in seen:
            errors.append(f"{where} : doublon — fusionner les types dans une seule arête")
        seen.add((e.get("from"), e.get("to")))
        types = e.get("types") or []
        if not types or not set(types) <= TYPES:
            errors.append(f"{where} : types {types} invalides ({', '.join(sorted(TYPES))})")
        if e.get("status") not in STATUSES:
            errors.append(f"{where} : status « {e.get('status')} » invalide")
        if e.get("confidence") not in CONFIDENCES:
            errors.append(f"{where} : confidence « {e.get('confidence')} » invalide")
        sources = e.get("sources") or []
        if not sources or not all(isinstance(s, str) and s.strip() for s in sources):
            errors.append(f"{where} : au moins une source requise")
        elif not any("http" in s for s in sources):
            warnings.append(f"{where} : aucune source avec URL")
        dates = {}
        for k in ("since", "until"):
            if e.get(k) is not None:
                d = str(e[k])
                if not re.fullmatch(r"\d{4}(-\d{2})?", d):
                    errors.append(f"{where} : {k} « {d} » doit être au format AAAA ou AAAA-MM")
                dates[k] = d
        if "since" not in dates:
            warnings.append(f"{where} : pas de date de début (since)")
        if len(dates) == 2 and dates["until"] < dates["since"]:
            errors.append(f"{where} : until antérieur à since")
        if e.get("status") == "ended" and "until" not in dates:
            warnings.append(f"{where} : relation terminée sans date de fin (until)")
        v = str(e.get("verified", ""))
        if not re.fullmatch(r"\d{4}-\d{2}", v):
            errors.append(f"{where} : verified « {v} » doit être au format AAAA-MM")
        elif months_since(v, today) > STALE_MONTHS:
            warnings.append(f"{where} : vérifiée en {v}, à revoir (> {STALE_MONTHS} mois)")

    ids = set()
    for g in (aligns or {}).get("groups", []):
        k = g.get("id")
        if k in ids:
            errors.append(f"groupe {k} : id en double")
        ids.add(k)
        if g.get("kind") == "forum":
            if g.get("bloc") is not None or g.get("level") != 0:
                errors.append(f"groupe {k} : un forum n'a ni bloc ni niveau (level: 0)")
        elif g.get("bloc") not in (aligns.get("blocs") or {}):
            errors.append(f"groupe {k} : bloc « {g.get('bloc')} » absent de blocs")
        if g.get("level") not in (0, 1, 2, 3):
            errors.append(f"groupe {k} : level doit valoir 0, 1, 2 ou 3")
        if g.get("entity") and g["entity"] not in actors:
            errors.append(f"groupe {k} : entity « {g['entity']} » absente de actors")
        srcs = g.get("sources") or []
        if not srcs or not all(isinstance(x, str) and "http" in x for x in srcs):
            errors.append(f"groupe {k} : sources avec URL requises")
        members = set(g.get("members") or [])
        for m in members:
            if not re.fullmatch(r"[A-Z]{2}", str(m)):
                errors.append(f"groupe {k} : membre « {m} » n'est pas un code ISO2")
        # dates d'adhésion / de départ : AAAA-MM ; joined pour un membre actuel, left pour un ancien membre
        if g.get("since") is not None and not re.fullmatch(r"\d{4}-\d{2}", str(g["since"])):
            errors.append(f"groupe {k} : since « {g['since']} » doit être au format AAAA-MM")
        for field, must_be_member in (("joined", True), ("left", False)):
            for m, d in (g.get(field) or {}).items():
                if not re.fullmatch(r"\d{4}-\d{2}", str(d)):
                    errors.append(f"groupe {k} : {field}[{m}] « {d} » doit être au format AAAA-MM")
                if (m in members) != must_be_member:
                    errors.append(f"groupe {k} : {field}[{m}] — " + ("absent de members" if must_be_member
                                  else "un ancien membre ne doit plus figurer dans members"))
    for b, v in ((aligns or {}).get("blocs") or {}).items():
        if not re.fullmatch(r"#[0-9a-fA-F]{6}", str(v.get("color", ""))):
            errors.append(f"bloc {b} : color doit être #rrggbb")

    return errors, warnings

def check_tensions(tensions, actors, today=None):
    """Tensions : acteurs connus, type et statut valides, sources avec URL, dates au bon format."""
    errors, warnings = [], []
    for i, t in enumerate(tensions, 1):
        where = f"tension {i} ({t.get('from')} – {t.get('to')})"
        for k in ("from", "to"):
            if t.get(k) not in actors:
                errors.append(f"{where} : {k} « {t.get(k)} » absent de actors")
        if t.get("type") not in network.TENSION_TYPES:
            errors.append(f"{where} : type « {t.get('type')} » invalide ({', '.join(network.TENSION_TYPES)})")
        if t.get("status") not in ("active", "reduced", "ended"):
            errors.append(f"{where} : status « {t.get('status')} » invalide (active, reduced, ended)")
        if t.get("confidence") not in CONFIDENCES:
            errors.append(f"{where} : confidence « {t.get('confidence')} » invalide")
        srcs = t.get("sources") or []
        if not srcs or not all(isinstance(x, str) and "http" in x for x in srcs):
            errors.append(f"{where} : sources avec URL requises")
        for k in ("since", "until"):
            if t.get(k) is not None and not re.fullmatch(r"\d{4}(-\d{2})?", str(t[k])):
                errors.append(f"{where} : {k} « {t[k]} » doit être au format AAAA ou AAAA-MM")
        v = str(t.get("verified", ""))
        if not re.fullmatch(r"\d{4}-\d{2}", v):
            errors.append(f"{where} : verified « {v} » doit être au format AAAA-MM")
        elif months_since(v, today) > STALE_MONTHS:
            warnings.append(f"{where} : vérifiée en {v}, à revoir (> {STALE_MONTHS} mois)")
    return errors, warnings

def check_dossiers(dossiers, actors, edges):
    """dossiers.yaml : acteurs connus, récit sourcé, dates valides ; signale les soutiens sans « pourquoi »."""
    errors, warnings = [], []
    has_url = lambda xs: bool(xs) and all(isinstance(x, str) and "http" in x for x in xs)
    for x in dossiers:
        k = x.get("id", "?")
        if not re.fullmatch(r"[a-z0-9-]+", str(k)):
            errors.append(f"dossier {k} : id en minuscules, chiffres et tirets seulement (nom de page)")
        for f in ("title", "since", "verified", "lede", "sides"):
            if not x.get(f):
                errors.append(f"dossier {k} : champ {f} manquant")
        if len(x.get("sides") or []) != 2:
            errors.append(f"dossier {k} : il faut exactement deux camps (sides)")
        if not x.get("card"):
            warnings.append(f"dossier {k} : pas de résumé court (card) pour la carte d'accueil")
        elif len(x["card"]) > 130:
            errors.append(f"dossier {k} : card trop long ({len(x['card'])} caractères, 130 au plus) — il serait coupé sur l'accueil")
        if not has_url(x.get("lede_sources")):
            errors.append(f"dossier {k} : lede_sources avec URL requises")
        for f in ("origins", "toll", "now", "history"):
            if x.get(f) and not has_url(x[f].get("sources")):
                errors.append(f"dossier {k} : {f} sans source avec URL")
        for i, st in enumerate(x.get("stakes") or []):
            if not has_url(st.get("sources")):
                errors.append(f"dossier {k} : enjeu {st.get('label', i)} sans source avec URL")
        for t in x.get("council") or []:
            if not re.fullmatch(r"\d{4}(-\d{2})?", str(t.get("date"))) or not t.get("text") or not has_url([t.get("source")]):
                errors.append(f"dossier {k} : Conseil de sécurité, entrée « {t.get('text')} » : date AAAA(-MM), texte et source avec URL requis")
        for t in x.get("timeline") or []:
            if not re.fullmatch(r"\d{4}(-\d{2})?", str(t.get("date"))):
                errors.append(f"dossier {k} : date de frise « {t.get('date')} » au format AAAA ou AAAA-MM")
            if not has_url([t.get("source")]):
                errors.append(f"dossier {k} : événement « {t.get('text')} » sans source avec URL")
        mp = x.get("map")
        if mp:
            for kind in ("pins", "routes", "flows"):
                for it in mp.get(kind) or []:
                    if not has_url([it.get("source")]):
                        errors.append(f"dossier {k} : carte, {kind} « {it.get('label')} » sans source avec URL")
            reg = mp.get("regions")
            if reg:
                if not has_url(reg.get("sources")):
                    errors.append(f"dossier {k} : carte, zones de contrôle sans source avec URL")
                import json, pathlib
                f = pathlib.Path(__file__).with_name("data") / "maps" / f"{reg.get('file')}.geojson"
                if not f.exists():
                    errors.append(f"dossier {k} : carte, contours data/maps/{reg.get('file')}.geojson introuvables")
                else:
                    known = {ft["properties"]["name"] for ft in json.loads(f.read_text())["features"]}
                    for name in [n for grp in (reg.get("sides") or []) for n in grp] + (reg.get("contested") or []):
                        if name not in known:
                            errors.append(f"dossier {k} : carte, région « {name} » absente de {f.name}")
        import dossier as _dossier
        reg = _dossier.registry()
        for pp in x.get("people") or []:
            if pp.get("who") not in reg:
                errors.append(f"dossier {k} : personne « {pp.get('who')} » absente du registre people de dossiers.yaml")
            elif reg[pp["who"]].get("actor") and reg[pp["who"]]["actor"] not in actors:
                errors.append(f"dossier {k} : personne « {pp['who']} » : acteur « {reg[pp['who']]['actor']} » inconnu")
            if not pp.get("role") or not pp.get("text"):
                errors.append(f"dossier {k} : personne « {pp.get('who')} » sans role ou sans text")
            if not has_url(pp.get("sources")):
                errors.append(f"dossier {k} : personne « {pp.get('who')} » sans source avec URL (une action documentée)")
        for sd in x.get("sides") or []:
            ids = set(sd.get("actors") or [])
            for a in ids - set(actors):
                errors.append(f"dossier {k} : acteur « {a} » absent de network.yaml")
            if not has_url(sd.get("sources")):
                errors.append(f"dossier {k} : camp « {sd.get('name')} » sans source avec URL")
            for e in edges:
                if e["to"] in ids and e["from"] not in ids and e["status"] != "ended" and not e.get("why"):
                    warnings.append(f"dossier {k} : soutien {e['from']} → {e['to']} sans « why »")
    return errors, warnings

def check_mediations(meds, actors):
    """Médiations : acteurs connus, deux parties distinctes du médiateur, statut, dates et sources avec URL."""
    errors = []
    for i, m in enumerate(meds):
        where = f"médiation {i} ({m.get('mediator')} entre {', '.join(m.get('between') or [])})"
        between = m.get("between") or []
        for a in [m.get("mediator"), *between]:
            if a not in actors:
                errors.append(f"{where} : acteur inconnu « {a} »")
        if len(set(between)) != 2 or m.get("mediator") in between:
            errors.append(f"{where} : il faut deux parties distinctes du médiateur (between)")
        if m.get("status") not in ("active", "reduced", "ended"):
            errors.append(f"{where} : status « {m.get('status')} » invalide (active, reduced, ended)")
        if m.get("confidence") not in CONFIDENCES:
            errors.append(f"{where} : confidence « {m.get('confidence')} » invalide")
        if not any("http" in str(s) for s in m.get("sources") or []):
            errors.append(f"{where} : aucune source avec URL")
        for k in ("since", "until"):
            if m.get(k) and not re.fullmatch(r"\d{4}(-\d{2})?", str(m[k])):
                errors.append(f"{where} : {k} au format AAAA ou AAAA-MM")
    return errors

def check_dependencies(deps, actors):
    """Leviers (dépendances mesurées) : acteurs connus et distincts, type connu, part entre 0 et 100, année AAAA,
    source avec URL. Une part chiffrée et sourcée, jamais une note d'importance."""
    errors = []
    for i, x in enumerate(deps):
        where = f"dépendance {i} ({x.get('from')} → {x.get('supplier')})"
        for k in ("from", "supplier"):
            if x.get(k) not in actors:
                errors.append(f"{where} : acteur {k} inconnu « {x.get(k)} »")
        if x.get("from") == x.get("supplier"):
            errors.append(f"{where} : un pays ne dépend pas de lui-même")
        if x.get("type") not in network.DEPENDENCY_TYPES:
            errors.append(f"{where} : type « {x.get('type')} » invalide ({', '.join(network.DEPENDENCY_TYPES)})")
        if x.get("type") == "trade" and x.get("direction") not in ("exports", "imports"):
            errors.append(f"{where} : direction obligatoire pour le commerce (exports ou imports)")
        if x.get("type") in ("minerals", "food") and not x.get("resource"):
            errors.append(f"{where} : resource obligatoire pour le type {x['type']} (ex. « terres rares », « blé »)")
        if not isinstance(x.get("share"), (int, float)) or not 0 < x["share"] <= 100:
            errors.append(f"{where} : share doit être un pourcentage entre 0 et 100")
        if not re.fullmatch(r"\d{4}", str(x.get("year", ""))):
            errors.append(f"{where} : year au format AAAA")
        if x.get("status", "active") not in ("active", "reduced", "ended"):
            errors.append(f"{where} : status « {x.get('status')} » invalide")
        if not any("http" in str(s) for s in x.get("sources") or []):
            errors.append(f"{where} : aucune source avec URL")
    return errors

def check_glossary(terms):
    """glossaire.yaml : ids uniques et en forme d'ancre, champs obligatoires, aucune forme (terme ou variante) partagée."""
    errors, warnings, ids, forms = [], [], set(), {}
    for i, t in enumerate(terms):
        where = f"glossaire {t.get('id', i)}"
        for k in ("id", "term", "definition"):
            if not t.get(k):
                errors.append(f"{where} : champ « {k} » manquant")
        tid = t.get("id", "")
        if tid in ids:
            errors.append(f"{where} : id en double")
        ids.add(tid)
        if tid and not re.fullmatch(r"[a-z0-9-]+", tid):
            errors.append(f"{where} : id « {tid} » invalide (minuscules, chiffres, tirets)")
        for f in [t.get("term", ""), *(t.get("aliases") or [])]:
            if f in forms:
                errors.append(f"{where} : « {f} » déjà utilisé par {forms[f]}")
            forms[f] = tid
    return errors, warnings

def check_term_refs(terms, sources=("build.py", "pages.py", "dossier.py", "method.py")):
    """Termes du glossaire cités dans le code (T("id"), Q("id"), term("id"), tables *_TERM) : tous doivent exister."""
    from pathlib import Path
    ids, errors = {t.get("id") for t in terms}, []
    pat = re.compile(r'\b(?:T|Q|term)\(\s*"([a-z0-9-]+)"|_TERM\s*=\s*\{([^}]*)\}')
    for f in sources:
        text = Path(__file__).with_name(f).read_text(encoding="utf-8")
        for m in pat.finditer(text):
            refs = [m.group(1)] if m.group(1) else re.findall(r':\s*"([a-z0-9-]+)"', m.group(2))
            errors += [f"{f} : terme du glossaire inconnu « {r} »" for r in refs if r not in ids]
    return errors

def check_presets(presets, actors, aligns, dossiers):
    """presets.yaml : vues, acteurs, types, organisations et dossiers existants ; champs cohérents avec la vue."""
    errors, warnings, ids = [], [], set()
    types, tensions = TYPES, set(network.TENSION_TYPES)
    groups, dos = {g["id"] for g in aligns["groups"]}, {x["id"] for x in dossiers}
    for p in presets:
        where = f"preset {p.get('id')}"
        if not p.get("id") or p["id"] in ids or not p.get("question"):
            errors.append(f"{where} : id manquant ou en double, ou question manquante")
        ids.add(p.get("id"))
        if p.get("view") not in {"graphe", "carte", "organisations"}:
            errors.append(f"{where} : vue « {p.get('view')} » invalide (graphe, carte, organisations)")
        for a in ([p["focus"]] if p.get("focus") else []) + list(p.get("around") or []):
            if a not in actors:
                errors.append(f"{where} : acteur inconnu « {a} »")
        if p.get("dossier") and p["dossier"] not in dos:
            errors.append(f"{where} : dossier inconnu « {p['dossier']} »")
        for k, allowed in (("types", types), ("tensions", tensions), ("kinds", {"core", "non_state", "party", "person"})):
            for v in p.get(k) or []:
                if v not in allowed:
                    errors.append(f"{where} : {k} « {v} » invalide")
        if p.get("panel") not in (None, "received"):
            errors.append(f"{where} : panel « {p['panel']} » invalide (received)")
        if p.get("colormode") not in (None, "formal", "votes"):
            errors.append(f"{where} : colormode « {p['colormode']} » invalide")
        if p.get("view") == "organisations":
            orgs = p.get("orgs") or []
            if not 2 <= len(orgs) <= 6:
                errors.append(f"{where} : vue Organisations : 2 à 6 organisations (orgs)")
            for g in orgs:
                if g not in groups:
                    errors.append(f"{where} : organisation inconnue « {g} »")
        elif p.get("orgs") or p.get("highlight"):
            errors.append(f"{where} : orgs/highlight ne servent qu'à la vue organisations")
        if p.get("colormode") and p.get("view") != "carte":
            errors.append(f"{where} : colormode ne sert qu'à la vue carte")
    return errors, warnings

if __name__ == "__main__":
    import dossier, glossary, presets
    actors, edges = network.load()
    errors, warnings = check(actors, edges, aligns=network.alignments())
    de, dw = check_dossiers(dossier.load(), actors, edges)
    te, tw = check_tensions(network.tensions(), actors)
    de, dw = de + te, dw + tw
    ge, gw = check_glossary(glossary.load())
    ge += check_mediations(network.mediations(), actors)
    ge += check_dependencies(network.dependencies(), actors)
    ge += check_term_refs(glossary.load())
    pe, pw = check_presets(presets.load(), actors, network.alignments(), dossier.load())
    de, dw = de + ge + pe, dw + gw + pw
    errors, warnings = errors + de, warnings + dw
    for w in warnings:
        print(f"⚠️  {w}")
    for e in errors:
        print(f"❌ {e}")
    print(f"\n{len(actors)} acteurs, {len(edges)} arêtes — {len(errors)} erreur(s), {len(warnings)} avertissement(s)")
    sys.exit(1 if errors else 0)
