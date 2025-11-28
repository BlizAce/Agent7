#!/usr/bin/env python3
"""
Agent7 - AI Task Management System
Uses Claude CLI and/or local LLM for planning, coding, and testing tasks.
"""
import argparse
import sys
from typing import Optional
from database import Database
from claude_client import ClaudeClient
from local_llm_client import LocalLLMClient
from task_orchestrator import TaskOrchestrator


def create_project(db: Database, name: str, description: str):
    """Create a new project."""
    try:
        project_id = db.create_project(name, description)
        print(f"✅ Project created: {name} (ID: {project_id})")
        return project_id
    except Exception as e:
        print(f"❌ Error creating project: {e}")
        return None


def list_projects(db: Database):
    """List all projects."""
    projects = db.list_projects()
    
    if not projects:
        print("No projects found. Create one with: agent7.py create-project")
        return
    
    print("\n📋 Projects:")
    print("-" * 80)
    for p in projects:
        print(f"ID: {p['id']:3d} | {p['name']:30s} | Created: {p['created_at']}")
        if p['description']:
            print(f"      Description: {p['description']}")
    print("-" * 80)


def create_task(db: Database, project_id: int, title: str, 
                description: str, task_type: str, priority: int = 0):
    """Create a new task."""
    try:
        task_id = db.create_task(project_id, title, description, task_type, priority)
        print(f"✅ Task created: {title} (ID: {task_id})")
        return task_id
    except Exception as e:
        print(f"❌ Error creating task: {e}")
        return None


def list_tasks(db: Database, project_id: Optional[int] = None, 
               status: Optional[str] = None):
    """List tasks."""
    tasks = db.list_tasks(project_id, status)
    
    if not tasks:
        print("No tasks found.")
        return
    
    print("\n📝 Tasks:")
    print("-" * 80)
    for t in tasks:
        status_emoji = {
            'pending': '⏳',
            'in_progress': '🔄',
            'completed': '✅',
            'failed': '❌'
        }.get(t['status'], '❓')
        
        print(f"{status_emoji} ID: {t['id']:3d} | [{t['task_type']:8s}] {t['title']:30s}")
        print(f"   Status: {t['status']:12s} | Priority: {t['priority']} | Project: {t['project_id']}")
        if t['description'] and len(t['description']) < 100:
            print(f"   {t['description']}")
    print("-" * 80)


def show_task_details(db: Database, task_id: int):
    """Show detailed information about a task."""
    task = db.get_task(task_id)
    if not task:
        print(f"❌ Task {task_id} not found")
        return
    
    print("\n" + "=" * 80)
    print(f"Task ID: {task['id']}")
    print(f"Title: {task['title']}")
    print(f"Type: {task['task_type']}")
    print(f"Status: {task['status']}")
    print(f"Priority: {task['priority']}")
    print(f"Project ID: {task['project_id']}")
    print(f"Created: {task['created_at']}")
    print(f"Updated: {task['updated_at']}")
    
    if task['description']:
        print(f"\nDescription:\n{task['description']}")
    
    # Show results
    results = db.get_results(task_id)
    if results:
        print(f"\n📊 Results ({len(results)}):")
        print("-" * 80)
        for r in results:
            print(f"\n[{r['result_type'].upper()}] - {r['created_at']}")
            print(r['content'][:500] + ("..." if len(r['content']) > 500 else ""))
    
    # Show conversations
    conversations = db.get_conversations(task_id)
    if conversations:
        print(f"\n💬 Conversations ({len(conversations)}):")
        print("-" * 80)
        for c in conversations:
            print(f"\n[{c['model_type']}] - {c['created_at']}")
            print(f"Prompt: {c['prompt'][:200]}...")
            if c['response']:
                print(f"Response: {c['response'][:200]}...")
    
    print("=" * 80)


def execute_task_cmd(orchestrator: TaskOrchestrator, task_id: int, language: str):
    """Execute a single task."""
    success = orchestrator.execute_task(task_id, language)
    sys.exit(0 if success else 1)


def execute_workflow_cmd(orchestrator: TaskOrchestrator, project_id: int, language: str):
    """Execute a workflow for a project."""
    results = orchestrator.execute_workflow(project_id, language)
    sys.exit(0 if results['failed'] == 0 else 1)


