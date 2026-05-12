import { createContext, useContext, useEffect, useState } from 'react';
import { getAllAreas } from '../api';

const AreaContext = createContext();

export function AreaProvider({ children }) {

  const [areas, setAreas] = useState(null);
  const [currentArea, setCurrentArea] = useState(null); 
  const [error, setError] = useState(null);

  async function reloadAreas() {
    try {
      const response = await getAllAreas(); 
      setAreas(response); 
      setCurrentArea((current) => current ?? response[0]); 
      setError(null);
    } catch(error) {
      setError(error.message);
    }
  }
  
  useEffect(() => {
    reloadAreas(); 
  }, []); 

  return (
    <AreaContext.Provider value = {{ areas, currentArea, setCurrentArea, reloadAreas, error }}>
      {children}
    </AreaContext.Provider>
  )
}

export function useArea() {
  const context = useContext(AreaContext);

  if (!context) {
    throw new Error('useArea must be used within an AreaProvider');
  }

  return context;
}
