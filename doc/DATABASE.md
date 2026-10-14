# Database

Il progetto usa SQLite come database locale. Lo schema e definito in:

```text
backend/schema.sql
```

## Tabelle

- `areas`: aree di lavoro (`id`, `name`).
- `projects`: progetti collegati a un'area (`area_id`, `name`, `description`, `created_at`, `updated_at`).
- `tasks`: task e subtask collegate a un progetto (`project_id`, `parent_id`, `title`, `description`, `completed`, `created_at`, `updated_at`).
- `settings`: una sola riga con lingua, tema e colori custom.
- `calendar`: tabella vuota prevista per il calendario, non ancora usata.

`completed` vale `0` o `1`. Le date sono testi nel formato di `CURRENT_TIMESTAMP`
di SQLite (UTC, `YYYY-MM-DD HH:MM:SS`).

## Relazioni

```text
areas 1 -> N projects
projects 1 -> N tasks
tasks 1 -> N tasks (subtask tramite parent_id)
```

Foreign key:

```sql
projects.area_id -> areas.id
tasks.project_id -> projects.id
tasks.parent_id  -> tasks.id
```

Tutte usano `ON DELETE CASCADE`: eliminando un'area vengono eliminati i suoi
progetti, eliminando un progetto le sue task, eliminando una task le sue subtask.

Le foreign key in SQLite sono attive solo se la connessione esegue
`PRAGMA foreign_keys = ON`, come fa `get_db_connection()` in `backend/db/db.py`.
Usare sempre quella funzione per aprire connessioni.

## Eliminazione dell'ultima area

Il trigger `trg_recreate_last_area` crea una nuova area vuota chiamata `utente`
quando un'eliminazione lascia la tabella `areas` senza righe. La nuova area ha
un nuovo id: non e un ripristino di quella eliminata e non recupera i suoi
progetti o task, che vengono cancellati normalmente tramite le foreign key.
Eliminazione e creazione avvengono nella stessa transazione.

Se rimangono altre aree, non viene creata alcuna area aggiuntiva. La conferma
di eliminazione nell'interfaccia esplicita questo comportamento; dopo
`reloadAreas()` il context seleziona una delle aree presenti, inclusa quella
ricreata. La migrazione `002` ripristina anche i database gia rimasti senza aree.

## Subtask e trigger di completamento

Il modello prevede un solo livello di subtask: una task con `parent_id` non
puo avere a sua volta subtask. Sia i tool MCP sia l'API REST `insert_task`
verificano che il parent esista, appartenga allo stesso progetto e non sia una
subtask. Il database verifica l'esistenza tramite foreign key, ma non impone
le altre due regole.

Lo stato di una task che ha subtask e derivato da quello delle subtask tramite
quattro trigger:

- `trg_subtask_after_insert`, `trg_subtask_after_update`, `trg_subtask_after_delete`:
  dopo ogni modifica di una subtask ricalcolano il parent, che risulta completato
  solo se non ha subtask aperte. Se viene eliminata l'ultima subtask, lo stato del
  parent resta invariato e la task torna modificabile a mano;
- `trg_parent_derived`: se si modifica direttamente lo stato di una task che ha
  subtask, lo ricalcola dalle subtask, annullando la modifica manuale.

Una modifica diretta dello stato di un parent con subtask verrebbe annullata da
`trg_parent_derived`. Per questo l'API REST (`update_status_task`) e il tool MCP
`bulk_set_task_completed` la rifiutano con un errore invece di eseguirla.

La migrazione `001_fix_subtask_delete.sql` aggiorna anche i database esistenti:
il vecchio trigger completava il parent eliminando l'ultima subtask aperta.
La correzione non ricostruisce gli stati eventualmente alterati in passato.

## Vista progetti

La vista `v_projects_status` restituisce i dati dei progetti con:

- nome area;
- numero totale task;
- numero task completate;
- percentuale di completamento (arrotondata a due decimali).

I conteggi includono solo le task di primo livello (`parent_id IS NULL`): le
subtask contano attraverso lo stato del loro parent.

## Dati iniziali

Alla creazione del DB vengono inserite:

```sql
INSERT INTO areas DEFAULT VALUES;
INSERT INTO settings DEFAULT VALUES;
```

