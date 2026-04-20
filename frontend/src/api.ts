import { apiCore } from './apiCore';
import { Project, ProjectCreate, ProjectUpdate } from './types/projects';

export const getAllProjects = () => apiCore<Project[]>('/projects/get_all_projects');