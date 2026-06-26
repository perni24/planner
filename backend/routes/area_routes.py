from starlette.responses import JSONResponse
from starlette.routing import Route
import db.repositories.area_repo as areaRepo
from validators.request_validator import validate_payload

async def get_all_areas(request): 
    areas = areaRepo.get_all_areas()
    return JSONResponse(areas)

async def insert_area(request):
    data = await request.json()
    values, error = validate_payload(data, ["name"])
    if error:
        return JSONResponse({"error": error}, status_code=400)
    areaRepo.insert_area(values["name"])
    return JSONResponse({"message": "area insert successful"})

async def update_area(request):
    data = await request.json()
    values, error = validate_payload(data, ["id", "name"])
    if error:
        return JSONResponse({"error": error}, status_code=400)
    updated_rows = areaRepo.update_area(values["id"], values["name"])
    if updated_rows == 0:
        return JSONResponse({"error": "area not found"}, status_code=404)
    return JSONResponse({"message": "area update successful"})

async def delete_area(request):
    data = await request.json()
    values, error = validate_payload(data, ["id"])
    if error:
        return JSONResponse({"error": error}, status_code=400)
    deleted_rows = areaRepo.delete_area(values["id"])
    if deleted_rows == 0:
        return JSONResponse({"error": "area not found"}, status_code=404)
    return JSONResponse({"message": "area delete successful"})



routes = [
    Route("/get_all_areas", endpoint=get_all_areas),
    Route("/insert_area", endpoint=insert_area, methods=["POST"]),
    Route("/update_area", endpoint=update_area, methods=["PUT"]), 
    Route("/delete_area", endpoint=delete_area, methods=["DELETE"])
]
