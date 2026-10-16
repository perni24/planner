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
- Qualita: ESLint e TypeScript per il frontend, Ruff per il backend.
- Distribuzione: PyInstaller e GitHub Actions.

## Backend

- `main.py`: unico entry point. `main()` prepara cartelle, lingue e database con `initialize_runtime()`, poi `start_server()` avvia Uvicorn in un thread e PyWebView nel thread principale. Attende il nostro server prima di aprire la finestra, ne richiede l'arresto alla chiusura e mantiene API REST, MCP e frontend compilato. Importare il modulo non avvia server o finestra.
- `config.py`: ambiente (sviluppo/produzione), percorsi incluso il profilo persistente WebView, host, porta, versione app, URL e renderer della finestra e timeout di avvio/arresto. Il reload di Uvicorn e disattivato.
- `schema.sql`: schema SQLite, trigger, vista `v_projects_status` e dati iniziali.
- `build_portable.py`: build del frontend e della cartella portable con PyInstaller.
- `requirements.txt`: dipendenze Python di runtime (Starlette, Uvicorn, MCP e PyWebView).
- `requirements-dev.txt`: include le dipendenze di runtime e aggiunge PyInstaller e Ruff per sviluppo e build.
- `db/db.py`: connessione SQLite, creazione del DB, migrazioni all'avvio e copie consistenti per il download backup.
- `db/migration_runner.py`: elenco ordinato delle migrazioni, versionamento con `PRAGMA user_version`, transazioni e backup automatici.
- `db/migrations/`: script SQL numerati per aggiornare i database esistenti e compatibilita con le release precedenti.
- `db/repositories/`: un modulo per entita (`area_repo`, `project_repo`, `task_repo`, `setting_repo`) piu `mcp_repo` con le query usate dai tool MCP (letture e operazioni bulk). Contengono solo SQL e conversione dati.
- `routes/`: un modulo per gruppo di endpoint. `api.py` li monta sia alla radice sia sotto `/api`.
- `services/`:
  - `mcp_service.py`: validazione e logica delle operazioni MCP, pubblicazione degli eventi;
  - `event_service.py`: code in memoria per gli eventi SSE, chiuse alla disconnessione o allo spegnimento per sbloccare le letture pendenti;
  - `app_lifecycle.py`: registrazione e invocazione della callback per lo shutdown REST, senza terminazioni forzate o monitor di presenza del frontend;
  - `operation_control.py`: stop idempotente, scadenze ereditabili e controlli cooperativi condivisi da richieste, SQLite, backup e migrazioni;
  - `desktop_error_service.py`: log desktop rotanti, messaggi localizzati senza accesso al DB e dialoghi con fallback;
  - `locale_service.py`: lettura dei file lingua;
  - `update_service.py`: controllo dell'ultima release su GitHub.
- `integration/mcp/`: server MCP (`server.py`), registrazione dei tool (`mcp_tools.py`) e modelli Pydantic dei parametri (`models.py`).
- `validators/request_validator.py`: validazione di id e testi, usata da route e service.
- `middleware/origin_guard.py`: blocca le richieste di modifica inviate da pagine di altri siti (CSRF).
- `middleware/shutdown_guard.py`: rifiuta le nuove richieste durante l'arresto e restituisce errori JSON per annullamento e timeout del database, se la risposta non e ancora iniziata.
- `locales/`: file lingua JSON di default.
- `test/*.http`: richieste HTTP manuali per provare le API.
- `test/test_migrations.py`: test automatici con `unittest`, su database temporanei, per inizializzazione, migrazioni e rollback.
- `test/test_backup.py`: test automatici del download backup, consistenza delle copie e pulizia dei temporanei, senza avviare il server.
- `test/test_repositories.py`: test automatici di letture e scritture REST/MCP, commit/rollback e chiusura delle connessioni SQLite.
- `test/test_startup.py`: test dell'inizializzazione, della finestra simulata, dei thread, dei timeout e degli errori di avvio; include prove con Uvicorn e porte locali temporanee, senza aprire finestre native.
- `test/test_events.py`: test di chiusura delle code SSE e pubblicazione concorrente allo spegnimento.
- `test/test_app_routes.py`: test di shutdown, versione e controllo aggiornamenti e rimozione del vecchio endpoint heartbeat.
- `test/test_desktop_errors.py`: test di rotazione log, errori di scrittura, dizionari e dialoghi simulati.
- `test/test_operation_control.py`: test di scadenze, cancellazione SQLite e bulk, timeout dei lock, pulizia dei backup e rollback delle migrazioni.

