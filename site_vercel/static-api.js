/* Version en ligne de SAMS : remplace le serveur Python local.
   - données en lecture : fichiers data/*.json précalculés depuis le notebook ;
   - parties en direct (chat, outil, évaluation, labo, bureau) : vrai code Python exécuté dans le navigateur (worker.js, Pyodide) ;
   - audit : les verdicts sont gardés dans ce navigateur. */
(function () {
  const vraiFetch = window.fetch.bind(window);
  const VraiES = window.EventSource;

  // ---------- bandeau d'état du moteur Python
  const bandeau = document.createElement("div");
  bandeau.style.cssText = "position:fixed;left:16px;bottom:16px;z-index:9999;max-width:min(420px,calc(100vw - 32px));padding:10px 14px;border-radius:12px;" +
    "background:#111827;color:#fff;font:500 13px/1.4 'Plus Jakarta Sans',system-ui,sans-serif;box-shadow:0 8px 24px rgba(0,0,0,.18)";
  bandeau.textContent = "Moteur Python : chargement dans le navigateur (environ 20 s la première fois)…";
  const montrer = () => document.body ? document.body.appendChild(bandeau) : setTimeout(montrer, 50);
  montrer();

  // ---------- moteur Python (Web Worker)
  const worker = new Worker("worker.js");
  let n = 0; const attente = {};
  worker.onmessage = (e) => {
    const d = e.data;
    if (d.pret) { bandeau.textContent = "Moteur Python prêt : les agents répondent en direct."; bandeau.style.background = "#065f46"; setTimeout(() => bandeau.remove(), 3500); return; }
    if (d.echec) { bandeau.textContent = "Le moteur Python n'a pas pu démarrer : " + d.echec; bandeau.style.background = "#991b1b"; return; }
    if (attente[d.id]) { attente[d.id](JSON.parse(d.r)); delete attente[d.id]; }
  };
  const appelPy = (route, corps) => new Promise((res) => { const id = ++n; attente[id] = res; worker.postMessage({ id, route, corps }); });

  // ---------- données précalculées
  const cache = {};
  const json = (f) => cache[f] || (cache[f] = vraiFetch("data/" + f).then((r) => { if (!r.ok) throw new Error(f); return r.json(); }));
  const reponse = (obj) => new Response(JSON.stringify(obj), { status: 200, headers: { "Content-Type": "application/json" } });

  // ---------- audit (verdicts gardés dans ce navigateur)
  const CLE_LS = "sams_audit_v1";
  const lireLS = () => { try { return JSON.parse(localStorage.getItem(CLE_LS) || "{}"); } catch { return {}; } };
  const ecrireLS = (v) => { try { localStorage.setItem(CLE_LS, JSON.stringify(v)); } catch { /* stockage indisponible */ } };
  const auditLignes = async () => { const base = await json("audit.json"); const loc = lireLS(); return base.map((l) => (loc[l.n] ? { ...l, ...loc[l.n] } : l)); };
  const r3 = (x) => Math.round(x * 1000) / 1000;
  async function kappa() {
    if (!Object.keys(lireLS()).length) return json("kappa.json");          // audit d'origine : résultat calculé par le notebook
    const lignes = await auditLignes(), cle = await json("cle_audit.json");
    const faits = lignes.filter((l) => l.verdict === "réussi" || l.verdict === "échec");
    if (faits.length < lignes.length) return { complet: false, faits: faits.length, total: lignes.length };
    const h = lignes.map((l) => l.verdict === "réussi"), e = lignes.map((l) => cle[l.n].verdict_evaluateur === "réussi");
    const k = (idx) => {
      const m = idx.length, po = idx.filter((i) => h[i] === e[i]).length / m;
      const ph = idx.filter((i) => h[i]).length / m, pe_ = idx.filter((i) => e[i]).length / m;
      const pe = ph * pe_ + (1 - ph) * (1 - pe_);
      return [pe < 1 ? (po - pe) / (1 - pe) : 1, po];
    };
    const tous = h.map((_, i) => i); const [kv, po] = k(tous);
    let s = 42; const alea = () => { s = (s * 1664525 + 1013904223) % 4294967296; return s / 4294967296; };
    const boots = []; for (let b = 0; b < 2000; b++) { const v = k(tous.map(() => Math.floor(alea() * h.length)))[0]; if (isFinite(v)) boots.push(v); }
    boots.sort((a, b) => a - b); const q = (p) => boots[Math.min(boots.length - 1, Math.floor(p * boots.length))];
    const nb = (f) => tous.filter(f).length;
    const lecture = kv <= 0.2 ? "faible" : kv <= 0.4 ? "passable" : kv <= 0.6 ? "modéré" : kv <= 0.8 ? "substantiel" : "quasi parfait";
    return { complet: true, kappa: r3(kv), ic: [r3(q(0.025)), r3(q(0.975))], accord: r3(po), lecture, n: lignes.length,
      confusion: { humain_reussi_eval_reussi: nb((i) => h[i] && e[i]), humain_reussi_eval_echec: nb((i) => h[i] && !e[i]),
                   humain_echec_eval_reussi: nb((i) => !h[i] && e[i]), humain_echec_eval_echec: nb((i) => !h[i] && !e[i]) },
      desaccords: lignes.filter((l, i) => h[i] !== e[i]).map((l) => ({ ...l, ...cle[l.n] })) };
  }

  // ---------- routes /api/*
  window.fetch = async (u, o = {}) => {
    const url = typeof u === "string" ? u : u.url;
    if (!url.startsWith("/api/")) return vraiFetch(u, o);
    const [chemin, qs] = url.split("?"); const q = Object.fromEntries(new URLSearchParams(qs || ""));
    const corps = o.body ? JSON.parse(o.body) : {};
    if ((o.method || "GET").toUpperCase() === "GET") {
      if (chemin === "/api/resume") return reponse(await json("resume.json"));
      if (chemin === "/api/scenarios") return reponse(await json(`scenarios_${q.jeu || "TEST"}.json`));
      if (chemin === "/api/traces") return reponse(await json(`traces_${q.systeme || "classique"}.json`).catch(() => []));
      if (chemin === "/api/donnees") return reponse(await json("donnees.json"));
      if (chemin === "/api/audit") return reponse(await auditLignes());
      if (chemin === "/api/audit/kappa") return reponse(await kappa());
      return reponse({ erreur: "route inconnue" });
    }
    if (chemin === "/api/audit") {
      const loc = lireLS(); loc[corps.n] = { verdict: corps.verdict, cause: corps.cause || "", commentaire: corps.commentaire || "" }; ecrireLS(loc);
      return reponse({ ok: true, excel: "verdict gardé dans ce navigateur (version en ligne)" });
    }
    if (chemin === "/api/figure") return reponse({ ok: true, fichier: "dossier Téléchargements" });
    return reponse(await appelPy(chemin, corps));          // chat, chat/reset, outil, evaluer, labo
  };

  // ---------- bureau en direct : même déroulé que le flux du serveur local
  class FluxDirect {
    constructor(url) {
      this.ferme = false; this.onmessage = null; this.onerror = null;
      const q = Object.fromEntries(new URLSearchParams(url.split("?")[1] || ""));
      this.lancer(parseFloat(q.vitesse || "1"), q.jeu || "TEST").catch(() => this.onerror && this.onerror());
    }
    close() { this.ferme = true; }
    async lancer(vitesse, jeu) {
      const pause = Math.max(0.05, 0.9 / vitesse) * 1000, dormir = (ms) => new Promise((r) => setTimeout(r, ms));
      const emettre = (ev) => { if (!this.ferme && this.onmessage) this.onmessage({ data: JSON.stringify(ev) }); };
      const scenarios = await json(`scenarios_${jeu}.json`), relus = {};
      if (jeu === "TEST") for (const s of ["llm_a", "llm_b"]) {
        try { relus[s] = {}; (await json(`traces_${s}.json`)).forEach((l) => (relus[s][l.scenario] = relus[s][l.scenario] || []).push(l)); } catch { delete relus[s]; }
      }
      for (const sc of scenarios) {
        for (const agent of ["baseline", "classique"]) {
          const lignes = await appelPy("/api/evaluer", { agent, scenario: sc.id, jeu });
          for (const l of Array.isArray(lignes) ? lignes : []) { if (this.ferme) return; emettre({ agent, mode: "direct", ...l }); await dormir(pause / 2); }
        }
        for (const s of Object.keys(relus)) for (const l of relus[s][sc.id] || []) { if (this.ferme) return; emettre({ agent: s, mode: "relu (GPU Colab)", ...l }); await dormir(pause / 2); }
      }
      emettre({ fin: true });
    }
  }
  window.EventSource = function (url, o) { return String(url).startsWith("/api/") ? new FluxDirect(url) : new VraiES(url, o); };
})();
