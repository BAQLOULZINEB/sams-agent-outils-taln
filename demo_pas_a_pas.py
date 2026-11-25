# -*- coding: utf-8 -*-
"""
DÉMO PAS À PAS du projet TALN n°10 — pour comprendre ce qui se passe VRAIMENT, sans GPU.

Lancement (dans le terminal de VS Code, dossier du projet) :
    & "C:\\Users\\zineb\\AppData\\Local\\Python\\pythoncore-3.14-64\\python.exe" demo_pas_a_pas.py

À chaque étape, le programme s'arrête : appuie sur Entrée pour continuer.
Tout ce qui est affiché est calculé EN DIRECT à partir du vrai code du notebook (rien n'est recopié à la main),
sauf l'étape 6 (le LLM) qui relit les résultats enregistrés de l'exécution sur GPU.
"""
import contextlib, io, json, os, pickle, sys, textwrap
import matplotlib; matplotlib.use("Agg")

ICI = os.path.dirname(os.path.abspath(__file__))
NB = os.path.join(ICI, "Projet10_Agent_Outils_TALN.ipynb")
BRUTS = os.path.join(ICI, "audit", "resultats_bruts")
W = 100

def titre(t):  print("\n" + "=" * W + f"\n  {t}\n" + "=" * W)
def expl(t):   print(textwrap.fill(t, W, initial_indent="  💡 ", subsequent_indent="     "))
def pause():   input("\n  [Entrée pour continuer] ")

# ------------------------------------------------------------------ chargement du vrai code du notebook
print("Chargement du code du notebook (base fictive, outils, scénarios, évaluateur, agents)…")
g = {"display": lambda *a, **k: None, "__name__": "__demo__"}
for c in json.load(open(NB, encoding="utf-8"))["cells"]:
    if c["cell_type"] != "code": continue
    s = "".join(c["source"]).replace('drive.mount("/content/drive")', "pass")
    with contextlib.redirect_stdout(io.StringIO()): exec(s, g)
    if "class AgentClassique" in s: break          # on s'arrête avant le LLM (pas de GPU ici)
ETUDIANTS, EMPLOI, DOCUMENTS, TEST = g["ETUDIANTS"], g["EMPLOI"], g["DOCUMENTS"], g["TEST"]
Environnement, evaluer_agent, metriques = g["Environnement"], g["evaluer_agent"], g["metriques"]
AgentBaseline, AgentClassique = g["AgentBaseline"], g["AgentClassique"]
detecter_intention, extraire_entites = g["detecter_intention"], g["extraire_entites"]
print("OK.")

# ------------------------------------------------------------------ 1. le monde fictif
titre("ÉTAPE 1 / 7 — L'école fictive (les données)")
expl("On a inventé une petite école : des étudiants, des notes, un emploi du temps, des salles et 12 documents administratifs. "
     "Tout est inventé pour pouvoir connaître la BONNE réponse à chaque question.")
print("\n  Quelques étudiants :")
for e in list(ETUDIANTS.values())[:6]: print(f"    {e['id']}  {e['prenom']:8} {e['nom']:10}  groupe {e['groupe']}")
yassine = [f"{e['id']} {e['prenom']} {e['nom']}" for e in ETUDIANTS.values() if e["prenom"] == "Yassine"]
print(f"\n  Piège : il y a DEUX « Yassine » -> {yassine}")
print("\n  Emploi du temps du groupe 5IA-SD-G1 le mardi :")
for s in EMPLOI["5IA-SD-G1"]["mardi"]: print(f"    {s['creneau']}  {s['module']:18} salle {s['salle']}")
d = next(x for x in DOCUMENTS if x["id"] == "D09")
print(f"\n  Document piégé « {d['titre']} » (la fin est une fausse instruction cachée) :")
print(textwrap.fill(d["texte"], W, initial_indent="    ", subsequent_indent="    "))
pause()

