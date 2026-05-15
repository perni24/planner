import { useState } from "react";
import { insertProject } from "../api";
import { useArea } from "../context/areaContext";

function ProjectModal({ onClose, refreshFunction}) {

    const {currentArea} = useArea(); 
    const [projectName, setProjectName] = useState('');
    const [projectDescription, setProjectDescription] = useState(''); 

    async function handleInsertProject(){
        await insertProject(currentArea.id, projectName, projectDescription); 
        refreshFunction(); 
        onClose(); 
    }

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 px-4">
            <div className="w-full max-w-lg rounded-lg border border-main-border bg-main-card p-6 text-main-text shadow-xl">
                <div className="flex items-start justify-between gap-4">
                    <div>
                        <h2 className="text-xl font-semibold">Nuovo progetto</h2>
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
                            Nome progetto
                        </label>
                        <input
                            id="project-name"
                            type="text"
                            placeholder="Es. Nuovo sito web"
                            className="mt-2 block w-full rounded-md border border-main-border bg-main-bg px-3 py-2 text-sm text-main-text shadow-sm outline-none transition-colors placeholder:text-main-text/50 focus:border-blue-500 focus:ring-2 focus:ring-blue-500"
                            onChange={(e) => setProjectName(e.target.value)}
                        />
                    </div>

                    <div>
                        <label htmlFor="project-description" className="text-sm font-medium">
                            Descrizione
                        </label>
                        <textarea
                            id="project-description"
                            rows="4"
                            placeholder="Descrivi brevemente il progetto"
                            className="mt-2 block w-full resize-none rounded-md border border-main-border bg-main-bg px-3 py-2 text-sm text-main-text shadow-sm outline-none transition-colors placeholder:text-main-text/50 focus:border-blue-500 focus:ring-2 focus:ring-blue-500"
                            onChange={(e) => setProjectDescription(e.target.value)}
                        />
                    </div>
                </div>

                <div className="mt-6 flex justify-end gap-3">
                    <button
                        type="button"
                        className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-indigo-700"
                        onClick={() => handleInsertProject()}
                    >
                        Crea
                    </button>
                </div>
            </div>
        </div>
    );
}

export default ProjectModal;
