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
PyWebView gestisce il ciclo di vita dell'app senza heartbeat dal frontend;
React, API REST, MCP, SQLite ed eventi SSE restano invariati.

`backend/main.py` resta l'unico punto di ingresso, anche per PyInstaller:
prepara l'ambiente, avvia Uvicorn in un thread separato, attende che sia pronto
e apre PyWebView nel thread principale. Non e previsto `backend/desktop.py`
ne un secondo avvio portable basato sul browser.

#### Verifiche native ancora aperte

L'avvio della finestra e stato verificato manualmente su Windows. I test
automatici simulano la GUI: non sostituiscono le prove seguenti. I dettagli delle
funzioni implementate sono in `ARCHITETTURA_PORTABLE.md`; la procedura di prova
e in `GUIDA_SVILUPPO.md`.

- [ ] Verificare lettura e salvataggio di progetti/task, MCP durante la minimizzazione e chiusura durante salvataggi REST/MCP e download; controllare che processo e porta vengano rilasciati
- [ ] Verificare i messaggi nativi Windows per errori di avvio e crash e la chiusura della finestra dopo lo shutdown via API
- [ ] Verificare che cookie e `localStorage` persistano dopo chiusura e riavvio; tema e lingua sono salvati nel DB e non dimostrano da soli la persistenza del profilo
- [ ] Verificare download del backup con scelta della destinazione e annullamento del dialogo, link GitHub nel browser esterno e copia dell'indirizzo MCP; adeguare solo se necessario
- [ ] Testare temi, lingue, aggiornamenti SSE e uso MCP dopo riavvio e sospensione/ripresa del PC

#### Build e distribuzione desktop

Queste attivita sostituiscono il vecchio passaggio 8. Procedere nell'ordine
seguente, prima di distribuire il nuovo avvio desktop.

**1. Renderer e dipendenze**

- [ ] Confermare i requisiti WebView2 su Windows, scegliere GTK o Qt su Linux e verificare il renderer nativo e le dipendenze Python su macOS
- [ ] Definire il fallback grafico degli errori prima dell'apertura della finestra su macOS/Linux: oggi restano log e console

**2. Script PyInstaller**

- [ ] Adeguare `build_portable.py` ai renderer scelti: verificare hook/import necessari ed escludere eventuali renderer inutilizzati, mantenendo `main.py` e inizialmente la console Windows
- [ ] Verificare i contenuti del pacchetto: frontend, schema, migrazioni, lingue e licenze; non includere database, log o profili WebView personali

**3. Pacchetto macOS**

- [ ] Definire il formato di distribuzione macOS; se si usa un bundle `.app`, adattare `APP_DIR` per mantenere `data/` e `locales/` in una posizione esterna al bundle e scrivibile
- [ ] Valutare firma e notarizzazione separatamente dalla semplice riuscita della build

**4. GitHub Actions e archivi**

- [ ] Installare nel workflow le dipendenze specifiche dei renderer per ciascun sistema, mantenendo gli avvii su tag `v*` e manuale
- [ ] Adeguare il confezionamento degli archivi e verificare su Linux/macOS la conservazione dei permessi di esecuzione dopo l'estrazione

**5. Verifica dei pacchetti e documentazione**

- [ ] Provare i pacchetti estratti su macchine pulite Windows, macOS e Linux, senza Python, Node o Vite installati: avvio, salvataggi, backup, MCP, persistenza e chiusura completa
- [ ] Allineare guide, istruzioni per gli agenti e documentazione portable ai renderer, ai prerequisiti e ai pacchetti effettivamente verificati

## 2. Alta

### Dipendenze e build
- [ ] Fissare la versione di `mcp` (il codice usa `mcp.server.mcpserver.MCPServer` e `ToolError` dell'SDK 2.x)
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
