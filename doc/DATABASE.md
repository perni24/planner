# Database

Planner usa SQLite. Lo schema per i database nuovi e in `backend/schema.sql`.

## Tabelle e relazioni

- `areas` (`id`, `name`).
- `projects` (`area_id`, `name`, `description`, `created_at`, `updated_at`).
- `tasks` (`project_id`, `parent_id`, `title`, `description`, `completed`,
  `created_at`, `updated_at`): task e subtask.
- `settings`: una sola riga con lingua, tema e colori custom.
- `calendar`: prevista per il calendario, non ancora usata.

```text
areas 1 -> N projects -> N tasks -> N subtask (tasks.parent_id)
```

Tutte le foreign key hanno `ON DELETE CASCADE`. Sono attive solo con
`PRAGMA foreign_keys = ON`, che imposta `get_db_connection()` (`backend/db/db.py`):
usare sempre quella funzione, nella forma
`with closing(get_db_connection()) as conn, conn:` (commit/rollback, poi chiusura).

`completed` vale `0` o `1`; le date sono testi UTC `YYYY-MM-DD HH:MM:SS`.

## Regole gestite dal database

- **Ultima area**: il trigger `trg_recreate_last_area` crea una nuova area vuota
  `utente` quando viene eliminata l'ultima. Non recupera progetti o task eliminati.
- **Subtask**: un solo livello. REST e MCP verificano che il parent esista, sia
  nello stesso progetto e sia una task principale; lo schema da solo non impone
  queste ultime due regole.
- **Stato delle task con subtask**: e calcolato dai trigger, che segnano il parent
  completato solo se non ha subtask aperte.
  - `trg_subtask_after_insert`, `trg_subtask_after_update`, `trg_subtask_after_delete`
    ricalcolano il parent dopo ogni modifica di una subtask; se viene eliminata
    l'ultima, il parent conserva lo stato e torna modificabile a mano.
  - `trg_subtask_after_move` ricalcola vecchio e nuovo parent quando cambia
    `parent_id`, con la stessa regola per il parent rimasto senza subtask.
  - `trg_parent_derived` annulla una modifica manuale dello stato di un parent:
    per questo `update_status_task` e `bulk_set_task_completed` la rifiutano.
- **Vista `v_projects_status`**: progetti con nome area, task totali e completate e
  percentuale, contando solo le task principali.

## Creazione e migrazioni

All'avvio `init_db()`:

- applica `schema.sql` a un database nuovo o vuoto;
- per un database esistente legge `PRAGMA user_version` e applica solo le
  migrazioni mancanti, elencate in `MIGRATION_FILES` (`db/migration_runner.py`);
- rifiuta un database con versione piu recente di quella supportata.

La versione dello schema (oggi `3`) e indipendente da `APP_VERSION`; i database
delle prime release, senza versione, valgono `0`. Prima di migrare viene salvato un
backup in `migration_backups/` (`backend/db/` in sviluppo, `PlannerApp/data/` nella
portable). Ogni migrazione e una transazione insieme all'aggiornamento della
versione: un errore la annulla e blocca l'avvio.

| Script | Contenuto |
|---|---|
| `001_fix_subtask_delete.sql` | corregge il trigger di eliminazione subtask; per i DB di `v0.0.1` esegue prima `legacy_add_subtasks.sql` (aggiunge `parent_id`, trigger e vista) |
| `002_recreate_last_area.sql` | installa `trg_recreate_last_area` e ricrea un'area se non ce ne sono |
| `003_subtask_parent_change.sql` | installa `trg_subtask_after_move` |

### Aggiungere una modifica allo schema

1. Aggiorna `backend/schema.sql` (schema finale per le nuove installazioni).
2. Crea lo script successivo in `backend/db/migrations/` (es. `004_nome.sql`) e
   aggiungilo in fondo a `MIGRATION_FILES`.
3. Prova sia un database nuovo sia l'aggiornamento di uno precedente.

Non modificare o rinumerare migrazioni gia distribuite. Gli script non devono
contenere `BEGIN`, `COMMIT`, `ROLLBACK`, `SAVEPOINT` o assegnazioni a
`PRAGMA user_version`: il runner li rifiuta.

## Backup

`GET /api/backup/download` crea con `backup_database()` (`Connection.backup()`) una
copia consistente in una cartella temporanea dentro `DATA_DIR`, la invia e la
elimina. Contiene dati, schema e `user_version`, non i file lingua. I backup delle
migrazioni restano separati. L'importazione non e ancora disponibile.

## Timeout e annullamento

`get_db_connection()` assegna normalmente una scadenza di 30 secondi dall'apertura
della connessione (`DATABASE_OPERATION_TIMEOUT_SECONDS`). Non e un'attesa minima
e non si rinnova a ogni query. Se esiste uno scope con una scadenza piu breve,
prevale sempre quella.

`init_db()` usa invece un unico budget di 120 secondi
(`RUNTIME_INITIALIZATION_TIMEOUT_SECONDS`), anche se chiamata direttamente. La
connessione di inizializzazione e il backup preventivo ricevono esplicitamente
questo budget con `operation_timeout_seconds`; lo scope condiviso impedisce di
ripartire da 120 a ogni migrazione o backup. Il budget comprende il tempo gia
trascorso nella preparazione del runtime eseguita da `main.py`. I backup richiesti
dall'interfaccia conservano il normale limite di 30 secondi.

SQLite richiama il controllo Python di timeout e spegnimento ogni 50.000
istruzioni della propria macchina virtuale (`DATABASE_PROGRESS_STEPS`), non ogni
50.000 righe. Questo riduce i passaggi SQLite/Python rispetto alle precedenti
1.000 istruzioni, senza disabilitare l'annullamento. Restano anche i controlli
tra gli elementi bulk, tra le istruzioni delle migrazioni e prima del commit.

L'attesa di un lock SQLite resta limitata a 1 secondo. Durante la chiusura resta
la tolleranza di 3 secondi prima dell'annullamento cooperativo; il controllo
successivo interrompe il lavoro e la transazione corrente viene annullata.
Questi limiti non possono interrompere I/O bloccato internamente dal sistema
operativo e non garantiscono un tempo massimo assoluto di arresto.
