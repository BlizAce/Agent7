# Agent7 - AI Task Management System

Agent7 is a comprehensive AI-powered task management system for autonomous software development. **Version 2.2+ works entirely with LM Studio** - no API required, no rate limits, completely local!

## 🎉 New in Version 2.2 (Current)

- **100% Local with LM Studio**: No Claude CLI required, completely free and unlimited
- **Simpler Architecture**: Single AI system, easier to use and maintain
- **Full Tool Chain**: Project exploration (7 tools) + file operations work seamlessly
- **Iterative Execution**: LM Studio explores, creates, validates in intelligent cycles
- **No Session Limits**: Run as long as you want with your local model

## 🚀 Features from Version 2.0-2.1

- **Web-Based UI**: Modern dashboard accessible at `http://localhost:5000`
- **Intelligent Orchestration**: LM Studio orchestrates Claude for optimal results
- **File Access**: Claude directly creates and modifies files in your project
- **Session Management**: Automatically handles Claude session limits and schedules resumption
- **Windows Service**: Scheduler runs as background service
- **Automated Testing**: Executes pytest and validates results with AI
- **Real-Time Output**: WebSocket-powered live output streaming
- **Project Explorer**: Browse and monitor file changes in real-time

## Features ✨

- **Dual AI Architecture**: LM Studio orchestrates, Claude executes
- **Task Types**: Planning, Coding, and Testing workflows
- **Direct File Operations**: Claude uses `--dangerously-skip-permissions` for file access
- **Session Recovery**: Auto-schedules task resumption when hitting API limits
- **Test Execution**: Runs pytest and validates with LM Studio
- **Web Interface**: Monitor tasks, view output, explore project files
- **Windows Service**: Background scheduler survives reboots
- **Local Database**: SQLite tracks everything with full history
- **Project Management**: Single-project focus with directory selection
- **Smart Validation**: AI validates all outputs before marking complete

## Prerequisites

1. **Python 3.8+**
2. **LM Studio** (required): Running at `http://localhost:1234/v1`
   - Download from: https://lmstudio.ai/
   - Load a code-capable model (recommend: DeepSeek Coder 33B, CodeLlama 34B)
   - Start the API server in LM Studio

**Note**: v2.2+ uses LM Studio only. Claude CLI is planned for v3.0 as an optional enhancement.

## Installation

1. Clone or download this repository

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Make the script executable (optional, Linux/Mac):
```bash
chmod +x agent7.py
```

## Quick Start (Web UI)

### Easiest Way: Use the Launcher

1. **Run the launcher:**
   ```cmd
   launch_agent7.bat
   ```
   
   This will:
   - Create virtual environment (if needed)
   - Install all dependencies
   - Start scheduler service
   - Launch web UI at `http://localhost:5000`

2. **Open your browser to `http://localhost:5000`**

3. **Select your project directory** in the UI

4. **Create and execute tasks** through the web interface

### Web UI Features

- **Dashboard**: Real-time status of LM Studio, Claude, and execution
- **Project Selection**: Browse and select project directories
- **Task Creation**: Create planning, coding, and testing tasks
- **Live Output**: Stream Claude's output in real-time via WebSocket
- **File Explorer**: View project files and recent modifications
- **Statistics**: Track completed, pending, and failed tasks
- **Task Details**: View full conversation history and results

## Quick Start (CLI)

### 1. Check System Status

```bash
python agent7.py status
```

This will show:
- Database status
- Claude CLI availability
- Local LLM availability

### 2. Create a Project

```bash
python agent7.py create-project "My Web App" "Building a REST API"
```

### 3. Create Tasks

```bash
# Planning task
python agent7.py create-task 1 --type planning --title "Design API" \
  --desc "Design RESTful API architecture with endpoints and data models"

# Coding task
python agent7.py create-task 1 --type coding --title "Implement API" \
  --desc "Create Flask API with user authentication and CRUD operations"

# Testing task  
python agent7.py create-task 1 --type testing --title "Test API" \
  --desc "Write comprehensive unit tests for all API endpoints"
```

