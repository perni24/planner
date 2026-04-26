import { createContext, useContext, useState } from 'react';

// 1. Creazione del Context
const ThemeContext = createContext();

// 2. Componente Provider che avvolge l'applicazione
export function ThemeProvider({ children }) {
  // Placeholder per lo stato
  const [value, setValue] = useState(null);

  return (
    <ThemeContext.Provider value={{ value, setValue }}>
      {children}
    </ThemeContext.Provider>
  );
}

// 3. Hook personalizzato per accedere al Context velocemente
export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};
