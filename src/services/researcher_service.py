# researcher_service.py
# --------------------------------------------------------
# This service represents the "Researcher" agent.
# It is responsible for:
#   1. Creating a document or business note.
#   2. Storing that document in the MCP Registry (central memory).
#   3. Sending an A2A message with a pointer to the "Analyst" agent via Broker.
#   4. Receiving replies (confirmations/analysis) from Analyst.
# --------------------------------------------------------

from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import os, requests  # requests is used to call MCP and Broker HTTP APIs

# --------------------------------------------------------
# Initialize FastAPI app
# --------------------------------------------------------
app = FastAPI(title="Researcher Agent")

# --------------------------------------------------------
# Configuration variables (env-based)
# --------------------------------------------------------
# MCP_BASE: where the MCP registry is running (default port 7000)
# REGISTRY_TOKEN: shared token to authorize MCP access
# BROKER_URL: where the Broker service is running (default port 7003)
MCP_BASE = os.getenv("MCP_BASE", "http://127.0.0.1:7000/mcp")
REGISTRY_TOKEN = os.getenv("MCP_REGISTRY_TOKEN", "teacher-secret")
BROKER_URL = os.getenv("BROKER_URL", "http://127.0.0.1:7003")

# --------------------------------------------------------
# Local inbox for received messages (useful for debugging)
# --------------------------------------------------------
INBOX: List[Dict[str, Any]] = []  # stores replies from Analyst

# --------------------------------------------------------
# Define the A2A message format
# --------------------------------------------------------
class A2AMessage(BaseModel):
    sender: str
    receiver: str
    type: str
    payload: Dict[str, Any]
    conv_id: str

# --------------------------------------------------------
# Helper function: store a note/document into MCP
# --------------------------------------------------------
def mcp_put(data: str, owner: str, meta: Optional[Dict[str, Any]] = None) -> str:
    """
    Sends a POST request to MCP to store text data.
    Returns a pointer like ctx://note/<uuid> which other agents can fetch later.
    """
    r = requests.post(
        f"{MCP_BASE}/resources/create",
        json={"data": data, "owner": owner, "meta": meta or {}},
        headers={"Authorization": f"Bearer {REGISTRY_TOKEN}"},
        timeout=10,
    )
    r.raise_for_status()  # throw error if failed
    return r.json()["pointer"]

# --------------------------------------------------------
# Endpoint: view Researcher’s local inbox (messages received)
# --------------------------------------------------------
@app.get("/inbox")
def inbox():
    """Returns all messages currently in the Researcher's inbox."""
    return INBOX

# --------------------------------------------------------
# Endpoint: clear inbox (optional)
# --------------------------------------------------------
@app.delete("/inbox/clear")
def inbox_clear():
    """Clears all messages from the Researcher's inbox."""
    INBOX.clear()
    return {"status": "cleared"}

# --------------------------------------------------------
# Endpoint 1: Produce a note and enqueue message to Analyst
# --------------------------------------------------------
@app.post("/produce_note_and_enqueue")
def produce_note_and_enqueue():
    """
    1. Creates a small example business note (e.g., quarterly EdTech report).
    2. Saves it to MCP Registry and gets a pointer.
    3. Constructs an A2A message for Analyst with that pointer.
    4. Sends it via Broker.
    """
    # --- Step 1: Create the business note ---
    note = """Q3 EdTech report (Pakistan):
- YoY growth: 38–42%
- Drivers: mobile-first adoption, fee-based LMS in HEIs, local content
- Risks: churn, regulatory uncertainty
- Sources: ReportA(2025), ReportB(2024), SurveyC(n=612)"""

    # --- Step 2: Store note in MCP and get pointer back ---
    pointer = mcp_put(
        data=note,
        owner="Researcher",
        meta={"topic": "EdTech", "quarter": "Q3", "country": "PK", "year": 2025},
    )

    # --- Step 3: Build the A2A message for Analyst ---
    msg = A2AMessage(
        sender="Researcher",
        receiver="Analyst",
        type="inform",
        payload={"pointer": pointer, "task": "Verify facts, extract KPIs, 120-word summary."},
        conv_id="conv-001",  # conversation ID (can be any unique string)
    )

    # --- Step 4: Send the message to Broker (Analyst’s queue) ---
    r = requests.post(f"{BROKER_URL}/broker/send", json=msg.dict(), timeout=10)
    r.raise_for_status()

    # --- Step 5: Return confirmation for debugging/UI ---
    return {"enqueued": msg.dict(), "broker_response": r.json()}

# --------------------------------------------------------
# Endpoint 2: Pull reply messages from Broker
# --------------------------------------------------------
@app.post("/pull_reply_from_broker")
def pull_reply_from_broker():
    """
    Polls the Broker for messages addressed to 'Researcher'.
    If found, stores them in local INBOX.
    """
    r = requests.get(f"{BROKER_URL}/broker/poll/Researcher", timeout=10)
    r.raise_for_status()
    data = r.json()

    # If a valid message was received, add it to local inbox
    if data.get("status") == "ok":
        INBOX.append(data["message"])

    return data
