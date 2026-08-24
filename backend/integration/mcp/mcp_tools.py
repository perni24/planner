from db.repositories import mcp_repo

def register_mcp_tools(mcp):

    @mcp.tool()
    def get_all_projects() -> list[dict]:
        """Restituisce tutti progetti."""
        return mcp_repo.get_all_projects()