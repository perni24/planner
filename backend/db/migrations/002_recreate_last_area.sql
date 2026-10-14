CREATE TRIGGER trg_recreate_last_area
AFTER DELETE ON areas
WHEN NOT EXISTS (SELECT 1 FROM areas)
BEGIN
    INSERT INTO areas (name) VALUES ('utente');
END;

-- Ripristina anche i database rimasti senza aree prima di questa migrazione.
INSERT INTO areas (name)
SELECT 'utente'
WHERE NOT EXISTS (SELECT 1 FROM areas);
