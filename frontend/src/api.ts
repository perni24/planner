import { apiCore } from './apiCore';
import { Project, ProjectCreate, ProjectUpdate } from './types/projects';

export const getAllProjects = () => apiCore<Project[]>('/projects/get_all_projects');

export const getAvailableLanguages = () => apiCore<string[]>('/locales/get_available_languages'); 