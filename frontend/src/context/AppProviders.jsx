import { ThemeProvider } from './ThemeContext';
import { SettingsProvider } from './SettingsContext';

function AppProviders({ children }) {
  return (
    <SettingsProvider>
      <ThemeProvider>
        {children}
      </ThemeProvider>
    </SettingsProvider>
  );
}

export default AppProviders;
