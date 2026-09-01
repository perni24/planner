import { useState, useEffect } from 'react';
import { useTheme } from '../context/useTheme';
import { checkAppUpdate, getAppVersion, getAvailableLanguages } from '../api';
import { useLanguage } from '../context/useLanguage';
import { useToast } from '../context/useToast';
import McpSettings from '../components/McpSettings';

function Setting() {
  const { theme, customColors, updateCustomColor, changeTheme } = useTheme();
  const { language, jsonLanguage, changeLanguage } = useLanguage(); 
  const { showToast } = useToast();

  const [allLanguages, setAllLanguages] = useState([]); 
  const [appVersion, setAppVersion] = useState('');
  const [updateStatus, setUpdateStatus] = useState(null);
  const [isCheckingUpdate, setIsCheckingUpdate] = useState(false);

  useEffect(() => {
    const loadLanguage = async () => {
      try{
        const response = await getAvailableLanguages();
        setAllLanguages(response);  
      }catch(error){
        console.error('Error Loading Language in Setting.jsx:', error);
      }
    }
    loadLanguage(); 
  }, []);

  useEffect(() => {
    const loadAppVersion = async () => {
      try {
        const response = await getAppVersion();
        setAppVersion(response.version);
      } catch (error) {
        console.error('Error Loading App Version in Setting.jsx:', error);
      }
    };

    loadAppVersion();
  }, []);

  async function handleCheckUpdate() {
    setIsCheckingUpdate(true);

    try {
      const response = await checkAppUpdate();
      setUpdateStatus(response);

      if (response.update_available) {
        showToast(jsonLanguage['settings.version.toast.updateAvailable'], 'info');
      } else if (response.error) {
        showToast(jsonLanguage['settings.version.toast.error'], 'error');
      } else {
        showToast(jsonLanguage['settings.version.toast.upToDate'], 'success');
      }
    } catch (error) {
      console.error('Error Checking App Update in Setting.jsx:', error);
      showToast(jsonLanguage['settings.version.toast.error'], 'error');
    } finally {
      setIsCheckingUpdate(false);
    }
  }
  
  return (
    <div className="container mx-auto p-6 max-w-2xl">
      <h1 className="text-3xl font-bold mb-8">
        {jsonLanguage['settings.title']}
      </h1>

      <div className="bg-main-card border border-main-border shadow rounded-lg p-6 space-y-8">
        {/* Selezione Tema Base */}
        <div className="flex flex-col gap-4">
          <label 
            htmlFor="theme-select" 
            className="text-sm font-medium"
          >
            {jsonLanguage['settings.theme.label']}
          </label>
          <select
            id="theme-select"
            className="block w-full px-4 py-2 bg-main-card border border-main-border rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            value={theme}
            onChange={(e) => changeTheme(e.target.value)}
          >
            <option value="light">{jsonLanguage['settings.theme.light']}</option>
            <option value="dark">{jsonLanguage['settings.theme.dark']}</option>
            <option value="system">{jsonLanguage['settings.theme.system']}</option>
            <option value="custom">{jsonLanguage['settings.theme.custom']}</option>
          </select>
        </div>

        {/* Sezione Colori Personalizzati (HTML/CSS UI) */}
        {theme === 'custom' && (
          <div className="pt-6 border-t border-main-border">
            <h2 className="text-lg font-semibold mb-4">{jsonLanguage['settings.colors.title']}</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="flex flex-col gap-2">
                <label className="text-sm font-medium">{jsonLanguage['settings.colors.background']}</label>
                <input 
                  type="color" 
                  className="w-full h-10 p-1 bg-main-bg border border-main-border rounded cursor-pointer"
                  value={customColors.background}
                  onChange={(e) => updateCustomColor('background', e.target.value)}
                />
              </div>
              <div className="flex flex-col gap-2">
                <label className="text-sm font-medium">{jsonLanguage['settings.colors.foreground']}</label>
                <input 
                  type="color" 
                  className="w-full h-10 p-1 bg-main-bg border border-main-border rounded cursor-pointer"
                  value={customColors.foreground}
                  onChange={(e) => updateCustomColor('foreground', e.target.value)}
                />
              </div>
              <div className="flex flex-col gap-2">
                <label className="text-sm font-medium">{jsonLanguage['settings.colors.card']}</label>
                <input 
                  type="color" 
                  className="w-full h-10 p-1 bg-main-bg border border-main-border rounded cursor-pointer"
                  value={customColors.card}
                  onChange={(e) => updateCustomColor('card', e.target.value)}
                />
              </div>
              <div className="flex flex-col gap-2">
                <label className="text-sm font-medium">{jsonLanguage['settings.colors.border']}</label>
                <input 
                  type="color" 
                  className="w-full h-10 p-1 bg-main-bg border border-main-border rounded cursor-pointer"
                  value={customColors.border}
                  onChange={(e) => updateCustomColor('border', e.target.value)}
                />
              </div>
              <div className="flex flex-col gap-2">
                <label className="text-sm font-medium">{jsonLanguage['settings.colors.hover']}</label>
                <input 
                  type="color" 
                  className="w-full h-10 p-1 bg-main-bg border border-main-border rounded cursor-pointer"
                  value={customColors.hover}
                  onChange={(e) => updateCustomColor('hover', e.target.value)}
                />
              </div>
              <div className="flex flex-col gap-2">
                <label className="text-sm font-medium">{jsonLanguage['settings.colors.hoverText']}</label>
                <input 
                  type="color" 
                  className="w-full h-10 p-1 bg-main-bg border border-main-border rounded cursor-pointer"
                  value={customColors.hoverText}
                  onChange={(e) => updateCustomColor('hoverText', e.target.value)}
                />
              </div>
            </div>
          </div>
        )}
        <div className="flex flex-col gap-4">
          <label 
              htmlFor="language-select" 
              className="text-sm font-medium"
          >
              {jsonLanguage['settings.language.label']}
          </label>
          <select
            id="language-select"
            className="block w-full px-4 py-2 bg-main-card border border-main-border rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            value = {language}
            onChange={(e) => changeLanguage(e.target.value)}
            >
            {allLanguages.map((item) => (
              <option key={item} value={item}>{item}</option>
            ))}
          </select>
        </div>

        <div className="flex flex-col gap-4">
          <label className="text-sm font-medium">
            {jsonLanguage['settings.backup.title']}
          </label>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <button
              type="button"
              onClick={() => {
                window.location.href = '/api/backup/download';
              }}
              className="block w-full px-4 py-2 bg-main-card border border-main-border rounded-md shadow-sm text-sm font-medium text-main-text hover:bg-main-hover hover:text-main-hover-text transition-colors"
            >
              {jsonLanguage['settings.backup.download']}
            </button>

            <button
              type="button"
              disabled
              title="Coming soon"
              className="block w-full px-4 py-2 bg-main-card border border-main-border rounded-md shadow-sm text-sm font-medium text-main-text opacity-50 cursor-not-allowed"
            >
              {jsonLanguage['settings.backup.import']}
            </button>
          </div>
        </div>

        <McpSettings />

        <div className="flex flex-col gap-4">
          <label className="text-sm font-medium">
            {jsonLanguage['settings.version.title']}
          </label>

          <div className="block w-full px-4 py-2 bg-main-card border border-main-border rounded-md shadow-sm text-sm text-main-text">
            {jsonLanguage['settings.version.current']}: {appVersion || '-'}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <button
              type="button"
              onClick={handleCheckUpdate}
              disabled={isCheckingUpdate}
              className={`block w-full px-4 py-2 bg-main-card border border-main-border rounded-md shadow-sm text-sm font-medium text-main-text transition-colors ${
                isCheckingUpdate
                  ? 'opacity-50 cursor-not-allowed'
                  : 'hover:bg-main-hover hover:text-main-hover-text'
              }`}
            >
              {isCheckingUpdate
                ? jsonLanguage['settings.version.checking']
                : jsonLanguage['settings.version.check']}
            </button>

            <button
              type="button"
              disabled={!updateStatus?.update_available}
              onClick={() => {
                if (updateStatus?.release_url) {
                  window.open(updateStatus.release_url, '_blank', 'noopener,noreferrer');
                }
              }}
              className={`block w-full px-4 py-2 bg-main-card border border-main-border rounded-md shadow-sm text-sm font-medium text-main-text transition-colors ${
                updateStatus?.update_available
                  ? 'hover:bg-main-hover hover:text-main-hover-text'
                  : 'opacity-50 cursor-not-allowed'
              }`}
            >
              {jsonLanguage['settings.version.openRelease']}
            </button>
          </div>
        </div>

      </div>
    </div>
  );
}

export default Setting;
