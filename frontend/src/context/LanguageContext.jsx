import { createContext, useContext, useEffect, useState } from 'react';
import { useSettings } from './SettingsContext';
import { loadLanguage, updateLanguage } from '../api';

const LanguageContext = createContext();

export function LanguageProvider({ children }) {

  const { settings } = useSettings();
  const [language, setLanguage] = useState(settings?.language ?? 'it');
  const [jsonLanguage, setJsonLanguage] = useState({});
  const [error, setError] = useState(null);
  
  useEffect(() => {
    const loadJson = async () => {
      try {
        const response = await loadLanguage(); 
        setJsonLanguage(response); 
      }catch (error) {
        setError(error.message);
      }
    }
    loadJson(); 
  }, [language]);

  async function changeLanguage(newLanguage){
    try{
      const response = await updateLanguage(newLanguage);  
      setLanguage(newLanguage); 
    }catch (error) {
      setError(error.message);
    }
  }

  return (
      <LanguageContext.Provider value = {{ language, jsonLanguage, changeLanguage, error }}>
        {children}
      </LanguageContext.Provider>
  )

}

export function useLanguage() {
  const context = useContext(LanguageContext);

  if (!context) {
    throw new Error('useLanguage must be used within a LanguageProvider');
  }

  return context;
}