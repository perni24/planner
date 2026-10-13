# TODO

Attivita aperte, ordinate per priorita. Le attivita completate vengono rimosse: lo
storico resta nella cronologia Git. Le idee non ancora pianificate stanno in
`SVILUPPI_FUTURI.md`.

## 1. Critico

Da risolvere prima della prossima release.

### Funzionamento
- [ ] Impedire l'eliminazione dell'ultima area, oppure permettere di crearne una quando non ce ne sono (oggi l'interfaccia resta senza `AreaSwitcher`)

### Interfaccia desktop e spegnimento (PyWebView)

Decisione: nell'app portable backend e MCP restano attivi finche la finestra di
Planner e aperta, anche se minimizzata. Chiudendo la finestra si arresta tutto.
Non sono previste una modalita solo backend o un'icona nell'area di notifica.
PyWebView sostituira il browser e l'heartbeat per il ciclo di vita dell'app;
React, API REST, MCP, SQLite ed eventi SSE restano invariati.

- [ ] Creare una prova di integrazione PyWebView separata dalla build distribuita, verificando il funzionamento sui tre sistemi operativi
- [ ] Aggiungere `pywebview` alle dipendenze e scegliere i renderer supportati: verificare WebView2 su Windows e le dipendenze native su Linux/macOS
- [ ] Creare `backend/desktop.py` per gestire la finestra nel thread principale e Uvicorn in un thread separato
- [ ] Adeguare `main.py` e `config.py`: avvio desktop nella portable, sviluppo con browser/Vite e reload invariato, senza apertura automatica del browser in modalita desktop
- [ ] Attendere che il backend sia pronto prima di caricare la pagina nella finestra; gestire gli errori di avvio (incluse migrazioni fallite e porta occupata) senza lasciare processi attivi
- [ ] Collegare la chiusura della finestra all'arresto ordinato di Uvicorn, mantenendo l'app attiva se minimizzata; gestire SSE/MCP e prevedere un tempo massimo per lo spegnimento
- [ ] Rimuovere il monitor heartbeat e le chiamate periodiche del frontend quando il ciclo di vita sara gestito da PyWebView, adeguando gli endpoint e i riferimenti rimasti
- [ ] Configurare in `config.py` il percorso dei dati persistenti del WebView e la modalita non privata per conservare `localStorage` e cookie tra gli avvii
- [ ] Adeguare PyInstaller e GitHub Actions alle dipendenze grafiche e al packaging macOS, valutando firma e notarizzazione; mantenere inizialmente la console per diagnosticare gli errori e verificare su macchine pulite
- [ ] Testare download del backup, apertura dei link GitHub nel browser esterno, temi, lingue, SSE e MCP; verificare chiusura con richieste in corso, riavvio, minimizzazione e sospensione del PC
- [ ] Aggiornare guide, istruzioni per gli agenti e documentazione portable quando l'integrazione sara implementata

## 2. Alta

### Dipendenze e build
- [ ] Fissare la versione di `mcp` (il codice usa `mcp.server.mcpserver.MCPServer` e `ToolError` dell'SDK 2.x)
- [ ] Verificare su Linux/macOS che gli zip prodotti dalla CI mantengano il permesso di esecuzione e che l'app estratta si avvii
- [ ] CI: verificare che `APP_VERSION` corrisponda al tag della release

### Gestione errori
- [ ] Aggiungere un gestore globale degli errori nel backend (JSON non valido, `IntegrityError`, chiavi mancanti in `custom_colors`)
- [ ] Allineare `apiCore.ts`, che legge `detail`/`message`, al campo `error` restituito dal backend
- [ ] `get_project`: restituire `404` se il progetto non esiste (oggi `200` con `null`) e gestirlo in `Tasks.jsx`
- [ ] Validare la lingua in `update_language` e usare una lingua di fallback se il file manca
- [ ] Validare in `update_theme` i valori ammessi per `theme`, il tipo e le chiavi di `custom_colors` e il formato dei colori prima di scrivere nel DB

### Lingue portable
- [ ] Integrare le nuove chiavi dei dizionari inclusi nel bundle con i file esterni `locales/`, preservando le traduzioni dell'utente: oggi aggiornare l'app con file lingua gia presenti puo lasciare testi vuoti

### Backup
- [ ] Generare il backup con l'API `sqlite3.backup()` invece di copiare il file in uso

## 3. Media

### Backend
- [ ] Chiudere esplicitamente le connessioni SQLite (`with conn` fa commit ma non chiude)
- [ ] Progettare e implementare l'importazione sicura di un backup
- [ ] Aggiornare i file `.http` per coprire tutte le route (mancano `update_task`, `update_status_task`, `app/*` e `backup/download`)

### Frontend
- [ ] Sistemare il timer del `ToastContext` con `clearTimeout`/`useRef`

### Refactoring

Miglioramenti organizzativi, non bloccanti per la release.

- [ ] Spostare le chiamate API dai modali e dalle card verso pagine o context, passando ai componenti callback come `onSave`, `onDelete`, `onToggle` e `onEdit`
- [ ] Uniformare i nomi delle funzioni API frontend (es. `get_tasks_by_project` e `getProjectByArea`)
- [ ] Separare `pyinstaller` e `ruff` dalle dipendenze di runtime

## 4. Bassa

### Interfaccia
- [ ] Formattare le date mostrate in UI
- [ ] Standardizzare testi brevi e simboli come X, x e OK
- [ ] Migliorare gli stati vuoti per progetti, aree e task
- [ ] Mostrare il fallback `noDescription`: la descrizione vuota e salvata come `""`, quindi `??` non scatta mai
- [ ] Far seguire al tema `system` i cambi del tema del sistema operativo
- [ ] Migliorare l'accessibilita dei modali e la gestione del focus
- [ ] Calendario: implementare la pagina (e usare la tabella `calendar`) oppure nascondere la pagina e rimuovere la tabella

### Codice
- [ ] Convertire `requirements.txt` da UTF-16 a UTF-8 per uniformare la codifica del repository
- [ ] Aggiungere `tsconfig` e `typescript` per verificare i tipi, oppure convertire i file `.ts` in `.js`
- [ ] Rimuovere `types/test.ts`

### Automazione facoltativa

I lint vengono eseguiti manualmente in locale; automatizzarli non e un requisito
per la release.

- [ ] Valutare, se desiderato, l'esecuzione di `npm run lint` e `ruff check` nel workflow CI
