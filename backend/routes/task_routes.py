from starlette.responses import JSONResponse
from starlette.routing import Route
import db.repositories.task_repo as taskRepo

async def get_all_tasks(request):
    tasks = taskRepo.get_all_tasks()
    return JSONResponse(tasks)

async def get_tasks_by_project(request):
    project_id = request.query_params.get("project_id")
    tasks = taskRepo.get_tasks_by_project(project_id)
    return JSONResponse(tasks)

async def insert_task(request):
    data = await request.json()
    project_id = data.get("project_id")
    title = data.get("title")
    description = data.get("description")
    taskRepo.insert_task(project_id, title, description)
    return JSONResponse({"message": "Task insert successful"})

async def update_task(request):
    data = await request.json()
    task_id = data.get("task_id")
    title = data.get("title")
    description = data.get("description")
    taskRepo.update_task(task_id, title, description)
    return JSONResponse({"message": "Task update successful"})

async def update_status_task(request):
    data = await request.json()
    task_id = data.get("task_id")
    taskRepo.update_status_task(task_id)
    return JSONResponse({"message": "Task update successful"})

async def delete_task(request): 
    data = await request.json()
    task_id = data.get("task_id")
    taskRepo.delete_task(task_id)
    return JSONResponse({"message": "Task delete successful"}) 


# Configurazione delle rotte
routes = [
    Route("/get_all_tasks", endpoint=get_all_tasks), 
    Route("/get_tasks_by_project", endpoint=get_tasks_by_project),
    Route("/insert_task", endpoint=insert_task, methods=["POST"]),
    Route("/update_task", endpoint=update_task, methods=["POST"]), 
    Route("/update_status_task", endpoint=update_status_task, methods=["POST"]),
    Route("/delete_task", endpoint=delete_task, methods=["POST"])
]
