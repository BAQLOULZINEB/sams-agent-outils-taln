# -*- coding: utf-8 -*-
"""
Construit la version EN LIGNE de SAMS (site statique pour Vercel) dans ../site_vercel.

    & "C:\\Users\\zineb\\AppData\\Local\\Python\\pythoncore-3.14-64\\python.exe" construire_site_vercel.py

- Les données en lecture (résultats, scénarios, traces, base fictive, audit) sont précalculées ici en JSON.
- Le code du notebook (outils, évaluateur, baseline, agent classique) est copié dans site_vercel/py/ :
  il s'exécute EN DIRECT dans le navigateur du visiteur grâce à Pyodide (Python compilé en WebAssembly).
- Les agents LLM restent relus depuis l'exécution GPU sur Colab, exactement comme en local.
Le script vérifie que le code copié donne les mêmes résultats que le serveur local.
"""
import json, os, shutil, sys, io, contextlib

ICI = os.path.dirname(os.path.abspath(__file__))
PROJET = os.path.dirname(ICI)
SORTIE = os.path.join(PROJET, "site_vercel")
NB = os.path.join(PROJET, "Projet10_Agent_Outils_TALN.ipynb")

# ------------------------------------------------------------ 1. code du notebook pour le navigateur
REMPLACE_INTENTION = '''from sklearn.pipeline import Pipeline, FeatureUnion
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score, accuracy_score
# Version navigateur : on entraîne directement le détecteur retenu dans le notebook
# (régression logistique, TF-IDF mots + caractères), sans refaire la comparaison des 5 modèles.
def vect_mots():  return TfidfVectorizer(preprocessor=norm, ngram_range=(1, 2), sublinear_tf=True)
def vect_chars(): return TfidfVectorizer(preprocessor=norm, analyzer="char_wb", ngram_range=(2, 5), sublinear_tf=True)
CLF_INTENT = Pipeline([("v", FeatureUnion([("w", vect_mots()), ("ch", vect_chars())])), ("c", LogisticRegression(C=10, max_iter=2000))])
CLF_INTENT.fit(X_int, y_int)
def detecter_intention(texte):
    proba = CLF_INTENT.predict_proba([texte])[0]
    ordre = np.argsort(-proba)
    return [(CLF_INTENT.classes_[i], float(proba[i])) for i in ordre[:3]]
'''
morceaux = []
for c in json.load(open(NB, encoding="utf-8"))["cells"]:
    if c["cell_type"] != "code": continue
    s = "".join(c["source"])
    if "CANDIDATS = {" in s:
        s = REMPLACE_INTENTION
    elif "CLF_INTENT = CANDIDATS" in s:
        continue
    s = s.replace('drive.mount("/content/drive")', "pass").replace("import matplotlib.pyplot as plt", "plt = None")
    morceaux.append(s)
    if "class AgentClassique" in s: break
SEP = "\n\n# " + "=" * 60 + "\n\n"
CODE_NB = "display = lambda *a, **k: None\n\n" + SEP.join(morceaux)
CODE_NB = "# -*- coding: utf-8 -*-\n# Code du notebook Projet10 (cellules jusqu'à l'agent classique), exécuté dans le navigateur par Pyodide.\n" + CODE_NB

MOTEUR = r'''# -*- coding: utf-8 -*-
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
'''

# ------------------------------------------------------------ 2. vérifier que le code copié = le serveur local
print("1/3  Vérification du code copié (exécution native)…")
G = {"__name__": "__site__"}
with contextlib.redirect_stdout(io.StringIO()):
    exec(CODE_NB, G); exec(MOTEUR, G)
sys.path.insert(0, ICI)
with contextlib.redirect_stdout(io.StringIO()):
    import serveur as S                                  # calcule tout ce que le serveur local calcule
