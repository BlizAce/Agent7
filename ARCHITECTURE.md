# Agent7 Architecture (Version 2.0)

## System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                   User Interface Layer                      │
│                                                             │
│  ┌──────────────┐                    ┌──────────────┐      │
│  │   Web UI     │                    │  CLI (legacy)│      │
│  │ localhost:   │                    │  agent7.py   │      │
│  │   5000       │                    └──────┬───────┘      │
│  │ (Flask +     │                           │              │
│  │  SocketIO)   │                           │              │
│  └──────┬───────┘                           │              │
└─────────┼───────────────────────────────────┼──────────────┘
          │                                   │
          └───────────────┬───────────────────┘
                          ▼
┌─────────────────────────────────────────────────────────────┐
│              Enhanced Task Orchestrator                     │
│              (task_orchestrator.py)                         │
│                                                             │
│  • Brain Integration    • Session Recovery                 │
│  • File Access         • Test Execution                    │
│  • Workflow Management • AI Validation                     │
└───────┬──────────────────┬──────────────────┬──────────────┘
        │                  │                  │
        ▼                  ▼                  ▼
┌───────────────┐  ┌──────────────┐  ┌──────────────────┐
│ Orchestration │  │   Session    │  │  Test Runner     │
│     Brain     │  │   Manager    │  │ (test_runner.py) │
│ (LM Studio)   │  │              │  │                  │
│               │  │ • Scheduling │  │ • Pytest Exec    │
│ • Plan Prompts│  │ • Checkpoints│  │ • Result Parse   │
│ • Select      │  │ • Recovery   │  │ • Validation     │
│   Agents      │  └──────┬───────┘  └──────────────────┘
│ • Validate    │         │
│   Results     │         ▼
└───────┬───────┘  ┌──────────────────┐
        │          │ Scheduler Service│
        │          │ (Windows Service)│
        │          │                  │
        │          │ • Background Run │
        │          │ • Auto Resume    │
        │          └──────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│                     AI Execution Layer                      │
│                                                             │
│  ┌──────────────────────┐      ┌─────────────────────┐    │
│  │   Claude Client      │      │  Local LLM Client   │    │
│  │  (claude_client.py)  │      │ (local_llm_client)  │    │
│  │                      │      │                     │    │
│  │ • File Access Mode   │      │ • Orchestration     │    │
│  │ • --dangerously-     │      │ • Validation        │    │
│  │   skip-permissions   │      │ • Decision Making   │    │
│  │ • Session Detection  │      └─────────┬───────────┘    │
│  │ • File Tracking      │                │                │
│  └──────────┬───────────┘                │                │
│             │                            │                │
│             ▼                            ▼                │
│  ┌──────────────────┐        ┌──────────────────┐        │
│  │   Claude CLI     │        │    LM Studio     │        │
│  │  (in project     │        │  localhost:1234  │        │
│  │   directory)     │        │                  │        │
│  └──────────────────┘        └──────────────────┘        │
└──────────────┬──────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────┐
│              Enhanced Database (database.py)                │
│                                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────────┐            │
│  │ Projects │  │  Tasks   │  │Conversations │            │
│  └──────────┘  └──────────┘  └──────────────┘            │
│                                                             │
│  ┌──────────┐  ┌──────────────┐  ┌────────────────┐      │
│  │ Results  │  │ Checkpoints  │  │ File           │      │
│  │          │  │ (recovery)   │  │ Modifications  │      │
│  └──────────┘  └──────────────┘  └────────────────┘      │
│                                                             │
│  ┌────────────────┐                                        │
│  │ Test Executions│                                        │
│  │  (pytest runs) │                                        │
│  └────────────────┘                                        │
│                                                             │
│                    SQLite (agent7.db)                       │
└─────────────────────────────────────────────────────────────┘
```

## Components

### 1. Web Server (`web_server.py`)
- **Purpose**: Modern web interface and API
- **Responsibilities**:
  - Serve web dashboard at localhost:5000
  - Provide RESTful API endpoints
  - WebSocket for real-time output streaming
  - Project and task management
  - Background task execution
  - File browsing and statistics

### 2. Orchestration Brain (`orchestration_brain.py`)
- **Purpose**: Intelligent AI orchestration using LM Studio
- **Responsibilities**:
  - Create optimal prompts for Claude
  - Determine which Claude agents to use
  - Validate Claude's outputs
  - Assess test execution results
  - Make strategic decisions about next actions
  - Parse structured responses

### 3. Session Manager (`session_manager.py`)
- **Purpose**: Handle Claude session limits and scheduling
- **Responsibilities**:
  - Detect "Session limit reached" messages
  - Parse reset times from Claude output
  - Save checkpoints for task resumption
  - Schedule automatic continuation
  - Resume tasks at scheduled times
  - Integrate with Windows scheduler service

### 4. Scheduler Service (`scheduler_service.py`)
- **Purpose**: Windows service for background scheduling
- **Responsibilities**:
  - Run as Windows background service
  - Monitor database for scheduled tasks
  - Resume tasks at specified times
  - Survive system reboots
  - Log operations to file
  - Provide service management commands

### 5. Test Runner (`test_runner.py`)
- **Purpose**: Execute and validate tests
- **Responsibilities**:
  - Execute pytest in project directory
  - Parse test output (passed/failed/skipped)
  - Support unittest framework
  - Save results to database
  - Format human-readable summaries
  - Integrate with orchestration brain

### 6. Enhanced Task Orchestrator (`task_orchestrator.py`)
- **Purpose**: Coordinate complete workflows
- **Responsibilities**:
  - Integrate all new components
  - Execute tasks with file access
  - Handle session recovery
  - Run automated tests
  - Validate with AI brain
  - Track file modifications
  - Support both CLI and web UI

### 7. Enhanced Claude Client (`claude_client.py`)
- **Purpose**: Interface with Claude CLI with file operations
- **Responsibilities**:
  - Execute Claude with `--dangerously-skip-permissions`
  - Set working directory to project path
  - Stream output in real-time
  - Detect session limit messages
  - Parse file modifications from output
  - Support agent instructions
  - Handle conversation continuity

### 8. Local LLM Client (`local_llm_client.py`)
- **Purpose**: Interface with LM Studio for orchestration
- **Responsibilities**:
  - Send HTTP requests to OpenAI-compatible API
  - Handle orchestration prompts
  - Validate outputs
  - Make decisions
  - Check availability
  - Format prompts for local models

### 9. Enhanced Database (`database.py`)
- **Purpose**: Comprehensive persistent storage
- **Responsibilities**:
  - Store projects, tasks, conversations, results
  - Track checkpoints for session recovery
  - Log file modifications
  - Store test execution history
  - Maintain complete audit trail
  - Support all new features

### 10. CLI Interface (`agent7.py`) - Legacy
- **Purpose**: Command-line interface (backward compatible)
- **Responsibilities**:
  - Parse command-line arguments
  - Initialize components
  - Display results
  - Handle traditional CLI commands

### 11. Configuration (`config.py`)
- **Purpose**: Centralized configuration management
- **Responsibilities**:
  - Store all system settings
  - Validate configuration
  - Provide defaults
  - Support customization
  - Export configuration as dictionary

## Data Flow

### Enhanced Task Execution Flow (Version 2.0)

```
User Creates Task in Web UI
    │
    ▼