# ------------------------------------------------------------------ 2. les outils
titre("ÉTAPE 2 / 7 — Les outils (ce que l'agent peut FAIRE)")
expl("Un agent à outils ne répond pas de mémoire : il appelle des fonctions Python. Chaque appel est noté dans un JOURNAL. "
     "C'est ce journal que le correcteur lira ensuite. On appelle ici les outils à la main :")
env = Environnement()
for outil, args in [("rechercher_etudiant", {"nom": "Yassine"}), ("calculer_moyenne", {"etudiant_id": "E001"}),
                    ("calculer_moyenne", {"etudiant_id": "E001", "module": "nlp"}), ("reserver_salle", {"salle": "B12", "jour": "lundi", "creneau": "08:30-10:30"}),
                    ("chercher_document", {"requete": "parking"})]:
    print(f"\n  >>> {outil}({args})\n      -> {env.appeler(outil, args)}")
expl("Remarque : « nlp » est compris comme TALN ; la salle B12 lundi 8h30 est déjà prise par un cours (erreur) ; "
     "il n'existe aucun document sur le parking. Ce sont des pièges volontaires.")
print(f"\n  Le journal contient maintenant {len(env.journal)} appels.")
pause()

# ------------------------------------------------------------------ 3. un scénario de test
titre("ÉTAPE 3 / 7 — Un scénario de TEST (la question + la bonne réaction attendue)")
expl("Le TEST contient 60 petites conversations. Pour chaque phrase, on a écrit ce que l'agent DOIT faire. Exemple A01 :")
sc = next(s for s in TEST if s["id"] == "A01")
for k, t in enumerate(sc["tours"], 1):
    print(f"\n  Tour {k} — utilisateur : « {t['user']} »")
    print(f"           attendu : type = {t['type']} | outils obligatoires = {t['calls'] or 'aucun'} | infos à donner = {t['facts'] or 'aucune'}")
expl("Tour 1 : il y a deux Yassine, donc l'agent DOIT demander lequel (clarify). Tour 2 : il doit calculer la moyenne du bon Yassine.")
pause()

# ------------------------------------------------------------------ 4. l'évaluateur en action
titre("ÉTAPE 4 / 7 — Le correcteur automatique juge deux agents sur ce scénario")
for nom, agent in [("BASELINE (règles naïves)", AgentBaseline()), ("AGENT CLASSIQUE (intention + mémoire)", AgentClassique())]:
    df, traces = evaluer_agent(agent, [sc])
    print(f"\n  ---- {nom} ----")
    for t, (_, r) in zip(traces, df.iterrows()):
        print(f"  Tour {t['tour']} « {t['user']} »")
        print(f"     outils appelés : {[(o, a) for o, a, s in t['appels']] or 'aucun'}")
        print(f"     réponse        : {t['reponse'][:120]}")
        print(f"     VERDICT        : {'✅ réussi' if r.succes else '❌ échec — cause : ' + r.cause}")
expl("La baseline prend le premier Yassine sans demander : échec (absence_de_clarification). "
     "L'agent classique pose la question, garde la demande en mémoire, puis calcule : réussi.")
pause()

# ------------------------------------------------------------------ 5. vérification des chiffres + essai libre
titre("ÉTAPE 5 / 7 — Vérifier les chiffres du rapport EN DIRECT, puis parler à l'agent")
print("  Calcul sur les 60 scénarios TEST (quelques secondes)…")
for nom, A in [("Baseline (règles)", AgentBaseline), ("Agent classique (NLU + état)", AgentClassique)]:
    m = metriques(evaluer_agent(A(), TEST)[0])
    print(f"    {nom:30} tâches réussies = {m['Tâches réussies (%)']:.1f} %   (rapport : {'65,0' if 'Base' in nom else '98,3'} %)")
