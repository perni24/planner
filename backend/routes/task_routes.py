from starlette.responses import JSONResponse
from starlette.routing import Route
import db.repositories.task_repo as taskRepo

async def get_tasks_by_project(request):
    project_id = request.query_params.get("project_id")
    task = taskRepo.get_tasks_by_project(project_id)
    return JSONResponse(task)

# Configurazione delle rotte
routes = [
    Route("/get_tasks_by_project", endpoint=get_tasks_by_project),
]
