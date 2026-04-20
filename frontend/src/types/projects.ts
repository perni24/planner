export interface Project {
    id: number,
    name: string,
    description: string | null,
    created_at: string,
    updated_at: string
}

/*Usiamo 'Omit' per dire: "Prendi Project ma escludi id, created_at e updated_at"*/
export type ProjectCreate = Omit<Project, 'id' | 'created_at' | 'updated_at'>;

/*Usiamo 'Partial' su ProjectCreate per dire: "Tutti i campi sono opzionali"*/
export type ProjectUpdate = Partial<ProjectCreate>;
