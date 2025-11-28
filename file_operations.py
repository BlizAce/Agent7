"""
File operations module - Parses Claude's output and creates/modifies files.
"""
import os
import re
from typing import List, Dict, Any, Optional
from database import Database


class FileOperations:
    """
    Handles file creation, modification, and deletion based on Claude's output.
    Parses code blocks and file suggestions from Claude's responses.
    """
    
    def __init__(self, db: Optional[Database] = None):
        """
        Initialize file operations handler.
        
        Args:
            db: Optional database for tracking changes
        """
        self.db = db
    
    def parse_and_execute(
        self, 
        claude_output: str, 
        project_directory: str,
        task_id: Optional[int] = None,
        dry_run: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Parse Claude's output and execute file operations.
        
        Args:
            claude_output: Output from Claude
            project_directory: Target directory for files
            task_id: Optional task ID for tracking
            dry_run: If True, don't actually create files
            
        Returns:
            List of operations performed
        """
        operations = []
        
        # Parse file operations from Claude's output
        file_blocks = self.extract_file_blocks(claude_output)
        
        for file_block in file_blocks:
            filepath = file_block['filepath']
            content = file_block['content']
            operation = file_block['operation']  # create, modify, delete
            
            full_path = os.path.join(project_directory, filepath)
            
            if dry_run:
                operations.append({
                    'operation': operation,
                    'filepath': filepath,
                    'success': True,
                    'dry_run': True
                })
                continue
            
            try:
                if operation == 'create' or operation == 'modify':
                    # Check if file already exists
                    file_existed = os.path.exists(full_path)
                    action_taken = 'modified' if file_existed else 'created'
                    
                    # Create directories if needed
                    dir_path = os.path.dirname(full_path)
                    if dir_path:
                        os.makedirs(dir_path, exist_ok=True)
                    
                    # Write file (overwrites if exists)
                    with open(full_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    
                    # Track in database
                    if self.db and task_id:
                        self.db.save_file_modification(task_id, filepath, action_taken)
                    
                    operations.append({
                        'operation': operation,
                        'filepath': filepath,
                        'success': True,
                        'action': action_taken,
                        'bytes_written': len(content),
                        'existed': file_existed
                    })
                
                elif operation == 'delete':
                    if os.path.exists(full_path):
                        os.remove(full_path)
                        
                        if self.db and task_id:
                            self.db.save_file_modification(task_id, filepath, 'deleted')
                        
                        operations.append({
                            'operation': 'delete',
                            'filepath': filepath,
                            'success': True
                        })
                
            except Exception as e:
                operations.append({
                    'operation': operation,
                    'filepath': filepath,
                    'success': False,
                    'error': str(e)
                })
        
        return operations
    
    def extract_file_blocks(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract file blocks from Claude's output.
        
        Looks for patterns like:
        - File: filename.py
        - Create file: filename.py
        - ```python (with filename in comment)
        - Explicit file creation blocks
        
        Args:
            text: Claude's output text
            
        Returns:
            List of file blocks with filepath, content, and operation
        """
        file_blocks = []
        
        # Pattern 1: Explicit file markers with code blocks
        # "File: example.py" or "**File: example.py**" followed by code block
        # Handles markdown bold/italic syntax
        pattern1 = r'\*{0,2}(?:File|Create file|Modify file):\s*([^\n*]+?\.[\w]+)\*{0,2}\s*\n```(?:\w+)?\n(.*?)```'
        matches1 = re.findall(pattern1, text, re.DOTALL | re.IGNORECASE)
        
        for filepath, content in matches1:
            filepath = filepath.strip().strip('`').strip('"').strip("'").strip('*')
            file_blocks.append({
                'filepath': filepath,
                'content': content.strip(),
                'operation': 'create'
            })
        
        # Pattern 2: Code blocks with filename in first comment
        # ```python
        # filename.py
        pattern2 = r'```(?:\w+)?\n#\s*([^\n]+?\.[\w]+)\n(.*?)```'
        matches2 = re.findall(pattern2, text, re.DOTALL)
        
        for filepath, content in matches2:
            filepath = filepath.strip()
            # Check if this isn't already captured
            if not any(fb['filepath'] == filepath for fb in file_blocks):
                file_blocks.append({
                    'filepath': filepath,
                    'content': content.strip(),
                    'operation': 'create'
                })
        
        # Pattern 3: Explicit structure like:
        # Create `main.py`:
        # ```python
        # code
        # ```
        pattern3 = r'(?:Create|Update|Modify)\s+[`"\']([^\n`"\']+?\.[\w]+)[`"\']:\s*\n```(?:\w+)?\n(.*?)```'
        matches3 = re.findall(pattern3, text, re.DOTALL | re.IGNORECASE)
        
        for filepath, content in matches3:
            filepath = filepath.strip()
            if not any(fb['filepath'] == filepath for fb in file_blocks):
                file_blocks.append({
                    'filepath': filepath,
                    'content': content.strip(),
                    'operation': 'create'
                })
        
        # Pattern 4: HTML/CSS/JS files with explicit markers (with markdown support)
        pattern4 = r'\*{0,2}(?:File|Create):\s*([^\n*]+?\.(?:html|css|js|json|txt|md))\*{0,2}\s*\n```(?:\w+)?\n(.*?)```'
        matches4 = re.findall(pattern4, text, re.DOTALL | re.IGNORECASE)
        
        for filepath, content in matches4:
            filepath = filepath.strip().strip('`').strip('"').strip("'").strip('*')
            if not any(fb['filepath'] == filepath for fb in file_blocks):
                file_blocks.append({
                    'filepath': filepath,
                    'content': content.strip(),
                    'operation': 'create'
                })
        
        return file_blocks
    
    def create_file(
        self, 
        filepath: str, 
        content: str, 
        project_directory: str,
        task_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Create a single file.
        
        Args:
            filepath: Relative file path
            content: File content
            project_directory: Project directory
            task_id: Optional task ID for tracking
            
        Returns:
            Result dict
        """
        full_path = os.path.join(project_directory, filepath)
        
        try:
            # Create directories
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            # Write file
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Track in database
            if self.db and task_id:
                self.db.save_file_modification(task_id, filepath, 'created')
            
            return {
                'success': True,
                'filepath': filepath,
                'bytes_written': len(content)
            }
        except Exception as e:
            return {
                'success': False,
                'filepath': filepath,
                'error': str(e)
            }
    
    def modify_file(
        self, 
        filepath: str, 
        content: str, 
        project_directory: str,
        task_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Modify an existing file.
        
        Args:
            filepath: Relative file path
            content: New file content
            project_directory: Project directory
            task_id: Optional task ID for tracking
            
        Returns:
            Result dict
        """
        full_path = os.path.join(project_directory, filepath)
        
        try:
            # Backup existing file
            if os.path.exists(full_path):
                backup_path = full_path + '.bak'
                with open(full_path, 'r', encoding='utf-8') as f:
                    backup_content = f.read()
                with open(backup_path, 'w', encoding='utf-8') as f:
                    f.write(backup_content)
            
            # Write new content
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Track in database
            if self.db and task_id:
                self.db.save_file_modification(task_id, filepath, 'modified')
            
            return {
                'success': True,
                'filepath': filepath,
                'bytes_written': len(content),
                'backed_up': True
            }
        except Exception as e:
            return {
                'success': False,
                'filepath': filepath,
                'error': str(e)
            }
    
    def delete_file(
        self, 
        filepath: str, 
        project_directory: str,
        task_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Delete a file.
        
        Args:
            filepath: Relative file path
            project_directory: Project directory
            task_id: Optional task ID for tracking
            
        Returns:
            Result dict
        """
        full_path = os.path.join(project_directory, filepath)
        
        try:
            if os.path.exists(full_path):
                os.remove(full_path)
                
                # Track in database
                if self.db and task_id:
                    self.db.save_file_modification(task_id, filepath, 'deleted')
                
                return {
                    'success': True,
                    'filepath': filepath
                }
            else:
                return {
                    'success': False,
                    'filepath': filepath,
                    'error': 'File does not exist'
                }
        except Exception as e:
            return {
                'success': False,
                'filepath': filepath,
                'error': str(e)
            }
    
    def format_operations_summary(self, operations: List[Dict[str, Any]]) -> str:
        """
        Format file operations into human-readable summary.
        
        Args:
            operations: List of operation results
            
        Returns:
            Formatted summary string
        """
        if not operations:
            return "No file operations performed"
        
        successful = [op for op in operations if op['success']]
        failed = [op for op in operations if not op['success']]
        
        summary = f"📝 File Operations: {len(successful)}/{len(operations)} successful\n"
        
        if successful:
            # Separate created vs modified
            created = [op for op in successful if not op.get('existed')]
            modified = [op for op in successful if op.get('existed')]
            
            if created:
                summary += "\nCreated:\n"
                for op in created:
                    filepath = op['filepath']
                    if op.get('dry_run'):
                        summary += f"  [DRY RUN] {filepath}\n"
                    else:
                        bytes_written = op.get('bytes_written', 0)
                        summary += f"  ✅ {filepath} ({bytes_written} bytes)\n"
            
            if modified:
                summary += "\nModified:\n"
                for op in modified:
                    filepath = op['filepath']
                    if op.get('dry_run'):
                        summary += f"  [DRY RUN] {filepath}\n"
                    else:
                        bytes_written = op.get('bytes_written', 0)
                        summary += f"  🔄 {filepath} ({bytes_written} bytes)\n"
        
        if failed:
            summary += "\nFailed:\n"
            for op in failed:
                summary += f"  ❌ {op['filepath']}: {op.get('error', 'Unknown error')}\n"
        
        return summary

