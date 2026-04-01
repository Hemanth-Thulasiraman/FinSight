FinSight — Autonomous Financial Research Agent

## What it does
FinSight is an autonomous financial research agent that compresses equity research time from hours to minutes. Financial analysts often have to gather company news, market data, and financial information from fragmented sources, and even then the resulting research can be incomplete, inconsistent, and difficult to audit. FinSight solves this by autonomously collecting relevant information, adapting its research path based on what it finds, and generating a structured, cited research brief with a full audit trail of the sources and tools used.

## Architecture
FinSight is built as a LangGraph-based research agent exposed through a FastAPI interface. A user request enters through the API layer, which validates and routes the request into the agent workflow. The workflow begins with a human-in-the-loop checkpoint for ticker ambiguity resolution, then checks memory for previously generated briefs using pgvector with PostgreSQL. If prior research exists, the system reuses it to avoid redundant tool calls and generate a “changes since last research” section. Otherwise, it performs a full run from scratch. The LLM follows a ReAct-style loop to choose tools, interpret outputs, and synthesize results into a structured brief. Before delivery, the output passes through a second human review checkpoint for validation of important numerical claims. Final briefs are stored in S3, system state and embeddings are persisted in PostgreSQL, and LangSmith provides tracing and observability.

[View Architecture Diagram](./docs/finsight_system_architecture.html)

| Component            | Decision                | Justification                                                                                                                                                  |
|----------------------|------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Agent framework      | LangGraph              | Provides graph-based orchestration for stateful, multi-step agent workflows with support for branching logic, checkpointing, and Human-in-the-Loop (HITL) control points. |
| Orchestration pattern| ReAct                  | Enables the agent to iteratively reason, select tools, observe outputs, and refine subsequent actions, making it suitable for research-style workflows with dynamic decision paths. |
| LLM                  | GPT-4o                 | Serves as the core reasoning engine for planning, tool selection, synthesis, and brief generation, with strong performance on structured reasoning and multi-step task execution. |
| Vector DB            | pgvector + PostgreSQL  | Supports semantic retrieval of prior research briefs and embeddings within the same relational database, reducing architectural complexity while enabling vector similarity search. |
| Embedding model      | text-embedding-3-small | Generates dense vector embeddings efficiently for retrieval tasks, offering a strong balance between semantic quality, latency, and cost.                      |
| API layer            | FastAPI                | Provides a high-performance Python API framework for request validation, routing, and integration with the LangGraph agent backend.                            |
| Monitoring           | LangSmith              | Enables end-to-end observability for agent execution, including trace inspection, tool-call monitoring, debugging, and workflow performance analysis.           |
| Deployment           | Railway                | Simplifies cloud deployment and environment management for rapid development, service hosting, and streamlined backend delivery.                                 |
| Storage              | PostgreSQL + S3        | PostgreSQL persists structured application state, embeddings, and prior briefs, while S3 provides durable object storage for finalized research artifacts.      |
## Setup

### Prerequisites
- Python 3.10+
- PostgreSQL with pgvector (we recommend Neon — free at neon.tech)
- OpenAI API key
- NewsAPI key (free at newsapi.org)

### Installation
1. Clone the repo
2. Create virtual environment
3. Install dependencies
4. Configure environment variables
5. Initialize database
6. Run the agent

### Step by step
```bash
# 1) Clone the repo
git clone <your-repo-url>
cd FinSight

# 2) Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3) Install dependencies
pip install -r requirements.txt

# 4) Configure environment variables
cp .env.example .env
````

Add your keys and database URL to `.env`:

```env
OPENAI_API_KEY=your_openai_key
NEWSAPI_KEY=your_newsapi_key
DATABASE_URL=your_neon_or_postgres_connection_string
```

```bash
# 5) Initialize the database
# Sign up at neon.tech, create a project called finsight
# Enable pgvector: run "CREATE EXTENSION IF NOT EXISTS vector;" in the SQL editor
# Copy your connection string to DATABASE_URL in .env
python test_db.py

# 6) Run the agent
python -m agent.run AAPL
```

## Usage

Run the agent by passing a ticker or company symbol as input. The workflow first resolves any ticker ambiguity through a human approval step, then checks whether a previous brief already exists for that company. If memory is available, the agent uses it to reduce redundant research and add a “changes since last research” section. Otherwise, it performs a full autonomous research run by calling tools for company profile data, recent news, and financial data. The final output is a structured markdown brief, which is reviewed, saved, and logged with traceable execution metadata.

Example:

```bash
python -m agent.run TSLA
```

What to expect:

* A structured research brief in markdown format
* Source-backed synthesis of recent company developments
* Reuse of prior research when available
* Logged execution state and tool traces for auditability
* Final brief saved locally in development and to S3 in production

## Project Structure

```text
FinSight/
├── agent/                               # LangGraph workflow, agent loop, and orchestration logic
├── tools/                               # Tool integrations for profile, news, financials, memory, and saving briefs
├── prompts/                             # Prompt templates for reasoning and brief generation
├── docs/
│   └── finsight_system_architecture.html   # System architecture diagram
├── test_db.py                           # Database connection and pgvector initialization test
├── requirements.txt                     # Python dependencies
├── .env.example                         # Example environment variables
└── README.md                            # Project documentation
```

## Evaluation Results

| Metric               | Target | Actual  |
| -------------------- | ------ | ------- |
| Task completion rate | >90%   | 100%    |
| Avg quality score    | >4/5   | 1.0/1.0 |
| Avg latency          | <90s   | 9.4s    |
| Cost per run         | <$0.50 | ~$0.007 |

## What I learned

Building FinSight showed me that financial research is a strong use case for agents because the workflow cannot be hardcoded in advance. The depth and direction of research depend on what the system discovers mid-run, so adaptive tool use matters much more than in a traditional pipeline. I also learned that observability, memory, and human review are essential in high-stakes domains, especially when numerical claims need to be trustworthy. Most importantly, a useful agent is not just about generating text — it also needs to justify where its conclusions came from and make that process auditable.

## Live Demo
API: https://web-production-20cc5.up.railway.app/docs  (working)
