import { useState, useEffect } from 'react';
import { getProjectByArea } from '../api';
import ProjectCard from '../components/ProjectCard';
import ProjectModal from '../components/ProjectModal';
import { useArea } from "../context/useArea";
import { Link } from 'react-router-dom';

function Project() {

  const {currentArea} = useArea(); 

  const [projects, setProjects] = useState([]);
  const [isProjectModalOpen, setIsProjectModalOpen] = useState(false);
  
  async function loadProjects() {
    if (!currentArea?.id) {
      return;
    }

    try{
      const response = await getProjectByArea(currentArea.id);
      setProjects(response);
    }catch (error) {
      console.error('Error loading projects:', error);
    }
  }

  useEffect(() => {
    async function loadInitialProjects() {
      if (!currentArea?.id) {
        return;
      }

      try {
        const response = await getProjectByArea(currentArea.id);
        setProjects(response);
      } catch (error) {
        console.error('Error loading projects:', error);
      }
    }

    loadInitialProjects();
  }, [currentArea?.id]);



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
      <ProjectModal onClose={() => setIsProjectModalOpen(false)} refreshFunction={loadProjects} />
    )}
    </>
  );
}

export default Project;
