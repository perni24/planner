import { ThemeProvider } from './ThemeContext';
import { SettingsProvider } from './SettingsContext';
import { LanguageProvider } from './LanguageContext';
import { AreaProvider } from './areaContext';

function AppProviders({ children }) {
  return (
    <SettingsProvider>
      <LanguageProvider>
        <ThemeProvider>
          <AreaProvider>
            {children}
          </AreaProvider>
        </ThemeProvider>
      </LanguageProvider>
    </SettingsProvider>
  );
}

export default AppProviders;
