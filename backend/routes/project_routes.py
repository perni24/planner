from starlette.responses import JSONResponse
from starlette.routing import Route
import db.repositories.project_repo as projectRepo


async def get_all_projects(request):
    projects = projectRepo.get_all_projects()
    return JSONResponse(projects)

async def get_projects_by_area(request):
    area_id = request.query_params.get("area_id")
    projects = projectRepo.get_projects_by_area(area_id)
    return JSONResponse(projects)

async def get_project(request):
    project_id = request.query_params.get("project_id")
    project = projectRepo.get_project(project_id)
    return JSONResponse(project)

async def insert_project(request):
    data = await request.json()
    area_id = data.get("area_id")
    name = data.get("name")
    description = data.get("description")
    if not name:
        return JSONResponse({"error": "campo name obbligatorio"}, status_code=400)
    projectRepo.insert_project(area_id, name, description)
    return JSONResponse({"message": "Project insert successful"})

async def update_project(request):
    data = await request.json()
    project_id = data.get("project_id")
    name = data.get("name")
    description = data.get("description")
    projectRepo.update_project(project_id, name, description)
    return JSONResponse({"message": "Project updated successful"})

async def delete_project(request):
    data = await request.json()
    project_id = data.get("project_id")
    projectRepo.delete_project(project_id)
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