┌─────────────────────────────────────┐
│ Web Server receives request         │
│ Task saved to database              │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│ User clicks "Execute"               │
│ Background thread started           │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│ Orchestrator loads task             │
│ Gets project directory              │
│ Lists existing files                │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│ Orchestration Brain (LM Studio)     │
│ • Analyzes task requirements        │
│ • Creates optimal prompt            │
│ • Selects Claude agents             │
│ • Defines validation criteria       │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│ Claude CLI launched with:           │
│ • --dangerously-skip-permissions    │
│ • Working dir = project directory   │
│ • Agent instructions                │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│ Claude executes in project:         │
│ • Creates/modifies files            │
│ • Streams output to WebSocket       │
│ • User sees real-time progress      │
└──────────────┬──────────────────────┘
               │
               ▼
        ┌──────┴──────┐
        │             │
        ▼             ▼
┌───────────┐  ┌─────────────────────┐
│ Session   │  │ Execution completes │
│ Limit?    │  │ Files detected      │
└─────┬─────┘  └──────────┬──────────┘
      │                   │
      │ YES               │ NO
      ▼                   ▼
┌───────────────────┐  ┌────────────────────┐
│ Save checkpoint   │  │ Test Runner        │
│ Parse reset time  │  │ • Execute pytest   │
│ Schedule resume   │  │ • Parse results    │
│ Scheduler service │  └─────────┬──────────┘
│ will continue     │            │
└───────────────────┘            ▼
                      ┌────────────────────┐
                      │ Orchestration Brain│
                      │ validates:         │
                      │ • Claude's work    │
                      │ • Test results     │
                      │ • File changes     │
                      └─────────┬──────────┘
                                │
                                ▼
                      ┌────────────────────┐
                      │ Save to Database:  │
                      │ • Conversation     │
                      │ • Results          │
                      │ • File mods        │
                      │ • Test execution   │
                      │ • Validation notes │
                      └─────────┬──────────┘
                                │
                                ▼
                      ┌────────────────────┐
                      │ Update task status │
                      │ • completed ✅     │
                      │ • failed ❌        │
                      │ • scheduled ⏰     │
                      └─────────┬──────────┘
                                │
                                ▼
                      ┌────────────────────┐
                      │ WebSocket notifies │
                      │ UI updates display │
                      └────────────────────┘
