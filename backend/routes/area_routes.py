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

async def update_area(request):
    data = await request.json()
    id = data.get("id")
    name = data.get("name")
    if not id:
        return JSONResponse({"error": "campo id obbligatorio"}, status_code=400)
    if not name:
        return JSONResponse({"error": "campo name obbligatorio"}, status_code=400)
    areaRepo.update_area(id, name)
    return JSONResponse({"message": "area update successful"})

async def delete_area(request):
    data = await request.json()
    id = data.get("id")
    if not id:
        return JSONResponse({"error": "campo id obbligatorio"}, status_code=400)
    areaRepo.delete_area(id)
    return JSONResponse({"message": "area delete successful"})



routes = [
    Route("/get_all_areas", endpoint=get_all_areas),
    Route("/insert_area", endpoint=insert_area, methods=["POST"]),
    Route("/update_area", endpoint=update_area, methods=["PUT"]), 
    Route("/delete_area", endpoint=delete_area, methods=["DELETE"])
]