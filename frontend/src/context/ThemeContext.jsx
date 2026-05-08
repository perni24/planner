import { createContext, useContext, useEffect, useState } from 'react';
import { useSettings } from './SettingsContext';
import { updateTheme } from '../api';


const ThemeContext = createContext();


export function ThemeProvider({ children }) {

  const { settings } = useSettings();

  const [theme, setTheme] = useState(settings?.theme ?? 'system');
  const [customColors, setCustomColors] = useState({
    background: settings?.custom_background ?? '#0f172a',
    foreground: settings?.custom_foreground ?? '#f0f9ff',
    card: settings?.custom_card ?? '#1e3a8a',
    border: settings?.custom_border ?? '#3b82f6',
    hover: settings?.custom_hover ?? '#2563eb',
    hoverText: settings?.custom_hover_text ?? '#f0f9ff'
  });

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

  async function updateCustomColor(colorName, value) {
    const nextColors = {
      ...customColors,
      [colorName]: value,
    };

    setCustomColors(nextColors);

    try {
      await updateTheme(theme, nextColors);
    } catch (error) {
      console.error('Error updating theme:', error);
    }
  }


  async function changeTheme(newTheme){
    setTheme(newTheme);
    try{
      await updateTheme(newTheme, customColors);
    }catch(error){
      console.error('Error updating theme:', error);
    }
  }

  return (
    <ThemeContext.Provider
      value={{
        theme,
        customColors,
        updateCustomColor, 
        changeTheme
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
