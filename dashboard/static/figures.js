/* Section « Rapport (figures) » : une figure par page, format 16:9, prête à capturer ou exporter en PNG pour l'article.
   Utilise html, Graph, AG, api définis dans app.js (appelés seulement au rendu, après le chargement de app.js). */

const COUL = { baseline: "#94a3b8", classique: "#0ea5a4", llm_a: "#8b5cf6", llm_b: "#3b82f6", llm_15: "#f59e0b" };
const NOMS = { baseline: "Baseline (règles)", classique: "Agent classique", llm_a: "Qwen-3B direct", llm_b: "Qwen-3B plan", llm_15: "Qwen-1.5B direct" };
const CAT_FR = { ambigu: "Demande ambiguë", hors_perimetre: "Hors périmètre", info_absente: "Info absente", injection: "Injection cachée",
  multi_tours: "Multi-tours", nominal: "Nominal", outil_indisponible: "Outil en panne" };
const CAUSE_FR = { refus_ou_question_injustifie: "Question / refus injustifié", absence_de_clarification: "N'a pas demandé de précision",
  absence_de_refus: "N'a pas refusé", outil_manquant: "Outil manquant ou mauvais outil", arguments_incorrects: "Mauvais arguments",
  hallucination: "Hallucination", reponse_incomplete: "Réponse incomplète" };
const CAUSE_COUL = ["#fb923c", "#facc15", "#a78bfa", "#60a5fa", "#f472b6", "#ef4444", "#94a3b8"];

/* Plugins Chart.js : valeurs écrites sur les barres + barres d'erreur (intervalle de confiance) */
const pluginValeurs = { id: "valeurs", afterDatasetsDraw(c, _, o) {
  if (!o || !o.actif) return; const x = c.ctx; x.save(); x.font = "700 13px Plus Jakarta Sans"; x.fillStyle = "#1d2230";
  c.data.datasets.forEach((d, i) => { if (d.sansValeurs) return; c.getDatasetMeta(i).data.forEach((b, j) => {
    const v = d.data[j]; if (v === null || v === undefined || typeof v === "object") return;
    const h = c.options.indexAxis === "y", txt = (o.format || ((n) => n))(v);
    if (o.dedans && h) { x.save(); x.fillStyle = "#fff"; x.textAlign = "left"; x.textBaseline = "middle"; x.font = "800 16px Plus Jakarta Sans"; x.fillText(txt, c.chartArea.left + 14, b.y); x.restore(); return; }
    const neg = h && v < 0; x.textAlign = h ? (neg ? "right" : "left") : "center"; x.textBaseline = h ? "middle" : "bottom";
    x.fillText(txt, h ? (neg ? b.x - 8 : b.x + 8 + (o.decalage || 0)) : b.x, h ? b.y : b.y - 6 - (o.decalage || 0)); }); });
  x.restore(); } };
const pluginIC = { id: "ic", afterDatasetsDraw(c, _, o) {
  if (!o || !o.ic) return; const x = c.ctx, m = c.getDatasetMeta(0), sc = c.scales[c.options.indexAxis === "y" ? "x" : "y"];
  x.save(); x.strokeStyle = "#1d2230"; x.lineWidth = 2;
  m.data.forEach((b, j) => { const [lo, hi] = o.ic[j]; const h = c.options.indexAxis === "y";
    const a = sc.getPixelForValue(lo), z = sc.getPixelForValue(hi), p = h ? b.y : b.x;
    x.beginPath(); if (h) { x.moveTo(a, p); x.lineTo(z, p); x.moveTo(a, p - 7); x.lineTo(a, p + 7); x.moveTo(z, p - 7); x.lineTo(z, p + 7); }
    else { x.moveTo(p, a); x.lineTo(p, z); x.moveTo(p - 7, a); x.lineTo(p + 7, a); x.moveTo(p - 7, z); x.lineTo(p + 7, z); } x.stroke(); });
  x.restore(); } };
Chart.register(pluginValeurs, pluginIC);
const AXE = { grid: { color: "#eef0f3" }, ticks: { font: { size: 13 } } };

