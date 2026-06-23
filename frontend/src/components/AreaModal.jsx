import { useState } from "react";
import { insertArea, updateArea, deleteArea } from "../api";
import { useArea } from "../context/areaContext";
import { useLanguage } from "../context/LanguageContext";
import { useToast } from '../context/ToastContext';

function AreaModal({ onClose, area = null, isEditMode = false  }) {
  
const { reloadAreas } = useArea();
const { jsonLanguage } = useLanguage(); 
const { showToast } = useToast();
const [areaName, setAreaName] = useState(isEditMode ? area?.name ?? '' : '')
const disabledButton = areaName.trim().length === 0
const hasChanges = areaName.trim() !== (area?.name ?? '').trim()
const disabledSaveButton = disabledButton || (isEditMode && (!area?.id || !hasChanges))
const disabledDeleteButton = isEditMode && !area?.id

async function handleUpsertArea() {
  const name = areaName.trim();

  if (!name || (isEditMode && !area?.id)) {
    return;
  }

  try {
    if(isEditMode){
      await updateArea(area.id, name);
      showToast(jsonLanguage['areaModal.toast.updated'], 'success');
    }else{
      await insertArea(name);
      showToast(jsonLanguage['areaModal.toast.created'], 'success');
    }
    await reloadAreas();
    onClose();
    } catch (error) {
      console.error(error);
      showToast(jsonLanguage['areaModal.toast.errorSave'], 'error');
    }
}

async function handleDeleteArea() {
  if (!area?.id) {
    return;
  }

  try {
    await deleteArea(area.id)
    showToast(jsonLanguage['areaModal.toast.deleted'], 'success');
    await reloadAreas();
    onClose();
  } catch (error) {
    console.error(error);
    showToast(jsonLanguage['areaModal.toast.errorDelete'], 'error');
  }
}

return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 px-4">
      <div className="w-full max-w-md rounded-lg border border-main-border bg-main-card p-6 text-main-text shadow-xl">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h2 className="text-xl font-semibold">{ isEditMode ? jsonLanguage['areaModal.title.edit'] : jsonLanguage['areaModal.title.create']}</h2>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="rounded-md px-2 py-1 text-sm text-main-text transition-colors hover:bg-main-hover hover:text-main-hover-text"
          >
            X
          </button>
        </div>

        <div className="mt-6">
          <label htmlFor="area-name" className="text-sm font-medium">
            {jsonLanguage['areaModal.name.label']}
          </label>
          <input
            id="area-name"
            type="text"
            value={areaName}
            placeholder={jsonLanguage['areaModal.name.placeholder']}
            className="mt-2 block w-full rounded-md border border-main-border bg-main-bg px-3 py-2 text-sm text-main-text shadow-sm outline-none transition-colors placeholder:text-main-text/50 focus:border-blue-500 focus:ring-2 focus:ring-blue-500"
            onChange={(e) => setAreaName(e.target.value)}
          />
        </div>

        <div className="mt-6 flex justify-end gap-3">
          {isEditMode && (
            <button
              type="button"
              className="rounded-md border border-red-500 px-4 py-2 text-sm font-medium text-red-500 transition-colors hover:bg-red-500 hover:text-white disabled:cursor-not-allowed disabled:border-gray-400 disabled:text-gray-400 disabled:hover:bg-transparent disabled:hover:text-gray-400"
              disabled={disabledDeleteButton}
              onClick={() => handleDeleteArea()}
            >
              {jsonLanguage['areaModal.actions.delete']}
            </button>
          )}
          <button
            type="button"
            className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-indigo-700 disabled:cursor-not-allowed disabled:bg-gray-400 disabled:opacity-60 disabled:hover:bg-gray-400"
            disabled={disabledSaveButton}
            onClick={() => handleUpsertArea()}
          >
            { isEditMode ? jsonLanguage['areaModal.actions.edit'] : jsonLanguage['areaModal.actions.create'] }
          </button>
        </div>
      </div>
    </div>
  );
}

export default AreaModal;
