# API Backend

Il backend espone le API sia alla radice sia sotto `/api`.

Esempio:

```text
/projects/get_all_projects
/api/projects/get_all_projects
```

In sviluppo Vite inoltra le richieste `/api` al backend togliendo il prefisso. Nell'eseguibile il backend risponde direttamente a `/api`.

Le richieste con body usano JSON. In caso di errore di validazione la risposta ha
stato `400` e la forma:

```json
{"error": "project_id must be a valid integer"}
```

Gli update e i delete restituiscono `404` se l'elemento non esiste. Gli errori non
gestiti (JSON non valido, foreign key inesistente) restituiscono `500`.

Tutte le richieste con un header `Host` diverso da `127.0.0.1` o `localhost` (piu il
valore di `HOST`, se cambiato) vengono rifiutate con `400` e il testo
`Invalid host header`. E la protezione contro il DNS rebinding, applicata da
`TrustedHostMiddleware` con l'elenco `ALLOWED_HOSTS` di `backend/config.py`.

Le richieste `POST`, `PUT`, `PATCH` e `DELETE` inviate da una pagina di un altro sito
vengono rifiutate con `403` (`{"error": "Cross-origin request blocked"}`), comprese
quelle verso `/mcp`. Il controllo e in `backend/middleware/origin_guard.py`:

- l'header `Origin` deve coincidere con l'indirizzo del backend (stessa origine);
- in sviluppo e accettata anche qualsiasi origine locale (`localhost`, `127.0.0.1`,
  `[::1]` su qualsiasi porta), per il frontend servito da Vite;
- le richieste senza `Origin` (client MCP, curl, file `.http`) sono accettate, salvo
  che il browser le marchi con `Sec-Fetch-Site: cross-site`.

Le richieste `GET` non sono controllate: un altro sito puo inviarle ma, senza CORS,
non puo leggerne la risposta.

## Health check

```text
GET /health
GET /api/health
```

Risposta:

```json
{"status": "online"}
```

## Areas

```text
GET    /api/areas/get_all_areas
POST   /api/areas/insert_area      {name}
PUT    /api/areas/update_area      {id, name}
DELETE /api/areas/delete_area      {id}
```

Eliminando un'area vengono eliminati anche i suoi progetti e le loro task.
Se era l'ultima area, il trigger `trg_recreate_last_area` crea automaticamente
un'area vuota `utente` con un nuovo id, senza recuperare i dati eliminati.
La risposta del delete resta invariata; per ottenere la nuova area si ricarica
`get_all_areas`.

## Projects

```text
GET  /api/projects/get_all_projects
GET  /api/projects/get_projects_by_area?area_id=1
GET  /api/projects/get_project?project_id=1
POST /api/projects/insert_project   {area_id, name, description}
POST /api/projects/update_project   {project_id, name, description}
POST /api/projects/delete_project   {project_id}
```

`get_projects_by_area` e `get_project` leggono dalla vista `v_projects_status`, quindi
includono `area_name`, `total_tasks`, `completed_tasks` e `completion_percentage`.
`get_all_projects` legge invece dalla tabella `projects`.

`get_project` restituisce `null` (con stato `200`) se il progetto non esiste.

## Tasks

```text
GET  /api/tasks/get_all_tasks
GET  /api/tasks/get_tasks_by_project?project_id=1
POST /api/tasks/insert_task          {project_id, title, description, parent_id}
POST /api/tasks/update_task          {task_id, title, description}
POST /api/tasks/update_status_task   {task_id}
POST /api/tasks/delete_task          {task_id}
```

`parent_id` e facoltativo: se presente, la task e una subtask della task indicata.
Se omesso o `null`, viene creata una task principale. Prima dell'inserimento,
`insert_task` verifica che il parent esista, appartenga allo stesso progetto e
sia una task principale. Una relazione non valida non viene salvata:

- parent inesistente: `404`, `{"error": "Parent task not found"}`;
- parent di un altro progetto: `400`, `{"error": "Parent task belongs to a different project"}`;
- parent che e gia una subtask: `400`, `{"error": "A subtask cannot be used as a parent"}`.

