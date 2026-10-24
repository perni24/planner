# Troubleshooting

## L'eseguibile si apre e si chiude subito

Avvialo da terminale per leggere l'errore:

```powershell
cd backend\dist\PlannerApp
.\PlannerApp.exe
```

Gli errori gestiti dal coordinatore desktop mostrano un dialogo su Windows e
salvano i dettagli in `PlannerApp/data/logs/planner.log` (in sviluppo
`backend/db/logs/planner.log`). Se la cartella non e scrivibile resta la console.
Gli errori del bootloader PyInstaller, precedenti all'avvio Python, richiedono
ancora l'avvio da terminale e non passano dal gestore desktop.

## WebView2 mancante o non funzionante su Windows

Planner usa Microsoft Edge WebView2 Runtime Evergreen, preinstallato in Windows 11.
Su una normale installazione di Windows 11 non occorre installarlo separatamente.
La portable non include il motore completo ne un installer del runtime; il solo
browser Microsoft Edge non lo sostituisce.

Se l'errore di avvio o il log indica un problema WebView2:

1. Chiudi Planner e leggi i dettagli in `data/logs/planner.log` nella cartella portable.
2. Se il runtime manca o e danneggiato, usa il [download ufficiale Microsoft](https://developer.microsoft.com/en-us/microsoft-edge/webview2/): il bootstrapper Evergreen scarica il runtime adatto al PC; lo standalone installer permette l'installazione offline.
3. Completa l'installazione o il ripristino e riavvia Planner, senza ricompilarlo.

Non disinstallare WebView2 dal PC principale per provarne l'assenza: altre app
potrebbero dipenderne. Un eventuale test senza runtime va eseguito su una macchina
virtuale o un PC di prova ed e una verifica aggiuntiva di robustezza.
Riferimento: [distribuzione WebView2](https://learn.microsoft.com/en-us/microsoft-edge/webview2/concepts/distribution).

## Errore `Failed to load Python DLL`

Succede quando viene copiato solo `PlannerApp.exe` senza la cartella `_internal`.

Con PyInstaller `--onedir` devi copiare tutta la cartella:

```text
PlannerApp/
  PlannerApp.exe
  _internal/
```

## Porta 8000 gia occupata

Se Planner segnala che lo spegnimento sta impiegando troppo tempo, attende ancora
la pulizia sicura del backend: non aprire una seconda istanza e non sostituire il
DB in uso. Controlla il log. I timeout interrompono cooperativamente SQLite e i
backup, ma non possono sbloccare I/O nativo fermo nel sistema operativo.

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

Attiva l'ambiente virtuale e installa le dipendenze di sviluppo e build:

```powershell
cd backend
python -m pip install -r requirements-dev.txt
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

Il dizionario deve essere un oggetto piatto non vuoto con valori stringa. I
codici ammessi sono, per esempio, `it`, `en` e `pt-BR`. File malformati o
illeggibili non compaiono nella lista; un cambio verso una lingua non
disponibile viene rifiutato con `400`, senza modificare la preferenza salvata.

Se la lingua gia scelta non e piu utilizzabile, il backend prova la sua copia
inclusa nell'app, poi italiano e inglese. Questo fallback non ripara i file e
non cambia la preferenza nel DB: per recuperare la lingua personalizzata occorre
correggere il relativo JSON. Se mancano tutte le copie utilizzabili, il
caricamento restituisce `503`; conserva una copia dei file personalizzati prima
di ripristinare quelli di default. Per dettagli vedi `I18N.md`.

## Linux: impossibile caricare il plugin Qt `xcb`

Se compare `Could not load the Qt platform plugin "xcb"`, il plugin puo essere
presente ma una sua libreria di sistema puo mancare. La portable include Qt e
QtWebEngine, non tutte le librerie del sistema operativo.

Avvia Planner da un terminale nella cartella estratta:

```bash
QT_DEBUG_PLUGINS=1 ./PlannerApp
ldd _internal/PyQt6/Qt6/plugins/platforms/libqxcb.so
```

Cerca `not found` nell'output e installa la libreria indicata usando il gestore
pacchetti della distribuzione. Su Ubuntu 22.04, per esempio, `libxcb-cursor.so.0`
corrisponde a `libxcb-cursor0` e `libxkbcommon-x11.so.0` a `libxkbcommon-x11-0`.
Lo step `Install Linux desktop dependencies` nel workflow elenca i pacchetti
previsti per quella base; i nomi possono differire sulle altre distribuzioni.
Non installare GTK/WebKit per aggirare l'errore: Planner usa Qt/PyQt6.

Estrai l'archivio TAR.GZ mantenendo tutta la cartella, inclusi `_internal/`,
permessi e collegamenti simbolici. Esegui l'app come utente normale in una
sessione desktop, non con `sudo`; non disabilitare la sandbox Chromium per
risolvere un errore di dipendenze. La verifica con Wayland e X11 resta distinta
dal controllo dei file della build.
Riferimento: [dipendenze dei plugin Qt su Linux](https://doc.qt.io/qt-6/linux-requirements.html).

## macOS blocca l'app

Le release attuali non includono macOS. Il pacchetto macOS della `v0.1.0` non e
firmato ne notarizzato e Gatekeeper lo blocca; da macOS 15 il tasto destro ->
`Apri` non basta piu. Per una prova, dal Terminale nella cartella estratta:

```bash
xattr -dr com.apple.quarantine .
chmod +x PlannerApp
./PlannerApp
```

Il primo comando toglie la quarantena anche alle librerie in `_internal/`, il
secondo ripristina il permesso di esecuzione perso nello zip. Il pacchetto contiene
solo codice arm64: su un Mac Intel non parte ("Bad CPU type in executable").
Dettagli e lavoro necessario per il supporto in `SVILUPPI_FUTURI.md`.
