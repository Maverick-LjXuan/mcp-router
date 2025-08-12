import json
import asyncio
import httpx
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from mcp.server.fastmcp import FastMCP

# Initialize the discovery service
try:
    from discovery_service import DiscoveryService
    discovery_service = DiscoveryService()
except ImportError:
    # Create a mock discovery service for testing
    class MockDiscoveryService:
        def search_server(self, query, top_k=3):
            return [{
                "server_name": "example_service",
                "server_description": "An example service for demonstration",
                "server_endpoint": "http://example.com/mcp",
                "tools": "[]",
                "score": 0.95
            }]
        
        def add_server(self, server_name, server_description, server_endpoint, tools):
            return {"status": "success", "message": f"Server '{server_name}' registered."}
        
        def get_server_endpoint(self, server_name):
            return "http://example.com/mcp"
    
    discovery_service = MockDiscoveryService()

# Try to import SSE components for services that require it
try:
    from mcp import ClientSession
    from mcp.client.sse import sse_client
    from contextlib import AsyncExitStack
    HAVE_SSE_SUPPORT = True
except ImportError:
    HAVE_SSE_SUPPORT = False
    print("MCP SSE components not available. SSE-based services will not work.")

# Define data models for our tools
class SearchServerRequest(BaseModel):
    query: str
    top_k: Optional[int] = Field(default=3, description="Number of top results to return")

class AddServerRequest(BaseModel):
    server_name: str
    server_description: str
    server_endpoint: str
    tools: List[Dict[str, Any]]

class ExecToolRequest(BaseModel):
    target_server_name: str
    target_tool_name: str
    parameters: Dict[str, Any]

# Initialize the MCP server
mcp = FastMCP("mcp-router", port=9000)

@mcp.tool()
async def search_mcp_server(query: str, top_k: Optional[int] = 3) -> str:
    """
    Search for registered MCP servers based on a query.
    
    Args:
        query: Search query
        top_k: Number of top results to return (default: 3)
    """
    try:
        # Search for servers
        results = discovery_service.search_server(query, top_k)
        
        # Parse tools JSON strings back to objects
        for result in results:
            result["tools"] = json.loads(result["tools"])
        
        return json.dumps(results, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)

@mcp.tool()
async def add_mcp_server(
    server_name: str, 
    server_description: str, 
    server_endpoint: str, 
    tools: List[Dict[str, Any]]
) -> str:
    """
    Register a new MCP server with the discovery service.
    
    Args:
        server_name: Unique name of the server
        server_description: Description of the server
        server_endpoint: Endpoint URL of the server
        tools: List of tools provided by the server
    """
    try:
        # Serialize tools list to JSON string
        tools_json = json.dumps(tools, ensure_ascii=False)
        
        # Add server to discovery service
        result = discovery_service.add_server(
            server_name,
            server_description,
            server_endpoint,
            tools_json
        )
        
        return json.dumps(result, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)

@mcp.tool()
async def exec_mcp_tool(
    target_server_name: str, 
    target_tool_name: str, 
    parameters: Dict[str, Any]
) -> str:
    """
    Execute a tool on a target MCP server.
    
    Args:
        target_server_name: Name of the target server
        target_tool_name: Name of the tool to execute
        parameters: Parameters for the tool
    """
    try:
        # Get target server endpoint
        target_endpoint = discovery_service.get_server_endpoint(target_server_name)
        
        # Check if this is an SSE service (like AMap)
        if "sse" in target_endpoint.lower() and HAVE_SSE_SUPPORT:
            # Use SSE connection for services that require it
            return await _execute_sse_tool(target_endpoint, target_tool_name, parameters)
        else:
            # Use HTTP POST for standard MCP services
            return await _execute_http_tool(target_endpoint, target_tool_name, parameters)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)

async def _execute_sse_tool(endpoint: str, tool_name: str, parameters: Dict[str, Any]) -> str:
    """
    Execute a tool on a target MCP server using SSE connection.
    
    Args:
        endpoint: The SSE endpoint URL
        tool_name: Name of the tool to execute
        parameters: Parameters for the tool
    """
    exit_stack = AsyncExitStack()
    
    try:
        # Create SSE client
        sse_cm = sse_client(endpoint)
        streams = await exit_stack.enter_async_context(sse_cm)
        
        # Create session
        session_cm = ClientSession(streams[0], streams[1])
        session = await exit_stack.enter_async_context(session_cm)
        
        # Initialize session
        await session.initialize()
        
        # Execute tool
        result = await session.call_tool(tool_name, parameters)
        
        # Convert result to dict if it's a CallToolResult object
        if hasattr(result, '_asdict'):
            result = result._asdict()
        elif hasattr(result, '__dict__'):
            result = result.__dict__
        
        # Return result as JSON
        return json.dumps(result, ensure_ascii=False, default=str)
    finally:
        # Clean up
        await exit_stack.aclose()

async def _execute_http_tool(endpoint: str, tool_name: str, parameters: Dict[str, Any]) -> str:
    """
    Execute a tool on a target MCP server using HTTP POST.
    
    Args:
        endpoint: The HTTP endpoint URL
        tool_name: Name of the tool to execute
        parameters: Parameters for the tool
    """
    # Construct JSON-RPC request
    json_rpc_request = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": parameters
        },
        "id": 1
    }
    
    # Send request to target server
    async with httpx.AsyncClient() as client:
        response = await client.post(
            endpoint,
            json=json_rpc_request,
            headers={"Content-Type": "application/json"}
        )
        
        # Return the response from the target server
        response_data = response.json()
        return json.dumps(response_data, ensure_ascii=False)

if __name__ == "__main__":
    # Run the server
    mcp.run(transport='stdio')