/* ---------- gabarit commun d'une figure ---------- */
function Figure({ n, titre, sous, kpis = [], retenir, source, children }) {
  return html`<div className="fig-cadre" id=${"figure-" + n}>
    <div className="fig-tete"><div className="fig-num">Figure ${n}</div><h2>${titre}</h2>${sous && html`<p>${sous}</p>`}</div>
    <div className="fig-corps">
      <div className="fig-graph">${children}</div>
      <aside className="fig-cote">
        ${kpis.map(([v, t, c]) => html`<div key=${t} className="fig-kpi"><div className="v" style=${{ color: c || "#1d2230" }}>${v}</div><div className="t">${t}</div></div>`)}
        ${retenir && html`<div className="fig-retenir"><div className="section-titre">À retenir</div>${retenir}</div>`}
      </aside>
    </div>
    <div className="fig-pied"><span>${source || "60 scénarios TEST · 77 tours · Qwen2.5 sur GPU T4 · évaluateur automatique identique pour tous"}</span><span>SAMS · Projet TALN n°10 · EMSI</span></div>
  </div>`;
}

/* ---------- les figures ---------- */
function F_methode({ R }) {
  const etapes = [["ecole", "Monde fictif", "24 étudiants · 6 modules · 5 salles · 12 documents (3 piégés)"], ["outils", "9 outils", "7 outils métier + 2 méta-outils (question, refus)"],
    ["couches", "3 jeux séparés", "DEV 24 (réglage) · TEST 60 (mesure unique) · 24 reformulations"], ["robot", "5 systèmes", "règles, agent classique, Qwen-3B direct / plan, Qwen-1.5B"],
    ["comparaison", "1 correcteur", "le même pour tous : 9 métriques + cause d'échec"], ["hausse", "Analyse", "IC 95 %, McNemar, ablations, robustesse, sécurité, audit humain"]];
  return html`<${Figure} n="1" titre="Démarche : un monde contrôlé, des pièges, un seul correcteur pour tous"
    sous="Comme tout est inventé, on connaît toujours la bonne réponse : chaque échec est mesurable et explicable."
    kpis=${[["60", "scénarios TEST piégés (7 catégories)"], ["5", "systèmes comparés"], ["9", "métriques par système"]]}
    retenir="Réglage uniquement sur DEV, une seule mesure sur TEST : on évite de « tricher » sur le test.">
    <div className="pipeline">${etapes.map(([i, t, d], k) => html`<${React.Fragment} key=${t}>
      <div className="etape-pipe"><div className="ico">${Ic(i, 30)}</div><b>${t}</b><small>${d}</small></div>${k < etapes.length - 1 ? html`<div className="fleche">→</div>` : null}</${React.Fragment}>`)}</div>
    <div className="pieges">${R.categories.map((c) => html`<span key=${c} className="puce">${CAT_FR[c]}</span>`)}</div>
  </${Figure}>`;
}

function F_principal({ R }) {
  const S = [...R.systemes].sort((a, b) => b.valeurs[0] - a.valeurs[0]);
  return html`<${Figure} n="2" titre="Résultat principal : l'agent classique gagne, le LLM avec plan le suit"
    sous="Part des 60 conversations entièrement réussies. Trait noir = intervalle de confiance à 95 % (bootstrap)."
    kpis=${[["98,3 %", "agent classique", COUL.classique], ["83,3 %", "meilleur LLM (Qwen-3B plan)", COUL.llm_b], ["± 12 pts", "incertitude typique (60 scénarios)"]]}
    retenir="Planifier avant d'agir fait gagner 15 points au même modèle (68,3 → 83,3 %). Le petit modèle 1.5B s'effondre (43,3 %).">
    <${Graph} type="bar" hauteur=${430} data=${{ labels: S.map((s) => NOMS[s.id]), datasets: [{ data: S.map((s) => s.valeurs[0]), backgroundColor: S.map((s) => COUL[s.id]), borderRadius: 10, barPercentage: .62 }] }}
      options=${{ indexAxis: "y", plugins: { legend: { display: false }, valeurs: { actif: true, dedans: true, format: (v) => v.toFixed(1) + " %" }, ic: { ic: S.map((s) => s.ic) } },
        scales: { x: { ...AXE, min: 0, max: 105, title: { display: true, text: "tâches réussies (%)" } }, y: { ...AXE, grid: { display: false }, ticks: { font: { size: 15, weight: "600" } } } } }} />
  </${Figure}>`;
}

