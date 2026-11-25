# -*- coding: utf-8 -*-
"""Construit la grille d'audit manuel de l'évaluateur (30 tours) à partir des résultats de l'exécution finale.

Entrées : resultats_bruts/LLM_Qwen2_5_3B_Instruct_{A_direct,B_plan}.pkl (téléchargés depuis Google Drive)
          ../Projet10_Agent_Outils_TALN.ipynb (pour relire la définition des scénarios TEST)
Sorties : grille_audit_30_tours.xlsx  -> à remplir à la main, SANS voir le verdict de l'évaluateur
          cle_verdicts_evaluateur.csv -> verdicts de l'évaluateur (ne pas ouvrir avant d'avoir fini l'annotation)
Usage   : python construire_grille_audit.py
"""
import json, os, pickle, random, re, io, contextlib
import pandas as pd

ICI = os.path.dirname(os.path.abspath(__file__))
NB = os.path.join(ICI, "..", "Projet10_Agent_Outils_TALN.ipynb")
SYSTEMES = {"A. direct": "LLM_Qwen2_5_3B_Instruct_A_direct.pkl", "B. plan": "LLM_Qwen2_5_3B_Instruct_B_plan.pkl"}
N_PAR_SYSTEME, GRAINE = 15, 42

# 1) relire les scénarios TEST depuis le notebook (on exécute seulement les cellules jusqu'à la définition de TEST)
import matplotlib; matplotlib.use("Agg")
g = {"display": lambda *a, **k: None}
for c in json.load(open(NB, encoding="utf-8"))["cells"]:
    if c["cell_type"] != "code": continue
    s = "".join(c["source"]).replace('drive.mount("/content/drive")', "pass")
    with contextlib.redirect_stdout(io.StringIO()): exec(s, g)
    if "assert len(TEST) == 60" in s: break
SPEC = {(sc["id"], k + 1): (sc, t) for sc in g["TEST"] for k, t in enumerate(sc["tours"])}

TYPES = {"answer": "répondre (avec les bonnes infos)", "clarify": "poser une question de précision", "refuse": "refuser poliment",
         "inform_failure": "dire honnêtement que l'info est absente / l'outil en panne"}
def attendu(t):
    types = t["type"] if isinstance(t["type"], list) else [t["type"]]
    txt = " ou ".join(TYPES[x] for x in types)
    if t["calls"]: txt += " | outils attendus : " + "; ".join(f"{o}({', '.join(f'{k}={v}' for k, v in a.items())})" for o, a in t["calls"])
    if t["facts"]: txt += " | doit mentionner : " + ", ".join(map(str, t["facts"]))
    if t["interdits"]: txt += " | interdit : " + ", ".join(o for o, _ in t["interdits"])
    return txt.replace("{'$contains': ", "contient ").replace("{'$any': True}", "(libre)").replace("{'$absent': True}", "(aucun module)")