for agent in ("baseline", "classique"):
    lab = json.loads(G["traiter"]("/api/labo", json.dumps({"agent": agent, "jeu": "TEST"})))
    attendu = S.METRIQUES[agent]["Tâches réussies (%)"]
    assert abs(lab["metriques"]["Tâches réussies (%)"] - attendu) < 1e-6, (agent, lab["metriques"]["Tâches réussies (%)"], attendu)
    print(f"     {agent:10} : {lab['metriques']['Tâches réussies (%)']:.1f} % (serveur local : {attendu:.1f} %)  OK")
for phrase in ["Quelle est la moyenne de Yassine ?", "Et sa note en TALN ?", "Écris un poème", "réserve la B14 mercredi 16:15-18:15"]:
    a = [i for i, _ in G["detecter_intention"](phrase)]; b = [i for i, _ in S.G["detecter_intention"](phrase)]
    assert a == b, (phrase, a, b)
print("     détecteur d'intention : mêmes prédictions  OK")

# ------------------------------------------------------------ 3. écrire le site
print("2/3  Écriture du site…")
os.makedirs(os.path.join(SORTIE, "data"), exist_ok=True); os.makedirs(os.path.join(SORTIE, "py"), exist_ok=True)
for f in os.listdir(os.path.join(ICI, "static")):
    src = os.path.join(ICI, "static", f)
    if os.path.isdir(src): shutil.copytree(src, os.path.join(SORTIE, f), dirs_exist_ok=True)
    else: shutil.copy2(src, os.path.join(SORTIE, f))
for f in os.listdir(os.path.join(ICI, "vercel")):                 # static-api.js, worker.js, vercel.json
    shutil.copy2(os.path.join(ICI, "vercel", f), os.path.join(SORTIE, f))
idx = open(os.path.join(SORTIE, "index.html"), encoding="utf-8").read()
if "static-api.js" not in idx:
    idx = idx.replace('<script src="icons.js"></script>', '<script src="static-api.js"></script>\n<script src="icons.js"></script>')
open(os.path.join(SORTIE, "index.html"), "w", encoding="utf-8").write(idx)
open(os.path.join(SORTIE, "py", "sams_code.py"), "w", encoding="utf-8").write(CODE_NB)
open(os.path.join(SORTIE, "py", "moteur.py"), "w", encoding="utf-8").write(MOTEUR)

def ecrire(nom, obj):
    json.dump(S.propre(obj), open(os.path.join(SORTIE, "data", nom), "w", encoding="utf-8"), ensure_ascii=False)

ecrire("resume.json", {"resultats": S.RESULTATS, "direct": S.METRIQUES, "stats_llm": S.STATS_LLM,
                       "dispo": list(S.TRACES), "nb": {k: len(v) for k, v in S.JEUX.items()}})
for jeu, sc in S.JEUX.items():
    ecrire(f"scenarios_{jeu}.json", [{"id": s["id"], "categorie": s["categorie"], "indisponibles": s["indisponibles"],
                                     "tours": [{"user": t["user"], **S.spec_lisible(t)} for t in s["tours"]]} for s in sc])
for sid, tr in S.TRACES.items(): ecrire(f"traces_{sid}.json", tr)
G2 = S.G
ecrire("donnees.json", {"etudiants": list(G2["ETUDIANTS"].values()), "emploi": G2["EMPLOI"], "salles": G2["SALLES"],
                        "documents": [{**d, "piege": d["id"] in G2["DOCS_INJECTES"]} for d in G2["DOCUMENTS"]],
                        "outils": G2["SCHEMAS"], "modules": {m: v[0] for m, v in G2["MODULES"].items()}})
ecrire("audit.json", S.audit_lignes())
ecrire("kappa.json", S.audit_kappa())
import pandas as pd
cle = pd.read_csv(S.CLE, encoding="utf-8-sig")
ecrire("cle_audit.json", {int(r["n°"]): {"verdict_evaluateur": r["verdict_evaluateur"],
                                         "cause_evaluateur": r["cause_evaluateur"] if isinstance(r["cause_evaluateur"], str) else ""}
                          for r in cle.to_dict("records")})
print("3/3  Site prêt :", SORTIE)
