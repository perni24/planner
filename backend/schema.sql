CREATE TABLE areas(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL
);

CREATE TABLE projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    area_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (area_id) REFERENCES areas(id) ON DELETE CASCADE
);

CREATE TABLE tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    completed INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);

CREATE TABLE calendar(
    id INTEGER PRIMARY KEY AUTOINCREMENT
);

CREATE TABLE settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    theme TEXT NOT NULL DEFAULT 'system',
    custom_background TEXT NOT NULL DEFAULT '#0f172a',
    custom_foreground TEXT NOT NULL DEFAULT '#f0f9ff',
    custom_card TEXT NOT NULL DEFAULT '#1e3a8a',
    custom_border TEXT NOT NULL DEFAULT '#3b82f6',
    custom_hover TEXT NOT NULL DEFAULT '#2563eb',
    custom_hover_text TEXT NOT NULL DEFAULT '#f0f9ff'
);

CREATE VIEW v_projects_status AS
SELECT
    p.id,
    p.area_id,
    a.name AS area_name,
    p.name,
    p.description,
    p.created_at,
    p.updated_at,
    COUNT(t.id) AS total_tasks,
    COALESCE(SUM(CASE WHEN t.completed = 1 THEN 1 ELSE 0 END), 0) AS completed_tasks,
    CASE
        WHEN COUNT(t.id) = 0 THEN 0
        ELSE ROUND(
            COALESCE(SUM(CASE WHEN t.completed = 1 THEN 1 ELSE 0 END), 0) * 100.0 / COUNT(t.id),
            2
        )
    END AS completion_percentage
FROM projects p
LEFT JOIN areas a ON a.id = p.area_id
LEFT JOIN tasks t ON t.project_id = p.id
GROUP BY
    p.id,
    p.area_id,
    a.name,
    p.name,
    p.description,
    p.created_at,
    p.updated_at;