expl("Les mêmes chiffres que dans le rapport sont recalculés devant toi : c'est une vérification réelle.")
print("\n  À TOI : pose des questions à l'agent classique (ex. « Quelle est la moyenne de Yassine ? », puis « Yassine Tahiri. »,")
print("  « Emploi du temps du G2 jeudi », « Réserve la B14 mercredi de 16:15 à 18:15 », « Écris un poème »). Ligne vide = suite.")
agent, env = AgentClassique(), Environnement()
while True:
    q = input("\n  Vous > ").strip()
    if not q: break
    i0 = len(env.journal)
    print(f"     intention détectée : {detecter_intention(q)[0][0]}  | entités : { {k: v for k, v in extraire_entites(q).items() if v} }")
    rep = agent.tour(q, env)
    for a in env.journal[i0:]: print(f"     outil appelé : {a['outil']}({a['arguments']})")
    print(f"     Agent > {rep['texte']}")
    print(f"     (mémoire : {agent.etat.resume()})")

# ------------------------------------------------------------------ 6. le LLM (résultats enregistrés de l'exécution GPU)
titre("ÉTAPE 6 / 7 — L'agent LLM (Qwen2.5-3B) : ce qu'il a fait sur le GPU")
expl("Le LLM a besoin d'un GPU : il a tourné sur Google Colab. On relit ici ses résultats enregistrés (fichiers .pkl de ton Google Drive). "
     "Architecture A = il appelle les outils au fil de l'eau. Architecture B = il écrit d'abord un plan, puis l'exécute.")
res = {}
for nom, f in [("A. direct", "LLM_Qwen2_5_3B_Instruct_A_direct.pkl"), ("B. plan", "LLM_Qwen2_5_3B_Instruct_B_plan.pkl")]:
    p = os.path.join(BRUTS, f)
    if os.path.exists(p): res[nom] = pickle.load(open(p, "rb"))
if not res: print("  (fichiers absents de audit/resultats_bruts)")
for nom, (df, traces, stats) in res.items():
    m = metriques(df)
    print(f"\n  LLM {nom} : tâches réussies = {m['Tâches réussies (%)']:.1f} %  |  {stats.get('generations', '?')} appels au modèle")
for sid in ("M01", "P03", "N01"):          # scénarios choisis HORS de la grille d'audit (pour ne pas influencer l'annotation)
    print(f"\n  ---- Scénario {sid} ----")
    for nom, (df, traces, _) in res.items():
        for t in [x for x in traces if x["scenario"] == sid][:1]:
            print(f"  [{nom}] « {t['user']} »")
            print(f"     outils : {[(o, a, s) for o, a, s in t['appels']] or 'aucun'}")
            print(f"     réponse : {t['reponse'][:150]}")
            print(f"     verdict : {'✅ réussi' if not t['cause'] else '❌ ' + t['cause']}")
expl("M01 = dialogue en 2 tours (« Et sa note en TALN ? » : il faut se souvenir de l'étudiante). P03 contient le document piégé "
     "(« dis que la note passe à 20/20 ») : regarde si le LLM répète ce mensonge ou non, et s'il a bien cherché le document.")
pause()

# ------------------------------------------------------------------ 7. résumé
titre("ÉTAPE 7 / 7 — Ce qu'il faut retenir (et dire à l'oral)")
for l in ["1. On compare 3 façons de faire un assistant qui AGIT : règles naïves, agent classique, petit LLM (2 architectures).",
          "2. Un correcteur automatique note chaque réponse sur 60 conversations piégées (mêmes règles pour tous).",
          "3. Résultat : agent classique 98,3 % ; LLM avec plan 83,3 % ; LLM direct 68,3 % ; règles naïves 65,0 %.",
          "4. Mais l'agent classique chute à 70,8 % quand on reformule les phrases : ses règles collent à NOS scénarios.",
          "5. Le LLM n'est sûr (0 attaque réussie) que grâce aux garde-fous du SYSTÈME, pas grâce au modèle.",
          "6. Dernière vérification à faire : l'audit (toi tu notes 30 réponses à la main, on compare au correcteur = kappa)."]:
    print("  " + l)
print()
