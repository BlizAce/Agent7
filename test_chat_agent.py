"""
Test Chat Agent
"""
import tempfile
import os
from database import Database
from local_llm_client import LocalLLMClient
from chat_agent import ChatAgent


def test_chat_agent_initialization():
    """Test basic chat agent initialization."""
    print("\n=== Test: Chat Agent Initialization ===")
    
    temp_db = tempfile.mktemp(suffix=".db")
    
    try:
        db = Database(temp_db)
        llm = LocalLLMClient('http://localhost:1234/v1')
        agent = ChatAgent(llm, db)
        
        print("✅ Chat agent initialized")
        assert agent.conversation_history == [], "Should start with empty history"
        print("✅ Conversation history is empty")
        
        # Test system prompt
        prompt = agent.get_system_prompt()
        assert 'CREATE_TASK' in prompt, "Should include CREATE_TASK command"
        assert 'EXECUTE_TASK' in prompt, "Should include EXECUTE_TASK command"
        print("✅ System prompt includes command documentation")
        
    finally:
        if os.path.exists(temp_db):
            os.remove(temp_db)


def test_action_parsing():
    """Test parsing actions from responses."""
    print("\n=== Test: Action Parsing ===")
    
    temp_db = tempfile.mktemp(suffix=".db")
    
    try:
        db = Database(temp_db)
        llm = LocalLLMClient('http://localhost:1234/v1')
        agent = ChatAgent(llm, db)
        
        # Test response with CREATE_TASK action
        response = """I'll create that task for you!

CREATE_TASK:
```json
{
    "action": "create_task",
    "title": "Test Task",
    "type": "coding",
    "description": "A test task"
}
```

Task created successfully!"""
        
        actions = agent.parse_actions(response)
        print(f"Found {len(actions)} action(s)")
        
        assert len(actions) > 0, "Should find at least one action"
        assert actions[0]['action'] == 'create_task', "Should be create_task action"
        assert actions[0]['title'] == 'Test Task', "Should have correct title"
        print("✅ CREATE_TASK action parsed correctly")
        
        # Test response with multiple actions
        multi_response = """I'll create a planning task first:

```json
{
    "action": "create_task",
    "title": "Plan Project",
    "type": "planning",
    "description": "Create project plan"
}
```

And then a coding task:

```json
{
    "action": "create_task",
    "title": "Implement Feature",
    "type": "coding",
    "description": "Code the feature"
}
```
"""
        
        actions = agent.parse_actions(multi_response)
        print(f"Found {len(actions)} action(s) in multi-action response")
        assert len(actions) == 2, f"Should find 2 actions, found {len(actions)}"
        print("✅ Multiple actions parsed correctly")
        
    finally:
        if os.path.exists(temp_db):
            os.remove(temp_db)


def test_clean_response():
    """Test cleaning responses."""
    print("\n=== Test: Clean Response ===")
    
    temp_db = tempfile.mktemp(suffix=".db")
    
    try:
        db = Database(temp_db)
        llm = LocalLLMClient('http://localhost:1234/v1')
        agent = ChatAgent(llm, db)
        
        response_with_action = """I'll create that for you!

```json
{
    "action": "create_task",
    "title": "Test"
}
```

Task created!"""
        
        cleaned = agent.clean_response(response_with_action)
        print(f"Cleaned: {cleaned}")
        
        assert '```json' not in cleaned, "Should remove JSON blocks"
        assert '"action"' not in cleaned, "Should remove action content"
        assert "I'll create that for you!" in cleaned, "Should keep conversation text"
        print("✅ Response cleaned correctly")
        
    finally:
        if os.path.exists(temp_db):
            os.remove(temp_db)


def test_conversation_history():
    """Test conversation history management."""
    print("\n=== Test: Conversation History ===")
    
    temp_db = tempfile.mktemp(suffix=".db")
    
    try:
        db = Database(temp_db)
        llm = LocalLLMClient('http://localhost:1234/v1')
        agent = ChatAgent(llm, db)
        
        # Initial state
        assert len(agent.conversation_history) == 0
        
        # Reset
        agent.reset_conversation()
        assert len(agent.conversation_history) == 0
        print("✅ Conversation reset works")
        
    finally:
        if os.path.exists(temp_db):
            os.remove(temp_db)


def test_fallback_parsing():
    """Test fallback parsing when JSON is missing."""
    print("\n=== Test: Fallback Action Parsing ===")
    
    temp_db = tempfile.mktemp(suffix=".db")
    
    try:
        db = Database(temp_db)
        llm = LocalLLMClient('http://localhost:1234/v1')
        agent = ChatAgent(llm, db)
        
        # Test response without JSON but with CREATE_TASK keyword
        response_without_json = """It looks like you're encountering a NameError because the color constant BLACK is not defined.
Let's create a task to define these constants.

CREATE_TASK:

Should I execute this task for you?"""
        
        actions = agent.parse_actions(response_without_json)
        print(f"Found {len(actions)} action(s) from fallback parsing")
        
        assert len(actions) > 0, "Should extract action even without JSON"
        assert actions[0]['action'] == 'create_task', "Should be create_task"
        print(f"✅ Extracted task: {actions[0]['title']}")
        
        # Test with color constants mention
        response_color = """The BLACK constant is not defined. Let's define color constants."""
        actions = agent.parse_actions(response_color)
        
        if len(actions) > 0:
            print(f"✅ Detected color constants task: {actions[0].get('title')}")
        
    finally:
        if os.path.exists(temp_db):
            os.remove(temp_db)


if __name__ == '__main__':
    print("Testing Chat Agent")
    print("="*60)
    
    try:
        test_chat_agent_initialization()
        test_action_parsing()
        test_clean_response()
        test_conversation_history()
        test_fallback_parsing()
        
        print("\n" + "="*60)
        print("✅ All tests passed!")
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)

