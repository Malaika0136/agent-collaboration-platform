# frontend_service.py
# --------------------------------------------------------
# This is the Frontend (orchestrator + web UI) service.
# It provides a simple HTML page where a user can input text to analyze.
# The pipeline:
#   1. Takes user input text.
#   2. Stores it in MCP Registry and gets a pointer.
#   3. Sends an A2A message to Analyst (through Broker) with that pointer.
#   4. Triggers the Analyst to process it (via Groq LLM).
#   5. Polls the Broker for the Analyst's reply (to Researcher).
#   6. Displays the summarized analysis on the web page.
# --------------------------------------------------------

from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, PlainTextResponse
from pydantic import BaseModel
from typing import Dict, Any, Optional
from string import Template
import os, uuid, time, requests, json

# --------------------------------------------------------
# Initialize FastAPI app
# --------------------------------------------------------
app = FastAPI(title="A2A+MCP Frontend")

# --------------------------------------------------------
# Configurable service URLs and tokens
# --------------------------------------------------------
# You can override these using environment variables if ports differ.
MCP_BASE    = os.getenv("MCP_BASE", "http://127.0.0.1:7000/mcp")
BROKER_URL  = os.getenv("BROKER_URL", "http://127.0.0.1:7003")
ANALYST_URL = os.getenv("ANALYST_URL", "http://127.0.0.1:7002")
REGISTRY_TOKEN = os.getenv("MCP_REGISTRY_TOKEN", "teacher-secret")

