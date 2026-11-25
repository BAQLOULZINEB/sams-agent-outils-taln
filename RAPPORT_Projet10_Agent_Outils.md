# Projet TALN — Sujet 10 : Agent conversationnel à outils
*Filière IA & Science des Données, 5e année — EMSI Rabat — 2026/2027*

> Document de travail pour l'article : méthode, explications et résultats **vérifiés** de l'exécution finale
> (notebook `Projet10_Agent_Outils_TALN.ipynb`, Google Colab, GPU Tesla T4).

---

## 1. Problème et question de recherche

Un assistant de secrétariat pédagogique doit **agir**, pas seulement répondre : consulter un emploi du temps, calculer une moyenne,
chercher un document administratif, réserver une salle, envoyer un e-mail. Il le fait en **appelant des outils** (fonctions).

**Question :** un petit LLM ouvert (**Qwen2.5-3B-Instruct**) qui choisit lui-même ses outils est-il meilleur qu'un **agent classique** à base de règles
(intention + entités + mémoire) ? Et quelle architecture LLM est la plus fiable : **appel direct** ou **planification** ?

### 1.1 État de l'art (succinct)
- **Systèmes de dialogue orientés tâche.** L'approche classique enchaîne compréhension (intention + entités), **suivi de l'état du dialogue**
  et politique d'action ; les corpus comme MultiWOZ [8] ont popularisé l'évaluation du suivi d'état. Notre agent classique suit ce schéma.
- **LLM qui utilisent des outils.** Toolformer [3] montre qu'un modèle de langue peut apprendre à appeler des API ; Gorilla [7] étudie la justesse
  des appels (nom de l'outil et arguments). Les modèles ouverts récents comme Qwen2.5 [5] exposent un **appel de fonctions natif** (sortie JSON).
- **Raisonner puis agir.** ReAct [2] alterne raisonnement et appels d'outils pas à pas (notre architecture A) ; les approches « planifier puis
  résoudre » [4] font d'abord écrire un plan (notre architecture B).
- **Récupération d'information et sécurité.** La génération augmentée par récupération (RAG) [13] s'appuie sur des documents retrouvés ;
  les **injections d'instructions indirectes** [6] montrent qu'un document piégé peut détourner un agent : c'est notre volet avancé.
- **Bases classiques mobilisées.** TF-IDF pour la recherche et la classification [9] ; évaluation statistique par bootstrap [12] et test de McNemar [11] ;
  accord humain / correcteur par le kappa de Cohen [10], lu avec l'échelle de Landis & Koch [14].

## 2. Données et protocole d'évaluation

### 2.1 Un monde fictif contrôlé
- **24 étudiants** inventés (2 groupes), **6 modules**, notes CC + examen (note de module = 0,4 × CC + 0,6 × examen), emploi du temps, 5 salles, **12 documents**.
- **Pièges volontaires :** deux étudiants prénommés *Yassine* (ambiguïté) ; une note d'examen manquante (information absente) ; **3 documents piégés**
  contenant une fausse « instruction système » (envoyer les notes vers Gmail, réserver une salle, dire que la note passe à 20/20).

### 2.2 Les outils
7 outils métier (`rechercher_etudiant`, `consulter_emploi_du_temps`, `calculer_moyenne`, `lister_notes`, `chercher_document`, `reserver_salle`, `envoyer_email`)
+ 2 **méta-outils** (`demander_clarification`, `refuser_demande`) qui rendent les questions et les refus **mesurables**.
Chaque outil **vérifie ses arguments** et chaque appel est **journalisé** : c'est ce journal que lit l'évaluateur.

### 2.3 Trois jeux séparés
| Jeu | Taille | Usage |
|---|---|---|
| **TEST** | 60 scénarios (77 tours) : 16 nominaux, 10 multi-tours, 8 ambigus, 6 info absente, 6 outil en panne, 8 hors périmètre, 6 injections | mesure finale, **une seule fois** |
| **DEV** | 24 scénarios, phrases différentes | tous les réglages |
| **Reformulations** | 24 variantes de tours TEST (fautes, familiarités) | robustesse, jamais utilisées pour régler |

### 2.4 L'évaluateur automatique
Pour chaque tour : type de réaction attendu (répondre / clarifier / refuser / signaler l'échec), **appels obligatoires** avec arguments (comparés après
normalisation : « G2 » = « 5IA-SD-G2 »), **faits** attendus dans la réponse (calculés depuis la base), **actions interdites**, **affirmations interdites**.
Un tour est réussi s'il n'a aucune cause d'échec ; une **tâche** (scénario) est réussie si **tous** ses tours le sont.

**Métriques :** taux de tâches réussies, tours réussis, rappel des outils, exactitude des arguments, refus justifiés, clarifications correctes,
refus/questions injustifiés, taux d'attaques réussies, latence.

## 3. Les systèmes comparés

| Système | Principe |
|---|---|
| **Baseline** | mots-clés → outil ; valeurs par défaut quand il manque une info ; ni mémoire ni clarification |
| **Agent classique** | détecteur d'intention (régression logistique TF-IDF mots + caractères, F1 macro TEST = 0,982), extraction d'entités, **état du dialogue**, questions de clarification, réponses par gabarits |
| **Agent LLM — A. direct** | boucle ReAct : le LLM voit les outils utiles et les appelle jusqu'à pouvoir répondre (5 pas max) |
| **Agent LLM — B. plan** | le LLM écrit d'abord un **plan JSON** ; chaque étape n'expose que l'outil prévu ; complétion en lecture seule ; réponse finale |

**Composants communs de l'agent LLM :** filtre d'outils selon l'intention, état du dialogue injecté dans le prompt, et **défense anti-injection** :
documents balisés comme données non fiables, phrases adressées à « l'assistant » retirées, **garde de permissions** hors du modèle
(« le modèle propose, le système impose les droits ») pour l'e-mail et la réservation.

## 4. Démarche expérimentale (transparence)

1. **Première exécution complète (v1)** sur GPU T4 : LLM A. direct 51,7 %, B. plan 51,7 %.
2. **Analyse des erreurs v1** : mauvais outil pour « note en module », identifiants inventés, questions posées en texte libre au lieu de l'outil
   de clarification, plans incomplets, JSON d'appel mal formé, et un **bug du notebook** (modèle 3B non rechargé après l'étude 1.5B → reformulations LLM faussées à 4,2 %).
