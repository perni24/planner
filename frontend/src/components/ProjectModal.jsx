import { useState } from "react";
import { insertProject, updateProject, deleteProject } from "../api";
import { useArea } from "../context/useArea";
import { useNavigate } from 'react-router-dom';
import { useLanguage } from "../context/useLanguage";
import { useToast } from "../context/useToast";
import ConfirmModal from "./ConfirmModal";

function ProjectModal({ onClose, refreshFunction, isEditMode = false, project = null }) {
    const navigate = useNavigate();
    const {jsonLanguage} = useLanguage(); 
    const { showToast } = useToast();
    const {currentArea} = useArea(); 
    const [projectName, setProjectName] = useState(isEditMode ? project?.name ?? '' : '');
    const [projectDescription, setProjectDescription] = useState(isEditMode ? project?.description ?? '' : ''); 
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [isConfirmOpen, setIsConfirmOpen] = useState(false);

    const disabledButton = projectName.trim().length === 0
    const hasChanges = projectName.trim() !== (project?.name ?? '').trim() || projectDescription.trim() !== (project?.description ?? '').trim()
    const disabledSaveButton = disabledButton || isSubmitting || (!isEditMode && !currentArea?.id) || (isEditMode && (!project?.id || !hasChanges))
    const disabledDeleteButton = isSubmitting || (isEditMode && !project?.id)

    async function handleUpsertProject(){
        if (isSubmitting) {
            return;
        }

        const name = projectName.trim();

        if (!name || (!isEditMode && !currentArea?.id) || (isEditMode && !project?.id)) {
            showToast(jsonLanguage['projectModal.toast.invalidData'], 'error');
            return;
        }

        try {
            setIsSubmitting(true);

            if (!isEditMode) {
                await insertProject(currentArea.id, name, projectDescription); 
                showToast(jsonLanguage['projectModal.toast.created'], 'success');
                await refreshFunction?.(); 
            }else{
                await updateProject(project.id, name, projectDescription)
                showToast(jsonLanguage['projectModal.toast.updated'], 'success');
                await refreshFunction?.(); 
            }

            onClose(); 
        } catch (error) {
            console.error(error);
            showToast(jsonLanguage['projectModal.toast.errorSave'], 'error');
        } finally {
            setIsSubmitting(false);
        }
    }

    async function handleDeleteProject(){
        if (isSubmitting) {
            return;
        }

        if (!project?.id) {
            showToast(jsonLanguage['projectModal.toast.invalidData'], 'error');
            return;
        }

        try {
            setIsSubmitting(true);

            await deleteProject(project.id);
            showToast(jsonLanguage['projectModal.toast.deleted'], 'success');
            onClose();
            navigate('/');
        } catch (error) {
            console.error(error);
            showToast(jsonLanguage['projectModal.toast.errorDelete'], 'error');
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
                            {isEditMode ? jsonLanguage['projectModal.title.edit'] : jsonLanguage['projectModal.title.create']}
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
                        <label htmlFor="project-name" className="text-sm font-medium">
                            {jsonLanguage['projectModal.name.label']}
                        </label>
                        <input
                            id="project-name"
                            type="text"
                            value={projectName}
                            placeholder={jsonLanguage['projectModal.name.placeholder']}
                            className="mt-2 block w-full rounded-md border border-main-border bg-main-bg px-3 py-2 text-sm text-main-text shadow-sm outline-none transition-colors placeholder:text-main-text/50 focus:border-blue-500 focus:ring-2 focus:ring-blue-500"
                            onChange={(e) => setProjectName(e.target.value)}
                        />
                    </div>

                    <div>
                        <label htmlFor="project-description" className="text-sm font-medium">
                            {jsonLanguage['projectModal.description.label']}
                        </label>
                        <textarea
                            id="project-description"
                            rows="4"
                            value={projectDescription}
                            placeholder={jsonLanguage['projectModal.description.placeholder']}
                            className="mt-2 block w-full resize-none rounded-md border border-main-border bg-main-bg px-3 py-2 text-sm text-main-text shadow-sm outline-none transition-colors placeholder:text-main-text/50 focus:border-blue-500 focus:ring-2 focus:ring-blue-500"
                            onChange={(e) => setProjectDescription(e.target.value)}
                        />
                    </div>
                </div>

                <div className="mt-6 flex justify-end gap-3">
                    {isEditMode && (
                        <button
                            type="button"
                            className="rounded-md border border-red-500 px-4 py-2 text-sm font-medium text-red-500 transition-colors hover:bg-red-500 hover:text-white disabled:cursor-not-allowed disabled:border-gray-400 disabled:text-gray-400 disabled:hover:bg-transparent disabled:hover:text-gray-400"
                            disabled={disabledDeleteButton}
                            onClick={() => setIsConfirmOpen(true)}
                        >
                            {jsonLanguage['projectModal.actions.delete']}
                        </button>
                    )}

                    <button
                        type="button"
                        className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-indigo-700 disabled:cursor-not-allowed disabled:bg-gray-400 disabled:opacity-60 disabled:hover:bg-gray-400"
                        disabled={disabledSaveButton}
                        onClick={() => handleUpsertProject()}
                    >
                        {isEditMode ? jsonLanguage['projectModal.actions.edit'] : jsonLanguage['projectModal.actions.create']}
                    </button>
                </div>
            </div>

            {isConfirmOpen && (
                <ConfirmModal
                    title={jsonLanguage['confirmModal.project.title']}
                    message={jsonLanguage['confirmModal.project.message']}
                    confirmLabel={jsonLanguage['confirmModal.actions.delete']}
                    cancelLabel={jsonLanguage['confirmModal.actions.cancel']}
                    isSubmitting={isSubmitting}
                    onCancel={() => setIsConfirmOpen(false)}
                    onConfirm={handleDeleteProject}
                />
            )}
        </div>
    );
}

export default ProjectModal;
