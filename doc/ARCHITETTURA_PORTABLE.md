# Architettura Portable

L'app puo essere eseguita come cartella portable generata con PyInstaller in modalita `--onedir`.

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

- `_internal/`: contiene runtime Python, librerie, `schema.sql`, frontend buildato e file inclusi da PyInstaller. Non va modificata manualmente.
- `data/`: contiene il database SQLite creato vicino all'eseguibile al primo avvio.
- `locales/`: contiene i file lingua esterni copiati al primo avvio e modificabili dall'utente.

## Percorsi principali

I percorsi sono definiti in `backend/config.py`.

In sviluppo:

```text
DB_PATH -> backend/db/planner.db
LOCALES_DIR -> backend/locales
FRONTEND_DIST_DIR -> frontend/dist
```

In PyInstaller:

```text
DB_PATH -> PlannerApp/data/planner.db
LOCALES_DIR -> PlannerApp/locales
FRONTEND_DIST_DIR -> _internal/frontend_dist
```

## Avvio dell'app

Quando l'eseguibile parte:

1. crea le cartelle runtime `data/` e `locales/` se non esistono;
2. copia i file lingua default in `locales/` solo se mancano;
3. crea il database SQLite se non esiste;
4. avvia il backend locale su `127.0.0.1:8000` (modificabile con le variabili d'ambiente `HOST` e `PORT`);
5. apre automaticamente il browser dopo circa un secondo;
6. serve il frontend React buildato, le API sotto `/api` e il server MCP sotto `/mcp`.

## Shutdown automatico

Il frontend invia un heartbeat al backend ogni 10 secondi.

Se il backend non riceve heartbeat per circa 60 secondi in produzione, presume che la UI sia stata chiusa e arresta il server.

Endpoint coinvolto:

```text
POST /api/app/heartbeat
```

Conseguenze da conoscere:

- il server MCP funziona solo finche la UI resta aperta nel browser: un client AI
  usato senza la scheda di Planner aperta perde la connessione dopo circa un minuto;
- i browser rallentano i timer delle schede in background, quindi una scheda nascosta
  a lungo potrebbe non inviare heartbeat abbastanza spesso (vedi `TODO.md`).

In sviluppo il controllo dell'heartbeat e disattivato.

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

Il database esistente non viene aggiornato se la nuova versione modifica lo schema
(vedi `DATABASE.md`).

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
