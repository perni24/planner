# Troubleshooting

Il primo posto dove guardare e il log: `PlannerApp/data/logs/planner.log` nella
portable, `backend/db/logs/planner.log` in sviluppo. Gli errori che avvengono prima
dell'avvio di Python si vedono solo avviando l'eseguibile da un terminale.

## L'app si apre e si chiude subito

Avviala da terminale per leggere l'errore (`.\PlannerApp.exe` su Windows,
`./PlannerApp` su Linux) e controlla il log.

`Failed to load Python DLL` indica che e stato copiato solo l'eseguibile: serve
l'intera cartella `PlannerApp`, compresa `_internal/`.

## Windows: `Failed to resolve Python.Runtime.Loader.Initialize`

.NET Framework non carica le DLL della portable perche lo ZIP scaricato ha il segno
"proveniente da Internet". Le build attuali lo risolvono con `PlannerApp.exe.config`
accanto all'eseguibile. Se il file manca (build precedenti), sblocca i file dalla
cartella estratta e riavvia:

```powershell
Get-ChildItem -Recurse | Unblock-File
```

oppure, prima di estrarre: tasto destro sullo ZIP -> Proprieta -> "Annulla blocco".
Al primo avvio SmartScreen puo bloccare l'eseguibile non firmato: "Ulteriori
informazioni" -> "Esegui comunque".

## Windows: WebView2 mancante o danneggiato

WebView2 Runtime e preinstallato in Windows 11 e non e incluso nella portable; il
browser Edge non lo sostituisce. Se il log indica un problema WebView2, installalo
o ripristinalo dal [download ufficiale Microsoft](https://developer.microsoft.com/en-us/microsoft-edge/webview2/)
e riavvia Planner.

## Linux: l'app si chiude con `GLIBCXX_... not found`

Errori EGL/OpenGL seguiti da `libstdc++.so.6: version GLIBCXX_3.4.31 not found`:
il pacchetto contiene il runtime C++ di Ubuntu 22.04, piu vecchio di quello
richiesto dai driver grafici. Le build attuali lo rimuovono; con una build
precedente elimina `_internal/libstdc++.so.6` e `_internal/libgcc_s.so.1`.

## Linux: impossibile caricare il plugin Qt `xcb`

Manca una libreria di sistema del plugin. Dalla cartella estratta:

```bash
QT_DEBUG_PLUGINS=1 ./PlannerApp
ldd _internal/PyQt6/Qt6/plugins/platforms/libqxcb.so | grep "not found"
```

e installa le librerie indicate (su Ubuntu, per esempio, `libxcb-cursor0` e
`libxkbcommon-x11-0`; l'elenco della CI e nello step `Install Linux desktop
dependencies`). Estrai il TAR.GZ completo, mantenendo permessi e collegamenti, ed
esegui l'app come utente normale, non con `sudo`.
Riferimento: [requisiti di Qt su Linux](https://doc.qt.io/qt-6/linux-requirements.html).

## Porta 8000 gia occupata

E aperta un'altra istanza o un server di sviluppo (`python main.py`,
`PlannerApp`). Chiudila; se Planner segnala che l'arresto precedente e lento,
attendi che il processo termini prima di riavviare.

## Errore `Invalid host header`

Il backend accetta solo `127.0.0.1` e `localhost` (protezione contro il DNS
rebinding). Con la variabile `HOST` impostata a un nome o IP specifico viene
accettato anche quello; `0.0.0.0` non rende l'app raggiungibile dalla rete e IPv6
non e supportato.

## Errore durante una migrazione del database

L'avvio si interrompe e la migrazione corrente viene annullata; il log indica lo
script e la causa. Controlla permessi di scrittura e spazio libero; se manca uno
script, ricopia `_internal/` dalla build. Non eliminare il DB e non modificare
`PRAGMA user_version`.

Prima di migrare viene salvato un backup in `data/migration_backups/`. Per
ripristinarlo chiudi l'app, conserva una copia del DB attuale e copia il backup al
posto di `planner.db`. `Unsupported database schema version` indica un database
creato da una versione piu recente dell'app: usa quella versione.

## Il DB non viene creato

L'app deve poter scrivere nella propria cartella: il DB e
`PlannerApp/data/planner.db`.

## Le modifiche al frontend non compaiono

`python main.py` usa la build in `frontend/dist`, che non e versionata: dopo una
modifica o un `git pull` esegui `npm run build` (prima `npm ci` se manca TypeScript
o sono cambiate le dipendenze) e riavvia. Una portable usa il frontend incluso nel
suo `_internal/`: serve una nuova build.

## Finestra bianca in sviluppo

Una finestra bianca intitolata `Web Inspector - Planner` e l'inspector di Qt, non
Planner: chiudila. Con `DEBUG` attivo (default in sviluppo) puoi fare il debug da
un browser Chromium su `http://127.0.0.1:8228` (la porta effettiva e nel terminale);
su Windows con tasto destro -> Ispeziona. Quella porta accetta connessioni da
qualsiasi origine: non usare `DEBUG=1` nelle build distribuite. Per avviare senza
debug: `DEBUG=0 python main.py`.

Se e bianca la finestra `Planner`, controlla che `frontend/dist` esista e il log.

## Le lingue non cambiano

I file in `PlannerApp/locales/` devono essere JSON validi (oggetto piatto con valori
stringa, senza commenti): quelli non validi non compaiono nell'elenco. Se la lingua
scelta non e piu utilizzabile, il backend usa la copia inclusa o italiano/inglese,
senza modificare file o preferenza. Dettagli in `I18N.md`.

## `npm` o PyInstaller non trovati durante la build

Verifica `npm --version` (Node.js nel PATH) e installa le dipendenze di build nel
venv attivo con `python -m pip install -r requirements-dev.txt`.

## macOS blocca l'app

macOS non e distribuito. Per provare il pacchetto `v0.1.0`, non firmato, dalla
cartella estratta:

```bash
xattr -dr com.apple.quarantine .
chmod +x PlannerApp
./PlannerApp
```

Il pacchetto e solo arm64 (non parte sui Mac Intel). Vedi `SVILUPPI_FUTURI.md`.