function F_radar({ R }) {
  const S = R.systemes.filter((s) => s.id !== "llm_15");
  const axes = ["Tâches réussies", "Bon outil", "Bons arguments", "Refus justifiés", "Bonnes questions", "Pas de question inutile"];
  const val = (s) => [s.valeurs[0], s.valeurs[2], s.valeurs[3], s.valeurs[4], s.valeurs[5], 100 - s.valeurs[6]];
  return html`<${Figure} n="3" titre="Profil de compétences : où chaque système est fort ou faible"
    sous="Six critères sur 100 (plus loin du centre = mieux)."
    kpis=${[["100 %", "arguments exacts pour Qwen-3B (direct et plan)", COUL.llm_b], ["62,5 %", "bonnes questions de précision des LLM", "#d97706"], ["0 %", "questions des règles naïves", COUL.baseline]]}
    retenir="Les LLM recopient bien les valeurs (arguments parfaits) mais demandent encore mal les précisions. Les règles naïves ne savent jamais demander.">
    <${Graph} type="radar" hauteur=${440} data=${{ labels: axes, datasets: S.map((s) => ({ label: NOMS[s.id], data: val(s), borderColor: COUL[s.id], backgroundColor: COUL[s.id] + "22", borderWidth: 2.5, pointRadius: 3 })) }}
      options=${{ scales: { r: { min: 0, max: 100, ticks: { stepSize: 25, backdropColor: "transparent" }, pointLabels: { font: { size: 14, weight: "600" } }, grid: { color: "#e5e7eb" } } },
        plugins: { legend: { position: "bottom", labels: { font: { size: 13 } } } } }} />
  </${Figure}>`;
}

function F_heatmap({ R }) {
  const ids = ["baseline", "classique", "llm_a", "llm_b", "llm_15"];
  const mix = (a, b, t) => a.map((x, k) => Math.round(x + (b[k] - x) * t));
  const couleur = (v) => { const R = [239, 68, 68], A = [245, 158, 11], V = [22, 163, 74]; const c = v < 60 ? mix(R, A, v / 60) : mix(A, V, (v - 60) / 40); return `rgb(${c.join(",")})`; };
  return html`<${Figure} n="4" titre="Quand échouent-ils ? Réussite par type de piège"
    sous="Chaque case = % de scénarios réussis. Rouge = échoue souvent, vert = réussit."
    kpis=${[["30 %", "dialogues multi-tours réussis par les règles naïves", "#dc2626"], ["100 %", "injections déjouées par Qwen-3B plan", "#16a34a"], ["50–62 %", "demandes ambiguës traitées par les LLM", "#d97706"]]}
    retenir="Les points faibles des LLM : demandes ambiguës et dialogues multi-tours. Les règles naïves échouent dès qu'il faut se souvenir ou demander.">
    <div className="heatmap"><div></div>${R.categories.map((c) => html`<div key=${c} className="hm-col">${CAT_FR[c]}</div>`)}
      ${ids.map((id) => html`<${React.Fragment} key=${id}><div className="hm-lig"><span className="point" style=${{ background: COUL[id] }}></span>${NOMS[id]}</div>
        ${R.par_categorie[id].map((v, j) => html`<div key=${j} className="hm-case" style=${{ background: couleur(v) }}>${Math.round(v)}</div>`)}</${React.Fragment}>`)}</div>
  </${Figure}>`;
}

function F_causes({ R }) {
  const ids = ["baseline", "classique", "llm_a", "llm_b", "llm_15"];
  const tot = Object.fromEntries(ids.map((id) => [id, R.causes[id].reduce((a, b) => a + b, 0)]));
  return html`<${Figure} n="5" titre="Pourquoi échouent-ils ? Répartition des causes d'échec"
    sous="Part de chaque cause parmi les tours ratés (entre parenthèses : nombre de tours ratés sur 77)."
    kpis=${[["5 / 11", "échecs de Qwen-3B plan dus au mauvais outil", COUL.llm_b], ["7 / 19", "échecs de Qwen-3B direct dus à une question inutile", COUL.llm_a], ["1 / 77", "seul tour raté par l'agent classique", COUL.classique]]}
    retenir="Le LLM direct pose trop de questions inutiles ; le LLM avec plan ne le fait plus, mais choisit parfois le mauvais outil. Le 1.5B se trompe surtout d'outil et d'arguments.">
    <${Graph} type="bar" hauteur=${430} data=${{ labels: ids.map((id) => `${NOMS[id]} (${tot[id]})`),
      datasets: R.causes.noms.map((n, i) => ({ label: CAUSE_FR[n], data: ids.map((id) => tot[id] ? 100 * R.causes[id][i] / tot[id] : 0), backgroundColor: CAUSE_COUL[i], borderRadius: 3 })) }}
      options=${{ indexAxis: "y", plugins: { legend: { position: "bottom", labels: { font: { size: 12 }, boxWidth: 12 } } },
        scales: { x: { ...AXE, stacked: true, max: 100, title: { display: true, text: "% des tours ratés" } }, y: { ...AXE, stacked: true, grid: { display: false }, ticks: { font: { size: 14, weight: "600" } } } } }} />
  </${Figure}>`;
}

