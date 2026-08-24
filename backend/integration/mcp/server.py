from mcp.server.mcpserver import MCPServer

from integration.mcp.mcp_tools import register_mcp_tools

planner_mcp = MCPServer(
    "Planner",
    instructions=(
        "Permette di consultare e gestire aree, progetti e task."
    ),
)

register_mcp_tools(planner_mcp)

mcp_app = planner_mcp.streamable_http_app(
    streamable_http_path="/",
    stateless_http=True,
    json_response=True,
)
