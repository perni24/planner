import { apiCore } from './apiCore';
import { Project, ProjectCreate, ProjectUpdate } from './types/projects';
import { LocaleDictionary } from './types/locales';
import { Settings } from './types/settings';

export const getAllProjects = () => apiCore<Project[]>('/projects/get_all_projects');

// settings 
export const getAllSettings = () => apiCore<Settings>('/settings/get_all_settings'); 

// languages
export const getAvailableLanguages = () => apiCore<string[]>('/locales/get_available_languages'); 

export const loadLanguage = () => apiCore<LocaleDictionary>('/locales/load_language');
