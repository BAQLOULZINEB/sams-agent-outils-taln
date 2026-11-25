/* Bureau isométrique : les agents sont des employés de l'école, dessinés en SVG (aucune image externe). */
(function () {
  const html = htm.bind(React.createElement);
  const W = 1000, H = 640, S = 44, OX = 500, OY = 120;
  const iso = (x, y, z = 0) => [OX + (x - y) * S * 0.866, OY + (x + y) * S * 0.5 - z * S];
  const pts = (l) => l.map((p) => iso(...p).join(",")).join(" ");

  function boite(x, y, z, w, d, h, c, cle) {          // c = [dessus, face gauche, face droite]
    return html`<g key=${cle}>
      <polygon points=${pts([[x, y + d, z], [x + w, y + d, z], [x + w, y + d, z + h], [x, y + d, z + h]])} fill=${c[1]} />
      <polygon points=${pts([[x + w, y, z], [x + w, y + d, z], [x + w, y + d, z + h], [x + w, y, z + h]])} fill=${c[2]} />
      <polygon points=${pts([[x, y, z + h], [x + w, y, z + h], [x + w, y + d, z + h], [x, y + d, z + h]])} fill=${c[0]} />
    </g>`;
  }
  const BLANC = ["#ffffff", "#e9ebef", "#dcdfe5"], GRIS = ["#f4f5f7", "#d9dce2", "#c9cdd5"], BOIS = ["#f1e7da", "#d9c7b0", "#c9b598"];

  function plante(x, y, cle, grand) {
    const [px, py] = iso(x + .3, y + .3, 0), k = grand ? 1.35 : 1;
    return html`<g key=${cle}>
      ${boite(x, y, 0, .6, .6, .55, BLANC, cle + "p")}
      <g transform=${`translate(${px} ${py - .55 * S - 6}) scale(${k})`}>
        <ellipse cx="0" cy="-14" rx="16" ry="22" fill="#4ade80" /><ellipse cx="-11" cy="-4" rx="10" ry="15" fill="#22c55e" />
        <ellipse cx="11" cy="-6" rx="10" ry="16" fill="#16a34a" /><ellipse cx="2" cy="-30" rx="8" ry="11" fill="#86efac" />
      </g></g>`;
  }

  // Un employé assis : cheveux, peau, haut. etat = repos | travail | ok | ko
  function employe(a, etat, choisi, onClic) {
    const [px, py] = iso(a.x + .45, a.y - .35, 0);
    const bob = etat === "travail" ? "bob" : "";
    return html`<g key=${"e" + a.id} transform=${`translate(${px} ${py})`} style=${{ cursor: "pointer" }} onClick=${() => onClic(a.id)}>
      <ellipse cx="0" cy="6" rx="24" ry="9" fill="rgba(0,0,0,.08)" />
      <rect x="-17" y="-40" width="34" height="38" rx="9" fill="#e5e7eb" />
      <g className=${bob}>
        <path d="M-15 -4 Q-16 -34 0 -36 Q16 -34 15 -4 Z" fill=${a.haut} />
        <rect x="-19" y="-24" width="8" height="18" rx="4" fill=${a.haut} /><rect x="11" y="-24" width="8" height="18" rx="4" fill=${a.haut} />
        <circle cx="0" cy="-50" r="14" fill=${a.peau} />
        <path d=${a.coiffure} fill=${a.cheveux} />
        <circle cx="-5" cy="-49" r="1.7" fill="#1f2937" /><circle cx="5" cy="-49" r="1.7" fill="#1f2937" />
        <path d="M-4 -43 Q0 -40 4 -43" stroke="#be185d" strokeWidth="1.5" fill="none" strokeLinecap="round" />
      </g>
      ${choisi ? html`<ellipse cx="0" cy="6" rx="30" ry="12" fill="none" stroke="#14171f" strokeWidth="2" strokeDasharray="4 4" />` : null}
    </g>`;
  }

  function poste(a, etat) {                          // bureau + écran devant l'employé
    const couleurEcran = { repos: "#cbd5e1", travail: "#60a5fa", ok: "#4ade80", ko: "#f87171" }[etat] || "#cbd5e1";
    return html`<g key=${"p" + a.id}>
      ${boite(a.x - .2, a.y, 0, 1.5, .9, .72, BOIS, a.id + "d")}
      ${boite(a.x + .25, a.y + .15, .72, .6, .12, .5, ["#334155", "#1e293b", "#0f172a"], a.id + "m")}
      <polygon points=${pts([[a.x + .29, a.y + .27, .76], [a.x + .81, a.y + .27, .76], [a.x + .81, a.y + .27, 1.18], [a.x + .29, a.y + .27, 1.18]])}
        fill=${couleurEcran} className=${etat === "travail" ? "clignote" : ""} />
      ${boite(a.x + .95, a.y + .3, .72, .25, .35, .04, ["#e2e8f0", "#cbd5e1", "#cbd5e1"], a.id + "c")}
    </g>`;
  }

  function SceneBureau({ agents, etats, choisi, onChoisir, bulles, scores }) {
    const elems = [];
    // sol + murs
    elems.push(html`<polygon key="sol" points=${pts([[0, 0, 0], [12, 0, 0], [12, 10, 0], [0, 10, 0]])} fill="#f8f9fb" stroke="#e5e7eb" />`);
    for (let i = 1; i < 12; i++) elems.push(html`<polyline key=${"gx" + i} points=${pts([[i, 0, 0], [i, 10, 0]])} stroke="#eef0f3" />`);
    for (let j = 1; j < 10; j++) elems.push(html`<polyline key=${"gy" + j} points=${pts([[0, j, 0], [12, j, 0]])} stroke="#eef0f3" />`);
    elems.push(html`<polygon key="murG" points=${pts([[0, 0, 0], [0, 10, 0], [0, 10, 3.2], [0, 0, 3.2]])} fill="#f1f2f5" />`);
    elems.push(html`<polygon key="murD" points=${pts([[0, 0, 0], [12, 0, 0], [12, 0, 3.2], [0, 0, 3.2]])} fill="#e9ebef" />`);
    // tableau blanc (mur gauche) + affiche du score (mur droit)
    elems.push(html`<polygon key="tab" points=${pts([[0, 1.2, 1.1], [0, 4.6, 1.1], [0, 4.6, 2.6], [0, 1.2, 2.6]])} fill="#ffffff" stroke="#d1d5db" />`);
    [[1.6, 1.9, "#60a5fa"], [2.5, 2.3, "#f472b6"], [3.4, 1.6, "#34d399"]].forEach(([y, z, c], i) =>
      elems.push(html`<polygon key=${"bar" + i} points=${pts([[0, y, 1.25], [0, y + .55, 1.25], [0, y + .55, z], [0, y, z]])} fill=${c} />`));
    elems.push(html`<polygon key="ecr" points=${pts([[3, 0, 1.2], [8, 0, 1.2], [8, 0, 2.7], [3, 0, 2.7]])} fill="#1f2937" />`);
    const [tx, ty] = iso(5.5, 0, 2.05);
    elems.push(html`<text key="ecrt" x=${tx} y=${ty} fill="#e5e7eb" fontSize="13" fontWeight="700" textAnchor="middle"
      transform=${`rotate(-30 ${tx} ${ty}) skewX(30)`} style=${{ fontFamily: "inherit" }}>SECRÉTARIAT · EMSI</text>`);
    // décor
    elems.push(boite(9.6, 6.6, 0, 1.9, 1.2, .45, GRIS, "canape"), boite(9.6, 6.6, .45, 1.9, .3, .45, GRIS, "dossier"));
    elems.push(plante(.3, .3, "pl1", true), plante(11.2, .3, "pl2", true), plante(.3, 9.2, "pl3"), plante(5.2, 5.0, "pl4"));
    // employés : tri par profondeur (x + y) pour un affichage correct
    const items = agents.map((a) => ({ a, z: a.x + a.y }));
    items.sort((p, q) => p.z - q.z).forEach(({ a }) => {
      const e = etats[a.id] || "repos";
      if (a.debout) elems.push(employe(a, e, choisi === a.id, onChoisir));
      else { elems.push(employe(a, e, choisi === a.id, onChoisir)); elems.push(poste(a, e)); }
    });
    const pourcent = ([x, y]) => ({ left: (x / W * 100) + "%", top: (y / H * 100) + "%" });
    return html`<div className="scene-cadre" style=${{ position: "relative", width: "100%", maxWidth: "1100px", aspectRatio: "1000 / 640", margin: "0 auto" }}>
      <svg viewBox=${`0 0 ${W} ${H}`}>${elems}</svg>
      ${agents.map((a) => {
        const p = iso(a.x + .45, a.y - .35, 0);
        const s = scores[a.id];
        return html`<div key=${"t" + a.id} className=${"etiquette" + (choisi === a.id ? " choisi" : "")} style=${{ ...pourcent([p[0], p[1] + 18]) }}
          onClick=${() => onChoisir(a.id)}>
          <span className="point" style=${{ background: a.couleur }}></span>${a.prenom}<span className="score">· ${a.role}${s ? ` · ${s}` : ""}</span></div>`;
      })}
      ${agents.filter((a) => bulles[a.id]).map((a) => {
        const p = iso(a.x + .45, a.y - .35, 0);
        const mini = bulles[a.id] && bulles[a.id].props && bulles[a.id].props.className === "mini";
        return html`<div key=${"b" + a.id} className=${"bulle" + (mini ? " compacte" : "")} style=${pourcent([p[0], p[1] - (mini ? 62 : 70)])}>${bulles[a.id]}</div>`;
      })}
    </div>`;
  }
  window.SceneBureau = SceneBureau;
  const st = document.createElement("style");
  st.textContent = `.bob{animation:bob 1s ease-in-out infinite}@keyframes bob{50%{transform:translateY(-2px)}}
  .clignote{animation:clig 1.2s ease-in-out infinite}@keyframes clig{50%{opacity:.55}}
  .scene-cadre svg{position:absolute;inset:0;width:100%;height:100%}`;
  document.head.appendChild(st);
})();
