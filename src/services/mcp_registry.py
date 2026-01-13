# mcp_registry.py
# --------------------------------------------------------
# This file implements the MCP (Memory Context Protocol) Registry.
# It acts as a small in-memory database to store documents or notes.
# Each stored item is identified by a unique "pointer" (ctx://note/<uuid>)
# which other services (Researcher, Analyst, etc.) use to fetch the data later.
# --------------------------------------------------------

from fastapi import FastAPI, HTTPException, Header   # FastAPI framework + exception handling
from pydantic import BaseModel                       # Data validation model
from typing import Dict, Any, Optional               # Type hints for readability
import os, uuid                                      # OS env vars and unique ID generation

# --------------------------------------------------------
# Initialize FastAPI app
# --------------------------------------------------------
app = FastAPI(title="MCP Registry (Pointers + Auth)")

# --------------------------------------------------------
# Configuration variables
# --------------------------------------------------------
# Token used for simple authentication between services.
# Must match the MCP_REGISTRY_TOKEN value in all other services.
REGISTRY_TOKEN = os.getenv("MCP_REGISTRY_TOKEN", "teacher-secret")

# In-memory store: maps each resource ID (rid) to its content and metadata.
# Structure: { rid: { "data": <text>, "owner": <agent>, "meta": {extra info} } }
CONTEXT_STORE: Dict[str, Dict[str, Any]] = {}

# --------------------------------------------------------
# Pydantic request model for resource creation
# --------------------------------------------------------
class MCPCreateRequest(BaseModel):
    data: str                              # Actual text or document to store
    owner: str                             # Who created the resource (e.g., "Researcher")
    meta: Optional[Dict[str, Any]] = None  # Optional metadata (topic, source, etc.)

# --------------------------------------------------------
# Endpoint: Create a new resource in the MCP
# --------------------------------------------------------
@app.post("/mcp/resources/create")
def mcp_create(req: MCPCreateRequest, authorization: str = Header(None)):
    """
    Stores a document (data) sent by an agent.
    Returns a unique pointer (ctx://note/<rid>) that can be shared.
    Requires header: Authorization: Bearer <REGISTRY_TOKEN>
    """
    # Basic token authentication
    if authorization != f"Bearer {REGISTRY_TOKEN}":
        raise HTTPException(401, "Unauthorized MCP create")

    # Generate unique resource ID
    rid = str(uuid.uuid4())

    # Store document, owner, and metadata in memory
    CONTEXT_STORE[rid] = {
        "data": req.data,
        "owner": req.owner,
        "meta": req.meta or {}
    }

    # Return both the pointer and raw ID
    return {"pointer": f"ctx://note/{rid}", "rid": rid}

# --------------------------------------------------------
# Endpoint: Fetch an existing resource by ID
# --------------------------------------------------------
@app.get("/mcp/resources/fetch/{rid}")
def mcp_fetch(rid: str, authorization: str = Header(None)):
    """
    Retrieves the stored document by its resource ID (rid).
    Requires header: Authorization: Bearer <REGISTRY_TOKEN>
    """
    # Check token validity
    if authorization != f"Bearer {REGISTRY_TOKEN}":
        raise HTTPException(401, "Unauthorized MCP fetch")

    # Ensure the resource exists
    if rid not in CONTEXT_STORE:
        raise HTTPException(404, "Not found")

    # Return the stored object (data + owner + meta)
    return {"rid": rid, **CONTEXT_STORE[rid]}

# --------------------------------------------------------
# Endpoint: List all stored resources (without returning full data)
# --------------------------------------------------------
@app.get("/mcp/resources/list")
def mcp_list(authorization: str = Header(None)):
    """
    Lists all stored resources for debugging/inspection.
    Only shows rid, owner, and metadata — not the full document.
    Requires header: Authorization: Bearer <REGISTRY_TOKEN>
    """
    # Check authorization
    if authorization != f"Bearer {REGISTRY_TOKEN}":
        raise HTTPException(401, "Unauthorized MCP list")

    # Return lightweight summary for all items
    return [
        {"rid": rid, "owner": v["owner"], "meta": v["meta"]}
        for rid, v in CONTEXT_STORE.items()
    ]
