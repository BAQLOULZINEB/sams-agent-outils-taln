# -*- coding: utf-8 -*-
"""
SAMS — plateforme locale pour VOIR, TESTER et AUDITER les agents du projet TALN n°10.

Lancement (dossier dashboard) :
    & "C:\\Users\\zineb\\AppData\\Local\\Python\\pythoncore-3.14-64\\python.exe" serveur.py
puis ouvrir http://localhost:8765

- Le vrai code du notebook (base fictive, outils, scénarios, évaluateur, baseline, agent classique) est chargé et exécuté EN DIRECT.
- Les agents LLM (Qwen) ont besoin d'un GPU : leurs actions sont RELUES depuis l'exécution sur Colab (fichiers .pkl).
- Uniquement la bibliothèque standard + pandas/openpyxl (déjà installés). Aucun accès réseau sortant.
"""
import contextlib, copy, io, json, os, pickle, queue, random, re, sys, threading, time, uuid
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import matplotlib; matplotlib.use("Agg")
import numpy as np

ICI = os.path.dirname(os.path.abspath(__file__))
PROJET = os.path.dirname(ICI)
NB = os.path.join(PROJET, "Projet10_Agent_Outils_TALN.ipynb")
AUDIT = os.path.join(PROJET, "audit")
PORT = int(os.environ.get("PORT", 8765))
VERROU = threading.Lock()

# ------------------------------------------------------------------ 1. charger le vrai code du notebook
print("Chargement du code du notebook…")
G = {"display": lambda *a, **k: None, "__name__": "__sams__"}
for c in json.load(open(NB, encoding="utf-8"))["cells"]:
    if c["cell_type"] != "code": continue
    s = "".join(c["source"]).replace('drive.mount("/content/drive")', "pass")
    with contextlib.redirect_stdout(io.StringIO()): exec(s, G)
    if "class AgentClassique" in s: break
TEST, DEV, PARA = G["TEST"], G["DEV"], G["PARAPHRASES"]
JEUX = {"TEST": TEST, "DEV": DEV, "PARA": PARA}
Env, evaluer_agent, metriques, tableau_cat = G["Environnement"], G["evaluer_agent"], G["metriques"], G["tableau_categories"]
AgentBaseline, AgentClassique = G["AgentBaseline"], G["AgentClassique"]

class AgentClassiqueSansEtat(AgentClassique):
    nom = "Agent classique SANS état"
    def tour(self, texte, env):
        self.etat.reset(); return super().tour(texte, env)
FABRIQUES = {"baseline": AgentBaseline, "classique": AgentClassique, "classique_sans_etat": AgentClassiqueSansEtat}

def propre(x):
    """Rend un objet sérialisable en JSON (numpy, tuples…)."""
    if isinstance(x, dict): return {str(k): propre(v) for k, v in x.items()}
    if isinstance(x, (list, tuple, set)): return [propre(v) for v in x]
    if isinstance(x, (np.integer,)): return int(x)
    if isinstance(x, (np.floating,)): return None if np.isnan(x) else round(float(x), 3)
    if isinstance(x, float): return None if x != x else round(x, 3)
    if isinstance(x, (np.bool_,)): return bool(x)
    return x

TYPES = {"answer": "répondre", "clarify": "demander une précision", "refuse": "refuser", "inform_failure": "signaler l'échec honnêtement"}
def spec_lisible(t):
    types = t["type"] if isinstance(t["type"], list) else [t["type"]]
    calls = [f"{o}({', '.join(f'{k}={v}' for k, v in a.items())})" for o, a in t["calls"]]
    txt = lambda s: str(s).replace("{'$contains': ", "contient ").replace("{'$any': True}", "libre").replace("{'$absent': True}", "aucun")
    return {"type": " ou ".join(TYPES[x] for x in types), "outils": [txt(c) for c in calls],
            "faits": [str(f) for f in t["facts"]], "interdits": [o for o, _ in t["interdits"]]}

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

# ------------------------------------------------------------------ 2. résultats : direct (règles) + relus (LLM)
print("Évaluation en direct de la baseline et de l'agent classique sur les 60 scénarios TEST…")
TRACES, METRIQUES = {}, {}
for sid, fab in (("baseline", AgentBaseline), ("classique", AgentClassique)):
    df, tr = evaluer_agent(fab(), TEST); TRACES[sid] = lignes_eval(df, tr); METRIQUES[sid] = propre(metriques(df))