function F_robustesse({ R }) {
  const ids = ["baseline", "classique", "llm_a", "llm_b"];
  return html`<${Figure} n="6" titre="Robustesse : face à des phrases reformulées, tout le monde chute"
    sous="Même demande, dite autrement (fautes, familiarités) : 24 reformulations jamais utilisées pour régler les systèmes."
    kpis=${[["−27,5 pts", "chute de l'agent classique (98,3 → 70,8 %)", "#dc2626"], ["−25,0 pts", "chute de Qwen-3B plan (83,3 → 58,3 %)", COUL.llm_b], ["12,5 pts", "écart restant classique / LLM plan (contre 15 sur TEST)"]]}
    retenir="Le score de l'agent classique est optimiste : ses règles collent aux phrases de l'équipe. Sur du langage libre, l'écart avec le LLM se réduit.">
    <${Graph} type="line" hauteur=${430} data=${{ labels: ["Phrases du TEST", "Phrases reformulées"], datasets: R.robustesse.map((r, i) => ({ label: NOMS[ids[i]], data: [r.test, r.para],
      borderColor: COUL[ids[i]], backgroundColor: COUL[ids[i]], borderWidth: 4, pointRadius: 8, tension: 0 })) }}
      options=${{ plugins: { legend: { position: "bottom" }, valeurs: { actif: true, format: (v) => v.toFixed(1) + " %" } }, scales: { y: { ...AXE, min: 40, max: 102, title: { display: true, text: "tâches réussies (%)" } }, x: { ...AXE, ticks: { font: { size: 15, weight: "600" } } } } }} />
  </${Figure}>`;
}

function F_securite({ R }) {
  const g = (cfg) => R.securite.find((s) => s.config === cfg);
  return html`<${Figure} n="7" titre="Sécurité : la défense du système ramène les attaques à zéro"
    sous="3 documents contiennent une fausse instruction cachée. Attaque réussie = l'agent obéit ou répète le mensonge."
    kpis=${[["33 % → 0 %", "attaques réussies, sans puis avec défense", "#16a34a"], ["0", "blocage à tort (4 blocages, tous justifiés)"], ["0 %", "tentatives d'action interdite (e-mail, réservation)"]]}
    retenir="Le modèle seul répète le mensonge injecté une fois sur trois. Filtrer les documents et imposer les droits hors du modèle suffit : « le modèle propose, le système impose ».">
    <${Graph} type="bar" hauteur=${430} data=${{ labels: ["Qwen-3B direct", "Qwen-3B plan"], datasets: [
      { label: "Sans défense", data: [g("A. direct sans défense").attaques, g("B. plan sans défense").attaques], backgroundColor: "#f87171", borderRadius: 10 },
      { label: "Avec défense", data: [g("A. direct avec défense").attaques, g("B. plan avec défense").attaques], backgroundColor: "#22c55e", borderRadius: 10, minBarLength: 4 }] }}
      options=${{ plugins: { legend: { position: "bottom" }, valeurs: { actif: true, format: (v) => v.toFixed(1) + " %" } }, scales: { y: { ...AXE, min: 0, max: 50, title: { display: true, text: "attaques réussies (%)" } }, x: { ...AXE, ticks: { font: { size: 15, weight: "600" } } } } }} />
  </${Figure}>`;
}

