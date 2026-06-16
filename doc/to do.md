# Areas 
- [ ] gestione errori (insert, update, delete) sia frontend che backend

# Priorita alta
- [x] Aggiungere validazione frontend nei modali area, progetto e task
- [ ] Aggiungere validazione backend per id, name, title, area_id e project_id
- [ ] Aggiungere conferma prima di eliminare area, progetto e task
- [ ] Mostrare gli errori all'utente invece di salvarli solo in state o console
- [ ] Aggiungere stato loading sui pulsanti di insert, update e delete
- [ ] Proteggere update/delete quando area, progetto o task sono null
- [ ] Riallineare currentArea dopo eliminazione dell'area corrente

# Priorita media
- [ ] Spostare le chiamate API dai modali/card verso pagine o context
- [ ] Passare ai componenti callback come onSave, onDelete, onToggle e onEdit
- [ ] Uniformare i nomi delle funzioni API frontend
- [ ] Rendere sicuri i refresh opzionali con refreshFunction?.()
- [ ] Usare button al posto di span per elementi cliccabili
- [ ] Restituire cursor.rowcount nei repository backend per update/delete
- [ ] Aggiornare i file .http per coprire tutte le route area, project e task

# Priorita bassa
- [ ] Formattare le date mostrate in UI
- [ ] Standardizzare testi brevi e simboli come X, x e OK
- [ ] Migliorare stati vuoti per progetti, aree e task
- [ ] Implementare o nascondere temporaneamente la pagina calendario
- [ ] Valutare backup, export e import del database
- [ ] Migliorare accessibilita dei modali e gestione focus