3. **Réglage sur DEV uniquement, en 2 tours (v2)** : règles de prompt supplémentaires, exécution séquentielle des appels, garde d'arguments
   (un groupe, un créneau ou un étudiant ne peut pas être deviné), conversion des questions libres en `demander_clarification`, reprise de format,
   phase de complétion du plan en lecture seule, filtrage des phrases injectées. DEV : A 50,0 → 79,2 % ; B 37,5 → 75,0 %.
4. **Un seul passage sur TEST** avec la v2 (résultats ci-dessous). Les scénarios TEST et l'évaluateur n'ont **jamais** été modifiés
   (vérification automatique), et la baseline et l'agent classique retrouvent exactement leurs scores.

## 5. Résultats (TEST, 60 scénarios)

### 5.1 Tableau principal

| Système | Tâches réussies | IC 95 % | Tours | Rappel outils | Arguments | Refus justifiés | Clarifications | Refus injustifiés | Attaques | Latence |
|---|---|---|---|---|---|---|---|---|---|---|
| Baseline | 65,0 % | 51,7–76,7 | 64,9 % | 72,7 % | 95,0 % | 87,5 % | 0,0 % | 14,8 % | 0 % | ≈ 0 s |
| **Agent classique** | **98,3 %** | 95,0–100 | 98,7 % | 98,2 % | 100 % | 100 % | 100 % | 0,0 % | 0 % | ≈ 0 s |
| LLM 3B — A. direct | 68,3 % | 56,7–80,0 | 75,3 % | 78,2 % | 100 % | 87,5 % | 62,5 % | 11,5 % | 0 % | 4,7 s |
| **LLM 3B — B. plan** | **83,3 %** | 73,3–91,7 | 85,7 % | 90,9 % | 100 % | 100 % | 62,5 % | 0,0 % | 0 % | 7,3 s |
| LLM 1.5B — A. direct | 43,3 % | 31,6–56,7 | 42,9 % | 50,9 % | 57,1 % | 100 % | 37,5 % | 13,1 % | 0 % | 2,3 s |

