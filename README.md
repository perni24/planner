# Planner App

Planner App e un'applicazione locale per organizzare aree di lavoro, progetti e
attivita. E in fase beta: prima di usarla per dati importanti scarica regolarmente un
backup dalle Impostazioni.

## Funzioni

- Aree di lavoro, progetti, task e subtask, con avanzamento calcolato automaticamente.
- Server MCP integrato per leggere e modificare i dati da un client AI.
- Lingue tramite file JSON modificabili, tema e colori personalizzati.
- Dati in un database SQLite locale, con backup scaricabile.

## Uso

Scarica lo ZIP dalla pagina delle release, estrailo e avvia `PlannerApp.exe`: va
tenuta l'intera cartella, che contiene anche i dati in `data/`. Al primo avvio
Windows puo mostrare SmartScreen: "Ulteriori informazioni" -> "Esegui comunque".

- **Windows**: serve WebView2 Runtime, preinstallato in Windows 11. Se manca, vedi
  `doc/TROUBLESHOOTING.md`.
- **Linux**: il pacchetto (circa 510 MB, glibc 2.34 o successiva) e per ora
  disponibile solo come artifact di prova del workflow.

Aggiornamenti e struttura della cartella sono descritti in
`doc/ARCHITETTURA_PORTABLE.md`.

## Sviluppo

- `backend/`: Python (Starlette, Uvicorn, SQLite, MCP) e build portable.
- `frontend/`: React con Vite e Tailwind.

Avvio rapido (dettagli in `doc/GUIDA_SVILUPPO.md`):

```bash
cd frontend && npm ci && npm run build
cd ../backend
python -m venv .venv && source .venv/bin/activate   # Windows: .\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
python main.py
```

Documentazione tecnica in `doc/` (parti da `doc/STRUTTURA_PROGETTO.md`); istruzioni
per gli agenti AI in `AGENTS.md`.

## Licenza

GNU GPL v3 (`LICENSE`). Componenti di terze parti in `THIRD_PARTY_NOTICES.md`.
