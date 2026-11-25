# SAMS — plateforme pour voir, tester et auditer les agents

## Lancer
- **Double-clic** sur `LANCER_SAMS.bat` (ouvre le navigateur tout seul), ou dans un terminal :
  `& "C:\Users\zineb\AppData\Local\Python\pythoncore-3.14-64\python.exe" serveur.py` puis ouvrir http://localhost:8765
- Laisser la fenêtre « SAMS - serveur » ouverte ; la fermer arrête la plateforme.

## Les 10 pages (barre de gauche)
| Page | À quoi elle sert |
|---|---|
| 🏢 **Bureau en direct** | les agents sont des employés de l'école. « Lancer la journée de test » : ils traitent les 60 scénarios devant vous, Éva (la correctrice) les note, Gaston (la garde) bloque les actions interdites. Clic sur un employé = l'inspecteur montre ce qu'il fait vraiment. En bas : écrire à Clara ou Basile en direct. |
| 📑 **Rapport (figures)** | 12 figures, une par page (16:9), avec titre-conclusion, un graphique, 3 chiffres clés et « À retenir ». Flèches ← → pour naviguer ; « Exporter » enregistre les PNG dans Téléchargements **et** dans `rapport_figures/` du projet |
| 📊 Vue d'ensemble | les chiffres clés et les 3 conclusions |
| 💬 **Atelier** | discuter avec un agent et voir son raisonnement (intention, entités, outils, mémoire) ; simuler une panne d'outil ; relire ce qu'a fait le LLM sur GPU |
| ⚖️ Comparaison | toutes les métriques, par catégorie de piège, robustesse aux reformulations, causes d'échec |
| 🛡️ Sécurité | les 3 documents piégés, les résultats avec / sans défense, test en direct |
| 🔎 Traces | chaque tour étape par étape (demande → outils → réponse → verdict) |
| 🧪 **Labo** | relancer une évaluation complète en direct (TEST, DEV, reformulations) pour vérifier ou améliorer un agent |
| ✅ **Audit humain** | noter les 30 tours à l'aveugle, puis calculer le kappa (les verdicts sont aussi recopiés dans la grille Excel) |
| 🧭 **Parcours 7 étapes** | comprendre le projet en le manipulant (données → outils → scénario → correction → vérification → LLM → résumé) |
| 🔬 Expériences | ablations, DEV → TEST, McNemar, statistiques internes des LLM, courbe d'apprentissage |

## Le bureau 3D
- Les agents sont des figurines 3D (three.js) : grosses têtes, cheveux colorés, mobilier blanc, ombres douces.
- Glisser = tourner la vue, molette = zoomer, bouton « ⟲ Recentrer ». Clic sur un personnage = l'inspecter.
- Pendant le test : ils tapent au clavier, sautent de joie après un succès, secouent la tête après un échec ; leur écran passe au bleu (travail), vert (réussi) ou rouge (échec).
- three.js est chargé depuis internet ; sans connexion, le bureau s'affiche automatiquement en version 2D.

## Ce qui est en direct, ce qui est relu
- **En direct** (vrai code du notebook, sur votre PC) : l'école fictive, les outils, l'évaluateur, la baseline, l'agent classique.
- **Relu** : les agents LLM Qwen ont besoin d'un GPU ; leurs actions viennent de l'exécution finale sur Google Colab (`audit/resultats_bruts/*.pkl`).
- Au démarrage, le serveur rejoue les 60 scénarios et vérifie qu'il retrouve les chiffres du rapport (page Parcours, étape 5).
