DROP TRIGGER IF EXISTS trg_subtask_after_delete;

CREATE TRIGGER trg_subtask_after_delete
AFTER DELETE ON tasks
WHEN OLD.parent_id IS NOT NULL
AND EXISTS (SELECT 1 FROM tasks WHERE parent_id = OLD.parent_id)
BEGIN
    UPDATE tasks
    SET completed = CASE
        WHEN (SELECT COUNT(*) FROM tasks WHERE parent_id = OLD.parent_id AND completed = 0) = 0 THEN 1
        ELSE 0
    END,
    updated_at = CURRENT_TIMESTAMP
    WHERE id = OLD.parent_id;
END;
