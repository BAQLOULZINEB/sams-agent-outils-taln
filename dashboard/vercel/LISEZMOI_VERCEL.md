# SAMS en ligne (Vercel)

Adresse publique : **https://sams-taln.vercel.app** (projet Vercel `sams-agent-outils-taln`).

Ce dossier est un site **statique** : aucun serveur à faire tourner.

- Données en lecture (résultats, scénarios, traces, base fictive, audit) : `data/*.json`, précalculées depuis le notebook.
- Parties en direct (atelier, labo, évaluation, bureau) : le vrai code du notebook (`py/`) s'exécute dans le
  navigateur du visiteur avec Pyodide. Premier chargement : environ 20 secondes.
- Agents LLM (Qwen) : relus depuis l'exécution GPU sur Colab, comme dans la version locale.
- Audit : les verdicts d'un visiteur sont gardés dans son propre navigateur.

## Reconstruire le site après une modification
Depuis le dossier `dashboard` :
```powershell
& "C:\Users\zineb\AppData\Local\Python\pythoncore-3.14-64\python.exe" construire_site_vercel.py
```

## Déployer
Depuis ce dossier (`site_vercel`) :
```powershell
npx vercel@65.12.1 login
```
```powershell
npx vercel@65.12.1 deploy --prod
```