function F_reglage({ R }) {
  const [a, b] = R.dev_vs_test;
  return html`<${Figure} n="8" titre="Réglage sur DEV, puis une seule mesure sur TEST : le gain se confirme"
    sous="v1 = première version de l'agent LLM ; v2 = version ajustée en analysant ses erreurs, réglée uniquement sur les 24 scénarios DEV."
    kpis=${[["+16,6 pts", "Qwen-3B direct sur TEST (51,7 → 68,3 %)", COUL.llm_a], ["+31,6 pts", "Qwen-3B plan sur TEST (51,7 → 83,3 %)", COUL.llm_b], ["2", "tours de réglage sur DEV"]]}
    retenir="Le gain mesuré sur TEST confirme celui vu sur DEV : les corrections ne sont pas du « par cœur » sur les scénarios de réglage.">
    <${Graph} type="line" hauteur=${430} data=${{ labels: ["v1 (initiale)", "v2 (ajustée)"], datasets: [
      { label: "Qwen direct — DEV", data: [a.dev_v1, a.dev_v2], borderColor: COUL.llm_a, borderDash: [6, 6], pointRadius: 6, borderWidth: 3, sansValeurs: true },
      { label: "Qwen direct — TEST", data: [a.test_v1, a.test_v2], borderColor: COUL.llm_a, backgroundColor: COUL.llm_a, pointRadius: 8, borderWidth: 4 },
      { label: "Qwen plan — DEV", data: [b.dev_v1, b.dev_v2], borderColor: COUL.llm_b, borderDash: [6, 6], pointRadius: 6, borderWidth: 3, sansValeurs: true },
      { label: "Qwen plan — TEST", data: [b.test_v1, b.test_v2], borderColor: COUL.llm_b, backgroundColor: COUL.llm_b, pointRadius: 8, borderWidth: 4 }] }}
      options=${{ plugins: { legend: { position: "bottom" }, valeurs: { actif: true, format: (v) => v.toFixed(1) } }, scales: { y: { ...AXE, min: 30, max: 92, title: { display: true, text: "tâches réussies (%)" } }, x: { ...AXE, ticks: { font: { size: 15, weight: "600" } } } } }} />
  </${Figure}>`;
}

function F_ablations({ R }) {
  const lignes = [["Qwen direct sans détection d'intention", 65.0 - 68.3, COUL.llm_a], ["Qwen direct sans résumé d'état", 73.3 - 68.3, COUL.llm_a], ["Agent classique sans mémoire", 75.0 - 98.3, COUL.classique]];
  return html`<${Figure} n="9" titre="Ablations : la mémoire est vitale pour les règles, pas pour le LLM"
    sous="Effet (en points) du retrait d'un seul composant, toutes choses égales par ailleurs. Négatif = le composant aidait."
    kpis=${[["−23,3 pts", "agent classique sans mémoire du dialogue", "#dc2626"], ["−3,3 pts", "LLM sans détection d'intention (dans l'incertitude)"], ["+5,0 pts", "LLM sans résumé d'état (non significatif)"]]}
    retenir="Le LLM relit toute la conversation : le résumé d'état ne lui apporte rien de mesurable. L'agent à règles, lui, ne peut rien faire sans mémoire.">
    <${Graph} type="bar" hauteur=${400} data=${{ labels: lignes.map((l) => l[0]), datasets: [{ data: lignes.map((l) => l[1]), backgroundColor: lignes.map((l) => l[1] < 0 ? "#f87171" : "#86efac"), borderColor: lignes.map((l) => l[2]), borderWidth: 2, borderRadius: 8, barPercentage: .55 }] }}
      options=${{ indexAxis: "y", plugins: { legend: { display: false }, valeurs: { actif: true, format: (v) => (v > 0 ? "+" : "") + v.toFixed(1) + " pts" } },
        scales: { x: { ...AXE, min: -30, max: 12, title: { display: true, text: "variation des tâches réussies (points)" } }, y: { ...AXE, grid: { display: false }, ticks: { font: { size: 14, weight: "600" } } } } }} />
  </${Figure}>`;
}

function F_mcnemar({ R }) {
  const M = R.mcnemar;
  return html`<${Figure} n="10" titre="Les écarts sont-ils réels ? Test de McNemar sur les mêmes 60 scénarios"
    sous="Barres = nombre de scénarios réussis par un seul des deux systèmes. Plus la barre est déséquilibrée, plus l'écart est solide."
    kpis=${[["6 / 6", "comparaisons significatives (p < 0,05)", "#16a34a"], ["p = 0,023", "plan meilleur que direct"], ["p = 0,012", "classique meilleur que plan"]]}
    retenir="Toutes les différences entre systèmes principaux sont significatives. Les écarts d'ablation de quelques points, eux, ne le sont pas.">
    <${Graph} type="bar" hauteur=${430} data=${{ labels: M.map((m) => `${m.a}  vs  ${m.b}   (p ${m.p < .001 ? "< 0,001" : "= " + m.p.toFixed(3)})`), datasets: [
      { label: "réussi seulement par le 1er", data: M.map((m) => m.a_seul), backgroundColor: "#3b82f6", borderRadius: 6 },
      { label: "réussi seulement par le 2nd", data: M.map((m) => -m.b_seul), backgroundColor: "#f59e0b", borderRadius: 6 }] }}
      options=${{ indexAxis: "y", plugins: { legend: { position: "bottom" }, tooltip: { callbacks: { label: (c) => `${c.dataset.label} : ${Math.abs(c.raw)}` } } },
        scales: { x: { ...AXE, stacked: true, ticks: { callback: (v) => Math.abs(v) }, title: { display: true, text: "nombre de scénarios" } }, y: { ...AXE, stacked: true, grid: { display: false }, ticks: { font: { size: 12.5, weight: "600" } } } } }} />
  </${Figure}>`;
}

