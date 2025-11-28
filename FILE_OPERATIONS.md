# File Operations System

## Overview

Agent7's **File Operations** system automatically parses Claude's output and creates/modifies files in your project. This solves the critical problem where Claude describes code but doesn't actually write files.

## The Problem (Solved!)

**Before File Operations**:
- Claude would describe code in its response
- LM Studio would validate and see "No files created"
- Task would fail even though Claude provided correct code

**After File Operations**:
- Claude formats code in structured blocks
- Agent7 automatically parses and extracts files
- Files are written to project directory
- LM Studio validates actual files exist
- Tasks complete successfully! ✅

## How It Works

### 1. Prompt Generation

LM Studio tells Claude to use this specific format:

```
File: filename.ext
```language
code content
```
```

### 2. Claude Responds

Claude describes the solution and formats file blocks:

```
I'll create a Pong game for you!

File: pong.py
```python
import pygame

# Game code here
```

File: requirements.txt
```
pygame==2.5.0
```
```

### 3. Automatic Parsing

Agent7's `FileOperations` class:

```python
from file_operations import FileOperations

file_ops = FileOperations(db)
operations = file_ops.parse_and_execute(
    claude_output=response['response'],
    project_directory="/path/to/project",
    task_id=1
)
```

### 4. Files Created

Agent7 automatically:
- Extracts `pong.py` and `requirements.txt`
- Creates any necessary directories
- Writes files to project
- Tracks in database
- Reports success

## Supported File Formats

The parser recognizes multiple patterns:

### Pattern 1: Explicit File Marker
```
File: example.py
```python
code here
```
```

### Pattern 2: Create File Marker
```
Create file: config.json
```json
{"version": "1.0"}
```
```

### Pattern 3: Modify File Marker
```
Modify file: app.py
```python
updated code
```
```

### Pattern 4: File with Language Tag
```
Create `index.html`:
```html
<!DOCTYPE html>
<html>...
```
```

## File Operations API

### parse_and_execute()

Main method that does everything:

```python
operations = file_ops.parse_and_execute(
    claude_output=text,      # Claude's response
    project_directory=path,  # Target directory
    task_id=123,            # For tracking (optional)
    dry_run=False           # Test without creating files
)
```

**Returns**: List of operations performed

```python
[
    {
        'operation': 'create',
        'filepath': 'pong.py',
        'success': True,
        'bytes_written': 1523
    },
    ...
]
```

### extract_file_blocks()

Parse Claude's output without creating files:

```python
blocks = file_ops.extract_file_blocks(claude_output)
# Returns: [{'filepath': 'file.py', 'content': '...', 'operation': 'create'}, ...]
```

### create_file(), modify_file(), delete_file()

Individual file operations:

```python
result = file_ops.create_file(
    filepath='app.py',
    content='print("Hello")',
    project_directory='/project',
    task_id=1
)
```

### format_operations_summary()

Get human-readable summary:

```python
summary = file_ops.format_operations_summary(operations)
print(summary)
```

Output:
```
📝 File Operations: 2/2 successful

Created/Modified:
  ✅ pong.py (1523 bytes)
  ✅ requirements.txt (15 bytes)
```

## Integration with Web UI

File operations are integrated into the web server:

```python
# In web_server.py

# After Claude responds
file_operations = state['file_ops'].parse_and_execute(
    result.get('response', ''),
    project_dir,
    task_id=task_id
)

# Show results in UI
if file_operations:
    ops_summary = state['file_ops'].format_operations_summary(file_operations)
    socketio.emit('output', {'data': ops_summary + "\n"})
    
    # Update file list
    files_modified = [op['filepath'] for op in file_operations if op['success']]
```

## Database Tracking

Every file operation is tracked:

```sql
CREATE TABLE file_modifications (
    id INTEGER PRIMARY KEY,
    task_id INTEGER,
    filepath TEXT,
    action TEXT,  -- 'created', 'modified', 'deleted'
    detected_at TIMESTAMP
);
```

