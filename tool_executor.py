"""
Tool Executor - Parses Claude's tool requests and executes them.

Handles the flow:
1. Claude requests a tool in natural language
2. Executor parses the request
3. Tool is executed
4. Results are returned to Claude
"""
import re
import json
from typing import Dict, Any, Optional
from project_tools import ProjectTools


class ToolExecutor:
    """
    Executes tools requested by Claude for project exploration.
    """
    
    def __init__(self, project_directory: str):
        """
        Initialize tool executor.
        
        Args:
            project_directory: Root directory of project
        """
        self.project_tools = ProjectTools(project_directory)
        self.tools_available = {
            'list_files': self.project_tools.list_files,
            'read_file': self.project_tools.read_file,
            'search_in_files': self.project_tools.search_in_files,
            'find_files': self.project_tools.find_files,
            'find_definitions': self.project_tools.find_definitions,
            'get_project_structure': self.project_tools.get_project_structure,
            'get_file_info': self.project_tools.get_file_info
        }
    
    def detect_tool_requests(self, text: str) -> list[Dict[str, Any]]:
        """
        Detect tool requests in LM Studio's output.
        
        Looks for patterns like:
        - JSON: [{"name": "tool", "arguments": {...}}]
        - "I need to use list_files..."
        - "Let me read_file(...)..."
        - "TOOL: list_files(...)"
        
        Args:
            text: LM Studio's output text
            
        Returns:
            List of detected tool requests
        """
        tool_requests = []
        
        # Pattern 0: JSON format (OpenAI function calling style)
        # [{"name": "get_project_structure", "arguments": {"max_depth": 1}}]
        import json
        json_pattern = r'\[?\s*\{\s*"name"\s*:\s*"(\w+)"\s*,\s*"arguments"\s*:\s*(\{.*?\})\s*\}\s*\]?'
        json_matches = re.findall(json_pattern, text, re.DOTALL)
        
        for tool_name, args_json in json_matches:
            if tool_name in self.tools_available:
                try:
                    args_dict = json.loads(args_json)
                    tool_requests.append({
                        'tool': tool_name,
                        'args_dict': args_dict,
                        'pattern': 'json'
                    })
                except json.JSONDecodeError:
                    pass
        
        # Pattern 1: Explicit TOOL: marker
        # TOOL: list_files(relative_path="src", extensions=[".py"])
        pattern1 = r'TOOL:\s*(\w+)\((.*?)\)'
        matches1 = re.findall(pattern1, text, re.IGNORECASE)
        
        for tool_name, args_str in matches1:
            if tool_name in self.tools_available:
                tool_requests.append({
                    'tool': tool_name,
                    'args_str': args_str,
                    'pattern': 'explicit'
                })
        
        # Pattern 2: "I need to use TOOL_NAME"
        # I need to use list_files on "src" directory
        pattern2 = r'(?:I need to use|Let me use|I\'ll use|Using)\s+(\w+)'
        matches2 = re.findall(pattern2, text, re.IGNORECASE)
        
        for tool_name in matches2:
            if tool_name in self.tools_available:
                # Extract context around the tool mention
                context_match = re.search(
                    rf'(?:I need to use|Let me use|I\'ll use|Using)\s+{tool_name}.*?[.\n]',
                    text,
                    re.IGNORECASE | re.DOTALL
                )
                context = context_match.group(0) if context_match else ""
                
                tool_requests.append({
                    'tool': tool_name,
                    'context': context,
                    'pattern': 'natural_language'
                })
        
        # Pattern 3: Function call syntax
        # list_files("src", extensions=[".py"])
        pattern3 = r'(\w+)\((.*?)\)'
        matches3 = re.findall(pattern3, text)
        
        for tool_name, args_str in matches3:
            if tool_name in self.tools_available:
                # Check if it's in a code-like context
                if any(marker in text for marker in ['```', 'TOOL:', 'USE:']):
                    tool_requests.append({
                        'tool': tool_name,
                        'args_str': args_str,
                        'pattern': 'function_call'
                    })
        
        return tool_requests
    
    def parse_tool_args(self, args_str: str) -> Dict[str, Any]:
        """
        Parse tool arguments from string.
        
        Handles formats like:
        - path="src", extensions=[".py"]
        - "src", [".py"]
        - {"path": "src", "extensions": [".py"]}
        
        Args:
            args_str: Argument string
            
        Returns:
            Dict of parsed arguments
        """
        args = {}
        
        # Try JSON format first
        try:
            args = json.loads(f"{{{args_str}}}")
            return args
        except:
            pass
        
        # Parse key=value pairs
        # path="src", extensions=[".py"], max_depth=3
        kv_pattern = r'(\w+)\s*=\s*([^\,]+)'
        matches = re.findall(kv_pattern, args_str)
        
        for key, value in matches:
            # Parse value
            value = value.strip()
            
            # Try to evaluate as Python literal
            try:
                import ast
                args[key] = ast.literal_eval(value)
            except:
                # Keep as string, removing quotes
                args[key] = value.strip('"').strip("'")
        
        # If no key=value pairs, try positional arguments
        if not args:
            # Split by commas outside brackets
            parts = []
            bracket_depth = 0
            current = ""
            
            for char in args_str:
                if char in '[{(':
                    bracket_depth += 1
                elif char in ']})':
                    bracket_depth -= 1
                elif char == ',' and bracket_depth == 0:
                    parts.append(current.strip())
                    current = ""
                    continue
                current += char
            
            if current.strip():
                parts.append(current.strip())
            
            # Parse each part
            parsed_parts = []
            for part in parts:
                try:
                    import ast
                    parsed_parts.append(ast.literal_eval(part))
                except:
                    parsed_parts.append(part.strip('"').strip("'"))
            
            # Map to common argument names based on tool
            # This is a simplified mapping
            if len(parsed_parts) >= 1:
                args['path'] = parsed_parts[0] if parsed_parts else "."
            if len(parsed_parts) >= 2:
                args['extensions'] = parsed_parts[1] if len(parsed_parts) > 1 else None
        
        return args
    
    def execute_tool(
        self,
        tool_name: str,
        args: Optional[Dict[str, Any]] = None,
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute a tool with given arguments.
        
        Args:
            tool_name: Name of tool to execute
            args: Tool arguments
            context: Natural language context (if available)
            
        Returns:
            Tool execution result
        """
        if tool_name not in self.tools_available:
            return {
                'success': False,
                'error': f"Tool '{tool_name}' not found"
            }
        
        tool_func = self.tools_available[tool_name]
        
        # If context provided but no args, try to extract args from context
        if context and not args:
            args = self.extract_args_from_context(tool_name, context)
        
        if not args:
            args = {}
        
        try:
            result = tool_func(**args)
            result['tool'] = tool_name
            result['args'] = args
            return result
        except TypeError as e:
            # Argument mismatch
            return {
                'success': False,
                'error': f"Invalid arguments for {tool_name}: {e}",
                'tool': tool_name
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'tool': tool_name
            }
    
    def extract_args_from_context(
        self,
        tool_name: str,
        context: str
    ) -> Dict[str, Any]:
        """
        Extract tool arguments from natural language context.
        
        Args:
            tool_name: Tool name
            context: Context string
            
        Returns:
            Extracted arguments
        """
        args = {}
        
        # Common patterns
        
        # Extract path/directory
        path_match = re.search(r'(?:on|in|from)\s+["\']?([^\s"\']+)["\']?\s+(?:directory|folder|path)', context, re.IGNORECASE)
        if path_match:
            args['relative_path'] = path_match.group(1)
        
        # Extract file path
        file_match = re.search(r'file\s+["\']?([^\s"\']+)["\']?', context, re.IGNORECASE)
        if file_match:
            args['filepath'] = file_match.group(1)
        
        # Extract pattern
        pattern_match = re.search(r'(?:for|pattern|search)\s+["\']([^"\']+)["\']', context, re.IGNORECASE)
        if pattern_match:
            args['pattern'] = pattern_match.group(1)
        
        # Extract extensions
        ext_match = re.search(r'(?:extensions?|files?)\s+\[([^\]]+)\]', context, re.IGNORECASE)
        if ext_match:
            exts = [e.strip().strip('"').strip("'") for e in ext_match.group(1).split(',')]
            args['extensions'] = exts
        
        return args
    
    def parse_and_execute(self, text: str) -> list[Dict[str, Any]]:
        """
        Parse tool requests from text and execute them.
        
        Args:
            text: Text containing tool requests
            
        Returns:
            List of execution results
        """
        tool_requests = self.detect_tool_requests(text)
        results = []
        
        for request in tool_requests:
            tool_name = request['tool']
            
            # Parse arguments
            args = None
            if 'args_dict' in request:
                # JSON format - already parsed
                args = request['args_dict']
            elif 'args_str' in request:
                # String format - needs parsing
                args = self.parse_tool_args(request['args_str'])
            elif 'context' in request:
                # Natural language - extract from context
                args = self.extract_args_from_context(tool_name, request['context'])
            
            # Execute
            result = self.execute_tool(tool_name, args, request.get('context'))
            results.append(result)
        
        return results
    
    def format_tool_result(self, result: Dict[str, Any]) -> str:
        """
        Format tool result for display to Claude.
        
        Args:
            result: Tool execution result
            
        Returns:
            Formatted string
        """
        if not result.get('success'):
            return f"❌ Error: {result.get('error', 'Unknown error')}"
        
        tool_name = result.get('tool', 'unknown')
        
        # Format based on tool type
        if tool_name == 'list_files':
            files = result.get('files', [])
            dirs = result.get('directories', [])
            output = f"📁 Files in directory ({len(files)} files, {len(dirs)} directories):\n\n"
            
            if dirs:
                output += "Directories:\n"
                for d in dirs[:20]:  # Limit display
                    output += f"  📁 {d['name']}\n"
            
            if files:
                output += "\nFiles:\n"
                for f in files[:20]:  # Limit display
                    size_kb = f['size'] / 1024
                    output += f"  📄 {f['name']} ({size_kb:.1f} KB)\n"
            
            if len(files) > 20:
                output += f"\n... and {len(files) - 20} more files"
            
            return output
        
        elif tool_name == 'read_file':
            content = result.get('content', '')
            lines = result.get('lines', 0)
            filepath = result.get('filepath', '')
            return f"📄 {filepath} ({lines} lines):\n\n```\n{content}\n```"
        
        elif tool_name == 'search_in_files':
            matches = result.get('matches', [])
            total = result.get('total', 0)
            output = f"🔍 Found {total} matches:\n\n"
            
            for match in matches[:20]:  # Limit display
                output += f"  {match['file']}:{match['line']}\n    {match['content']}\n\n"
            
            if len(matches) > 20:
                output += f"... and {len(matches) - 20} more matches"
            
            return output
        
        elif tool_name == 'find_files':
            matches = result.get('matches', [])
            total = result.get('total', 0)
            output = f"📂 Found {total} files:\n\n"
            
            for match in matches[:20]:
                size_kb = match['size'] / 1024
                output += f"  {match['path']} ({size_kb:.1f} KB)\n"
            
            if len(matches) > 20:
                output += f"... and {len(matches) - 20} more files"
            
            return output
        
        elif tool_name == 'find_definitions':
            matches = result.get('matches', [])
            total = result.get('total', 0)
            output = f"🔎 Found {total} definitions:\n\n"
            
            for match in matches:
                output += f"  {match['type']} in {match['file']}:{match['line']}\n    {match['content']}\n\n"
            
            return output
        
        elif tool_name == 'get_file_info':
            name = result.get('name', '')
            size = result.get('size', 0)
            lines = result.get('lines', 0)
            ext = result.get('extension', '')
            
            size_kb = size / 1024
            output = f"ℹ️  File Info: {name}\n"
            output += f"  Size: {size_kb:.1f} KB\n"
            output += f"  Lines: {lines}\n"
            output += f"  Extension: {ext}\n"
            
            return output
        
        else:
            # Generic formatting
            return f"✅ {tool_name} executed:\n{json.dumps(result, indent=2)}"
    
    def get_tools_summary(self) -> str:
        """Get summary of available tools."""
        return self.project_tools.get_tools_description()

