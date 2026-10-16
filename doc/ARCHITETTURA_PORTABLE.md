# Architettura Portable

L'app puo essere eseguita come cartella portable generata con PyInstaller in modalita `--onedir`.

Il codice usa ora l'avvio desktop PyWebView, ancora in fase di integrazione:
packaging e funzionamento nativo sui tre sistemi devono essere verificati prima
della distribuzione. Le vecchie release gia pubblicate mantengono il precedente
avvio nel browser.

## Struttura dell'output

Dopo la build locale o GitHub Actions, l'output principale e:

```text
backend/dist/PlannerApp/
  PlannerApp.exe
  _internal/
```

Al primo avvio vengono aggiunte le cartelle modificabili:

```text
PlannerApp/
  data/
    planner.db
    webview/
  locales/
    it.json
    en.json
```

Su Linux e macOS il file eseguibile non avra estensione `.exe`, ma la logica resta la stessa.

## Cartelle tecniche

- `_internal/`: contiene runtime Python, librerie, `schema.sql`, `db/migrations/`, frontend buildato e file inclusi da PyInstaller. Non va modificata manualmente.
- `data/`: contiene il database SQLite creato vicino all'eseguibile al primo avvio. `migration_backups/` viene aggiunta quando un database esistente deve essere aggiornato.
- `data/logs/`: log degli errori desktop e di Uvicorn. `planner.log` arriva a circa 1 MB, con al massimo tre copie ruotate; se la cartella non e scrivibile resta la console.
- `data/webview/`: profilo della finestra (cookie, dati web e cache gestiti dal renderer), separato dal profilo del browser dell'utente.
- `locales/`: contiene i file lingua esterni copiati al primo avvio e modificabili dall'utente.

## Percorsi principali

I percorsi sono definiti in `backend/config.py`.

In sviluppo:

```text
DB_PATH -> backend/db/planner.db
MIGRATIONS_DIR -> backend/db/migrations
MIGRATION_BACKUPS_DIR -> backend/db/migration_backups
LOCALES_DIR -> backend/locales
FRONTEND_DIST_DIR -> frontend/dist
DESKTOP_LOG_PATH -> backend/db/logs/planner.log
WEBVIEW_STORAGE_DIR -> backend/db/webview/
```

In PyInstaller:

```text
DB_PATH -> PlannerApp/data/planner.db
MIGRATIONS_DIR -> _internal/db/migrations
MIGRATION_BACKUPS_DIR -> PlannerApp/data/migration_backups
LOCALES_DIR -> PlannerApp/locales
FRONTEND_DIST_DIR -> _internal/frontend_dist
DESKTOP_LOG_PATH -> PlannerApp/data/logs/planner.log
WEBVIEW_STORAGE_DIR -> PlannerApp/data/webview/
```

## Avvio dell'app

Quando l'eseguibile parte:

1. crea le cartelle runtime `data/`, `locales/` e `data/webview/` se non esistono;
2. copia i file lingua default in `locales/` solo se mancano;
3. crea il database SQLite se nuovo o vuoto, oppure applica le migrazioni mancanti dopo un backup automatico;
4. verifica la presenza del frontend compilato e avvia Uvicorn in un thread separato su `127.0.0.1:8000`, senza reload (host e porta restano configurabili);
5. attende che quel server sia pronto, con un timeout di 15 secondi, senza interrogare altri servizi eventualmente presenti sulla stessa porta;
6. apre PyWebView nel thread principale all'URL configurato in `APP_URL`; su Windows usa WebView2;
7. serve il frontend React buildato, le API sotto `/api` e il server MCP sotto `/mcp` finche la finestra resta aperta.

L'importazione di `main.py` non prepara il runtime e non avvia server o finestra.
Frontend mancante, porta occupata, timeout ed errori del renderer impediscono
l'avvio o richiedono lo stop del backend. Il coordinatore registra il traceback
e mostra un messaggio breve, con il percorso del log; l'uscita ha codice 1.
Ctrl+C termina con codice 130 senza mostrare un errore.

Se la finestra e gia aperta si usa un dialogo PyWebView. Per gli errori prima
della finestra o del renderer, Windows usa un dialogo nativo indipendente da
WebView2; sulle altre piattaforme restano console e log finche il fallback
grafico non sara definito. Un errore del dialogo non nasconde quello originale.
I messaggi usano la lingua di sistema it/en e il fallback inglese, senza
interrogare il database potenzialmente guasto (vedi `I18N.md`).

L'inizializzazione precedente al server ha un budget cooperativo di 120 secondi,
controllato tra le fasi e le istruzioni delle migrazioni. Ogni connessione SQLite
ha un limite di esecuzione di 30 secondi e un'attesa per lock di 1 secondo.
Backup e query controllano le scadenze anche durante il lavoro. I limiti non
possono interrompere una singola chiamata I/O bloccata dal sistema operativo.

## Chiusura della finestra

Chiudere la finestra richiede l'arresto di Uvicorn e attende il thread backend.
Minimizzare la finestra non lo interrompe, quindi anche MCP resta attivo.

