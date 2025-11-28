# Agent7 - Quick Start Guide

Get up and running with Agent7 in 5 minutes!

## Step 1: Installation

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

## Step 3: Verify Setup

```bash
python test_setup.py
```

This will check:
- ✅ Database functionality
- ✅ Local LLM availability
- ✅ Claude CLI availability

## Step 4: First Project

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

## Step 5: Complete Workflow Example

```bash
# Run the example script
python example_usage.py
```

This will:
1. Create a "Calculator App" project
2. Create planning, coding, and testing tasks
3. Execute all tasks in sequence
4. Show the results

## Common Commands

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

### "Local LLM not available"
- Ensure LM Studio is running
- Check that the server is on port 1234
- Try accessing http://localhost:1234/v1/models in your browser

### "Claude CLI not found"
- Install Claude CLI
- Make sure it's in your PATH
- Run `claude configure` to set up credentials

### Database errors
- Check file permissions in the current directory
- Try specifying a different path: `--db /path/to/database.db`

## Next Steps

1. Read the full [README.md](README.md) for detailed documentation
2. Explore the code to customize behavior
3. Create your own workflows
4. Integrate with your existing tools

## Examples of What You Can Do

- **Plan a web application**: Get AI to break down features
- **Generate boilerplate code**: Quick scaffolding for common patterns
- **Create test suites**: Comprehensive testing for your code
- **Code reviews**: Get AI feedback on code quality
- **Documentation**: Generate docs from code
- **Refactoring plans**: Plan complex refactoring tasks

Happy coding! 🚀


