"""
Test project tools and tool executor.
"""
import os
import tempfile
import shutil
from project_tools import ProjectTools
from tool_executor import ToolExecutor


def create_test_project():
    """Create a temporary test project structure."""
    temp_dir = tempfile.mkdtemp(prefix="agent7_test_")
    
    # Create directory structure
    os.makedirs(os.path.join(temp_dir, "src"))
    os.makedirs(os.path.join(temp_dir, "tests"))
    os.makedirs(os.path.join(temp_dir, "docs"))
    
    # Create test files
    with open(os.path.join(temp_dir, "README.md"), "w") as f:
        f.write("# Test Project\n\nThis is a test project.")
    
    with open(os.path.join(temp_dir, "src", "main.py"), "w") as f:
        f.write("""def main():
    print("Hello, World!")

class MyClass:
    def __init__(self):
        pass

if __name__ == "__main__":
    main()
""")
    
    with open(os.path.join(temp_dir, "src", "utils.py"), "w") as f:
        f.write("""def helper_function():
    return "Helper"

class UtilityClass:
    pass
""")
    
    with open(os.path.join(temp_dir, "tests", "test_main.py"), "w") as f:
        f.write("""import pytest

def test_example():
    assert True
""")
    
    with open(os.path.join(temp_dir, "config.json"), "w") as f:
        f.write('{"version": "1.0"}')
    
    return temp_dir


def test_list_files():
    """Test listing files in directory."""
    print("\n=== Test: list_files ===")
    
    temp_dir = create_test_project()
    tools = ProjectTools(temp_dir)
    
    try:
        # List root directory
        result = tools.list_files(".")
        assert result['success'], "Should succeed"
        assert result['total_files'] > 0, "Should find files"
        print(f"✅ Found {result['total_files']} files, {result['total_directories']} directories")
        
        # List with extension filter
        result = tools.list_files(".", extensions=[".py"])
        py_files = [f for f in result['files'] if f['extension'] == '.py']
        print(f"✅ Found {len(py_files)} Python files with extension filter")
        
        # List subdirectory
        result = tools.list_files("src")
        assert result['success'], "Should succeed"
        print(f"✅ Listed src directory: {result['total_files']} files")
        
    finally:
        shutil.rmtree(temp_dir)


def test_read_file():
    """Test reading file contents."""
    print("\n=== Test: read_file ===")
    
    temp_dir = create_test_project()
    tools = ProjectTools(temp_dir)
    
    try:
        # Read full file
        result = tools.read_file("src/main.py")
        assert result['success'], "Should succeed"
        assert "def main()" in result['content'], "Should contain function"
        print(f"✅ Read file: {result['lines']} lines, {result['size']} bytes")
        
        # Read with line range
        result = tools.read_file("src/main.py", start_line=1, end_line=3)
        assert result['success'], "Should succeed"
        assert result['lines'] == 3, "Should have 3 lines"
        print(f"✅ Read lines 1-3: {result['lines']} lines")
        
        # Non-existent file
        result = tools.read_file("nonexistent.py")
        assert not result['success'], "Should fail"
        print(f"✅ Correctly handled non-existent file")
        
    finally:
        shutil.rmtree(temp_dir)


def test_search_in_files():
    """Test searching for patterns in files."""
    print("\n=== Test: search_in_files ===")
    
    temp_dir = create_test_project()
    tools = ProjectTools(temp_dir)
    
    try:
        # Search for function definition
        result = tools.search_in_files("def main", extensions=[".py"])
        assert result['success'], "Should succeed"
        assert result['total'] > 0, "Should find matches"
        print(f"✅ Found 'def main' in {result['total']} places")
        
        # Search for class
        result = tools.search_in_files("class.*Class", extensions=[".py"])
        assert result['success'], "Should succeed"
        print(f"✅ Found class definitions: {result['total']} matches")
        
        # Case insensitive search
        result = tools.search_in_files("HELLO", case_sensitive=False)
        assert result['success'], "Should succeed"
        print(f"✅ Case-insensitive search: {result['total']} matches")
        
    finally:
        shutil.rmtree(temp_dir)


def test_find_files():
    """Test finding files by name pattern."""
    print("\n=== Test: find_files ===")
    
    temp_dir = create_test_project()
    tools = ProjectTools(temp_dir)
    
    try:
        # Find Python files
        result = tools.find_files("*.py")
        assert result['success'], "Should succeed"
        assert result['total'] > 0, "Should find Python files"
        print(f"✅ Found {result['total']} Python files")
        
        # Find specific file
        result = tools.find_files("main.py")
        assert result['success'], "Should succeed"
        assert result['total'] > 0, "Should find main.py"
        print(f"✅ Found main.py: {result['matches'][0]['path']}")
        
        # Find JSON files
        result = tools.find_files("*.json")
        assert result['success'], "Should succeed"
        print(f"✅ Found {result['total']} JSON files")
        
    finally:
        shutil.rmtree(temp_dir)


