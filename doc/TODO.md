# TODO

Attivita aperte, ordinate per priorita. Le attivita completate vengono rimosse: lo
storico resta nella cronologia Git. Le idee non ancora pianificate stanno in
`SVILUPPI_FUTURI.md`.

## 1. Critico

Da risolvere prima della prossima release.

### Database
- [ ] Introdurre un sistema di migrazioni dello schema (`PRAGMA user_version` e script numerati): oggi `init_db()` non modifica un DB esistente
- [ ] Trigger `trg_subtask_after_delete`: corretto in `schema.sql`, ma i database esistenti hanno ancora la versione vecchia (eliminando l'ultima subtask aperta il parent risulta completato). Aggiornarlo con la prima migrazione
- [ ] REST `insert_task`: impedire subtask di subtask e `parent_id` di un altro progetto (come gia fa MCP)

### Funzionamento
- [ ] Rivedere lo spegnimento automatico: il server MCP non funziona senza UI aperta e le schede in background possono saltare gli heartbeat
- [ ] Verificare che lo spegnimento non resti bloccato con connessioni SSE aperte
- [ ] Impedire l'eliminazione dell'ultima area, oppure permettere di crearne una quando non ce ne sono (oggi l'interfaccia resta senza `AreaSwitcher`)

## 2. Alta

### Dipendenze e build
- [ ] Convertire `requirements.txt` da UTF-16 a UTF-8
- [ ] Fissare la versione di `mcp` (il codice usa `mcp.server.mcpserver.MCPServer` e `ToolError` dell'SDK 2.x)
- [ ] Separare `pyinstaller` e `ruff` dalle dipendenze di runtime
- [ ] CI: verificare che gli zip Linux/macOS creati con `Compress-Archive` mantengano il permesso di esecuzione
- [ ] CI: eseguire `npm run lint` e `ruff check` nel workflow
- [ ] CI: verificare che `APP_VERSION` corrisponda al tag della release

### Gestione errori
- [ ] Aggiungere un gestore globale degli errori nel backend (JSON non valido, `IntegrityError`, chiavi mancanti in `custom_colors`)
- [ ] Allineare `apiCore.ts`, che legge `detail`/`message`, al campo `error` restituito dal backend
- [ ] `get_project`: restituire `404` se il progetto non esiste (oggi `200` con `null`) e gestirlo in `Tasks.jsx`
- [ ] Validare la lingua in `update_language` e usare una lingua di fallback se il file manca

### Backup
- [ ] Generare il backup con l'API `sqlite3.backup()` invece di copiare il file in uso

## 3. Media

### Backend
- [ ] Chiudere esplicitamente le connessioni SQLite (`with conn` fa commit ma non chiude)
- [ ] Progettare e implementare l'importazione sicura di un backup
- [ ] Aggiornare i file `.http` per coprire tutte le route (mancano `update_task`, `update_status_task`, `app/*` e `backup/download`)

### Frontend
- [ ] Spostare le chiamate API dai modali e dalle card verso pagine o context, passando ai componenti callback come `onSave`, `onDelete`, `onToggle` e `onEdit`
- [ ] Uniformare i nomi delle funzioni API frontend (es. `get_tasks_by_project` e `getProjectByArea`)
- [ ] Sistemare il timer del `ToastContext` con `clearTimeout`/`useRef`

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
- [ ] Aggiungere `tsconfig` e `typescript` per verificare i tipi, oppure convertire i file `.ts` in `.js`
- [ ] Rimuovere `types/test.ts`
