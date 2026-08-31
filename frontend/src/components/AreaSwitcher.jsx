import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useArea } from '../context/useArea';
import AreaModal from './AreaModal';
import { useLanguage } from '../context/useLanguage';
import settingsIcon from '../assets/icons/settings.svg?no-inline';

function AreaSwitcher() {
  const { areas, currentArea, setCurrentArea, error } = useArea(); 
  const { jsonLanguage } = useLanguage(); 
  const navigate = useNavigate();
  const [isOpen, setIsOpen] = useState(false);
  const [isAreaModalOpen, setIsAreaModalOpen] = useState(false);
  const [isEditMode, setIsEditMode] = useState(false);
  const [selectedArea, setSelectedArea] = useState(null);
  const switcherRef = useRef(null);

  const currentInitial = currentArea?.name?.charAt(0).toUpperCase() ?? '?';

  useEffect(() => {
    if (!isOpen) {
      return undefined;
    }

    function closeOnOutsideClick(event) {
      if (!switcherRef.current?.contains(event.target)) {
        setIsOpen(false);
      }
    }

    document.addEventListener('mousedown', closeOnOutsideClick);

    return () => {
      document.removeEventListener('mousedown', closeOnOutsideClick);
    };
  }, [isOpen]);

  function selectArea(area) {
    setCurrentArea(area);
    setIsOpen(false);
    navigate('/');
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
    <div ref={switcherRef} className="relative">
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
                aria-label={`${jsonLanguage['areaSwitcher.actions.settings']} ${area.name}`}
              >
                <span
                  className="block h-4 w-4 shrink-0 bg-current"
                  style={{
                    maskImage: `url(${settingsIcon})`,
                    WebkitMaskImage: `url(${settingsIcon})`,
                    maskRepeat: 'no-repeat',
                    WebkitMaskRepeat: 'no-repeat',
                    maskPosition: 'center',
                    WebkitMaskPosition: 'center',
                    maskSize: 'contain',
                    WebkitMaskSize: 'contain',
                  }}
                  aria-hidden="true"
                />
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
