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

## Subtask e trigger di completamento

Il modello prevede un solo livello di subtask: una task con `parent_id` non
dovrebbe avere a sua volta subtask. I tool MCP verificano questa regola e che il
parent appartenga allo stesso progetto; l'API REST e il database non la verificano.

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

Comportamento da conoscere (vedi `TODO.md`): nei database creati prima della
correzione di `trg_subtask_after_delete` (ottobre 2026) il trigger e ancora quello
vecchio: eliminando l'ultima subtask aperta, il parent risulta completato. Serve una
migrazione per aggiornarlo.

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

`init_db()` esegue `schema.sql` solo se il file del database non esiste. Se esiste,
non viene applicato nulla.

Di conseguenza una modifica a `schema.sql` vale solo per i database nuovi: i
database gia creati dagli utenti non vengono aggiornati. Prima di modificare lo
schema in una release va introdotto un sistema di migrazioni (vedi `TODO.md`).

## Accesso al DB

Il flusso e:

```text
route HTTP -> repository -> SQLite
tool MCP   -> services/mcp_service.py -> db/repositories/mcp_repo.py -> SQLite
```

I repository stanno in `backend/db/repositories/`. Le route e i service non
contengono SQL diretto: validano la richiesta, chiamano il repository e
restituiscono il risultato.
