"""
Project Tools - Provides file exploration and search capabilities for Claude.

These tools allow Claude to:
- Explore directory structure
- Read existing files
- Search for code patterns
- Find files by name
- Understand project context
"""
import os
import re
from typing import List, Dict, Any, Optional
from pathlib import Path


class ProjectTools:
    """
    Tools for exploring and searching a project directory.
    Can be used by Claude to understand existing code before making changes.
    """
    
    def __init__(self, project_directory: str):
        """
        Initialize project tools.
        
        Args:
            project_directory: Root directory of the project
        """
        self.project_directory = project_directory
        self.ignore_patterns = [
            '__pycache__',
            '.git',
            'node_modules',
            'venv',
            'env',
            '.env',
            '.pytest_cache',
            '.mypy_cache',
            '*.pyc',
            '*.pyo',
            '*.pyd',
            '.DS_Store',
            'Thumbs.db'
        ]
    
    def list_files(
        self, 
        relative_path: str = ".",
        extensions: Optional[List[str]] = None,
        max_depth: int = 3,
        include_hidden: bool = False
    ) -> Dict[str, Any]:
        """
        List files in directory with optional filtering.
        
        Args:
            relative_path: Path relative to project root
            extensions: Filter by extensions (e.g., ['.py', '.js'])
            max_depth: Maximum directory depth to traverse
            include_hidden: Include hidden files/folders
            
        Returns:
            Dict with 'files', 'directories', and 'total_files'
        """
        full_path = os.path.join(self.project_directory, relative_path)
        
        if not os.path.exists(full_path):
            return {
                'success': False,
                'error': f"Path not found: {relative_path}"
            }
        
        files = []
        directories = []
        
        try:
            for item in os.listdir(full_path):
                # Skip ignored patterns
                if any(pattern in item for pattern in self.ignore_patterns):
                    continue
                
                # Skip hidden files/folders if not included
                if not include_hidden and item.startswith('.'):
                    continue
                
                item_path = os.path.join(full_path, item)
                relative_item_path = os.path.relpath(item_path, self.project_directory)
                
                if os.path.isfile(item_path):
                    # Filter by extension if specified
                    if extensions:
                        if not any(item.endswith(ext) for ext in extensions):
                            continue
                    
                    file_size = os.path.getsize(item_path)
                    files.append({
                        'name': item,
                        'path': relative_item_path,
                        'size': file_size,
                        'extension': os.path.splitext(item)[1]
                    })
                
                elif os.path.isdir(item_path):
                    directories.append({
                        'name': item,
                        'path': relative_item_path
                    })
            
            return {
                'success': True,
                'files': sorted(files, key=lambda x: x['name']),
                'directories': sorted(directories, key=lambda x: x['name']),
                'total_files': len(files),
                'total_directories': len(directories)
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def read_file(
        self, 
        filepath: str,
        start_line: Optional[int] = None,
        end_line: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Read contents of a file.
        
        Args:
            filepath: Path relative to project root
            start_line: Optional start line (1-indexed)
            end_line: Optional end line (1-indexed)
            
        Returns:
            Dict with 'content', 'lines', 'size'
        """
        full_path = os.path.join(self.project_directory, filepath)
        
        if not os.path.exists(full_path):
            return {
                'success': False,
                'error': f"File not found: {filepath}"
            }
        
        if not os.path.isfile(full_path):
            return {
                'success': False,
                'error': f"Not a file: {filepath}"
            }
        
        try:
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            # Apply line range if specified
            if start_line is not None or end_line is not None:
                start = (start_line - 1) if start_line else 0
                end = end_line if end_line else len(lines)
                lines = lines[start:end]
            
            content = ''.join(lines)
            
            return {
                'success': True,
                'content': content,
                'lines': len(lines),
                'size': len(content),
                'filepath': filepath
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def search_in_files(
        self,
        pattern: str,
        extensions: Optional[List[str]] = None,
        case_sensitive: bool = False,
        max_results: int = 50
    ) -> Dict[str, Any]:
        """
        Search for a pattern in project files (grep-like).
        
        Args:
            pattern: Text or regex pattern to search for
            extensions: File extensions to search (e.g., ['.py'])
            case_sensitive: Case-sensitive search
            max_results: Maximum number of matches to return
            
        Returns:
            Dict with 'matches' list containing file, line number, and content
        """
        matches = []
        flags = 0 if case_sensitive else re.IGNORECASE
        
        try:
            regex = re.compile(pattern, flags)
        except re.error as e:
            return {
                'success': False,
                'error': f"Invalid regex pattern: {e}"
            }
        
        try:
            for root, dirs, files in os.walk(self.project_directory):
                # Remove ignored directories
                dirs[:] = [d for d in dirs if not any(pattern in d for pattern in self.ignore_patterns)]
                
                for file in files:
                    # Skip ignored files
                    if any(pattern in file for pattern in self.ignore_patterns):
                        continue
                    
                    # Filter by extension
                    if extensions and not any(file.endswith(ext) for ext in extensions):
                        continue
                    
                    filepath = os.path.join(root, file)
                    relative_path = os.path.relpath(filepath, self.project_directory)
                    
                    try:
                        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                            for line_num, line in enumerate(f, 1):
                                if regex.search(line):
                                    matches.append({
                                        'file': relative_path,
                                        'line': line_num,
                                        'content': line.rstrip(),
                                        'match': regex.search(line).group(0)
                                    })
                                    
                                    if len(matches) >= max_results:
                                        return {
                                            'success': True,
                                            'matches': matches,
                                            'total': len(matches),
                                            'truncated': True,
                                            'message': f"Results limited to {max_results}"
                                        }
                    except:
                        # Skip files that can't be read
                        continue
            
            return {
                'success': True,
                'matches': matches,
                'total': len(matches),
                'truncated': False
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def find_files(
        self,
        name_pattern: str,
        case_sensitive: bool = False
    ) -> Dict[str, Any]:
        """
        Find files by name pattern.
        
        Args:
            name_pattern: Pattern to match (supports wildcards)
            case_sensitive: Case-sensitive matching
            
        Returns:
            Dict with list of matching files
        """
        # Convert shell-style wildcards to regex
        regex_pattern = name_pattern.replace('.', r'\.')
        regex_pattern = regex_pattern.replace('*', '.*')
        regex_pattern = regex_pattern.replace('?', '.')
        
        flags = 0 if case_sensitive else re.IGNORECASE
        
        try:
            regex = re.compile(regex_pattern, flags)
        except re.error as e:
            return {
                'success': False,
                'error': f"Invalid pattern: {e}"
            }
        
        matches = []
        
        try:
            for root, dirs, files in os.walk(self.project_directory):
                # Remove ignored directories
                dirs[:] = [d for d in dirs if not any(pattern in d for pattern in self.ignore_patterns)]
                
                for file in files:
                    if regex.search(file):
                        filepath = os.path.join(root, file)
                        relative_path = os.path.relpath(filepath, self.project_directory)
                        
                        matches.append({
                            'name': file,
                            'path': relative_path,
                            'size': os.path.getsize(filepath)
                        })
            
            return {
                'success': True,
                'matches': matches,
                'total': len(matches)
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_project_structure(
        self,
        max_depth: int = 3,
        extensions: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get a tree-like structure of the project.
        
        Args:
            max_depth: Maximum depth to traverse
            extensions: Filter by file extensions
            
        Returns:
            Dict with nested structure
        """
        def build_tree(path: str, depth: int = 0) -> Dict[str, Any]:
            if depth > max_depth:
                return None
            
            relative_path = os.path.relpath(path, self.project_directory)
            name = os.path.basename(path)
            
            # Skip ignored patterns
            if any(pattern in name for pattern in self.ignore_patterns):
                return None
            
            if os.path.isfile(path):
                # Filter by extension
                if extensions and not any(name.endswith(ext) for ext in extensions):
                    return None
                
                return {
                    'type': 'file',
                    'name': name,
                    'path': relative_path,
                    'size': os.path.getsize(path)
                }
            
            elif os.path.isdir(path):
                children = []
                try:
                    for item in sorted(os.listdir(path)):
                        item_path = os.path.join(path, item)
                        child = build_tree(item_path, depth + 1)
                        if child:
                            children.append(child)
                except PermissionError:
                    pass
                
                return {
                    'type': 'directory',
                    'name': name,
                    'path': relative_path,
                    'children': children
                }
        
        try:
            tree = build_tree(self.project_directory)
            return {
                'success': True,
                'structure': tree
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def find_definitions(
        self,
        name: str,
        definition_type: str = 'any'
    ) -> Dict[str, Any]:
        """
        Find function/class definitions in Python files.
        
        Args:
            name: Name of function/class to find
            definition_type: 'function', 'class', or 'any'
            
        Returns:
            Dict with matching definitions
        """
        matches = []
        
        # Regex patterns for Python definitions
        patterns = []
        if definition_type in ['function', 'any']:
            patterns.append(rf'^\s*def\s+{re.escape(name)}\s*\(')
        if definition_type in ['class', 'any']:
            patterns.append(rf'^\s*class\s+{re.escape(name)}\s*[\(:]')
        
        try:
            for root, dirs, files in os.walk(self.project_directory):
                # Remove ignored directories
                dirs[:] = [d for d in dirs if not any(pattern in d for pattern in self.ignore_patterns)]
                
                for file in files:
                    if not file.endswith('.py'):
                        continue
                    
                    filepath = os.path.join(root, file)
                    relative_path = os.path.relpath(filepath, self.project_directory)
                    
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            for line_num, line in enumerate(f, 1):
                                for pattern in patterns:
                                    if re.search(pattern, line):
                                        matches.append({
                                            'file': relative_path,
                                            'line': line_num,
                                            'content': line.rstrip(),
                                            'type': 'function' if 'def' in line else 'class'
                                        })
                    except:
                        continue
            
            return {
                'success': True,
                'matches': matches,
                'total': len(matches)
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_file_info(self, filepath: str) -> Dict[str, Any]:
        """
        Get detailed information about a file.
        
        Args:
            filepath: Path relative to project root
            
        Returns:
            Dict with file metadata
        """
        full_path = os.path.join(self.project_directory, filepath)
        
        if not os.path.exists(full_path):
            return {
                'success': False,
                'error': f"File not found: {filepath}"
            }
        
        try:
            stat = os.stat(full_path)
            
            # Count lines for text files
            lines = 0
            if os.path.isfile(full_path):
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        lines = sum(1 for _ in f)
                except:
                    pass
            
            return {
                'success': True,
                'path': filepath,
                'name': os.path.basename(filepath),
                'size': stat.st_size,
                'lines': lines,
                'extension': os.path.splitext(filepath)[1],
                'is_file': os.path.isfile(full_path),
                'is_directory': os.path.isdir(full_path),
                'modified': stat.st_mtime
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_tools_description(self) -> str:
        """
        Get description of available tools for Claude.
        
        Returns:
            Markdown-formatted description of tools
        """
        return """
## Available Project Exploration Tools

You have access to these tools to explore and understand the project:

1. **list_files(path, extensions)** - List files in a directory
   - Example: list_files("src", extensions=[".py"])
   - Returns: List of files with sizes

2. **read_file(filepath, start_line, end_line)** - Read file contents
   - Example: read_file("main.py", start_line=1, end_line=50)
   - Returns: File content

3. **search_in_files(pattern, extensions)** - Search for text/regex
   - Example: search_in_files("def main", extensions=[".py"])
   - Returns: Matches with file, line number, content

4. **find_files(name_pattern)** - Find files by name
   - Example: find_files("*.json")
   - Returns: List of matching files

5. **find_definitions(name, type)** - Find function/class definitions
   - Example: find_definitions("MyClass", type="class")
   - Returns: Definitions with locations

6. **get_project_structure(max_depth)** - Get directory tree
   - Example: get_project_structure(max_depth=2)
   - Returns: Nested directory structure

7. **get_file_info(filepath)** - Get file metadata
   - Example: get_file_info("app.py")
   - Returns: Size, lines, extension, etc.

**How to use**: When you need project information, request a tool like:
"I need to use list_files on the 'src' directory with extensions ['.py']"

The system will execute the tool and provide results before you proceed.
"""

