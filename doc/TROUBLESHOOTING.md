# Troubleshooting

## L'eseguibile si apre e si chiude subito

Avvialo da terminale per leggere l'errore:

```powershell
cd backend\dist\PlannerApp
.\PlannerApp.exe
```

Se lo avvii con doppio click, la finestra puo chiudersi prima di mostrare il messaggio.

## Errore `Failed to load Python DLL`

Succede quando viene copiato solo `PlannerApp.exe` senza la cartella `_internal`.

Con PyInstaller `--onedir` devi copiare tutta la cartella:

```text
PlannerApp/
  PlannerApp.exe
  _internal/
```

## Porta 8000 gia occupata

Chiudi eventuali server gia avviati:

```text
python main.py
npm run dev
PlannerApp.exe
```

Il backend usa:

```text
http://127.0.0.1:8000
```

## Errore `Invalid host header`

Il backend accetta solo richieste rivolte a `127.0.0.1` o `localhost` (protezione
contro il DNS rebinding). Apri l'app da:

```text
http://127.0.0.1:8000
http://localhost:8000
```

Se hai impostato la variabile `HOST` con un nome o un IP specifico, quel valore
viene accettato. Con `HOST=0.0.0.0` restano accettati solo i nomi locali, quindi
l'app non e raggiungibile da altri dispositivi della rete. Anche `HOST=::1` (IPv6)
non e supportato.

## `npm` non trovato durante la build

Verifica che Node.js sia installato e disponibile nel PATH:

```powershell
npm --version
```

Su Windows lo script usa `npm.cmd` automaticamente.

## PyInstaller non trovato

Installa le dipendenze backend:

```powershell
cd backend
pip install -r requirements.txt
```

Poi rilancia:

```powershell
python build_portable.py
```

## Il DB non viene creato

Controlla che l'app abbia permessi di scrittura nella cartella dove si trova l'eseguibile.

In modalita portable il DB viene creato qui:

```text
PlannerApp/data/planner.db
```

## Errore durante una migrazione del database

Avvia l'app da terminale per leggere il nome dello script e la causa dell'errore.
L'avvio si interrompe e la migrazione corrente viene annullata; quelle precedenti
gia confermate non vengono ripetute al prossimo avvio.

Conserva il database originale e controlla permessi di scrittura e spazio libero.
Se manca uno script, ricopia l'intera cartella `_internal/` dalla build: include
anche `db/migrations/`. Non eliminare il DB e non modificare manualmente
`PRAGMA user_version` per aggirare l'errore.

Prima dell'aggiornamento viene salvato un backup in:

```text
PlannerApp/data/migration_backups/
```

In sviluppo si trova in `backend/db/migration_backups/`. Per un ripristino manuale
chiudi prima tutti i processi dell'app, conserva una copia del DB attuale e copia
il backup scelto al posto di `planner.db`. Il prossimo avvio tentera nuovamente
le migrazioni mancanti: occorre prima risolvere la causa dell'errore.

Se compare `Unsupported database schema version`, usa una versione dell'app che
supporti quello schema. Non e disponibile un downgrade automatico.

## Le lingue non cambiano

Controlla che i file lingua siano presenti in:

```text
PlannerApp/locales/
```

E che il JSON sia valido. I file JSON non supportano commenti.

## macOS blocca l'app

Le build PyInstaller non firmate possono essere bloccate da Gatekeeper. Per i test
locali apri l'app dal menu contestuale con `Apri`. Per una distribuzione pubblica
senza avvisi servono firma e notarizzazione Apple.
