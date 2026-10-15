import { useNavigate, useParams } from 'react-router-dom';
import {
  getTasksByProject,
  getProject,
  insertTask,
  updateTask,
  deleteTask,
  updateTaskStatus,
  updateProject,
  deleteProject,
} from '../api';
import { useEffect, useEffectEvent, useState } from 'react';
import TaskCard from '../components/TaskCard';
import TaskModal from '../components/TaskModal';
import ProjectModal from '../components/ProjectModal';
import { useLanguage } from '../context/useLanguage';
import { useDataSync } from '../context/useDataSync';
import { useToast } from '../context/useToast';

function Tasks() {
  const { projectId } = useParams();
  const navigate = useNavigate();
  const { jsonLanguage } = useLanguage();
  const { lastEvent } = useDataSync();
  const { showToast } = useToast();
  const [project, setProject] = useState(null);
  const [tasks, setTasks] = useState([]);
  const [isTaskModalOpen, setIsTaskModalOpen] = useState(false);
  const [selectedTask, setSelectedTask] = useState(null);
  const [isTaskEditMode, setIsTaskEditMode] = useState(false);
  const [initialParentId, setInitialParentId] = useState(null);
  const [isProjectModalOpen, setIsProjectModalOpen] = useState(false);

  const topLevelTasks = tasks.filter((task) => task.parent_id == null);
  const openTasks = topLevelTasks.filter((task) => task.completed === 0);
  const completedTasks = topLevelTasks.filter((task) => task.completed === 1);
  const subtasksByParent = {};
  tasks.forEach((task) => {
    if (task.parent_id != null) {
      if (!subtasksByParent[task.parent_id]) subtasksByParent[task.parent_id] = [];
      subtasksByParent[task.parent_id].push(task);
    }
  });
  const getSubtasks = (taskId) => subtasksByParent[taskId] ?? [];
  const totalTasks = topLevelTasks.length;
  const completedCount = topLevelTasks.filter((task) => task.completed === 1).length;
  const completionPercentage = totalTasks === 0 ? 0 : Math.round((completedCount / totalTasks) * 100);

  async function loadProject() {
    try {
      const response = await getProject(Number(projectId));
      setProject(response);
    } catch (error) {
      console.error('Error loading project:', error);
    }
  }

  async function loadTasks() {
    try {
      const response = await getTasksByProject(Number(projectId));
      setTasks(response);
    } catch (error) {
      console.error('Error loading tasks:', error);
    }
  }

  async function handleSaveTask({ title, description, parentId }) {
    if ((!isTaskEditMode && !Number(projectId)) || (isTaskEditMode && !selectedTask?.id)) {
      showToast(jsonLanguage['taskModal.toast.invalidData'], 'error');
      throw new Error('Missing project or task id');
    }

    try {
      if (isTaskEditMode) {
        await updateTask(selectedTask.id, title, description);
      } else {
        await insertTask(Number(projectId), title, description, parentId);
      }
      await loadTasks();
      showToast(jsonLanguage[isTaskEditMode ? 'taskModal.toast.updated' : 'taskModal.toast.created'], 'success');
    } catch (error) {
      console.error(error);
      showToast(jsonLanguage['taskModal.toast.errorSave'], 'error');
      throw error;
    }
  }

  async function handleDeleteTask(id) {
    if (!id) {
      showToast(jsonLanguage['taskModal.toast.invalidData'], 'error');
      throw new Error('Missing task id');
    }

    try {
      await deleteTask(id);
      await loadTasks();
      showToast(jsonLanguage['taskModal.toast.deleted'], 'success');
    } catch (error) {
      console.error(error);
      showToast(jsonLanguage['taskModal.toast.errorDelete'], 'error');
      throw error;
    }
  }

  async function handleToggleTask(task) {
    if (!task?.id) {
      showToast(jsonLanguage['taskCard.toast.invalidData'], 'error');
      throw new Error('Missing task id');
    }

    try {
      await updateTaskStatus(task.id);
      await loadTasks();
    } catch (error) {
      console.error(error);
      showToast(jsonLanguage['taskCard.toast.errorUpdateStatus'], 'error');
      throw error;
    }
  }

  async function handleSaveProject({ name, description }) {
    if (!project?.id) {
      showToast(jsonLanguage['projectModal.toast.invalidData'], 'error');
      throw new Error('Missing project id');
    }

    try {
      await updateProject(project.id, name, description);
      await loadProject();
      showToast(jsonLanguage['projectModal.toast.updated'], 'success');
    } catch (error) {
      console.error(error);
      showToast(jsonLanguage['projectModal.toast.errorSave'], 'error');
      throw error;
    }
  }

  async function handleDeleteProject(id) {
    if (!id) {
      showToast(jsonLanguage['projectModal.toast.invalidData'], 'error');
      throw new Error('Missing project id');
    }

    try {
      await deleteProject(id);
      showToast(jsonLanguage['projectModal.toast.deleted'], 'success');
      navigate('/');
    } catch (error) {
      console.error(error);
      showToast(jsonLanguage['projectModal.toast.errorDelete'], 'error');
      throw error;
    }
  }

  const reloadTaskPageFromEvent = useEffectEvent((entity) => {
    if (entity === 'task') {
      loadTasks();
    }

    if (entity === 'project') {
      loadProject();
    }
  });

  function openNewTaskModal() {
    setSelectedTask(null);
    setIsTaskEditMode(false);
    setInitialParentId(null);
    setIsTaskModalOpen(true);
  }

  function openAddSubtaskModal(task) {
    setSelectedTask(null);
    setIsTaskEditMode(false);
    setInitialParentId(task.id);
    setIsTaskModalOpen(true);
  }

  function openEditTaskModal(task) {
    setSelectedTask(task);
    setIsTaskEditMode(true);
    setIsTaskModalOpen(true);
  }

  useEffect(() => {
    async function loadInitialData() {
      const id = Number(projectId);

      try {
        const projectResponse = await getProject(id);
        setProject(projectResponse);
      } catch (error) {
        console.error('Error loading project:', error);
      }

      try {
        const tasksResponse = await getTasksByProject(id);
        setTasks(tasksResponse);
      } catch (error) {
        console.error('Error loading tasks:', error);
      }
    }

    loadInitialData();
  }, [projectId]);

  useEffect(() => {
    if (lastEvent) {
      reloadTaskPageFromEvent(lastEvent.entity);
    }
  }, [lastEvent]);

  return (
    <div className="w-full space-y-8 text-main-text">
      <section className="rounded-2xl border border-main-border bg-main-card p-6 shadow-md">
        <div className="flex flex-col gap-6 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <p className="text-sm font-medium text-main-text/70">{jsonLanguage['tasksPage.project']}</p>
            <h1 className="mt-2 text-3xl font-bold">{project?.name ?? jsonLanguage['tasksPage.loadingProject']}</h1>
            <p className="mt-3 max-w-2xl text-sm leading-6 text-main-text/75">
              {project?.description ?? jsonLanguage['tasksPage.noDescription']}
            </p>
          </div>

          <div className="flex gap-3">
            <button
              type="button"
              onClick={() => setIsProjectModalOpen(true)}
              className="rounded-lg border border-main-border px-4 py-2 text-sm font-semibold text-main-text transition-colors hover:bg-main-hover hover:text-main-hover-text"
            >
              {jsonLanguage['tasksPage.actions.editProject']}
            </button>

            <button
              type="button"
              onClick={openNewTaskModal}
              className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-indigo-700"
            >
              {jsonLanguage['tasksPage.actions.newTask']}
            </button>
          </div>
        </div>

        <div className="mt-8">
          <div className="flex items-center justify-between text-sm">
            <span>{completedCount}/{totalTasks} {jsonLanguage['tasksPage.progress.completedTasks']}</span>
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
          <h2 className="text-xl font-semibold">{jsonLanguage['tasksPage.openTasks.title']}</h2>
          <span className="rounded-full border border-main-border px-3 py-1 text-xs text-main-text/70">
            {openTasks.length} {jsonLanguage['tasksPage.openTasks.count']}
          </span>
        </div>

        {openTasks.length === 0 ? (
          <div className="rounded-xl border border-dashed border-main-border bg-main-card p-6 text-sm text-main-text/70">
            {jsonLanguage['tasksPage.openTasks.empty']}
          </div>
        ) : (
          openTasks.map((task) => (
            <TaskCard key={task.id} task={task} subtasks={getSubtasks(task.id)} onEdit={openEditTaskModal} onAddSubtask={openAddSubtaskModal} onToggle={handleToggleTask}/>
          ))
        )}
      </section>

      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-semibold">{jsonLanguage['tasksPage.completedTasks.title']}</h2>
          <span className="rounded-full border border-main-border px-3 py-1 text-xs text-main-text/70">
            {completedTasks.length} {jsonLanguage['tasksPage.completedTasks.count']}
          </span>
        </div>

        {completedTasks.length === 0 ? (
          <div className="rounded-xl border border-dashed border-main-border bg-main-card p-6 text-sm text-main-text/70">
            {jsonLanguage['tasksPage.completedTasks.empty']}
          </div>
        ) : (
          completedTasks.map((task) => (
            <TaskCard key={task.id} task={task} subtasks={getSubtasks(task.id)} onEdit={openEditTaskModal} onAddSubtask={openAddSubtaskModal} onToggle={handleToggleTask}/>
          ))
        )}
      </section>

      {isTaskModalOpen && (
        <TaskModal
          onClose={() => setIsTaskModalOpen(false)}
          isEditMode={isTaskEditMode}
          task={selectedTask}
          onSave={handleSaveTask}
          onDelete={handleDeleteTask}
          project_id={Number(projectId)}
          parentOptions={topLevelTasks}
          initialParentId={initialParentId}
        />
      )}

      {isProjectModalOpen && (
        <ProjectModal
          onClose={() => setIsProjectModalOpen(false)}
          onSave={handleSaveProject}
          onDelete={handleDeleteProject}
          isEditMode={true}
          project={project}
        />
      )}
    </div>
  );
}

export default Tasks;
