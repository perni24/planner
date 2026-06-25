import { useEffect, useState } from 'react';
import { useSettings } from './useSettings';
import { loadLanguage, updateLanguage } from '../api';
import { LanguageContext } from './languageContextValue';

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
      await updateLanguage(newLanguage);  
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
