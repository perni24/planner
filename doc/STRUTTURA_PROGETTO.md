# Struttura del Progetto

Questo documento riassume le cartelle principali del progetto e il loro ruolo.
Elenca i file chiave, non tutti i file: per i dettagli fa fede il codice.

## Root

- `backend/`: backend Python, API, server MCP, database SQLite, build portable.
- `frontend/`: applicazione React/Vite.
- `doc/`: documentazione tecnica e note di progetto.
- `.github/workflows/release-build.yml`: build Windows, Linux e macOS e creazione della GitHub Release quando viene pubblicato un tag `v*`.
- `AGENTS.md`: istruzioni per gli agenti AI che lavorano sul progetto.
- `THIRD_PARTY_NOTICES.md`: licenze di terze parti (icone). Viene copiato nella build portable.
- `LICENSE`: licenza GNU GPL v3.

## Documentazione

- `GUIDA_SVILUPPO.md`: avvio sviluppo, build portable e release da tag.
- `STRUTTURA_PROGETTO.md`: questo documento.
- `ARCHITETTURA_PORTABLE.md`: comportamento dell'app PyInstaller.
- `DATABASE.md`: schema SQLite, relazioni, trigger e repository.
- `API_BACKEND.md`: endpoint REST, eventi SSE e tool MCP.
- `I18N.md`: gestione lingue JSON.
- `TROUBLESHOOTING.md`: problemi comuni e soluzioni.
- `SVILUPPI_FUTURI.md`: idee non ancora pianificate.
- `TODO.md`: attivita aperte e problemi noti.

## Tecnologie principali

- Frontend: React 19, Vite 8, Tailwind CSS 4 e React Router 7.
- Backend: Python, Starlette, Uvicorn, SQLite e SDK Python `mcp`.
- Qualita: ESLint per il frontend e Ruff per il backend.
- Distribuzione: PyInstaller e GitHub Actions.

## Backend

- `main.py`: entry point. Crea l'app Starlette, monta API e server MCP, serve il frontend buildato, apre il browser e avvia Uvicorn.
- `config.py`: ambiente (sviluppo/produzione), percorsi, host, porta, versione app.
- `schema.sql`: schema SQLite, trigger, vista `v_projects_status` e dati iniziali.
- `build_portable.py`: build del frontend e della cartella portable con PyInstaller.
- `requirements.txt`: dipendenze Python.
- `db/db.py`: connessione SQLite e creazione del DB al primo avvio.
- `db/repositories/`: un modulo per entita (`area_repo`, `project_repo`, `task_repo`, `setting_repo`) piu `mcp_repo` con le query usate dai tool MCP (letture e operazioni bulk). Contengono solo SQL e conversione dati.
- `routes/`: un modulo per gruppo di endpoint. `api.py` li monta sia alla radice sia sotto `/api`.
- `services/`:
  - `mcp_service.py`: validazione e logica delle operazioni MCP, pubblicazione degli eventi;
  - `event_service.py`: code in memoria per gli eventi SSE;
  - `app_lifecycle.py`: heartbeat e spegnimento automatico in produzione;
  - `locale_service.py`: lettura dei file lingua;
  - `update_service.py`: controllo dell'ultima release su GitHub.
- `integration/mcp/`: server MCP (`server.py`), registrazione dei tool (`mcp_tools.py`) e modelli Pydantic dei parametri (`models.py`).
- `validators/request_validator.py`: validazione di id e testi, usata da route e service.
- `middleware/origin_guard.py`: blocca le richieste di modifica inviate da pagine di altri siti (CSRF).
- `locales/`: file lingua JSON di default.
- `test/*.http`: richieste HTTP manuali per provare le API. Non esistono test automatici.

## Frontend (`frontend/src/`)

- `main.jsx`: monta React dentro `AppProviders`.
- `App.jsx`: router (`/`, `/tasks/:projectId`, `/settings`, `/calendar`).
- `api.ts` e `apiCore.ts`: tutte le chiamate HTTP al backend.
- `index.css`: Tailwind e variabili CSS dei temi.
- `pages/`: `Project.jsx` (progetti dell'area corrente), `Tasks.jsx` (task e subtask di un progetto), `Setting.jsx` (tema, lingua, backup, MCP, versione), `Calendar.jsx` (segnaposto, non implementato).
- `components/`: layout (`Dashboard`, `Header`, `SideBar`, `AreaSwitcher`), card, modali di creazione/modifica/eliminazione, `ConfirmModal`, `Toast`, `McpSettings`.
- `context/`: provider globali composti in `AppProviders.jsx`, che gestisce anche heartbeat e controllo aggiornamenti. `DataSyncContext.jsx` riceve gli eventi SSE da `/api/events`. Per ogni context esistono un file `*ContextValue.js` e un hook `use*.js`.
- `types/`: tipi delle risposte API (non verificati: manca la configurazione TypeScript).
- `assets/icons/`: icone SVG (licenza in `THIRD_PARTY_NOTICES.md`).

## Cartelle generate (non tracciate da Git)

- `frontend/node_modules/` e `frontend/dist/`: dipendenze npm e build frontend.
- `backend/.venv/`: ambiente virtuale Python.
- `backend/db/planner.db`: DB di sviluppo.
- `backend/build/` e `backend/dist/`: output PyInstaller.
