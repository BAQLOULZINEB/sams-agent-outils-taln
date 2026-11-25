/* Bureau 3D (three.js) : figurines « argile » des agents, mobilier blanc, plateforme isométrique, ombres douces.
   Expose window.creerBureau3D(conteneur, options) -> { maj(etats, choisi), detruire() }.
   Les étiquettes et bulles HTML portant data-ancre="id:tete|pied" sont repositionnées à chaque image. */
import * as THREE from "three";
import { RoundedBoxGeometry } from "three/addons/geometries/RoundedBoxGeometry.js";
import { RoomEnvironment } from "three/addons/environments/RoomEnvironment.js";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";

const mat = (c, o = {}) => new THREE.MeshStandardMaterial({ color: c, roughness: .55, metalness: 0, ...o });
const BLANC = () => new THREE.MeshPhysicalMaterial({ color: "#fbfbfc", roughness: .35, clearcoat: .6, clearcoatRoughness: .3 });
const ombre = (o) => { o.traverse((m) => { if (m.isMesh) { m.castShadow = true; m.receiveShadow = true; } }); return o; };
const rbox = (w, h, d, m, r = .04) => new THREE.Mesh(new RoundedBoxGeometry(w, h, d, 4, Math.min(r, w / 2, h / 2, d / 2)), m);
const sphere = (r, m, ws = 32) => new THREE.Mesh(new THREE.SphereGeometry(r, ws, ws * .75), m);
const capsule = (r, l, m) => new THREE.Mesh(new THREE.CapsuleGeometry(r, l, 8, 16), m);
const cyl = (rt, rb, h, m) => new THREE.Mesh(new THREE.CylinderGeometry(rt, rb, h, 32), m);

