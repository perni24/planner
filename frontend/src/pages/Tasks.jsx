import { useParams } from 'react-router-dom';
import { get_tasks_by_project } from '../api';
import { useState } from 'react';

function Tasks() {
  const {projectId} = useParams(); 
  const [tasks, setTasks] = useState([]);  
  const [error, setError] = useState(null);

  async function loadTasks(){
    try {
      const response = await get_tasks_by_project(Number(projectId)); 
      setTasks(response); 
    }catch (error){
      setError(error.message); 
    }
  }

  return (
    <div>
        <h1>Pagina Task</h1>
    </div>
  );
}

export default Tasks;
