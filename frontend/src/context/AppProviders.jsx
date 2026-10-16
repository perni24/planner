import { useEffect, useRef } from 'react';

import { checkAppUpdate } from '../api';
import { useLanguage } from './useLanguage';
import { useToast } from './useToast';
import { ThemeProvider } from './ThemeContext';
import { SettingsProvider } from './SettingsContext';
import { LanguageProvider } from './LanguageContext';
import { AreaProvider } from './areaContext';
import { DataSyncProvider } from './DataSyncContext';
import { ToastProvider } from './ToastContext';

function AppLifecycle({ children }) {
  const { jsonLanguage } = useLanguage();
  const { showToast } = useToast();
  const hasCheckedUpdate = useRef(false);

  useEffect(() => {
    if (hasCheckedUpdate.current) {
      return;
    }

    hasCheckedUpdate.current = true;

    checkAppUpdate()
      .then((updateStatus) => {
        if (updateStatus.update_available) {
          showToast(
            jsonLanguage['settings.version.toast.updateAvailable'] ??
              `Nuova versione disponibile: ${updateStatus.latest_version}`,
            'info',
            7000,
          );
        }
      })
      .catch((error) => {
        console.error('Error checking app updates:', error);
      });
  }, [jsonLanguage, showToast]);

  return children;
}

function AppProviders({ children }) {
  return (
    <SettingsProvider>
      <LanguageProvider>
        <ThemeProvider>
          <DataSyncProvider>
            <AreaProvider>
              <ToastProvider>
                <AppLifecycle>
                  {children}
                </AppLifecycle>
              </ToastProvider>
            </AreaProvider>
          </DataSyncProvider>
        </ThemeProvider>
      </LanguageProvider>
    </SettingsProvider>
  );
}

export default AppProviders;
