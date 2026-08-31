import { useContext } from 'react';

import { DataSyncContext } from './dataSyncContextValue';

export function useDataSync() {
  const context = useContext(DataSyncContext);

  if (!context) {
    throw new Error('useDataSync must be used within a DataSyncProvider');
  }

  return context;
}
