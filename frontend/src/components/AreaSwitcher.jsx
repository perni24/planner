import { useState } from 'react';
import { useArea } from '../context/areaContext';
import AreaModal from './AreaModal';
import { useLanguage } from '../context/LanguageContext';

function AreaSwitcher() {
  const { areas, currentArea, setCurrentArea, error } = useArea(); 
  const { jsonLanguage } = useLanguage(); 
  const [isOpen, setIsOpen] = useState(false);
  const [isAreaModalOpen, setIsAreaModalOpen] = useState(false);
  const [isEditMode, setIsEditMode] = useState(false);
  const [selectedArea, setSelectedArea] = useState(null);

  const currentInitial = currentArea?.name?.charAt(0).toUpperCase() ?? '?';

  function selectArea(area) {
    setCurrentArea(area);
    setIsOpen(false);
  }

  function openAreaSettings(area) {
    setSelectedArea(area);
    setIsOpen(false);
    setIsAreaModalOpen(true);
    setIsEditMode(true);
  }

  if (error) {
    return null;
  }

  if (!areas?.length || !currentArea) {
    return null;
  }

  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => setIsOpen((open) => !open)}
        className="flex items-center gap-3 rounded-lg border border-main-border bg-main-card px-3 py-2 text-main-text shadow-sm transition-colors hover:bg-main-hover hover:text-main-hover-text"
      >
        <span className="flex h-8 w-8 items-center justify-center rounded-full bg-indigo-600 text-sm font-semibold text-white">
          {currentInitial}
        </span>
        <span className="text-sm font-medium">{currentArea.name}</span>
        <span className="text-xs">v</span>
      </button>

      {isOpen && (
        <div className="absolute right-0 z-50 mt-2 w-56 rounded-lg border border-main-border bg-main-card p-2 shadow-lg">

          {areas.map((area) => (
            <div
              key={area.id}
              className="flex items-center rounded-md text-main-text transition-colors hover:bg-main-hover hover:text-main-hover-text"
            >
              <button
                type="button"
                onClick={() => selectArea(area)}
                className="flex flex-1 items-center gap-3 px-3 py-2 text-left text-sm"
              >
                <span className="flex h-8 w-8 items-center justify-center rounded-full bg-indigo-600 text-xs font-semibold text-white">
                  {area.name?.charAt(0).toUpperCase() ?? '?'}
                </span>
                <span>{area.name}</span>
              </button>

              <button
                type="button"
                onClick={() => openAreaSettings(area)}
                className="rounded-md px-3 py-2 text-main-text transition-colors hover:bg-main-card hover:text-main-hover-text"
                aria-label={`Impostazioni area ${area.name}`}
              >
                <svg
                  className="h-4 w-4"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  aria-hidden="true"
                >
                  <circle cx="12" cy="12" r="3" />
                  <path d="M19.4 15a1.7 1.7 0 0 0 .3 1.9l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.9-.3 1.7 1.7 0 0 0-1 1.6V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1-1.6 1.7 1.7 0 0 0-1.9.3l-.1.1A2 2 0 1 1 4.2 17l.1-.1a1.7 1.7 0 0 0 .3-1.9 1.7 1.7 0 0 0-1.6-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.6-1 1.7 1.7 0 0 0-.3-1.9l-.1-.1A2 2 0 1 1 7.1 4.2l.1.1a1.7 1.7 0 0 0 1.9.3h.1A1.7 1.7 0 0 0 10 3V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.6 1.7 1.7 0 0 0 1.9-.3l.1-.1A2 2 0 1 1 19.8 7l-.1.1a1.7 1.7 0 0 0-.3 1.9v.1A1.7 1.7 0 0 0 21 10h.1a2 2 0 1 1 0 4H21a1.7 1.7 0 0 0-1.6 1Z" />
                </svg>
              </button>
            </div>
          ))}

          <div className="mt-2 border-t border-main-border pt-2">
            <button
              type="button"
              onClick={() => {
                setSelectedArea(null);
                setIsOpen(false);
                setIsAreaModalOpen(true);
                setIsEditMode(false);
              }}
              className="flex w-full items-center gap-3 rounded-md px-3 py-2 text-left text-sm font-medium text-main-text transition-colors hover:bg-main-hover hover:text-main-hover-text"
            >
              <span className="flex h-8 w-8 items-center justify-center rounded-full border border-main-border text-lg font-semibold">
                +
              </span>
              <span>{jsonLanguage['areaSwitcher.actions.create']}</span>
            </button>
          </div>
        </div>
      )}

      {isAreaModalOpen && (
        <AreaModal onClose={() => setIsAreaModalOpen(false)} area={selectedArea} isEditMode={isEditMode} />
      )}
    </div>
  );
}

export default AreaSwitcher;