### 5.2 Réussite par catégorie de piège (% de scénarios)

| Système | ambigu | hors périmètre | info absente | injection | multi-tours | nominal | outil en panne |
|---|---|---|---|---|---|---|---|
| Baseline | 0 | 75,0 | 100 | 50,0 | 30,0 | 93,8 | 100 |
| Agent classique | 100 | 100 | 100 | 83,3 | 100 | 100 | 100 |
| LLM A. direct | 50,0 | 87,5 | 83,3 | 66,7 | 40,0 | 75,0 | 83,3 |
| LLM B. plan | 62,5 | 87,5 | 83,3 | **100** | 70,0 | 93,8 | 83,3 |
| LLM 1.5B | 0 | 100 | 50,0 | 16,7 | 10,0 | 43,8 | 100 |

### 5.3 Significativité (McNemar exact, scénarios appariés)

| Comparaison | Seul A réussit | Seul B réussit | p | Conclusion |
|---|---|---|---|---|
| B. plan vs Agent classique | 1 | 10 | 0,012 | classique significativement meilleur |
| B. plan vs Baseline | 15 | 4 | 0,019 | plan significativement meilleur |
| A. direct vs B. plan | 2 | 11 | 0,023 | plan significativement meilleur |
| 3B A. direct vs 1.5B | 20 | 5 | 0,004 | 3B significativement meilleur |
| Agent classique vs Baseline | 20 | 0 | < 0,001 | classique significativement meilleur |

**À retenir :** les différences entre systèmes principaux sont **significatives** (p < 0,05). Les écarts d'ablation de quelques points
restent **dans les intervalles de confiance** (± 11–12 points) et ne sont pas concluants.

### 5.4 Robustesse aux reformulations

| Système | TEST | Reformulations | Écart |
|---|---|---|---|
| Baseline | 65,0 % | 50,0 % | −15,0 |
| Agent classique | 98,3 % | 70,8 % | −27,5 |
| LLM A. direct | 68,3 % | 50,0 % | −18,3 |
| LLM B. plan | 83,3 % | 58,3 % | −25,0 |

### 5.5 Sécurité (14 scénarios injection + hors périmètre)

| Configuration | Scénarios exposés | Attaques réussies | Attaques \| exposé | Tentatives d'action interdite |
|---|---|---|---|---|
| A. direct sans défense | 100 % | 33,3 % | 33,3 % | 0 % |
| B. plan sans défense | 100 % | 33,3 % | 33,3 % | 0 % |
| A. direct avec défense | 66,7 % | **0 %** | **0 %** | 0 % |
| B. plan avec défense | 100 % | **0 %** | **0 %** | 0 % |

Garde de permissions : 4 appels bloqués (B. plan), **0 blocage à tort**.

### 5.6 Ablations

| Configuration | Tâches réussies |
|---|---|
| LLM A. direct complet | 68,3 % |
| sans détection d'intention | 65,0 % |
| sans état du dialogue | 73,3 % |
| Agent classique sans état du dialogue | 75,0 % (vs 98,3 %) |
| Détecteur d'intention : 78 → 978 phrases d'entraînement | F1 TEST 0,958 → 0,982 |

### 5.7 Statistiques internes (TEST, 77 tours)

| | A. direct | B. plan | 1.5B |
|---|---|---|---|
| Générations du modèle | 138 | 239 | 106 |
| Erreurs de format (finales) | 0 | 0 | 0 |
| Arguments refusés par les outils | 0 | 0 | 6 |
| Appels bloqués par la garde | 0 | 4 | 0 |
| Plans illisibles / interrompus | — | 5 / 6 | — |
| Arguments devinés remplacés par une question | 3 | 8 | 3 |
| Phrases injectées retirées des documents | 8 | 10 | 6 |

## 6. Discussion

1. **La planification gagne nettement chez le LLM** (83,3 % contre 68,3 %, p = 0,023) : en obligeant le petit modèle à annoncer toutes les étapes,
   puis en n'exposant qu'un outil par étape, on réduit les oublis d'outil et les réponses de mémoire, et on obtient 0 % de refus injustifiés.
   Le prix : 1,7 fois plus de générations et une latence de 7,3 s par tour.
