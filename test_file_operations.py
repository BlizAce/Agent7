"""
Test file operations module.
"""
from file_operations import FileOperations


def test_parse_file_blocks():
    """Test parsing of file blocks from Claude's output."""
    
    # Test case 1: Explicit file marker with code block
    output1 = """Sure! Here's the implementation:

File: example.py
```python
def hello():
    print("Hello, World!")

if __name__ == "__main__":
    hello()
```

This should work perfectly!"""
    
    file_ops = FileOperations()
    blocks = file_ops.extract_file_blocks(output1)
    
    assert len(blocks) > 0, "Should extract at least one file block"
    assert blocks[0]['filepath'] == 'example.py', f"Expected 'example.py', got {blocks[0]['filepath']}"
    assert 'def hello()' in blocks[0]['content'], "Should contain function definition"
    print("✅ Test 1 passed: Explicit file marker")
    
    # Test case 2: Create file marker
    output2 = """I'll create the main file for you:

Create file: main.py
```python
print("Starting application...")
```"""
    
    blocks = file_ops.extract_file_blocks(output2)
    assert len(blocks) > 0, "Should extract file block"
    assert 'main.py' in blocks[0]['filepath'], "Should extract main.py"
    print("✅ Test 2 passed: Create file marker")
    
    # Test case 3: Multiple files
    output3 = """Here's the structure:

File: app.py
```python
def run():
    pass
```

And the config:

File: config.json
```json
{
    "version": "1.0"
}
```"""
    
    blocks = file_ops.extract_file_blocks(output3)
    assert len(blocks) >= 2, f"Should extract 2 file blocks, got {len(blocks)}"
    print(f"✅ Test 3 passed: Multiple files ({len(blocks)} extracted)")
    
    # Test case 4: HTML file with proper marker
    output4 = """File: index.html
```html
<!DOCTYPE html>
<html>
<head><title>Test</title></head>
<body><h1>Hello</h1></body>
</html>
```"""
    
    blocks = file_ops.extract_file_blocks(output4)
    assert len(blocks) > 0, "Should extract HTML file"
    assert 'index.html' in blocks[0]['filepath'], "Should extract index.html"
    print("✅ Test 4 passed: HTML file")
    
    print("\n🎉 All file parsing tests passed!")
    
    # Show what was extracted
    print("\n📝 Sample extraction from Test 1:")
    print(f"   Filepath: {blocks[0]['filepath']}")
    print(f"   Content length: {len(blocks[0]['content'])} chars")
    print(f"   Operation: {blocks[0]['operation']}")


def test_dry_run():
    """Test dry run mode (doesn't actually create files)."""
    
    output = """File: test.txt
```
Hello, this is a test file!
```"""
    
    file_ops = FileOperations()
    operations = file_ops.parse_and_execute(
        output,
        project_directory='.',
        dry_run=True
    )
    
    assert len(operations) > 0, "Should perform operations"
    assert operations[0]['dry_run'] == True, "Should be marked as dry run"
    assert operations[0]['success'] == True, "Dry run should succeed"
    
    print("✅ Dry run test passed!")
    
    summary = file_ops.format_operations_summary(operations)
    print(f"\n{summary}")


if __name__ == '__main__':
    print("Testing File Operations Module\n" + "="*50)
    test_parse_file_blocks()
    print()
    test_dry_run()
    print("\n" + "="*50)
    print("✅ All tests passed!")

