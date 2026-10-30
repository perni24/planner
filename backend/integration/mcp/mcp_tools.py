from typing import Annotated

from pydantic import Field, StrictBool

from db.repositories import mcp_repo
import services.mcp_service as mcpService

from .models import (
    CreateArea,
    CreateProject,
    CreateTask,
    DeleteTask,
    EntityId,
    MoveSubtask,
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
    def get_project_tasks(project_id: EntityId) -> dict:
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
        """Update multiple projects in a single operation.

        Omit `description` to keep the current one; an empty string clears it.
        """
        project_data = [project.model_dump() for project in projects]
        return mcpService.bulk_update_project(project_data)

    @mcp.tool()
    def bulk_update_task(tasks: list[UpdateTask]) -> dict:
        """Update multiple tasks in a single operation.

        Omit `description` to keep the current one; an empty string clears it.
        """
        task_data = [task.model_dump() for task in tasks]
        return mcpService.bulk_update_task(task_data)

    @mcp.tool()
    def bulk_set_task_completed(tasks: list[SetTaskCompleted]) -> dict:
        """Set the completion status of multiple tasks in one operation.

        Tasks that have subtasks cannot be set directly: their status is derived
        from their subtasks and is completed only when all of them are completed.
        """
        task_data = [task.model_dump() for task in tasks]
        return mcpService.bulk_set_task_completed(task_data)

    @mcp.tool()
    def bulk_delete_task(
        tasks: Annotated[list[DeleteTask], Field(min_length=1, max_length=50)],
        include_subtasks: StrictBool = False,
    ) -> dict:
        """Delete up to 50 tasks or subtasks atomically.

        Tasks with subtasks are rejected unless include_subtasks is explicitly
        true. When true, their subtasks are deleted too. Returns all deleted IDs,
        including cascaded subtasks. Duplicate or missing requested IDs fail
        the entire batch.
        """
        return mcpService.bulk_delete_task(
            [task.model_dump() for task in tasks], include_subtasks
        )

    @mcp.tool()
    def bulk_move_subtask(
        subtasks: Annotated[list[MoveSubtask], Field(min_length=1, max_length=50)],
    ) -> dict:
        """Move up to 50 subtasks to other top-level tasks in the same project.

        Each item supplies the subtask id and destination parent_id. Main tasks,
        cross-project moves, nested subtasks, duplicate IDs and missing tasks
        are rejected atomically. Content and completion are preserved. Moving
        to the current parent is reported as unchanged.
        """
        return mcpService.bulk_move_subtask([task.model_dump() for task in subtasks])
