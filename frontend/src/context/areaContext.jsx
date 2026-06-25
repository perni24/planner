import { useEffect, useState } from 'react';
import { getAllAreas } from '../api';
import { AreaContext } from './areaContextValue';

export function AreaProvider({ children }) {

  const [areas, setAreas] = useState(null);
  const [currentArea, setCurrentArea] = useState(null); 
  const [error, setError] = useState(null);

  function updateAreasState(response) {
    setAreas(response);
    setCurrentArea((current) => {
      const currentStillExists = response.some((area) => area.id === current?.id);

      if (currentStillExists) {
        return current;
      }

      return response[0] ?? null;
    });
    setError(null);
  }

  async function reloadAreas() {
    try {
      const response = await getAllAreas(); 
      updateAreasState(response);
    } catch(error) {
      setError(error.message);
    }
  }
  
  useEffect(() => {
    async function loadInitialAreas() {
      try {
        const response = await getAllAreas();
        updateAreasState(response);
      } catch (error) {
        setError(error.message);
      }
    }

    loadInitialAreas(); 
  }, []); 

  return (
    <AreaContext.Provider value = {{ areas, currentArea, setCurrentArea, reloadAreas, error }}>
      {children}
    </AreaContext.Provider>
  )
}
