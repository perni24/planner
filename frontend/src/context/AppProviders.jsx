import { useEffect } from 'react';

import { sendAppHeartbeat } from '../api';
import { ThemeProvider } from './ThemeContext';
import { SettingsProvider } from './SettingsContext';
import { LanguageProvider } from './LanguageContext';
import { AreaProvider } from './areaContext';
import { ToastProvider } from './ToastContext';

const HEARTBEAT_INTERVAL_MS = 10000;

function AppProviders({ children }) {
  useEffect(() => {
    sendAppHeartbeat().catch((error) => {
      console.error('Error sending app heartbeat:', error);
    });

    const heartbeatInterval = window.setInterval(() => {
      sendAppHeartbeat().catch((error) => {
        console.error('Error sending app heartbeat:', error);
      });
    }, HEARTBEAT_INTERVAL_MS);

    return () => {
      window.clearInterval(heartbeatInterval);
    };
  }, []);

  return (
    <SettingsProvider>
      <LanguageProvider>
        <ThemeProvider>
          <AreaProvider>
            <ToastProvider>
              {children}
            </ToastProvider>
          </AreaProvider>
        </ThemeProvider>
      </LanguageProvider>
    </SettingsProvider>
  );
}

export default AppProviders;
