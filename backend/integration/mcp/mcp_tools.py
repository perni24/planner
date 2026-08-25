from db.repositories import mcp_repo
import services.mcp_service as mcpService

from .models import CreateArea

def register_mcp_tools(mcp):

    @mcp.tool()
    def get_all_projects() -> list[dict]:
        """ Restituisce tutti progetti. """
        return mcp_repo.get_all_projects()

    @mcp.tool()
    def bulk_insert_area(areas: list[CreateArea]) -> dict:
        """Crea più aree in una singola operazione."""
        names = [area.name for area in areas]
        return mcpService.bulk_insert_area(names)

    @mcp.tool()
    def bulk_insert_project()