```

### Session Recovery Flow

```
Claude hits session limit
    │
    ▼
┌─────────────────────────────────────┐
│ "Session limit reached ∙ resets 10pm" │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│ Session Manager:                    │
│ • Parses reset time                 │
│ • Saves checkpoint to database      │
│ • Includes conversation ID          │
│ • Stores remaining work             │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│ Task status → "pending"             │
│ User sees: "Scheduled for 10pm"     │
└─────────────────────────────────────┘
               │
               ⏰ Wait until 10pm
               │
               ▼
┌─────────────────────────────────────┐
│ Scheduler Service (running in       │
│ background) checks database         │
│ Finds scheduled checkpoint          │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│ Loads checkpoint data               │
│ Restores context                    │
│ Continues conversation with Claude  │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│ Task resumes automatically          │
│ Continues from where it left off    │
└─────────────────────────────────────┘
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

### Checkpoints Table (NEW)
```sql
CREATE TABLE checkpoints (
    id INTEGER PRIMARY KEY,
    task_id INTEGER,
    conversation_id TEXT,        -- Claude conversation ID
    project_directory TEXT,
    remaining_prompt TEXT,
    scheduled_for TIMESTAMP,     -- When to resume
    checkpoint_data TEXT,        -- JSON with full state
    created_at TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES tasks(id)
)
```

### File Modifications Table (NEW)
```sql
CREATE TABLE file_modifications (
    id INTEGER PRIMARY KEY,
    task_id INTEGER,
    filepath TEXT NOT NULL,
    action TEXT NOT NULL,        -- created, modified, deleted
    detected_at TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES tasks(id)
)
```

### Test Executions Table (NEW)
```sql
CREATE TABLE test_executions (
    id INTEGER PRIMARY KEY,
    task_id INTEGER,
    test_code TEXT,
    execution_output TEXT,
    passed BOOLEAN,
    validation_notes TEXT,       -- From LM Studio validation
    executed_at TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES tasks(id)
)
```

## Workflow Execution

### Enhanced Execution Model (Version 2.0)

```
1. Orchestration Planning (LM Studio)
   ↓
2. Claude Execution (with file access)
   ↓
3. Session Management (if needed)
   ↓
4. Test Execution (pytest)
   ↓
5. AI Validation (LM Studio)
   ↓
6. Completion
```

### Dual AI Architecture

**LM Studio (Brain)**:
- Analyzes tasks
- Creates prompts
- Selects agents
- Validates outputs
- Makes decisions

**Claude CLI (Hands)**:
- Executes tasks
- Creates files
- Modifies code
- Follows instructions
- Reports results

### Task Execution States (Enhanced)

```
pending → in_progress → completed ✅
                     ↘
                      failed ❌
                     ↗
         scheduled ⏰ (session limit)
              ↓
        (auto-resume at scheduled time)
              ↓
         in_progress (continued)
```

### Orchestration Flow

```python
# Step 1: Brain creates strategy
orchestration = brain.create_claude_prompt_for_task(
    task_description,
    task_type,
    project_context
)
# Returns: {
#   'agents': ['coding', 'testing'],
#   'prompt': '...',
#   'validation_criteria': '...'
# }

# Step 2: Execute with Claude
result = claude.send_message_with_file_access(
    prompt=orchestration['prompt'],
    project_directory=project_dir,
    use_agents=orchestration['agents']
)

# Step 3: Handle session limit if needed
if result['session_limited']:
    session_manager.schedule_resume(...)
    return 'SCHEDULED'

# Step 4: Run tests
test_results = test_runner.execute_pytest(project_dir)

# Step 5: Validate with brain
validation = brain.validate_claude_work(
    task_type,
    task_description,
    result['response'],
    result['files_modified'],
    orchestration['validation_criteria']
)

# Step 6: Complete or fail based on validation
if validation['status'] == 'COMPLETE':
    mark_complete()
else:
    mark_failed()
```

## Web UI Architecture

### Frontend (Single Page Application)

```
templates/index.html
    │
    ├─── static/css/style.css (styling)
    │
    └─── static/js/app.js (logic)
         │
         ├─── REST API calls (/api/*)
         │
         └─── WebSocket (real-time updates)
```

### Backend (Flask + Socket.IO)

```
web_server.py
    │
    ├─── HTTP Routes
    │    ├─── GET  /api/status
    │    ├─── GET  /api/tasks
    │    ├─── POST /api/tasks
    │    ├─── POST /api/execute/{task_id}
    │    ├─── GET  /api/files
    │    └─── GET  /api/stats
    │
    ├─── WebSocket Events
    │    ├─── output (Claude output streaming)
    │    ├─── task_status (status updates)
    │    └─── execution_complete
    │
    └─── Background Threads
         └─── execute_task_thread()
```

