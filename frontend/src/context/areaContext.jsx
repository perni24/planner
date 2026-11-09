import { useEffect, useEffectEvent, useReducer } from 'react';
import { getAllAreas, insertArea, updateArea, deleteArea } from '../api';
import { AreaContext } from './areaContextValue';
import { useDataSync } from './useDataSync';
import { useLatestRequest } from '../hooks/useLatestRead';
import { areaStateReducer, initialAreaState } from '../utils/areaState';

export function AreaProvider({ children }) {

  const { lastEvent } = useDataSync();
  const [{ areas, currentArea, error }, dispatch] = useReducer(areaStateReducer, initialAreaState);
  const runAreaRead = useLatestRequest();

  function setCurrentArea(area) {
    dispatch({ type: 'selected', id: area.id });
  }

  function reloadAreas() {
    return runAreaRead(
      getAllAreas,
      (areas) => dispatch({ type: 'loaded', areas }),
      (error) => {
        console.error('Error loading areas:', error);
        dispatch({ type: 'loadFailed' });
      },
    );
  }

  async function createArea(name) {
    const response = await insertArea(name);
    dispatch({ type: 'saved' });
    await reloadAreas();
    return response;
  }

  async function editArea(id, name) {
    const response = await updateArea(id, name);
    dispatch({ type: 'saved' });
    await reloadAreas();
    return response;
  }

  async function removeArea(id) {
    const response = await deleteArea(id);
    dispatch({ type: 'deleted', id });
    await reloadAreas();
    return response;
  }

  const reloadAreasFromEvent = useEffectEvent(reloadAreas);
  
  useEffect(() => {
    reloadAreasFromEvent();
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
