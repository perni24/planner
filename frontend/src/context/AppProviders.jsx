import { ThemeProvider } from './ThemeContext';
import { SettingsProvider } from './SettingsContext';
import { LanguageProvider } from './LanguageContext';
import { AreaProvider } from './areaContext';
import { ToastProvider } from './ToastContext';

function AppProviders({ children }) {
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
