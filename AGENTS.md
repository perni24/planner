# AGENTS.md

Istruzioni per gli agenti AI che lavorano su questo repository. Contiene quello che
serve per modificare il codice senza romperlo; il resto e in `doc/`.

## Il progetto in breve

Planner e un'app locale per organizzare aree, progetti, task e subtask. Gira sul PC
dell'utente come cartella portable (PyInstaller). Un backend Python serve sia
l'interfaccia React sia le API su `127.0.0.1:8000`, e salva i dati in SQLite. Un
server MCP integrato permette a un client AI di leggere e modificare i dati.

- `backend/`: Python 3.12+ (il codice deve restare compatibile con la 3.12 usata dalla CI), Starlette, Uvicorn, `sqlite3`, SDK `mcp`.
- `frontend/`: React 19, Vite 8, Tailwind CSS 4, React Router 7.
- `doc/`: documentazione in italiano. Parti da `doc/STRUTTURA_PROGETTO.md`.
- `doc/TODO.md`: attivita aperte e problemi noti. Controllalo prima di "correggere"
  un comportamento strano: potrebbe essere gia documentato.

## Comandi

Backend (da `backend/`, con il venv attivo in `backend/.venv/`):

```bash
pip install -r requirements.txt
python main.py          # sviluppo: reload attivo, nessuno spegnimento automatico
ruff check .            # lint
python -m unittest discover -s test -p test_*.py -v
```

Frontend (da `frontend/`):

```bash
npm install
npm run dev             # http://localhost:5173, proxy /api -> 127.0.0.1:8000
npm run lint
npm run build
```

Build portable: `python build_portable.py` da `backend/` (output in
`backend/dist/PlannerApp/`).

Esistono test automatici delle migrazioni e del download backup in
`backend/test/test_migrations.py` e `backend/test/test_backup.py`, su database
temporanei. Per verificare una modifica: esegui i linter, i test se hai toccato il
database o il backup, `npm run build` se hai toccato il frontend, e prova le altre
API con i file `backend/test/*.http` o con l'app avviata.

## Architettura backend

Flusso delle richieste:

```text
route REST (routes/*.py) -> repository (db/repositories/*_repo.py) -> SQLite
tool MCP (integration/mcp/mcp_tools.py) -> services/mcp_service.py -> db/repositories/mcp_repo.py -> SQLite
```

- L'SQL sui dati sta solo nei repository. Route e service validano, chiamano il
  repository e restituiscono il risultato. Lo schema e le migrazioni sono gestiti
  separatamente all'avvio in `db/db.py` e `db/migration_runner.py`.
- Apri le connessioni sempre con `get_db_connection()` (`db/db.py`): attiva
  `PRAGMA foreign_keys = ON`, senza il quale i `ON DELETE CASCADE` non funzionano.
- I repository REST chiamano `conn.commit()` esplicitamente; `mcp_repo` si affida al
  commit automatico di `with conn:`. Nota: `with conn:` non chiude la connessione.
- Tutte le route sono montate due volte, alla radice e sotto `/api`
  (`routes/api.py`). Il frontend usa sempre `/api/...`.
- Gli endpoint seguono lo stile `/<entita>/<azione>` (es. `/tasks/insert_task`).
  Quasi tutte le scritture usano `POST`, tranne le aree (`PUT` e `DELETE`).
- Le risposte di errore hanno la forma `{"error": "..."}` con stato `400` o `404`.
- Validazione: `validators/request_validator.py`. `validate_payload` accetta solo i
  nomi di campo previsti nel suo `match` (`id`, `area_id`, `project_id`, `task_id`,
  `name`, `title`, `description`, `parent_id`): per un campo nuovo va aggiunto un
  `case`, altrimenti restituisce `Unknown field`.
- I tool MCP sono funzioni sincrone registrate in `register_mcp_tools`, con
  parametri definiti come modelli Pydantic in `integration/mcp/models.py`. Le
  operazioni bulk validano tutto prima di scrivere e accettano al massimo 50
  elementi.
