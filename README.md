# Planner App

Planner App e un'applicazione locale per organizzare aree di lavoro, progetti e attivita.

Il progetto e attualmente in fase beta: alcune funzionalita sono ancora in evoluzione e la struttura potrebbe cambiare nelle prossime versioni.

## Funzioni principali

- Gestione di aree di lavoro.
- Creazione, modifica ed eliminazione di progetti.
- Gestione delle task e delle subtask collegate ai progetti, con avanzamento calcolato automaticamente.
- Integrazione con client AI tramite server MCP integrato.
- Cambio lingua tramite file JSON esterni.
- Impostazioni tema e colori personalizzati.
- Database locale SQLite.
- Versione portable generabile con PyInstaller.

## Struttura tecnica

Il progetto e diviso in due parti principali:

- `backend/`: API Python con Starlette, server MCP, database SQLite e build portable.
- `frontend/`: interfaccia React con Vite.

La documentazione tecnica si trova nella cartella `doc/`. Il punto di partenza e
`doc/STRUTTURA_PROGETTO.md`.

## Avvio in sviluppo

Riepilogo rapido. I passaggi completi, compresa la creazione dell'ambiente virtuale
e le release, sono in `doc/GUIDA_SVILUPPO.md`.

Backend:

```bash
cd backend
```

Attiva l'ambiente virtuale Python (`backend/.venv`) prima di installare le dipendenze.

Windows:

```powershell
.\.venv\Scripts\Activate.ps1
```

Linux/macOS:

```bash
source .venv/bin/activate
```

Poi installa le dipendenze e avvia il backend:

```bash
pip install -r requirements.txt
python main.py
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

## Build portable

Per creare la versione portable:

```bash
cd backend
python build_portable.py
```

L'output viene generato in:

```text
backend/dist/PlannerApp
```

Con la modalita `--onedir` va distribuita tutta la cartella `PlannerApp`, non solo l'eseguibile.

## Stato del progetto

Planner App e in beta. Prima di usarla per dati importanti e consigliato fare backup del database SQLite.