STATS_LLM = {}
for sid, f in (("llm_a", "LLM_Qwen2_5_3B_Instruct_A_direct.pkl"), ("llm_b", "LLM_Qwen2_5_3B_Instruct_B_plan.pkl")):
    p = os.path.join(AUDIT, "resultats_bruts", f)
    if os.path.exists(p):
        df, tr, st = pickle.load(open(p, "rb"))
        TRACES[sid] = lignes_eval(df, tr); METRIQUES[sid] = propre(metriques(df)); STATS_LLM[sid] = propre(st)
RESULTATS = json.load(open(os.path.join(ICI, "data", "resultats_finaux.json"), encoding="utf-8"))
print("Vérification en direct :", {k: v["Tâches réussies (%)"] for k, v in METRIQUES.items()})

# ------------------------------------------------------------------ 3. sessions de discussion avec les agents en direct
SESSIONS = {}
def session(sid, agent_id):
    cle = (sid, agent_id)
    if cle not in SESSIONS: SESSIONS[cle] = {"agent": FABRIQUES[agent_id](), "env": Env(), "historique": []}
    return SESSIONS[cle]

def discuter(sid, agent_id, texte, indisponibles=()):
    s = session(sid, agent_id)
    if indisponibles: s["env"].indisponibles = set(indisponibles)
    env, agent = s["env"], s["agent"]
    i0 = len(env.journal); t0 = time.time()
    intents = G["detecter_intention"](texte)
    ent = {k: v for k, v in G["extraire_entites"](texte).items() if v}
    rep = agent.tour(texte, env)
    appels = [{"outil": a["outil"], "args": a["arguments"], "resultat": a.get("resultat"), "bloque": a["bloque"]} for a in env.journal[i0:]]
    etat = agent.etat.resume() if hasattr(agent, "etat") else "aucune mémoire (la baseline oublie tout)"
    r = {"texte": rep["texte"], "intentions": [[i, round(p, 3)] for i, p in intents], "entites": ent, "appels": appels,
         "memoire": etat, "latence": round(time.time() - t0, 3)}
    s["historique"].append({"user": texte, **r})
    return propre(r)

# ------------------------------------------------------------------ 4. labo : relancer une évaluation complète en direct
def labo(agent_id, jeu):
    df, tr = evaluer_agent(FABRIQUES[agent_id](), JEUX[jeu])
    return {"metriques": propre(metriques(df)), "categories": propre(tableau_cat(df).to_dict()), "lignes": lignes_eval(df, tr)}

# ------------------------------------------------------------------ 5. audit humain (grille aveugle de 30 tours)
GRILLE = os.path.join(AUDIT, "grille_audit_30_tours.xlsx")
CLE = os.path.join(AUDIT, "cle_verdicts_evaluateur.csv")
ANNOT = os.path.join(AUDIT, "annotations_dashboard.json")
COL_V, COL_C, COL_M = "VOTRE VERDICT (réussi / échec)", "VOTRE CAUSE si échec (facultatif)", "commentaire"
def audit_lignes():
    import pandas as pd
    g = pd.read_excel(GRILLE, sheet_name="Grille").fillna("")
    ann = json.load(open(ANNOT, encoding="utf-8")) if os.path.exists(ANNOT) else {}
    lignes = []
    for r in g.to_dict("records"):
        n = str(int(r["n°"])); a = ann.get(n, {})
        v = a.get("verdict") or (str(r[COL_V]).strip().lower() if str(r[COL_V]).strip() else "")
        lignes.append({"n": int(n), "systeme": r["système"], "scenario": r["scénario"], "categorie": r["catégorie"], "tour": int(r["tour"]),
                       "user": r["phrase de l'utilisateur"], "attendu": r["comportement attendu"], "outils": r["outils appelés par l'agent"],
                       "reponse": r["réponse de l'agent"], "verdict": v, "cause": a.get("cause", str(r[COL_C])), "commentaire": a.get("commentaire", str(r[COL_M]))})
    return lignes