### 4. Execute Tasks

Execute a single task:
```bash
python agent7.py execute-task 1
```

Execute all pending tasks in a project (workflow):
```bash
python agent7.py execute-workflow 1
```

### 5. View Results

List all projects:
```bash
python agent7.py list-projects
```

List all tasks:
```bash
python agent7.py list-tasks
```

View detailed task information:
```bash
python agent7.py task-details 1
```

## Usage Examples

### Using Local LLM Only

```bash
python agent7.py execute-task 1 --no-claude --prefer-local
```

### Using Claude CLI Only

```bash
python agent7.py execute-task 1 --no-local-llm
```

### Custom LM Studio URL

```bash
python agent7.py execute-task 1 --local-llm-url http://192.168.1.100:1234/v1
```

### Filter Tasks by Status

```bash
python agent7.py list-tasks --status pending
python agent7.py list-tasks --status completed
```

### Filter Tasks by Project

```bash
python agent7.py list-tasks --project 1
```

### Specify Programming Language

```bash
python agent7.py execute-task 1 --language javascript
python agent7.py execute-workflow 1 --language python
```

## Configuration Options

### Command Line Arguments

- `--db <path>`: Database file path (default: `agent7.db`)
- `--claude-cli <command>`: Claude CLI command (default: `claude`)
- `--local-llm-url <url>`: Local LLM API URL (default: `http://localhost:1234/v1`)
- `--prefer-local`: Prefer local LLM over Claude when both available
- `--no-claude`: Disable Claude CLI
- `--no-local-llm`: Disable local LLM
- `--language <lang>`: Programming language for coding/testing tasks (default: `python`)

## Architecture

### Core Components

1. **web_server.py**: Flask web application
   - Modern web UI with WebSocket support
   - Real-time output streaming
   - Project and task management
   - File browsing and statistics

2. **orchestration_brain.py**: AI orchestration layer
   - Uses LM Studio to create optimal prompts for Claude
   - Determines which Claude agents to use
   - Validates Claude's work
   - Assesses test results

3. **session_manager.py**: Session and scheduling management
   - Detects Claude session limits
   - Schedules automatic resumption
   - Saves checkpoints for recovery

4. **scheduler_service.py**: Windows service wrapper
   - Runs scheduler as background service
   - Survives system reboots
   - Handles scheduled task resumption

5. **test_runner.py**: Test execution engine
   - Runs pytest in project directory
   - Parses test results
   - Integrates with orchestration brain for validation

6. **database.py**: Enhanced SQLite database
   - Projects, tasks, conversations, results
   - Checkpoints for session recovery
   - File modifications tracking
   - Test execution history

7. **claude_client.py**: Enhanced Claude CLI integration
   - File access mode with `--dangerously-skip-permissions`
   - Real-time output streaming
   - Session limit detection
   - File modification parsing

8. **local_llm_client.py**: Local LLM integration
   - OpenAI-compatible API for LM Studio
   - Orchestration and validation
   - Decision making

9. **task_orchestrator.py**: Enhanced task execution
   - Integrates all components
   - Manages full workflow
   - Session recovery
   - Test execution

10. **agent7.py**: Original CLI interface
    - Backward compatible
    - Command-line task management

### Database Schema

**Projects**: Store project information
- id, name, description, timestamps

**Tasks**: Individual tasks
- id, project_id, title, description, task_type, status, priority, timestamps

**Conversations**: AI interactions
- id, task_id, model_type, prompt, response, metadata, timestamp

**Results**: Task outputs
- id, task_id, result_type, content, metadata, timestamp

## Workflow

### Enhanced Autonomous Workflow

