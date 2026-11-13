# TODO

## 1. Critico: distribuzione

### Linux

La build CI su Ubuntu 22.04 (ridotta, senza `libstdc++`) e completata e i materiali
di licenza sono stati verificati. Le prove manuali del pacchetto Linux sono
passate: avvio, salvataggi e persistenza, backup, link esterni, copia indirizzo
MCP e chiusura, con copertura di Wayland, X11 e di una seconda distribuzione
oltre a Debian 13.

- [ ] Finestra di errore grafica prima dell'apertura della finestra (oggi solo
  console e log)

### Pubblicazione 0.2.0

- [ ] Dopo la pubblicazione della `v0.2.0`, verificare entrambi gli allegati e il
  link a `SOURCES.md` nelle note

### Windows

- [ ] Provare la build CI con `PlannerApp.exe.config` estraendo lo ZIP senza
  sbloccarlo (la build precedente partiva solo dopo `Unblock-File`). Se non basta:
  passare la configurazione a pythonnet prima di importare pywebview, o togliere il
  segno dalle DLL all'avvio
- [ ] Verificare nella build `licenses/` (`LICENSE.txt` di Python con OpenSSL e
  runtime Visual C++, `microsoft-webview2/`, pacchetti `pythonnet` e `clr_loader`)
- [ ] Provare il pacchetto su un PC pulito (senza Python o Node): avvio, salvataggi,
  backup, MCP, persistenza, chiusura
- [ ] Valutare se togliere la console (`--windowed`): richiede di redirigere
  stdout/stderr e tutti i log in `planner.log`

## 2. Alta

### Dipendenze e build
- [ ] File di lock per le dipendenze indirette (es. `uv pip compile --universal`), usato in CI
- [ ] Decidere se fissare `ruff` o usare sempre l'ultima versione; in entrambi i casi
  un `ruff.toml` con le regole scelte e la correzione delle 74 segnalazioni di ruff
  0.17 (`I001`, `B023` nei test, `RUF059`, `BLE001`, `SIM117`, `S110`)

### Database
- [ ] Le migrazioni girano con `foreign_keys = ON` dentro la transazione: una che
  ricostruisce una tabella cancellerebbe a cascata le righe collegate. Disattivarle
  prima di `BEGIN IMMEDIATE` e fare `PRAGMA foreign_key_check` prima del commit.
  Da fare prima di qualsiasi migrazione che ricostruisce tabelle
- [ ] DB migrati da `v0.0.1`: possibili progetti e task orfani (foreign key non
  attive in quella versione); pulirli in una migrazione. In quei DB `parent_id` e
  l'ultima colonna: le migrazioni devono elencare le colonne, mai `SELECT *`

### Validazione ed errori
- [ ] Gestore globale degli errori (JSON non valido, `IntegrityError`)
- [ ] `get_project`: `404` se il progetto non esiste e gestione in `Tasks.jsx`

### Interfaccia e lingue
- [ ] Il toast "aggiornamento disponibile" e sempre in italiano (il controllo parte
  prima del caricamento del dizionario)
- [ ] Portare le nuove chiavi dei dizionari nei file esterni `locales/` gia presenti,
  preservando le traduzioni dell'utente

## 3. Media

### Backend
- [ ] Con `HOST` personalizzato `/mcp` risponde `421`: passare all'SDK `mcp` un
  `transport_security` costruito da `ALLOWED_HOSTS`
- [ ] `GET /backup/download` copia l'intero DB a ogni richiesta e un altro sito puo
  farla partire: rifiutare `Sec-Fetch-Site: cross-site`
- [ ] Backup: `ignore_cleanup_errors=True` per la cartella temporanea, pulizia
  all'avvio di `planner-backup-*` rimaste, valutare la pulizia di `migration_backups/`
- [ ] `/app/shutdown` non e usato dal frontend: rimuoverlo o motivarlo
- [ ] Log: in `planner.log` finisce solo `uvicorn.error` (i crash dei tool MCP restano
  in console); `InterruptedError` durante lo stop arriva al client MCP come errore generico
- [ ] Messaggio specifico per la porta gia occupata
- [ ] Ctrl+C non esce sempre con `130` (durante le migrazioni diventa un errore; su
  Windows e Qt lo gestisce pywebview)

### Test
- [ ] Test per `origin_guard`, `TrustedHostMiddleware`, il `409` di
  `update_status_task`, i controlli sul parent di `insert_task` e `delete_area` con
  il trigger (`test_app_routes.py` monta le route senza middleware)
- [ ] Test di migrazione con gli schemi reali dei tag (`git show v0.0.1:backend/schema.sql`)

### Varie
- [ ] Importazione sicura di un backup
- [ ] File `.http` per le route mancanti (`update_task`, `update_status_task`, `app/*`, `backup/download`)

## 4. Bassa

- [ ] Date formattate nell'interfaccia
- [ ] Testi brevi e simboli uniformi (X, x, OK)
- [ ] Stati vuoti per progetti, aree e task
- [ ] Fallback `noDescription` mai mostrato (la descrizione vuota e `""`, `??` non scatta)
- [ ] Tema `system` che segue i cambi del sistema operativo
- [ ] Accessibilita e focus dei modali
- [ ] Calendario: implementarlo o rimuovere pagina e tabella
- [ ] Testi fissi fuori dai dizionari (`SideBar.jsx`, `title="Coming soon"` in `Setting.jsx`)
- [ ] `.gitignore`: `*.db-journal`, `*-wal`, `*-shm`
- [ ] Dialogo di errore nativo Windows con `MB_SETFOREGROUND`/`MB_TOPMOST`
- [ ] MCP: limite di 50 elementi negli schemi di tutti i tool bulk e lunghezza massima
  dei testi
- [ ] Facoltativo: `npm run lint` e `ruff check` nel workflow CI
