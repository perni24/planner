from mcp.server.fastmcp import FastMCP

from integrations.mcp.project_tools import register_project_tools

planner_mcp = FastMCP(
    "Planner",
    instructions=(
        "Permette di consultare e gestire aree, progetti e task."
    ),
    streamable_http_path="/",
)

register_project_tools(planner_mcp)

mcp_app = planner_mcp.streamable_http_app(
    stateless_http=True,
    json_response=True,
)