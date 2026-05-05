import { useState, useEffect } from 'react';
import { getAllProjects } from '../api';
import CardProgetto from '../components/CardProgetto';

function Project() {

  const [projects, setProjects] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    const loadProjects = async () => {
      try {
        const response = await getAllProjects();
        setProjects(response);
      } catch (error) {
        setError(error.message);
      }
    };

    loadProjects();
  }, []);


  return (
    <div className="grid w-full grid-cols-1 md:grid-cols-4 lg:grid-cols-6 gap-x-8 gap-y-8">
        <CardProgetto nuovo_progetto={true} />
        {projects.map((project) => (
          <CardProgetto key={project.id} data={project} />
        ))}
    </div>
  );
}

export default Project;
