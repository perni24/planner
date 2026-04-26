import { useState, useEffect } from 'react';

function Setting() {
  // logica da spostare in un contesto globale che viene eseguita prima del load della pagina
  const [theme, setTheme] = useState('system');
  const [customColors, setCustomColors] = useState({
    background: '#0f172a',
    foreground: '#1e3a8a',
    card: '#f0f9ff',
    border: '#3b82f6',
    hover: '#2563eb'
  });

  useEffect(() => {
    const root = window.document.documentElement;
    if(theme === 'light'){
      root.classList.remove('dark');
      root.classList.remove('custom');
    }else if(theme === 'dark'){
      root.classList.add('dark');
      root.classList.remove('custom');
    }else if(theme === 'system'){
      const isDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      if(isDark){
        root.classList.add('dark');
        root.classList.remove('custom');
      }else{
        root.classList.remove('dark');
        root.classList.remove('custom');
      }
    }else if(theme === 'custom'){
      root.classList.remove('dark');
      root.classList.add('custom');
    }
  }, [theme]);
  
  return (
    <div className="container mx-auto p-6 max-w-2xl">
      <h1 className="text-3xl font-bold mb-8">
        Impostazioni
      </h1>

      <div className="bg-main-card border border-main-border shadow rounded-lg p-6 space-y-8">
        {/* Selezione Tema Base */}
        <div className="flex flex-col gap-4">
          <label 
            htmlFor="theme-select" 
            className="text-sm font-medium"
          >
            Tema dell'applicazione
          </label>
          <select
            id="theme-select"
            className="block w-full px-4 py-2 bg-main-card border border-main-border rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            value={theme}
            onChange={(e) => setTheme(e.target.value)}
          >
            <option value="light">Chiaro</option>
            <option value="dark">Scuro</option>
            <option value="system">Sistema</option>
            <option value="custom">Personalizzato</option>
          </select>
        </div>

        {/* Sezione Colori Personalizzati (HTML/CSS UI) */}
        {theme === 'custom' && (
          <div className="pt-6 border-t border-main-border">
            <h2 className="text-lg font-semibold mb-4">Colori Personalizzati</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="flex flex-col gap-2">
                <label className="text-sm font-medium">Sfondo Pagina</label>
                <input 
                  type="color" 
                  className="w-full h-10 p-1 bg-main-bg border border-main-border rounded cursor-pointer"
                  value={customColors.background}
                  onChange={(e) => {
                    setCustomColors({...customColors, background: e.target.value})
                    document.documentElement.style.setProperty('--u-bg', e.target.value)}
                  }
                />
              </div>
              <div className="flex flex-col gap-2">
                <label className="text-sm font-medium">Testo Principale</label>
                <input 
                  type="color" 
                  className="w-full h-10 p-1 bg-main-bg border border-main-border rounded cursor-pointer"
                  value={customColors.foreground}
                  onChange={(e) => {
                    setCustomColors({...customColors, foreground: e.target.value}) 
                    document.documentElement.style.setProperty('--u-text', e.target.value)}
                  }
                />
              </div>
              <div className="flex flex-col gap-2">
                <label className="text-sm font-medium">Sfondo Card</label>
                <input 
                  type="color" 
                  className="w-full h-10 p-1 bg-main-bg border border-main-border rounded cursor-pointer"
                  value={customColors.card}
                  onChange={(e) => {
                    setCustomColors({...customColors, card: e.target.value})
                    document.documentElement.style.setProperty('--u-card', e.target.value)}
                  }
                />
              </div>
              <div className="flex flex-col gap-2">
                <label className="text-sm font-medium">Bordi</label>
                <input 
                  type="color" 
                  className="w-full h-10 p-1 bg-main-bg border border-main-border rounded cursor-pointer"
                  value={customColors.border}
                  onChange={(e) => {
                    setCustomColors({...customColors, border: e.target.value})
                    document.documentElement.style.setProperty('--u-border', e.target.value)}
                  }
                />
              </div>
            </div>
          </div>
        )}

      </div>
    </div>
  );
}

export default Setting;