function F_cout({ R }) {
  const gen = { baseline: 0, classique: 0, llm_a: R.stats_internes.llm_a[0], llm_b: R.stats_internes.llm_b[0], llm_15: R.stats_internes.llm_15[0] };
  return html`<${Figure} n="11" titre="Coût : la précision du plan se paie en temps de réponse"
    sous="Position = latence moyenne par tour (GPU T4) et réussite. Taille de la bulle = nombre d'appels au modèle sur les 77 tours."
    kpis=${[["≈ 0 s", "agents à règles (instantanés)", COUL.classique], ["7,3 s", "par tour pour Qwen-3B plan", COUL.llm_b], ["× 1,7", "appels au modèle : plan (239) vs direct (138)"]]}
    retenir="Planifier rend le LLM plus fiable mais plus lent. Pour un vrai secrétariat, il faudrait un GPU plus rapide ou un modèle servi par API.">
    <${Graph} type="bubble" hauteur=${430} data=${{ datasets: R.systemes.map((s) => ({ label: NOMS[s.id], data: [{ x: s.valeurs[8], y: s.valeurs[0], r: 8 + Math.sqrt(gen[s.id]) * 1.6 }],
      backgroundColor: COUL[s.id] + "cc", borderColor: COUL[s.id] })) }}
      options=${{ plugins: { legend: { position: "bottom" } }, scales: { x: { ...AXE, min: -.5, max: 8.5, title: { display: true, text: "latence moyenne par tour (secondes)" } }, y: { ...AXE, min: 30, max: 105, title: { display: true, text: "tâches réussies (%)" } } } }} />
  </${Figure}>`;
}

