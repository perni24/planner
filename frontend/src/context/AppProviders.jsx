import { ThemeProvider } from './ThemeContext';

function AppProviders({ children }) {
  return (
    <ThemeProvider>
      {children}
    </ThemeProvider>
  );
}

export default AppProviders;
