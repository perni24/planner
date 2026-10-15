import { useEffect, useEffectEvent, useState } from 'react';
import { getAllAreas, insertArea, updateArea, deleteArea } from '../api';
import { AreaContext } from './areaContextValue';
import { useDataSync } from './useDataSync';

export function AreaProvider({ children }) {

  const { lastEvent } = useDataSync();
  const [areas, setAreas] = useState(null);
  const [currentArea, setCurrentArea] = useState(null); 
  const [error, setError] = useState(null);

  function updateAreasState(response) {
    setAreas(response);
    setCurrentArea((current) => {
      return response.find((area) => area.id === current?.id) ?? response[0] ?? null;
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

  async function createArea(name) {
    const response = await insertArea(name);
    await reloadAreas();
    return response;
  }

  async function editArea(id, name) {
    const response = await updateArea(id, name);
    await reloadAreas();
    return response;
  }

  async function removeArea(id) {
    const response = await deleteArea(id);
    await reloadAreas();
    return response;
  }

  const reloadAreasFromEvent = useEffectEvent(() => {
    reloadAreas();
  });
  
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

  useEffect(() => {
    if (lastEvent?.entity === 'area') {
      reloadAreasFromEvent();
    }
  }, [lastEvent]);

  return (
    <AreaContext.Provider value = {{ areas, currentArea, setCurrentArea, reloadAreas, createArea, editArea, removeArea, error }}>
      {children}
    </AreaContext.Provider>
  )
}