# --------------------------------------------------------
# HTML Template for UI
# --------------------------------------------------------
# Template is used so we can dynamically insert result HTML later.
HTML_PAGE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <title>A2A + MCP Frontend</title>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <style>
    body { font-family: ui-sans-serif, system-ui, Arial; margin: 2rem; }
    form { margin-bottom: 1.5rem; }
    input[type=text], textarea { width: 100%; padding: 0.6rem; font-size: 1rem; }
    button { padding: 0.6rem 1rem; font-size: 1rem; cursor: pointer; }
    .card { border: 1px solid #ddd; border-radius: 8px; padding: 1rem; margin-top: 1rem; }
    .muted { color: #666; font-size: 0.9rem; }
    pre { background: #f7f7f7; padding: 0.8rem; border-radius: 6px; overflow:auto; }
    .ok { color: #0a7f2e; }
    .warn { color: #b86600; }
  </style>
</head>
<body>
  <h1>A2A + MCP Frontend</h1>
  <p class="muted">This sends your text to MCP (as context), dispatches an A2A message to Analyst via Broker, triggers Analyst to process (Groq), and returns the reply.</p>

  <!-- Form where user submits text -->
  <form method="post" action="/run">
    <label for="query"><b>Enter text/query to analyze</b></label><br/>
    <textarea id="query" name="query" rows="6" placeholder="Type something for Analyst to summarize…"></textarea>
    <br/><br/>
    <button type="submit">Run pipeline</button>
  </form>

  $RESULT

  <!-- Display service URLs for debugging -->
  <div class="card">
    <div class="muted">Services</div>
    <ul class="muted">
      <li>MCP: <code>$mcp</code></li>
      <li>Broker: <code>$broker</code></li>
      <li>Analyst: <code>$analyst</code></li>
    </ul>
  </div>
</body>
</html>
"""

# --------------------------------------------------------
# A2A Message format
# --------------------------------------------------------
class A2AMessage(BaseModel):
    sender: str
    receiver: str
    type: str
    payload: Dict[str, Any]
    conv_id: str

# --------------------------------------------------------
# Helper: Store user text in MCP and return pointer
# --------------------------------------------------------
def mcp_put(data: str, owner: str, meta: Optional[Dict[str, Any]] = None) -> str:
    """Store text in MCP Registry and return a pointer (ctx://note/uuid)."""
    r = requests.post(
        f"{MCP_BASE}/resources/create",
        json={"data": data, "owner": owner, "meta": meta or {}},
        headers={"Authorization": f"Bearer {REGISTRY_TOKEN}"},
        timeout=15,
    )
    r.raise_for_status()
    return r.json()["pointer"]

# --------------------------------------------------------
# Helper: Send a message to Broker
# --------------------------------------------------------
def broker_send(msg: Dict[str, Any]) -> Dict[str, Any]:
    """POST message to Broker (enqueue)."""
    r = requests.post(f"{BROKER_URL}/broker/send", json=msg, timeout=15)
    r.raise_for_status()
    return r.json()

# --------------------------------------------------------
# Helper: Poll Broker for messages for a given agent
# --------------------------------------------------------
def broker_poll(agent: str) -> Dict[str, Any]:
    """GET from Broker to check if a message exists for this agent."""
    r = requests.get(f"{BROKER_URL}/broker/poll/{agent}", timeout=15)
    r.raise_for_status()
    return r.json()

# --------------------------------------------------------
# Helper: Trigger Analyst to process one message
# --------------------------------------------------------
def analyst_process_once() -> Dict[str, Any]:
    """
    Ask the Analyst to run /pull_process_and_reply once.
    Analyst will poll the Broker and, if a message is available,
    process it and send back a reply to Researcher.
    """
    r = requests.post(f"{ANALYST_URL}/pull_process_and_reply", timeout=30)
    r.raise_for_status()
    return r.json()

# --------------------------------------------------------
# Route: homepage → shows HTML form
# --------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
def root():
    """Display simple HTML form."""
    return Template(HTML_PAGE).substitute(
        RESULT="",
        mcp=MCP_BASE,
        broker=BROKER_URL,
        analyst=ANALYST_URL,
    )

# --------------------------------------------------------
# Route: run full pipeline
# --------------------------------------------------------
@app.post("/run", response_class=HTMLResponse)
def run_pipeline(query: str = Form(...)):
    """
    This endpoint orchestrates the full A2A workflow:
      1) Stores user text in MCP
      2) Sends A2A message to Analyst
      3) Triggers Analyst to process
      4) Polls Broker until reply is received
      5) Displays the final analysis result on webpage
    """

    # Step 1: Save text in MCP
    try:
        pointer = mcp_put(
            data=query.strip(),
            owner="Researcher",
            meta={"source": "frontend", "kind": "user_query"},
        )
    except Exception as e:
        # Handle MCP errors (e.g., registry not running)
        res = f'<div class="card"><b class="warn">MCP error:</b><pre>{e}</pre></div>'
        return Template(HTML_PAGE).substitute(RESULT=res, mcp=MCP_BASE, broker=BROKER_URL, analyst=ANALYST_URL)

    # Step 2: Build A2A message and enqueue to Broker
    conv_id = f"conv-{uuid.uuid4()}"  # unique conversation ID
    msg = A2AMessage(
        sender="Researcher",
        receiver="Analyst",
        type="inform",
        payload={"pointer": pointer, "task": "Verify facts, extract KPIs, ~120-word summary."},
        conv_id=conv_id,
    ).dict()

    try:
        send_resp = broker_send(msg)
    except Exception as e:
        # Broker not reachable
        res = f'<div class="card"><b class="warn">Broker enqueue error:</b><pre>{e}</pre></div>'
        return Template(HTML_PAGE).substitute(RESULT=res, mcp=MCP_BASE, broker=BROKER_URL, analyst=ANALYST_URL)

    # Step 3: Repeatedly trigger Analyst and poll for reply (timeout ~25s)
    reply_msg = None
    start = time.time()
    deadline = start + 25.0  # total wait time
    attempts = 0
    stray_msgs = []          # store irrelevant messages (diff conv_id)

    while time.time() < deadline:
        attempts += 1
        try:
            analyst_process_once()  # ask analyst to process once
        except Exception:
            pass  # ignore transient errors

        # Poll for a reply for "Researcher"
        try:
            polled = broker_poll("Researcher")
        except Exception:
            polled = {"status": "error"}

        # Check if reply matches our conversation ID
        if polled.get("status") == "ok":
            m = polled.get("message")
            if m and m.get("conv_id") == conv_id:
                reply_msg = m
                break  # got our reply
            else:
                stray_msgs.append(m)  # not our message; store separately

        time.sleep(1.0)  # small delay before next poll

    # Step 4: Prepare debug blocks for webpage
    status_block = f"""
    <div class="card">
      <div><b>Frontend Run</b></div>
      <div class="muted">Attempts: {attempts}</div>
      <div>Pointer: <code>{pointer}</code></div>
      <div>Enqueue: <pre>{json.dumps(send_resp, indent=2, ensure_ascii=False)}</pre></div>
    </div>
    """

    stray_block = ""
    if stray_msgs:
        stray_block = f"""
        <div class="card">
          <div class="warn"><b>Note:</b> Received messages for other conv_ids (showing first only)</div>
          <pre>{json.dumps(stray_msgs[0], indent=2, ensure_ascii=False)}</pre>
        </div>
        """

    # Step 5: Handle timeout case
    if not reply_msg:
        res = status_block + stray_block + """
        <div class="card"><b class="warn">No reply received in time.</b>
        <div class="muted">Ensure Analyst is running and has GROQ_API_KEY set, then try again.</div></div>
        """
        return Template(HTML_PAGE).substitute(RESULT=res, mcp=MCP_BASE, broker=BROKER_URL, analyst=ANALYST_URL)

    # Step 6: Parse analysis (if JSON)
    analysis_text = reply_msg["payload"].get("analysis", "")
    pretty_analysis = analysis_text
    try:
        maybe_json = json.loads(analysis_text)
        pretty_analysis = json.dumps(maybe_json, indent=2, ensure_ascii=False)
    except Exception:
        pass  # analysis not in JSON → show raw

    # Step 7: Render success output
    res = status_block + stray_block + f"""
    <div class="card">
      <div><b class="ok">Reply received ✅</b></div>
      <div class="muted">Conversation: {conv_id}</div>
      <div>Source pointer: <code>{reply_msg["payload"].get("source_pointer","")}</code></div>
      <div>Raw message:</div>
      <pre>{json.dumps(reply_msg, indent=2, ensure_ascii=False)}</pre>
      <div><b>Analysis (parsed if JSON):</b></div>
      <pre>{pretty_analysis}</pre>
    </div>
    """

    return Template(HTML_PAGE).substitute(RESULT=res, mcp=MCP_BASE, broker=BROKER_URL, analyst=ANALYST_URL)

# --------------------------------------------------------
# Health check endpoint (for monitoring)
# --------------------------------------------------------
@app.get("/health", response_class=PlainTextResponse)
def health():
    """Simple health check endpoint."""
    return "ok"
