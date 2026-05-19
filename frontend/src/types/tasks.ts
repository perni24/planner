export interface Task {
    id: number,
    project_id: number,
    title: string,
    description: string | null,
    completed: 0 | 1,
    created_at: string,
    updated_at: string
}

export type TaskCreate = Omit<Task, 'id' | 'completed' | 'created_at' | 'updated_at'>;

export type TaskUpdate = Partial<Omit<Task, 'id' | 'project_id' | 'created_at' | 'updated_at'>>;
