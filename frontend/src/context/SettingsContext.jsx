import { useEffect, useState } from 'react';
import { getSettings } from '../api';
import { SettingsContext } from './settingsContextValue';

export function SettingsProvider({ children }) {

    const [settings, setSettings] = useState(null);
    const [isLoadingSettings, setIsLoadingSettings] = useState(true); 

    useEffect(() => {
        const loadSettings = async () => {
            try {
                const response = await getSettings();
                setSettings(response); 
            }catch (error) {
                console.error('Error loading settings:', error);
            }finally {
                setIsLoadingSettings(false);
            }
        }; 
        loadSettings();
    }, []); 

    if (isLoadingSettings){
        return null; 
    }

    return(
        <SettingsContext.Provider value = {{ 
            settings
        }}>
            {children}
        </SettingsContext.Provider> 
    );
}
