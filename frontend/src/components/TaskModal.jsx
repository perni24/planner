import { useState } from "react";
import { insertTask, updateTask, deleteTask } from "../api";
import { useLanguage } from "../context/useLanguage";
import { useToast } from "../context/useToast";

function TaskModal({ onClose, isEditMode = false, task = null, refreshFunction, project_id }) {
  const { jsonLanguage } = useLanguage();
  const { showToast } = useToast();

  const [taskName, setTaskName] = useState(isEditMode ? task?.title ?? '' : '');
  const [taskDescription, setTaskDescription] = useState(isEditMode ? task?.description ?? '' : ''); 
  const [isSubmitting, setIsSubmitting] = useState(false);
  const disabledButton = taskName.trim().length === 0
  const hasChanges = taskName.trim() !== (task?.title ?? '').trim() || taskDescription.trim() !== (task?.description ?? '').trim()
  const disabledSaveButton = disabledButton || isSubmitting || (!isEditMode && !project_id) || (isEditMode && (!task?.id || !hasChanges))
  const disabledDeleteButton = isSubmitting || (isEditMode && !task?.id)

  async function handleInsertTask(){
    if (isSubmitting) {
      return;
    }

    const title = taskName.trim();

    if (!title || !project_id) {
      showToast(jsonLanguage['taskModal.toast.invalidData'], 'error');
      return;
    }

    try {
      setIsSubmitting(true);

      await insertTask(project_id, title, taskDescription); 
      showToast(jsonLanguage['taskModal.toast.created'], 'success');
      await refreshFunction?.();
      onClose(); 
    } catch (error) {
      console.error(error);
      showToast(jsonLanguage['taskModal.toast.errorSave'], 'error');
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleUpdateTask(){
    if (isSubmitting) {
      return;
    }

    const title = taskName.trim();

    if (!title || !task?.id) {
      showToast(jsonLanguage['taskModal.toast.invalidData'], 'error');
      return;
    }

    try {
      setIsSubmitting(true);

      await updateTask(task.id, title, taskDescription);
      showToast(jsonLanguage['taskModal.toast.updated'], 'success');
      await refreshFunction?.();
      onClose(); 
    } catch (error) {
      console.error(error);
      showToast(jsonLanguage['taskModal.toast.errorSave'], 'error');
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleDeleteTask(){
    if (isSubmitting) {
      return;
    }

    if (!task?.id) {
      showToast(jsonLanguage['taskModal.toast.invalidData'], 'error');
      return;
    }

    try {
      setIsSubmitting(true);

      await deleteTask(task.id);
      showToast(jsonLanguage['taskModal.toast.deleted'], 'success');
      await refreshFunction?.();
      onClose(); 
    } catch (error) {
      console.error(error);
      showToast(jsonLanguage['taskModal.toast.errorDelete'], 'error');
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 px-4">
      <div className="w-full max-w-lg rounded-lg border border-main-border bg-main-card p-6 text-main-text shadow-xl">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h2 className="text-xl font-semibold">
              {isEditMode ? jsonLanguage['taskModal.title.edit'] : jsonLanguage['taskModal.title.create']}
            </h2>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="rounded-md px-2 py-1 text-sm text-main-text transition-colors hover:bg-main-hover hover:text-main-hover-text"
          >
            X
          </button>
        </div>

        <div className="mt-6 space-y-4">
          <div>
            <label htmlFor="task-title" className="text-sm font-medium">
              {jsonLanguage['taskModal.title.label']}
            </label>
            <input
              id="task-title"
              type="text"
              value={taskName}
              placeholder={jsonLanguage['taskModal.title.placeholder']}
              className="mt-2 block w-full rounded-md border border-main-border bg-main-bg px-3 py-2 text-sm text-main-text shadow-sm outline-none transition-colors placeholder:text-main-text/50 focus:border-blue-500 focus:ring-2 focus:ring-blue-500"
              onChange={(e) => setTaskName(e.target.value)}
            />
          </div>

          <div>
            <label htmlFor="task-description" className="text-sm font-medium">
              {jsonLanguage['taskModal.description.label']}
            </label>
            <textarea
              id="task-description"
              rows="4"
              value={taskDescription}
              placeholder={jsonLanguage['taskModal.description.placeholder']}
              className="mt-2 block w-full resize-none rounded-md border border-main-border bg-main-bg px-3 py-2 text-sm text-main-text shadow-sm outline-none transition-colors placeholder:text-main-text/50 focus:border-blue-500 focus:ring-2 focus:ring-blue-500"
              onChange={(e) => setTaskDescription(e.target.value)}
            />
          </div>

        </div>

        <div className="mt-6 flex justify-end gap-3">
          {isEditMode && (
            <button
              type="button"
              className="rounded-md border border-red-500 px-4 py-2 text-sm font-medium text-red-500 transition-colors hover:bg-red-500 hover:text-white disabled:cursor-not-allowed disabled:border-gray-400 disabled:text-gray-400 disabled:hover:bg-transparent disabled:hover:text-gray-400"
              disabled={disabledDeleteButton}
              onClick={() => handleDeleteTask()}
            >
              {jsonLanguage['taskModal.actions.delete']}
            </button>
          )}

          <button
            type="button"
            className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-indigo-700 disabled:cursor-not-allowed disabled:bg-gray-400 disabled:opacity-60 disabled:hover:bg-gray-400"
            disabled={disabledSaveButton}
            onClick={() => isEditMode ? handleUpdateTask() : handleInsertTask()}
          >
            {isEditMode ? jsonLanguage['taskModal.actions.edit'] : jsonLanguage['taskModal.actions.create']}
          </button>
        </div>
      </div>
    </div>
  );
}

export default TaskModal;
