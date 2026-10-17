# Sviluppi Futuri

Questo documento raccoglie idee e possibili evoluzioni non ancora pianificate.
Le idee richiedono una valutazione prima dell'implementazione; per quelle gia
pianificate viene indicato il rimando a `TODO.md`.

## Interfaccia desktop con PyWebView

L'integrazione e stata pianificata nella sezione "Interfaccia desktop e
spegnimento (PyWebView)" di `TODO.md`, con una prova prima della distribuzione.
Il frontend React verra mostrato in una finestra dedicata: backend e MCP resteranno
attivi anche con la finestra minimizzata e verranno arrestati alla sua chiusura,
senza heartbeat. Per la portable non e prevista una modalita solo backend.

## Supporto macOS

macOS e escluso dalle release (ottobre 2026): il pacchetto della `v0.1.0` non si
avviava. Il codice resta compatibile (pywebview usa il WebKit di sistema,
`WEBVIEW_GUI = None`), ma la distribuzione richiede un lavoro dedicato.

Cause probabili del mancato avvio, non verificate su un Mac:

- Gatekeeper: l'eseguibile non e firmato ne notarizzato. Da macOS 15 il tasto
  destro -> Apri non basta piu: serve "Apri comunque" in Privacy e sicurezza. Con
  `--onedir` anche ogni libreria in `_internal/` resta in quarantena e viene
  bloccata al caricamento;
- `Compress-Archive` non conserva il permesso di esecuzione Unix;
- `macos-latest` produce solo codice arm64, che non parte sui Mac Intel;
- il pacchetto e una cartella con un eseguibile Unix, non un bundle `.app`.

Per un uso di prova bastano `xattr -dr com.apple.quarantine .` e
`chmod +x PlannerApp` nella cartella estratta (vedi `TROUBLESHOOTING.md`).

Lavoro necessario per distribuirlo:

- scegliere il formato: bundle `.app` (PyInstaller `--windowed`) con `APP_DIR`
  adattato, perche `data/` e `locales/` non possono stare dentro il bundle;
- firma con un certificato Developer ID e notarizzazione (account Apple Developer);
- archivio che conservi permessi e firma (es. `.dmg` o `ditto`), per arm64 ed
  eventualmente Intel (build separate o universal2);
- verificare renderer, download, link esterni e dialoghi di errore con la finestra
  reale, anche prima dell'apertura della finestra;
- verificare la chiusura della finestra nello stesso istante in cui compare il
  messaggio di crash del backend: pywebview affida il dialogo al ciclo della
  finestra principale e, se questo e gia terminato, il thread di controllo di
  `main.py` potrebbe restare in attesa e il processo non terminare (ricavato dal
  codice di pywebview, non riprodotto);
- riaggiungere `macos-latest` (o le versioni scelte) al workflow di release.

## Distribuzione server con Docker o Podman

Valutare un'immagine container per eseguire Planner su un server personale,
mantenendo React, Starlette, SQLite e MCP. Non sarebbe necessario usare
l'eseguibile PyInstaller nel container.

Separare esplicitamente le modalita di avvio, per esempio con una futura
configurazione `APP_MODE=desktop|server`, senza basarsi soltanto su
`IS_PRODUCTION`:

- desktop: finestra PyWebView; alla chiusura si arrestano backend e MCP, come deciso per la portable;
- server: nessuna finestra, browser o heartbeat; backend e MCP restano attivi fino all'arresto del container.

Aspetti da implementare o verificare:

- mantenere il launcher desktop separato, senza importare o richiedere dipendenze grafiche in modalita server;
- creare un `Dockerfile`/`Containerfile` con build frontend tramite Node e immagine finale Python che serva `frontend/dist`, senza Vite, PyInstaller o reload;
- rendere configurabili i percorsi di database, backup e lingue personalizzate e montarli come volumi persistenti; verificare permessi e avvio rootless con Podman;
- inizializzare il database ed eseguire le migrazioni prima di rendere disponibili le API, conservando i backup automatici;
- configurare l'ascolto sulle interfacce del container, la pubblicazione controllata della porta e gli host ammessi, senza wildcard;
- adeguare `origin_guard` a HTTPS e all'eventuale reverse proxy mantenendo controlli sulle origini esatte, senza disattivare le protezioni o aggiungere CORS permissivo;
- proteggere sia REST sia MCP prima dell'accesso in rete: oggi l'app non ha autenticazione; valutare autenticazione oppure accesso limitato tramite VPN o reverse proxy autenticato;
- gestire i segnali di arresto del container e la chiusura ordinata delle connessioni SSE/MCP, con un tempo massimo di spegnimento;
- verificare aggiornamento dell'immagine senza perdita di dati, log, controllo di salute e compatibilita con Docker e Podman.

Inizialmente prevedere una sola istanza e un solo processo del backend: gli
eventi SSE sono conservati in memoria e non sono condivisi tra processi o
repliche. SQLite puo restare per questo scenario; la scalabilita richiederebbe
una valutazione separata.

Distinguere l'app condivisa da un'app multiutente con dati isolati: le aree non
sono account e le impostazioni sono globali. Account, autorizzazioni e isolamento
dei dati richiederebbero modifiche aggiuntive allo schema e alle API.

## Sincronizzazione completa tramite eventi SSE

La sincronizzazione tramite Server-Sent Events e gia attiva per le modifiche fatte
dai tool MCP (`GET /api/events`, vedi `API_BACKEND.md`). Restano da valutare:

- pubblicare gli eventi anche dalle route REST (con `event_service.publish()` dopo
  ogni modifica), cosi piu schede aperte restano allineate. Le route REST e i tool
  MCP restano separati: le prime lavorano su un elemento alla volta, i secondi in
  blocco, con validazioni e messaggi diversi;
- aggiungere eventi di eliminazione (`deleted`) e di cambio stato;
- includere negli eventi gli identificatori utili a ricaricare solo i dati
  interessati (per esempio `project_id` per le task);
- ricaricare i dati dopo una riconnessione SSE, perche gli eventi persi mentre la
  connessione era chiusa non vengono recuperati;
- gestire piu eventi ravvicinati nel frontend: `DataSyncContext` conserva solo
  l'ultimo evento ricevuto.

## Regole condivise tra REST e MCP

Con REST e MCP separati, le regole sui dati vanno scritte su entrambi i lati e
rischiano di divergere (oggi MCP impedisce le subtask di subtask, la REST no; il
controllo "la task ha subtask?" esiste sia in `task_repo` sia in `mcp_repo`).

Valutare di raccogliere queste regole in poche funzioni condivise, usate sia dalle
route sia da `mcp_service`, lasciando separati i flussi e i messaggi di errore.