`update_status_task` inverte lo stato `completed` della task. Su una task che ha
subtask risponde `409`: il suo stato e calcolato dalle subtask (vedi `DATABASE.md`).

## Settings

```text
GET  /api/settings/get_all_settings
POST /api/settings/update_language   {language}
POST /api/settings/update_theme      {theme, custom_colors}
```

`custom_colors` deve contenere le chiavi `background`, `foreground`, `card`,
`border`, `hover` e `hoverText`.

## Locales

```text
GET /api/locales/get_available_languages
GET /api/locales/load_language
```

`load_language` restituisce il dizionario della lingua salvata nelle settings. Le
lingue vengono lette dalla cartella configurata in `LOCALES_DIR` (vedi `I18N.md`).

## App lifecycle

```text
POST /api/app/heartbeat
POST /api/app/shutdown
GET  /api/app/version
GET  /api/app/check_update
```

`heartbeat` resta temporaneamente disponibile, ma il monitor non viene piu
avviato: il ciclo di vita e gestito dalla finestra PyWebView.

`shutdown` permette uno spegnimento esplicito del backend. Attualmente il frontend
non lo usa. La chiusura automatica della finestra quando il backend viene
arrestato via API resta da gestire (vedi `TODO.md`).

`version` restituisce `APP_VERSION` definita in `backend/config.py`.

`check_update` confronta la versione corrente con l'ultima GitHub Release pubblicata.

## Backup

```text
GET /api/backup/download
```

Scarica una copia consistente del database creata con `Connection.backup()`
di SQLite, con data e ora nel nome del file. La generazione avviene in un thread
separato e non invia il file originale in uso. Le connessioni vengono chiuse prima
del trasferimento; la copia temporanea viene eliminata al termine dell'invio,
anche in caso di errore. La risposta non viene memorizzata in cache.

Il backup conserva dati, schema e `PRAGMA user_version`. Non include i file lingua
esterni. Se il DB non esiste, la route restituisce `404` senza crearlo.
L'importazione di un backup non e ancora disponibile.

## Eventi (SSE)

```text
GET /api/events
```

Connessione Server-Sent Events usata dal frontend (`DataSyncContext.jsx`) per
ricaricare i dati quando cambiano. Ogni evento ha la forma:

```json
{"entity": "task", "action": "created", "ids": [12, 13]}
```

- `entity`: `area`, `project` o `task`;
- `action`: `created` o `updated`.

Se non ci sono eventi, il server invia un commento `: heartbeat` ogni 30 secondi.

Attualmente gli eventi vengono pubblicati solo dalle operazioni MCP: le modifiche
fatte tramite le API REST non generano eventi.

## Server MCP

```text
/mcp/
```

Server MCP con trasporto Streamable HTTP (stateless, risposte JSON). Si collega a un
client AI indicando l'URL `http://127.0.0.1:8000/mcp/`, mostrato anche nella pagina
Impostazioni.

Tool disponibili:

| Tool | Descrizione |
|---|---|
| `get_all_areas` | Tutte le aree, anche senza progetti. |
| `get_all_projects` | Tutti i progetti con stato di avanzamento. |
| `get_project_tasks` | Task e subtask di un progetto. |
| `bulk_insert_area` | Crea piu aree (nomi non duplicati nella richiesta). |
| `bulk_insert_project` | Crea piu progetti in aree esistenti. |
| `bulk_insert_task` | Crea piu task o subtask. Il parent deve appartenere allo stesso progetto e non essere a sua volta una subtask. |
| `bulk_update_project` | Aggiorna nome e descrizione di piu progetti. |
| `bulk_update_task` | Aggiorna titolo e descrizione di piu task. |
| `bulk_set_task_completed` | Imposta lo stato di completamento di piu task. Rifiuta le task che hanno subtask, il cui stato e calcolato dalle subtask. |

Le operazioni bulk accettano al massimo 50 elementi per chiamata e falliscono per
intero se un elemento non e valido o se un id non esiste. Non esistono tool di
eliminazione.

Quando una richiesta non e valida, il tool restituisce un errore con il motivo
(per esempio `Tasks not found: 99.`), cosi il client AI puo correggerla.

La logica dei tool sta in `services/mcp_service.py`, le query in
`db/repositories/mcp_repo.py`.
