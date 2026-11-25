@echo off
rem Double-cliquer ce fichier : démarre la plateforme SAMS puis ouvre le navigateur sur http://localhost:8765
cd /d "%~dp0"
set "PY=python"
if exist "%LOCALAPPDATA%\Python\pythoncore-3.14-64\python.exe" set "PY=%LOCALAPPDATA%\Python\pythoncore-3.14-64\python.exe"
start "SAMS - serveur (ne pas fermer)" "%PY%" serveur.py
echo Demarrage de SAMS (environ 15 secondes)...
timeout /t 15 /nobreak >nul
start "" http://localhost:8765
