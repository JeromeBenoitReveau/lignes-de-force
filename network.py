"""Lecture/requêtes du graphe network.yaml."""
from pathlib import Path
import yaml

PATH = Path(__file__).with_name("network.yaml")

def _data():
    return yaml.safe_load(PATH.read_text(encoding="utf-8"))

def load():
    data = _data()
    return data["actors"], data["edges"]

def tensions():
    """Guerres, sanctions, revendications, rivalités et guerres commerciales (clé tensions de network.yaml), hors soutiens."""
    return _data().get("tensions") or []

def mediations():
    """Médiations (clé mediations de network.yaml) : qui négocie entre qui. Ni soutien ni tension, hors calcul des blocs."""
    return _data().get("mediations") or []

def dependencies():
    """Leviers d'influence (clé dependencies de network.yaml) : parts chiffrées et sourcées d'une ressource tirée d'un
    fournisseur (armes importées…) : {from, supplier, type, share, year, period, status, sources, note}. Hors calcul des blocs."""
    return _data().get("dependencies") or []

DEPENDENCY_TYPES = {"arms": "armes", "gas": "gaz", "oil": "pétrole", "minerals": "minerais", "food": "denrées", "debt": "dette", "trade": "commerce", "chips": "puces", "electricity": "électricité", "transit": "transit"}

TENSION_TYPES = {"war": "guerre", "sanctions": "sanctionne", "claims": "revendique un territoire de", "rivalry": "rivalité avec",
                 "trade_war": "guerre commerciale avec", "blockade": "entrave la navigation dans"}

def leader(actors, aid):
    """Dirigeant d'un acteur : {name, role, sources, photo_key, actor} ou None. Le champ leader est soit un dict
    décrivant la personne (photo sous « leader:<id> » dans data/people.json), soit l'id d'un acteur « person »."""
    ld = actors.get(aid, {}).get("leader")
    if isinstance(ld, str):
        p = actors.get(ld, {})
        return {"name": p.get("name", ld), "role": p.get("note", ""), "photo_key": ld, "actor": ld}
    if isinstance(ld, dict):
        return {**ld, "photo_key": f"leader:{aid}", "actor": None}
    return None

ALIGN_PATH = Path(__file__).with_name("alignments.yaml")
LEVELS = {3: "défense mutuelle", 2: "partenariat stratégique", 1: "candidature ou participation gelée", 0: "intégration"}

def alignments():
    return yaml.safe_load(ALIGN_PATH.read_text(encoding="utf-8"))

def formal_ties(al):
    """{iso: [groupe, …]} pour tous les pays cités dans alignments.yaml."""
    ties = {}
    for g in al["groups"]:
        for iso in g["members"]:
            ties.setdefault(iso, []).append(g)
    return ties

def org_countries(al):
    """Tous les pays membres (actuels ou passés) d'une organisation d'alignments.yaml."""
    return {iso for g in al["groups"] for iso in [*g["members"], *(g.get("left") or {})]}

def influence(actors, edges, al):
    """Bloc d'influence et niveau de chaque pays ou acteur — déduits, jamais attribués à la main.
    member    : lien formel (alignments.yaml) ; level = niveau le plus élevé, par bloc
    satellite : sans lien formel, tous ses soutiens actifs viennent de membres (niveau ≥ 2) d'un même bloc
    contested : liens formels de même niveau avec deux blocs, ou soutiens venant de plusieurs blocs
    none      : ni lien formel ni soutien de bloc ; partis et personnalités ne sont jamais classés"""
    ties = formal_ties(al)
    def best(iso):
        per_bloc = {}
        for g in ties.get(iso, []):
            if g["level"] > 0 and g.get("bloc"):
                per_bloc[g["bloc"]] = max(per_bloc.get(g["bloc"], 0), g["level"])
        return per_bloc
    def bloc_of(aid):  # bloc d'un soutien : le sien s'il est membre (niveau ≥ 2), sinon celui de son pays d'ancrage
        for x in (aid, actors.get(aid, {}).get("base")):
            pb = {b: l for b, l in best(x).items() if l >= 2}
            if len(pb) == 1:
                return next(iter(pb))
        return None
    out = {}
    for aid in set(actors) | set(ties):
        a = actors.get(aid, {"kind": "state"})
        tied = [g["id"] for g in ties.get(aid, [])]
        pb = best(aid)
        via_all = sorted({e["from"] for e in edges if e["to"] == aid and e["status"] == "active"})
        if a["kind"] in ("party", "person", "company", "passage"):   # jamais classés dans un bloc
            out[aid] = {"bloc": None, "role": "none", "level": 0, "via": [], "ties": tied}
        elif pb:
            top = max(pb.values())
            leaders = sorted(b for b, l in pb.items() if l == top)
            out[aid] = ({"bloc": leaders[0], "role": "member", "level": top, "via": via_all, "ties": tied}
                        if len(leaders) == 1 else
                        {"bloc": None, "role": "contested", "level": top, "blocs": leaders, "via": via_all, "ties": tied})
        else:
            via = via_all
            of = [bloc_of(v) for v in via]
            blocs = sorted(set(of) - {None})
            if not blocs or (len(blocs) == 1 and None in of):
                # aucun soutien de bloc, ou un soutien hors bloc à côté : pas de satellite
                # (ex. Soudan soutenu par la Turquie, membre de l'OTAN, et par l'Égypte, hors bloc)
                out[aid] = {"bloc": None, "role": "none", "level": 0, "via": via, "ties": tied}
            elif len(blocs) == 1:
                out[aid] = {"bloc": blocs[0], "role": "satellite", "level": 1, "via": via, "ties": tied}
            else:
                out[aid] = {"bloc": None, "role": "contested", "level": 1, "blocs": blocs, "via": via, "ties": tied}
    return out

def name(actors, aid):
    return actors.get(aid, {}).get("name", aid)

def supporters_of(aid, edges):
    return [e for e in edges if e["to"] == aid and e["status"] != "ended"]

def supported_by(aid, edges):
    return [e for e in edges if e["from"] == aid and e["status"] != "ended"]

def proxies_in(country_iso, actors):
    """Acteurs non étatiques basés dans un pays (ex. YE → houthis)."""
    return [a for a, v in actors.items() if v.get("base") == country_iso and v["kind"] == "non_state"]

def based_in(country_iso, actors, kinds=("party", "person", "company")):
    """Partis et personnalités rattachés à un pays (ex. DE → afd)."""
    return [a for a, v in actors.items() if v.get("base") == country_iso and v["kind"] in kinds]

def members_of(bloc, actors):
    return [a for a, v in actors.items() if bloc in (v.get("member_of") or [])]

def subgraph(ids, edges, hops=1):
    """Arêtes autour d'un ensemble d'acteurs, sur n sauts."""
    nodes, out = set(ids), []
    for _ in range(hops):
        new = [e for e in edges if e["from"] in nodes or e["to"] in nodes]
        for e in new:
            nodes |= {e["from"], e["to"]}
        out = new
    return out