Query file history:

```python
db = Database('agent7.db')
files = db.execute("SELECT * FROM file_modifications WHERE task_id = ?", (task_id,))
```

## Testing

Run the test suite:

```cmd
python test_file_operations.py
```

Tests include:
- ✅ Explicit file marker parsing
- ✅ Create file marker parsing
- ✅ Multiple files in one response
- ✅ HTML/CSS/JS files
- ✅ Dry run mode
- ✅ Error handling

## Example Workflow

### Task: "Create a Pong game"

**Step 1**: LM Studio generates prompt:
```
Create a working Pong game with Pygame.

Format your files like this:
File: filename.py
```python
code
```
```

**Step 2**: Claude responds:
```
I'll create a complete Pong game!

File: pong.py
```python
import pygame
import sys

# Game initialization
pygame.init()
screen = pygame.display.set_mode((800, 600))

# [rest of code...]
```

File: requirements.txt
```
pygame==2.5.0
```
```

**Step 3**: Agent7 parses:
- Found: `pong.py` (1234 bytes)
- Found: `requirements.txt` (15 bytes)

**Step 4**: Files created:
```
C:\Projects\Pong\
  ├── pong.py         ✅ Created
  └── requirements.txt ✅ Created
```

**Step 5**: LM Studio validates:
- ✅ Files exist
- ✅ Code looks correct
- ✅ Dependencies listed
- Status: COMPLETED

## Benefits

✅ **Automatic** - No manual file creation needed  
✅ **Reliable** - Consistent parsing across all responses  
✅ **Tracked** - Every change logged in database  
✅ **Safe** - Creates backups for modifications  
✅ **Fast** - Immediate file creation after Claude responds  
✅ **Smart** - Handles multiple files, nested directories  
✅ **Tested** - Comprehensive test suite included  

## Error Handling

The system handles errors gracefully:

```python
operations = [
    {
        'operation': 'create',
        'filepath': 'test.py',
        'success': False,
        'error': 'Permission denied'
    }
]
```

Errors are:
- Logged to database
- Shown in Web UI
- Returned in operation results
- Don't crash the system

## Advanced Features

### Backup Files

When modifying files, backups are created:

```python
file_ops.modify_file('app.py', new_content, project_dir)
# Creates: app.py.bak with old content
```

### Dry Run Mode

Test parsing without creating files:

```python
operations = file_ops.parse_and_execute(
    output,
    project_dir,
    dry_run=True  # ← No files actually created
)
```

### Custom Patterns

Extend the parser for custom formats:

```python
# Add to FileOperations.extract_file_blocks()
pattern5 = r'Your custom regex pattern'
matches5 = re.findall(pattern5, text, re.DOTALL)
```

## Troubleshooting

### "No files detected"

**Problem**: Claude responded but no files were parsed

**Solution**: Check Claude's output format. Should be:
```
File: name.ext
```language
content
```
```

### "Permission denied"

**Problem**: Can't write to project directory

**Solution**: Check directory permissions or run as Administrator

### "Files created but validation fails"

**Problem**: Files exist but LM Studio says task incomplete

**Solution**: Check validation criteria - may need code fixes, not file creation

## Configuration

No configuration needed! The system works out of the box.

Optional settings in `config.py`:

```python
# Maximum file size to parse (in bytes)
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

# File extensions to track
TRACKED_EXTENSIONS = ['.py', '.js', '.html', '.css', '.json', '.txt', '.md']
```

## Future Enhancements

Potential improvements:

- 🔄 Diff view for modifications
- 📊 File change analytics
- 🔍 Code quality checks before writing
- 🎯 Selective file application (user approval)
- 📝 Git integration for automatic commits
- 🔐 Permission validation
- 📦 Archive old versions

---

**Version**: 2.1.0  
**Status**: ✅ Production Ready  
**Last Updated**: November 28, 2025

