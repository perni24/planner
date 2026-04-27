import { createContext, useContext, useEffect, useState } from 'react';

const ThemeContext = createContext();

const DEFAULT_CUSTOM_COLORS = {
  background: '#0f172a',
  foreground: '#f0f9ff',
  card: '#1e3a8a',
  border: '#3b82f6',
  hover: '#2563eb',
  hoverText: '#f0f9ff'
};

export function ThemeProvider({ children }) {
  const [theme, setTheme] = useState('system');
  const [customColors, setCustomColors] = useState(DEFAULT_CUSTOM_COLORS);

  useEffect(() => {
    const root = window.document.documentElement;

    root.classList.remove('dark', 'custom');

    if (theme === 'dark') {
      root.classList.add('dark');
    }

    if (theme === 'system') {
      const isDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      if (isDark) {
        root.classList.add('dark');
      }
    }

    if (theme === 'custom') {
      root.classList.add('custom');
    }
  }, [theme]);

  useEffect(() => {
    const root = window.document.documentElement;

    root.style.setProperty('--u-bg', customColors.background);
    root.style.setProperty('--u-text', customColors.foreground);
    root.style.setProperty('--u-card', customColors.card);
    root.style.setProperty('--u-border', customColors.border);
    root.style.setProperty('--u-hover', customColors.hover);
    root.style.setProperty('--u-hover-text', customColors.hoverText);
  }, [customColors]);

  function updateCustomColor(colorName, value) {
    setCustomColors((currentColors) => ({
      ...currentColors,
      [colorName]: value,
    }));
  }

  return (
    <ThemeContext.Provider
      value={{
        theme,
        setTheme,
        customColors,
        updateCustomColor
      }}
    >
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const context = useContext(ThemeContext);

  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }

  return context;
}