/* ---------- mobilier ---------- */
function chaise() {
  const g = new THREE.Group(), b = BLANC();
  const assise = rbox(.56, .1, .54, b, .05); assise.position.y = .52;
  const dos = rbox(.56, .52, .1, b, .05); dos.position.set(0, .84, -.24); dos.rotation.x = -.08;
  const pied = cyl(.04, .04, .4, mat("#d9dce2")); pied.position.y = .28;
  const base = cyl(.24, .26, .05, mat("#e3e5ea")); base.position.y = .05;
  g.add(assise, dos, pied, base); return ombre(g);
}
function ecranTexture(couleur) {
  const c = document.createElement("canvas"); c.width = 256; c.height = 160; const x = c.getContext("2d");
  x.fillStyle = "#1f2430"; x.fillRect(0, 0, 256, 160);
  x.fillStyle = couleur; x.fillRect(14, 14, 120, 12);
  x.fillStyle = "rgba(255,255,255,.55)"; [40, 58, 76].forEach((y, i) => x.fillRect(14, y, 180 - i * 40, 7));
  x.fillStyle = couleur; [[150, 90, 16, 50], [174, 70, 16, 70], [198, 100, 16, 40], [222, 60, 16, 80]].forEach(([a, y, w, h]) => { x.globalAlpha = .85; x.fillRect(a, y, w, h); });
  x.globalAlpha = 1; x.fillStyle = "rgba(255,255,255,.25)"; x.fillRect(14, 104, 110, 40);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; return t;
}
function bureau() {                                  // plateau + panneaux + écran + clavier ; l'écran fait face à -z (vers la personne)
  const g = new THREE.Group(), b = BLANC();
  const plateau = rbox(1.5, .07, .78, b, .03); plateau.position.y = .8;
  const p1 = rbox(.06, .78, .72, b, .02); p1.position.set(-.7, .4, 0);
  const p2 = p1.clone(); p2.position.x = .7;
  const fond = rbox(1.36, .45, .04, b, .02); fond.position.set(0, .56, .34);
  const pied = cyl(.03, .05, .2, mat("#cfd3da")); pied.position.set(0, .92, .12);
  const moniteur = rbox(.82, .5, .05, mat("#2a2f3a", { roughness: .4 }), .03); moniteur.position.set(0, 1.25, .12);
  const ecran = new THREE.Mesh(new THREE.PlaneGeometry(.74, .42), new THREE.MeshBasicMaterial({ map: ecranTexture("#94a3b8"), toneMapped: false }));
  ecran.position.set(0, 1.25, .092); ecran.rotation.y = Math.PI;
  const clavier = rbox(.5, .025, .16, mat("#eceef2"), .01); clavier.position.set(-.05, .845, -.12);
  const souris = sphere(.035, mat("#eceef2")); souris.scale.set(1, .5, 1.4); souris.position.set(.32, .845, -.12);
  const tasse = cyl(.045, .04, .09, mat("#fca5a5")); tasse.position.set(-.55, .88, .05);
  g.add(plateau, p1, p2, fond, pied, moniteur, ecran, clavier, souris, tasse); ombre(g);
  ecran.castShadow = false; g.userData.ecran = ecran; return g;
}
function plante(h = 1) {
  const g = new THREE.Group();
  const pot = cyl(.26, .2, .42, BLANC()); pot.position.y = .21;
  const terre = cyl(.24, .24, .02, mat("#6b4f3a")); terre.position.y = .42;
  g.add(pot, terre);
  const verts = ["#4ade80", "#22c55e", "#16a34a", "#86efac"];
  for (let i = 0; i < 9; i++) {
    const f = sphere(.16 + Math.random() * .08, mat(verts[i % 4], { roughness: .7 }), 16);
    const a = i * 2.4, r = .1 + (i % 3) * .07;
    f.scale.set(.7, 1.5, .5); f.position.set(Math.cos(a) * r, .7 + (i % 4) * .16 * h + .1, Math.sin(a) * r);
    f.rotation.set(Math.sin(a) * .5, a, Math.cos(a) * .5); g.add(f);
  }
  return ombre(g);
}
function tableau() {                                  // tableau blanc sur pied avec graphique
  const g = new THREE.Group();
  const c = document.createElement("canvas"); c.width = 320; c.height = 220; const x = c.getContext("2d");
  x.fillStyle = "#fff"; x.fillRect(0, 0, 320, 220); x.strokeStyle = "#e5e7eb"; for (let i = 1; i < 6; i++) { x.beginPath(); x.moveTo(20, i * 36); x.lineTo(300, i * 36); x.stroke(); }
  [["#60a5fa", 120], ["#f472b6", 160], ["#34d399", 90], ["#fbbf24", 140], ["#a78bfa", 110]].forEach(([col, hh], i) => { x.fillStyle = col; x.fillRect(40 + i * 52, 200 - hh, 30, hh); });
  x.strokeStyle = "#1f2937"; x.lineWidth = 3; x.beginPath(); x.moveTo(30, 150); x.quadraticCurveTo(160, 40, 300, 70); x.stroke();
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace;
  const cadre = rbox(1.6, 1.1, .06, BLANC(), .03); cadre.position.y = 1.45;
  const face = new THREE.Mesh(new THREE.PlaneGeometry(1.48, .98), new THREE.MeshBasicMaterial({ map: t, toneMapped: false })); face.position.set(0, 1.45, .032);
  const m1 = cyl(.025, .025, 1.2, mat("#cfd3da")); m1.position.set(-.55, .6, 0); const m2 = m1.clone(); m2.position.x = .55;
  const b1 = rbox(.5, .03, .06, mat("#cfd3da")); b1.position.set(-.55, .02, 0); const b2 = b1.clone(); b2.position.x = .55; b1.rotation.y = b2.rotation.y = Math.PI / 2;
  g.add(cadre, face, m1, m2, b1, b2); return ombre(g);
}
function tableRonde() {
  const g = new THREE.Group(), b = BLANC();
  const top = cyl(.75, .75, .07, b); top.position.y = .74;
  const pied = cyl(.08, .1, .7, mat("#e3e5ea")); pied.position.y = .37;
  const base = cyl(.35, .38, .04, b); base.position.y = .02;
  const portable = rbox(.4, .02, .28, mat("#d1d5db")); portable.position.set(.1, .79, .05);
  const ecr = rbox(.4, .26, .015, mat("#2a2f3a")); ecr.position.set(.1, .92, -.08); ecr.rotation.x = -.25;
  g.add(top, pied, base, portable, ecr); return ombre(g);
}
function canape() {
  const g = new THREE.Group(), b = BLANC();
  const assise = rbox(2.2, .36, .9, b, .12); assise.position.y = .26;
  const dos = rbox(2.2, .5, .22, b, .1); dos.position.set(0, .62, -.34);
  const a1 = rbox(.22, .5, .9, b, .1); a1.position.set(-1.0, .48, 0); const a2 = a1.clone(); a2.position.x = 1.0;
  const coussin = rbox(.45, .35, .12, mat("#fde2e4"), .06); coussin.position.set(-.6, .6, -.18); coussin.rotation.z = .15;
  g.add(assise, dos, a1, a2, coussin); return ombre(g);
}