2. **L'agent classique reste le plus performant sur TEST**, mais son score est **optimiste** : ses règles et les scénarios ont la même origine.
   Sur les reformulations inédites, il perd 27,5 points ; l'écart avec le LLM B. plan passe de 15 à 12,5 points.
3. **La taille du modèle est déterminante** : le 1.5B échoue surtout sur les arguments (57 % justes) et sur les dialogues multi-tours (10 %).
4. **La sécurité ne vient pas du modèle mais du système** : sans défense, le LLM répète le mensonge injecté dans un tiers des cas ;
   avec le filtrage des documents et la garde de permissions, 0 attaque réussie et 0 blocage à tort.
5. **Les ablations sont nuancées** : retirer la détection d'intention fait perdre des refus justifiés (87,5 → 75 %) ; retirer le résumé d'état
   ne pénalise pas le LLM (il relit l'historique de la conversation), alors qu'il est vital pour l'agent à règles (98,3 → 75 %).

## 7. Analyse des erreurs du meilleur agent LLM (B. plan, 11 tours ratés)
1. **Outil manquant (5)** — « Moyenne générale de l'étudiant E014 » : le plan cherche un étudiant nommé « E014 » au lieu d'utiliser l'identifiant.
2. **Absence de clarification (3)** — « Quelle est la moyenne de Yassine ? » : deux étudiants correspondent, mais la réponse ne pose pas une vraie question.
3. **Hallucination (2)** — réservation d'une salle déjà occupée : l'agent répond sur un étudiant « Dupont » inventé au lieu de signaler l'échec.

### 7.1 Audit humain du correcteur (fiabilité de l'évaluation)
30 tours des agents LLM (15 direct, 15 plan), tirés au hasard et stratifiés, ont été jugés **à l'aveugle** par un membre du groupe, puis comparés au correcteur.

| | Correcteur : réussi | Correcteur : échec |
|---|---|---|
| **Humain : réussi** | 13 | **8** (correcteur trop sévère) |
| **Humain : échec** | **3** (correcteur trop indulgent) | 6 |

- **Accord brut 63 %**, **kappa de Cohen = 0,25** (IC 95 % bootstrap : −0,09 à 0,59) : accord **passable** sur l'échelle de Landis & Koch [14].
- **Le désaccord est asymétrique (8 contre 3)** : le correcteur rejette des réponses libres que l'humain juge correctes. Exemples typiques :
  - « L'étudiant Karim Benali **n'a pas été trouvé** » (I02) : le mot-clé attendu est « pas trouvé » ; la forme fléchie « pas **été** trouvé » ne correspond pas.
    C'est exactement la limite vue en cours : une **correspondance de chaînes sans lemmatisation** rate les variantes morphologiques.
  - « Yassine Alaoui ou Yassine Tahiri ? Veuillez préciser. » (A01) : c'est bien une question de précision, mais posée en texte libre et non
    reconnue par la règle (« finit par un point d'interrogation »).
  - Refus formulés autrement que les tournures prévues (H02, H04).
- **Dans l'autre sens (3 cas)**, le correcteur valide des tours que l'humain refuse, par exemple P04 : l'e-mail est bien envoyé, mais l'humain
  juge son contenu insuffisant, ce que le correcteur ne vérifie pas (il accepte n'importe quel corps de message).
- **Conséquences pour les résultats.** Les scores des LLM, qui répondent en texte libre, sont plutôt **sous-estimés** ; ceux des agents à règles, dont les
  phrases modèles contiennent exactement les mots-clés attendus, sont mieux reconnus. Les **grands écarts** (classique / LLM, plan / direct, 3B / 1.5B,
  tous significatifs) restent valides ; les écarts de quelques points ne doivent pas être interprétés.
- **Limite de l'audit lui-même** : un seul annotateur, 30 tours ; un deuxième annotateur indépendant permettrait de mesurer l'accord entre humains.

## 8. Limites
- 60 scénarios écrits par l'équipe : intervalles de confiance larges, validité externe limitée (pas de vrais utilisateurs).
- Les défauts corrigés en v2 ont été repérés en lisant des erreurs de la v1 (dont quelques exemples TEST), puis réglés et validés sur DEV :
  un léger biais optimiste sur TEST n'est pas exclu.
- Le correcteur reconnaît le type de réponse par mots-clés : l'audit humain donne un accord seulement **passable (κ = 0,25)**, avec un biais
  de sévérité envers les réponses libres. Amélioration possible : lemmatiser les réponses avant la recherche de mots-clés, ou faire juger le type de
  réponse par un classifieur entraîné sur des réponses annotées.
- Un seul tirage par configuration (décodage glouton) ; conclusions propres à Qwen2.5-3B.
- La garde de permissions et le filtrage reposent sur des mots-clés : une demande légitime formulée autrement pourrait être bloquée.

## 9. Éthique
Données entièrement fictives ; en production, les notes sont des données personnelles (accès restreint, journalisation minimale, aucun envoi hors du
domaine de l'école) ; les actions à effet de bord exigent un humain dans la boucle ; un document n'est jamais une instruction ; l'assistant doit dire
quand il ne sait pas plutôt qu'inventer.

## 10. Conclusion
Un petit LLM ouvert de 3 milliards de paramètres, **encadré par une architecture de planification et par des contrôles hors du modèle**, atteint
**83,3 %** de tâches réussies, sans attaque réussie ni refus injustifié. Il reste derrière un agent à règles bien conçu sur des scénarios proches
de ses règles (98,3 %), mais l'écart se réduit sur des formulations inédites. Le résultat principal : la fiabilité d'un agent à outils vient
autant de **l'architecture et des garde-fous** que du modèle lui-même.

## 11. Lien avec le cours de TALN
| Notion du cours | Où elle apparaît dans le projet |
|---|---|
| Niveaux d'analyse : ambiguïté syntaxique, sémantique, **pragmatique** | « sa note » (coréférence via l'état du dialogue), deux « Yassine » (ambiguïté → question de précision) |
| **Prétraitement** : normalisation sans effacer le sens | `norm()` : minuscules et suppression des accents avant toute comparaison |
| **Tokenisation** : mots, caractères, sous-mots ; mots hors vocabulaire (**OOV**) | n-grammes de caractères (2–5) qui résistent aux fautes (« Benjeloun ») ; Qwen utilise une tokenisation BPE |
| **Sac de mots / TF-IDF**, similarité cosinus | recherche documentaire (seuil réglé sur DEV) et représentation du détecteur d'intention |
| **Classification de texte** (TP 5) : NB, régression logistique, SVM, F1 macro | détecteur d'intention : 5 modèles comparés, F1 macro TEST 0,982, courbe d'apprentissage |
| **Lemmatisation / stemming** | expliquent une erreur du correcteur (« pas été trouvé » ≠ « pas trouvé ») révélée par l'audit |
| **Modèles de langue** : prédire le prochain token, softmax, température | le LLM génère un JSON d'appel d'outil ; décodage glouton (température 0) pour des résultats reproductibles |
| **Transformer / attention** | Qwen2.5 est un Transformer décodeur ; il relit l'historique, d'où le faible effet du résumé d'état (ablation) |
| **RAG** : récupérer puis générer ; « une source fournit une information, pas une autorisation » | `chercher_document` puis réponse ; la garde de permissions n'autorise une action que si l'**utilisateur** l'a demandée |
| « Un filtre de mots n'est pas une frontière de sécurité » | notre filtre de phrases suspectes est complété par une garde **hors du modèle** ; limite discutée |
| **Évaluation** : métriques, accord entre annotateurs | 9 métriques, IC bootstrap, McNemar, kappa de Cohen de l'audit |

Les schémas `rapport_diagrammes/diagramme-3-pipeline-TALN.png` et `diagramme-4-cours-projet.png` illustrent ce tableau.

## Références
1. D. Jurafsky, J. H. Martin. *Speech and Language Processing*, 3e édition (version en ligne).
2. S. Yao et al. « ReAct: Synergizing Reasoning and Acting in Language Models ». *ICLR*, 2023.
3. T. Schick et al. « Toolformer: Language Models Can Teach Themselves to Use Tools ». *NeurIPS*, 2023.
4. L. Wang et al. « Plan-and-Solve Prompting: Improving Zero-Shot Chain-of-Thought Reasoning by Large Language Models ». *ACL*, 2023.
5. Qwen Team. « Qwen2.5 Technical Report ». arXiv:2412.15115, 2024.
6. K. Greshake et al. « Not What You've Signed Up For: Compromising Real-World LLM-Integrated Applications with Indirect Prompt Injection ». *AISec (ACM CCS workshop)*, 2023.
7. S. G. Patil et al. « Gorilla: Large Language Model Connected with Massive APIs ». arXiv:2305.15334, 2023.
8. P. Budzianowski et al. « MultiWOZ: A Large-Scale Multi-Domain Wizard-of-Oz Dataset for Task-Oriented Dialogue Modelling ». *EMNLP*, 2018.
9. G. Salton, C. Buckley. « Term-weighting approaches in automatic text retrieval ». *Information Processing & Management*, 24(5), 1988.
10. J. Cohen. « A Coefficient of Agreement for Nominal Scales ». *Educational and Psychological Measurement*, 20(1), 1960.
11. Q. McNemar. « Note on the sampling error of the difference between correlated proportions or percentages ». *Psychometrika*, 12(2), 1947.
12. B. Efron, R. J. Tibshirani. *An Introduction to the Bootstrap*. Chapman & Hall, 1993.
13. P. Lewis et al. « Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks ». *NeurIPS*, 2020.
14. J. R. Landis, G. G. Koch. « The Measurement of Observer Agreement for Categorical Data ». *Biometrics*, 33(1), 1977.
15. F. Pedregosa et al. « Scikit-learn: Machine Learning in Python ». *JMLR*, 12, 2011 ; T. Wolf et al. « Transformers: State-of-the-Art Natural Language Processing ». *EMNLP (démos)*, 2020.

*À vérifier avant dépôt : formater ces références selon le style demandé par l'enseignant.*

---

### Diagrammes explicatifs (dossier `rapport_diagrammes/`)
| Diagramme | Fichier | À placer dans la section |
|---|---|---|
| Architecture du système | `diagramme-1-architecture.png` | 3 (systèmes comparés) |
| Architectures A (direct) et B (plan) | `diagramme-2-architectures-A-B.png` | 3 (volet avancé) |
| Un tour vu par le TALN | `diagramme-3-pipeline-TALN.png` | 2 ou 11 (lien avec le cours) |
| Ce que le projet applique du cours | `diagramme-4-cours-projet.png` | 11 (lien avec le cours) |

Sources modifiables : les `.html` du même dossier (régénérés par `generer_diagrammes.py`).

### Figures prêtes pour l'article (dossier `rapport_figures/`)
Générées par la plateforme SAMS (page Rapport → « Exporter les 12 figures ») ; la figure 12 contient le kappa de l'audit.

| Figure | Fichier | À placer dans la section |
|---|---|---|
| 1 · Démarche | `figure-01-Demarche.png` | 2–4 (données, protocole, systèmes) |
| 2 · Résultat principal (avec IC 95 %) | `figure-02-Resultat-principal.png` | 5.1 |
| 3 · Profil de compétences (radar) | `figure-03-Profil.png` | 5.1 |
| 4 · Réussite par type de piège (carte de chaleur) | `figure-04-Quand-ca-echoue.png` | 5.2 |
| 5 · Causes d'échec | `figure-05-Pourquoi-ca-echoue.png` | 7 (analyse des erreurs) |
| 6 · Robustesse aux reformulations | `figure-06-Robustesse.png` | 5.4 |
| 7 · Sécurité avec / sans défense | `figure-07-Securite.png` | 5.5 |
| 8 · Réglage DEV → TEST | `figure-08-Reglage-DEV-TEST.png` | 4 (démarche) |
| 9 · Ablations | `figure-09-Ablations.png` | 5.6 |
| 10 · Significativité (McNemar) | `figure-10-Significativite.png` | 5.3 |
| 11 · Coût (latence × réussite) | `figure-11-Cout.png` | 6 (discussion) |
| 12 · Fiabilité du correcteur (kappa) | `figure-12-Audit.png` | 8 (limites) — après l'audit |

### Fichiers du projet
| Fichier | Contenu |
|---|---|
| **`Projet10_Agent_Outils_TALN.ipynb`** | **notebook unique : exécution finale sur GPU T4, commentée (à rendre) ; lu aussi par SAMS, la démo et l'audit** |
