# TODO

Attivita aperte, ordinate per priorita. Le attivita completate vengono rimosse: lo
storico resta nella cronologia Git. Le idee non ancora pianificate stanno in
`SVILUPPI_FUTURI.md`.

## 1. Critico

Da risolvere prima della prossima release.

### Interfaccia desktop e spegnimento (PyWebView)

Decisione: nell'app portable backend e MCP restano attivi finche la finestra di
Planner e aperta, anche se minimizzata. Chiudendo la finestra si arresta tutto.
Non sono previste una modalita solo backend o un'icona nell'area di notifica.
PyWebView sostituira il browser e l'heartbeat per il ciclo di vita dell'app;
React, API REST, MCP, SQLite ed eventi SSE restano invariati.

`backend/main.py` resta l'unico punto di ingresso, anche per PyInstaller:
prepara l'ambiente, avvia Uvicorn in un thread separato, attende che sia pronto
e apre PyWebView nel thread principale. Non e previsto `backend/desktop.py`
ne un secondo avvio portable basato sul browser.

Procedere nell'ordine seguente, verificando un passaggio alla volta. L'avvio
dell'app nella finestra nativa e stato verificato manualmente su Windows.
Restano le verifiche funzionali sotto elencate; macOS e Linux verranno verificati
prima di integrare il nuovo avvio nelle release.

#### Passaggio 1: Dipendenze

- [ ] Definire i renderer supportati e le dipendenze native necessarie su macOS e Linux

#### Passaggio 3: Avvio desktop di prova

- [ ] Completare le verifiche manuali nella finestra nativa Windows: lettura e salvataggio di progetti/task, MCP attivo durante la minimizzazione e porta liberata alla chiusura; l'avvio e confermato, mentre i test automatici simulano la finestra

#### Passaggio 4: Attesa ed errori di avvio

- [ ] Mostrare anche graficamente gli errori di avvio (migrazioni, porta occupata, frontend mancante e renderer non disponibile): oggi vengono propagati alla console; verificare anche inizializzazioni bloccate oltre il timeout
- [ ] Gestire l'arresto inatteso del backend dopo l'apertura della finestra e lo shutdown via API, evitando che la UI rimanga aperta senza server

#### Passaggio 5: Spegnimento dalla finestra

- [ ] Verificare lo spegnimento con scritture REST/MCP, download e connessioni SSE/MCP in corso; i test coprono gia la chiusura delle code SSE e il rilascio della porta con un client SSE connesso
- [ ] Gestire il superamento del timeout di arresto: oggi viene segnalato un errore ma il thread non-daemon puo rimanere attivo per non troncare operazioni; definire una strategia di cancellazione e verificare che non rimangano processi attivi

#### Passaggio 6: Persistenza e funzioni della finestra

- [ ] Configurare in `config.py` il percorso del profilo WebView (per esempio `data/webview/`) e la modalita non privata per conservare `localStorage` e cookie tra gli avvii; il profilo sara distinto da quello del browser
- [ ] Verificare download del backup e scelta della destinazione, link GitHub nel browser esterno e copia dell'indirizzo MCP, adeguando i comportamenti dove necessario
- [ ] Testare temi, lingue, aggiornamenti SSE e uso MCP, inclusi riavvio, minimizzazione e sospensione del PC

#### Passaggio 7: Rimozione heartbeat

- [ ] Solo dopo la verifica del ciclo di vita desktop, rimuovere il monitor in `app_lifecycle.py`, l'endpoint heartbeat e i relativi riferimenti backend
- [ ] Rimuovere `sendAppHeartbeat` e il timer da `AppProviders.jsx`, mantenendo il controllo degli aggiornamenti dell'app

#### Passaggio 8: Build e documentazione

- [ ] Adeguare PyInstaller e GitHub Actions al nuovo flusso desktop e alle dipendenze grafiche, mantenendo `main.py` come entry point e inizialmente la console per diagnosticare gli errori
- [ ] Verificare le build su macchine pulite Windows, macOS e Linux, inclusi requisiti nativi, packaging macOS, percorsi dei dati persistenti e valutazione di firma e notarizzazione
- [ ] Aggiornare guide, istruzioni per gli agenti e documentazione portable, rimuovendo i riferimenti al vecchio ciclo di vita basato su browser e heartbeat

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

## 3. Media

### Backend
- [ ] Progettare e implementare l'importazione sicura di un backup
- [ ] Aggiornare i file `.http` per coprire tutte le route (mancano `update_task`, `update_status_task`, `app/*` e `backup/download`)

## 4. Bassa

### Interfaccia
- [ ] Formattare le date mostrate in UI
- [ ] Standardizzare testi brevi e simboli come X, x e OK
- [ ] Migliorare gli stati vuoti per progetti, aree e task
- [ ] Mostrare il fallback `noDescription`: la descrizione vuota e salvata come `""`, quindi `??` non scatta mai
- [ ] Far seguire al tema `system` i cambi del tema del sistema operativo
- [ ] Migliorare l'accessibilita dei modali e la gestione del focus
- [ ] Calendario: implementare la pagina (e usare la tabella `calendar`) oppure nascondere la pagina e rimuovere la tabella

### Automazione facoltativa

I lint vengono eseguiti manualmente in locale; automatizzarli non e un requisito
per la release.

- [ ] Valutare, se desiderato, l'esecuzione di `npm run lint` e `ruff check` nel workflow CI
