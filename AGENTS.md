# AGENTS.md

Istruzioni per gli agenti AI che lavorano su questo repository: quello che serve
per modificare il codice senza romperlo. I dettagli sono in `doc/`.

## Il progetto in breve

Planner e un'app locale per organizzare aree, progetti, task e subtask. Gira come
cartella portable (PyInstaller) per Windows e Linux. Un backend Python serve
l'interfaccia React e le API su `127.0.0.1:8000`, salva i dati in SQLite e offre un
server MCP per i client AI. La finestra e PyWebView: WebView2 su Windows, Qt
WebEngine su Linux.

- `backend/`: Python 3.14, Starlette, Uvicorn, `sqlite3`, SDK `mcp`.
- `frontend/`: React 19, Vite 8, Tailwind CSS 4, React Router 7.
- `doc/`: documentazione in italiano, partendo da `doc/STRUTTURA_PROGETTO.md`.
- `doc/TODO.md`: attivita aperte e problemi noti. Controllalo prima di "correggere"
  un comportamento strano.

## Comandi

```bash
# backend/, con il venv in backend/.venv
python -m pip install -r requirements-dev.txt
python main.py                 # finestra e backend, senza reload
ruff check .
python -m unittest discover -s test -p test_*.py -v
python build_portable.py       # output in backend/dist/PlannerApp

# frontend/
npm ci
npm run dev                    # http://localhost:5173, proxy /api -> 127.0.0.1:8000
npm run lint
npm run typecheck
npm run build                  # necessario per vedere le modifiche in main.py
```

Per verificare una modifica: linter, test, `npm run build` se tocchi il frontend,
e le API non coperte dai test con i file `backend/test/*.http` o con l'app avviata.

## Backend

```text
route REST (routes/*.py) -> repository (db/repositories/*_repo.py) -> SQLite
tool MCP (integration/mcp/mcp_tools.py) -> services/mcp_service.py -> db/repositories/mcp_repo.py -> SQLite
```

- L'SQL sui dati sta solo nei repository. Apri le connessioni con
  `get_db_connection()` (attiva `PRAGMA foreign_keys = ON`) nella forma
  `with closing(get_db_connection()) as conn, conn:`, che fa commit/rollback e poi
  chiude. Non usare il solo `closing()`.
- Le route sono montate alla radice e sotto `/api`; il frontend usa `/api/...`.
  Endpoint nello stile `/<entita>/<azione>`, scritture in `POST` (aree: `PUT` e
  `DELETE`), errori `{"error": "..."}`.
- `validate_payload` (`validators/request_validator.py`) accetta solo i campi del
  suo `match`: per un campo nuovo aggiungi un `case`. Gli ID sono interi positivi
  fino a `2**63 - 1`; REST accetta anche stringhe di cifre ASCII, mai booleani o
  float. MCP usa il tipo strict `EntityId`: non tornare a `int` permissivi.
- Le impostazioni si validano complete (`validators/settings_validator.py`): niente
  aggiornamenti parziali senza cambiare il contratto in `doc/API_BACKEND.md`.
- Tool MCP: funzioni sincrone con modelli Pydantic (`integration/mcp/models.py`),
  bulk con validazione completa prima di scrivere e massimo 50 elementi. Gli errori
  per il client AI si sollevano con `ToolError`: le altre eccezioni arrivano come
  errore generico. Le operazioni che dipendono da altre righe ricontrollano i
  vincoli sotto `BEGIN IMMEDIATE` e pubblicano gli eventi dopo il commit.
- REST e MCP hanno logica separata di proposito (un elemento contro operazioni in
  blocco): non unificarli, ma applica a entrambi le regole comuni.
- Le scritture che il frontend deve vedere in tempo reale pubblicano un evento SSE
  con `services/event_service.publish()`.
- Percorsi e impostazioni solo da `config.py` (cambiano tra sviluppo e `IS_FROZEN`).
- SQLite: controlli cooperativi ogni 50.000 istruzioni interne; le connessioni
  normali hanno 30 secondi. `init_db()` condivide il budget di avvio di 120 secondi
  con connessione e backup di migrazione (`operation_timeout_seconds` esplicito),
  rispettando sempre eventuali scadenze esterne piu brevi. Non rimuovere i
  controlli di annullamento o allungare il limite delle richieste normali.
- `main.py` avvia Uvicorn in un thread e PyWebView nel thread principale; chiudere
  la finestra ferma il backend. Arresto e timeout passano da
  `services/operation_control.py`: non sostituirli con `os._exit()` o thread daemon.
- L'HTML e servito con `Cache-Control: no-store` e la finestra si apre con
  `?frontend=<hash di index.html>`. La route React `/tasks/{project_id:int}` precede
  il mount REST `/tasks`: non sovrapporle.
- macOS non e distribuito, ma non rimuovere il codice compatibile.

## Build e distribuzione

- Windows: build con console; `backend/windows/PlannerApp.exe.config`
  (`loadFromRemoteSources`) serve a pythonnet per caricare le DLL da uno ZIP
  scaricato: non rimuoverlo.
