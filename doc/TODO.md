# TODO

## 1. Critico

### Build e distribuzione desktop (PyWebView)

**1. Renderer Linux: Qt**

- [ ] Eseguire il workflow Linux configurato su `ubuntu-22.04` x64: confermare build reale, rilevamento PyQt6, risorse QtWebEngine e controlli del pacchetto; i test locali simulano la build
- [ ] Estrarre il `.tar.gz` prodotto dalla CI su Linux e verificare avvio, collegamenti simbolici e permessi dell'app e di `QtWebEngineProcess`
- [ ] Verificare nella build Linux reale `licenses/manifest.json` e i testi copiati dalle wheel QtPy/PyQt6/PyQt6-sip/Qt6/QtWebEngine; controllare che le versioni corrispondano alle librerie nel TAR.GZ
- [ ] Completare gli avvisi di terze parti Qt/Chromium per la versione QtWebEngine effettivamente inclusa: le licenze principali delle wheel non contengono tutti gli avvisi Chromium
- [ ] Prima della release Linux, predisporre e verificare l'accesso ai sorgenti corrispondenti delle componenti GPL/LGPL distribuite; il manifest e i collegamenti agli upstream non sostituiscono questa verifica
- [ ] Prove con la finestra reale: download del backup, link esterni, copia indirizzo MCP, chiusura, Wayland e X11; pacchetto estratto su Ubuntu 22.04 e su una distribuzione diversa (es. Fedora o KDE)
- [ ] Definire il fallback grafico degli errori prima dell'apertura della finestra su Linux, per esempio con Qt: oggi restano log e console
- [ ] Dopo build reale, licenze e prove native, abilitare l'allegato Linux nelle release: il filtro `pattern: PlannerApp-windows` lo esclude finche non e verificato

**2. Verifica dei pacchetti e documentazione**

- [ ] Provare i pacchetti estratti su macchine pulite Windows e Linux, senza Python, Node o Vite installati: avvio, salvataggi, backup, MCP, persistenza e chiusura completa
- [ ] Allineare guide, istruzioni per gli agenti e documentazione portable ai renderer, ai prerequisiti e ai pacchetti effettivamente verificati

## 2. Alta

