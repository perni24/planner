import { useState, useEffect } from 'react';
import { getAllProjects } from '../api';

function Project() {

  const [projects, setProjects] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    const loadProjects = async () => {
      try {
        const data = await getAllProjects();
        setProjects(data);
      } catch (error) {
        setError(error.message);
      }
    };

    loadProjects();
  }, []);


  return (
    <div>
        <h1>Pagina Progetti</h1>

    </div>
  );
}

export default Project;
