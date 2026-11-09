import Project from '../pages/Project';
import { useArea } from '../context/useArea';

export default function ProjectRoute() {
  const { currentArea } = useArea();
  const areaId = currentArea?.id;
  return <Project key={areaId} areaId={areaId} />;
}
