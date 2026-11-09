import { useEffect, useEffectEvent, useState } from 'react';
import { getProjectsByArea, insertProject } from '../api';
import ProjectCard from '../components/ProjectCard';
import ProjectModal from '../components/ProjectModal';
import { Link } from 'react-router-dom';
import { useDataSync } from '../context/useDataSync';
import { useLanguage } from '../context/useLanguage';
import { useToast } from '../context/useToast';
import { useLatestRead } from '../hooks/useLatestRead';

function Project({ areaId }) {
  const { lastEvent } = useDataSync();
  const { jsonLanguage } = useLanguage();
  const { showToast } = useToast();

  const [projects, loadProjects] = useLatestRead(
    (signal) => areaId ? getProjectsByArea(areaId, signal) : [],
    [],
    'Error loading projects:',
  );
  const [isProjectModalOpen, setIsProjectModalOpen] = useState(false);

  async function handleSaveProject({ name, description }) {
    if (!areaId) {
      showToast(jsonLanguage['projectModal.toast.invalidData'], 'error');
      throw new Error('No area selected');
    }

    try {
      await insertProject(areaId, name, description);
      await loadProjects();
      showToast(jsonLanguage['projectModal.toast.created'], 'success');
    } catch (error) {
      console.error(error);
      showToast(jsonLanguage['projectModal.toast.errorSave'], 'error');
      throw error;
    }
  }

  const reloadProjectsFromEvent = useEffectEvent(loadProjects);

  useEffect(() => {
    reloadProjectsFromEvent();
  }, []);

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
        areaId={areaId}
      />
    )}
    </>
  );
}

export default Project;
