import { useLayoutEffect, useRef, useState } from 'react';
import { createLatestRead } from '../utils/latestRead';

export function useLatestRequest() {
  const readerRef = useRef(null);

  useLayoutEffect(() => {
    const reader = createLatestRead();
    readerRef.current = reader;
    return () => {
      readerRef.current = null;
      reader.dispose();
    };
  }, []);

  return async (read, onData, onError) => {
    await readerRef.current?.run(read, onData, onError);
  };
}

export function useLatestRead(read, initialData, errorMessage) {
  const [data, setData] = useState(initialData);
  const run = useLatestRequest();

  function reload() {
    return run(read, setData, (error) => console.error(errorMessage, error));
  }

  return [data, reload];
}
