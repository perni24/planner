# Guida allo Sviluppo - Planner App

Segui questi passaggi per avviare il progetto in modalita sviluppo.

## 1. Backend (Python + Starlette)
Il backend gestisce il database SQLite e le API.

### Prima configurazione

Usa Python 3.14, aggiornato a una patch recente della serie `3.14.x`.
GitHub Actions compila le release Windows e Linux con la serie `3.14`;
sviluppo locale e dipendenze devono restare compatibili con questa serie.

Prima di creare il venv, verifica che `python --version` mostri `3.14.x`.
Un venv gia creato con un'altra serie Python va ricreato con l'interprete 3.14:
aggiornare il workflow non cambia l'interprete del venv locale.

```bash
cd backend
python -m venv .venv
```

Usa il nome `.venv`: `build_portable.py` cerca PyInstaller in `backend/.venv/`.
Se hai gia un ambiente chiamato `venv`, adatta i percorsi di attivazione; lo script
di build usa l'interprete corrente quando non trova PyInstaller in `.venv`.

### Avvio del server

```bash
cd backend
```

Attiva l'ambiente virtuale su Windows:

```powershell
.\.venv\Scripts\Activate.ps1
```

Attiva l'ambiente virtuale su Linux/macOS:

```bash
source .venv/bin/activate
```

Installa le dipendenze di sviluppo e build (incluse quelle del backend):

```bash
python -m pip install -r requirements-dev.txt
```

`requirements.txt` contiene solo le dipendenze di runtime (Starlette, Uvicorn,
MCP e PyWebView). Su Linux installa anche Qt (QtPy, PyQt6 e PyQt6-WebEngine), il
motore della finestra desktop: il download e di alcune centinaia di MB e la cartella
`PyQt6` occupa circa 500 MB nell'ambiente virtuale. Su Windows e macOS queste righe
vengono ignorate.
`requirements-dev.txt` lo include tramite `-r requirements.txt` e aggiunge
PyInstaller e Ruff. Per avviare l'app senza gli strumenti di lint o build, usa
`python -m pip install -r requirements.txt`.

Prima dell'avvio desktop prepara il frontend, dalla cartella `frontend/`:

```bash
npm install
npm run build
```

Poi, da `backend/` con il venv attivo, avvia l'app:

```bash
python main.py
```

Si apre una finestra PyWebView con il frontend compilato; il backend resta
disponibile su:

```text
http://127.0.0.1:8000
```

Su Windows e richiesto WebView2 Runtime Evergreen, preinstallato in Windows 11
(vedi `TROUBLESHOOTING.md` se manca o non funziona).
Uvicorn lavora in un thread separato senza
reload, anche se `RELOAD` e impostato nell'ambiente. Le modifiche Python
richiedono di chiudere e riavviare l'app; per vedere quelle React nella finestra
occorre una nuova build e un ricaricamento della pagina o un riavvio dell'app.
Gli errori di avvio vengono registrati in `backend/db/logs/planner.log` e
mostrati tramite dialogo nativo su Windows; se la GUI non e disponibile sulle
altre piattaforme resta la console. Il file ruota a circa 1 MB con tre copie.
Un crash del backend dopo l'apertura segnala l'errore e chiude la finestra;
lo shutdown via API la chiude normalmente, senza allarme.

La finestra resta aperta durante l'uso del backend/MCP; chiuderla ne richiede
l'arresto. Minimizzarla non interrompe il backend. Non viene piu aperto
automaticamente il browser e non servono richieste periodiche del frontend per
mantenere attivo il backend.

Il profilo PyWebView usa `backend/db/webview/` in sviluppo e `data/webview/`
nella portable, con modalita privata disattivata. Non e condiviso con Chrome o
Edge ed e escluso da Git. I download sono abilitati e i link esterni devono aprire
il browser predefinito, senza navigare via da Planner.

### Verifiche manuali delle funzioni desktop

