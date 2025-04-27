# Open WebUI Server Catalog

This document provides an overview of all existing OpenAPI tool servers in the ecosystem, their functionality, and special configuration requirements.

## Core Server Types

| Server | Description | Port | Special Requirements |
|--------|-------------|------|----------------------|
| **filesystem** | File system operations with security controls | 8081 | Configurable allowed directories |
| **memory** | Knowledge graph and persistent memory | 8082 | Requires persistent volume |
| **time** | Date/time utilities and conversions | 8083 | None |
| **weather** | Weather information by location | 8084* | External API access |
| **git** | Git repository operations | 8085* | None |
| **get-user-info** | User authentication proxy | 8086* | Requires OPEN_WEBUI_BASE_URL |
| **mcp-proxy** | Translates MCP tools to OpenAPI | 8087* | Depends on MCP server |

*Port may vary based on your configuration

## Server Details

### Filesystem Server

**Purpose**: Provides secure file system operations.

**Key Features**:
- Read, write, and edit text files
- Create, list, and delete directories
- Search files by content or pattern
- Configurable access restrictions

**Configuration**:
- Edit `config.py` to set allowed directories (`ALLOWED_DIRECTORIES`)

### Memory Server

**Purpose**: Persistent knowledge graph storage.

**Key Features**:
- Entity and relationship storage
- Observation tracking
- Search capabilities
- Persistent volume for data retention

**Configuration**:
- Requires volume configuration in compose files
- Docker: `memory:/app/data:rw`

### Time Server

**Purpose**: Time and date utilities.

**Key Features**:
- Current time in multiple timezones
- Time format conversion
- Elapsed time calculation
- Timezone list and conversion

### Weather Server

**Purpose**: Weather information retrieval.

**Key Features**:
- Current weather conditions
- Location-based forecasts
- Unit conversion based on country
- Uses Open-Meteo API

**Dependencies**:
- `requests`
- `reverse_geocoder`

### Git Server

**Purpose**: Git repository operations.

**Key Features**:
- Repository status and diff
- Commit, add, and reset capabilities
- Branch operations
- Log viewing

**Dependencies**:
- `gitpython`

### Get-User-Info Server

**Purpose**: User authentication proxy.

**Key Features**:
- Forward auth tokens to internal services
- Retrieve user profiles securely

**Configuration**:
- `OPEN_WEBUI_BASE_URL` environment variable required

### MCP-Proxy Server

**Purpose**: Bridge between MCP and OpenAPI.

**Key Features**:
- Dynamic endpoint creation from MCP tools
- Proxy MCP server tools as OpenAPI endpoints

**Configuration**:
- Requires MCP server command after `--`

## Adding New Servers

For detailed instructions on adding new servers, see:
- [Server Integration Workflow](server_integration_workflow.md)
- [Server Creation Script](server_creation_script.md)

## Best Practices

When developing new servers:

1. **Minimize Dependencies** - Keep requirements lightweight
2. **Use Standard Patterns** - Follow the FastAPI structure shown in other servers
3. **Document API Endpoints** - Use descriptive summaries and parameter descriptions
4. **Handle Errors Properly** - Return appropriate HTTP status codes and error messages
5. **Include Security Controls** - Add appropriate access restrictions
6. **Test Thoroughly** - Verify both standalone and integrated operation