## Frontend (`frontend/src/`)

La configurazione `frontend/tsconfig.json` verifica i file `.ts` e `.tsx` in
`src/` in modalita strict, senza generare JavaScript. Il comando
`npm run typecheck` viene eseguito anche prima della build Vite. I file `.js` e
`.jsx` restano controllati solo da ESLint.

- `main.jsx`: monta React dentro `AppProviders`.
- `App.jsx`: router (`/`, `/tasks/:projectId`, `/settings`, `/calendar`).
- `api.ts` e `apiCore.ts`: tutte le chiamate HTTP al backend. Le funzioni usano camelCase (`getProjectsByArea`, `getTasksByProject`, `updateTaskStatus`, `getSettings`); endpoint e campi dei payload restano quelli del backend.
- `index.css`: Tailwind e variabili CSS dei temi.
- `pages/`: `Project.jsx` (progetti dell'area corrente), `Tasks.jsx` (task e subtask di un progetto), `Setting.jsx` (tema, lingua, backup, MCP, versione), `Calendar.jsx` (segnaposto, non implementato).
- `components/`: layout (`Dashboard`, `Header`, `SideBar`, `AreaSwitcher`), card, modali di creazione/modifica/eliminazione, `ConfirmModal`, `Toast`, `McpSettings`.
- `context/`: provider globali composti in `AppProviders.jsx`, che gestisce anche il controllo aggiornamenti. `DataSyncContext.jsx` riceve gli eventi SSE da `/api/events`. Per ogni context esistono un file `*ContextValue.js` e un hook `use*.js`.
- `context/ToastContext.jsx`: mostra una sola notifica alla volta; annulla il timer precedente quando arriva un nuovo messaggio, alla chiusura manuale e allo smontaggio del provider.
- `types/`: tipi delle risposte API, verificati insieme ad `api.ts` e `apiCore.ts` da TypeScript.
- `assets/icons/`: icone SVG (licenza in `THIRD_PARTY_NOTICES.md`).

## Azioni dell'interfaccia

Modali e card ricevono callback, senza chiamare direttamente le API. Mantengono
campi, validazione, conferme e blocco dei pulsanti durante l'attesa.

- `AreaProvider`: espone `createArea`, `editArea` e `removeArea`, esegue le API e ricarica le aree; mantiene l'area corrente allineata ai dati ricevuti. `AreaSwitcher` passa le callback al modale e coordina toast e navigazione.
- `Project.jsx`: crea i progetti e aggiorna l'elenco dopo il salvataggio.
- `Tasks.jsx`: gestisce creazione, modifica, eliminazione e completamento delle task, incluse le subtask, e modifica/eliminazione del progetto aperto.

`onSave` e `onDelete` restituiscono Promise: il modale resta aperto se vengono
rifiutate. Anche `onToggle` viene attesa dalla card; i toast relativi alle API
sono gestiti dal chiamante, senza duplicazioni. La navigazione e decisa dal
contenitore, non dal modale. Le letture e gli aggiornamenti SSE restano nei
context e nelle pagine che possiedono i dati.

## Cartelle generate (non tracciate da Git)

- `frontend/node_modules/` e `frontend/dist/`: dipendenze npm e build frontend.
- `backend/.venv/`: ambiente virtuale Python.
- `backend/db/planner.db`: DB di sviluppo.
- `backend/db/migration_backups/`: backup automatici prima delle migrazioni in sviluppo.
- `backend/db/logs/`: log desktop e copie ruotate in sviluppo.
- `backend/db/webview/`: profilo persistente del renderer desktop in sviluppo, separato dai dati SQLite.
- `backend/build/` e `backend/dist/`: output PyInstaller.