- In `mcp_service.py` gli errori di validazione si sollevano con `ToolError`
  (`mcp.server.mcpserver.exceptions`): l'SDK mostra al client AI il messaggio solo
  per questa eccezione. Qualsiasi altra eccezione arriva come un generico
  `Error executing tool <nome>` e viene registrata nei log come crash.
- REST e MCP hanno logica separata di proposito: le route lavorano su un elemento
  alla volta, i tool MCP in blocco con messaggi pensati per un modello AI. Non
  unificarli. Se una regola vale per entrambi (es. chi puo fare da parent),
  applicala su entrambi i lati.
- Eventi SSE: `services/event_service.publish()` invia un evento
  `{"entity", "action", "ids"}` ai client connessi a `/api/events`. Oggi lo fanno
  solo le operazioni MCP. Se aggiungi una scrittura che il frontend deve vedere in
  tempo reale, pubblica un evento.
- Configurazione e percorsi stanno in `config.py` e cambiano tra sviluppo e
  eseguibile PyInstaller (`IS_FROZEN`). Non costruire percorsi a mano altrove.
- In produzione il server si spegne se non riceve heartbeat dalla UI per 60 secondi
  (`services/app_lifecycle.py`). In sviluppo il controllo e disattivato.

## Database

- Schema in `backend/schema.sql`: tabelle `areas`, `projects`, `tasks`, `settings`
  (una sola riga), `calendar` (vuota, inutilizzata), vista `v_projects_status`,
  quattro trigger sul completamento delle task.
- `schema.sql` viene applicato ai database nuovi o vuoti. Quelli esistenti vengono
  aggiornati all'avvio con `PRAGMA user_version` e gli script in `db/migrations/`,
  registrati in ordine in `MIGRATION_FILES` (`db/migration_runner.py`). Ogni modifica
  allo schema richiede sia l'aggiornamento di `schema.sql` sia una nuova migrazione;
  non modificare o rinumerare script gia distribuiti.
- Prima delle migrazioni viene creato un backup con l'API SQLite in
  `MIGRATION_BACKUPS_DIR` (`data/migration_backups/` nella portable). Ogni script e
  l'incremento di versione sono una transazione; un errore blocca l'avvio. Non
  inserire transazioni o assegnazioni a `user_version` negli script.
- La migrazione `001` corregge il trigger di eliminazione subtask e gestisce anche
  i DB di `v0.0.1` senza `parent_id`. Versione dello schema e `APP_VERSION` sono
  indipendenti; i database piu recenti di quelli supportati vengono rifiutati.
- Il download backup usa `backup_database()` in `db/db.py` (`Connection.backup()`)
  su una copia temporanea dentro `DATA_DIR`, non invia il DB originale in uso.
  Le connessioni sono chiuse prima dell'invio e il temporaneo viene eliminato
  al termine della risposta ASGI, anche in caso di errore o cancellazione.
- Un solo livello di subtask (`tasks.parent_id`). Lo stato di una task con subtask
  e calcolato dai trigger: non va impostato dal codice applicativo.
- `completed` e un intero `0`/`1`: il frontend confronta con `=== 1`, non con
  booleani.
- La vista conta solo le task di primo livello.
- Il trigger `trg_recreate_last_area` ricrea un'area vuota `utente` con nuovo id
  dopo l'eliminazione dell'ultima area, senza recuperare progetti o task. La
  migrazione `002` installa il trigger e ripristina i DB gia senza aree.
- Il DB di sviluppo e `backend/db/planner.db`: non va mai committato (gia in
  `.gitignore`). Per ripartire da zero basta eliminarlo.

## Architettura frontend

- Tutte le chiamate HTTP passano da `src/api.ts`, che usa `apiCore` in
  `src/apiCore.ts`. Non usare `fetch` nei componenti. Eccezioni: `EventSource` in
  `DataSyncContext.jsx` e il download del backup in `Setting.jsx`.
- Stato globale con i context in `src/context/`, composti in `AppProviders.jsx`.
  Ogni context usa tre file: `XContext.jsx` (provider), `xContextValue.js`
  (`createContext`) e `useX.js` (hook che lancia un errore fuori dal provider).
  Questa separazione serve alla regola ESLint `react-refresh`: mantienila.
