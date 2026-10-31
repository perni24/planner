# Sviluppi Futuri

Idee non ancora pianificate, da valutare prima dell'implementazione. Le attivita
gia decise sono in `TODO.md`.

## Distribuzione Windows: installer e firma

La portable ZIP non e firmata: al primo avvio SmartScreen la blocca ("Esegui
comunque") e i file estratti conservano il segno "proveniente da Internet". Un
installer (Inno Setup, NSIS o MSI) evita il segno sui file installati; la firma
Authenticode (certificato a pagamento o servizi gratuiti per progetti open source,
come SignPath) riduce gli avvisi. Valutare anche winget o Scoop.

## Supporto macOS

macOS e escluso dalle release: il pacchetto della `v0.1.0` non si avviava. Il
codice resta compatibile (pywebview usa il WebKit di sistema), ma servirebbero:

- un bundle `.app` (PyInstaller `--windowed`) con `data/` e `locales/` fuori dal
  bundle;
- firma Developer ID e notarizzazione (account Apple Developer), altrimenti
  Gatekeeper blocca eseguibile e librerie;
- un archivio che conservi permessi e firma (`.dmg` o `ditto`), per arm64 ed
  eventualmente Intel;
- prove con la finestra reale (download, link, dialoghi di errore) e il ritorno di
  macOS nel workflow di release.

## Distribuzione server con Docker o Podman

Un'immagine container per un server personale, senza PyInstaller e senza finestra:

- una modalita di avvio esplicita (es. `APP_MODE=desktop|server`) che non importi
  le dipendenze grafiche;
- percorsi di database, backup e lingue configurabili e montati come volumi;
- ascolto sulle interfacce del container con host ammessi espliciti e
  `origin_guard` adeguato a HTTPS e reverse proxy, senza CORS permissivo;
- autenticazione per REST e MCP prima di esporre l'app in rete (oggi non c'e),
  oppure accesso solo tramite VPN o reverse proxy autenticato;
- arresto ordinato ai segnali del container.

Un solo processo e sufficiente (gli eventi SSE sono in memoria). Aree e
impostazioni non sono separate per utente: un'app multiutente richiederebbe
modifiche a schema e API.

## Sincronizzazione completa tramite eventi SSE

Oggi solo i tool MCP pubblicano eventi. Restano da valutare:

- eventi anche dalle route REST, per tenere allineate piu finestre;
- identificatori utili nel payload (es. `project_id` delle task) per ricaricare solo
  i dati interessati;
- ricaricamento dopo una riconnessione SSE, perche gli eventi persi non vengono
  recuperati;
- gestione di eventi ravvicinati: `DataSyncContext` conserva solo l'ultimo.

## Regole condivise tra REST e MCP

REST e MCP restano separati, ma alcune regole sui dati sono scritte due volte (es.
il controllo "la task ha subtask?" in `task_repo` e `mcp_repo`) e possono
divergere. Valutare poche funzioni condivise, lasciando separati flussi e messaggi.
