import { useParams } from 'react-router-dom';
import { get_tasks_by_project, getProject } from '../api';
import { useEffect, useState } from 'react';
import TaskCard from '../components/TaskCard';
import TaskModal from '../components/TaskModal';
import ProjectModal from '../components/ProjectModal';

function Tasks() {
  const { projectId } = useParams();
  const [project, setProject] = useState(null);
  const [tasks, setTasks] = useState([]);
  const [error, setError] = useState(null);
  const [isTaskModalOpen, setIsTaskModalOpen] = useState(false);
  const [selectedTask, setSelectedTask] = useState(null);
  const [isTaskEditMode, setIsTaskEditMode] = useState(false);
  const [isProjectModalOpen, setIsProjectModalOpen] = useState(false);

  const openTasks = tasks.filter((task) => task.completed === 0);
  const completedTasks = tasks.filter((task) => task.completed === 1);
  const totalTasks = tasks.length;
  const completedCount = completedTasks.length;
  const completionPercentage = totalTasks === 0 ? 0 : Math.round((completedCount / totalTasks) * 100);

  async function loadProject() {
    try {
      const response = await getProject(Number(projectId));
      setProject(response);
    } catch (error) {
      setError(error.message);
    }
  }

  async function loadTasks() {
    try {
      const response = await get_tasks_by_project(Number(projectId));
      setTasks(response);
    } catch (error) {
      setError(error.message);
    }
  }

  function openNewTaskModal() {
    setSelectedTask(null);
    setIsTaskEditMode(false);
    setIsTaskModalOpen(true);
  }

  function openEditTaskModal(task) {
    setSelectedTask(task);
    setIsTaskEditMode(true);
    setIsTaskModalOpen(true);
  }

  useEffect(() => {
    loadProject();
    loadTasks();
  }, [projectId]);

  return (
    <div className="w-full space-y-8 text-main-text">
      <section className="rounded-2xl border border-main-border bg-main-card p-6 shadow-md">
        <div className="flex flex-col gap-6 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <p className="text-sm font-medium text-main-text/70">Progetto</p>
            <h1 className="mt-2 text-3xl font-bold">{project?.name ?? 'Caricamento progetto...'}</h1>
            <p className="mt-3 max-w-2xl text-sm leading-6 text-main-text/75">
              {project?.description ?? 'Nessuna descrizione disponibile.'}
            </p>
          </div>

          <div className="flex gap-3">
            <button
              type="button"
              onClick={() => setIsProjectModalOpen(true)}
              className="rounded-lg border border-main-border px-4 py-2 text-sm font-semibold text-main-text transition-colors hover:bg-main-hover hover:text-main-hover-text"
            >
              Modifica progetto
            </button>

            <button
              type="button"
              onClick={openNewTaskModal}
              className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-indigo-700"
            >
              + Nuova task
            </button>
          </div>
        </div>

        <div className="mt-8">
          <div className="flex items-center justify-between text-sm">
            <span>{completedCount}/{totalTasks} task completate</span>
            <span className="font-semibold">{completionPercentage}%</span>
          </div>
          <div className="mt-3 h-3 overflow-hidden rounded-full bg-main-bg">
            <div
              className="h-full rounded-full bg-indigo-600 transition-all duration-300"
              style={{ width: `${completionPercentage}%` }}
            />
          </div>
        </div>
      </section>

      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-semibold">Task aperte</h2>
          <span className="rounded-full border border-main-border px-3 py-1 text-xs text-main-text/70">
            {openTasks.length} da fare
          </span>
        </div>

        {openTasks.length === 0 ? (
          <div className="rounded-xl border border-dashed border-main-border bg-main-card p-6 text-sm text-main-text/70">
            Non ci sono task aperte per questo progetto.
          </div>
        ) : (
          openTasks.map((task) => (
            <TaskCard key={task.id} task={task} onEdit={openEditTaskModal} refreshFunction={loadTasks}/>
          ))
        )}
      </section>

      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-semibold">Task completate</h2>
          <span className="rounded-full border border-main-border px-3 py-1 text-xs text-main-text/70">
            {completedTasks.length} completate
          </span>
        </div>

        {completedTasks.length === 0 ? (
          <div className="rounded-xl border border-dashed border-main-border bg-main-card p-6 text-sm text-main-text/70">
            Nessuna task completata.
          </div>
        ) : (
          completedTasks.map((task) => (
            <TaskCard key={task.id} task={task} onEdit={openEditTaskModal} refreshFunction={loadTasks}/>
          ))
        )}
      </section>

      {isTaskModalOpen && (
        <TaskModal
          onClose={() => setIsTaskModalOpen(false)}
          isEditMode={isTaskEditMode}
          task={selectedTask}
          refreshFunction={loadTasks}
          project_id={Number(projectId)}
        />
      )}

      {isProjectModalOpen && (
        <ProjectModal
          onClose={() => setIsProjectModalOpen(false)}
          refreshFunction={loadProject}
          isEditMode={true}
          project={project}
        />
      )}
    </div>
  );
}

export default Tasks;