- Linux: `QT_API=pyqt6`; `prune_linux_bundle()` toglie QML, tema GTK3, stampa CUPS,
  le librerie usate solo da questi e `libstdc++`/`libgcc_s` (incompatibili con i
  driver grafici recenti). Non reintrodurli senza provare su una distribuzione recente.
- La build si ferma se la destinazione contiene dati runtime: non aggirarlo.
- Il job release richiede sia `PlannerApp-windows.zip` sia
  `PlannerApp-linux.tar.gz`. L'avvio manuale da un branch produce solo artifact.
- `build_licenses.py` copia nella build i testi di licenza di tutto cio che viene
  distribuito e si ferma se qualcosa non corrisponde (versioni di WebView2 SDK, Qt,
  ICU, librerie non coperte). Aggiorna i materiali seguendo `doc/GUIDA_SVILUPPO.md`,
  non disattivare i controlli. Una nuova dipendenza va aggiunta alle tabelle di
  `THIRD_PARTY_NOTICES.md`.
- Versioni fissate in `requirements.txt` (runtime) e `requirements-dev.txt`
  (strumenti, file UTF-8). I pacchetti Qt (`PyQt6*`, `QtPy`) si aggiornano insieme e
  restano nella serie di PyQt6-WebEngine.

## Database

- Schema finale in `backend/schema.sql`; i DB esistenti si aggiornano con gli
  script in `db/migrations/`, registrati in `MIGRATION_FILES`. Ogni modifica allo
  schema richiede entrambi; non modificare o rinumerare migrazioni distribuite e
  non mettere transazioni o `user_version` negli script. Procedura in `doc/DATABASE.md`.
- Un solo livello di subtask (`tasks.parent_id`). Lo stato di una task con subtask
  lo calcolano i trigger: non impostarlo dal codice.
- `completed` e `0`/`1`: il frontend confronta con `=== 1`.
- `backend/db/planner.db` non va committato; per ripartire da zero basta eliminarlo.

## Frontend

- Le chiamate HTTP passano da `src/api.ts` (funzioni in camelCase, payload con i
  nomi del backend). Eccezioni: `EventSource` in `DataSyncContext.jsx` e download
  del backup in `Setting.jsx`.
- Modali e card non importano `api.ts`: ricevono callback (`onSave`, `onDelete`,
  `onToggle`, `onEdit`) che restituiscono Promise. I chiamanti gestiscono toast,
  ricaricamento e navigazione; il modale si chiude solo se la callback riesce.
- Context in `src/context/` con tre file ciascuno (`XContext.jsx`,
  `xContextValue.js`, `useX.js`), per la regola ESLint `react-refresh`.
- Ricaricamento su eventi SSE con `useEffectEvent` e `lastEvent` di `useDataSync()`.
- Solo classi Tailwind, con i colori del tema `main-*` di `src/index.css`.
- Un componente per file, in PascalCase. TypeScript solo per `.ts`/`.tsx`
  (`import type` per i tipi).

## Testi e lingue

- Nessun testo fisso nell'interfaccia: `jsonLanguage['chiave']` da `useLanguage()`.
- Chiavi piatte con punti, aggiunte a tutti i file di `backend/locales/`.
- La portable copia i file lingua solo se mancano: le chiavi nuove non arrivano a
  chi li ha gia (vedi `doc/I18N.md`).

## Convenzioni

- Codice in inglese; commenti e documentazione in italiano. I file in `doc/` sono
  senza lettere accentate.
- Messaggi di errore delle API e descrizioni dei tool MCP in inglese.
- Python con funzioni a livello di modulo, classi solo per i modelli Pydantic.
- `APP_VERSION` in `backend/config.py` corrisponde al tag senza `v`.
- Quando cambi un comportamento documentato, aggiorna `doc/`.

## Sicurezza

Il backend ascolta su `127.0.0.1` senza autenticazione, ma qualsiasi pagina aperta
nel browser dell'utente puo raggiungerlo. Protezioni attive: nessun CORS,
`TrustedHostMiddleware` con `ALLOWED_HOSTS` (DNS rebinding) e
`middleware/origin_guard.py` (rifiuta scritture con `Origin` estraneo).

- Non aggiungere CORS, non allargare `origin_guard`, niente `*` in `ALLOWED_HOSTS`.
- Nessun endpoint `GET` che modifica dati.
- Nessun endpoint che legge o scrive file arbitrari o esegue comandi.
- Valida sempre gli input, anche dei tool MCP.

## Documentazione di riferimento

| Argomento | File |
|---|---|
| Struttura di cartelle e file | `doc/STRUTTURA_PROGETTO.md` |
| Endpoint REST, SSE e tool MCP | `doc/API_BACKEND.md` |
| Schema, trigger, migrazioni | `doc/DATABASE.md` |
| App portable e ciclo di vita | `doc/ARCHITETTURA_PORTABLE.md` |
| Avvio, test, build, licenze, release | `doc/GUIDA_SVILUPPO.md` |
| Lingue | `doc/I18N.md` |
| Problemi comuni | `doc/TROUBLESHOOTING.md` |
| Attivita aperte | `doc/TODO.md` |
