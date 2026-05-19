from starlette.responses import JSONResponse
from starlette.routing import Route
import db.repositories.task_repo as taskRepo

async def get_tasks_by_project(request):
    project_id = request.query_params.get("project_id")
    task = taskRepo.get_tasks_by_project(project_id)
    return JSONResponse(task)

async def insert_task(request):
    data = await request.json()
    project_id = data.get("project_id")
    title = data.get("title")
    description = data.get("description")
    taskRepo.insert_task(project_id, title, description)
    return JSONResponse({"message": "Task insert successful"})

async def delete_task(request): 
    data = await request.json()
    task_id = data.get("task_id")
    taskRepo.delete_task(task_id)
    return JSONResponse({"message": "Task delete successful"}) 


# Configurazione delle rotte
routes = [
    Route("/get_tasks_by_project", endpoint=get_tasks_by_project),
    Route("/insert_task", endpoint=insert_task, methods=["POST"]),
    Route("/delete_task", endpoint=delete_task, methods=["POST"]),
]
