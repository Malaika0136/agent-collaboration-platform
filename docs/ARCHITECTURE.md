# Architecture Documentation

## System Overview

The Agent Collaboration Platform is a distributed system designed to enable multiple AI agents to work together asynchronously. It demonstrates key patterns for building scalable, loosely-coupled agent systems.

## Core Components

### 1. Frontend Service (Port 8000)
**Role:** User-facing orchestrator and web interface

- Presents a web UI for users to submit documents/queries
- Coordinates the analysis workflow
- Stores documents in the MCP Registry
- Sends tasks to the Analyst via the Broker
- Polls for results and displays them to users

**Key Endpoints:**
- `GET /` - Web interface
- `POST /analyze` - Submit document for analysis

### 2. Broker Service (Port 7003)
**Role:** Asynchronous message router for agent communication

**Pattern:** In-memory message queue with per-receiver queues

The Broker decouples agents so they don't need to know about each other's addresses or availability.

- Maintains separate message queues for each agent
- Agents send messages without waiting for immediate delivery
- Receiving agents poll for their messages at their own pace
- Messages include: sender, receiver, type, payload, and conversation ID

**Key Endpoints:**
- `POST /a2a/send` - Queue a message for delivery
- `GET /a2a/poll/{receiver}` - Fetch one message for a receiver

**Message Format:**
```json
{
  "sender": "Frontend",
  "receiver": "Analyst",
  "type": "analyze",
  "payload": {"pointer": "ctx://note/abc-123", "data": "..."},
  "conv_id": "conv-xyz"
}
```

### 3. MCP Registry (Port 7000)
**Role:** Centralized context/document storage

**Pattern:** Shared memory that enables agents to reference documents without transferring large amounts of data

- Stores documents with metadata
- Generates unique resource identifiers (pointers)
- Provides simple token-based authentication
- Returns resource pointers (e.g., `ctx://note/uuid`) instead of raw data

**Key Endpoints:**
- `POST /mcp/resources/create` - Store a document, get pointer
- `GET /mcp/resources/fetch/{rid}` - Retrieve document by ID

**Data Structure:**
```json
{
  "data": "Document content here",
  "owner": "Researcher",
  "meta": {
    "topic": "business",
    "source": "user_input"
  }
}
```

### 4. Analyst Agent (Port 7002)
**Role:** Specialized AI agent for document analysis

- Polls the Broker for messages addressed to "Analyst"
- Extracts the resource pointer from messages
- Fetches the document from MCP Registry
- Calls Groq LLM to:
  - Extract key performance indicators (KPIs)
  - Generate a ~120-word summary
  - Analyze sentiment and key insights
- Sends confirmation message back via Broker

**Key Endpoints:**
- `GET /inbox` - View recently processed messages
- `DELETE /inbox/clear` - Clear inbox

**Processing Flow:**
```
1. Poll Broker for "Analyst" messages
2. Extract pointer: "ctx://note/abc-123"
3. Fetch document from MCP using pointer
4. Send to Groq LLM for analysis
5. Format results
6. Send confirmation back through Broker
```

### 5. Researcher Agent (Port 7001)
**Role:** Creates and manages research workflows

- Can programmatically create documents
- Stores documents in MCP Registry
- Sends workflow initiation messages to other agents
- Receives confirmations and results

**Used For:**
- Batch processing scenarios
- Programmatic document creation
- Workflow orchestration

## Communication Patterns

### Pattern 1: Request-Response (Asynchronous)
```
Frontend → [Broker] → Analyst
          ↓ (stores message)
        [Queue]
          ↓ (polled by Analyst)
       Analyst → [Broker] → Frontend
                ↓ (stores reply)
              [Queue]
                ↓ (polled by Frontend)
```

### Pattern 2: Shared Memory Reference
Instead of:
```
Frontend → [Large Document] → Analyst
```

We do:
```
Frontend → [Pointer: ctx://note/abc-123] → Analyst
Analyst → [Fetch from MCP Registry] → Document
```

Benefits:
- Smaller messages
- Efficient bandwidth usage
- Agents can independently update shared context
- Easier to implement document versioning

## Data Flow Example

### Complete Analysis Workflow

