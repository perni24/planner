from starlette.responses import JSONResponse
from starlette.routing import Route
import db.repositories.project_repo as projectRepo
from validators.request_validator import validate_payload


async def get_all_projects(request):
    projects = projectRepo.get_all_projects()
    return JSONResponse(projects)

async def get_projects_by_area(request):
    area_id = request.query_params.get("area_id")
    values, error = validate_payload({"area_id": area_id}, ["area_id"])
    if error:
        return JSONResponse({"error": error}, status_code=400)
    projects = projectRepo.get_projects_by_area(values["area_id"])
    return JSONResponse(projects)

async def get_project(request):
    project_id = request.query_params.get("project_id")
    values, error = validate_payload({"project_id": project_id}, ["project_id"])
    if error:
        return JSONResponse({"error": error}, status_code=400)
    project = projectRepo.get_project(values["project_id"])
    return JSONResponse(project)

async def insert_project(request):
    data = await request.json()
    values, error = validate_payload(data, ["area_id", "name", "description"])
    if error:
        return JSONResponse({"error": error}, status_code=400)
    projectRepo.insert_project(values["area_id"], values["name"], values["description"])
    return JSONResponse({"message": "Project insert successful"})

async def update_project(request):
    data = await request.json()
    values, error = validate_payload(data, ["project_id", "name", "description"])
    if error:
        return JSONResponse({"error": error}, status_code=400)
    projectRepo.update_project(values["project_id"], values["name"], values["description"])
    return JSONResponse({"message": "Project updated successful"})

async def delete_project(request):
    data = await request.json()
    values, error = validate_payload(data, ["project_id"])
    if error:
        return JSONResponse({"error": error}, status_code=400)
    projectRepo.delete_project(values["project_id"])
    return JSONResponse({"message" : "Project deleted successfully"})


# Configurazione delle rotte
routes = [
    Route("/get_all_projects", endpoint=get_all_projects),
    Route("/get_projects_by_area", endpoint=get_projects_by_area),
    Route("/get_project", endpoint=get_project),
    Route("/insert_project", endpoint=insert_project, methods=["POST"]),
    Route("/update_project", endpoint=update_project, methods=["POST"]),
    Route("/delete_project", endpoint=delete_project, methods=["POST"])
]

