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
        """Return all areas, including areas without projects."""
        return mcpService.get_all_areas()

    @mcp.tool()
    def get_all_projects() -> list[dict]:
        """Return all projects with their current status."""
        return mcp_repo.get_all_projects()

    @mcp.tool()
    def get_project_tasks(project_id: int) -> dict:
        """Return all tasks and subtasks belonging to a project."""
        return mcpService.get_project_tasks(project_id)

    @mcp.tool()
    def bulk_insert_area(areas: list[CreateArea]) -> dict:
        """Create multiple areas in a single operation."""
        names = [area.name for area in areas]
        return mcpService.bulk_insert_area(names)

    @mcp.tool()
    def bulk_insert_project(projects: list[CreateProject]) -> dict:
        """Create multiple projects in a single operation."""
        project_data = [project.model_dump() for project in projects]
        return mcpService.bulk_insert_project(project_data)

    @mcp.tool()
    def bulk_insert_task(tasks: list[CreateTask]) -> dict:
        """Create multiple tasks and subtasks in a single operation."""
        task_data = [task.model_dump() for task in tasks]
        return mcpService.bulk_insert_task(task_data)

    @mcp.tool()
    def bulk_update_project(projects: list[UpdateProject]) -> dict:
        """Update multiple projects in a single operation."""
        project_data = [project.model_dump() for project in projects]
        return mcpService.bulk_update_project(project_data)

    @mcp.tool()
    def bulk_update_task(tasks: list[UpdateTask]) -> dict:
        """Update multiple tasks in a single operation."""
        task_data = [task.model_dump() for task in tasks]
        return mcpService.bulk_update_task(task_data)

    @mcp.tool()
    def bulk_set_task_completed(tasks: list[SetTaskCompleted]) -> dict:
        """Set the completion status of multiple tasks in one operation."""
        task_data = [task.model_dump() for task in tasks]
        return mcpService.bulk_set_task_completed(task_data)