/* ---------- figurines ---------- */
function figurine(a) {
  const g = new THREE.Group(), assis = !a.debout;
  const peau = mat(a.peau, { roughness: .6 }), cheveux = mat(a.cheveux, { roughness: .72 }), haut = mat(a.haut), bas = mat(a.bas || "#475569");
  const yH = assis ? .62 : .78;                           // hauteur des hanches
  const corps = new THREE.Group(); corps.position.y = yH; g.add(corps);
  const torse = capsule(.23, .26, haut); torse.position.y = .32; torse.scale.set(1.05, 1, .9); corps.add(torse);
  const col = cyl(.07, .07, .08, peau); col.position.y = .58; corps.add(col);
  // tête
  const tete = new THREE.Group(); tete.position.y = .94; tete.scale.setScalar(1.28); corps.add(tete);   // grosse tête « chibi »
  const crane = sphere(.34, peau); tete.add(crane);
  const oeil = mat("#1f2937", { roughness: .2 });
  [-.11, .11].forEach((x) => { const o = sphere(.038, oeil, 16); o.scale.set(1, 1.25, .6); o.position.set(x, .0, .31); tete.add(o);
    const reflet = sphere(.012, mat("#ffffff"), 8); reflet.position.set(x + .012, .02, .335); tete.add(reflet);
    const joue = sphere(.055, mat("#fb7185", { transparent: true, opacity: .45 }), 16); joue.scale.set(1, .6, .3); joue.position.set(x * 1.6, -.08, .285); tete.add(joue); });
  const bouche = new THREE.Mesh(new THREE.TorusGeometry(.035, .009, 8, 16, Math.PI), mat("#be185d")); bouche.position.set(0, -.1, .325); bouche.rotation.z = Math.PI; tete.add(bouche);
  // cheveux : calotte inclinée vers l'arrière (le visage reste visible) + mèche + style
  const volume = sphere(.375, cheveux); volume.scale.set(1.06, 1.02, 1.0); volume.position.set(0, .05, -.075); tete.add(volume);   // masse arrière
  const calotte = new THREE.Mesh(new THREE.SphereGeometry(.372, 40, 30, 0, Math.PI * 2, 0, Math.PI * .5), cheveux);
  calotte.rotation.x = -.42; calotte.position.set(0, .03, -.01); tete.add(calotte);
  [[-1, .14], [1, .14]].forEach(([s, r]) => {                 // mèches de côté (encadrent le visage)
    if (a.style === "court") return;
    const m = sphere(r, cheveux); m.scale.set(.62, 1.25, .85); m.position.set(s * .3, -.04, .06); tete.add(m); });
  [[-.13, .26, .27, .3], [.08, .28, .28, -.35], [.24, .2, .22, -.6]].forEach(([x, y, z, rz]) => {   // frange en 3 mèches arrondies
    const f = sphere(.13, cheveux); f.scale.set(1.25, .6, .75); f.position.set(x, y, z); f.rotation.z = rz; tete.add(f); });
  if (a.style === "chignon") { const c = sphere(.15, cheveux); c.position.set(0, .36, -.08); tete.add(c); }
  if (a.style === "long") { const l = capsule(.27, .35, cheveux); l.scale.set(1.15, 1, .55); l.position.set(0, -.25, -.16); tete.add(l); }
  if (a.style === "carre") [-1, 1].forEach((s) => { const c = sphere(.17, cheveux); c.scale.set(.6, 1.2, .9); c.position.set(s * .27, -.12, -.02); tete.add(c); });
  if (a.style === "couettes") [-1, 1].forEach((s) => { const c = sphere(.13, cheveux); c.position.set(s * .36, .12, -.1); tete.add(c); });
  if (a.style === "queue") { const q = capsule(.1, .3, cheveux); q.position.set(0, -.05, -.38); q.rotation.x = .5; tete.add(q); }
  if (a.casquette) {                                      // casquette : dôme + visière + petit écusson
    const mc = mat(a.casquette, { roughness: .6 });
    const dome = new THREE.Mesh(new THREE.SphereGeometry(.385, 40, 24, 0, Math.PI * 2, 0, Math.PI * .5), mc); dome.position.y = .1; dome.rotation.x = -.18; tete.add(dome);
    const visiere = cyl(.24, .24, .03, mc); visiere.scale.set(1, 1, .65); visiere.position.set(0, .12, .33); visiere.rotation.x = .12; tete.add(visiere);
    const ecusson = sphere(.05, mat("#fbbf24", { metalness: .4, roughness: .3 }), 16); ecusson.scale.z = .4; ecusson.position.set(0, .3, .31); tete.add(ecusson);
  }
  // bras (pivot à l'épaule, pour animer la frappe au clavier)
  const bras = [-1, 1].map((s) => {
    const pivot = new THREE.Group(); pivot.position.set(s * .25, .46, 0); corps.add(pivot);
    const b = capsule(.07, .26, haut); b.position.y = -.17; pivot.add(b);
    const main = sphere(.075, peau, 16); main.position.y = -.36; pivot.add(main);
    pivot.rotation.x = assis ? -1.15 : 0; pivot.rotation.z = s * (assis ? -.15 : .12); return pivot;
  });
  // jambes
  [-1, 1].forEach((s) => {
    if (assis) {
      const cuisse = capsule(.09, .3, bas); cuisse.rotation.x = Math.PI / 2; cuisse.position.set(s * .11, yH - .02, .2); g.add(cuisse);
      const tibia = capsule(.08, .3, bas); tibia.position.set(s * .11, .3, .42); g.add(tibia);
      const pied = sphere(.09, mat("#f8fafc"), 16); pied.scale.set(1, .6, 1.5); pied.position.set(s * .11, .06, .48); g.add(pied);
    } else {
      const jambe = capsule(.09, .55, bas); jambe.position.set(s * .11, .38, 0); g.add(jambe);
      const pied = sphere(.09, mat("#f8fafc"), 16); pied.scale.set(1, .6, 1.5); pied.position.set(s * .11, .06, .05); g.add(pied);
    }
  });
  if (a.accessoire === "bloc") { const bl = rbox(.26, .34, .03, mat("#fde68a")); bl.position.set(.18, .3, .25); bl.rotation.x = -.3; corps.add(bl); }
  if (a.accessoire === "bouclier") { const bo = cyl(.16, .16, .03, mat("#22c55e")); bo.rotation.x = Math.PI / 2; bo.position.set(0, .32, .2); corps.add(bo); }
  ombre(g);
  g.userData = { corps, tete, bras, assis, phase: Math.random() * 6 };
  return g;
}

