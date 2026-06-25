import { useState } from 'react';
import Toast from '../components/Toast';
import { ToastContext } from './toastContextValue';

export function ToastProvider({ children }) {
  const [toast, setToast] = useState(null);

  function showToast(message, type = 'success', duration = 3000) {
    setToast({ message, type });

    setTimeout(() => {
      setToast(null);
    }, duration);
  }

  function hideToast() {
    setToast(null);
  }

  return (
    <ToastContext.Provider value={{ showToast, hideToast }}>
      {children}
      <Toast toast={toast} onClose={hideToast} />
    </ToastContext.Provider>
  );
}
