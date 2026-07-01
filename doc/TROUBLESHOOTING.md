# Troubleshooting

## L'eseguibile si apre e si chiude subito

Avvialo da terminale per leggere l'errore:

```powershell
cd backend\dist\PlannerApp
.\PlannerApp.exe
```

Se lo avvii con doppio click, la finestra puo chiudersi prima di mostrare il messaggio.

## Errore `Failed to load Python DLL`

Succede quando viene copiato solo `PlannerApp.exe` senza la cartella `_internal`.

Con PyInstaller `--onedir` devi copiare tutta la cartella:

```text
PlannerApp/
  PlannerApp.exe
  _internal/
```

## Porta 8000 gia occupata

Chiudi eventuali server gia avviati:

```text
python main.py
npm run dev
PlannerApp.exe
```

Il backend usa:

```text
http://127.0.0.1:8000
```

## `npm` non trovato durante la build

Verifica che Node.js sia installato e disponibile nel PATH:

```powershell
npm --version
```

Su Windows lo script usa `npm.cmd` automaticamente.

## PyInstaller non trovato

Installa le dipendenze backend:

```powershell
cd backend
pip install -r requirements.txt
```

Poi rilancia:

```powershell
python build_portable.py
```

## Il DB non viene creato

Controlla che l'app abbia permessi di scrittura nella cartella dove si trova l'eseguibile.

In modalita portable il DB viene creato qui:

```text
PlannerApp/data/planner.db
```

## Le lingue non cambiano

Controlla che i file lingua siano presenti in:

```text
PlannerApp/locales/
```

E che il JSON sia valido. I file JSON non supportano commenti.
