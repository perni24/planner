# Guida allo Sviluppo - Planner App

Segui questi passaggi per avviare il progetto in modalita sviluppo.

## 1. Backend (Python + Starlette)
Il backend gestisce il database SQLite e le API.

### Prima configurazione

```bash
cd backend
python -m venv venv
```

### Avvio del server

```bash
cd backend
```

Attiva l'ambiente virtuale su Windows:

```powershell
.\venv\Scripts\Activate.ps1
```

Attiva l'ambiente virtuale su Linux/macOS:

```bash
source venv/bin/activate
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
fetch('http://127.0.0.1:8000/health')
  .then((res) => res.json())
  .then((data) => console.log('Risposta Backend:', data))
  .catch((err) => console.error('Errore connessione:', err));
```

Se vedi questo risultato, il backend risponde correttamente:

```text
Risposta Backend: {status: "online"}
```

## 4. Build portable locale
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

## 5. Release e GitHub Actions
La build portable per Windows, Linux e macOS viene eseguita automaticamente da GitHub Actions solo quando viene pubblicato un tag di versione.

Il workflow si trova in:

```text
.github/workflows/release-build.yml
```

### Creare una nuova versione
Prima di creare una versione, assicurati di aver salvato e pubblicato tutte le modifiche su `main`.

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

Gli artifact generati saranno disponibili nella pagina del workflow su GitHub.

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
