import { apiCore } from './apiCore';
import { Project, ProjectCreate, ProjectUpdate } from './types/projects';
import { LocaleDictionary } from './types/locales';
import { Settings, CustomColors } from './types/settings';
import { ApiMessage } from './types/apiResponses';
import { Area } from './types/areas';

// areas
export const getAllAreas = () => apiCore<Area[]>('/areas/get_all_areas');

export const insertArea = (name: string) => apiCore<ApiMessage>('/areas/insert_area', {method: 'POST', body:{name}});

// projects 
export const getAllProjects = () => apiCore<Project[]>('/projects/get_all_projects');

// settings 
export const getAllSettings = () => apiCore<Settings>('/settings/get_all_settings'); 

export const updateLanguage = (language: string) => apiCore<ApiMessage>('/settings/update_language', {method: 'POST', body:{language}} ); 

export const updateTheme = (theme: string, custom_colors:CustomColors) => apiCore<ApiMessage>('/settings/update_theme', {method: 'POST', body: {theme, custom_colors}});

// languages
export const getAvailableLanguages = () => apiCore<string[]>('/locales/get_available_languages'); 

export const loadLanguage = () => apiCore<LocaleDictionary>('/locales/load_language');