1. **Project Selection**: Select your project directory via Web UI
2. **Task Creation**: Define what you want accomplished
3. **Orchestration Planning**: LM Studio analyzes task and creates optimal prompt
4. **Agent Selection**: Determines which Claude agents to use
5. **Claude Execution**: Claude runs in project directory with file access
6. **File Operations**: Claude directly creates/modifies files
7. **Test Execution**: System runs pytest automatically
8. **Validation**: LM Studio validates Claude's work and test results
9. **Session Recovery**: If Claude hits limits, automatically schedules resumption
10. **Completion**: Task marked complete with full history

### How It Works 🔄

### File Operations Workflow

Agent7 uses an intelligent file operations system:

1. **Prompt Generation**: LM Studio creates prompts that tell Claude to format files properly:
   ```
   File: example.py
   ```python
   code here
   ```
   ```

2. **Claude's Response**: Claude describes the code and formats file blocks

3. **Automatic Parsing**: Agent7's `FileOperations` module:
   - Extracts file blocks from Claude's output
   - Identifies filenames and content
   - Creates directories as needed
   - Writes files to the project directory
   - Tracks changes in database

4. **Validation**: LM Studio verifies files were created correctly

### Task Execution Workflow

- **LM Studio** acts as the "brain" - makes decisions, validates work
- **Claude CLI** acts as the "hands" - does the actual coding/planning
- **Web UI** lets you monitor everything in real-time
- **Scheduler** ensures tasks resume even if Claude hits session limits

## Tips

- Use **planning tasks** to break down complex problems
- Use **coding tasks** to generate implementation code
- Use **testing tasks** to create comprehensive test suites
- Review AI outputs in task details before using them
- Local LLM is faster but may have lower quality; Claude is slower but higher quality
- Use `--prefer-local` for quick iterations, Claude for important tasks

## Windows Task Scheduler (Automatic Resumption)

Agent7 uses Windows Task Scheduler to handle automatic task resumption when Claude hits session limits.

### Install Scheduler (Run as Administrator)

```cmd
create_scheduled_task.bat
```

This creates a background task that:
- Starts automatically on system boot
- Runs continuously in the background
- Checks for scheduled tasks every 30 seconds
- Automatically resumes tasks when session limits expire

### Manage Scheduler

**Check Status:**
```cmd
schtasks /Query /TN "Agent7Scheduler"
```

**Stop:**
```cmd
schtasks /End /TN "Agent7Scheduler"
```

**Restart:**
```cmd
schtasks /Run /TN "Agent7Scheduler"
```

**Remove:**
```cmd
remove_scheduled_task.bat
```

### Scheduler Features

- Runs in background even when UI is closed
- Survives system reboots
- Automatically resumes tasks at scheduled times
- Logs to `scheduler_debug.log`
- More reliable than Windows Services

## Troubleshooting

### Web UI won't start
- Check if port 5000 is available
- Make sure all dependencies installed: `pip install -r requirements.txt`
- Try running: `python web_server.py` to see detailed errors

### Claude CLI not found
- Install Claude CLI from https://docs.anthropic.com/claude/docs/claude-cli
- Make sure it's in your PATH
- Test with: `claude --version`

### Local LLM not available
- Start LM Studio and load a model
- Go to "Local Server" tab and click "Start Server"
- Verify at http://localhost:1234/v1/models
- Check config.py has correct LOCAL_LLM_URL

### No AI backend available
- Install at least one: Claude CLI or LM Studio
- Verify with: `python agent7.py status` or check Web UI status bar

### Session limit not handled
- Make sure scheduler service is running: `sc query Agent7Scheduler`
- If not installed, run: `install_service.bat` (as Administrator)
- Check `scheduler_service.log` for issues

### Tests not running
- Install pytest: `pip install pytest`
- Make sure test files exist in project directory
- Check ENABLE_TEST_EXECUTION in config.py

## License

MIT License - Feel free to use and modify as needed.

## Contributing

Contributions welcome! This is a flexible framework that can be extended with:
- Additional AI providers
- More task types
- Web UI
- Result exporters
- Integration with IDEs
- And more!

