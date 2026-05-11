import { useState } from 'react';
import { useArea } from '../context/areaContext';
import AreaModal from './AreaModal';

function AreaSwitcher() {
  const { areas, currentArea, setCurrentArea, error } = useArea(); 
  const [isOpen, setIsOpen] = useState(false);
  const [isAreaModalOpen, setIsAreaModalOpen] = useState(false);

  const currentInitial = currentArea?.name?.charAt(0).toUpperCase() ?? '?';

  function selectArea(area) {
    setCurrentArea(area);
    setIsOpen(false);
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
            <button
              key={area.id}
              type="button"
              onClick={() => selectArea(area)}
              className="flex w-full items-center gap-3 rounded-md px-3 py-2 text-left text-sm text-main-text transition-colors hover:bg-main-hover hover:text-main-hover-text"
            >
              <span className="flex h-8 w-8 items-center justify-center rounded-full bg-indigo-600 text-xs font-semibold text-white">
                {area.name?.charAt(0).toUpperCase() ?? '?'}
              </span>
              <span>{area.name}</span>
            </button>
          ))}

          <div className="mt-2 border-t border-main-border pt-2">
            <button
              type="button"
              onClick={() => {
                setIsOpen(false);
                setIsAreaModalOpen(true);
              }}
              className="flex w-full items-center gap-3 rounded-md px-3 py-2 text-left text-sm font-medium text-main-text transition-colors hover:bg-main-hover hover:text-main-hover-text"
            >
              <span className="flex h-8 w-8 items-center justify-center rounded-full border border-main-border text-lg font-semibold">
                +
              </span>
              <span>Nuova area</span>
            </button>
          </div>
        </div>
      )}

      {isAreaModalOpen && (
        <AreaModal onClose={() => setIsAreaModalOpen(false)} />
      )}
    </div>
  );
}

export default AreaSwitcher;
