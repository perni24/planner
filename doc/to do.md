# Areas 
- [ ] gestione errori (insert, update, delete) sia frontend che backend

# Prima di PyInstaller/GitHub Actions
- [x] Sistemare errori di `npm run lint`
- [x] Rendere configurabili `debug` e `reload` del backend per sviluppo/produzione
- [x] Installare e configurare Ruff per il controllo automatico del backend
- [x] Creare workflow GitHub Actions per build release Windows, Linux e macOS su tag `v*`
- [ ] Comprimere gli artifact release in zip/tar.gz per ogni sistema operativo
- [ ] Creare automaticamente una GitHub Release quando viene pubblicato un tag `v*`
- [ ] Allegare gli artifact compressi alla GitHub Release

# PyInstaller / App portable
- [x] Distinguere percorsi di sviluppo e produzione in `config.py`
- [x] Creare automaticamente le cartelle runtime `data/` e `locales/`
- [x] Copiare i file lingua di default fuori dall'eseguibile al primo avvio
- [x] Esporre le API backend anche sotto `/api`
- [x] Servire `frontend/dist` dal backend in produzione
- [x] Gestire il fallback a `index.html` per le route React
- [x] Creare lo script `build_portable.py`
- [x] Configurare PyInstaller in modalita `--onedir`
- [x] Testare avvio dell'eseguibile senza Vite
- [x] Verificare creazione di `data/planner.db` vicino all'eseguibile
- [x] Verificare lettura/modifica dei file in `locales/` vicino all'eseguibile
- [x] Spegnere il backend in produzione quando la UI non invia piu heartbeat

# Priorita alta
- [x] Aggiungere validazione frontend nei modali area, progetto e task
- [x] Aggiungere validazione backend per id, name, title, area_id e project_id
- [x] Aggiungere conferma prima di eliminare area, progetto e task
- [x] Mostrare gli errori all'utente invece di salvarli solo in state o console
- [x] Aggiungere stato loading sui pulsanti di insert, update e delete
- [x] Proteggere update/delete quando area, progetto o task sono null
- [x] Mostrare toast quando un'azione viene bloccata per dati mancanti o non validi
- [x] Riallineare currentArea dopo eliminazione dell'area corrente

# Priorita media
- [ ] Sistemare timer del ToastContext con clearTimeout/useRef
- [x] Aggiungere toast di errore al cambio stato task in TaskCard
- [ ] Aggiungere gestione sotto-task collegate alle task principali
- [ ] Spostare le chiamate API dai modali/card verso pagine o context
- [ ] Passare ai componenti callback come onSave, onDelete, onToggle e onEdit
- [ ] Uniformare i nomi delle funzioni API frontend
- [ ] Rendere sicuri i refresh opzionali con refreshFunction?.()
- [x] Usare button al posto di span per elementi cliccabili
- [x] Restituire cursor.rowcount nei repository backend per update/delete
- [ ] Aggiornare i file .http per coprire tutte le route area, project e task

# Priorita bassa
- [ ] Formattare le date mostrate in UI
- [ ] Standardizzare testi brevi e simboli come X, x e OK
- [ ] Migliorare stati vuoti per progetti, aree e task
- [ ] Implementare o nascondere temporaneamente la pagina calendario
- [ ] Valutare backup, export e import del database
- [ ] Migliorare accessibilita dei modali e gestione focus