### Real-Time Communication

```
Web Browser
    ↓ (HTTP)
Flask Server
    ↓ (function call)
Task Orchestrator
    ↓ (subprocess)
Claude CLI
    ↓ (stdout)
Task Orchestrator
    ↓ (emit)
Socket.IO
    ↓ (WebSocket)
Web Browser (live update)
```

## Windows Service Architecture

### Service Components

```
Scheduler Service (scheduler_service.py)
    │
    ├─── Service Management
    │    ├─── Install
    │    ├─── Start/Stop
    │    ├─── Status
    │    └─── Uninstall
    │
    ├─── Main Loop
    │    ├─── Check database every 30s
    │    ├─── Find scheduled checkpoints
    │    └─── Trigger resume callback
    │
    └─── Logging
         └─── scheduler_service.log
```

### Service Lifecycle

```
Install → Configure → Start → Running → Stop → Uninstall
                        ↓         │
                        └────────┘
                    (auto-restart on failure)
```

## Extension Points

### Adding New Task Types
1. Add task type to database schema
2. Implement execution method in `TaskOrchestrator`
3. Add web UI support
4. Update orchestration brain logic

### Adding New AI Providers
1. Create new client module
2. Implement same interface as existing clients
3. Update `TaskOrchestrator` to support new client
4. Add configuration options
5. Update web UI status display

### Adding New Features (Examples)

#### Multi-Project Support
- Update web UI for project switching
- Maintain separate task queues
- Enhanced project management

#### Result Exporters
- Add export buttons to web UI
- Implement formatters (JSON, Markdown, HTML)
- Download functionality

#### Advanced Analytics
- Task completion metrics
- Time tracking
- Success rates
- Performance dashboards

#### Plugin System
- Define plugin interface
- Plugin discovery mechanism
- Dynamic loading
- Custom agents support

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

### Current Implementation
- **API keys**: Stored by Claude CLI (not in this code)
- **Local LLM**: No authentication by default (localhost only)
- **Database**: No encryption (suitable for local, non-sensitive use)
- **Web UI**: No authentication (localhost only)
- **File Access**: Claude has full permissions via `--dangerously-skip-permissions`
- **Windows Service**: Runs under local system account

### Production Hardening (Future)
- Add web UI authentication (sessions, JWT)
- Implement rate limiting
- Add database encryption
- Restrict file access permissions
- Use dedicated service account
- Add audit logging
- Implement HTTPS
- Add CORS protection
- Validate all inputs
- Sanitize outputs

### File Access Security

**Current Approach**:
- Claude runs with `--dangerously-skip-permissions`
- Has full access to project directory
- No sandboxing

**Rationale**:
- Designed for trusted, local use
- User selects project directory explicitly
- All operations logged in database
- User can review before accepting changes

**For Production**:
- Implement file operation approval workflow
- Add file access whitelist/blacklist
- Sandbox Claude execution
- Require explicit user confirmation

## Performance Considerations

### Database
- SQLite adequate for single-user workload
- Indexes on commonly queried fields
- Checkpoint cleanup to prevent bloat
- Consider PostgreSQL for multi-user

### AI Response Times
- **LM Studio**: ~1-5 seconds (fast)
- **Claude CLI**: ~5-30 seconds (moderate)
- Both run in background threads (non-blocking UI)

### Web UI Responsiveness
- WebSocket for real-time updates
- Background task execution
- Progressive loading
- Efficient React-less design

### Caching Strategies
- **Prompt templates**: Cached in brain
- **Validation patterns**: Reused across tasks
- **File lists**: Cached per project
- **Test results**: Stored for comparison

### Scalability Limits
- Single project focus (by design)
- One task execution at a time
- Suitable for individual developers
- Not designed for team collaboration

## Monitoring and Observability

### Available Logs
- `scheduler_service.log` - Service operations
- Database - Complete audit trail
- Web console - Real-time output
- Flask debug logs (if enabled)

### Metrics Tracked
- Task success/failure rates
- Execution times
- Session limit hits
- Test pass rates
- File modification counts

### Health Checks
- LM Studio availability
- Claude CLI functionality
- Database connectivity
- Scheduler service status
- Disk space for database

## Disaster Recovery

### Backup Strategy
- Regular database backups (manual)
- Checkpoint data preserved
- Conversation history maintained
- Project files under version control (recommended)

### Recovery Scenarios

**Database Corruption**:
- Restore from backup
- Re-run failed tasks

**Service Crash**:
- Auto-restart by Windows service manager
- Scheduled tasks continue after restart

**Power Loss**:
- Scheduler service starts on boot
- Scheduled tasks resume automatically
- In-progress tasks may need manual restart

**Session Timeout**:
- Automatic detection
- Checkpoint created
- Scheduled for resumption
- No data loss


