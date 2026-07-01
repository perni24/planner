# Architettura Portable

L'app puo essere eseguita come cartella portable generata con PyInstaller in modalita `--onedir`.

## Struttura dell'output

Dopo la build locale o GitHub Actions, l'output principale e:

```text
backend/dist/PlannerApp/
  PlannerApp.exe
  _internal/
  data/
    planner.db
  locales/
    it.json
    en.json
```

Su Linux e macOS il file eseguibile non avra estensione `.exe`, ma la logica resta la stessa.

## Cartelle tecniche

- `_internal/`: contiene runtime Python, librerie, `schema.sql`, frontend buildato e file inclusi da PyInstaller. Non va modificata manualmente.
- `data/`: contiene il database SQLite creato vicino all'eseguibile.
- `locales/`: contiene i file lingua esterni modificabili dall'utente.

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
4. avvia il backend locale su `127.0.0.1:8000`;
5. apre automaticamente il browser in produzione;
6. serve il frontend React buildato dal backend.

## Shutdown automatico

Il frontend invia un heartbeat al backend ogni 10 secondi.

Se il backend non riceve heartbeat per circa 60 secondi in produzione, presume che la UI sia stata chiusa e arresta il server.

Endpoint coinvolto:

```text
POST /api/app/heartbeat
```

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
