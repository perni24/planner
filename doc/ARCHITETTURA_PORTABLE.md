# Architettura Portable

L'app viene distribuita come cartella generata da PyInstaller in modalita
`--onedir`: va sempre copiata l'intera cartella `PlannerApp`, non solo l'eseguibile.

## Motore della finestra

| Sistema | Renderer | Origine |
|---|---|---|
| Windows | WebView2 Runtime Evergreen (Chromium) | Preinstallato in Windows 11, aggiornato da Microsoft |
| Linux | Qt WebEngine (Chromium) | Incluso nel pacchetto, aggiornato con le release di Planner |

- **Windows**: il runtime non e incluso nella portable; se manca vedi
  `TROUBLESHOOTING.md`. `PlannerApp.exe.config` attiva `loadFromRemoteSources` in
  .NET Framework: senza, da uno ZIP scaricato e non sbloccato pythonnet non carica
  le sue DLL (`Failed to resolve Python.Runtime.Loader.Initialize`). Non toglie
  l'avviso di SmartScreen per un eseguibile non firmato.
- **Linux**: il pacchetto (circa 510 MB) contiene Qt WebEngine e le librerie di
  sistema necessarie, richiede glibc 2.34 o successiva e una sessione desktop. Per
  ora e solo un artifact di prova del workflow, non un allegato della release.
- **macOS**: non distribuito (vedi `SVILUPPI_FUTURI.md`).

## Struttura

```text
PlannerApp/
  PlannerApp(.exe)
  PlannerApp.exe.config   solo Windows
  _internal/              runtime Python, librerie, schema, migrazioni, frontend: non modificarla
  licenses/               testi di licenza dei componenti distribuiti (vedi THIRD_PARTY_NOTICES.md)
  LICENSE
  THIRD_PARTY_NOTICES.md
  data/                   creata al primo avvio
    planner.db
    migration_backups/    backup automatici prima delle migrazioni
    logs/planner.log      log desktop e Uvicorn, ruotato a circa 1 MB (tre copie)
    webview/              profilo della finestra (cookie, localStorage, cache)
  locales/                file lingua modificabili, copiati al primo avvio solo se mancano
```

I percorsi sono definiti in `backend/config.py`; in sviluppo dati, log e profilo
stanno in `backend/db/`, le lingue in `backend/locales/` e il frontend in
`frontend/dist/`.

## Avvio

1. Crea le cartelle runtime, copia i file lingua mancanti e prepara il database
   (creazione o migrazioni con backup, vedi `DATABASE.md`).
2. Verifica il frontend compilato e avvia Uvicorn in un thread su
   `127.0.0.1:8000`, senza reload.
3. Quando quel server e pronto (al massimo 15 secondi), apre la finestra su
   `APP_URL` con `?frontend=<hash di index.html>`: insieme a `Cache-Control:
   no-store` sull'HTML evita di mostrare una build precedente dalla cache.
4. Serve frontend, API (`/api`) e MCP (`/mcp/`) finche la finestra e aperta.

Se qualcosa fallisce (frontend mancante, porta occupata, migrazione, renderer),
l'errore va nel log e compare un messaggio con il percorso del log: un dialogo
nella finestra se e gia aperta, altrimenti su Windows un dialogo nativo; su Linux
restano console e log. Il processo esce con codice 1 (130 per Ctrl+C). I messaggi
usano la lingua del sistema (it/en) senza leggere il database.

## Chiusura

Chiudere la finestra ferma il backend; minimizzarla no, quindi MCP resta attivo.
Durante l'arresto le nuove richieste ricevono `503`, le connessioni SSE vengono
chiuse e le operazioni in corso hanno qualche secondo per finire, poi vengono
interrotte con rollback della transazione corrente. Se il backend non si ferma
entro il limite, l'app lo segnala e continua ad attendere senza terminazioni
forzate: non riavviare Planner finche il processo precedente non e terminato.
I limiti di tempo sono in `config.py`. Se il backend va in crash con la finestra
aperta, l'errore viene mostrato e la finestra si chiude.

## Funzioni della finestra

- Profilo persistente in `data/webview/` (`private_mode=False`), separato dal
  browser dell'utente. Tema e lingua sono comunque salvati nel database.
- Download abilitati: il backup (`/api/backup/download`) contiene solo il
  database, con nome datato generato dal backend.
- I link aperti con `window.open()` vanno nel browser di sistema.
- In sviluppo (`DEBUG` attivo) gli strumenti per sviluppatori non si aprono da
  soli: con Qt l'inspector e una finestra bianca (vedi `TROUBLESHOOTING.md`).

## Aggiornare l'app

Non c'e aggiornamento automatico: l'app segnala solo una nuova release su GitHub.
Scarica prima un backup, poi sostituisci eseguibile, `_internal/` e `licenses/`
con quelli nuovi e conserva `data/`. Le migrazioni aggiornano il database al primo
avvio. Se conservi `locales/`, le nuove chiavi di traduzione non vengono aggiunte:
elimina i file lingua non modificati per riceverli. Un database con schema piu
recente di quello supportato impedisce l'avvio: non tornare a una versione
precedente.
