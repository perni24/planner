# API Backend

Le API rispondono sia alla radice sia sotto `/api` (`/api/projects/get_all_projects`
e `/projects/get_all_projects`); il frontend usa `/api`, che in sviluppo Vite
inoltra al backend togliendo il prefisso. I body sono JSON.

## Regole comuni

- Errori di validazione: `400` con `{"error": "..."}`. Elemento inesistente in update
  e delete: `404`. Errori non gestiti (JSON non valido, foreign key): `500`.
- ID (`id`, `area_id`, `project_id`, `task_id`, `parent_id`): interi da `1` a
  `9223372036854775807`. REST accetta anche stringhe di sole cifre ASCII (`"7"`),
  mai booleani, decimali o altri formati. `parent_id` omesso o `null` indica una task
  principale.
- `Host` diverso da `127.0.0.1`, `localhost` (o `HOST`, se impostato): `400`
  `Invalid host header` (protezione DNS rebinding, `ALLOWED_HOSTS` in `config.py`).
- `POST`, `PUT`, `PATCH` e `DELETE` con `Origin` di un altro sito: `403`
  `{"error": "Cross-origin request blocked"}`, anche su `/mcp`
  (`middleware/origin_guard.py`). In sviluppo sono ammesse le origini locali (Vite);
  le richieste senza `Origin` (client MCP, curl) sono accettate salvo
  `Sec-Fetch-Site: cross-site`. Le `GET` non sono controllate: senza CORS un altro
  sito non ne legge la risposta.
- Durante l'arresto le nuove richieste ricevono `503`; un timeout SQLite prima della
  risposta restituisce `504`.

## Health

```text
GET /api/health                      -> {"status": "online"}
```

## Areas

```text
GET    /api/areas/get_all_areas
POST   /api/areas/insert_area      {name}
PUT    /api/areas/update_area      {id, name}
DELETE /api/areas/delete_area      {id}
```

Eliminare un'area elimina i suoi progetti e task. Se era l'ultima, il database crea
una nuova area vuota `utente` (ricaricare `get_all_areas` per ottenerla).

## Projects

```text
GET  /api/projects/get_all_projects
GET  /api/projects/get_projects_by_area?area_id=1
GET  /api/projects/get_project?project_id=1
POST /api/projects/insert_project   {area_id, name, description}
POST /api/projects/update_project   {project_id, name, description}
POST /api/projects/delete_project   {project_id}
```

`get_projects_by_area` e `get_project` includono `area_name`, `total_tasks`,
`completed_tasks` e `completion_percentage` (vista `v_projects_status`).
`get_project` restituisce `null` con `200` se il progetto non esiste.

## Tasks

```text
GET  /api/tasks/get_all_tasks
GET  /api/tasks/get_tasks_by_project?project_id=1
POST /api/tasks/insert_task          {project_id, title, description, parent_id}
POST /api/tasks/update_task          {task_id, title, description}
POST /api/tasks/update_status_task   {task_id}
POST /api/tasks/delete_task          {task_id}
```

Con `parent_id` la task e una subtask. Il parent deve esistere (`404` "Parent task
not found"), appartenere allo stesso progetto (`400`) ed essere una task principale
(`400`). `update_status_task` inverte `completed`; su una task con subtask risponde
`409`, perche il suo stato e calcolato dalle subtask (vedi `DATABASE.md`).

## Settings

```text
GET  /api/settings/get_all_settings
POST /api/settings/update_language   {language}
POST /api/settings/update_theme      {theme, custom_colors}
```

- `language`: codice (es. `it`, `pt-BR`) di un file lingua esterno valido in
  `LOCALES_DIR`.
- `theme`: `light`, `dark`, `system` o `custom`.
- `custom_colors`: sempre obbligatorio, con esattamente le chiavi `background`,
  `foreground`, `card`, `border`, `hover`, `hoverText` e valori `#RRGGBB`. Non sono
  previsti aggiornamenti parziali.

Payload non validi restituiscono `400` senza modificare i dati.

## Locales

```text
GET /api/locales/get_available_languages
GET /api/locales/load_language
```

`get_available_languages` elenca i dizionari esterni validi. `load_language`
restituisce quello della lingua salvata; se non e utilizzabile prova la copia
inclusa, poi italiano e inglese, senza modificare file o DB. Senza dizionari
utilizzabili restituisce `503`. Dettagli in `I18N.md`.

## App

```text
POST /api/app/shutdown        arresto esplicito del backend e chiusura della finestra (non usato dal frontend)
GET  /api/app/version         APP_VERSION di backend/config.py
GET  /api/app/check_update    confronto con l'ultima GitHub Release
```

`check_update` non blocca le altre richieste; se GitHub non risponde restituisce
`200` con `update_available: false` ed `error: "Unable to check for updates"`.

## Backup

```text
GET /api/backup/download
```

Scarica una copia consistente del database (dati, schema e `user_version`, senza i
file lingua) con data e ora nel nome. La copia temporanea viene eliminata dopo
l'invio. `404` se il DB non esiste. L'importazione non e ancora disponibile.

## Eventi (SSE)

```text
GET /api/events
```

Stream usato da `DataSyncContext.jsx` per ricaricare i dati. Eventi
`{"entity": "area|project|task", "action": "created|updated|deleted", "ids": [...]}`
e un commento `: heartbeat` ogni 30 secondi. Oggi li pubblicano solo le operazioni
MCP: le modifiche REST non generano eventi.

## Server MCP

Trasporto Streamable HTTP (stateless, risposte JSON) su
`http://127.0.0.1:8000/mcp/`, mostrato anche nelle Impostazioni.

| Tool | Descrizione |
|---|---|
| `get_all_areas` | Tutte le aree. |
| `get_all_projects` | Tutti i progetti con avanzamento. |
| `get_project_tasks` | Task e subtask di un progetto. |
| `bulk_insert_area` | Crea aree (nomi non duplicati nella richiesta). |
| `bulk_insert_project` | Crea progetti in aree esistenti. |
| `bulk_insert_task` | Crea task o subtask (parent dello stesso progetto e principale). |
| `bulk_update_project` | Aggiorna nome e descrizione; `description` omessa resta invariata, `""` la svuota. |
| `bulk_update_task` | Aggiorna titolo e descrizione, con la stessa regola. |
| `bulk_set_task_completed` | Imposta il completamento; rifiuta le task con subtask. |
| `bulk_delete_task` | Elimina task o subtask; per quelle con subtask serve `include_subtasks: true`. |
| `bulk_move_subtask` | Sposta subtask senza figli sotto altre task principali dello stesso progetto. |

- Ogni operazione bulk accetta da 1 a 50 elementi e fallisce per intero se un
  elemento non e valido; l'errore indica il motivo (es. `Tasks not found: 99.`).
- Gli ID devono essere interi JSON (validazione strict `EntityId`).
- `bulk_delete_task` (`{"tasks": [{"id": 15}], "include_subtasks": false}`)
  restituisce `requested`, `deleted` (incluse le subtask), `requested_task_ids`,
  `task_ids` e `parent_ids`.
- `bulk_move_subtask` (`{"subtasks": [{"id": 21, "parent_id": 8}]}`) non cambia
  contenuto o stato delle subtask; restituisce `requested`, `moved`, `task_ids`,
  `unchanged_ids` e `parent_ids`. Lo stato dei parent viene ricalcolato dal database.
- Le scritture pubblicano gli eventi SSE dopo il commit.

Logica in `services/mcp_service.py`, query in `db/repositories/mcp_repo.py`.
