# TODO

Attivita aperte, ordinate per priorita. Le attivita completate vengono rimosse: lo
storico resta nella cronologia Git. Le idee non ancora pianificate stanno in
`SVILUPPI_FUTURI.md`.

## 1. Critico

Da risolvere prima della prossima release.

### Bug emersi dalla revisione del codice (2026-10-17)
- [ ] Release Linux: finche build, CI e prove del renderer Qt non sono completate (vedi "Renderer Linux: Qt" sotto), escludere Linux dalla release o bloccarne la pubblicazione

### Interfaccia desktop e spegnimento (PyWebView)

Decisione: nell'app portable backend e MCP restano attivi finche la finestra di
Planner e aperta, anche se minimizzata. Chiudendo la finestra si arresta tutto.
Non sono previste una modalita solo backend o un'icona nell'area di notifica.
PyWebView gestisce il ciclo di vita dell'app senza heartbeat dal frontend;
React, API REST, MCP, SQLite ed eventi SSE restano invariati.

Sistemi supportati: Windows e Linux. macOS e escluso per ora (niente build in CI);
cause e lavoro necessario sono in `SVILUPPI_FUTURI.md`, "Supporto macOS".

`backend/main.py` resta l'unico punto di ingresso, anche per PyInstaller:
prepara l'ambiente, avvia Uvicorn in un thread separato, attende che sia pronto
e apre PyWebView nel thread principale. Non e previsto `backend/desktop.py`
ne un secondo avvio portable basato sul browser.

#### Verifiche native ancora aperte

L'avvio della finestra e stato verificato manualmente su Windows. I test
automatici simulano la GUI: non sostituiscono le prove seguenti. I dettagli delle
funzioni implementate sono in `ARCHITETTURA_PORTABLE.md`; la procedura di prova
e in `GUIDA_SVILUPPO.md`.

- [ ] Verificare lettura e salvataggio di progetti/task, MCP durante la minimizzazione e chiusura durante salvataggi REST/MCP e download; controllare che processo e porta vengano rilasciati
- [ ] Verificare i messaggi nativi Windows per errori di avvio e crash e la chiusura della finestra dopo lo shutdown via API
- [ ] Verificare che cookie e `localStorage` persistano dopo chiusura e riavvio; tema e lingua sono salvati nel DB e non dimostrano da soli la persistenza del profilo
- [ ] Verificare download del backup con scelta della destinazione e annullamento del dialogo, link GitHub nel browser esterno e copia dell'indirizzo MCP; adeguare solo se necessario
- [ ] Testare temi, lingue, aggiornamenti SSE e uso MCP dopo riavvio e sospensione/ripresa del PC

#### Build e distribuzione desktop

Queste attivita sostituiscono il vecchio passaggio 8. Procedere nell'ordine
seguente, prima di distribuire il nuovo avvio desktop.

**1. Renderer e dipendenze**

- [ ] Confermare i requisiti WebView2 su Windows

**Renderer Linux: Qt**

Scelto Qt (PyQt6 + QtWebEngine): il pacchetto e autosufficiente, a differenza di GTK
che richiede WebKitGTK installato. Fatto: dipendenze in `requirements.txt` e
`WEBVIEW_GUI = "qt"`; verificato in modalita offscreen che l'app completa si carica
nella finestra Qt (Chromium 140) e si chiude con `/app/shutdown`. Restano:

- [ ] `build_portable.py`: verificare con una build reale il rilevamento di `qtpy` (eventuale `QT_API=pyqt6` o `--hidden-import`), escludere `gi` (GTK) e valutare l'esclusione dei moduli Qt inutilizzati
- [ ] CI: compilare su `ubuntu-22.04` (compatibilita glibc), installare le librerie di sistema richieste da Qt (`libxcb-cursor0`, `libxkbcommon-x11-0`, `libegl1`, `libnss3`...) e creare un `.tar.gz` che conservi i permessi
- [ ] Licenze: aggiungere Qt, PyQt6 (GPL v3) e QtWebEngine a `THIRD_PARTY_NOTICES.md` e verificare che le note di licenza di Chromium siano incluse nel pacchetto
- [ ] Prove con la finestra reale: download del backup, link esterni, copia indirizzo MCP, chiusura, Wayland e X11; pacchetto estratto su Ubuntu 22.04 e su una distribuzione diversa (es. Fedora o KDE)
- [ ] `TROUBLESHOOTING.md`: errore Qt "Could not load the Qt platform plugin xcb" (libreria di sistema mancante)
- [ ] Definire il fallback grafico degli errori prima dell'apertura della finestra su Linux, per esempio con Qt: oggi restano log e console

