from db.repositories import mcp_repo
import services.mcp_service as mcpService

from .models import (
    CreateArea,
    CreateProject,
    CreateTask,
    SetTaskCompleted,
    UpdateProject,
    UpdateTask,
)

def register_mcp_tools(mcp):

    @mcp.tool()
    def get_all_areas() -> dict:
        """Restituisce tutte le aree, incluse quelle senza progetti."""
        return mcpService.get_all_areas()

    @mcp.tool()
    def get_all_projects() -> list[dict]:
        """ Restituisce tutti progetti. """
        return mcp_repo.get_all_projects()

    @mcp.tool()
    def get_project_tasks(project_id: int) -> dict:
        """Restituisce tutte le task e sotto-task di un progetto."""
        return mcpService.get_project_tasks(project_id)

    @mcp.tool()
    def bulk_insert_area(areas: list[CreateArea]) -> dict:
        """Crea più aree in una singola operazione."""
        names = [area.name for area in areas]
        return mcpService.bulk_insert_area(names)

    @mcp.tool()
    def bulk_insert_project(projects: list[CreateProject]) -> dict:
        """Crea più progetti in una singola operazione."""
        project_data = [project.model_dump() for project in projects]
        return mcpService.bulk_insert_project(project_data)

    @mcp.tool()
    def bulk_insert_task(tasks: list[CreateTask]) -> dict:
        """Crea più task in una singola operazione."""
        task_data = [task.model_dump() for task in tasks]
        return mcpService.bulk_insert_task(task_data)

    @mcp.tool()
    def bulk_update_project(projects: list[UpdateProject]) -> dict:
        """Aggiorna più progetti in una singola operazione."""
        project_data = [project.model_dump() for project in projects]
        return mcpService.bulk_update_project(project_data)

    @mcp.tool()
    def bulk_update_task(tasks: list[UpdateTask]) -> dict:
        """Aggiorna più task in una singola operazione."""
        task_data = [task.model_dump() for task in tasks]
        return mcpService.bulk_update_task(task_data)

    @mcp.tool()
    def bulk_set_task_completed(tasks: list[SetTaskCompleted]) -> dict:
        """Imposta lo stato completato di più task in una singola operazione."""
        task_data = [task.model_dump() for task in tasks]
        return mcpService.bulk_set_task_completed(task_data)
