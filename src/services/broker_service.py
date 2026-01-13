# broker_service.py
# --------------------------------------------------------
# This file implements a simple A2A (Agent-to-Agent) message broker.
# It works as an in-memory message queue system.
# Agents send messages to each other via this broker
# instead of direct network calls.
# --------------------------------------------------------

from fastapi import FastAPI                # FastAPI for web server and routes
from pydantic import BaseModel             # Data validation for message format
from typing import Dict, Any, List
from collections import defaultdict, deque # For in-memory queues per agent

# --------------------------------------------------------
# Initialize FastAPI app
# --------------------------------------------------------
app = FastAPI(title="Mini A2A Broker")

# --------------------------------------------------------
# Message format definition using Pydantic
# --------------------------------------------------------
class A2AMessage(BaseModel):
    sender: str            # Who is sending the message (e.g., "Researcher")
    receiver: str          # Who should receive it (e.g., "Analyst")
    type: str              # Message type (e.g., "inform", "confirm", "request")
    payload: Dict[str, Any]# Actual content/data of the message
    conv_id: str           # Conversation ID (unique per session/flow)

# --------------------------------------------------------
# Message queues for each receiver
# --------------------------------------------------------
# defaultdict creates an empty deque (queue) for each new receiver automatically.
# Example:
#   QUEUES["Analyst"] = deque([...])
#   QUEUES["Researcher"] = deque([...])
QUEUES: Dict[str, deque] = defaultdict(deque)

# --------------------------------------------------------
# Endpoint: send a message to another agent
# --------------------------------------------------------
@app.post("/broker/send")
def broker_send(msg: A2AMessage):
    """
    Enqueues a message for the receiver.
    The message is appended to the receiver's queue.
    Example:
      POST /broker/send
      {
        "sender": "Researcher",
        "receiver": "Analyst",
        "type": "inform",
        "payload": {"pointer": "ctx://note/abc"},
        "conv_id": "conv-001"
      }
    """
    # Add message (as dict) to the receiver's queue
    QUEUES[msg.receiver].append(msg.dict())

    # Return confirmation with queue size for debugging
    return {
        "status": "enqueued",
        "receiver": msg.receiver,
        "size": len(QUEUES[msg.receiver])
    }

# --------------------------------------------------------
# Endpoint: poll (receive) a message for a specific agent
# --------------------------------------------------------
@app.get("/broker/poll/{agent}")
def broker_poll(agent: str):
    """
    Allows an agent to poll its queue for pending messages.
    If queue empty → returns {"status": "empty"}
    If queue has messages → pops and returns the first one.
    """
    # If the queue is empty, tell the agent there are no messages
    if not QUEUES[agent]:
        return {"status": "empty"}

    # Pop (remove + return) the oldest message from the queue
    msg = QUEUES[agent].popleft()

    # Return it with status OK
    return {"status": "ok", "message": msg}

# --------------------------------------------------------
# Endpoint: check how many messages are waiting for an agent
# --------------------------------------------------------
@app.get("/broker/size/{agent}")
def broker_size(agent: str):
    """
    Returns the number of pending messages in a receiver's queue.
    Example:
      GET /broker/size/Analyst  →  {"agent": "Analyst", "size": 2}
    """
    return {"agent": agent, "size": len(QUEUES[agent])}
