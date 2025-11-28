"""
Test file operations with markdown bold syntax.
"""
from file_operations import FileOperations


def test_markdown_bold_format():
    """Test parsing files with **File:** markdown bold format."""
    
    # This is the actual format LM Studio uses
    output = """**File: src/main.py**
```python
import pygame

def main():
    print("Hello, World!")

if __name__ == "__main__":
    main()
```

**File: src/constants.py**
```python
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
```

**File: README.md**
```markdown
# My Project

This is a test project.
```
"""
    
    file_ops = FileOperations()
    blocks = file_ops.extract_file_blocks(output)
    
    print(f"Found {len(blocks)} file blocks:")
    for block in blocks:
        print(f"  - {block['filepath']} ({len(block['content'])} bytes)")
    
    assert len(blocks) >= 3, f"Expected at least 3 blocks, got {len(blocks)}"
    
    # Check filenames were parsed correctly
    filenames = [block['filepath'] for block in blocks]
    assert 'src/main.py' in filenames, "Should find src/main.py"
    assert 'src/constants.py' in filenames, "Should find src/constants.py"
    assert 'README.md' in filenames, "Should find README.md"
    
    # Check content was captured
    main_block = next(b for b in blocks if b['filepath'] == 'src/main.py')
    assert 'import pygame' in main_block['content'], "Should have Python code"
    assert 'def main()' in main_block['content'], "Should have main function"
    
    print("\n✅ All tests passed!")
    print("\nExtracted files:")
    for block in blocks:
        print(f"\nFile: {block['filepath']}")
        print(f"Content preview: {block['content'][:100]}...")


if __name__ == '__main__':
    print("Testing Markdown Bold Format Parsing\n" + "="*50)
    test_markdown_bold_format()

