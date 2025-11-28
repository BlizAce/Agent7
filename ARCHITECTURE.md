# Agent7 Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      Agent7 CLI                             │
│                    (agent7.py)                              │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│                 Task Orchestrator                           │
│              (task_orchestrator.py)                         │
│                                                             │
│  • Workflow Management                                      │
│  • Task Execution                                           │
│  • Client Selection                                         │
└────────┬──────────────────────────┬─────────────────────────┘
         │                          │
         ▼                          ▼
┌──────────────────┐      ┌──────────────────────┐
│  Claude Client   │      │  Local LLM Client    │
│ (claude_client)  │      │ (local_llm_client)   │
│                  │      │                      │
│ • Planning       │      │ • Code Generation    │
│ • Code Gen       │      │ • Code Review        │
│ • Code Review    │      │ • OpenAI API         │
│ • Test Gen       │      │   Compatible         │
└────────┬─────────┘      └────────┬─────────────┘
         │                         │
         ▼                         ▼
┌────────────────┐        ┌──────────────────┐
│   Claude CLI   │        │    LM Studio     │
│   Subprocess   │        │  localhost:1234  │
└────────────────┘        └──────────────────┘

                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│                      Database                               │
│                   (database.py)                             │
│                                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────────┐  ┌────────┐ │
│  │ Projects │  │  Tasks   │  │Conversations │  │Results │ │
│  └──────────┘  └──────────┘  └──────────────┘  └────────┘ │
│                                                             │
│                    SQLite (agent7.db)                       │
└─────────────────────────────────────────────────────────────┘
```

## Components

### 1. CLI Interface (`agent7.py`)
- **Purpose**: User interaction and command routing
- **Responsibilities**:
  - Parse command-line arguments
  - Initialize components
  - Display results
  - Handle user commands

### 2. Task Orchestrator (`task_orchestrator.py`)
- **Purpose**: Coordinate task execution
- **Responsibilities**:
  - Execute individual tasks
  - Run complete workflows
  - Select appropriate AI client
  - Update database with results
  - Error handling

### 3. Claude Client (`claude_client.py`)
- **Purpose**: Interface with Claude CLI
- **Responsibilities**:
  - Execute Claude CLI commands
  - Handle planning requests
  - Generate code
  - Review code
  - Generate tests
  - Parse responses

### 4. Local LLM Client (`local_llm_client.py`)
- **Purpose**: Interface with local LLM (LM Studio)
- **Responsibilities**:
  - Send HTTP requests to OpenAI-compatible API
  - Handle chat completions
  - Check availability
  - Format prompts for local models
  - Parse responses

### 5. Database (`database.py`)
- **Purpose**: Persistent storage
- **Responsibilities**:
  - Store projects and tasks
  - Track conversations
  - Save results
  - Maintain history
  - Query and filter data

## Data Flow

### Creating and Executing a Task

```
User Command
    │
    ▼
┌────────────────────────┐
│ CLI parses command     │
│ Creates task in DB     │
└───────────┬────────────┘
            │
            ▼
┌────────────────────────┐
│ Orchestrator loads     │
│ task from DB           │
└───────────┬────────────┘
            │
            ▼
┌────────────────────────┐
│ Select AI client       │
│ (Claude or Local LLM)  │
└───────────┬────────────┘
            │
            ▼
┌────────────────────────┐
│ Send prompt to AI      │
│ Receive response       │
└───────────┬────────────┘
            │
            ▼
┌────────────────────────┐
│ Save to DB:            │
│ • Conversation         │
│ • Result               │
│ • Update task status   │
└───────────┬────────────┘
            │
            ▼
┌────────────────────────┐
│ Display result to user │
└────────────────────────┘
```

## Database Schema

### Projects Table
```sql
CREATE TABLE projects (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
)
```

### Tasks Table
```sql
CREATE TABLE tasks (
    id INTEGER PRIMARY KEY,
    project_id INTEGER,
    title TEXT NOT NULL,
    description TEXT,
    task_type TEXT NOT NULL,      -- planning, coding, testing
    status TEXT DEFAULT 'pending', -- pending, in_progress, completed, failed
    priority INTEGER DEFAULT 0,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    completed_at TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id)
)
```

### Conversations Table
```sql
CREATE TABLE conversations (
    id INTEGER PRIMARY KEY,
    task_id INTEGER,
    model_type TEXT NOT NULL,    -- claude_cli, local_llm
    prompt TEXT NOT NULL,
    response TEXT,
    metadata TEXT,               -- JSON string
    created_at TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES tasks(id)
)
```

### Results Table
```sql
CREATE TABLE results (
    id INTEGER PRIMARY KEY,
    task_id INTEGER,
    result_type TEXT NOT NULL,   -- code, test, plan, error
    content TEXT NOT NULL,
    metadata TEXT,               -- JSON string
    created_at TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES tasks(id)
)
```

## Workflow Execution

### Sequential Execution
Tasks are executed in priority order within their type:
1. **Planning Tasks** (priority: high → low)
2. **Coding Tasks** (priority: high → low)
3. **Testing Tasks** (priority: high → low)

### Client Selection Logic
```python
if prefer_local:
    if local_llm.is_available():
        use local_llm
    else:
        use claude_cli
else:
    if claude_cli.is_available():
        use claude_cli
    else:
        use local_llm
```

### Task Execution States
```
pending → in_progress → completed
                     ↘
                      failed
```

## Extension Points

### Adding New Task Types
1. Add task type to database schema
2. Implement execution method in `TaskOrchestrator`
3. Add CLI commands in `agent7.py`

### Adding New AI Providers
1. Create new client module (e.g., `openai_client.py`)
2. Implement same interface as existing clients
3. Update `TaskOrchestrator` to support new client
4. Add CLI options

### Adding New Features
- **Result exporters**: JSON, Markdown, HTML
- **Web UI**: Flask/FastAPI frontend
- **Webhooks**: Notify external systems
- **Scheduling**: Cron-like task execution
- **Collaboration**: Multi-user support
- **Version control**: Track changes to results

## Performance Considerations

### Database
- SQLite is sufficient for single-user, moderate workloads
- For heavy use, consider PostgreSQL
- Indexes can be added for faster queries

### AI Client Selection
- Local LLM: Faster, no API costs, lower quality
- Claude CLI: Slower, API costs, higher quality
- Choose based on task importance

### Caching
- Could cache common prompts/responses
- Would reduce API calls and costs
- Trade-off: freshness vs. speed

## Security Considerations

- API keys stored by Claude CLI (not in this code)
- Local LLM has no authentication by default
- Database has no encryption (suitable for non-sensitive data)
- For production: add authentication, encryption, rate limiting


