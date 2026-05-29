import { updateStatusTask} from "../api";

function TaskCard({ task, onEdit, refreshFunction}) {
  
  const isCompleted = task.completed === 1;

  async function handleToggleStatus(){
    await updateStatusTask(task.id); 
    refreshFunction();
  }

  return (
    <article className="flex items-start gap-4 rounded-xl border border-main-border bg-main-card p-4 shadow-sm transition-colors hover:bg-main-hover hover:text-main-hover-text">
      <span
        className={
          isCompleted
            ? 'mt-1 flex h-5 w-5 items-center justify-center rounded-full bg-indigo-600 text-xs font-bold text-white'
            : 'mt-1 h-5 w-5 rounded-full border-2 border-indigo-500'
        }
        onClick={ ()=> handleToggleStatus()}
      >
        {isCompleted ? 'x' : ''}
      </span>

      <div className="flex-1">
        <h3 className={isCompleted ? 'font-semibold line-through' : 'font-semibold'}>
          {task.title}
        </h3>

        <p className="mt-1 text-sm text-main-text/70">
          {task.description ?? 'Nessuna descrizione.'}
        </p>

        <p className="mt-3 text-xs text-main-text/60">
          {isCompleted ? 'Completata' : 'Da fare'} - Creata il {task.created_at}
        </p>
      </div>

      <button
        type="button"
        onClick={() => onEdit?.(task)}
        className="rounded-md px-2 py-1 text-main-text transition-colors hover:bg-main-card hover:text-main-hover-text"
        aria-label={`Impostazioni task ${task.title}`}
      >
        <svg
          className="h-4 w-4"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          aria-hidden="true"
        >
          <circle cx="12" cy="12" r="3" />
          <path d="M19.4 15a1.7 1.7 0 0 0 .3 1.9l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.9-.3 1.7 1.7 0 0 0-1 1.6V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1-1.6 1.7 1.7 0 0 0-1.9.3l-.1.1A2 2 0 1 1 4.2 17l.1-.1a1.7 1.7 0 0 0 .3-1.9 1.7 1.7 0 0 0-1.6-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.6-1 1.7 1.7 0 0 0-.3-1.9l-.1-.1A2 2 0 1 1 7.1 4.2l.1.1a1.7 1.7 0 0 0 1.9.3h.1A1.7 1.7 0 0 0 10 3V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.6 1.7 1.7 0 0 0 1.9-.3l.1-.1A2 2 0 1 1 19.8 7l-.1.1a1.7 1.7 0 0 0-.3 1.9v.1A1.7 1.7 0 0 0 21 10h.1a2 2 0 1 1 0 4H21a1.7 1.7 0 0 0-1.6 1Z" />
        </svg>
      </button>
    </article>
  );
}

export default TaskCard;
