# Guida allo Sviluppo - Planner App

Segui questi passaggi per avviare il progetto in modalita sviluppo.

## 1. Backend (Python + Starlette)
Il backend gestisce il database SQLite e le API.

### Prima configurazione

Usa Python 3.14, aggiornato a una patch recente della serie `3.14.x`.
GitHub Actions compila le release Windows, Linux e macOS con la serie `3.14`;
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
MCP e PyWebView).
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

Su Windows e richiesto WebView2. Uvicorn lavora in un thread separato senza
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

## 6. Release e GitHub Actions
La build portable per Windows, Linux e macOS viene eseguita automaticamente da GitHub Actions solo quando viene pubblicato un tag di versione.

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

Quando il tag viene pubblicato, GitHub Actions avvia la build sui tre sistemi:

```text
PlannerApp-windows
PlannerApp-linux
PlannerApp-macos
```

Al termine, il workflow crea automaticamente la GitHub Release e allega i tre
archivi ZIP. Gli stessi artifact restano disponibili anche nella pagina del
workflow.

### Regole per i tag versione
Usa tag che iniziano con `v`, per esempio:

```text
v0.1.0
v0.2.0
v1.0.0
```

Il workflow non parte sui normali push: parte solo con tag compatibili con `v*`.

### Aggiornare una versione gia pubblicata
Se hai creato un tag sbagliato e non lo hai ancora usato come release ufficiale, puoi eliminarlo e ricrearlo:

```bash
git tag -d v0.1.0
git push origin --delete v0.1.0
git tag v0.1.0
git push origin v0.1.0
```

Evita di riutilizzare tag gia distribuiti agli utenti. In quel caso crea una nuova versione, per esempio `v0.1.1`.