**2. Script PyInstaller**

- [ ] Adeguare `build_portable.py` ai renderer scelti: verificare hook/import necessari ed escludere eventuali renderer inutilizzati, mantenendo `main.py` e inizialmente la console Windows
- [ ] Verificare i contenuti del pacchetto: frontend, schema, migrazioni, lingue e licenze; non includere database, log o profili WebView personali

**3. GitHub Actions e archivi**

- [ ] Installare nel workflow le dipendenze specifiche dei renderer per ciascun sistema, mantenendo gli avvii su tag `v*` e manuale
- [ ] Adeguare il confezionamento degli archivi e verificare su Linux la conservazione dei permessi di esecuzione dopo l'estrazione

**4. Verifica dei pacchetti e documentazione**

- [ ] Provare i pacchetti estratti su macchine pulite Windows e Linux, senza Python, Node o Vite installati: avvio, salvataggi, backup, MCP, persistenza e chiusura completa
- [ ] Allineare guide, istruzioni per gli agenti e documentazione portable ai renderer, ai prerequisiti e ai pacchetti effettivamente verificati

## 2. Alta

### Dipendenze e build
- [ ] Fissare la versione di `mcp` (il codice usa `mcp.server.mcpserver.MCPServer` e `ToolError` dell'SDK 2.x)
- [ ] CI: verificare che `APP_VERSION` corrisponda al tag della release

### Database e migrazioni
- [ ] `migration_runner.py`: le migrazioni girano con `foreign_keys = ON` dentro la transazione, dove `PRAGMA foreign_keys = OFF` viene ignorato. Una migrazione che ricostruisce una tabella cancellerebbe a cascata le righe collegate. Disattivare le foreign key prima di `BEGIN IMMEDIATE`, eseguire `PRAGMA foreign_key_check` prima del commit e documentarlo in `DATABASE.md`. Da fare prima di qualsiasi migrazione che ricostruisce tabelle
- [ ] Database migrati da `v0.0.1`: quella versione non attivava le foreign key e puo aver lasciato progetti e task orfani, ancora visibili via MCP (`get_all_projects` con `area_name` nullo). Pulirli o riassegnarli in una migrazione
- [ ] Nei database migrati da `v0.0.1` la colonna `parent_id` e l'ultima di `tasks`: documentare in `DATABASE.md` che le migrazioni devono usare elenchi di colonne espliciti, mai `SELECT *`
- [ ] L'inizializzazione del DB ha di fatto un limite di 30 secondi (`DATABASE_OPERATION_TIMEOUT_SECONDS`), non i 120 documentati: la connessione di `init_db` eredita il limite per singola operazione. Aprirla con il budget di inizializzazione oppure correggere la documentazione
- [ ] Il controllo di annullamento SQLite ogni 1000 passi (`DATABASE_PROGRESS_STEPS`) rallenta molto le query quando un altro thread esegue codice Python (misurato: da 0,06 a 17,8 secondi). Portarlo a 50.000-100.000

### Validazione input
- [ ] `validate_int`: id oltre il limite SQLite (es. `10**30`) causano `500` in REST ed errori generici in MCP; `true` e `1.9` vengono accettati come `1`. Rifiutare `bool`, float non interi e valori oltre `2**63-1`
- [ ] MCP: Pydantic converte `"yes"` e `1` in `True`, quindi il controllo `isinstance(completed, bool)` in `mcp_service` non scatta mai. Usare tipi strict nei modelli

### Gestione errori
- [ ] Aggiungere un gestore globale degli errori nel backend (JSON non valido, `IntegrityError`, chiavi mancanti in `custom_colors`)
- [ ] Allineare `apiCore.ts`, che legge `detail`/`message`, al campo `error` restituito dal backend
- [ ] `get_project`: restituire `404` se il progetto non esiste (oggi `200` con `null`) e gestirlo in `Tasks.jsx`
- [ ] Validare la lingua in `update_language` e usare una lingua di fallback se il file manca
- [ ] Validare in `update_theme` i valori ammessi per `theme`, il tipo e le chiavi di `custom_colors` e il formato dei colori prima di scrivere nel DB

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

I lint vengono eseguiti manualmente in locale; automatizzarli non e un requisito
per la release.

- [ ] Valutare, se desiderato, l'esecuzione di `npm run lint` e `ruff check` nel workflow CI
