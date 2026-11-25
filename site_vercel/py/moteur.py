# -*- coding: utf-8 -*-
# Moteur de SAMS côté navigateur : mêmes fonctions que dashboard/serveur.py (chat, outil, évaluation, labo).
import json, time
import numpy as np

class AgentClassiqueSansEtat(AgentClassique):
    nom = "Agent classique SANS état"
    def tour(self, texte, env):
        self.etat.reset(); return super().tour(texte, env)
FABRIQUES = {"baseline": AgentBaseline, "classique": AgentClassique, "classique_sans_etat": AgentClassiqueSansEtat}
JEUX = {"TEST": TEST, "DEV": DEV, "PARA": PARAPHRASES}

def propre(x):
    if isinstance(x, dict): return {str(k): propre(v) for k, v in x.items()}
    if isinstance(x, (list, tuple, set)): return [propre(v) for v in x]
    if isinstance(x, (np.integer,)): return int(x)
    if isinstance(x, (np.floating,)): return None if np.isnan(x) else round(float(x), 3)
    if isinstance(x, float): return None if x != x else round(x, 3)
    if isinstance(x, (np.bool_,)): return bool(x)
    return x

def lignes_eval(df, traces):
    d = {(r.scenario, int(r.tour)): r for r in df.itertuples()}
    out = []
    for t in traces:
        r = d[(t["scenario"], int(t["tour"]))]
        out.append({"scenario": t["scenario"], "tour": int(t["tour"]), "categorie": r.categorie, "user": t["user"],
                    "appels": [{"outil": o, "args": a, "statut": s} for o, a, s in t["appels"]], "reponse": t["reponse"],
                    "succes": bool(r.succes), "cause": r.cause, "causes": list(r.causes), "type_attendu": r.type_attendu,
                    "type_observe": r.type_observe, "latence": round(float(r.latence_s), 2)})
    return out

SESSIONS = {}
def discuter(sid, agent_id, texte, indisponibles=()):
    cle = (sid, agent_id)
    if cle not in SESSIONS: SESSIONS[cle] = {"agent": FABRIQUES[agent_id](), "env": Environnement()}
    s = SESSIONS[cle]
    if indisponibles: s["env"].indisponibles = set(indisponibles)
    env, agent = s["env"], s["agent"]
    i0 = len(env.journal); t0 = time.time()
    intents = detecter_intention(texte)
    ent = {k: v for k, v in extraire_entites(texte).items() if v}
    rep = agent.tour(texte, env)
    appels = [{"outil": a["outil"], "args": a["arguments"], "resultat": a.get("resultat"), "bloque": a["bloque"]} for a in env.journal[i0:]]
    etat = agent.etat.resume() if hasattr(agent, "etat") else "aucune mémoire (la baseline oublie tout)"
    return {"texte": rep["texte"], "intentions": [[i, round(p, 3)] for i, p in intents], "entites": ent, "appels": appels,
            "memoire": etat, "latence": round(time.time() - t0, 3)}

def traiter(route, corps):
    c = json.loads(corps or "{}")
    if route == "/api/chat":
        r = discuter(c.get("session", "defaut"), c.get("agent", "classique"), c["texte"], c.get("indisponibles", []))
    elif route == "/api/chat/reset":
        for k in [k for k in SESSIONS if k[0] == c.get("session", "defaut")]: del SESSIONS[k]
        r = {"ok": True}
    elif route == "/api/outil":
        r = {"resultat": Environnement(c.get("indisponibles", [])).appeler(c["outil"], c.get("args", {}))}
    elif route == "/api/evaluer":
        sc = next(s for s in JEUX[c.get("jeu", "TEST")] if s["id"] == c["scenario"])
        df, tr = evaluer_agent(FABRIQUES[c.get("agent", "classique")](), [sc])
        r = lignes_eval(df, tr)
    elif route == "/api/labo":
        df, tr = evaluer_agent(FABRIQUES[c.get("agent", "classique")](), JEUX[c.get("jeu", "TEST")])
        r = {"metriques": metriques(df), "categories": tableau_categories(df).to_dict(), "lignes": lignes_eval(df, tr)}
    else:
        r = {"erreur": "route inconnue : " + route}
    return json.dumps(propre(r), ensure_ascii=False)
