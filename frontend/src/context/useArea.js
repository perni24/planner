import { useContext } from 'react';
import { AreaContext } from './areaContextValue';

export function useArea() {
  const context = useContext(AreaContext);

  if (!context) {
    throw new Error('useArea must be used within an AreaProvider');
  }

  return context;
}