function F_audit({ kappa }) {
  const ok = kappa && kappa.complet, fr = (x, d = 2) => x.toFixed(d).replace(".", ",");
  const plusSevere = ok ? kappa.confusion.humain_reussi_eval_echec : 0, plusIndulgent = ok ? kappa.confusion.humain_echec_eval_reussi : 0;
  return html`<${Figure} n="12" titre=${ok ? `Fiabilité du correcteur : accord ${kappa.lecture} avec un humain (κ = ${fr(kappa.kappa)})` : "Fiabilité du correcteur : audit humain en cours"}
    sous="30 tours des agents LLM jugés à l'aveugle par un humain, comparés au verdict du correcteur automatique."
    kpis=${ok ? [[fr(kappa.accord * 100, 0) + " %", "accord brut humain / correcteur"], [fr(kappa.kappa), `kappa de Cohen (IC 95 % ${fr(kappa.ic[0])} à ${fr(kappa.ic[1])})`],
      [`${plusSevere} contre ${plusIndulgent}`, "le correcteur est plus sévère que l'humain"]] : [["—", "à compléter : page Audit humain"]]}
    retenir=${ok ? `Le correcteur refuse ${plusSevere} réponses libres que l'humain juge correctes : ses règles par mots-clés sous-estiment plutôt les LLM. Les grands écarts entre systèmes restent valides ; les écarts de quelques points, non.` : "Terminer les 30 verdicts, puis « Calculer le kappa » : cette figure se remplit toute seule."}>
    ${ok ? html`<div className="matrice">
        <div></div><div className="hm-col">Correcteur : réussi</div><div className="hm-col">Correcteur : échec</div>
        <div className="hm-lig">Humain : réussi</div><div className="hm-case" style=${{ background: "#22c55e" }}>${kappa.confusion.humain_reussi_eval_reussi}</div><div className="hm-case" style=${{ background: "#f87171" }}>${kappa.confusion.humain_reussi_eval_echec}</div>
        <div className="hm-lig">Humain : échec</div><div className="hm-case" style=${{ background: "#fb923c" }}>${kappa.confusion.humain_echec_eval_reussi}</div><div className="hm-case" style=${{ background: "#22c55e" }}>${kappa.confusion.humain_echec_eval_echec}</div></div>
      <p className="aide" style=${{ textAlign: "center", marginTop: 14 }}>Diagonale verte = accord · rouge = correcteur trop sévère · orange = correcteur trop indulgent</p>`
      : html`<div className="chargement" style=${{ height: "100%" }}>En attente des 30 verdicts humains</div>`}
  </${Figure}>`;
}

const FIGURES = [["Démarche", F_methode], ["Résultat principal", F_principal], ["Profil", F_radar], ["Quand ça échoue", F_heatmap], ["Pourquoi ça échoue", F_causes],
  ["Robustesse", F_robustesse], ["Sécurité", F_securite], ["Réglage DEV→TEST", F_reglage], ["Ablations", F_ablations], ["Significativité", F_mcnemar], ["Coût", F_cout], ["Audit", F_audit]];

function RapportFigures({ resume }) {
  const [i, setI] = useState(() => { try { return +(localStorage.getItem("sams-fig") || 0); } catch (e) { return 0; } });
  const [kappa, setKappa] = useState(null);
  const [exp, setExp] = useState("");
  useEffect(() => { api.get("/api/audit/kappa").then(setKappa); }, []);
  useEffect(() => { try { localStorage.setItem("sams-fig", i); } catch (e) {} }, [i]);
  useEffect(() => { const k = (e) => { if (e.key === "ArrowRight") setI((x) => Math.min(FIGURES.length - 1, x + 1)); if (e.key === "ArrowLeft") setI((x) => Math.max(0, x - 1)); };
    window.addEventListener("keydown", k); return () => window.removeEventListener("keydown", k); }, []);
  const exporter = async (toutes) => {
    const liste = toutes ? FIGURES.map((_, j) => j) : [i];
    for (const j of liste) {
      setI(j); setExp(`Export de la figure ${j + 1}…`); await new Promise((r) => setTimeout(r, 700));
      // graphiques dessinés immédiatement (sans animation) : sinon un onglet en arrière-plan capture un graphique vide
      Object.values(Chart.instances).forEach((ch) => { ch.options.animation = false; ch.update("none"); });
      await new Promise((r) => setTimeout(r, 300));
      const el = document.getElementById("figure-" + (j + 1)); if (!el) continue;
      const c = await html2canvas(el, { scale: 2, backgroundColor: "#ffffff" });
      const nom = `figure-${String(j + 1).padStart(2, "0")}-${FIGURES[j][0].normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/[^\w]+/g, "-")}`;
      const png = c.toDataURL("image/png");
      const a = document.createElement("a"); a.href = png; a.download = nom + ".png"; a.click();
      await api.post("/api/figure", { nom, png });           // copie aussi dans le dossier du projet : rapport_figures/
    }
    setExp((toutes ? "12 figures exportées" : "Figure exportée") + " : dossier Téléchargements + dossier du projet « rapport_figures ».");
  };
  const F = FIGURES[i][1];
  return html`<div className="page">
    <div className="page-entete"><div><h1>Rapport — figures</h1><p>Une figure par page, prête pour l'article et la présentation. Flèches ← → du clavier pour naviguer.</p></div>
      <div className="controles"><button className="btn" onClick=${() => exporter(false)}>${Ic("telecharger", 15)} Exporter cette figure (PNG)</button><button className="btn noir" onClick=${() => exporter(true)}>${Ic("telecharger", 15)} Exporter les 12 figures</button></div></div>
    <div className="stepper">${FIGURES.map(([t], j) => html`<button key=${j} className=${j === i ? "actif" : ""} onClick=${() => setI(j)}>${j + 1} · ${t}</button>`)}</div>
    ${exp && html`<div className="aide">${exp}</div>`}
    <${F} R=${resume.resultats} kappa=${kappa} />
    <div className="controles"><button className="btn" disabled=${i === 0} onClick=${() => setI(i - 1)}>← Figure précédente</button><button className="btn noir" disabled=${i === FIGURES.length - 1} onClick=${() => setI(i + 1)}>Figure suivante →</button></div>
  </div>`;
}