- Per ricaricare i dati quando arriva un evento SSE si usa `useEffectEvent`
  (React 19.2) insieme a `lastEvent` di `useDataSync()`.
- Stile solo con classi Tailwind. I colori del tema usano le classi `main-*`
  (`bg-main-card`, `text-main-text`, `border-main-border`...) definite in
  `src/index.css`: usale invece dei colori fissi, cosi i temi chiaro, scuro e custom
  continuano a funzionare.
- Componenti e pagine in PascalCase, un componente per file.
- I file `.ts` in `src/types/` non vengono verificati: non c'e `tsconfig` ne il
  pacchetto `typescript`, ed ESLint controlla solo `.js` e `.jsx`.

## Testi e lingue

- Nessun testo fisso nell'interfaccia: usa `jsonLanguage['chiave']` da
  `useLanguage()`.
- Le chiavi sono piatte, con punti (`"taskModal.actions.create"`), e vanno aggiunte
  a **tutti** i file in `backend/locales/` (oggi `it.json` e `en.json`).
- L'app portable copia i file lingua accanto all'eseguibile solo se mancano: le
  chiavi nuove non arrivano a chi ha gia quei file.

## Convenzioni

- Codice (variabili, funzioni, endpoint) in inglese. Commenti e documentazione in
  italiano. I file in `doc/` sono scritti senza lettere accentate ("e", "attivita").
- Messaggi di errore delle API e descrizioni dei tool MCP in inglese.
- Python: stile coerente con i file esistenti, funzioni a livello di modulo, niente
  classi se non per i modelli Pydantic.
- `backend/requirements.txt` e codificato in UTF-16. Se lo modifichi, controlla di
  non mischiare codifiche (meglio convertirlo tutto in UTF-8).
- `APP_VERSION` in `backend/config.py` deve corrispondere al tag di release senza
  la `v` (tag `v0.1.0` -> `"0.1.0"`). La versione in `frontend/package.json` non e
  usata.
- Quando cambi un comportamento documentato, aggiorna il file pertinente in `doc/`.

## Sicurezza

Il backend ascolta solo su `127.0.0.1`, ma e raggiungibile da qualsiasi pagina web
aperta nel browser dell'utente. Non ha autenticazione. Le protezioni attive sono:

- nessun middleware CORS: le altre origini non possono leggere le risposte;
- `TrustedHostMiddleware` (in `main.py`): rifiuta con `400` le richieste con un
  header `Host` non presente in `ALLOWED_HOSTS` (`config.py`), contro il DNS
  rebinding. Non gestisce IPv6 (`Host: [::1]:8000` viene rifiutato);
- `middleware/origin_guard.py`: rifiuta con `403` le richieste `POST`, `PUT`,
  `PATCH` e `DELETE` con un `Origin` diverso da quello del backend (in sviluppo
  sono ammesse anche le origini locali, per Vite).

Di conseguenza:

- non aggiungere CORS, non allargare le origini ammesse da `origin_guard` e non
  aggiungere `*` ad `ALLOWED_HOSTS`;
- non creare endpoint `GET` che modificano dati: `origin_guard` non li controlla;
- non aggiungere endpoint che leggono o scrivono file arbitrari o eseguono comandi;
- valida sempre gli input, anche quelli dei tool MCP, che arrivano da un modello AI.

## Documentazione di riferimento

| Argomento | File |
|---|---|
| Struttura di cartelle e file | `doc/STRUTTURA_PROGETTO.md` |
| Endpoint REST, SSE e tool MCP | `doc/API_BACKEND.md` |
| Schema, trigger, vista | `doc/DATABASE.md` |
| App portable, heartbeat, aggiornamenti | `doc/ARCHITETTURA_PORTABLE.md` |
| Avvio, lint, build, release | `doc/GUIDA_SVILUPPO.md` |
| Lingue | `doc/I18N.md` |
| Problemi comuni | `doc/TROUBLESHOOTING.md` |
| Attivita aperte e problemi noti | `doc/TODO.md` |
