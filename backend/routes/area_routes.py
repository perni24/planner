from starlette.responses import JSONResponse
from starlette.routing import Route
import db.repositories.area_repo as areaRepo

async def get_all_areas(request): 
    areas = areaRepo.get_all_areas()
    return JSONResponse(areas)

async def insert_area(request):
    data = await request.json()

    name = data.get("name")

    if not name:
        return JSONResponse({"error": "campo name obbligatorio"}, status_code=400)
    
    areaRepo.insert_area(name)

    return JSONResponse({"message": "area insert successful"})


routes = [
    Route("/get_all_areas", endpoint=get_all_areas),
    Route("/insert_area", endpoint=insert_area, methods=["POST"]),
]