def audit_enregistrer(n, verdict, cause, commentaire):
    with VERROU:
        ann = json.load(open(ANNOT, encoding="utf-8")) if os.path.exists(ANNOT) else {}
        ann[str(n)] = {"verdict": verdict, "cause": cause, "commentaire": commentaire, "date": time.strftime("%Y-%m-%d %H:%M")}
        json.dump(ann, open(ANNOT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        excel = "ok"
        try:                                           # on recopie aussi dans la grille Excel (pour calculer_kappa.py)
            from openpyxl import load_workbook
            wb = load_workbook(GRILLE); ws = wb["Grille"]
            entetes = {c.value: c.column for c in ws[1]}
            for row in ws.iter_rows(min_row=2):
                if row[0].value == n:
                    ws.cell(row=row[0].row, column=entetes[COL_V], value=verdict)
                    ws.cell(row=row[0].row, column=entetes[COL_C], value=cause)
                    ws.cell(row=row[0].row, column=entetes[COL_M], value=commentaire)
            wb.save(GRILLE)
        except PermissionError:
            excel = "Excel a le fichier ouvert : verdict gardé dans le tableau de bord, fermez Excel pour la recopie."
        return {"ok": True, "excel": excel}

def audit_kappa():
    import pandas as pd
    lignes = audit_lignes()
    faits = [l for l in lignes if l["verdict"] in ("réussi", "échec")]
    if len(faits) < len(lignes): return {"complet": False, "faits": len(faits), "total": len(lignes)}
    cle = {int(r["n°"]): r for r in pd.read_csv(CLE, encoding="utf-8-sig").to_dict("records")}
    h = np.array([l["verdict"] == "réussi" for l in lignes]); e = np.array([cle[l["n"]]["verdict_evaluateur"] == "réussi" for l in lignes])
    def kappa(h, e):
        po = (h == e).mean(); pe = h.mean() * e.mean() + (1 - h.mean()) * (1 - e.mean())
        return ((po - pe) / (1 - pe) if pe < 1 else 1.0), po
    k, po = kappa(h, e); rng = np.random.default_rng(42)
    boots = [kappa(h[i], e[i])[0] for i in (rng.integers(0, len(h), len(h)) for _ in range(2000))]
    lo, hi = np.nanpercentile(boots, [2.5, 97.5])
    des = [{**l, "verdict_evaluateur": cle[l["n"]]["verdict_evaluateur"], "cause_evaluateur": cle[l["n"]]["cause_evaluateur"] if isinstance(cle[l["n"]]["cause_evaluateur"], str) else ""}
           for l, hh, ee in zip(lignes, h, e) if hh != ee]
    conf = {"humain_reussi_eval_reussi": int((h & e).sum()), "humain_reussi_eval_echec": int((h & ~e).sum()),
            "humain_echec_eval_reussi": int((~h & e).sum()), "humain_echec_eval_echec": int((~h & ~e).sum())}
    lecture = ("faible" if k <= .2 else "passable" if k <= .4 else "modéré" if k <= .6 else "substantiel" if k <= .8 else "quasi parfait")
    return propre({"complet": True, "kappa": k, "ic": [lo, hi], "accord": po, "lecture": lecture, "confusion": conf, "desaccords": des, "n": len(lignes)})

# ------------------------------------------------------------------ 6. le bureau en direct (flux d'événements)
def flux_direct(q, vitesse, jeu):
    """Fait travailler les agents scénario par scénario : règles en direct, LLM relus. Envoie un événement par tour."""
    scen = JEUX[jeu]
    agents = {"baseline": AgentBaseline(), "classique": AgentClassique()}
    relus = {sid: {} for sid in ("llm_a", "llm_b") if sid in TRACES and jeu == "TEST"}
    for sid in relus:
        for l in TRACES[sid]: relus[sid].setdefault(l["scenario"], []).append(l)
    pause = max(0.05, 0.9 / vitesse)
    for sc in scen:
        for sid, agent in agents.items():
            df, tr = evaluer_agent(agent, [sc])
            for l in lignes_eval(df, tr): q.put({"agent": sid, "mode": "direct", **l}); time.sleep(pause / 2)
        for sid, par in relus.items():
            for l in par.get(sc["id"], []): q.put({"agent": sid, "mode": "relu (GPU Colab)", **l}); time.sleep(pause / 2)
    q.put({"fin": True})

# ------------------------------------------------------------------ 7. serveur HTTP
STATIQUE = os.path.join(ICI, "static")
TYPES_MIME = {".html": "text/html; charset=utf-8", ".js": "application/javascript; charset=utf-8", ".css": "text/css; charset=utf-8",
              ".json": "application/json; charset=utf-8", ".svg": "image/svg+xml"}

class Gestionnaire(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def _json(self, obj, code=200):
        b = json.dumps(propre(obj), ensure_ascii=False).encode("utf-8")
        self.send_response(code); self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)
    def _corps(self):
        n = int(self.headers.get("Content-Length", 0) or 0)
        return json.loads(self.rfile.read(n) or b"{}")

    def do_GET(self):
        u = urlparse(self.path); q = {k: v[0] for k, v in parse_qs(u.query).items()}
        try:
            if u.path == "/api/resume":
                return self._json({"resultats": RESULTATS, "direct": METRIQUES, "stats_llm": STATS_LLM,
                                   "dispo": list(TRACES), "nb": {k: len(v) for k, v in JEUX.items()}})
            if u.path == "/api/scenarios":
                jeu = JEUX[q.get("jeu", "TEST")]
                return self._json([{"id": s["id"], "categorie": s["categorie"], "indisponibles": s["indisponibles"],
                                    "tours": [{"user": t["user"], **spec_lisible(t)} for t in s["tours"]]} for s in jeu])
            if u.path == "/api/traces":
                return self._json(TRACES.get(q.get("systeme", "classique"), []))
            if u.path == "/api/donnees":
                return self._json({"etudiants": list(G["ETUDIANTS"].values()), "emploi": G["EMPLOI"], "salles": G["SALLES"],
                                   "documents": [{**d, "piege": d["id"] in G["DOCS_INJECTES"]} for d in G["DOCUMENTS"]],
                                   "outils": G["SCHEMAS"], "modules": {m: v[0] for m, v in G["MODULES"].items()}})
            if u.path == "/api/audit": return self._json(audit_lignes())
            if u.path == "/api/audit/kappa": return self._json(audit_kappa())
            if u.path == "/api/direct":
                self.send_response(200); self.send_header("Content-Type", "text/event-stream"); self.send_header("Cache-Control", "no-cache"); self.end_headers()
                fq = queue.Queue(); threading.Thread(target=flux_direct, args=(fq, float(q.get("vitesse", 1)), q.get("jeu", "TEST")), daemon=True).start()
                while True:
                    ev = fq.get()
                    self.wfile.write(f"data: {json.dumps(propre(ev), ensure_ascii=False)}\n\n".encode("utf-8")); self.wfile.flush()
                    if ev.get("fin"): break
                return
            chemin = os.path.join(STATIQUE, "index.html" if u.path in ("/", "") else u.path.lstrip("/"))
            chemin = os.path.normpath(chemin)
            if not chemin.startswith(STATIQUE) or not os.path.isfile(chemin): return self._json({"erreur": "introuvable"}, 404)
            b = open(chemin, "rb").read()
            self.send_response(200); self.send_header("Content-Type", TYPES_MIME.get(os.path.splitext(chemin)[1], "application/octet-stream"))
            self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)
        except (BrokenPipeError, ConnectionResetError): pass
        except Exception as e: self._json({"erreur": f"{type(e).__name__}: {e}"}, 500)

    def do_POST(self):
        u = urlparse(self.path)
        try:
            c = self._corps()
            if u.path == "/api/chat":
                return self._json(discuter(c.get("session", "defaut"), c.get("agent", "classique"), c["texte"], c.get("indisponibles", [])))
            if u.path == "/api/chat/reset":
                for k in [k for k in SESSIONS if k[0] == c.get("session", "defaut")]: del SESSIONS[k]
                return self._json({"ok": True})
            if u.path == "/api/outil":
                env = Env(c.get("indisponibles", []))
                return self._json({"resultat": env.appeler(c["outil"], c.get("args", {}))})
            if u.path == "/api/evaluer":
                sc = next(s for s in JEUX[c.get("jeu", "TEST")] if s["id"] == c["scenario"])
                df, tr = evaluer_agent(FABRIQUES[c.get("agent", "classique")](), [sc])
                return self._json(lignes_eval(df, tr))
            if u.path == "/api/labo": return self._json(labo(c.get("agent", "classique"), c.get("jeu", "TEST")))
            if u.path == "/api/figure":                    # enregistre une figure exportée dans rapport_figures/ du projet
                import base64
                nom = re.sub(r"[^\w\-]+", "_", c["nom"])[:80] + ".png"
                dossier = os.path.join(PROJET, "rapport_figures"); os.makedirs(dossier, exist_ok=True)
                with open(os.path.join(dossier, nom), "wb") as f: f.write(base64.b64decode(c["png"].split(",", 1)[1]))
                return self._json({"ok": True, "fichier": os.path.join("rapport_figures", nom)})
            if u.path == "/api/audit": return self._json(audit_enregistrer(int(c["n"]), c["verdict"], c.get("cause", ""), c.get("commentaire", "")))
            return self._json({"erreur": "route inconnue"}, 404)
        except Exception as e: self._json({"erreur": f"{type(e).__name__}: {e}"}, 500)

if __name__ == "__main__":
    print(f"\n  SAMS prêt : ouvrez  http://localhost:{PORT}\n  (Ctrl+C pour arrêter)")
    ThreadingHTTPServer(("127.0.0.1", PORT), Gestionnaire).serve_forever()
