import { createContext, useContext, useEffect, useState } from 'react';
import { getAllAreas } from '../api';

const AreaContext = createContext();

export function AreaProvider({ children }) {

  const [areas, setAreas] = useState(null);
  const [currentArea, setCurrentArea] = useState(null); 
  const [error, setError] = useState(null);
  
  useEffect(() => {
    const loadArea = async () => {
      try {
        const response = await getAllAreas(); 
        setAreas(response); 
        setCurrentArea(response[0]); 
      }catch(error){
        setError(error.message);
      }
    }

    loadArea(); 
  }, []); 

  return (
    <AreaContext.Provider value = {{ areas, currentArea, setCurrentArea, error }}>
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