"""
Test JSON format tool parsing
"""
import tempfile
import os
from tool_executor import ToolExecutor
from project_tools import ProjectTools


def test_json_format_parsing():
    """Test parsing JSON format tool calls."""
    print("\n=== Test: JSON Format Tool Parsing ===")
    
    temp_dir = tempfile.mkdtemp()
    
    try:
        executor = ToolExecutor(temp_dir)
        
        # Test JSON format (OpenAI function calling style)
        response_with_json = '''[{"name": "get_project_structure", "arguments": {"max_depth": 1}}]'''
        
        requests = executor.detect_tool_requests(response_with_json)
        print(f"Found {len(requests)} tool request(s)")
        
        assert len(requests) == 1, f"Should find 1 request, found {len(requests)}"
        assert requests[0]['tool'] == 'get_project_structure', "Should be get_project_structure"
        assert requests[0]['pattern'] == 'json', "Should be JSON pattern"
        assert 'args_dict' in requests[0], "Should have args_dict"
        assert requests[0]['args_dict']['max_depth'] == 1, "Should parse max_depth=1"
        
        print("✅ JSON format parsed correctly")
        print(f"   Tool: {requests[0]['tool']}")
        print(f"   Args: {requests[0]['args_dict']}")
        
        # Test multiple JSON calls
        multi_json = '''[{"name": "get_project_structure", "arguments": {"max_depth": 1}}]
[{"name": "read_file", "arguments": {"filepath": "main.py"}}]'''
        
        requests = executor.detect_tool_requests(multi_json)
        print(f"\nFound {len(requests)} request(s) in multi-call")
        
        assert len(requests) == 2, f"Should find 2 requests, found {len(requests)}"
        print("✅ Multiple JSON calls parsed correctly")
        
        # Test execution
        results = executor.parse_and_execute(response_with_json)
        print(f"\nExecuted {len(results)} tool(s)")
        
        assert len(results) == 1, "Should execute 1 tool"
        assert results[0]['success'], "Execution should succeed"
        print("✅ JSON tool execution works")
        
    finally:
        import shutil
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)


def test_mixed_formats():
    """Test parsing mixed TOOL: and JSON formats."""
    print("\n=== Test: Mixed Format Parsing ===")
    
    temp_dir = tempfile.mkdtemp()
    
    try:
        executor = ToolExecutor(temp_dir)
        
        # Mix of JSON and TOOL: formats
        mixed = '''[{"name": "get_project_structure", "arguments": {}}]
        
TOOL: list_files(relative_path=".", extensions=[".py"])'''
        
        requests = executor.detect_tool_requests(mixed)
        print(f"Found {len(requests)} request(s) in mixed format")
        
        # Should find at least 2 (may find more due to natural language detection)
        assert len(requests) >= 2, f"Should find at least 2 requests, found {len(requests)}"
        
        # Check that JSON format is detected
        json_requests = [r for r in requests if r['pattern'] == 'json']
        assert len(json_requests) >= 1, "Should find at least 1 JSON request"
        
        # Check that explicit format is detected
        explicit_requests = [r for r in requests if r['pattern'] == 'explicit']
        assert len(explicit_requests) >= 1, "Should find at least 1 explicit request"
        
        print("✅ Mixed formats parsed correctly")
        print(f"   JSON: {len(json_requests)}, Explicit: {len(explicit_requests)}")
        
    finally:
        import shutil
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)


if __name__ == '__main__':
    print("Testing JSON Tool Format Support")
    print("="*60)
    
    try:
        test_json_format_parsing()
        test_mixed_formats()
        
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

