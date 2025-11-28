# Agent7 - Quick Start Guide (Version 2.0)

Get up and running with Agent7's web interface in 5 minutes!

## 🚀 Fastest Way: Use the Launcher

### Step 1: Double-click `launch_agent7.bat`

That's it! The launcher will:
- ✅ Create virtual environment (if needed)
- ✅ Install all dependencies
- ✅ Start the scheduler service
- ✅ Launch the web UI at `http://localhost:5000`
- ✅ Open your browser automatically

## Manual Installation

If you prefer manual setup:

```bash
# Install dependencies
pip install -r requirements.txt
```

## Step 2: Setup AI Backend

Choose **one or both**:

### Option A: Local LLM (LM Studio)

1. Download LM Studio from https://lmstudio.ai/
2. Load a model (e.g., Llama 3, Mistral, etc.)
3. Go to the "Local Server" tab
4. Click "Start Server"
5. Verify it's running at `http://localhost:1234`

### Option B: Claude CLI

```bash
# Install Claude CLI (if not already installed)
# Follow: https://docs.anthropic.com/claude/docs/claude-cli

# Configure with your API key
claude configure
```

## Step 3: Verify Setup (Optional)

```bash
python test_setup.py
```

This will check:
- ✅ Database functionality
- ✅ Local LLM availability
- ✅ Claude CLI availability

## Step 4: Use the Web UI (Recommended)

### 4a. Access the Dashboard

Open your browser to `http://localhost:5000`

You'll see:
- 📊 Status indicators (LM Studio, Claude, execution state)
- 📁 Project directory selector
- 📝 Task creation form
- 💻 Live output console
- 📂 Project file explorer
- 📈 Statistics dashboard

### 4b. Select Your Project Directory

1. Enter your project path (e.g., `C:\Projects\MyApp`)
2. Click "Select Project"
3. The system will scan and display your files

### 4c. Create Your First Task

1. **Title**: "Add user authentication"
2. **Description**: "Implement JWT-based authentication with login and logout endpoints"
3. **Type**: Coding
4. **Priority**: 5
5. Click "Create Task"

### 4d. Execute the Task

1. Find your task in the tasks list
2. Click "▶️ Execute"
3. Watch the magic happen in real-time:
   - 🧠 LM Studio analyzes and creates optimal prompt
   - 🤖 Claude launches in your project directory
   - 📝 Files are created/modified automatically
   - 🧪 Tests run automatically
   - ✅ AI validates the results

### 4e. View Results

- Check the live output console for Claude's work
- See file modifications in the project explorer
- View detailed task results by clicking "📋 Details"

## Alternative: CLI Usage (Still Supported)

### Step 4: First Project (CLI)

```bash
# Check status
python agent7.py status

# Create a project
python agent7.py create-project "Hello World" "My first Agent7 project"

# Create a planning task
python agent7.py create-task 1 \
  --type planning \
  --title "Plan Hello World" \
  --desc "Create a plan for a simple hello world program"

# Execute the task
python agent7.py execute-task 1

# View the results
python agent7.py task-details 1
```

## Step 5: Install Task Scheduler (Recommended)

For automatic task resumption when Claude hits session limits:

```cmd
# Run as Administrator
create_scheduled_task.bat
```

This creates a Windows Scheduled Task that:
- ⏰ Automatically resumes tasks at scheduled times
- 🔄 Runs in background (survives reboots)
- 📅 Requires no manual intervention
- 📊 Logs activity to `scheduler_debug.log`

## Step 6: Try the Example (CLI)

```bash
# Run the example script (uses CLI interface)
python example_usage.py
```

This will:
1. Create a "Calculator App" project
2. Create planning, coding, and testing tasks
3. Execute all tasks in sequence
4. Show the results

## 🌐 Web UI Features

### Real-Time Monitoring
- 👁️ Watch Claude's output stream live
- 📊 See task status updates instantly
- 📈 Monitor statistics in real-time

### Smart Orchestration
- 🧠 LM Studio creates optimal prompts
- 🎯 Automatically selects best Claude agents
- ✅ Validates all outputs with AI

### Session Management
- ⏸️ Detects "Session limit reached"
- ⏰ Auto-schedules resumption (e.g., 10pm)
- 🔄 Continues automatically via Windows service

### Project Integration
- 📁 Browse project files
- 👀 Track file modifications
- 🧪 View test results
- 📋 Complete task history

## Common CLI Commands (Still Available)

