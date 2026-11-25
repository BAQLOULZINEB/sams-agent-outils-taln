# -*- coding: utf-8 -*-
"""Génère les 4 diagrammes du rapport (design system « architecture-diagram » : fond slate-950, JetBrains Mono, SVG inline).
Usage : python generer_diagrammes.py   -> écrit les .html ici et une copie dans ../dashboard/static/diagrammes/ (pour l'export PNG)."""
import os, re, shutil

ICI = os.path.dirname(os.path.abspath(__file__))
COPIE = os.path.join(ICI, "..", "dashboard", "static", "diagrammes")
TEMPLATE = open(os.path.join(os.path.expanduser("~"), ".claude", "skills", "diagram-design", "resources", "template.html"), encoding="utf-8").read()
TETE = TEMPLATE.split("<body>")[0]
SCRIPTS = TEMPLATE[TEMPLATE.index("  <script>\n    async function copyAsImage"):]

# ---------- primitives SVG (palette du skill) ----------
C = {"front": ("rgba(8, 51, 68, 0.4)", "#22d3ee"), "back": ("rgba(6, 78, 59, 0.4)", "#34d399"), "db": ("rgba(76, 29, 149, 0.4)", "#a78bfa"),
     "cloud": ("rgba(120, 53, 15, 0.3)", "#fbbf24"), "secu": ("rgba(136, 19, 55, 0.4)", "#fb7185"), "bus": ("rgba(251, 146, 60, 0.3)", "#fb923c"),
     "ext": ("rgba(30, 41, 59, 0.5)", "#94a3b8")}
def boite(x, y, w, h, typ, titre, lignes=(), note=None, taille=11):
    f, s = C[typ]; cx = x + w / 2
    out = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="#0f172a"/>',
           f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="{f}" stroke="{s}" stroke-width="1.5"/>',
           f'<text x="{cx}" y="{y + 20}" fill="white" font-size="{taille}" font-weight="600" text-anchor="middle">{titre}</text>']
    for i, l in enumerate(lignes):
        out.append(f'<text x="{cx}" y="{y + 36 + i * 13}" fill="#94a3b8" font-size="9" text-anchor="middle">{l}</text>')
    if note: out.append(f'<text x="{cx}" y="{y + h - 9}" fill="{s}" font-size="8" text-anchor="middle">{note}</text>')
    return "\n".join(out)
def zone(x, y, w, h, titre, coul="#fbbf24", tiret="8,4"):
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="{coul}0d" stroke="{coul}" stroke-width="1" stroke-dasharray="{tiret}"/>'
            f'<text x="{x + 12}" y="{y + 18}" fill="{coul}" font-size="10" font-weight="600">{titre}</text>')
