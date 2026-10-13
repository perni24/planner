-- Preparazione dei DB v0.0.1, eseguita nella stessa transazione della migrazione 001.
ALTER TABLE tasks ADD COLUMN parent_id INTEGER REFERENCES tasks(id) ON DELETE CASCADE;

CREATE TRIGGER trg_subtask_after_insert
AFTER INSERT ON tasks
WHEN NEW.parent_id IS NOT NULL
BEGIN
    UPDATE tasks
    SET completed = CASE
        WHEN (SELECT COUNT(*) FROM tasks WHERE parent_id = NEW.parent_id AND completed = 0) = 0 THEN 1
        ELSE 0
    END,
    updated_at = CURRENT_TIMESTAMP
    WHERE id = NEW.parent_id;
END;

CREATE TRIGGER trg_subtask_after_update
AFTER UPDATE OF completed ON tasks
WHEN NEW.parent_id IS NOT NULL
BEGIN
    UPDATE tasks
    SET completed = CASE
        WHEN (SELECT COUNT(*) FROM tasks WHERE parent_id = NEW.parent_id AND completed = 0) = 0 THEN 1
        ELSE 0
    END,
    updated_at = CURRENT_TIMESTAMP
    WHERE id = NEW.parent_id;
END;

CREATE TRIGGER trg_parent_derived
AFTER UPDATE OF completed ON tasks
WHEN NEW.parent_id IS NULL
AND EXISTS (SELECT 1 FROM tasks WHERE parent_id = NEW.id)
BEGIN
    UPDATE tasks
    SET completed = CASE
        WHEN (SELECT COUNT(*) FROM tasks WHERE parent_id = NEW.id AND completed = 0) = 0 THEN 1
        ELSE 0
    END,
    updated_at = CURRENT_TIMESTAMP
    WHERE id = NEW.id;
END;

DROP VIEW v_projects_status;

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
LEFT JOIN tasks t ON t.project_id = p.id AND t.parent_id IS NULL
GROUP BY
    p.id,
    p.area_id,
    a.name,
    p.name,
    p.description,
    p.created_at,
    p.updated_at;