### Dipendenze e build
- [ ] Fissare la versione di `mcp` (il codice usa `mcp.server.mcpserver.MCPServer` e `ToolError` dell'SDK 2.x)

### Database e migrazioni
- [ ] `migration_runner.py`: le migrazioni girano con `foreign_keys = ON` dentro la transazione, dove `PRAGMA foreign_keys = OFF` viene ignorato. Una migrazione che ricostruisce una tabella cancellerebbe a cascata le righe collegate. Disattivare le foreign key prima di `BEGIN IMMEDIATE`, eseguire `PRAGMA foreign_key_check` prima del commit e documentarlo in `DATABASE.md`. Da fare prima di qualsiasi migrazione che ricostruisce tabelle
- [ ] Database migrati da `v0.0.1`: quella versione non attivava le foreign key e puo aver lasciato progetti e task orfani, ancora visibili via MCP (`get_all_projects` con `area_name` nullo). Pulirli o riassegnarli in una migrazione
- [ ] Nei database migrati da `v0.0.1` la colonna `parent_id` e l'ultima di `tasks`: documentare in `DATABASE.md` che le migrazioni devono usare elenchi di colonne espliciti, mai `SELECT *`
- [ ] L'inizializzazione del DB ha di fatto un limite di 30 secondi (`DATABASE_OPERATION_TIMEOUT_SECONDS`), non i 120 documentati: la connessione di `init_db` eredita il limite per singola operazione. Aprirla con il budget di inizializzazione oppure correggere la documentazione
- [ ] Il controllo di annullamento SQLite ogni 1000 passi (`DATABASE_PROGRESS_STEPS`) rallenta molto le query quando un altro thread esegue codice Python (misurato: da 0,06 a 17,8 secondi). Portarlo a 50.000-100.000

### Validazione input
- [ ] MCP: Pydantic converte `"yes"` e `1` in `True`, quindi il controllo `isinstance(completed, bool)` in `mcp_service` non scatta mai. Usare tipi strict nei modelli

### Gestione errori
- [ ] Aggiungere un gestore globale degli errori nel backend (JSON non valido nelle altre route, `IntegrityError`)
- [ ] `get_project`: restituire `404` se il progetto non esiste (oggi `200` con `null`) e gestirlo in `Tasks.jsx`

### Interfaccia
- [ ] Il toast "aggiornamento disponibile" in `AppProviders.jsx` e sempre in italiano: il controllo parte prima che il dizionario lingua sia caricato, quindi viene usato il testo di riserva. Attendere il dizionario o leggere la chiave quando arriva la risposta

### Lingue portable
- [ ] Integrare le nuove chiavi dei dizionari inclusi nel bundle con i file esterni `locales/`, preservando le traduzioni dell'utente: oggi aggiornare l'app con file lingua gia presenti puo lasciare testi vuoti

## 3. Media

### Backend
- [ ] Con `HOST` personalizzato `/mcp` risponde `421`: l'SDK `mcp` ha un proprio controllo di `Host` limitato ai nomi locali. Passare `transport_security` costruito da `ALLOWED_HOSTS`
- [ ] `GET /backup/download` crea una copia completa del DB a ogni richiesta (anche `HEAD`) e un altro sito puo farla scattare: rifiutare `Sec-Fetch-Site: cross-site` su questa route
- [ ] Backup: creare la cartella temporanea con `ignore_cleanup_errors=True` (su Windows antivirus o indicizzazione possono bloccare l'eliminazione) e rimuovere all'avvio le cartelle `planner-backup-*` rimaste; valutare la pulizia dei vecchi backup in `migration_backups/`
- [ ] `/app/shutdown` non e piu usato dal frontend ma resta esposto: rimuoverlo o documentare perche resta
- [ ] Log: solo `uvicorn.error` finisce in `planner.log`, i crash dei tool MCP restano in console. `InterruptedError` durante lo stop arriva al client MCP come errore generico
- [ ] Messaggio specifico quando la porta e gia occupata (es. un'istanza precedente ancora in chiusura) invece dell'errore generico di avvio
- [ ] Ctrl+C non restituisce sempre `130` come documentato in `ARCHITETTURA_PORTABLE.md`: durante le migrazioni diventa un errore di migrazione, su Windows e Qt lo gestisce pywebview. Correggere il comportamento o la documentazione

### Test
- [ ] Aggiungere test automatici per `origin_guard`, `TrustedHostMiddleware`, il `409` di `update_status_task`, i controlli sul parent di `insert_task` e `delete_area` con il trigger. `test_app_routes.py` monta le route senza middleware
- [ ] Nei test di migrazione costruire i DB legacy dagli schemi reali dei tag (`git show v0.0.1:backend/schema.sql`) invece che modificando `schema.sql` con espressioni regolari

### Frontend
- [ ] Risposte fuori ordine: cambiando area o facendo click rapidi su task diverse, una risposta lenta puo sovrascrivere quella piu recente (`Project.jsx`, `Tasks.jsx`). Ignorare le risposte non piu attuali e svuotare i dati al cambio di area
- [ ] Se dopo una scrittura riuscita il ricaricamento delle aree fallisce, `AreaSwitcher` scompare finche non arriva un evento SSE e l'errore non viene mostrato

- [ ] Progettare e implementare l'importazione sicura di un backup
- [ ] Aggiornare i file `.http` per coprire tutte le route (mancano `update_task`, `update_status_task`, `app/*` e `backup/download`)

## 4. Bassa

### Interfaccia
- [ ] Formattare le date mostrate in UI
- [ ] Standardizzare testi brevi e simboli come X, x e OK
- [ ] Migliorare gli stati vuoti per progetti, aree e task
- [ ] Mostrare il fallback `noDescription`: la descrizione vuota e salvata come `""`, quindi `??` non scatta mai
- [ ] Far seguire al tema `system` i cambi del tema del sistema operativo
- [ ] Migliorare l'accessibilita dei modali e la gestione del focus
- [ ] Calendario: implementare la pagina (e usare la tabella `calendar`) oppure nascondere la pagina e rimuovere la tabella

### Varie
- [ ] Testi fissi fuori dai dizionari: `aria-label`/`title` in `SideBar.jsx` e `title="Coming soon"` in `Setting.jsx`
- [ ] Aggiornare in `AGENTS.md` e `API_BACKEND.md` l'elenco dei codici di errore: oltre a 400/404 esistono 403, 409, 503, 504, il 400 in testo semplice di `TrustedHostMiddleware` e il 421 di `/mcp`
- [ ] Aggiungere a `.gitignore` i file `*.db-journal`, `*-wal` e `*-shm`
- [ ] Messaggio di errore nativo Windows: aggiungere `MB_SETFOREGROUND`/`MB_TOPMOST`, altrimenti dopo la chiusura della finestra puo apparire dietro le altre
- [ ] MCP: dichiarare il limite di 50 elementi nello schema dei tool (`Field(max_length=50)`) e limitare la lunghezza dei testi

### Automazione facoltativa

- [ ] Valutare, se desiderato, l'esecuzione di `npm run lint` e `ruff check` nel workflow CI
