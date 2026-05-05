import { createContext, useContext, useEffect, useState } from 'react';
import { getAllSettings } from '../api';

const SettingsContext = createContext();

export function SettingsProvider({ children }) {

    const [settings, setSettings] = useState([]); 
    const [error, setError] = useState(null);

    useEffect(() => {
        const loadSettings = async () => {
            try {
                const response = await getAllSettings(); 
                setSettings(response[0]); 
            }catch (error) {
                setError(error.message);
            }
        }; 
        loadSettings();
    }, []); 

    return(
        <SettingsContext.Provider value = {{ 
            settings,
            setSettings
        }}>
            {children}
        </SettingsContext.Provider> 
    );
}

export function useSettings() {
  const context = useContext(SettingsContext);

  if (!context) {
    throw new Error('useSettings must be used within a SettingsProvider');
  }

  return context;
}