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
  locales/
    it.json
    en.json
```

Su Linux e macOS il file eseguibile non avra estensione `.exe`, ma la logica resta la stessa.

## Cartelle tecniche

- `_internal/`: contiene runtime Python, librerie, `schema.sql`, `db/migrations/`, frontend buildato e file inclusi da PyInstaller. Non va modificata manualmente.
- `data/`: contiene il database SQLite creato vicino all'eseguibile al primo avvio. `migration_backups/` viene aggiunta quando un database esistente deve essere aggiornato.
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
```

In PyInstaller:

```text
DB_PATH -> PlannerApp/data/planner.db
MIGRATIONS_DIR -> _internal/db/migrations
MIGRATION_BACKUPS_DIR -> PlannerApp/data/migration_backups
LOCALES_DIR -> PlannerApp/locales
FRONTEND_DIST_DIR -> _internal/frontend_dist
```

## Avvio dell'app

Quando l'eseguibile parte:

1. crea le cartelle runtime `data/` e `locales/` se non esistono;
2. copia i file lingua default in `locales/` solo se mancano;
3. crea il database SQLite se nuovo o vuoto, oppure applica le migrazioni mancanti dopo un backup automatico;
4. verifica la presenza del frontend compilato e avvia Uvicorn in un thread separato su `127.0.0.1:8000`, senza reload (host e porta restano configurabili);
5. attende che quel server sia pronto, con un timeout di 15 secondi, senza interrogare altri servizi eventualmente presenti sulla stessa porta;
6. apre PyWebView nel thread principale all'URL configurato in `APP_URL`; su Windows usa WebView2;
7. serve il frontend React buildato, le API sotto `/api` e il server MCP sotto `/mcp` finche la finestra resta aperta.

L'importazione di `main.py` non prepara il runtime e non avvia server o finestra.
Frontend mancante, porta occupata, timeout ed errori del renderer impediscono
l'avvio o richiedono lo stop del backend e vengono propagati alla console.

## Chiusura della finestra

Chiudere la finestra richiede l'arresto di Uvicorn e attende il thread backend.
Minimizzare la finestra non lo interrompe, quindi anche MCP resta attivo.

Uvicorn concede 5 secondi alle richieste in corso; il coordinatore attende fino
a 10 secondi. Le code SSE vengono chiuse alla disconnessione e nel lifespan per
sbloccare le letture ancora pendenti nell'executor. I timeout sono definiti in
`config.py`.

Se il thread non termina entro il timeout viene segnalato un errore, senza
ucciderlo o troncare le operazioni: puo quindi restare attivo. La gestione
completa dei blocchi, delle scritture e delle sessioni MCP durante lo spegnimento
resta aperta in `TODO.md`, come la gestione della finestra dopo uno stop via API.

Il monitor heartbeat non viene piu avviato. L'endpoint `POST /api/app/heartbeat`
e le chiamate del frontend ogni 10 secondi sono ancora presenti, ma non decidono
quando spegnere il server; saranno rimossi in un passaggio successivo.

Download del backup nella finestra e persistenza del profilo WebView non sono
ancora configurati e restano da verificare nel passaggio dedicato.

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
