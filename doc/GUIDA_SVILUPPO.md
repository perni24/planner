# Guida allo Sviluppo - Planner App

Segui questi passaggi per avviare il progetto in modalita sviluppo.

## 1. Backend (Python + Starlette)
Il backend gestisce il database SQLite e le API.

### Prima configurazione

Serve Python 3.12 o superiore. GitHub Actions compila le release con la 3.12, quindi il codice deve restare compatibile con quella versione.

```bash
cd backend
python -m venv .venv
```

Usa il nome `.venv`: `build_portable.py` cerca PyInstaller in `backend/.venv/`.

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

Installa le dipendenze:

```bash
pip install -r requirements.txt
```

Avvia il server:

```bash
python main.py
```

Il server sara disponibile su:

```text
http://127.0.0.1:8000
```

Il database di sviluppo viene creato automaticamente in:

```text
backend/db/planner.db
```

## 2. Frontend (React + Vite)
Il frontend e l'interfaccia utente dell'applicazione.

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

In sviluppo il backend non si spegne quando manca l'heartbeat, quindi il server MCP
resta disponibile anche senza frontend aperto. Nell'app portable invece si spegne
circa 60 secondi dopo la chiusura della UI (vedi `ARCHITETTURA_PORTABLE.md`).

## 4. Controlli di qualita
Prima di un commit esegui i linter.

Frontend:

```bash
cd frontend
npm run lint
```

Backend (con l'ambiente virtuale attivo):

```bash
cd backend
ruff check .
```

Test automatici di migrazioni e download backup (da `backend/`, con l'ambiente virtuale attivo):

```bash
python -m unittest discover -s test -p test_*.py -v
```

I test usano database temporanei: non modificano `backend/db/planner.db`.
Coprono creazione, aggiornamento delle vecchie release, comportamento dei trigger,
rollback e riavvio dopo errori. I test del backup simulano richieste ASGI e
verificano integrita della copia, WAL, modifiche durante l'invio, download
simultanei e pulizia dei temporanei anche in caso di errore o cancellazione.
Le altre API vengono ancora provate manualmente.
GitHub Actions non esegue questi controlli.

Per modifiche allo schema segui la procedura in `DATABASE.md`: occorre aggiornare
sia `schema.sql` sia le migrazioni per i database esistenti.

## 5. Build portable locale
Per creare l'app portable localmente:

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
