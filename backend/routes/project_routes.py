from starlette.responses import JSONResponse
from starlette.routing import Route
import db.repositories.project_repo as projectRepo


async def get_all_projects(request):
    projects = projectRepo.get_all_projects()
    return JSONResponse(projects)

async def insert_project(request):

    data = await request.json()

    name = data.get("name")
    description = data.get("description")

    if not name:
        return JSONResponse({"error": "campo name obbligatorio"}, status_code=400)

    projectRepo.insert_project(name,description)

    return JSONResponse({"message": "Progetto inserito con successo"})

async def delete_project(request):

    data = await request.json()

    id = data.get("id")

    projectRepo.delete_project(id)

    return JSONResponse({"message" : "Progetto eliminato con successo"})


# Configurazione delle rotte
routes = [
    Route("/get_all_projects", endpoint=get_all_projects),
    Route("/insert_project", endpoint=insert_project, methods=["POST"]),
    Route("/delete_project", endpoint=delete_project, methods=["POST"])
]

