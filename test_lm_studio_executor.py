"""
Test LM Studio Executor (requires LM Studio running).
"""
import os
import tempfile
import shutil
from database import Database
from local_llm_client import LocalLLMClient
from lm_studio_executor import LMStudioExecutor


def test_basic_execution():
    """Test basic LM Studio execution."""
    print("\n=== Test: Basic Execution ===")
    
    # Create temp directory for test project
    temp_dir = tempfile.mkdtemp(prefix="agent7_test_")
    temp_db = tempfile.mktemp(suffix=".db")
    
    try:
        # Initialize components
        db = Database(temp_db)
        llm = LocalLLMClient('http://localhost:1234/v1')
        
        # Check if LM Studio is available
        if not llm.check_availability():
            print("⚠️  LM Studio not available at localhost:1234")
            print("   Start LM Studio with a model loaded to run this test")
            return
        
        print("✅ LM Studio is available")
        
        # Create executor
        executor = LMStudioExecutor(llm, db, temp_dir)
        print("✅ Executor created")
        
        # Create a simple task (project_id, title, description, task_type)
        task_id = db.create_task(
            project_id=1,
            title="Test Task",
            description="Create a simple hello.py file",
            task_type="coding"
        )
        print(f"✅ Task created: {task_id}")
        
        # Test system prompt
        system_prompt = executor.create_system_prompt()
        assert len(system_prompt) > 0, "System prompt should not be empty"
        assert "PROJECT EXPLORATION TOOLS" in system_prompt
        assert "FILE CREATION FORMAT" in system_prompt
        print("✅ System prompt generated")
        
        # Test task prompt
        task_prompt = executor.create_task_prompt(
            "Create hello.py",
            "coding"
        )
        assert len(task_prompt) > 0, "Task prompt should not be empty"
        print("✅ Task prompt generated")
        
        # Test simple execution (just 1 iteration to be quick)
        print("\n🤖 Executing task with LM Studio...")
        result = executor.execute_task(
            task_id=task_id,
            task_description="Create a hello.py file that prints 'Hello, World!'",
            task_type='coding',
            max_iterations=1
        )
        
        print(f"\n📊 Result:")
        print(f"  Success: {result.get('success')}")
        print(f"  Status: {result.get('status')}")
        print(f"  Iterations: {result.get('iterations')}")
        print(f"  File Operations: {len(result.get('file_operations', []))}")
        print(f"  Tool Results: {len(result.get('tool_results', []))}")
        
        # Check if response was received
        assert result.get('response'), "Should have response"
        print("✅ Received response from LM Studio")
        
        # Check conversation history
        assert len(executor.conversation_history) > 0, "Should have conversation history"
        print(f"✅ Conversation history: {len(executor.conversation_history)} messages")
        
        print("\n✅ All tests passed!")
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        raise
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        raise
    finally:
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)
        if os.path.exists(temp_db):
            os.remove(temp_db)


def test_conversation_history():
    """Test conversation history building."""
    print("\n=== Test: Conversation History ===")
    
    temp_dir = tempfile.mkdtemp(prefix="agent7_test_")
    temp_db = tempfile.mktemp(suffix=".db")
    
    try:
        db = Database(temp_db)
        llm = LocalLLMClient('http://localhost:1234/v1')
        
        if not llm.check_availability():
            print("⚠️  LM Studio not available - skipping test")
            return
        
        executor = LMStudioExecutor(llm, db, temp_dir)
        
        # Check initial state
        assert executor.conversation_history == [], "Should start empty"
        print("✅ Initial history is empty")
        
        # Simulate adding to history
        executor.conversation_history.append({
            'role': 'assistant',
            'content': 'Test message'
        })
        
        assert len(executor.conversation_history) == 1
        print("✅ Can add to conversation history")
        
        print("\n✅ Conversation history test passed!")
        
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
        if os.path.exists(temp_db):
            os.remove(temp_db)


if __name__ == '__main__':
    print("Testing LM Studio Executor")
    print("="*50)
    print("\nRequirements:")
    print("- LM Studio running at localhost:1234")
    print("- Model loaded and API server enabled")
    print()
    
    try:
        test_conversation_history()
        test_basic_execution()
        
        print("\n" + "="*50)
        print("✅ All tests completed!")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Tests failed with error: {e}")
        import traceback
        traceback.print_exc()

