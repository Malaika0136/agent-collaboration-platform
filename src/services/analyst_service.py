# analyst_service.py
# --------------------------------------------------------
# This service represents the "Analyst" agent.
# It:
#   1) Polls the Broker for messages addressed to "Analyst"
#   2) Extracts a pointer from the message payload
#   3) Fetches the corresponding document from the MCP Registry
#   4) Calls the Groq LLM to analyze the text (KPIs + ~120-word summary)
#   5) Sends a reply ("confirm") back to the Researcher via the Broker
# Notes:
#   - Requires GROQ_API_KEY in the environment to call Groq
#   - If no key is set, returns a canned warning response
# --------------------------------------------------------

from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, Any, List
import os, requests
from groq import Groq

# Initialize FastAPI app (visible in docs: /docs)
app = FastAPI(title="Analyst Agent (Groq)")

# -------------------------- Config --------------------------
# Base URL for MCP registry (for fetching stored documents)
MCP_BASE = os.getenv("MCP_BASE", "http://127.0.0.1:7000/mcp")

# Shared registry token for simple auth with MCP
REGISTRY_TOKEN = os.getenv("MCP_REGISTRY_TOKEN", "teacher-secret")

# Broker base URL (for polling/ sending A2A messages)
BROKER_URL = os.getenv("BROKER_URL", "http://127.0.0.1:7003")

# Groq API credentials and model selection
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

# Groq client (None if API key missing → we will return a canned response)
groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

# Optional: in-memory inbox for visibility / debugging (what we polled)
INBOX: List[Dict[str, Any]] = []

# ------------------------- Models ---------------------------
class A2AMessage(BaseModel):
    """Envelope for agent-to-agent messages routed via Broker."""
    sender: str
    receiver: str
    type: str
    payload: Dict[str, Any]
    conv_id: str

# -------------------------- Utils ---------------------------
@app.get("/inbox")
def inbox():
    """Debug endpoint: show messages this Analyst has recently pulled."""
    return INBOX

@app.delete("/inbox/clear")
def inbox_clear():
    """Debug endpoint: clear local inbox."""
    INBOX.clear()
    return {"status": "cleared"}

def mcp_get(pointer: str) -> Dict[str, Any]:
    """
    Fetch a stored document from MCP using a pointer like 'ctx://note/<rid>'.
    We only need the final <rid> for the fetch API.
    """
    rid = pointer.split("/")[-1]  # extract the UUID part
    r = requests.get(
        f"{MCP_BASE}/resources/fetch/{rid}",
        headers={"Authorization": f"Bearer {REGISTRY_TOKEN}"},
        timeout=10,
    )
    r.raise_for_status()
    return r.json()  # { rid, data, owner, meta }

def call_groq(system: str, user: str) -> str:
    """
    Call the Groq chat completion API with a system+user prompt.
    If GROQ_API_KEY is not set, return a canned warning message.
    """
    if not groq_client:
        return "⚠️ GROQ_API_KEY not set — returning canned response."
    chat = groq_client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],        pip install fastapi uvicorn groq requests python-dotenv
        temperature=0.2,
        max_tokens=600,
    )
    return chat.choices[0].message.content.strip()

# ------------------------- Main Flow ------------------------
@app.post("/pull_process_and_reply")
def pull_process_and_reply():
    """
    End-to-end Analyst step:
      1) Poll Broker for a message addressed to 'Analyst'
      2) If message has a 'pointer' in payload, fetch document from MCP
      3) Analyze with Groq (KPIs + ~120-word summary as JSON)
      4) Send a 'confirm' reply back to Researcher via Broker (same conv_id)
    Returns a small status payload useful for debugging.
    """
    # 1) Poll broker for any waiting message for "Analyst"
    rp = requests.get(f"{BROKER_URL}/broker/poll/Analyst", timeout=10)
    rp.raise_for_status()
    data = rp.json()
    if data.get("status") != "ok":
        # No messages available right now
        return {"status": "no-messages"}

    # We got a message; keep a copy for debugging visibility
    msg = data["message"]
    INBOX.append(msg)

    # 2) Extract the MCP pointer from payload
    pointer = msg["payload"].get("pointer")
    if not pointer:
        # If there is no pointer, ignore (could be other message types)
        return {"status": "ignored", "reason": "no pointer"}

    # Fetch the actual document associated with the pointer
    resource = mcp_get(pointer)
    doc_text = resource["data"]

    # 3) Build prompts and call Groq to analyze the text
    system = "You analyze business notes, verify claims, extract KPIs, and write concise summaries."
    user = f"""
Document:
\"\"\"{doc_text}\"\"\"


Tasks:
1) Extract KPIs (YoY growth, drivers, risks) in bullet points.
2) Write a neutral ~120-word summary for an exec note.
3) Keep numeric ranges as stated (no hallucination).
4) Return JSON with keys: kpis (list of bullets), summary (string).
"""
    analysis = call_groq(system, user)

    # 4) Prepare a reply back to the Researcher (mirror the original conv_id)
    reply = A2AMessage(
        sender="Analyst",
        receiver="Researcher",
        type="confirm",
        payload={"analysis": analysis, "source_pointer": pointer},
        conv_id=msg["conv_id"],
    )

    # Enqueue the reply via Broker so Researcher can poll and receive it
    rq = requests.post(f"{BROKER_URL}/broker/send", json=reply.dict(), timeout=10)
    rq.raise_for_status()

    # Return a small debug response
    return {"reply_enqueued": reply.dict()}
