# Server Creation Script Documentation

This document explains how to use the automated server creation script that generates standardized Open WebUI tool servers.

## Prerequisites

- Python 3.6+
- Access to a terminal

## Script Location

The script is located at:
```
/servers/llm_documentation/create_server.py
```

## Basic Usage

To create a new server with default settings:

```bash
# Navigate to the project root
cd /path/to/openapi-servers

# Run the script (make it executable first if needed)
python servers/llm_documentation/create_server.py my-server-name
```

This will:
1. Create a new server directory at `servers/my-server-name`
2. Set up all standard files (main.py, Dockerfile, etc.)
3. Add the server to the root `compose.yaml` file
4. Assign the next available port

## Command Line Options

The script supports several options:

```
python create_server.py my-server-name [OPTIONS]
```

Options:
- `--title "Server Title"` - Sets a specific title for the server (default: name converted to title case)
- `--description "Server description"` - Sets a description for the server (default: "A new OpenAPI server")
- `--port 8084` - Assigns a specific port for the server (default: auto-assigned next port)
- `--dir "/path/to/root"` - Sets the root directory of the project (default: current directory)

## Examples

### Basic Server

```bash
python servers/llm_documentation/create_server.py calculator
```

### Custom Title and Description

```bash
python servers/llm_documentation/create_server.py math-tools \
  --title "Mathematics Toolkit" \
  --description "A collection of mathematical utilities including calculator, statistics, and equation solving."
```

### Specific Port

```bash
python servers/llm_documentation/create_server.py code-analyzer --port 8085
```

## Next Steps After Creation

After creating a server:

1. Implement your API endpoints in `servers/your-server-name/main.py`
2. Add any specific dependencies to `servers/your-server-name/requirements.txt`
3. Test your server individually with Docker Compose:
   ```bash
   cd servers/your-server-name
   docker compose up
   ```
4. Test as part of the full system:
   ```bash
   cd /path/to/openapi-servers
   docker compose up
   ```

## Script Architecture

The script follows this logic flow:

1. Parse command line arguments
2. Determine settings (port, title, description)
3. Create server directory and all required files
4. Update the root compose.yaml to include the new server
5. Print confirmation and next steps

Key functions:
- `create_new_server()` - Main function to create all server files
- `find_next_available_port()` - Analyzes compose.yaml to find the next free port
- `main()` - Entry point handling command line arguments