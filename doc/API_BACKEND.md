# API Backend

Il backend espone le API sia alla radice sia sotto `/api`.

Esempio:

```text
/projects/get_all_projects
/api/projects/get_all_projects
```

In sviluppo Vite usa il proxy `/api`. Nell'eseguibile il backend risponde direttamente a `/api`.

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
POST   /api/areas/insert_area
PUT    /api/areas/update_area
DELETE /api/areas/delete_area
```

Campi principali:

- `id`
- `name`

## Projects

```text
GET  /api/projects/get_all_projects
GET  /api/projects/get_projects_by_area?area_id=1
GET  /api/projects/get_project?project_id=1
POST /api/projects/insert_project
POST /api/projects/update_project
POST /api/projects/delete_project
```

Campi principali:

- `project_id`
- `area_id`
- `name`
- `description`

## Tasks

```text
GET  /api/tasks/get_all_tasks
GET  /api/tasks/get_tasks_by_project?project_id=1
POST /api/tasks/insert_task
POST /api/tasks/update_task
POST /api/tasks/update_status_task
POST /api/tasks/delete_task
```

Campi principali:

- `task_id`
- `project_id`
- `title`
- `description`

## Settings

```text
GET  /api/settings/get_all_settings
POST /api/settings/update_language
POST /api/settings/update_theme
```

Le settings gestiscono lingua, tema e colori custom.

## Locales

```text
GET /api/locales/get_available_languages
GET /api/locales/load_language
```

Le lingue vengono lette dalla cartella configurata in `LOCALES_DIR`.

## App lifecycle

```text
POST /api/app/heartbeat
POST /api/app/shutdown
```

`heartbeat` mantiene vivo il backend quando la UI e aperta.

`shutdown` permette uno spegnimento esplicito del backend.
