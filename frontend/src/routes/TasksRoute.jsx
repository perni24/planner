import { useParams } from 'react-router-dom';
import Tasks from '../pages/Tasks';

export default function TasksRoute() {
  const { projectId } = useParams();
  return <Tasks key={projectId} projectId={Number(projectId)} />;
}
