import { useEffect, useState } from 'react';

import { DataSyncContext } from './dataSyncContextValue';


export function DataSyncProvider({ children }) {
  const [lastEvent, setLastEvent] = useState(null);

  useEffect(() => {
    const eventSource = new EventSource('/api/events');

    eventSource.onmessage = (message) => {
      try {
        setLastEvent(JSON.parse(message.data));
      } catch (error) {
        console.error('Invalid server event:', error);
      }
    };

    return () => {
      eventSource.close();
    };
  }, []);

  return (
    <DataSyncContext.Provider value={{ lastEvent }}>
      {children}
    </DataSyncContext.Provider>
  );
}
