# Guida allo Sviluppo - Planner App

Segui questi passaggi per avviare il progetto in modalità sviluppo.

## 1. Backend (Python + Starlette)
Il backend gestisce il database SQLite e le API.

### Prima configurazione (da fare solo la prima volta)

```bash
# Entra nella cartella backend
cd backend

# Crea l'ambiente virtuale (Linux)
python -m venv .venv

# Crea l'ambiente virtuale (Windows)
python -m venv .venv
```

### Avvio del server

```bash
# Entra nella cartella backend (se non sei già dentro)
cd backend

# Attiva l'ambiente virtuale (Linux)
source .venv/bin/activate

# Attiva l'ambiente virtuale (Windows)
.\.venv\Scripts\activate

# Installa le dipendenze
pip install -r requirements.txt

# Avvia il server
python main.py
```
*Il server sarà attivo su: `http://127.0.0.1:8000`*
*Il database verrà creato automaticamente in `backend/db/planner.db`.*

---

## 2. Frontend (React + Vite)
Il frontend è l'interfaccia utente dell'applicazione.

```bash
# Entra nella cartella frontend
cd frontend

# Installa le dipendenze (solo la prima volta o se aggiungi librerie)
npm install

# Avvia il server di sviluppo Vite
npm run dev
```
*Vite ti fornirà un indirizzo (solitamente `http://localhost:5173`).*
*I comandi npm sopra sono validi sia per Linux che per Windows.*

---

## 3. Come testare la comunicazione
Per verificare che il Frontend possa parlare con il Backend senza errori di CORS:

1. Assicurati che **entrambi** i server siano accesi.
2. Apri il link del frontend nel browser.
3. Apri la console del browser (F12 -> Console).
4. Incolla questo codice per fare un test veloce:
   ```javascript
   fetch('http://127.0.0.1:8000/')
     .then(res => res.json())
     .then(data => console.log("Risposta Backend:", data))
     .catch(err => console.error("Errore connessione:", err));
   ```
   Se vedi `Risposta Backend: {messaggio: "Il backend del Planner è attivo!"}`, tutto funziona correttamente!
