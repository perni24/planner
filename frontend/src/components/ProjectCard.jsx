import { useLanguage } from "../context/LanguageContext";

function ProjectCard({ data, nuovo_progetto = false, onClick }) {
  const { jsonLanguage } = useLanguage();

  const totalTasks = data?.total_tasks ?? 0;
  const completedTasks = data?.completed_tasks ?? 0;
  const completionPercentage = data?.completion_percentage ?? 0;
  const isCompleted = totalTasks > 0 && completionPercentage === 100;


  if (nuovo_progetto) {
    return (
      <div
        onClick={onClick}
        className="group flex aspect-square cursor-pointer flex-col rounded-xl border border-dashed border-main-border bg-main-card p-4 text-main-text shadow-md transition-all duration-200 hover:-translate-y-1 hover:border-indigo-500 hover:bg-main-hover hover:shadow-xl"
      >
        <h2 className="text-center text-xl font-semibold">
          {jsonLanguage['cardProject.new']}
        </h2>
        <p className="flex flex-1 items-center justify-center text-6xl font-bold transition-transform duration-200 group-hover:scale-110">
          +
        </p>
        <p className="text-center text-sm text-main-text/70">
          {jsonLanguage['cardProject.createDescription']}
        </p>
      </div>
    );
  }

  return (
    <div
      onClick={onClick}
      className="group flex aspect-square cursor-pointer flex-col rounded-xl border border-main-border bg-main-card p-4 text-main-text shadow-md transition-all duration-200 hover:-translate-y-1 hover:border-indigo-500 hover:bg-main-hover hover:shadow-xl"
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold">{data?.name ?? jsonLanguage['cardProject.untitled']}</h2>
          <p className="mt-2 line-clamp-2 text-sm text-main-text/70">
            {data?.description ?? jsonLanguage['cardProject.noDescription']}
          </p>
        </div>

        {isCompleted && (
          <span className="rounded-full bg-indigo-600 px-2 py-1 text-xs font-semibold text-white">
            {jsonLanguage['cardProject.completed']}
          </span>
        )}
      </div>

      <div className="mt-auto space-y-3">
        {data?.area_name && (
          <p className="text-xs text-main-text/60">
            {jsonLanguage['cardProject.area']}: {data.area_name}
          </p>
        )}

        <div>
          <div className="flex justify-between text-xs text-main-text/70">
            <span>{completedTasks}/{totalTasks} {jsonLanguage['cardProject.task']}</span>
            <span>{completionPercentage}%</span>
          </div>

          <div className="mt-2 h-2 overflow-hidden rounded-full bg-main-bg">
            <div
              className="h-full rounded-full bg-indigo-600 transition-all duration-300"
              style={{ width: `${completionPercentage}%` }}
            />
          </div>
        </div>

      </div>
    </div>
  );
}

export default ProjectCard;
