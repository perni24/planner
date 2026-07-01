# Struttura del Progetto

Questo documento riassume le cartelle principali del progetto e il loro contenuto.

## Root

- `backend/`: backend Python, API, database SQLite, build portable.
- `frontend/`: applicazione React/Vite.
- `doc/`: documentazione tecnica e note di progetto.
- `.github/workflows/`: workflow GitHub Actions.
- `.gitignore`: file e cartelle esclusi da Git.

## Documentazione

- `GUIDA_SVILUPPO.md`: avvio sviluppo, build portable e release da tag.
- `STRUTTURA_PROGETTO.md`: panoramica delle cartelle.
- `tecnologie.md`: tecnologie principali.
- `ARCHITETTURA_PORTABLE.md`: comportamento dell'app PyInstaller.
- `DATABASE.md`: schema SQLite, relazioni e repository.
- `API_BACKEND.md`: endpoint backend principali.
- `I18N.md`: gestione lingue JSON.
- `TROUBLESHOOTING.md`: problemi comuni e soluzioni.
- `to do.md`: attivita aperte.
- `diagramma_flusso.canvas`: diagramma visuale.

## GitHub Actions

- `.github/workflows/release-build.yml`: build release Windows, Linux e macOS quando viene pubblicato un tag `v*`.

## Backend

- `main.py`: entry point backend, avvio Starlette/Uvicorn, serving frontend buildato e apertura browser in produzione.
- `config.py`: configurazione centralizzata di ambiente, path, DB, locales e frontend dist.
- `schema.sql`: schema SQLite, viste e dati iniziali.
- `build_portable.py`: script cross-platform per creare la cartella portable con PyInstaller.
- `requirements.txt`: dipendenze Python.

## Backend - database

- `db/db.py`: connessione SQLite e inizializzazione del DB.
- `db/repositories/area_repo.py`: query aree.
- `db/repositories/project_repo.py`: query progetti.
- `db/repositories/task_repo.py`: query task.
- `db/repositories/setting_repo.py`: query impostazioni.

I repository contengono SQL e conversione dati. Non dovrebbero contenere logica HTTP o UI.

## Backend - routes

- `routes/api.py`: monta tutte le route anche sotto `/api`.
- `routes/area_routes.py`: endpoint aree.
- `routes/project_routes.py`: endpoint progetti.
- `routes/task_routes.py`: endpoint task.
- `routes/setting_routes.py`: endpoint impostazioni.
- `routes/locale_routes.py`: endpoint lingue.
- `routes/app_routes.py`: heartbeat e shutdown applicazione.

Le route leggono request/query/body, validano i dati, chiamano repository o service e restituiscono `JSONResponse`.

## Backend - services e validators

- `services/locale_service.py`: lettura lingue JSON.
- `services/app_lifecycle.py`: heartbeat e shutdown automatico in produzione.
- `validators/request_validator.py`: validazione payload riutilizzabile.

## Backend - test manuali

- `test/*.http`: richieste HTTP manuali per provare le API.

## Frontend

- `package.json`: script npm e dipendenze.
- `package-lock.json`: lockfile npm.
- `vite.config.js`: configurazione Vite e proxy `/api`.
- `eslint.config.js`: configurazione ESLint.
- `index.html`: entry HTML.

## Frontend - src

- `main.jsx`: monta React e `AppProviders`.
- `App.jsx`: router React.
- `index.css`: CSS globale, Tailwind e variabili tema.
- `apiCore.ts`: funzione base per le chiamate HTTP.
- `api.ts`: funzioni API frontend.

## Frontend - components

- `Dashboard.jsx`: layout principale con header, sidebar e outlet.
- `Header.jsx`: barra superiore.
- `SideBar.jsx`: menu laterale comprimibile.
- `AreaSwitcher.jsx`: selezione area corrente.
- `AreaModal.jsx`: creazione/modifica/eliminazione area.
- `ProjectCard.jsx`: card progetto.
- `ProjectModal.jsx`: creazione/modifica/eliminazione progetto.
- `TaskCard.jsx`: card task.
- `TaskModal.jsx`: creazione/modifica/eliminazione task.
- `ConfirmModal.jsx`: conferma eliminazioni.
- `Toast.jsx`: notifica visuale.

## Frontend - context

- `AppProviders.jsx`: compone tutti i provider globali.
- `SettingsContext.jsx`: caricamento settings iniziali.
- `LanguageContext.jsx`: lingua e dizionario JSON.
- `ThemeContext.jsx`: tema e colori custom.
- `areaContext.jsx`: aree e area corrente.
- `ToastContext.jsx`: notifiche toast.

I file `use*.js` espongono gli hook dedicati ai context.

## Frontend - pages

- `Project.jsx`: pagina progetti.
- `Tasks.jsx`: pagina task di un progetto.
- `Setting.jsx`: pagina impostazioni.
- `Calendar.jsx`: pagina calendario.

## Frontend - types

- `areas.ts`: tipi area.
- `projects.ts`: tipi progetto.
- `tasks.ts`: tipi task.
- `settings.ts`: tipi settings.
- `locales.ts`: tipi dizionario lingua.
- `apiResponses.ts`: tipi risposte API generiche.

## Cartelle generate

- `frontend/node_modules/`: dipendenze npm.
- `backend/venv/`: ambiente virtuale Python.
- `backend/db/planner.db`: DB di sviluppo generato.
- `backend/dist/`: output PyInstaller.
- `backend/build/`: cartella temporanea PyInstaller.
- `backend/__pycache__/`: cache Python.
