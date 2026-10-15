import { useEffect, useEffectEvent, useState } from 'react';
import { getProjectsByArea, insertProject } from '../api';
import ProjectCard from '../components/ProjectCard';
import ProjectModal from '../components/ProjectModal';
import { useArea } from "../context/useArea";
import { Link } from 'react-router-dom';
import { useDataSync } from '../context/useDataSync';
import { useLanguage } from '../context/useLanguage';
import { useToast } from '../context/useToast';

function Project() {

  const {currentArea} = useArea(); 
  const { lastEvent } = useDataSync();
  const { jsonLanguage } = useLanguage();
  const { showToast } = useToast();

  const [projects, setProjects] = useState([]);
  const [isProjectModalOpen, setIsProjectModalOpen] = useState(false);
  
  async function loadProjects() {
    if (!currentArea?.id) {
      return;
    }

    try{
      const response = await getProjectsByArea(currentArea.id);
      setProjects(response);
    }catch (error) {
      console.error('Error loading projects:', error);
    }
  }

  async function handleSaveProject({ name, description }) {
    if (!currentArea?.id) {
      showToast(jsonLanguage['projectModal.toast.invalidData'], 'error');
      throw new Error('No area selected');
    }

    try {
      await insertProject(currentArea.id, name, description);
      await loadProjects();
      showToast(jsonLanguage['projectModal.toast.created'], 'success');
    } catch (error) {
      console.error(error);
      showToast(jsonLanguage['projectModal.toast.errorSave'], 'error');
      throw error;
    }
  }

  const reloadProjectsFromEvent = useEffectEvent(() => {
    loadProjects();
  });

  useEffect(() => {
    async function loadInitialProjects() {
      if (!currentArea?.id) {
        return;
      }

      try {
        const response = await getProjectsByArea(currentArea.id);
        setProjects(response);
      } catch (error) {
        console.error('Error loading projects:', error);
      }
    }

    loadInitialProjects();
  }, [currentArea?.id]);

  useEffect(() => {
    if (
      lastEvent?.entity === 'project' ||
      lastEvent?.entity === 'task'
    ) {
      reloadProjectsFromEvent();
    }
  }, [lastEvent]);



  return (
    <>
    <div className="grid w-full grid-cols-1 md:grid-cols-4 lg:grid-cols-6 gap-x-8 gap-y-8">
        <ProjectCard nuovo_progetto={true} onClick={() => setIsProjectModalOpen(true)} />
        {projects.map((project) => (
          <Link key={project.id} to={`tasks/${project.id}`}>
            <ProjectCard data={project} />
          </Link>
        ))}
    </div>

    {isProjectModalOpen && (
      <ProjectModal
        onClose={() => setIsProjectModalOpen(false)}
        onSave={handleSaveProject}
        areaId={currentArea?.id}
      />
    )}
    </>
  );
}

export default Project;