def fleche(pts, coul="#64748b", tiret=None, etiq=None, ex=0, ey=-6):
    d = "M " + " L ".join(f"{a} {b}" for a, b in pts)
    t = f' stroke-dasharray="{tiret}"' if tiret else ""
    s = f'<path d="{d}" fill="none" stroke="{coul}" stroke-width="1.5"{t} marker-end="url(#arrowhead)"/>'
    if etiq:
        (x1, y1), (x2, y2) = pts[len(pts) // 2 - 1], pts[len(pts) // 2]
        s += f'<text x="{(x1 + x2) / 2 + ex}" y="{(y1 + y2) / 2 + ey}" fill="#94a3b8" font-size="8" text-anchor="middle">{etiq}</text>'
    return s
def legende(x, y, items):
    out = [f'<text x="{x}" y="{y}" fill="white" font-size="10" font-weight="600">Légende</text>']
    for i, (typ, lib) in enumerate(items):
        xx = x + 80 + i * 150
        if typ in C:
            f, s = C[typ]; out.append(f'<rect x="{xx}" y="{y - 9}" width="16" height="10" rx="2" fill="{f}" stroke="{s}" stroke-width="1"/>')
        else:
            out.append(f'<line x1="{xx}" y1="{y - 4}" x2="{xx + 16}" y2="{y - 4}" stroke="{typ}" stroke-width="1.5" stroke-dasharray="3,3"/>')
        out.append(f'<text x="{xx + 22}" y="{y}" fill="#94a3b8" font-size="8">{lib}</text>')
    return "\n".join(out)
def carte(coul, titre, items):
    li = "\n".join(f"          <li>• {i}</li>" for i in items)
    return f'''      <div class="card">
        <div class="card-header"><div class="card-dot {coul}"></div><h3>{titre}</h3></div>
        <ul>
{li}
        </ul>
      </div>'''

def page(fichier, titre, sous, vb, svg, cartes, pied):
    tete = re.sub(r"<title>.*?</title>", f"<title>{titre}</title>", TETE).replace('<html lang="en">', '<html lang="fr">')
    corps = f'''<body>
  <div class="container" id="report-container">
    <div class="header">
      <div class="header-row">
        <div class="pulse-dot"></div>
        <h1>{titre}</h1>
        <div class="toolbar">
          <div class="toolbar-actions">
            <button onclick="copyAsImage(this)">Copier</button>
            <button onclick="downloadPNG(this)">PNG</button>
            <button onclick="downloadPDF(this)">PDF</button>
          </div>
          <button class="toolbar-toggle" onclick="this.parentElement.classList.toggle('expanded')" title="Exporter" aria-label="Exporter">⋯</button>
        </div>
      </div>
      <p class="subtitle">{sous}</p>
    </div>
    <div class="diagram-container">
      <svg viewBox="0 0 {vb[0]} {vb[1]}" font-family="JetBrains Mono, monospace">
        <defs>
          <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto"><polygon points="0 0, 10 3.5, 0 7" fill="#64748b" /></marker>
          <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse"><path d="M 40 0 L 0 0 0 40" fill="none" stroke="#1e293b" stroke-width="0.5"/></pattern>
        </defs>
        <rect width="100%" height="100%" fill="url(#grid)" />
{svg}
      </svg>
    </div>
    <div class="cards">
{chr(10).join(cartes)}
    </div>
    <p class="footer">{pied}</p>
  </div>

'''
    html = tete + corps + SCRIPTS.replace("link.download = 'diagram.png'", f"link.download = '{fichier[:-5]}.png'").replace("pdf.save('diagram.pdf')", f"pdf.save('{fichier[:-5]}.pdf')")
    for d in (ICI, COPIE):
        os.makedirs(d, exist_ok=True); open(os.path.join(d, fichier), "w", encoding="utf-8").write(html)
    print("écrit", fichier)

PIED = "Projet TALN n°10 · Agent conversationnel à outils · EMSI Rabat · 5IA-SD · 2026/2027"

# =============================================================== 1. ARCHITECTURE DU SYSTÈME
s = []
s.append(zone(185, 40, 515, 470, "AGENT CONVERSATIONNEL · un tour de dialogue"))
# flèches d'abord (derrière les boîtes)
s.append(fleche([(150, 108), (208, 108)], "#22d3ee", etiq="phrase", ey=-8))
s.append(fleche([(345, 108), (373, 108)], "#34d399"))
s.append(fleche([(508, 108), (536, 108)], "#34d399"))
s.append(fleche([(604, 136), (604, 160), (560, 160), (560, 183)], "#34d399", etiq="intention + entités", ex=-30, ey=-5))
s.append(fleche([(345, 226), (373, 226)], "#a78bfa", tiret="4,4"))
s.append(fleche([(520, 300), (520, 318)], "#fb923c"))
s.append(fleche([(597, 340), (597, 403)], "#fb923c", etiq="appel proposé", ex=40, ey=-2))
s.append(fleche([(668, 430), (728, 430), (728, 290), (756, 290)], "#fb7185", etiq="si autorisé", ex=0, ey=-4))
s.append(fleche([(860, 340), (860, 398)], "#a78bfa", etiq="lit / écrit", ex=34, ey=4))
s.append(fleche([(758, 470), (742, 470), (742, 496), (442, 496), (442, 480)], "#fbbf24", tiret="5,5"))
s.append('<text x="600" y="508" fill="#fbbf24" font-size="8" text-anchor="middle">documents retrouvés (non fiables)</text>')
s.append(fleche([(373, 290), (268, 290), (268, 535), (90, 535), (90, 362)], "#22d3ee", etiq="réponse", ex=-24, ey=0))
s.append(fleche([(560, 510), (560, 560), (330, 560), (330, 581)], "#64748b", tiret="3,3", etiq="journal de chaque appel", ex=0, ey=-6))
s.append(fleche([(480, 612), (533, 612)], "#34d399"))
s.append(fleche([(640, 644), (640, 670), (330, 670), (330, 642)], "#fb7185", tiret="4,4", etiq="kappa = 0,25", ex=0, ey=-6))
# boîtes
s.append(boite(30, 80, 120, 280, "ext", "Utilisateur", ["secrétariat", "pédagogique", "", "« Et sa note", "en TALN ? »"], note="multi-tours"))
s.append(boite(208, 80, 137, 56, "back", "Prétraitement", ["minuscules, accents"]))
s.append(boite(373, 80, 135, 56, "back", "Intention", ["TF-IDF + RegLog"]))
s.append(boite(536, 80, 137, 56, "back", "Entités", ["regex + difflib"]))
s.append(boite(208, 190, 137, 72, "db", "État du dialogue", ["étudiant, groupe,", "jour, demande", "en attente"]))
s.append(boite(373, 183, 300, 117, "front", "Décideur (3 variantes comparées)", ["1. Baseline : règles par mots-clés", "2. Classique : intention + entités + état", "3. LLM Qwen2.5-3B (appel de fonctions)", "   A. appel direct  ·  B. plan puis exécution"], taille=11))
s.append('<rect x="373" y="318" width="300" height="22" rx="4" fill="rgba(251, 146, 60, 0.3)" stroke="#fb923c" stroke-width="1"/>'
         '<text x="523" y="333" fill="#fb923c" font-size="8.5" text-anchor="middle">appel de fonction JSON {name, arguments}</text>')
s.append(zone(358, 372, 325, 116, "DÉFENSE (hors du modèle)", "#fb7185", "4,4"))
s.append(boite(372, 404, 140, 70, "secu", "Filtre documents", ["retire les phrases", "« à l'assistant »"]))
s.append(boite(526, 404, 142, 70, "secu", "Garde", ["e-mail / réservation", "seulement si demandé"]))
s.append(boite(758, 160, 205, 180, "cloud", "9 outils", ["rechercher_etudiant", "consulter_emploi_du_temps", "calculer_moyenne", "lister_notes", "chercher_document (TF-IDF)", "reserver_salle  ·  envoyer_email", "demander_clarification", "refuser_demande"], note="schémas JSON"))
s.append(boite(758, 398, 205, 104, "db", "Base fictive de l'école", ["24 étudiants · 6 modules", "emplois du temps · 5 salles", "12 documents (3 piégés)"], note="graine fixe = reproductible"))
s.append(boite(180, 583, 300, 59, "back", "Correcteur automatique", ["type de réaction · outils · arguments", "faits · actions interdites · cause"]))
s.append(boite(533, 583, 215, 59, "secu", "Audit humain", ["30 tours jugés à l'aveugle", "accord brut 63 %"]))
s.append(boite(775, 583, 188, 59, "front", "9 métriques", ["tâches réussies, refus", "justifiés, attaques…"]))
s.append(fleche([(748, 612), (773, 612)], "#22d3ee"))
s.append(legende(30, 712, [("back", "Traitement TALN"), ("db", "Données / mémoire"), ("front", "Décision / sortie"), ("cloud", "Outils"), ("secu", "Sécurité / contrôle")]))
page("diagramme-1-architecture.html", "Architecture du système : de la phrase à l'action contrôlée",
     "Chaque tour : le texte est analysé (TALN), un décideur choisit un outil, la défense filtre, le correcteur note tout depuis le journal.",
     (1000, 730), "\n".join(s),
     [carte("emerald", "Briques TALN (cours ch. 1–2)", ["Normalisation : minuscules, suppression des accents", "TF-IDF mots + n-grammes de caractères (fautes, OOV)", "Classification d'intention : F1 macro TEST = 0,982", "Entités par expressions régulières + distance d'édition"]),
      carte("cyan", "Décideur : ce qu'on compare", ["Baseline règles : 65,0 % des tâches", "Agent classique : 98,3 %", "Qwen2.5-3B direct : 68,3 % · plan : 83,3 %", "Même correcteur, mêmes 60 scénarios TEST"]),
      carte("rose", "Contrôle et confiance", ["Garde : « le modèle propose, le système impose »", "Attaques réussies : 33 % sans défense → 0 % avec", "Audit humain : kappa 0,25 (accord passable)", "Le correcteur est plus sévère que l'humain"])], PIED)

# =============================================================== 2. ARCHITECTURES A vs B
s = []
s.append(zone(25, 40, 455, 560, "A · APPEL DIRECT (boucle ReAct)", "#a78bfa"))
s.append(zone(520, 40, 455, 560, "B · PLANIFIER PUIS EXÉCUTER", "#22d3ee"))
# A
s.append(fleche([(252, 126), (252, 158)], "#a78bfa"))
s.append(fleche([(252, 238), (252, 270)], "#a78bfa", etiq="appel d'outil", ex=46, ey=4))
s.append(fleche([(252, 330), (252, 362)], "#a78bfa", etiq="résultat", ex=36, ey=4))
s.append(fleche([(110, 392), (70, 392), (70, 198), (98, 198)], "#a78bfa", tiret="5,5"))
s.append('<text x="78" y="300" fill="#a78bfa" font-size="9" text-anchor="start">boucle</text><text x="78" y="312" fill="#a78bfa" font-size="9" text-anchor="start">≤ 5</text>')
s.append(fleche([(252, 422), (252, 462)], "#a78bfa", etiq="plus d'appel", ex=44, ey=4))
s.append(boite(110, 70, 285, 56, "ext", "Message de l'utilisateur", ["+ historique + état du dialogue"]))
s.append(boite(100, 158, 305, 80, "front", "Le LLM voit TOUS les outils utiles", ["et choisit librement à chaque pas", "(filtrés par l'intention détectée)"]))
s.append(boite(110, 270, 285, 60, "cloud", "Exécution de l'outil", ["passe par la garde de permissions"]))
s.append(boite(110, 362, 285, 60, "db", "Résultat renvoyé au LLM", ["un document lu peut l'influencer"]))
s.append(boite(110, 462, 285, 56, "back", "Réponse finale", ["texte en français"]))
s.append('<text x="252" y="560" fill="#a78bfa" font-size="12" font-weight="700" text-anchor="middle">68,3 % des tâches · 4,7 s / tour</text>')
s.append('<text x="252" y="578" fill="#94a3b8" font-size="9" text-anchor="middle">138 appels au modèle · 11,5 % de questions inutiles</text>')
# B
s.append(fleche([(747, 126), (747, 150)], "#22d3ee"))
s.append(fleche([(747, 210), (747, 238)], "#22d3ee", etiq="plan JSON", ex=38, ey=4))
s.append(fleche([(605, 288), (565, 288), (565, 250), (603, 250)], "#22d3ee", tiret="5,5"))
s.append('<text x="560" y="236" fill="#22d3ee" font-size="8.5" text-anchor="start">étape suivante</text>')
s.append(fleche([(747, 298), (747, 360)], "#22d3ee", etiq="toutes les étapes faites", ex=70, ey=4))
s.append(fleche([(747, 420), (747, 462)], "#22d3ee"))
s.append(boite(605, 70, 285, 56, "ext", "Message de l'utilisateur", ["+ historique + état du dialogue"]))
s.append(boite(605, 150, 285, 60, "front", "1. Le LLM écrit un PLAN", ['{"etapes": [rechercher, calculer]}']))
s.append(boite(605, 238, 285, 60, "cloud", "2. Étape k : UN seul outil exposé", ["celui prévu par le plan"]))
s.append(boite(605, 360, 285, 60, "secu", "3. Complétion en lecture seule", ["jamais d'e-mail ni de réservation", "non prévus par le plan"]))
s.append(boite(605, 462, 285, 56, "back", "4. Réponse finale", ["texte en français"]))
s.append('<text x="747" y="560" fill="#22d3ee" font-size="12" font-weight="700" text-anchor="middle">83,3 % des tâches · 7,3 s / tour</text>')
s.append('<text x="747" y="578" fill="#94a3b8" font-size="9" text-anchor="middle">239 appels au modèle · 0 % de questions inutiles</text>')
s.append('<text x="500" y="628" fill="white" font-size="11" font-weight="600" text-anchor="middle">Même modèle (Qwen2.5-3B), mêmes 60 scénarios : B &gt; A de 15 points · McNemar p = 0,023</text>')
s.append(legende(25, 662, [("front", "Décision du LLM"), ("cloud", "Outil"), ("secu", "Garde-fou"), ("back", "Sortie"), ("#94a3b8", "Boucle")]))
page("diagramme-2-architectures-A-B.html", "Deux architectures pour le même LLM",
     "Volet avancé du sujet : appel direct des outils contre planification en étapes.",
     (1000, 680), "\n".join(s),
     [carte("violet", "A · Appel direct", ["Souple : choisit l'outil au fil de l'eau", "Moins d'appels au modèle, plus rapide", "Défaut : questions inutiles (7 tours ratés)", "Un document lu peut orienter la suite"]),
      carte("cyan", "B · Plan puis exécution", ["Oblige à prévoir toutes les étapes", "Un outil par étape : moins de confusion", "Défaut : mauvais outil si le plan est faux", "Sécurité : rien d'imprévu après lecture"]),
      carte("amber", "Lien avec le cours", ["Modèle de langue : prédit le prochain token", "Le JSON du plan est un texte généré", "Décodage glouton (τ = 0) : reproductible", "Contrainte de sortie = contrôle de la génération"])], PIED)

# =============================================================== 3. PIPELINE TALN D'UN TOUR
s = []
etapes = [("ext", "1. Texte brut", ["« et sa note", "en TALN ? »"], "Niveaux d'analyse"),
          ("back", "2. Normalisation", ["minuscules", "sans accents"], "Prétraitement"),
          ("back", "3. Vectorisation", ["TF-IDF mots (1–2)", "+ car. (2–5)"], "BoW / TF-IDF / OOV"),
          ("back", "4. Intention", ["RegLog : moyenne", "F1 macro 0,982"], "Classification (TP 5)"),
          ("db", "5. Entités + état", ["module = TALN", "« sa » = Kenza"], "Ambiguïté, pragmatique"),
          ("front", "6. LLM (Transformer)", ["génère l'appel :", "calculer_moyenne"], "Modèle de langue"),
          ("cloud", "7. Outil + réponse", ["moyenne TALN = 12,0", "réponse en français"], "RAG : récupérer, générer")]
pos = [(40, 110), (290, 110), (540, 110), (790, 110), (790, 340), (540, 340), (290, 340)]
for k in range(len(pos) - 1):
    (x1, y1), (x2, y2) = pos[k], pos[k + 1]
    if y1 == y2 and x2 > x1: s.append(fleche([(x1 + 170, y1 + 40), (x2 - 2, y2 + 40)], "#34d399"))
    elif y1 == y2: s.append(fleche([(x1 - 2, y1 + 40), (x2 + 170, y2 + 40)], "#22d3ee"))
    else: s.append(fleche([(x1 + 85, y1 + 112), (x2 + 85, y2 - 2)], "#a78bfa"))
s.append(fleche([(288, 380), (250, 380), (250, 425), (125, 425), (125, 450)], "#fbbf24", tiret="5,5"))
for (typ, t, l, concept), (x, y) in zip(etapes, pos):
    s.append(boite(x, y, 170, 80, typ, t, l))
    s.append(f'<rect x="{x}" y="{y + 88}" width="170" height="22" rx="11" fill="rgba(251, 191, 36, 0.12)" stroke="#fbbf24" stroke-width="1"/>'
             f'<text x="{x + 85}" y="{y + 103}" fill="#fbbf24" font-size="8.5" text-anchor="middle">cours : {concept}</text>')
s.append(boite(40, 452, 170, 70, "back", "8. Correcteur", ["note le tour", "réussi / échec + cause"]))
s.append('<text x="500" y="60" fill="white" font-size="11" font-weight="600" text-anchor="middle">Un tour de dialogue = une chaîne de traitements TALN qui se termine par une ACTION</text>')
s.append(legende(40, 580, [("ext", "Entrée"), ("back", "Analyse classique"), ("db", "Mémoire"), ("front", "Génération (LLM)"), ("cloud", "Action")]))
page("diagramme-3-pipeline-TALN.html", "Du texte à l'action : un tour vu par le TALN",
     "Chaque étape du projet correspond à une notion étudiée dans le cours (étiquettes jaunes).",
     (1000, 610), "\n".join(s),
     [carte("emerald", "Pourquoi des n-grammes de caractères", ["Robustes aux fautes : « Benjeloun » ≈ « Benjelloun »", "Gèrent les mots hors vocabulaire (OOV)", "« réclamer » partage « recla » avec « réclamation »", "Même idée que les sous-mots BPE / FastText"]),
      carte("violet", "Ambiguïté et pragmatique", ["« sa note » : il faut l'état du dialogue", "« Yassine » : deux étudiants → poser une question", "« Mets 18 à Rim » : intention interdite → refuser", "Le sens dépend du contexte, pas des seuls mots"]),
      carte("cyan", "Le LLM dans la chaîne", ["Transformer décodeur, tokenisation BPE", "Génère un JSON au lieu d'un texte libre", "Décodage glouton : toujours le token le plus probable", "Ne remplace pas les contrôles hors du modèle"])], PIED)

# =============================================================== 4. CARTE COURS ↔ PROJET
s = []
cours = [("Fondations & règles", "niveaux linguistiques, ambiguïté"), ("Unités & représentations", "tokenisation, nettoyage, BoW, TF-IDF"),
         ("Contexte & probabilités", "modèles de langue, softmax, attention"), ("Tâches & adaptation", "classification, RAG, adaptation"),
         ("Tester & raisonner", "évaluation, sécurité, accord")]
projet = [("Scénarios piégés", "ambigu, multi-tours, hors périmètre"), ("Recherche documentaire", "TF-IDF + seuil réglé sur DEV"),
          ("Détecteur d'intention", "TF-IDF + RegLog, courbe d'apprentissage"), ("Agent LLM Qwen2.5", "appel de fonctions, direct / plan"),
          ("Défense anti-injection", "filtre + garde de permissions"), ("Évaluation", "métriques, IC, McNemar, kappa")]
liens = [(0, 0, "ambiguïté → clarification"), (1, 1, "TF-IDF, n-grammes"), (1, 2, "vectorisation"), (3, 2, "classification"),
         (2, 3, "génération de tokens"), (3, 3, "RAG : récupérer + générer"), (4, 4, "« source ≠ autorisation »"), (4, 5, "macro-F1, accord")]
yc = [90 + i * 105 for i in range(5)]; yp = [70 + i * 92 for i in range(6)]
ordre = {}
for i, j, lib in liens:
    y1, y2 = yc[i] + 30, yp[j] + 30
    k = ordre.get(i, 0); ordre[i] = k + 1
    s.append(f'<path d="M 330 {y1} C 470 {y1}, 530 {y2}, 668 {y2}" fill="none" stroke="#fbbf24" stroke-width="1.3" stroke-opacity="0.75" marker-end="url(#arrowhead)"/>')
    s.append(f'<text x="338" y="{y1 - 6 if k == 0 else y1 + 14}" fill="#fbbf24" font-size="8.5" text-anchor="start">{lib}</text>')
s.append('<text x="190" y="48" fill="#a78bfa" font-size="10" font-weight="600" text-anchor="middle">CE QU\'ON A ÉTUDIÉ (cours TALN)</text>')
s.append('<text x="820" y="48" fill="#34d399" font-size="10" font-weight="600" text-anchor="middle">CE QU\'ON A CONSTRUIT (projet 10)</text>')
for (t, d), y in zip(cours, yc): s.append(boite(50, y, 280, 60, "db", t, [d]))
for (t, d), y in zip(projet, yp): s.append(boite(670, y, 300, 60, "back", t, [d]))
s.append(legende(50, 640, [("db", "Thème du cours"), ("back", "Composant du projet"), ("#fbbf24", "Notion appliquée")]))
page("diagramme-4-cours-projet.html", "Ce que le projet applique du cours TALN",
     "Chaque composant du projet met en œuvre une notion du cours ; le volet avancé va vers les agents et la sécurité des LLM.",
     (1000, 665), "\n".join(s),
     [carte("violet", "Chapitre 1 : prétraitement", ["Normalisation sans effacer le sens", "Tokenisation : mots, caractères, sous-mots", "Mots hors vocabulaire : n-grammes de caractères", "Ambiguïté syntaxique, sémantique, pragmatique"]),
      carte("emerald", "Chapitre 2 : représentations", ["BoW puis TF-IDF : fréquent ici, rare ailleurs", "Similarité cosinus pour la recherche", "Limite : pas de sens contextuel → place du LLM", "Modèle de langue : prédire le prochain token"]),
      carte("amber", "Au-delà du cours (volet avancé)", ["Appel de fonctions par un LLM ouvert", "Deux architectures : direct vs plan", "Injection d'instructions cachées (RAG)", "Audit du correcteur par un humain (kappa)"])], PIED)