/* ---------- scène ---------- */
window.creerBureau3D = function (conteneur, { agents, onChoisir }) {
  const W = () => conteneur.clientWidth, H = () => conteneur.clientHeight;
  const rendu = new THREE.WebGLRenderer({ antialias: true, alpha: true });
  rendu.setPixelRatio(Math.min(2, devicePixelRatio)); rendu.setSize(W(), H());
  rendu.shadowMap.enabled = true; rendu.shadowMap.type = THREE.PCFSoftShadowMap;
  rendu.toneMapping = THREE.ACESFilmicToneMapping; rendu.toneMappingExposure = 1.05; rendu.outputColorSpace = THREE.SRGBColorSpace;
  rendu.domElement.style.cssText = "position:absolute;inset:0;width:100%;height:100%;outline:none";
  conteneur.prepend(rendu.domElement);
  const scene = new THREE.Scene();
  scene.environment = new THREE.PMREMGenerator(rendu).fromScene(new RoomEnvironment(), .04).texture;
  const taille = 7.4;
  const cam = new THREE.OrthographicCamera(-1, 1, 1, -1, -100, 200);
  cam.position.set(14, 12.5, 14); cam.lookAt(0, .55, .5);
  const cadrer = () => { const r = W() / H(); const t = taille / (r < 1.45 ? r / 1.45 : 1);
    cam.left = -t * r / 2; cam.right = t * r / 2; cam.top = t / 2; cam.bottom = -t / 2; cam.updateProjectionMatrix(); rendu.setSize(W(), H()); };
  cadrer();
  const ctrl = new OrbitControls(cam, rendu.domElement); ctrl.target.set(0, .55, .5); ctrl.enableDamping = true;
  ctrl.minPolarAngle = .6; ctrl.maxPolarAngle = 1.15; ctrl.minZoom = .7; ctrl.maxZoom = 2.2; ctrl.enablePan = false; ctrl.update();
  // lumières douces
  scene.add(new THREE.HemisphereLight("#ffffff", "#dfe3ea", .9));
  const soleil = new THREE.DirectionalLight("#ffffff", 1.6); soleil.position.set(6, 12, 8); soleil.castShadow = true;
  soleil.shadow.mapSize.set(2048, 2048); soleil.shadow.radius = 6; soleil.shadow.bias = -.0004;
  Object.assign(soleil.shadow.camera, { left: -10, right: 10, top: 10, bottom: -10, near: 1, far: 40 }); scene.add(soleil);
  // plateforme blanche arrondie (comme une maquette)
  const socle = rbox(11.4, .5, 9, new THREE.MeshPhysicalMaterial({ color: "#ffffff", roughness: .5, clearcoat: .3 }), .35); socle.position.y = -.25; socle.receiveShadow = true; scene.add(socle);
  const sol = new THREE.Mesh(new THREE.PlaneGeometry(10.9, 8.5), mat("#f3f4f7", { roughness: .8 })); sol.rotation.x = -Math.PI / 2; sol.position.y = .002; sol.receiveShadow = true; scene.add(sol);
  const tapis = new THREE.Mesh(new THREE.CircleGeometry(1.6, 48), mat("#eef1f6", { roughness: .9 })); tapis.rotation.x = -Math.PI / 2; tapis.position.set(-3.1, .006, 2.3); tapis.receiveShadow = true; scene.add(tapis);
  // décor
  const placer = (o, x, z, ry = 0) => { o.position.set(x, 0, z); o.rotation.y = ry; scene.add(o); return o; };
  placer(tableau(), -4.5, -1.7, .9);
  placer(tableRonde(), -3.1, 2.3);
  [[-3.1, 3.35, Math.PI], [-4.15, 2.3, -Math.PI / 2], [-2.05, 2.3, Math.PI / 2]].forEach(([x, z, r]) => placer(chaise(), x, z, r));
  placer(canape(), 2.4, 3.4, Math.PI);
  [[-5.1, -3.9, 1.2], [5.1, -3.9, 1.3], [-5.1, 3.9, .9], [0.7, 3.6, .8], [5.1, .9, 1]].forEach(([x, z, h]) => placer(plante(h), x, z));
  const cloison = rbox(3.6, .5, .06, BLANC(), .03); cloison.position.set(0, 1.07, .12); ombre(cloison); scene.add(cloison);
  // agents
  const fig = {}, ecrans = {}, cliquables = [];
  agents.forEach((a) => {
    const f = figurine(a); f.position.set(a.p[0], 0, a.p[1]); f.rotation.y = a.ry || 0; f.userData.id = a.id; scene.add(f); fig[a.id] = f;
    f.traverse((m) => { if (m.isMesh) { m.userData.id = a.id; cliquables.push(m); } });
    if (!a.debout) {
      const c = chaise(); c.position.copy(f.position); c.rotation.y = f.rotation.y; scene.add(c);
      const d = bureau(); const dir = new THREE.Vector3(0, 0, .78).applyAxisAngle(new THREE.Vector3(0, 1, 0), f.rotation.y);
      d.position.copy(f.position).add(dir); d.rotation.y = f.rotation.y; scene.add(d); ecrans[a.id] = d.userData.ecran;
    }
  });
  // clic sur un employé
  const ray = new THREE.Raycaster(), souris = new THREE.Vector2();
  rendu.domElement.addEventListener("click", (e) => {
    const r = rendu.domElement.getBoundingClientRect(); souris.set(((e.clientX - r.left) / r.width) * 2 - 1, -((e.clientY - r.top) / r.height) * 2 + 1);
    ray.setFromCamera(souris, cam); const h = ray.intersectObjects(cliquables, false)[0]; if (h) onChoisir(h.object.userData.id);
  });
  rendu.domElement.style.cursor = "grab";
  // état reçu de React
  let etats = {}, choisi = null;
  const anneau = new THREE.Mesh(new THREE.RingGeometry(.55, .63, 48), new THREE.MeshBasicMaterial({ color: "#14171f", transparent: true, opacity: .55 }));
  anneau.rotation.x = -Math.PI / 2; anneau.position.y = .01; scene.add(anneau);
  const couleurs = { repos: "#94a3b8", travail: "#3b82f6", ok: "#22c55e", ko: "#ef4444" }, texCache = {};
  const tex = (c) => texCache[c] || (texCache[c] = ecranTexture(c));
  // ancrage des étiquettes HTML sur les têtes / pieds
  const v = new THREE.Vector3();
  const placerHTML = () => {
    conteneur.querySelectorAll("[data-ancre]").forEach((el) => {
      const [id, ou] = el.dataset.ancre.split(":"); const f = fig[id]; if (!f) return;
      v.copy(f.position); v.y += ou === "tete" ? (f.userData.assis ? 2.0 : 2.25) : .12; v.project(cam);
      el.style.left = ((v.x + 1) / 2 * W()) + "px"; el.style.top = ((1 - v.y) / 2 * H()) + "px";
    });
  };
  const horloge = new THREE.Clock(); let anim;
  const boucle = () => {
    anim = requestAnimationFrame(boucle); const t = horloge.getElapsedTime();
    Object.entries(fig).forEach(([id, f]) => {
      const u = f.userData, e = etats[id] || "repos", ph = t + u.phase;
      u.corps.position.y = (u.assis ? .62 : .78) + Math.sin(ph * 1.6) * .008 + (e === "ok" ? Math.max(0, Math.sin(ph * 9)) * .06 : 0);
      u.tete.rotation.y = e === "ko" ? Math.sin(ph * 10) * .35 : Math.sin(ph * .5) * .12;
      u.tete.rotation.z = Math.sin(ph * .7) * .04;
      u.bras.forEach((b, i) => {
        if (u.assis) b.rotation.x = -1.15 + (e === "travail" || e === "ok" || e === "ko" ? Math.sin(ph * 16 + i * 3) * .12 : Math.sin(ph * 1.2 + i) * .03);
        else b.rotation.x = e === "ok" ? -2.6 + Math.sin(ph * 8) * .2 : Math.sin(ph * 1.1 + i * 3) * .08;
      });
      const ec = ecrans[id]; if (ec) { const c = couleurs[e]; if (ec.userData.c !== c) { ec.material.map = tex(c); ec.material.needsUpdate = true; ec.userData.c = c; } }
    });
    if (choisi && fig[choisi]) { anneau.visible = true; anneau.position.x = fig[choisi].position.x; anneau.position.z = fig[choisi].position.z; anneau.scale.setScalar(1 + Math.sin(t * 3) * .05); }
    else anneau.visible = false;
    ctrl.update(); rendu.render(scene, cam); placerHTML();
  };
  boucle();
  window.__bureau3d = { cam, ctrl };            // accès de débogage (zoom depuis la console)
  const ro = new ResizeObserver(cadrer); ro.observe(conteneur);
  return {
    maj(e, c) { etats = e || {}; choisi = c; },
    recentrer() { cam.position.set(14, 12.5, 14); cam.zoom = 1; ctrl.target.set(0, .55, .5); cam.updateProjectionMatrix(); ctrl.update(); },
    detruire() { cancelAnimationFrame(anim); ro.disconnect(); ctrl.dispose(); rendu.dispose(); rendu.domElement.remove(); },
  };
};
window.dispatchEvent(new Event("bureau3d-pret"));
