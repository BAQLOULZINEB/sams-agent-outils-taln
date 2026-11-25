/* Moteur Python de SAMS dans le navigateur : Pyodide exécute le vrai code du notebook (outils, évaluateur, agents). */
importScripts("https://cdn.jsdelivr.net/pyodide/v0.26.4/full/pyodide.js");

const pret = (async () => {
  const py = await loadPyodide();
  await py.loadPackage(["numpy", "pandas", "scikit-learn"]);
  const [code, moteur] = await Promise.all(["py/sams_code.py", "py/moteur.py"].map((u) => fetch(u).then((r) => r.text())));
  py.runPython(code);     // base fictive, outils, scénarios, évaluateur, détecteur d'intention, baseline, agent classique
  py.runPython(moteur);   // routes : chat, outil, évaluer, labo
  return py.globals.get("traiter");
})();

pret.then(() => self.postMessage({ pret: true })).catch((e) => self.postMessage({ echec: String(e) }));

self.onmessage = async (e) => {
  const { id, route, corps } = e.data;
  try {
    const traiter = await pret;
    self.postMessage({ id, r: traiter(route, JSON.stringify(corps || {})) });
  } catch (err) {
    self.postMessage({ id, r: JSON.stringify({ erreur: String(err) }) });
  }
};
