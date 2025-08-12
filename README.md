# MCP Router

MCP Router is a service discovery and proxy for MCP (Model Control Protocol) services. It allows you to register, discover, and execute tools on remote MCP servers.

## Features

1. **Service Discovery**: Register and search for MCP services using vector-based similarity search
2. **Tool Execution Proxy**: Execute tools on remote MCP servers through the router
3. **MCP Compliance**: Fully compliant with the MCP protocol specification

## Architecture

The MCP Router consists of two core modules:

1. **MCP Data Plane**: The frontend that interacts with MCP clients, providing service discovery, registration, and tool execution proxying
2. **MCP Discovery Service**: The backend that uses Alibaba Cloud's vector database and embedding models for intelligent search and management of registered MCP services

## Prerequisites

- Python 3.11 or higher
- Access to Alibaba Cloud DashScope and DashVector services
- API keys for DashScope and DashVector

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd mcp-router
   ```

2. Install dependencies using uv:
   ```bash
   uv add pydantic httpx dashscope dashvector python-dotenv
   ```

3. Set up environment variables in `.env`:
   ```env
   DASHSCOPE_API_KEY=your_dashscope_api_key
   DASHVECTOR_API_KEY=your_dashvector_api_key
   DASHVECTOR_ENDPOINT=your_dashvector_endpoint
   COLLECTION_NAME=mcp_services_collection
   EMBEDDING_DIMENSION=1024
   ```

## Usage

Run the MCP Router server:
```bash
uv run python mcp_router.py
```

## Tools

The MCP Router provides three tools:

1. **search_mcp_server**: Search for registered MCP servers based on a query
2. **add_mcp_server**: Register a new MCP server with the discovery service
3. **exec_mcp_tool**: Execute a tool on a target MCP server

## Development

### Running Tests

```bash
uv run pytest
```

### Code Structure

- `mcp_router.py`: Main MCP server implementation (Data Plane)
- `discovery_service.py`: Discovery service implementation (Discovery Service)
- `config.py`: Configuration management
- `test_mcp_router.py`: Unit tests

## License

MIT