```bash
# List all projects
python agent7.py list-projects

# List all tasks
python agent7.py list-tasks

# List pending tasks
python agent7.py list-tasks --status pending

# List tasks for a specific project
python agent7.py list-tasks --project 1

# View task details
python agent7.py task-details <task_id>

# Execute a complete workflow (all pending tasks in a project)
python agent7.py execute-workflow <project_id>

# Start web server manually
python web_server.py
```

## Tips

### Use Local LLM for Speed
```bash
python agent7.py execute-task 1 --prefer-local
```

### Use Claude for Quality
```bash
python agent7.py execute-task 1 --no-local-llm
```

### Different Programming Languages
```bash
python agent7.py create-task 1 \
  --type coding \
  --title "Build JavaScript API" \
  --desc "Create Express.js REST API"

python agent7.py execute-task 2 --language javascript
```

## Troubleshooting

### Web UI won't start
- Check if port 5000 is available
- Run: `python web_server.py` to see errors
- Install dependencies: `pip install -r requirements.txt`

### "Local LLM not available" (Red in Web UI)
- Ensure LM Studio is running
- Check that the server is on port 1234
- Try accessing http://localhost:1234/v1/models in your browser
- Go to LM Studio → "Local Server" → "Start Server"

### "Claude CLI not found"
- Install Claude CLI from https://docs.anthropic.com/claude/docs/claude-cli
- Make sure it's in your PATH
- Run `claude configure` to set up credentials
- Test with: `claude --version`

### Tasks not resuming after session limit
- Check scheduler task: `schtasks /Query /TN "Agent7Scheduler"`
- Install if missing: `create_scheduled_task.bat` (as Administrator)
- Check logs: `scheduler_debug.log`

### Database errors
- Check file permissions in the current directory
- Database auto-creates on first run
- Delete `agent7.db` to start fresh (loses history)

### Files not being created by Claude
- Verify project directory is correct
- Check Claude has necessary permissions
- Review output console for errors

## Next Steps

1. Read the full [README.md](README.md) for detailed documentation
2. Explore the code to customize behavior
3. Create your own workflows
4. Integrate with your existing tools

## Real-World Examples

### Example 1: Build a REST API

**Web UI Steps**:
1. Select project: `C:\Projects\MyAPI`
2. Create task:
   - Title: "Create REST API"
   - Description: "Build Express.js REST API with CRUD endpoints for users"
   - Type: Coding
3. Click Execute
4. Watch as:
   - Files are created (`server.js`, `routes/users.js`, etc.)
   - Tests are generated and run
   - Results are validated

### Example 2: Add Feature with Tests

**Task Description**: "Add email verification to user registration with tests"

**What Happens**:
- 🧠 LM Studio determines: use coding + testing agents
- 🤖 Claude creates email verification logic
- 📝 Claude adds tests for verification
- 🧪 Pytest runs automatically
- ✅ LM Studio validates implementation and tests

### Example 3: Session Limit Recovery

**Scenario**: Task takes 30 minutes, Claude has 20-minute limit

**What Happens**:
1. Claude works for 20 minutes
2. System detects: "Session limit reached ∙ resets 10pm"
3. Saves checkpoint with current progress
4. Schedules resumption for 10pm
5. At 10pm: Windows service automatically continues
6. Task completes without any manual intervention

## Pro Tips

### 💡 Tip 1: Be Specific in Descriptions
**Bad**: "Make it better"
**Good**: "Add input validation to prevent SQL injection in the login form"

### 💡 Tip 2: Use Planning Tasks First
For complex features:
1. Create planning task → Execute
2. Review the plan in task details
3. Create coding task based on the plan
4. Create testing task for validation

### 💡 Tip 3: Monitor the Output Console
Watch the real-time output to see:
- What Claude is thinking
- Which files are being created
- Test results as they run
- Validation feedback

### 💡 Tip 4: Let It Run Overnight
For big tasks:
- Start execution before leaving
- Scheduler service handles session limits
- Task completes overnight
- Review results in the morning

## What Makes v2.0 Special

✨ **Autonomous Operation**: Set it and forget it
✨ **Smart Orchestration**: LM Studio ensures quality
✨ **Real File Access**: Claude creates actual code
✨ **Resilient**: Handles session limits automatically
✨ **Monitored**: See everything in real-time
✨ **Validated**: AI checks all work

## Next Steps

1. 🌐 Explore the web UI at `http://localhost:5000`
2. 📖 Read [README.md](README.md) for detailed docs
3. 🏗️ Check [ARCHITECTURE.md](ARCHITECTURE.md) to understand the system
4. 🔧 Review [config.py](config.py) for customization options
5. 🎯 Build something awesome!

Happy coding! 🚀


