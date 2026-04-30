# Struttura del progetto

Questo documento riassume le cartelle principali del progetto e il loro contenuto.

## Root

La root contiene le cartelle principali dell'applicazione e i file generali del repository.

- `backend/`: codice server Python, API, database SQLite e query.
- `frontend/`: applicazione React/Vite.
- `doc/`: documentazione tecnica e note di progetto.
- `.gitignore`: file e cartelle esclusi dal versionamento Git.
- `GEMINI.md`: note operative o istruzioni specifiche del progetto.

## backend

Contiene il backend Python basato su Starlette e la gestione del database SQLite.

- `main.py`: entry point del backend. Crea l'app Starlette, inizializza il database e avvia il server.
- `schema.sql`: definizione dello schema SQLite: tabelle, foreign key, indici, viste e dati iniziali.
- `requirements.txt`: dipendenze Python del backend.

## backend/db

Contiene la configurazione e l'accesso al database.

- `db.py`: definisce il path del database, crea la connessione SQLite e inizializza il DB leggendo `schema.sql`.
- `planner.db`: file SQLite locale generato dall'applicazione. Non dovrebbe essere modificato manualmente durante lo sviluppo ordinario.

## backend/db/repositories

Contiene le funzioni che interrogano o modificano il database.

- `project_repo.py`: query relative ai progetti e alle viste sui progetti.
- `task_repo.py`: query relative alle task.
- `setting_repo.py`: query relative alle impostazioni dell'app.

I repository dovrebbero contenere SQL e conversione dei risultati, evitando logica HTTP o logica UI.

## backend/routes

Contiene gli endpoint HTTP del backend.

- `api.py`: raccoglie e monta le route principali dell'applicazione.
- `project_routes.py`: endpoint per progetti.
- `task_routes.py`: endpoint per task.
- `setting_routes.py`: endpoint per impostazioni.

Le route ricevono la richiesta HTTP, leggono parametri/body, chiamano i repository e restituiscono `JSONResponse`.

## backend/test

Contiene file di supporto per test manuali delle API.

- `project.http`: richieste HTTP di esempio per provare gli endpoint dei progetti.

## frontend

Contiene l'applicazione React gestita da Vite.

- `package.json`: script npm e dipendenze frontend.
- `package-lock.json`: lockfile delle dipendenze.
- `vite.config.js`: configurazione Vite.
- `index.html`: HTML di ingresso dell'app React.
- `eslint.config.js`: configurazione linting.
- `README.md`: documentazione generata o specifica del frontend.

## frontend/src

Contiene il codice sorgente dell'app React.

- `main.jsx`: entry point React. Monta `App` nel DOM e applica i provider globali.
- `App.jsx`: configurazione del router React.
- `index.css`: CSS globale, import Tailwind e variabili tema.
- `api.ts`: funzioni API specifiche usate dal frontend.
- `apiCore.ts`: funzioni o configurazione base per le chiamate API.

## frontend/src/components

Contiene componenti riutilizzabili o componenti di layout.

- `Dashboard.jsx`: layout principale con `Header`, `SideBar` e `Outlet`.
- `Header.jsx`: intestazione superiore dell'app.
- `SideBar.jsx`: menu laterale di navigazione.
- `CardProgetto.jsx`: card visuale per progetto o creazione nuovo progetto.

## frontend/src/context

Contiene i React Context globali.

- `AppProviders.jsx`: compone i provider globali e avvolge l'app.
- `ThemeContext.jsx`: gestisce tema, colori custom e variabili CSS globali.

I context sono indicati per stato globale stabile, come tema, lingua o impostazioni condivise.

## frontend/src/pages

Contiene le pagine renderizzate dalle route React.

- `Project.jsx`: pagina principale dei progetti.
- `Tasks.jsx`: pagina delle task.
- `Calendar.jsx`: pagina calendario.
- `Setting.jsx`: pagina impostazioni.

Le pagine dovrebbero orchestrare dati e layout della vista, delegando blocchi ripetuti ai componenti.

## frontend/src/types

Contiene definizioni TypeScript o tipi condivisi.

- `projects.ts`: tipi relativi ai progetti.
- `test.ts`: file di test o sperimentazione sui tipi.

## Cartelle generate o da non modificare manualmente

- `frontend/node_modules/`: dipendenze npm installate.
- `backend/venv/`: ambiente virtuale Python.
- `__pycache__/`: cache Python generata automaticamente.
- `backend/db/planner.db`: database SQLite locale generato dall'app.
