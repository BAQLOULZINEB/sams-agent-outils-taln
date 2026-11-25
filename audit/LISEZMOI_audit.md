# Audit manuel de l'évaluateur (30 tours) — mode d'emploi

**Pourquoi ?** L'évaluateur automatique décide du comportement de l'agent en partie avec des **mots-clés**. Pour montrer qu'il est fiable,
on compare ses verdicts à un **jugement humain indépendant** sur un échantillon, et on mesure l'accord avec le **kappa de Cohen**
(accord corrigé du hasard : 0 = pas mieux que le hasard, 1 = accord parfait).

## Échantillon
- 30 tours de l'exécution finale (TEST) : **15 de LLM A. direct + 15 de LLM B. plan**.
- Tirage aléatoire (graine 42), **stratifié** : environ moitié tours jugés réussis / moitié ratés par l'évaluateur, toutes les catégories de pièges.
- Ordre mélangé, et le verdict de l'évaluateur est **caché** dans `cle_verdicts_evaluateur.csv` → annotation « à l'aveugle ».

## Étapes
1. Ouvrir `grille_audit_30_tours.xlsx` (onglet **Consignes** puis **Grille**).
2. Pour chaque ligne, lire la phrase, le comportement attendu, les outils appelés et la réponse ; remplir la colonne jaune
   **VOTRE VERDICT** (`réussi` / `échec`, liste déroulante). La cause et le commentaire sont facultatifs.
3. **Ne pas ouvrir** `cle_verdicts_evaluateur.csv` avant d'avoir fini.
4. Enregistrer, puis dans ce dossier : `python calculer_kappa.py`
5. Reporter dans l'article : accord brut, **kappa** (et son IC 95 %), matrice de confusion, et commenter les désaccords
   (ex. « l'évaluateur est plus sévère que l'humain sur … »).

*Idéal (si possible) : faire annoter la même grille par un 2e membre du binôme sans se concerter, pour un accord inter-annotateurs humain.*

## Fichiers
| Fichier | Rôle |
|---|---|
| `grille_audit_30_tours.xlsx` | grille à remplir |
| `cle_verdicts_evaluateur.csv` | verdicts cachés de l'évaluateur |
| `calculer_kappa.py` | calcule accord, kappa, matrice de confusion, désaccords |
| `construire_grille_audit.py` | régénère la grille (même tirage, graine 42) |
| `resultats_bruts/*.pkl` | résultats détaillés de l'exécution finale (copiés depuis Google Drive) |