La prima richiesta di stop fissa una scadenza condivisa; richieste successive non
la prolungano. Le nuove richieste ricevono `503` e non vengono aperte nuove
connessioni al database. Le code SSE vengono chiuse subito, oltre che alla
disconnessione e nel lifespan, sbloccando le letture pendenti nell'executor.

Le operazioni gia iniziate hanno 3 secondi per terminare. Dopo questa tolleranza,
i controlli di avanzamento interrompono query, backup e bulk MCP ancora in corso.
I bulk controllano anche tra gli elementi e prima del commit: un annullamento
esegue il rollback della transazione corrente, senza cancellare dati gia
confermati. Anche migrazione e incremento della versione restano atomici.
I file di backup incompleti vengono eliminati dopo la chiusura delle connessioni.

Uvicorn concede 5 secondi alle richieste in corso; il coordinatore attende 10
secondi prima di segnalare un arresto lento. Se il thread non termina, mostra un
messaggio specifico e continua ad attenderne la conclusione sicura. Non usa
`os._exit()`, thread daemon o terminazioni forzate. Questo non garantisce l'uscita
entro un tempo assoluto in caso di I/O nativo non interrompibile: non riavviare
Planner finche il processo precedente non e terminato. Tutti i limiti sono in
`config.py`; la verifica manuale della finestra resta in `TODO.md`.

Un evento Python segnala la conclusione del thread backend. Il monitor attende
che la finestra sia mostrata prima di interagire con la GUI: in caso di crash
mostra l'errore e chiude la finestra; dopo uno shutdown richiesto via API la
chiude senza allarme. Se il renderer fallisce, il monitor viene annullato.

Il vecchio monitor heartbeat, il relativo endpoint e il timer React sono stati
rimossi. `app_lifecycle.py` mantiene soltanto la callback dello shutdown esplicito;
`AppProviders.jsx` mantiene il controllo automatico degli aggiornamenti.
Il commento heartbeat delle connessioni SSE resta attivo: mantiene la connessione
eventi e non decide quando spegnere il backend.

## Profilo e funzioni della finestra

L'avvio passa `private_mode=False` e `storage_path=WEBVIEW_STORAGE_DIR` a
PyWebView. La cartella viene creata senza cancellare i dati gia presenti ed e
esclusa da Git. Cookie e `localStorage` appartengono alla finestra, non al browser
esterno; i dati web sono inoltre separati per origine (host e porta). Cambiare
host o porta puo quindi far apparire vuoto il `localStorage` della nuova origine.
Tema e lingua continuano a essere salvati nel database SQLite.

Il download backup usa ancora `/api/backup/download`, con nome datato generato
dal backend. `ALLOW_DOWNLOADS=True` abilita la gestione del download da parte del
renderer; su Windows/WebView2 e prevista la finestra di scelta della destinazione.
Non viene esposto un endpoint che accetta percorsi di file dal frontend. Il
backup scaricato contiene soltanto SQLite, non il profilo WebView o i file lingua.

`OPEN_EXTERNAL_LINKS_IN_BROWSER=True` mantiene i link aperti con `window.open()`
nel browser esterno; la pagina GitHub non deve sostituire Planner nella finestra.
La copia dell'indirizzo MCP resta basata su `navigator.clipboard.writeText()` e
sui toast esistenti, senza un bridge Python-JavaScript.

I test automatici verificano le opzioni e i percorsi, non il renderer: salvataggio
e annullamento download, link, clipboard, persistenza effettiva e ripresa dalla
sospensione vanno ancora provati nella finestra nativa (vedi `TODO.md`). Non e
garantita la trasferibilita del profilo WebView tra sistemi o PC diversi: il DB
resta la fonte dei dati dell'applicazione.

## Aggiornare l'app

Non esiste un aggiornamento automatico: l'app segnala solo che e disponibile una
nuova release su GitHub.

Per aggiornare, sostituisci l'eseguibile e `_internal/` con quelli della nuova
versione e conserva `data/` (contiene il database). Conviene scaricare prima un
backup dalle Impostazioni.

Anche `locales/` puo essere conservata, ma in quel caso eventuali nuove chiavi di
traduzione della nuova versione non vengono aggiunte ai file esistenti: per
riceverle elimina i file lingua non modificati, cosi vengono ricopiati al
prossimo avvio.

Il database esistente viene aggiornato automaticamente dalle migrazioni incluse
nella nuova versione, conservando i dati. La versione dello schema e registrata
in `PRAGMA user_version`, separatamente dalla versione dell'app. Prima di migrare
viene salvato un backup in `data/migration_backups/`.

Se una migrazione fallisce, la transazione corrente viene annullata e il server
non parte. Anche un database con schema piu recente di quello supportato impedisce
l'avvio: non usare una vecchia build per fare downgrade. Per dettagli e procedure
vedi `DATABASE.md` e `TROUBLESHOOTING.md`.

## Regola importante

Con `--onedir` non bisogna copiare solo `PlannerApp.exe`.

Va copiata tutta la cartella:

```text
PlannerApp/
  PlannerApp.exe
  _internal/
  data/
  locales/
```