Questo garantisce che l'app abbia una prima area (con nome `utente`) e una riga
impostazioni.

## Creazione e modifiche dello schema

`init_db()` viene eseguita all'avvio, prima di rendere disponibili le API:

- per un database nuovo o vuoto applica `schema.sql` e registra la versione corrente;
- per un database esistente legge `PRAGMA user_version` e applica soltanto le migrazioni mancanti;
- se la versione del database e superiore a quella supportata, interrompe l'avvio senza modificarlo: non esiste un downgrade automatico.

La versione dello schema e un intero indipendente da `APP_VERSION`: oggi vale `2`.
I database delle release precedenti, senza versione, vengono riconosciuti come `0`.
Le migrazioni sono file SQL in `backend/db/migrations/`, registrati in ordine nella
tupla `MIGRATION_FILES` di `backend/db/migration_runner.py`.

Prima di aggiornare un database esistente viene creato un backup consistente con
`sqlite3.backup()`. I backup hanno nome `planner_v<versione>_<data_ora>.db` e stanno
in `backend/db/migration_backups/` in sviluppo, oppure in
`PlannerApp/data/migration_backups/` nell'app portable. Non vengono creati per un
database nuovo o gia aggiornato.

Ogni migrazione e una transazione: script e incremento di `user_version` vengono
confermati insieme. Un errore annulla la migrazione corrente e blocca l'avvio; le
migrazioni precedenti gia confermate restano applicate. Al prossimo avvio si
riparte da quelle mancanti.

### Prima migrazione

`001_fix_subtask_delete.sql` sostituisce il trigger difettoso. Per i database di
`v0.0.1`, che non hanno ancora le subtask, il runner esegue prima
`legacy_add_subtasks.sql` nella stessa transazione: aggiunge `parent_id`, i trigger
di completamento e aggiorna la vista progetti. I dati e gli id esistenti vengono
conservati. I database di `v0.1.0` hanno gia questi elementi e ricevono soltanto la
correzione del trigger. Successivamente viene applicata anche la migrazione `002`.

### Seconda migrazione

`002_recreate_last_area.sql` installa `trg_recreate_last_area`. Se non esistono
aree, inserisce `utente`; altrimenti conserva tutte le aree esistenti. Non modifica
gli id o i dati presenti. I database allo schema `1` ricevono solo questa
migrazione, quelli senza versione ricevono prima la `001`.

### Aggiungere una modifica allo schema

1. Aggiorna `backend/schema.sql`, che deve rappresentare lo schema finale per le nuove installazioni.
2. Crea lo script successivo, per esempio `backend/db/migrations/003_nome_modifica.sql`, per trasformare lo schema precedente in quello nuovo.
3. Aggiungi il nome del file in fondo a `MIGRATION_FILES`, senza saltare numeri.
4. Verifica sia un database nuovo sia l'aggiornamento di un database precedente, anche in caso di errore e riavvio.

Non modificare o rinumerare migrazioni gia distribuite: aggiungine una nuova.
Gli script non devono contenere `BEGIN`, `COMMIT`, `ROLLBACK`, `SAVEPOINT` o
assegnazioni a `PRAGMA user_version`: transazioni e versione sono gestite dal
runner, che rifiuta queste istruzioni. La build portable include automaticamente
l'intera cartella delle migrazioni.

## Backup scaricabili

`GET /api/backup/download` genera una copia consistente tramite
`backup_database()` (`backend/db/db.py`), che usa `Connection.backup()` e chiude
esplicitamente entrambe le connessioni. Il file originale non viene inviato al
browser: la copia viene creata in una cartella temporanea dentro `DATA_DIR`,
eliminata dopo il trasferimento anche in caso di errore. Sono conservati anche
schema, trigger e `user_version`; i file lingua esterni non sono inclusi.

I backup delle migrazioni restano separati e vengono conservati in
`MIGRATION_BACKUPS_DIR`. L'importazione da interfaccia non e ancora disponibile.

## Accesso al DB

Il flusso e:

```text
route HTTP -> repository -> SQLite
tool MCP   -> services/mcp_service.py -> db/repositories/mcp_repo.py -> SQLite
```

I repository stanno in `backend/db/repositories/`. Le route e i service non
contengono SQL diretto: validano la richiesta, chiamano il repository e
restituiscono il risultato.
