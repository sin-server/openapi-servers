#!/usr/bin/env python3
"""
Server Creation Script for Open WebUI

This script automates the creation of new OpenAPI tool servers for the Open WebUI ecosystem,
following the standard structure and patterns.

Usage:
    python create_server.py [--host 0.0.0.0] [--port 8084] my-server-name [--title "My Server"] [--description "Server description"]
"""

import os
import sys
import argparse
import shutil
import re

def create_new_server(server_name, server_title, server_description, server_port, base_dir=None):
    """Create a new OpenAPI server with the standard structure."""
    if base_dir is None:
        base_dir = os.getcwd()
    
    server_dir = os.path.join(base_dir, 'servers', server_name)
    
    # Create the server directory
    os.makedirs(server_dir, exist_ok=True)
    
    # Create requirements.txt
    with open(os.path.join(server_dir, 'requirements.txt'), 'w') as f:
        f.write("fastapi\nuvicorn[standard]\npydantic\npython-multipart\n\n# Add your server-specific dependencies below\n")
    
    # Create main.py with template
    with open(os.path.join(server_dir, 'main.py'), 'w') as f:
        f.write(f"""from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional

app = FastAPI(
    title="{server_title}",
    version="1.0.0",
    description="{server_description}",
)

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define your Pydantic models here

# Define your API endpoints here
@app.get("/")
def read_root():
    return {{"message": "Your {server_title} server is running!"}}
""")
    
    # Create Dockerfile
    with open(os.path.join(server_dir, 'Dockerfile'), 'w') as f:
        f.write("""# syntax=docker/dockerfile:1

ARG PYTHON_VERSION=3.10.12
FROM python:${PYTHON_VERSION}-slim as base

# Prevents Python from writing pyc files.
ENV PYTHONDONTWRITEBYTECODE=1

# Keeps Python from buffering stdout and stderr to avoid situations where
# the application crashes without emitting any logs due to buffering.
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Create a non-privileged user that the app will run under.
ARG UID=10001
RUN adduser \\
    --disabled-password \\
    --gecos "" \\
    --home "/nonexistent" \\
    --shell "/sbin/nologin" \\
    --no-create-home \\
    --uid "${UID}" \\
    appuser

# Download dependencies as a separate step to take advantage of Docker's caching.
RUN --mount=type=cache,target=/root/.cache/pip \\
    --mount=type=bind,source=requirements.txt,target=requirements.txt \\
    python -m pip install -r requirements.txt

# Switch to the non-privileged user to run the application.
USER appuser

# Copy the source code into the container.
COPY . .

# Expose the port that the application listens on.
EXPOSE 8000

# Run the application.
CMD uvicorn 'main:app' --host=0.0.0.0 --port=8000
""")
    
    # Create compose.yaml
    with open(os.path.join(server_dir, 'compose.yaml'), 'w') as f:
        f.write("""services:
  server:
    build:
      context: .
    ports:
      - 8000:8000
""")
    
    # Create .dockerignore
    with open(os.path.join(server_dir, '.dockerignore'), 'w') as f:
        f.write("""**/.DS_Store
**/__pycache__
**/.venv
**/.classpath
**/.dockerignore
**/.env
**/.git
**/.gitignore
**/.project
**/.settings
**/.toolstarget
**/.vs
**/.vscode
**/*.*proj.user
**/*.dbmdl
**/*.jfm
**/bin
**/charts
**/docker-compose*
**/compose.y*ml
**/Dockerfile*
**/node_modules
**/npm-debug.log
**/obj
**/secrets.dev.yaml
**/values.dev.yaml
LICENSE
README.md
""")
    
    # Create README.md
    with open(os.path.join(server_dir, 'README.md'), 'w') as f:
        f.write(f"""# 🚀 {server_title}

{server_description}

## 🚀 Quickstart

```bash
git clone https://github.com/open-webui/openapi-servers
cd openapi-servers/servers/{server_name}
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --reload
```

📡 Your server will be live at:  
http://localhost:8000/docs

---

Built for plug & play ⚡
""")
    
    # Update root compose.yaml
    compose_path = os.path.join(base_dir, 'compose.yaml')
    
    if os.path.exists(compose_path):
        with open(compose_path, 'r') as f:
            compose_content = f.read()
        
        # Find where to insert new service (before volumes section or at the end)
        volumes_match = re.search(r'\nvolumes:', compose_content)
        if volumes_match:
            insert_point = volumes_match.start()
        else:
            insert_point = len(compose_content)
        
        # Format the new service entry
        new_service = f"""  {server_name}:
    build:
      context: ./servers/{server_name}
    ports:
      - {server_port}:8000
"""
        
        # Insert the new service
        if insert_point == len(compose_content) and not compose_content.endswith('\n'):
            new_service = '\n' + new_service
            
        new_compose_content = compose_content[:insert_point] + new_service + compose_content[insert_point:]
        
        # Write updated content
        with open(compose_path, 'w') as f:
            f.write(new_compose_content)
    else:
        print(f"Warning: Root compose.yaml not found at {compose_path}")
    
    return server_dir

def find_next_available_port(base_dir=None, start_port=8081):
    """Find the next available port by analyzing the compose.yaml file."""
    if base_dir is None:
        base_dir = os.getcwd()
        
    compose_path = os.path.join(base_dir, 'compose.yaml')
    
    if not os.path.exists(compose_path):
        return start_port
    
    # Read the compose file
    with open(compose_path, 'r') as f:
        compose_content = f.read()
    
    # Extract all port mappings
    port_pattern = r'ports:\s*-\s*(\d+):8000'
    ports = [int(port) for port in re.findall(port_pattern, compose_content)]
    
    # Find the next available port
    if ports:
        return max(ports) + 1
    else:
        return start_port

def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description='Create a new OpenAPI server')
    parser.add_argument('server_name', help='Name of the server (used for directory name)')
    parser.add_argument('--title', help='Title of the server API', default=None)
    parser.add_argument('--description', help='Description of the server API', default="A new OpenAPI server")
    parser.add_argument('--port', type=int, help='Host port for the server (in docker-compose)', default=None)
    parser.add_argument('--dir', help='Base directory of the openapi-servers repository', default=None)
    
    args = parser.parse_args()
    
    # Default values if not provided
    base_dir = args.dir or os.getcwd() 
    title = args.title or args.server_name.replace('-', ' ').title()
    next_port = args.port or find_next_available_port(base_dir)
    
    try:
        server_dir = create_new_server(args.server_name, title, args.description, next_port, base_dir)
        
        print(f"Successfully created new server '{args.server_name}' at {server_dir}")
        print(f"Added to root compose.yaml with port {next_port}")
        print("\nNext steps:")
        print(f"1. Implement your API endpoints in {server_dir}/main.py")
        print(f"2. Add any specific dependencies to {server_dir}/requirements.txt")
        print("3. Test your server individually with 'docker compose up' in the server directory")
        print("4. Test as part of the full system with 'docker compose up' in the root directory")
    
    except Exception as e:
        print(f"Error creating server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()