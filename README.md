# Planner App

Planner App e un'applicazione locale per organizzare aree di lavoro, progetti e attivita.

Il progetto e attualmente in fase beta: alcune funzionalita sono ancora in evoluzione e la struttura potrebbe cambiare nelle prossime versioni.

## Funzioni principali

- Gestione di aree di lavoro.
- Creazione, modifica ed eliminazione di progetti.
- Gestione delle task e delle subtask collegate ai progetti, con avanzamento calcolato automaticamente.
- Integrazione con client AI tramite server MCP integrato.
- Cambio lingua tramite file JSON esterni.
- Impostazioni tema e colori personalizzati.
- Database locale SQLite.
- Versione portable generabile con PyInstaller.

## Struttura tecnica

Il progetto e diviso in due parti principali:

- `backend/`: API Python con Starlette, server MCP, database SQLite e build portable.
- `frontend/`: interfaccia React con Vite.

La documentazione tecnica si trova nella cartella `doc/`. Il punto di partenza e
`doc/STRUTTURA_PROGETTO.md`.

## Requisiti Windows

Planner usa Microsoft Edge WebView2 Runtime Evergreen, preinstallato in Windows 11:
su una normale installazione non occorre installare componenti aggiuntivi.
Il runtime non e incluso nella cartella portable. Se risulta mancante o danneggiato,
usa il [download ufficiale Microsoft](https://developer.microsoft.com/en-us/microsoft-edge/webview2/)
e consulta `doc/TROUBLESHOOTING.md`. Il solo browser Edge non sostituisce il runtime.

## Avvio in sviluppo

Riepilogo rapido. I passaggi completi, compresa la creazione dell'ambiente virtuale
e le release, sono in `doc/GUIDA_SVILUPPO.md`.

Prima prepara il frontend, dalla cartella principale del progetto:

```bash
cd frontend
npm install
npm run build
```

Backend (da un altro terminale nella cartella principale):

```bash
cd backend
```

Se usi un ambiente virtuale Python nella cartella `backend/venv`, attivalo prima
di installare le dipendenze. I comandi seguenti vanno eseguiti da `backend/`;
se il tuo ambiente ha un nome diverso, adatta il percorso.

Windows (PowerShell):

```powershell
.\venv\Scripts\Activate.ps1
```

Linux/macOS:

```bash
source venv/bin/activate
```

Poi installa le dipendenze e avvia il backend:

```bash
python -m pip install -r requirements-dev.txt
python main.py
```

`requirements-dev.txt` include le dipendenze dell'app e gli strumenti di sviluppo
e build. Per il solo backend basta `requirements.txt`.

`python main.py` apre Planner in una finestra PyWebView e avvia il backend senza
reload. Su Windows usa WebView2, come indicato nei requisiti. Chiudendo la finestra si richiede l'arresto
del backend; minimizzandola resta attivo.

Per sviluppare il frontend con Vite, in un terminale separato:

```bash
cd frontend
npm install
npm run dev
```

Apri l'indirizzo di Vite nel browser mantenendo la finestra Planner aperta.
La finestra desktop usa invece la build: per aggiornarla esegui `npm run build`
e riavvia l'app.

## Build portable

Per creare la versione portable:

```bash
cd backend
python build_portable.py
```

L'output viene generato in:

```text
backend/dist/PlannerApp
```

Con la modalita `--onedir` va distribuita tutta la cartella `PlannerApp`, non solo l'eseguibile.

## Stato del progetto

Planner App e in beta. Prima di usarla per dati importanti e consigliato fare backup del database SQLite.
