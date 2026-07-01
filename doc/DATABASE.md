# Database

Il progetto usa SQLite come database locale. Lo schema e definito in:

```text
backend/schema.sql
```

## Tabelle principali

- `areas`: contiene le aree di lavoro.
- `projects`: contiene i progetti collegati a una `area`.
- `tasks`: contiene le task collegate a un `project`.
- `settings`: contiene lingua, tema e colori custom dell'app.
- `calendar`: tabella prevista per funzionalita calendario future.

## Relazioni

```text
areas 1 -> N projects
projects 1 -> N tasks
```

Le relazioni sono gestite con foreign key:

```sql
projects.area_id -> areas.id
tasks.project_id -> projects.id
```

Entrambe usano `ON DELETE CASCADE`, quindi eliminando un'area vengono eliminati i suoi progetti, ed eliminando un progetto vengono eliminate le sue task.

## Vista progetti

La vista:

```text
v_projects_status
```

restituisce i dati dei progetti con:

- nome area;
- numero totale task;
- numero task completate;
- percentuale completamento.

Questa vista serve per evitare di ricalcolare lo stato progetto nel frontend.

## Dati iniziali

Alla creazione del DB vengono inserite:

```sql
INSERT INTO areas DEFAULT VALUES;
INSERT INTO settings DEFAULT VALUES;
```

Questo garantisce che l'app abbia una prima area e una riga impostazioni.

## Accesso al DB

Il flusso consigliato e:

```text
route HTTP -> repository -> SQLite
```

I repository stanno in:

```text
backend/db/repositories/
```

Le route non dovrebbero contenere SQL diretto. Devono validare la richiesta, chiamare il repository e restituire una risposta JSON.
