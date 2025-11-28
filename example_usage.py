#!/usr/bin/env python3
"""
Example usage script for Agent7.
This demonstrates how to use Agent7 programmatically.
"""
from database import Database
from claude_client import ClaudeClient
from local_llm_client import LocalLLMClient
from task_orchestrator import TaskOrchestrator


def main():
    """Demonstrate Agent7 usage."""
    
    # Initialize database
    print("🚀 Initializing Agent7...")
    db = Database("example.db")
    
    # Initialize AI clients
    # Note: You can use one or both depending on what's available
    claude = None  # ClaudeClient() if Claude CLI is available
    local_llm = LocalLLMClient("http://localhost:1234/v1")
    
    # Check if local LLM is available
    if local_llm.check_availability():
        print("✅ Local LLM is available")
    else:
        print("⚠️  Local LLM not available - make sure LM Studio is running")
        return
    
    # Create orchestrator
    orchestrator = TaskOrchestrator(
        db,
        claude_client=claude,
        local_llm_client=local_llm,
        prefer_local=True
    )
    
    # Create a project
    print("\n📁 Creating project...")
    project_id = db.create_project(
        "Calculator App",
        "A simple calculator application with basic operations"
    )
    print(f"Project created with ID: {project_id}")
    
    # Create planning task
    print("\n📝 Creating planning task...")
    planning_task_id = db.create_task(
        project_id,
        "Plan Calculator Architecture",
        "Design a simple calculator with add, subtract, multiply, divide operations. Include error handling.",
        "planning",
        priority=10
    )
    
    # Create coding task
    print("📝 Creating coding task...")
    coding_task_id = db.create_task(
        project_id,
        "Implement Calculator",
        "Create a Calculator class with methods: add(a, b), subtract(a, b), multiply(a, b), divide(a, b). Include error handling for division by zero.",
        "coding",
        priority=5
    )
    
    # Create testing task
    print("📝 Creating testing task...")
    testing_task_id = db.create_task(
        project_id,
        "Test Calculator",
        """
class Calculator:
    def add(self, a, b):
        return a + b
    
    def subtract(self, a, b):
        return a - b
    
    def multiply(self, a, b):
        return a * b
    
    def divide(self, a, b):
        if b == 0:
            raise ValueError("Cannot divide by zero")
        return a / b
        """,
        "testing",
        priority=1
    )
    
    # Execute workflow
    print("\n⚙️  Executing workflow...")
    results = orchestrator.execute_workflow(project_id, language="python")
    
    print(f"\n✨ Results:")
    print(f"   Total tasks: {results['total']}")
    print(f"   Completed: {results['completed']}")
    print(f"   Failed: {results['failed']}")
    
    # Show task details
    print("\n📊 Task Results:")
    for task_result in results['task_results']:
        task = db.get_task(task_result['task_id'])
        print(f"\n{'='*60}")
        print(f"Task: {task['title']}")
        print(f"Type: {task['task_type']}")
        print(f"Status: {task['status']}")
        
        # Get the latest result
        task_results = db.get_results(task_result['task_id'])
        if task_results:
            latest = task_results[-1]
            print(f"\nResult ({latest['result_type']}):")
            print("-" * 60)
            content = latest['content']
            # Show first 500 characters
            if len(content) > 500:
                print(content[:500] + "\n... (truncated)")
            else:
                print(content)
    
    print("\n" + "="*60)
    print("✅ Example complete!")
    print(f"\nDatabase saved to: example.db")
    print("You can inspect it further using agent7.py commands")


if __name__ == '__main__':
    main()


