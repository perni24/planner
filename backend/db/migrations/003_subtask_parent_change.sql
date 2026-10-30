CREATE TRIGGER trg_subtask_after_move
AFTER UPDATE OF parent_id ON tasks
WHEN OLD.parent_id IS NOT NEW.parent_id
BEGIN
    UPDATE tasks
    SET completed = CASE
        WHEN EXISTS (SELECT 1 FROM tasks WHERE parent_id = OLD.parent_id AND completed = 0) THEN 0
        ELSE 1
    END,
    updated_at = CURRENT_TIMESTAMP
    WHERE id = OLD.parent_id
    AND EXISTS (SELECT 1 FROM tasks WHERE parent_id = OLD.parent_id);

    UPDATE tasks
    SET completed = CASE
        WHEN EXISTS (SELECT 1 FROM tasks WHERE parent_id = NEW.parent_id AND completed = 0) THEN 0
        ELSE 1
    END,
    updated_at = CURRENT_TIMESTAMP
    WHERE id = NEW.parent_id;
END;