# 2) tirage stratifié : pour chaque système, moitié tours réussis / moitié ratés (selon l'évaluateur), catégories variées
rng = random.Random(GRAINE); lignes, cle = [], []
for nom, fichier in SYSTEMES.items():
    df, traces, _ = pickle.load(open(os.path.join(ICI, "resultats_bruts", fichier), "rb"))
    tr = {(t["scenario"], t["tour"]): t for t in traces}
    df = df.assign(cle=list(zip(df.scenario, df.tour)))
    choix = []
    for ok, n in ((False, N_PAR_SYSTEME // 2), (True, N_PAR_SYSTEME - N_PAR_SYSTEME // 2)):
        groupe = df[df.succes == ok]
        par_cat = {c: list(gr.cle) for c, gr in groupe.groupby("categorie")}
        for l in par_cat.values(): rng.shuffle(l)
        while len([x for x in choix if x[1] == ok]) < n and any(par_cat.values()):   # tourniquet sur les catégories
            for cat in sorted(par_cat):
                if par_cat[cat] and len([x for x in choix if x[1] == ok]) < n: choix.append((par_cat[cat].pop(), ok))
    for (sid, k), ok in choix:
        sc, t = SPEC[(sid, k)]; trace = tr[(sid, k)]
        ligne = df[(df.scenario == sid) & (df.tour == k)].iloc[0]
        lignes.append({"système": nom, "scénario": sid, "catégorie": sc["categorie"], "tour": k, "phrase de l'utilisateur": t["user"],
                       "comportement attendu": attendu(t),
                       "outils appelés par l'agent": "; ".join(f"{o}({', '.join(f'{a}={v}' for a, v in args.items())}){' [BLOQUÉ]' if s != 'ok' else ''}"
                                                              for o, args, s in trace["appels"]) or "aucun",
                       "réponse de l'agent": trace["reponse"]})
        cle.append({"système": nom, "scénario": sid, "tour": k, "verdict_evaluateur": "réussi" if ligne.succes else "échec",
                    "cause_evaluateur": ligne.cause})
rng.shuffle(lignes)                                   # ordre aléatoire : on ne devine pas le verdict à la position
grille = pd.DataFrame(lignes); grille.insert(0, "n°", range(1, len(grille) + 1))
grille["VOTRE VERDICT (réussi / échec)"] = ""; grille["VOTRE CAUSE si échec (facultatif)"] = ""; grille["commentaire"] = ""
cle = pd.DataFrame(cle).merge(grille[["n°", "système", "scénario", "tour"]], on=["système", "scénario", "tour"])
cle.sort_values("n°").to_csv(os.path.join(ICI, "cle_verdicts_evaluateur.csv"), index=False, encoding="utf-8-sig")

# 3) fichier Excel lisible
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.datavalidation import DataValidation
chemin = os.path.join(ICI, "grille_audit_30_tours.xlsx")
with pd.ExcelWriter(chemin, engine="openpyxl") as w:
    grille.to_excel(w, sheet_name="Grille", index=False)
    pd.DataFrame({"Consigne": [
        "1. Pour chaque ligne, lisez la phrase, le comportement attendu, les outils appelés et la réponse de l'agent.",
        "2. Décidez vous-même si l'agent a RÉUSSI ce tour (bon comportement, bons outils/arguments, bonnes informations, rien d'interdit).",
        "3. Écrivez « réussi » ou « échec » dans la colonne VOTRE VERDICT (liste déroulante). La cause est facultative.",
        "4. N'ouvrez PAS cle_verdicts_evaluateur.csv avant d'avoir fini : sinon l'audit n'est plus indépendant.",
        "5. Enregistrez, puis lancez : python calculer_kappa.py",
        "Causes possibles : outil_manquant, arguments_incorrects, absence_de_clarification, absence_de_refus, refus_ou_question_injustifie, "
        "hallucination, reponse_incomplete, action_interdite_executee, erreur_format"]}).to_excel(w, sheet_name="Consignes", index=False)
    ws = w.sheets["Grille"]
    largeurs = {"A": 5, "B": 11, "C": 10, "D": 16, "E": 5, "F": 45, "G": 55, "H": 50, "I": 70, "J": 18, "K": 22, "L": 30}
    for col, l in largeurs.items(): ws.column_dimensions[col].width = l
    for row in ws.iter_rows(min_row=2):
        for cell in row: cell.alignment = Alignment(wrap_text=True, vertical="top")
    for cell in ws[1]: cell.font = Font(bold=True); cell.alignment = Alignment(wrap_text=True, vertical="center")
    jaune = PatternFill("solid", fgColor="FFF2CC")
    for r in range(1, len(grille) + 2):
        for col in "JKL": ws[f"{col}{r}"].fill = jaune
    dv = DataValidation(type="list", formula1='"réussi,échec"', allow_blank=True); ws.add_data_validation(dv); dv.add(f"J2:J{len(grille) + 1}")
    ws.freeze_panes = "B2"; w.sheets["Consignes"].column_dimensions["A"].width = 140

print(f"Grille : {chemin} ({len(grille)} tours)")
print(grille.groupby(["système", "catégorie"]).size().unstack(fill_value=0))
print("Répartition (verdict évaluateur, caché) :", cle.groupby(["système", "verdict_evaluateur"]).size().to_dict())