1. Dalla console della finestra in sviluppo, salva una chiave di prova con `localStorage.setItem('planner-profile-test', 'ok')`. Chiudi e riavvia l'app mantenendo host e porta, verifica `localStorage.getItem('planner-profile-test')`, poi rimuovila con `localStorage.removeItem('planner-profile-test')`. La persistenza di tema e lingua non basta per questa prova: quei valori sono gia nel DB.
2. Dalle Impostazioni scarica un backup, scegli una destinazione, controlla il nome datato e verifica il DB scaricato. Ripeti annullando il dialogo: Planner deve restare utilizzabile.
3. Se e disponibile un aggiornamento, apri la pagina di download: deve comparire nel browser esterno, non al posto di Planner.
4. Copia l'indirizzo MCP e incollalo in un editor esterno; controlla che il toast di esito corrisponda al risultato.
5. Cambia tema e lingua, riavvia, poi verifica modifiche MCP e aggiornamenti SSE anche durante minimizzazione e dopo sospensione/ripresa del PC.

Queste prove richiedono il renderer nativo di ogni sistema supportato. I test con
finestra simulata verificano solo configurazione e coordinamento del backend.

Il database di sviluppo viene creato automaticamente in:

```text
backend/db/planner.db
```

## 2. Frontend (React + Vite)
Il frontend e l'interfaccia utente dell'applicazione. Per svilupparlo con hot
reload puoi avviare Vite in un secondo terminale e aprirlo nel browser, mantenendo
aperta la finestra Planner per tenere attivo il backend. La finestra PyWebView
continua a usare il frontend compilato, non il server Vite.

```bash
cd frontend
npm install
npm run dev
```

Vite fornira un indirizzo simile a:

```text
http://localhost:5173
```

## 3. Come testare la comunicazione
Per verificare che il frontend possa parlare con il backend:

1. Assicurati che backend e frontend siano accesi.
2. Apri il link del frontend nel browser.
3. Apri la console del browser con F12.
4. Esegui questo test:

```javascript
fetch('/api/health')
  .then((res) => res.json())
  .then((data) => console.log('Risposta Backend:', data))
  .catch((err) => console.error('Errore connessione:', err));
```

La richiesta passa dal proxy di Vite, come quelle dell'app. Se vedi questo
risultato, il backend risponde correttamente:

```text
Risposta Backend: {status: "online"}
```

Per provare le singole API senza frontend puoi usare i file `backend/test/*.http`
(estensione REST Client di VS Code o simili).

### Provare il server MCP
Con il backend acceso, collega un client AI compatibile con MCP usando il
trasporto Streamable HTTP e l'indirizzo:

```text
http://127.0.0.1:8000/mcp/
```

Il server MCP resta disponibile finche la finestra Planner e aperta, anche se
minimizzata. La sua chiusura richiede l'arresto del backend; non sono previsti
timer di presenza del frontend (vedi `ARCHITETTURA_PORTABLE.md`).

## 4. Controlli di qualita
Prima di un commit esegui i linter.

Frontend:

```bash
cd frontend
npm run lint
npm run typecheck
```

`typecheck` esegue `tsc --noEmit`: controlla i file `.ts` e `.tsx` in `src/`
con le regole strict di `tsconfig.json`, senza produrre file JavaScript.
I componenti `.jsx` e gli altri file `.js` restano esclusi da questo controllo;
ESLint continua a verificarli. I tipi non validano le risposte JSON a runtime.

Anche `npm run build` esegue il controllo dei tipi prima di Vite e si interrompe
se trova errori. Vale anche per le build portable locali e in GitHub Actions.

