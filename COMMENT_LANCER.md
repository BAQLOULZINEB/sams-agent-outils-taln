# Comment relancer le projet (depuis VS Code)

Dossier du projet : `C:\Users\zineb\projet 5IASD\Projet10_Agent_Outils_TALN`
Python à utiliser (numpy, pandas, scikit-learn déjà installés) :
`C:\Users\zineb\AppData\Local\Python\pythoncore-3.14-64\python.exe`

## 0. Ouvrir le projet dans VS Code
```powershell
code "C:\Users\zineb\projet 5IASD\Projet10_Agent_Outils_TALN"
```
Puis : menu Terminal > Nouveau terminal. Toutes les commandes ci-dessous se tapent dans ce terminal.

## 1. La plateforme SAMS (démo visuelle)
```powershell
& "C:\Users\zineb\AppData\Local\Python\pythoncore-3.14-64\python.exe" dashboard\serveur.py
```
Ouvrir ensuite http://localhost:8765 dans le navigateur. Arrêt : Ctrl+C dans le terminal.
Sans VS Code : double-cliquer `dashboard\LANCER_SAMS.bat`.
Si le message « adresse déjà utilisée » apparaît : le serveur tourne déjà, ouvrir simplement le navigateur.

## 1 bis. La version en ligne (Vercel)
Adresse publique : **https://sams-taln.vercel.app**. Le site statique est dans `site_vercel\` (voir `site_vercel\LISEZMOI_VERCEL.md`).
Reconstruire après une modification, puis déployer :
```powershell
& "C:\Users\zineb\AppData\Local\Python\pythoncore-3.14-64\python.exe" dashboard\construire_site_vercel.py
```
```powershell
cd site_vercel
npx vercel@65.12.1 deploy --prod
```

## 2. La démonstration pas à pas (7 étapes, dans le terminal)
```powershell
& "C:\Users\zineb\AppData\Local\Python\pythoncore-3.14-64\python.exe" demo_pas_a_pas.py
```
Appuyer sur Entrée pour passer à l'étape suivante.

## 3. Recalculer le kappa de l'audit humain
```powershell
& "C:\Users\zineb\AppData\Local\Python\pythoncore-3.14-64\python.exe" audit\calculer_kappa.py
```

## 4. Recompiler le rapport et l'article (LaTeX)
```powershell
cd rapport_latex
pdflatex article_7pages.tex
pdflatex article_7pages.tex
```
Même chose avec `article_10pages.tex` (version avec page de garde) ou `main.tex` (rapport complet).
Le PDF produit porte le nom du fichier `.tex`.

## 5. Le notebook
- Notebook unique : `Projet10_Agent_Outils_TALN.ipynb` (déjà exécuté sur GPU, commenté ; c'est lui que lisent SAMS, la démo et l'audit). Ne pas le relancer sans GPU.
- Pour relancer toute l'expérience avec le LLM : il faut un GPU, donc Google Colab.
  1. Ouvrir une copie de `Projet10_Agent_Outils_TALN.ipynb` sur https://colab.research.google.com (Fichier > Importer).
  2. Exécution > Modifier le type d'exécution > GPU T4.
  3. Exécution > Tout exécuter (compter 15 à 25 min par configuration LLM, donc plusieurs heures au total ; les résultats sont gardés dans Google Drive).
- Dans VS Code (sans GPU) : ouvrir une COPIE du notebook, choisir le noyau Python ci-dessus.
  Les parties baseline, agent classique et évaluateur tournent ; les parties LLM sont sautées proprement.
- `RECALCULER = False` (étape 11) : les résultats déjà sauvegardés sont relus au lieu d'être recalculés.
