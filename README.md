# RESERVE-X

## Conditional Resource Reservation for Autonomous AI Agents

> **Don't reserve the resource. Reserve the RIGHT to use the resource.**

RESERVE-X is a resource coordination system designed for environments where multiple autonomous AI agents compete for limited shared resources.

Instead of immediately allocating a resource to an agent that *might* need it later, RESERVE-X creates a **conditional resource option** — giving the agent the right to request the resource in the future without consuming it immediately.

When the predicted need actually occurs, the agent can exercise the option and attempt to obtain the actual resource.

### What RESERVE-X combines

- Conditional resource reservation
- Probabilistic overcommitment analysis
- Workflow-based resource prediction
- Autonomous agent simulation
- What-If scenario simulation
- Offline resilience
- Local ML prediction
- Optional Gemini-powered workflow interpretation
- React monitoring dashboard

---

## The Problem

Autonomous AI agents increasingly operate simultaneously and compete for the same limited resources.

For example:

```text
Coding Agent
Testing Agent
Security Agent
Database Agent
Deployment Agent

may all require shared resources such as:

GPU Compute
Database Instances
Testing Environments
Terminal Environments
Deployment Infrastructure

The problem is that an agent may know:

"I will probably need this resource."

but not:

"I definitely need this resource right now."

Allocating resources immediately wastes capacity when the predicted need never occurs.

Waiting until the resource is actually needed can cause multiple agents to request the same resource simultaneously.

The RESERVE-X Approach

RESERVE-X introduces conditional resource reservation.

Instead of reserving the resource itself, an agent reserves the right to request the resource later.

Agent predicts future need
          |
          v
   Create Resource Option
          |
          v
      Risk Analysis
          |
      +---+---+
      |       |
      v       v
   Exercise  Cancel/Expire
      |
      v
Actual Resource Allocation

The fundamental distinction is:

Resource Option != Resource Allocation

A pending option does not consume the underlying resource.

Only exercising the option attempts to create an actual allocation.

Example

Suppose the system has:

GPU_COMPUTE capacity = 1

Three agents may need it:

Coding Agent      90%
Research Agent    80%
Testing Agent     70%

Instead of immediately allocating the GPU, RESERVE-X creates three conditional options.

The system can then calculate:

Capacity:          1
Expected Demand:   2.40
Overcommit Risk:   90.2%

This exposes potential contention before the agents actually compete for the resource.

If an option is exercised while capacity is unavailable, the request receives a conflict response and the option remains pending.

When the resource becomes available, the pending option can be exercised again.

Core Concepts
Resource

A concrete resource that can actually be allocated.

Example:

NVIDIA H100 Cluster Alpha
Capability

An abstract resource type required by an agent.

Examples:

GPU_COMPUTE
DATABASE
TESTING
TERMINAL
SECURITY_SCAN
DEPLOYMENT
Resource Option

A conditional reservation containing information such as:

Agent
Capability
Probability
Amount
Priority
Expiration
Status

Possible states:

PENDING
EXERCISED
CANCELLED
EXPIRED
Allocation

An actual assignment of a concrete resource.

The lifecycle is:

Resource Option
      |
      | exercise
      v
Resource Allocation
      |
      | release
      v
Resource Available
Features
1. Conditional Resource Options

Agents can create future resource claims without immediately consuming capacity.

Example:

{
  "agent_id": "coding-agent-01",
  "capability": "GPU_COMPUTE",
  "probability": 0.9,
  "amount": 1,
  "priority": 5
}
2. Probabilistic Risk Engine

RESERVE-X evaluates the probability that pending options will simultaneously require resources.

It calculates:

Expected demand
Resource capacity
Overcommitment probability
Resource contention
Risk level

Risk levels:

LOW
MEDIUM
HIGH
CRITICAL
3. Learned Workflow Prediction

RESERVE-X includes a local ML predictor based on historical agent workflows.

The current implementation uses:

scikit-learn
RandomForestClassifier

The predictor estimates which capability an agent is likely to require next.

Example:

{
  "capability": "GPU_COMPUTE",
  "probability": 0.87
}

The prediction can then be used to create a conditional resource option.

4. What-If Simulator

The What-If Simulator allows hypothetical scenarios to be evaluated without modifying the actual RESERVE-X state.

For example:

Current agents:    5
Scenario agents:  15

The system compares the current state with the hypothetical scenario and shows how resource demand and risk would change.

5. Live Autonomous Simulation

RESERVE-X includes a live simulation where multiple autonomous agents execute multi-step workflows.

Agents can:

Start workflows
Predict upcoming resource requirements
Create resource options
Exercise options
Encounter contention
Release resources
Continue to later workflow stages
6. Offline Resilience

RESERVE-X can continue critical operations during temporary network loss.

During an outage, the system can locally perform:

Resource option creation
Workflow prediction
Risk calculation
Event creation
Operation queuing

The architecture is:

Network Lost
     |
     v
Offline Manager
     |
     +----------------+
     |                |
     v                v
 Local ML         Local Risk
     |                |
     +-------+--------+
             |
             v
        SQLite Store
             |
             v
        Pending Queue

When connectivity returns:

Network Restored
       |
       v
Queue Synchronization
       |
       v
RESERVE-X API
       |
       v
Operations Reconciled

Queued operations use identifiers/idempotency handling to avoid duplicate synchronization.

Intelligence Layer

RESERVE-X can optionally use Gemini to interpret natural-language workflows.

For example:

"Run the tests, perform a security scan and deploy the application."

The intelligence layer can convert the workflow into structured information that can be used by the local prediction and reservation system.

The LLM is intentionally not a hard dependency.

Online
  |
  v
Gemini
  |
  v
Workflow Interpretation
  |
  v
Local ML Predictor
  |
  v
RESERVE-X Engine

If the LLM is unavailable:

Historical Workflow Data
          |
          v
Local ML Predictor
          |
          v
RESERVE-X Engine

This keeps the core reservation system operational without requiring an external AI service.

Architecture
                 +----------------------+
                 |   React Dashboard    |
                 +----------+-----------+
                            |
                            v
                 +----------------------+
                 |      FastAPI API     |
                 +----------+-----------+
                            |
        +-------------------+-------------------+
        |                   |                   |
        v                   v                   v
 +-------------+      +-------------+     +-------------+
 |   Options   |      | Risk Engine |     |  Resources  |
 +-------------+      +-------------+     +-------------+
        |                   |                   |
        +-------------------+-------------------+
                            |
                            v
                 +----------------------+
                 |    RESERVE-X Core    |
                 +----------+-----------+
                            |
             +--------------+--------------+
             |              |              |
             v              v              v
       ML Predictor   Offline Manager   Simulation
             |              |              |
             v              v              v
      Workflow Data      SQLite       Agent Workflows
Project Structure
RESERVE-X/
│
├── backend/
│   ├── api/
│   ├── engine/
│   ├── intelligence/
│   ├── models/
│   ├── offline/
│   ├── tests/
│   ├── main.py
│   └── requirements.txt
│
├── simulation/
│   ├── agents.py
│   ├── historical_data.py
│   ├── learned_predictor.py
│   ├── live_runner.py
│   ├── predictor.py
│   ├── reservex_client.py
│   ├── resources.py
│   └── simulator.py
│
├── frontend/
│   ├── src/
│   ├── package.json
│   └── ...
│
├── README.md
├── LICENSE
└── .gitignore
Tech Stack
Backend
Python
FastAPI
Uvicorn
Pydantic
SQLite
Frontend
React
TypeScript
Vite
Machine Learning
scikit-learn
Random Forest
AI
Gemini API
Local ML fallback
Simulation
Python-based autonomous agent simulation
Running RESERVE-X Locally
Requirements

Install:

Python 3.10+
Node.js
npm
Git
1. Clone the repository
git clone https://github.com/PranavAgrawal07/RESERVE-X.git
cd RESERVE-X
2. Install backend dependencies

From the project root:

pip install -r backend/requirements.txt

Using a virtual environment is recommended:

Windows
python -m venv .venv
.venv\Scripts\activate
pip install -r backend\requirements.txt
macOS/Linux
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
3. Install frontend dependencies

Open another terminal:

cd frontend
npm install
4. Start the backend

From the project root:

uvicorn backend.main:app --host 127.0.0.1 --port 8000

Backend:

http://127.0.0.1:8000

Swagger:

http://127.0.0.1:8000/docs

Keep this terminal running.

5. Start the frontend

Open another terminal:

cd frontend
npm run dev

Open the URL shown by Vite, normally:

http://localhost:5173

The complete local setup is:

Browser
   |
   v
React Dashboard
   |
   v
http://127.0.0.1:8000/api/v1
   |
   v
FastAPI Backend
Using the Dashboard

Once both services are running, the dashboard can be used to explore the system.

Dashboard

View:

Resources
Active options
Allocations
Risk
Recent events
System status
Options

Create and manage conditional resource options.

You can:

Create options
View pending options
Exercise options
Cancel options
Inspect option status
Risk

View:

Capacity
Expected demand
Overcommit probability
Risk level
Competing agents
What-If

Modify hypothetical conditions and compare them with the current system without changing the real state.

Live Simulation

Run autonomous agents through simulated workflows and watch their resource requirements evolve.

Offline Resilience

Demonstrate:

Disconnect
    ↓
Continue operating
    ↓
Create queued operations
    ↓
Reconnect
    ↓
Automatic synchronization
Using Swagger

FastAPI provides interactive API documentation at:

http://127.0.0.1:8000/docs

To test an endpoint:

Open Swagger
Select an endpoint
Click Try it out
Enter the request body
Click Execute
Inspect the response
Important API Endpoints
System
GET /api/v1/status
GET /api/v1/risk
GET /api/v1/events
Resources
GET  /api/v1/resources
POST /api/v1/resources
Options
GET   /api/v1/options
POST  /api/v1/options
PATCH /api/v1/options/{id}

POST /api/v1/options/{id}/exercise
POST /api/v1/options/{id}/cancel
Allocations
POST /api/v1/allocations/{id}/release
What-If
POST /api/v1/simulation/what-if
Live Simulation
GET  /api/v1/simulation/live/status
POST /api/v1/simulation/live/start
POST /api/v1/simulation/live/reset
Offline Resilience
GET  /api/v1/connectivity/status
POST /api/v1/connectivity/offline
POST /api/v1/connectivity/online
GET  /api/v1/connectivity/queue
GET  /api/v1/connectivity/events
Intelligence
POST /api/v1/intelligence/predict
GET  /api/v1/intelligence/history
GET  /api/v1/intelligence/status
POST /api/v1/intelligence/feedback
Example API Workflow
1. Create a resource
POST /api/v1/resources
{
  "name": "NVIDIA H100 Cluster Alpha",
  "capability": "GPU_COMPUTE",
  "capacity": 1
}
2. Create a conditional option
POST /api/v1/options
{
  "agent_id": "Coding-Agent",
  "capability": "GPU_COMPUTE",
  "probability": 0.9,
  "amount": 1,
  "priority": 5,
  "expires_at": "2026-12-31T23:59:59+00:00"
}

The option starts as:

PENDING

No GPU has been allocated yet.

3. Exercise the option
POST /api/v1/options/{option_id}/exercise

If capacity is available, an allocation is created.

If capacity is unavailable, the option remains pending.

4. Release the allocation
POST /api/v1/allocations/{allocation_id}/release

The resource becomes available again.

Testing Offline Resilience

To reproduce the offline demo:

Start the backend and frontend.
Confirm the dashboard shows ONLINE.
Disconnect Wi-Fi.
Confirm the dashboard switches to OFFLINE MODE.
Create a resource option.
Verify that it is placed in the offline queue.
Keep the application running while disconnected.
Reconnect Wi-Fi.
RESERVE-X automatically synchronizes the queued operation.

Offline operations are persisted locally in:

data/offline_resilience.db

The database is ignored by Git and is not committed to the repository.

Gemini Configuration

Gemini is optional.

If you want to use the Intelligence Layer, configure:

GEMINI_API_KEY=your_api_key_here

Do not put the API key directly into source code or commit it to GitHub.

Without Gemini, RESERVE-X can fall back to the local ML prediction system.

Testing

Run the backend test suite from the project root:

pytest

The tests cover:

Resource management
Option lifecycle
Allocation and release
Exercise conflicts
Risk calculation
What-If simulation
Learned prediction
Autonomous simulation
Live simulation
Offline queueing
Offline synchronization
Connectivity recovery
Intelligence functionality

To build the frontend:

cd frontend
npm run build
Deployment

RESERVE-X can be deployed as two services:

                 Internet
                    |
          +---------+---------+
          |                   |
          v                   v
   React Static Site      FastAPI Service
          |                   |
          +---------+---------+
                    |
                    v
                RESERVE-X
Backend

Build:

pip install -r backend/requirements.txt

Start:

uvicorn backend.main:app --host 0.0.0.0 --port $PORT
Frontend

Build:

npm install && npm run build

Publish directory:

dist

Configure the frontend API URL using:

VITE_API_BASE_URL
End-to-End Example

With one GPU:

GPU_COMPUTE capacity = 1

Three agents create options:

Coding Agent      90%
Research Agent    80%
Testing Agent     70%

RESERVE-X calculates:

Expected Demand = 2.40
Overcommit Risk = 90.2%

The Coding Agent exercises its option:

GPU available
      ↓
Coding Agent allocated GPU

The Research Agent attempts to exercise:

GPU unavailable
      ↓
409 Conflict
      ↓
Research option remains PENDING

The Coding Agent releases the GPU:

GPU released
      ↓
Research Agent exercises option
      ↓
Allocation created

The complete RESERVE-X workflow is:

Predict
   ↓
Reserve the RIGHT
   ↓
Measure Risk
   ↓
Need Materializes
   ↓
Exercise
   ↓
Allocate
   ↓
Release
Why RESERVE-X?

Traditional resource allocation asks:

Who gets the resource now?

RESERVE-X asks:

Who should have the right to use the resource if they actually need it?

This allows autonomous systems to reason about uncertain future demand while keeping actual resource allocation explicit.

Future Improvements
More advanced workflow forecasting
Reinforcement-learning-based reservation policies
Distributed resource coordination
Persistent production database
Multi-cluster coordination
Advanced capability matching
Dynamic agent priorities
Historical risk analytics
Adaptive prediction models
Team

Built as a 3-person hackathon project.

Backend & Core Engine
Conditional resource options
Resource lifecycle
Risk engine
FastAPI API
Offline resilience
Simulation & Prediction
Autonomous agent workflows
Historical workflow data
Learned prediction
Live simulation
Frontend
React dashboard
Resource monitoring
Option lifecycle
Risk visualization
What-If simulator
Offline resilience UI
License

This project is licensed under the MIT License.

RESERVE-X
Reserve the right. Allocate only when needed.

**This is the version I'd actually put on GitHub.** It gives a stranger the three things they need:

1. **Why the project exists**
2. **How the architecture/features work**
3. **Exactly how to clone it, run it, and use/demo it**

I would **not** add a huge endpoint-by-endpoint API manual, every implementation detail, or a giant architecture essay. The Swagger docs already handle the detailed API exploration.