def test_find_definitions():
    """Test finding function/class definitions."""
    print("\n=== Test: find_definitions ===")
    
    temp_dir = create_test_project()
    tools = ProjectTools(temp_dir)
    
    try:
        # Find function
        result = tools.find_definitions("main", definition_type="function")
        assert result['success'], "Should succeed"
        assert result['total'] > 0, "Should find main function"
        print(f"✅ Found 'main' function in {result['matches'][0]['file']}")
        
        # Find class
        result = tools.find_definitions("MyClass", definition_type="class")
        assert result['success'], "Should succeed"
        assert result['total'] > 0, "Should find MyClass"
        print(f"✅ Found 'MyClass' class")
        
        # Find any definition
        result = tools.find_definitions("helper_function", definition_type="any")
        assert result['success'], "Should succeed"
        print(f"✅ Found 'helper_function': {result['total']} matches")
        
    finally:
        shutil.rmtree(temp_dir)


def test_get_project_structure():
    """Test getting project structure."""
    print("\n=== Test: get_project_structure ===")
    
    temp_dir = create_test_project()
    tools = ProjectTools(temp_dir)
    
    try:
        result = tools.get_project_structure(max_depth=2)
        assert result['success'], "Should succeed"
        assert result['structure'] is not None, "Should have structure"
        print(f"✅ Got project structure")
        
        # Check structure has directories
        structure = result['structure']
        assert structure['type'] == 'directory', "Root should be directory"
        assert len(structure['children']) > 0, "Should have children"
        print(f"✅ Structure has {len(structure['children'])} top-level items")
        
    finally:
        shutil.rmtree(temp_dir)


def test_tool_executor():
    """Test tool executor parsing and execution."""
    print("\n=== Test: ToolExecutor ===")
    
    temp_dir = create_test_project()
    executor = ToolExecutor(temp_dir)
    
    try:
        # Test explicit TOOL: marker
        text1 = 'TOOL: list_files(path="src", extensions=[".py"])'
        requests = executor.detect_tool_requests(text1)
        assert len(requests) > 0, "Should detect tool request"
        print(f"✅ Detected explicit TOOL: marker")
        
        # Test natural language
        text2 = "I need to use read_file on src/main.py to understand the code"
        requests = executor.detect_tool_requests(text2)
        assert len(requests) > 0, "Should detect natural language request"
        print(f"✅ Detected natural language tool request")
        
        # Test execution
        result = executor.execute_tool("list_files", {"relative_path": "src"})
        assert result['success'], "Tool should execute successfully"
        print(f"✅ Executed list_files tool")
        
        # Test parse and execute
        text3 = 'TOOL: read_file(filepath="README.md")'
        results = executor.parse_and_execute(text3)
        assert len(results) > 0, "Should execute tools"
        assert results[0]['success'], "Should succeed"
        print(f"✅ Parsed and executed tool from text")
        
        # Test formatting
        formatted = executor.format_tool_result(results[0])
        assert len(formatted) > 0, "Should format result"
        assert "README.md" in formatted, "Should contain filename"
        print(f"✅ Formatted tool result")
        
    finally:
        shutil.rmtree(temp_dir)


def test_get_file_info():
    """Test getting file information."""
    print("\n=== Test: get_file_info ===")
    
    temp_dir = create_test_project()
    tools = ProjectTools(temp_dir)
    
    try:
        result = tools.get_file_info("src/main.py")
        assert result['success'], "Should succeed"
        assert result['size'] > 0, "Should have size"
        assert result['lines'] > 0, "Should have lines"
        assert result['extension'] == '.py', "Should be Python file"
        print(f"✅ Got file info: {result['size']} bytes, {result['lines']} lines")
        
    finally:
        shutil.rmtree(temp_dir)


if __name__ == '__main__':
    print("Testing Project Tools and Tool Executor\n" + "="*50)
    
    try:
        test_list_files()
        test_read_file()
        test_search_in_files()
        test_find_files()
        test_find_definitions()
        test_get_project_structure()
        test_get_file_info()
        test_tool_executor()
        
        print("\n" + "="*50)
        print("✅ All tests passed!")
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        raise
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        raise

