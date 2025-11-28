#!/usr/bin/env python3
"""
Test script to verify Agent7 setup.
Run this to check if all components are working.
"""
import sys
from database import Database
from claude_client import ClaudeClient
from local_llm_client import LocalLLMClient


def test_database():
    """Test database functionality."""
    print("Testing database...")
    try:
        db = Database(":memory:")  # Use in-memory database for testing
        
        # Test project creation
        project_id = db.create_project("Test Project", "Testing")
        assert project_id is not None, "Failed to create project"
        
        # Test task creation
        task_id = db.create_task(
            project_id, "Test Task", "Testing task", "planning"
        )
        assert task_id is not None, "Failed to create task"
        
        # Test retrieval
        project = db.get_project(project_id)
        assert project is not None, "Failed to retrieve project"
        
        task = db.get_task(task_id)
        assert task is not None, "Failed to retrieve task"
        
        print("✅ Database tests passed")
        return True
    except Exception as e:
        print(f"❌ Database tests failed: {e}")
        return False


def test_local_llm():
    """Test local LLM connectivity."""
    print("\nTesting local LLM...")
    try:
        client = LocalLLMClient("http://localhost:1234/v1")
        
        if client.check_availability():
            print("✅ Local LLM is available")
            
            # Try a simple request
            print("   Testing simple prompt...")
            result = client.send_message(
                "Say 'hello' in one word.",
                max_tokens=10,
                temperature=0.1
            )
            
            if result.get('response'):
                print(f"   Response received: {result['response'][:50]}")
                print("✅ Local LLM communication successful")
                return True
            else:
                print(f"⚠️  Local LLM responded but no content: {result.get('error')}")
                return False
        else:
            print("⚠️  Local LLM not available")
            print("   Make sure LM Studio is running at http://localhost:1234")
            return False
            
    except Exception as e:
        print(f"❌ Local LLM test failed: {e}")
        return False


def test_claude_cli():
    """Test Claude CLI availability."""
    print("\nTesting Claude CLI...")
    try:
        client = ClaudeClient()
        
        # We can't actually test Claude without credentials,
        # but we can check if the command exists
        import subprocess
        try:
            result = subprocess.run(
                ["claude", "--version"],
                capture_output=True,
                timeout=5
            )
            if result.returncode == 0:
                print("✅ Claude CLI is available")
                return True
            else:
                print("⚠️  Claude CLI command exists but may not be configured")
                print("   Run 'claude configure' to set up")
                return False
        except FileNotFoundError:
            print("⚠️  Claude CLI not found")
            print("   Install from: https://docs.anthropic.com/claude/docs/claude-cli")
            return False
            
    except Exception as e:
        print(f"⚠️  Could not test Claude CLI: {e}")
        return False


def main():
    """Run all tests."""
    print("="*60)
    print("Agent7 Setup Test")
    print("="*60)
    
    results = {
        'database': test_database(),
        'local_llm': test_local_llm(),
        'claude_cli': test_claude_cli()
    }
    
    print("\n" + "="*60)
    print("Test Results Summary")
    print("="*60)
    
    for component, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{component:20s}: {status}")
    
    print("="*60)
    
    # Check if at least one AI backend is available
    ai_available = results['local_llm'] or results['claude_cli']
    
    if results['database'] and ai_available:
        print("\n✅ Agent7 is ready to use!")
        print("\nNext steps:")
        print("1. Run: python agent7.py status")
        print("2. Create a project: python agent7.py create-project 'My Project'")
        print("3. See example: python example_usage.py")
        return 0
    else:
        print("\n⚠️  Setup incomplete:")
        if not results['database']:
            print("- Database tests failed (critical)")
        if not ai_available:
            print("- No AI backend available (need Claude CLI or Local LLM)")
            print("  Install Claude CLI or start LM Studio")
        return 1


if __name__ == '__main__':
    sys.exit(main())


