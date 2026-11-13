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

Scarica l'archivio per il tuo sistema dalla [pagina delle release](https://github.com/perni24/planner/releases).
Estrailo e conserva l'intera cartella: i dati sono salvati in `data/` accanto
all'eseguibile.

- **Windows**: estrai `PlannerApp-windows.zip` e avvia `PlannerApp.exe`. Serve
  WebView2 Runtime, preinstallato in Windows 11. Se manca, vedi
  [Risoluzione dei problemi](doc/TROUBLESHOOTING.md). Al primo avvio puo comparire
  SmartScreen: "Ulteriori informazioni" -> "Esegui comunque".
- **Linux x86-64** (dalla `0.2.0`): estrai `PlannerApp-linux.tar.gz` con
  `tar -xzf PlannerApp-linux.tar.gz`, poi avvia `./PlannerApp/PlannerApp` dal
  terminale. Serve una sessione desktop e glibc 2.34 o successiva.

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
