# -*- coding: utf-8 -*-
"""Compare votre annotation manuelle (grille_audit_30_tours.xlsx) aux verdicts de l'évaluateur automatique.
Calcule : accord brut, kappa de Cohen (+ IC 95 % bootstrap), matrice de confusion, précision / rappel de l'évaluateur, liste des désaccords.
Usage : python calculer_kappa.py
"""
import os
import numpy as np
import pandas as pd

ICI = os.path.dirname(os.path.abspath(__file__))
g = pd.read_excel(os.path.join(ICI, "grille_audit_30_tours.xlsx"), sheet_name="Grille")
k = pd.read_csv(os.path.join(ICI, "cle_verdicts_evaluateur.csv"), encoding="utf-8-sig")
col = "VOTRE VERDICT (réussi / échec)"
g[col] = g[col].astype(str).str.strip().str.lower().replace({"reussi": "réussi", "echec": "échec", "nan": ""})
vides = g[~g[col].isin(["réussi", "échec"])]
if len(vides): raise SystemExit(f"{len(vides)} ligne(s) sans verdict valide (n° {list(vides['n°'])}) : écrivez « réussi » ou « échec ».")
d = g.merge(k[["n°", "verdict_evaluateur", "cause_evaluateur"]], on="n°")
h, e = (d[col] == "réussi").to_numpy(), (d["verdict_evaluateur"] == "réussi").to_numpy()

def kappa(h, e):
    po = (h == e).mean()
    pe = h.mean() * e.mean() + (1 - h.mean()) * (1 - e.mean())
    return (po - pe) / (1 - pe) if pe < 1 else 1.0, po
kap, po = kappa(h, e)
rng = np.random.default_rng(42); boots = []
for _ in range(2000):
    i = rng.integers(0, len(h), len(h)); boots.append(kappa(h[i], e[i])[0])
lo, hi = np.nanpercentile(boots, [2.5, 97.5])

print(f"Tours annotés : {len(d)}")
print(f"Accord brut (humain = évaluateur) : {100 * po:.1f} %")
print(f"Kappa de Cohen : {kap:.3f}  (IC 95 % bootstrap : {lo:.2f} – {hi:.2f})")
print("Lecture (Landis & Koch) : < 0,20 faible | 0,21–0,40 passable | 0,41–0,60 modéré | 0,61–0,80 substantiel | > 0,80 quasi parfait\n")
print("Matrice de confusion (lignes = vous, colonnes = évaluateur) :")
print(pd.crosstab(d[col], d["verdict_evaluateur"], margins=True), "\n")
vp = ((~h) & (~e)).sum()      # échec détecté par les deux
print(f"Échecs réels repérés par l'évaluateur (rappel des échecs) : {vp}/{(~h).sum()}")
print(f"Échecs signalés par l'évaluateur confirmés par vous (précision) : {vp}/{(~e).sum()}\n")
des = d[h != e]
print(f"=== {len(des)} désaccord(s) à commenter dans le rapport ===")
for _, r in des.iterrows():
    print(f"n°{r['n°']:>2} [{r['système']} · {r['scénario']} t{r['tour']}] vous : {r[col]} | évaluateur : {r['verdict_evaluateur']} ({r['cause_evaluateur'] or '—'})")
    phrase, reponse = r["phrase de l'utilisateur"], str(r["réponse de l'agent"])[:160]
    print(f"      « {phrase} » -> {reponse}")