Backend (con l'ambiente virtuale attivo):

```bash
cd backend
ruff check .
```

Test automatici di migrazioni, download backup, repository, avvio ed eventi (da `backend/`, con l'ambiente virtuale attivo):

```bash
python -m unittest discover -s test -p test_*.py -v
```

I test usano database temporanei: non modificano `backend/db/planner.db`.
`test/test_id_validation.py` verifica la validazione condivisa degli ID, le
route REST e gli schemi MCP strict: booleani, float e interi fuori intervallo
sono rifiutati prima delle query. Le chiamate ai repository sono simulate.
`test/test_settings_validation.py` verifica tema, colori, JSON delle impostazioni
e dizionari lingua, anche mancanti o corrotti, con fallback senza sovrascritture;
una prova su DB temporaneo conferma che le richieste non valide non lo cambiano.
Coprono creazione, aggiornamento delle vecchie release, comportamento dei trigger,
rollback e riavvio dopo errori. I test del backup simulano richieste ASGI e
verificano integrita della copia, WAL, modifiche durante l'invio, download
simultanei e pulizia dei temporanei anche in caso di errore o cancellazione.
I test dei repository verificano la chiusura delle connessioni, la persistenza
delle scritture REST/MCP e il rollback delle operazioni bulk fallite a meta.
Le altre API vengono ancora provate manualmente.
`test/test_startup.py` verifica il ciclo desktop, i thread, i timeout e gli errori
con una finestra simulata e server su porte TCP locali temporanee, anche con
scritture REST/MCP in corso durante lo stop. Verifica inoltre percorsi del profilo
sviluppo/portable, creazione senza sovrascrittura e opzioni di download e browser.
`test/test_events.py` verifica la chiusura delle code SSE e lo sblocco delle letture.
`test/test_app_routes.py` verifica la rimozione del vecchio endpoint heartbeat e
il mantenimento di shutdown, versione e controllo aggiornamenti, senza rete esterna.
`test/test_desktop_errors.py` verifica log rotanti, traduzioni e fallback senza
aprire dialoghi nativi; i file di log di prova sono temporanei.
`test/test_operation_control.py` verifica cancellazione cooperativa, timeout dei
lock SQLite, backup bloccati, rollback e ripetizione delle richieste di stop.
`test/test_build_portable.py` verifica le opzioni Windows/Linux, la selezione di
PyQt6, le risorse richieste, le licenze e il rifiuto di sovrascrivere cartelle con
dati runtime. Questi test simulano la compilazione e non avviano l'eseguibile.
`test/test_release_workflow.py` esegue il codice Python del controllo versione e
dei permessi nell'archivio TAR.GZ su file temporanei; non esegue GitHub Actions.
`test/test_build_licenses.py` verifica copia byte per byte dei testi upstream,
versioni registrate e rifiuto di materiali mancanti, vuoti o modificati.
Non vengono aperte finestre native: la prova manuale di PyWebView resta necessaria.
I linter e i test backend restano manuali. GitHub Actions esegue il controllo
TypeScript come parte della build frontend.

Per modifiche allo schema segui la procedura in `DATABASE.md`: occorre aggiornare
sia `schema.sql` sia le migrazioni per i database esistenti.

## 5. Build portable locale
Per creare l'app portable localmente, con l'ambiente virtuale attivo e le
dipendenze di `requirements-dev.txt` installate:

```bash
cd backend
python build_portable.py
```

Lo script esegue:

```text
npm run build
pyinstaller --onedir
```

L'output viene creato in:

```text
backend/dist/PlannerApp
```

Su Windows l'eseguibile sara:

```text
backend/dist/PlannerApp/PlannerApp.exe
```

Con la modalita `--onedir` devi copiare tutta la cartella `PlannerApp`, non solo il file eseguibile.

### Build Windows desktop

Su Windows lo script mantiene la console diagnostica, disabilita UPX e raccoglie
esplicitamente le risorse di `webview`, inclusi i JavaScript del bridge. Le DLL
WebView2 e Python.NET sono raccolte dagli hook installati. Qt, GTK, CEF e i
backend per gli altri sistemi vengono esclusi soltanto dalla build Windows.
Il runtime WebView2 Evergreen e preinstallato in Windows 11: normalmente non
richiede interventi dell'utente. Resta un componente di sistema e non viene
incluso come motore completo o installer nella portable. Il collegamento al
download Microsoft in `TROUBLESHOOTING.md` serve per i casi di runtime mancante
o danneggiato. Il browser Edge da solo non sostituisce il runtime.
La prova con runtime assente e una verifica aggiuntiva di robustezza da svolgere
in un ambiente isolato, non un prerequisito per l'uso normale su Windows 11.

Prima della compilazione vengono controllate le licenze. Al termine vengono
verificati frontend, schema, migrazioni, lingue, licenze e, su Windows, i
JavaScript e le DLL principali di WebView2/Python.NET. Un pacchetto incompleto
fa fallire la build: questi controlli non sostituiscono la prova di avvio su un
PC pulito.

Se la cartella di destinazione contiene `data/`, `locales/` esterne o database
alla radice, la build si ferma senza cancellarli. Non compilare sopra una
portable gia usata. Per scegliere un'altra cartella di output, da `backend/`:

```bash
python build_portable.py --dist-dir dist/windows
```

In questo caso il risultato e `backend/dist/windows/PlannerApp/`.
Le opzioni di esclusione Windows non vengono applicate a Linux.

### Build Linux desktop

Compila su Linux: la build Windows non puo generare l'eseguibile Linux.
Il workflow usa `ubuntu-22.04` x64 come base e installa prima le librerie di
sistema X11/XCB, OpenGL/EGL, NSS, audio e D-Bus necessarie a Qt. L'elenco e nello
step `Install Linux desktop dependencies`; per una build locale su Ubuntu 22.04
prepara le stesse dipendenze oltre a quelle di `requirements-dev.txt`.
Non occorre installare WebKitGTK o un secondo binding Qt.

Lo script imposta `QT_API=pyqt6` per PyInstaller e include esplicitamente il
renderer Qt, QtPy, QtWebEngine e QtWebChannel; anche `config.py` seleziona PyQt6
all'avvio Linux. Vengono esclusi GTK, gli altri binding Qt e i renderer di altri
sistemi, senza escludere moduli QtQuick/QML che QtWebEngine potrebbe richiedere.
Gli hook PyInstaller raccolgono librerie, plugin, processo Chromium e risorse.
La verifica finale richiede `QtWebEngineProcess`, `libQt6WebEngineCore.so.6`,
plugin XCB, risorse Chromium, ICU, dizionario en-US e JavaScript PyWebView; su
Linux controlla inoltre i permessi di esecuzione dell'app e del processo helper.

### Materiali di licenza Linux

`THIRD_PARTY_NOTICES.md` distingue le icone, QtPy (MIT), i binding
PyQt6/PyQt6-WebEngine (GPLv3) e le librerie native Qt delle wheel (LGPLv3).
QtWebEngine incorpora anche Chromium e altri componenti con licenze proprie:
questa sintesi non ne sostituisce gli avvisi individuali.

La build Linux passa `--copy-metadata` per QtPy, PyQt6, PyQt6-sip,
PyQt6-WebEngine, PyQt6-Qt6 e PyQt6-WebEngine-Qt6. Dopo PyInstaller,
`build_licenses.py` legge questi metadati dal bundle e copia senza modifiche
i file LICENSE, COPYING, NOTICE e COPYRIGHT presenti in `licenses/<pacchetto>/`.
Non usa le versioni dell'interprete esterno che avvia lo script, che potrebbero
essere diverse da quelle del venv usato per PyInstaller.

`licenses/manifest.json` registra per ogni componente versione effettiva,
collegamento alla release upstream, percorsi e hash SHA-256 dei testi copiati.
La build fallisce se manca un componente, un testo principale di licenza o se
il controllo finale trova file mancanti o alterati. Windows non raccoglie Qt
e non richiede questa cartella. Il TAR.GZ include automaticamente `licenses/`.

Il manifest non e un inventario completo di tutte le dipendenze e non e una
distribuzione dei sorgenti. In particolare, i LICENSE delle wheel non
comprendono tutti gli avvisi delle componenti Chromium. Prima della pubblicazione
Linux occorre ancora raccogliere e verificare gli avvisi Qt/Chromium e l'accesso
ai sorgenti corrispondenti per le versioni effettive. Queste verifiche restano
in `TODO.md`, insieme al controllo dei materiali nel pacchetto Linux reale.
Non abilitare l'allegato Linux alla release sulla sola base del manifest.

### Archivio e verifica Linux

La CI crea `PlannerApp-linux.tar.gz` con l'intera cartella `PlannerApp/`,
preservando i permessi e i collegamenti simbolici, e controlla nel TAR i bit
di esecuzione dell'app e del processo helper. Per estrarlo e avviarlo:

```bash
tar -xzf PlannerApp-linux.tar.gz
./PlannerApp/PlannerApp
```

Le wheel x64 di [PyQt6-Qt6](https://pypi.org/project/PyQt6-Qt6/6.11.0/) e
[QtWebEngine](https://pypi.org/project/PyQt6-WebEngine-Qt6/6.11.0/) della serie
impostata richiedono glibc 2.34 o successiva. La base Ubuntu 22.04 non garantisce
da sola la compatibilita con tutte le distribuzioni: build reale e prove su
desktop puliti, Wayland e X11 restano in `TODO.md`. Vedi anche
`TROUBLESHOOTING.md` per gli errori del plugin XCB.

## 6. Release e GitHub Actions
La build portable per Windows e Linux viene eseguita da GitHub Actions alla
pubblicazione di un tag di versione o tramite avvio manuale `workflow_dispatch`.

Il workflow si trova in:

```text
.github/workflows/release-build.yml
```

### Creare una nuova versione
Prima di creare una versione, assicurati di aver salvato e pubblicato tutte le modifiche su `main`.

Aggiorna la versione in `backend/config.py` (la versione in `frontend/package.json`
non viene usata):

```python
APP_VERSION = "0.1.0"
```

Il valore di `APP_VERSION` deve corrispondere al tag release senza la `v` iniziale:

```text
APP_VERSION = "0.1.0"
tag GitHub = v0.1.0
```

Il workflow verifica questa corrispondenza dopo il setup di Python, prima di
installare le dipendenze. Se le versioni differiscono, il job fallisce e la
release non viene pubblicata. Il controllo si applica ai riferimenti tag,
anche se selezionati per un avvio manuale; gli avvii manuali su un branch lo saltano.

```bash
git status
git add .
git commit -m "Preparazione release v0.1.0"
git push origin main
```

Poi crea e pubblica il tag:

```bash
git tag v0.1.0
git push origin v0.1.0
```

Quando il tag viene pubblicato, GitHub Actions avvia la build su Windows e Linux:

```text
PlannerApp-windows
PlannerApp-linux
```

macOS e escluso per ora (vedi `SVILUPPI_FUTURI.md`, "Supporto macOS").

Al termine delle build su tag, il workflow crea automaticamente la GitHub
Release e allega lo ZIP Windows. Il TAR.GZ Linux resta soltanto un artifact di
prova nella pagina del workflow finche licenze, build reale e prove native non
sono completate. Il download degli allegati release e limitato da
`pattern: PlannerApp-windows`: rimuovere o ampliare il filtro e aggiungere il
TAR.GZ a `files` solo dopo queste verifiche. Entrambe le build devono riuscire
per avviare il job release. Gli avvii manuali producono artifact, non release.

### Regole per i tag versione
Usa tag che iniziano con `v`, per esempio:

```text
v0.1.0
v0.2.0
v1.0.0
```

Il workflow non parte sui normali push: parte con tag compatibili con `v*` o
con l'avvio manuale.

### Aggiornare una versione gia pubblicata
Se hai creato un tag sbagliato e non lo hai ancora usato come release ufficiale, puoi eliminarlo e ricrearlo:

```bash
git tag -d v0.1.0
git push origin --delete v0.1.0
git tag v0.1.0
git push origin v0.1.0
```

Evita di riutilizzare tag gia distribuiti agli utenti. In quel caso crea una nuova versione, per esempio `v0.1.1`.