```
1. USER INPUT
   User enters text in web UI

2. FRONTEND STORES
   Frontend calls: POST /mcp/resources/create
   MCP returns: pointer = "ctx://note/abc-123"

3. FRONTEND SENDS MESSAGE
   Frontend sends to Broker:
   {
     "sender": "Frontend",
     "receiver": "Analyst",
     "type": "analyze",
     "payload": {"pointer": "ctx://note/abc-123"},
     "conv_id": "conv-xyz"
   }

4. BROKER QUEUES
   Broker stores message in Analyst's queue

5. ANALYST POLLS
   Analyst polls: GET /a2a/poll/Analyst
   Receives the message above

6. ANALYST FETCHES DOCUMENT
   Analyst calls: GET /mcp/resources/fetch/abc-123
   MCP returns: {"data": "User's text", "owner": "Frontend", ...}

7. ANALYST PROCESSES
   Analyst sends to Groq LLM:
   "Analyze this: {text}"
   Groq returns: KPIs, summary, insights

8. ANALYST RESPONDS
   Analyst sends to Broker:
   {
     "sender": "Analyst",
     "receiver": "Frontend",
     "type": "analysis_complete",
     "payload": {"kpis": [...], "summary": "..."},
     "conv_id": "conv-xyz"
   }

9. FRONTEND POLLS
   Frontend polls: GET /a2a/poll/Frontend
   Receives Analyst's response

10. FRONTEND DISPLAYS
    User sees results in web UI
```

## Design Decisions

### Why Asynchronous Messaging?
- **Scalability:** Agents don't block waiting for responses
- **Resilience:** Agents can fail independently without cascading failures
- **Flexibility:** Easy to add new agents without modifying existing ones
- **Real-time:** Long-running processes don't freeze the UI

### Why MCP Registry?
- **Efficiency:** Large documents referenced by pointer, not copied
- **Auditability:** Central log of all stored documents
- **Sharing:** Multiple agents can reference the same document
- **Extensibility:** Easy to add versioning, access control, etc.

### Why Token Authentication?
- **Simple:** No complex OAuth/JWT for internal services
- **Secure:** Shared secret prevents unauthorized access
- **Easy:** Environment variable configuration

## Scalability Considerations

### Current Limitations
- MCP Registry is in-memory (limited to available RAM)
- Broker queues are in-memory (messages lost on restart)
- No distributed deployment support

### Future Enhancements
- **Persistent Storage:** Use PostgreSQL for MCP Registry and message logs
- **Message Queue:** Replace in-memory queues with RabbitMQ/Kafka
- **Load Balancing:** Deploy multiple instances behind a load balancer
- **Caching:** Add Redis for performance
- **Monitoring:** Prometheus metrics and distributed tracing

## Security Considerations

### Current
- Simple token-based authentication
- No encryption in transit
- No user authentication on frontend

### Recommendations
- Use HTTPS/TLS in production
- Implement proper user authentication
- Add rate limiting
- Validate all inputs
- Use secrets manager for credentials
- Implement request signing
- Add audit logging

## Testing Strategy

### Unit Tests
- Individual service business logic
- Message formatting and parsing
- MCP Registry operations

### Integration Tests
- End-to-end workflows
- Inter-service communication
- Error handling and recovery

### Load Tests
- Concurrent message processing
- Large document handling
- Service scaling limits

## Deployment Architecture

### Development
All services on localhost with fixed ports and in-memory storage

### Production
```
User → [Load Balancer] → [Frontend (scaled)]
                              ↓
                    [Service Mesh/API Gateway]
                    ↓ ↓ ↓ ↓ ↓
            [Analyst] [Researcher] [Broker] [MCP Registry]
                              ↓
                    [Persistent Storage]
                    - PostgreSQL
                    - Redis Cache
```

## Configuration Management

Services use environment variables for configuration:
- `GROQ_API_KEY` - LLM provider key
- `MCP_BASE` - Registry location
- `MCP_REGISTRY_TOKEN` - Shared secret
- `BROKER_URL` - Message broker location

This enables:
- Easy local development with defaults
- Production deployment with custom values
- Docker-Compose and Kubernetes support
