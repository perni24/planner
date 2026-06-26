from starlette.responses import JSONResponse
from starlette.routing import Route
import db.repositories.task_repo as taskRepo
from validators.request_validator import validate_payload

async def get_all_tasks(request):
    tasks = taskRepo.get_all_tasks()
    return JSONResponse(tasks)

async def get_tasks_by_project(request):
    project_id = request.query_params.get("project_id")
    values, error = validate_payload({"project_id": project_id}, ["project_id"])
    if error:
        return JSONResponse({"error": error}, status_code=400)
    tasks = taskRepo.get_tasks_by_project(values["project_id"])
    return JSONResponse(tasks)

async def insert_task(request):
    data = await request.json()
    values, error = validate_payload(data, ["project_id", "title", "description"])
    if error:
        return JSONResponse({"error": error}, status_code=400)
    taskRepo.insert_task(values["project_id"], values["title"], values["description"])
    return JSONResponse({"message": "Task insert successful"})

async def update_task(request):
    data = await request.json()
    values, error = validate_payload(data, ["task_id", "title", "description"])
    if error:
        return JSONResponse({"error": error}, status_code=400)
    updated_rows = taskRepo.update_task(values["task_id"], values["title"], values["description"])
    if updated_rows == 0:
        return JSONResponse({"error": "Task not found"}, status_code=404)
    return JSONResponse({"message": "Task update successful"})

async def update_status_task(request):
    data = await request.json()
    values, error = validate_payload(data, ["task_id"])
    if error:
        return JSONResponse({"error": error}, status_code=400)
    updated_rows = taskRepo.update_status_task(values["task_id"])
    if updated_rows == 0:
        return JSONResponse({"error": "Task not found"}, status_code=404)
    return JSONResponse({"message": "Task update successful"})

async def delete_task(request): 
    data = await request.json()
    values, error = validate_payload(data, ["task_id"])
    if error:
        return JSONResponse({"error": error}, status_code=400)
    deleted_rows = taskRepo.delete_task(values["task_id"])
    if deleted_rows == 0:
        return JSONResponse({"error": "Task not found"}, status_code=404)
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
