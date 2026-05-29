import { apiCore } from './apiCore';
import { Project } from './types/projects';
import { LocaleDictionary } from './types/locales';
import { Settings, CustomColors } from './types/settings';
import { ApiMessage } from './types/apiResponses';
import { Area } from './types/areas';
import { Task } from './types/tasks';

// areas
export const getAllAreas = () => apiCore<Area[]>('/areas/get_all_areas');

export const insertArea = (name: string) => apiCore<ApiMessage>('/areas/insert_area', {method: 'POST', body:{name}});

export const updateArea = (id: number, name: string) => apiCore<ApiMessage>('/areas/update_area', {method:'PUT', body:{id, name}})

export const deleteArea = (id: number) => apiCore<ApiMessage>('/areas/delete_area', {method:'DELETE', body:{id}})

// projects 
export const getProjectByArea = (area_id: number) => apiCore<Project[]>(`/projects/get_projects_by_area?area_id=${area_id}`);

export const getProject = (project_id: number) => apiCore<Project>(`/projects/get_project?project_id=${project_id}`);

export const insertProject = (area_id: number, name: string, description: string ) => apiCore<ApiMessage>('/projects/insert_project', {method: 'POST', body:{area_id, name, description}})

export const updateProject = (project_id: number, name: string, description: string) => apiCore<ApiMessage>('/projects/update_project', {method: 'POST', body:{project_id, name, description}})

export const deleteProject = (project_id: number) => apiCore<ApiMessage>('/projects/delete_project', {method: 'POST', body:{project_id}})

// tasks
export const get_tasks_by_project = (project_id: number) => apiCore<Task[]>(`/tasks/get_tasks_by_project?project_id=${project_id}`);

export const insertTask = (project_id: number, title: string, description: string) => apiCore<ApiMessage>('/tasks/insert_task', {method: 'POST', body:{project_id, title, description}}); 

export const updateTask = (task_id:number, title:string, description:string) => apiCore<ApiMessage>('/tasks/update_task', {method: 'POST', body:{task_id, title, description}});

export const updateStatusTask = (task_id:number) => apiCore<ApiMessage>('/tasks/update_status_task', {method: 'POST', body:{task_id}});

export const deleteTask = (task_id: number) => apiCore<ApiMessage>('/tasks/delete_task', {method: 'POST', body:{task_id}});

// settings 
export const getAllSettings = () => apiCore<Settings>('/settings/get_all_settings'); 

export const updateLanguage = (language: string) => apiCore<ApiMessage>('/settings/update_language', {method: 'POST', body:{language}} ); 

export const updateTheme = (theme: string, custom_colors:CustomColors) => apiCore<ApiMessage>('/settings/update_theme', {method: 'POST', body: {theme, custom_colors}});

// languages
export const getAvailableLanguages = () => apiCore<string[]>('/locales/get_available_languages'); 

export const loadLanguage = () => apiCore<LocaleDictionary>('/locales/load_language');


