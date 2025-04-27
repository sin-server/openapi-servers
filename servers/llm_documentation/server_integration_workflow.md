# Open WebUI Server Integration Workflow

This guide provides a step-by-step workflow for adding new servers to the Open WebUI tool server ecosystem.

## Overview

Open WebUI Tool Servers follow a consistent structure and workflow:

1. Each server is a standalone FastAPI application in its own directory under `servers/`
2. All servers expose REST APIs that follow OpenAPI specifications
3. The root `compose.yaml` orchestrates running multiple servers together with unique port mappings
4. Each server has its own local `compose.yaml` for individual testing

## Server Structure

Each server follows this standard file structure:

```
servers/your-server-name/
├── .dockerignore        # Files to exclude from Docker builds
├── Dockerfile           # Container build instructions
├── README.md            # Server-specific documentation
├── compose.yaml         # Individual server docker-compose
├── main.py              # Primary FastAPI application 
├── requirements.txt     # Python dependencies
└── [other files]        # Server-specific configuration files
```

## Step-by-Step Integration Workflow

### 1. Create a New Server Directory

```bash
mkdir -p /path/to/openapi-servers/servers/your-server-name
cd /path/to/openapi-servers/servers/your-server-name
```

### 2. Create the Core Files

#### a. Create `requirements.txt`

```
fastapi
uvicorn[standard]
pydantic
python-multipart

# Add your server-specific dependencies below
```

#### b. Create Basic `main.py`

```python
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional

app = FastAPI(
    title="Your Server Title",
    version="1.0.0",
    description="Description of your server's functionality.",
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
    return {"message": "Your server is running!"}
```

#### c. Create a Standard `Dockerfile`

```dockerfile
# syntax=docker/dockerfile:1

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
RUN adduser \
    --disabled-password \
    --gecos "" \
    --home "/nonexistent" \
    --shell "/sbin/nologin" \
    --no-create-home \
    --uid "${UID}" \
    appuser

# Download dependencies as a separate step to take advantage of Docker's caching.
RUN --mount=type=cache,target=/root/.cache/pip \
    --mount=type=bind,source=requirements.txt,target=requirements.txt \
    python -m pip install -r requirements.txt

# Switch to the non-privileged user to run the application.
USER appuser

# Copy the source code into the container.
COPY . .

# Expose the port that the application listens on.
EXPOSE 8000

# Run the application.
CMD uvicorn 'main:app' --host=0.0.0.0 --port=8000
```

#### d. Create a Server-specific `compose.yaml`

```yaml
services:
  server:
    build:
      context: .
    ports:
      - 8000:8000
```

#### e. Create a `.dockerignore` File

```
**/.DS_Store
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
```

#### f. Create a Basic `README.md`

```markdown
# 🚀 Your Server Name

Brief description of your server's purpose and functionality.

## 🚀 Quickstart

```bash
git clone https://github.com/open-webui/openapi-servers
cd openapi-servers/servers/your-server-name
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --reload
```

📡 Your server will be live at:  
http://localhost:8000/docs

---

Built for plug & play ⚡
```

### 3. Update the Root `compose.yaml`

Add your server to the root `compose.yaml` file:

```yaml
services:
  # ... existing services ...
  
  your-server-name:
    build:
      context: ./servers/your-server-name
    ports:
      - 8084:8000  # Use the next available port

# ... existing volumes ...
```

### 4. Implement Your Server's Specific Functionality

Develop the API endpoints in `main.py` to implement your server's specific functionality:
- Define Pydantic models for request/response validation
- Create FastAPI route handlers
- Implement utility functions
- Add any configuration files if needed

### 5. Test Your Server

Test your server individually:

```bash
cd /path/to/openapi-servers/servers/your-server-name
docker compose up
```

Then test it as part of the full system:

```bash
cd /path/to/openapi-servers
docker compose up
```

## Special Considerations

### Persistent Storage

If your server needs persistent storage:

1. Add a volume in your server's `compose.yaml`:
```yaml
services:
  server:
    # ... other settings ...
    volumes:
      - data:/app/data:rw

volumes:
  data:
```

2. Add the volume to the root `compose.yaml`:
```yaml
services:
  your-server-name:
    # ... other settings ...
    volumes:
      - your_data:/app/data:rw

volumes:
  # ... other volumes ...
  your_data:
```

### Environment Variables

For configuration via environment variables:

1. Add them to your server's `compose.yaml`:
```yaml
services:
  server:
    # ... other settings ...
    environment:
      - KEY=value
```

2. And to the root `compose.yaml`:
```yaml
services:
  your-server-name:
    # ... other settings ...
    environment:
      - KEY=value
```

## Automated Integration Script

For automated server creation, see the Python script in `server_creation_script.md`.