def check_status(db: Database, claude_client: Optional[ClaudeClient],
                 local_llm_client: Optional[LocalLLMClient]):
    """Check system status."""
    print("\n🔍 Agent7 System Status")
    print("=" * 80)
    
    # Database
    projects = db.list_projects()
    tasks = db.list_tasks()
    print(f"📊 Database: OK")
    print(f"   Projects: {len(projects)}")
    print(f"   Tasks: {len(tasks)}")
    
    # Claude CLI
    if claude_client:
        print(f"🤖 Claude CLI: Configured")
    else:
        print(f"🤖 Claude CLI: Not configured")
    
    # Local LLM
    if local_llm_client:
        if local_llm_client.check_availability():
            print(f"💻 Local LLM: Available at {local_llm_client.base_url}")
        else:
            print(f"⚠️  Local LLM: Configured but not available at {local_llm_client.base_url}")
            print(f"   Make sure LM Studio is running")
    else:
        print(f"💻 Local LLM: Not configured")
    
    print("=" * 80)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Agent7 - AI Task Management System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create a project
  python agent7.py create-project "My App" "A web application"
  
  # Create tasks
  python agent7.py create-task 1 --type planning --title "Plan architecture" --desc "Design system architecture"
  python agent7.py create-task 1 --type coding --title "Build API" --desc "Create REST API endpoints"
  python agent7.py create-task 1 --type testing --title "Test API" --desc "Write tests for API"
  
  # Execute tasks
  python agent7.py execute-task 1
  python agent7.py execute-workflow 1
  
  # View information
  python agent7.py list-projects
  python agent7.py list-tasks
  python agent7.py task-details 1
  python agent7.py status
        """
    )
    
    parser.add_argument('command', help='Command to execute')
    parser.add_argument('args', nargs='*', help='Command arguments')
    
    # Common options
    parser.add_argument('--db', default='agent7.db', help='Database file path')
    parser.add_argument('--claude-cli', default='claude', help='Claude CLI command')
    parser.add_argument('--local-llm-url', default='http://localhost:1234/v1',
                       help='Local LLM API URL')
    parser.add_argument('--prefer-local', action='store_true',
                       help='Prefer local LLM over Claude')
    parser.add_argument('--no-claude', action='store_true',
                       help='Disable Claude CLI')
    parser.add_argument('--no-local-llm', action='store_true',
                       help='Disable local LLM')
    
    # Task execution options
    parser.add_argument('--language', default='python', help='Programming language')
    parser.add_argument('--type', choices=['planning', 'coding', 'testing'],
                       help='Task type')
    parser.add_argument('--title', help='Task title')
    parser.add_argument('--desc', '--description', dest='description', help='Task description')
    parser.add_argument('--priority', type=int, default=0, help='Task priority')
    parser.add_argument('--status', choices=['pending', 'in_progress', 'completed', 'failed'],
                       help='Filter by status')
    parser.add_argument('--project', type=int, help='Project ID filter')
    
    args = parser.parse_args()
    
    # Initialize database
    db = Database(args.db)
    
    # Initialize clients
    claude_client = None if args.no_claude else ClaudeClient(args.claude_cli)
    local_llm_client = None if args.no_local_llm else LocalLLMClient(args.local_llm_url)
    
    # Initialize orchestrator
    orchestrator = TaskOrchestrator(
        db,
        claude_client,
        local_llm_client,
        args.prefer_local
    )
    
    # Execute command
    cmd = args.command.lower()
    
    if cmd == 'create-project':
        if len(args.args) < 1:
            print("Usage: create-project <name> [description]")
            sys.exit(1)
        name = args.args[0]
        description = args.args[1] if len(args.args) > 1 else ""
        create_project(db, name, description)
    
    elif cmd == 'list-projects':
        list_projects(db)
    
    elif cmd == 'create-task':
        if len(args.args) < 1 or not args.type or not args.title:
            print("Usage: create-task <project_id> --type <type> --title <title> --desc <description>")
            sys.exit(1)
        project_id = int(args.args[0])
        create_task(db, project_id, args.title, args.description or "", args.type, args.priority)
    
    elif cmd == 'list-tasks':
        list_tasks(db, args.project, args.status)
    
    elif cmd == 'task-details':
        if len(args.args) < 1:
            print("Usage: task-details <task_id>")
            sys.exit(1)
        task_id = int(args.args[0])
        show_task_details(db, task_id)
    
    elif cmd == 'execute-task':
        if len(args.args) < 1:
            print("Usage: execute-task <task_id>")
            sys.exit(1)
        task_id = int(args.args[0])
        execute_task_cmd(orchestrator, task_id, args.language)
    
    elif cmd == 'execute-workflow':
        if len(args.args) < 1:
            print("Usage: execute-workflow <project_id>")
            sys.exit(1)
        project_id = int(args.args[0])
        execute_workflow_cmd(orchestrator, project_id, args.language)
    
    elif cmd == 'status':
        check_status(db, claude_client, local_llm_client)
    
    else:
        print(f"Unknown command: {cmd}")
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()


