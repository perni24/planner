import { useEffect, useRef, useState } from 'react';
import Toast from '../components/Toast';
import { ToastContext } from './toastContextValue';

export function ToastProvider({ children }) {
  const [toast, setToast] = useState(null);
  const timeoutRef = useRef(null);

  useEffect(() => {
    return () => {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    };
  }, []);

  function showToast(message, type = 'success', duration = 3000) {
    clearTimeout(timeoutRef.current);
    setToast({ message, type });

    timeoutRef.current = setTimeout(() => {
      timeoutRef.current = null;
      setToast(null);
    }, duration);
  }

  function hideToast() {
    clearTimeout(timeoutRef.current);
    timeoutRef.current = null;
    setToast(null);
  }

  return (
    <ToastContext.Provider value={{ showToast, hideToast }}>
      {children}
      <Toast toast={toast} onClose={hideToast} />
    </ToastContext.Provider>
  );
}
