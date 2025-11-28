"""
LM Studio Executor - Main execution engine using local LLM.

This replaces Claude CLI integration, making Agent7 work entirely with LM Studio.
"""
import os
from typing import Dict, Any, Optional, List
from local_llm_client import LocalLLMClient
from project_tools import ProjectTools
from tool_executor import ToolExecutor
from file_operations import FileOperations
from database import Database


class LMStudioExecutor:
    """
    Executes tasks using LM Studio with full tool chain support.
    
    Flow:
    1. LM Studio explores project with tools
    2. LM Studio generates code/files
    3. File Operations creates files
    4. LM Studio validates results
    """
    
    def __init__(
        self,
        llm_client: LocalLLMClient,
        db: Database,
        project_directory: str
    ):
        """
        Initialize LM Studio executor.
        
        Args:
            llm_client: LM Studio client
            db: Database for tracking
            project_directory: Project root directory
        """
        self.llm = llm_client
        self.db = db
        self.project_directory = project_directory
        
        # Initialize tool chain
        self.project_tools = ProjectTools(project_directory)
        self.tool_executor = ToolExecutor(project_directory)
        self.file_ops = FileOperations(db)
        
        # Conversation history for context
        self.conversation_history = []
    
    def create_system_prompt(self) -> str:
        """
        Create system prompt for LM Studio with tool descriptions.
        
        Returns:
            System prompt string
        """
        return """You are an expert software developer AI assistant working on a project.

Your capabilities:
1. EXPLORE: Use project tools to understand existing code
2. PLAN: Decide what needs to be done
3. CREATE: Generate code in the proper format for file creation
4. VALIDATE: Review your work

PROJECT EXPLORATION TOOLS:
You have access to these tools to explore the project:

- list_files(relative_path, extensions) - List files in directory
- read_file(filepath, start_line, end_line) - Read file contents  
- search_in_files(pattern, extensions) - Search for text/patterns
- find_files(name_pattern) - Find files by name (wildcards)
- find_definitions(name, type) - Find Python functions/classes
- get_project_structure(max_depth) - Get directory tree
- get_file_info(filepath) - Get file metadata

To use a tool, request it explicitly (use EXACT parameter names):
TOOL: list_files(relative_path="src", extensions=[".py"])
TOOL: read_file(filepath="main.py")
TOOL: search_in_files(pattern="class.*Database", extensions=[".py"])

FILE CREATION/MODIFICATION FORMAT:
When creating OR modifying files, use this EXACT format:

File: path/to/filename.ext
```language
complete file content here
```

🚨 FOR CODING TASKS: You MUST output File: blocks! Don't just explain - DO IT!

⚠️ CRITICAL RULES:
1. **Use EXACT file paths** from exploration results (e.g., if file is at "paddle.py", use "paddle.py" NOT "src/paddle.py")
2. **Read existing files FIRST** if modifying them (use read_file tool)
3. **Include COMPLETE file content** - this will overwrite the entire file
4. **Verify paths** - if get_project_structure shows "main.py" at root, use "main.py" not "src/main.py"
5. **ALWAYS OUTPUT FILES** for coding tasks - explaining what to do is NOT enough!

WORKFLOW FOR EXISTING PROJECTS:
1. **EXPLORE FIRST**: Use get_project_structure() to see actual file locations
2. **READ EXISTING FILES**: Use read_file() to see current content
3. **OUTPUT FILE BLOCKS**: Create File: blocks with complete updated content
4. **DON'T JUST TALK ABOUT IT**: Actually output the files!

WRONG ❌ (just explaining):
"The main.py file needs to pass 5 parameters to Paddle()..."

CORRECT ✅ (actually doing it):
File: main.py
```python
# Complete file content with the fix
```

Be thorough, professional, and write production-quality code.

TASK TYPE SPECIFIC BEHAVIOR:
- **planning**: Create markdown documentation files (.md) with plans, requirements, TODO lists
- **coding**: Create actual code files (.py, .js, .html, etc.) based on plans
- **testing**: Create test files and test documentation"""
    
    def create_task_prompt(
        self,
        task_description: str,
        task_type: str,
        context: Optional[str] = None
    ) -> str:
        """
        Create prompt for a specific task.
        
        Args:
            task_description: What to do
            task_type: planning, coding, testing, etc.
            context: Additional context
            
        Returns:
            Task prompt string
        """
        prompt = f"""Task Type: {task_type}
Task: {task_description}

Project Directory: {self.project_directory}
"""
        
        if context:
            prompt += f"\nContext:\n{context}\n"
        
        # Add specific instructions based on task type
        if task_type == 'coding':
            prompt += """
Instructions:
1. Explore project: TOOL: get_project_structure()
2. Read existing code: TOOL: read_file(filepath="...")
3. ⚠️ MANDATORY: Output fixed files using File: format!

⚠️⚠️⚠️ CRITICAL FOR CODING TASKS ⚠️⚠️⚠️
You MUST output files in this format:

File: filename.py
```python
complete file content here
```

Example:
File: main.py
```python
import pygame
# ... rest of file ...
```

DO NOT just say "update line X" - OUTPUT THE COMPLETE FILE!
Without File: blocks, your code changes will NOT be saved!
"""
        elif task_type == 'planning':
            prompt += """
Instructions:
1. Explore the project structure first (use TOOL: get_project_structure())
2. Analyze the requirements
3. Create a PLANNING DOCUMENT as a markdown (.md) file
4. Your planning document should include:
   - Project overview
   - Requirements breakdown
   - Architecture decisions
   - TODO list with priorities
   - Files that will need to be created/modified
   - Timeline estimates
   - Potential challenges

IMPORTANT: Create planning documents using the File: format:

File: PLAN.md
```markdown
# Project Plan: [Project Name]

## Overview
[Brief description]

## Requirements
- [ ] Requirement 1
- [ ] Requirement 2

## Architecture
[Design decisions]

## TODO List
1. [ ] Task 1
2. [ ] Task 2

## Files to Create
- file1.py - Purpose
- file2.py - Purpose

## Timeline
[Estimates]
```

Create comprehensive planning documents that coding tasks can reference!
"""
        elif task_type == 'testing':
            prompt += """
Instructions:
1. Explore existing test structure
2. Create pytest-compatible tests
3. Follow existing test patterns
4. Use File: format to create test files
"""
        
        return prompt
    
    def execute_task(
        self,
        task_id: int,
        task_description: str,
        task_type: str = 'coding',
        max_iterations: int = 3,
        callback: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        Execute a task with LM Studio.
        
        Args:
            task_id: Task ID for tracking
            task_description: What to do
            task_type: Type of task
            max_iterations: Max tool-execute cycles
            callback: Optional callback for progress updates
            
        Returns:
            Execution result with files created and status
        """
        if callback:
            callback({'status': 'starting', 'message': 'Initializing LM Studio executor...'})
        
        # Reset conversation
        self.conversation_history = []
        
        # Create initial prompt
        task_prompt = self.create_task_prompt(task_description, task_type)
        
        all_file_operations = []
        all_tool_results = []
        nudge_used = False  # Track if we used the nudge
        
        # Iterative execution with tool support
        # Allow one extra iteration if nudge is needed
        max_iter = max_iterations
        for iteration in range(max_iter + 1):  # +1 to allow nudge iteration
            if callback:
                callback({
                    'status': 'executing',
                    'message': f'Iteration {iteration + 1}/{max_iterations}...',
                    'iteration': iteration + 1
                })
            
            # Send to LM Studio
            response = self.llm.send_message(
                task_prompt,
                system_prompt=self.create_system_prompt(),
                temperature=0.3,
                max_tokens=4096,
                history=self.conversation_history
            )
            
            if not response.get('response'):
                return {
                    'success': False,
                    'error': 'No response from LM Studio',
                    'task_id': task_id
                }
            
            llm_response = response['response']
            
            # Add to conversation history
            self.conversation_history.append({
                'role': 'assistant',
                'content': llm_response
            })
            
            if callback:
                callback({
                    'status': 'response',
                    'message': 'LM Studio responded',
                    'response': llm_response
                })
            
            # Check for tool requests
            tool_results = self.tool_executor.parse_and_execute(llm_response)
            
            if tool_results:
                if callback:
                    callback({
                        'status': 'tools',
                        'message': f'Executing {len(tool_results)} tool(s)...',
                        'tool_count': len(tool_results)
                    })
                
                all_tool_results.extend(tool_results)
                
                # Format tool results for LM Studio
                tool_output = "\n\n=== Tool Results ===\n\n"
                for tool_result in tool_results:
                    formatted = self.tool_executor.format_tool_result(tool_result)
                    tool_output += formatted + "\n\n"
                
                if callback:
                    callback({
                        'status': 'tool_results',
                        'message': 'Tool results ready',
                        'results': tool_output
                    })
                
                # Continue conversation with tool results
                task_prompt = tool_output + "\nBased on these results, continue with your task. Create the necessary files using the File: format."
                
                # Add tool results to history
                self.conversation_history.append({
                    'role': 'user',
                    'content': tool_output
                })
                
                continue  # Go to next iteration with tool results
            
            # Check for file operations
            if callback:
                callback({
                    'status': 'files',
                    'message': 'Parsing LM Studio output for files...',
                    'operations': []
                })
            
            file_operations = self.file_ops.parse_and_execute(
                llm_response,
                self.project_directory,
                task_id=task_id
            )
            
            if callback:
                callback({
                    'status': 'files',
                    'message': f'Found {len(file_operations)} file operation(s)',
                    'operations': file_operations
                })
            
            if file_operations:
                if callback:
                    ops_summary = self.file_ops.format_operations_summary(file_operations)
                    callback({
                        'status': 'files',
                        'message': 'Creating files...',
                        'operations': file_operations,
                        'summary': ops_summary
                    })
                
                all_file_operations.extend(file_operations)
                
                # If files were created, we're likely done
                # But ask LM Studio to validate
                files_created = [op['filepath'] for op in file_operations if op['success']]
                
                if files_created:
                    files_str = ', '.join(files_created)
                    validation_prompt = (
                        "Files created: " + files_str + "\n\n" +
                        "Please validate:\n" +
                        "1. Are all necessary files created?\n" +
                        "2. Is the code correct and complete?\n" +
                        "3. Does it integrate properly with existing code (if any)?\n" +
                        "4. Is anything missing?\n\n" +
                        "Respond with:\n" +
                        "VALIDATION: [PASS/FAIL]\n" +
                        "NOTES: [your assessment]"
                    )
                    
                    self.conversation_history.append({
                        'role': 'user',
                        'content': validation_prompt
                    })
                    
                    # Get validation response
                    validation = self.llm.send_message(
                        validation_prompt,
                        system_prompt="You are validating code quality. Be thorough but fair.",
                        temperature=0.2,
                        max_tokens=1024,
                        history=self.conversation_history
                    )
                    
                    validation_text = validation.get('response', '')
                    
                    if callback:
                        callback({
                            'status': 'validation',
                            'message': 'Validating results...',
                            'validation': validation_text
                        })
                    
                    # Check if validation passed
                    if 'VALIDATION: PASS' in validation_text.upper():
                        return {
                            'success': True,
                            'task_id': task_id,
                            'response': llm_response,
                            'file_operations': all_file_operations,
                            'tool_results': all_tool_results,
                            'validation': validation_text,
                            'status': 'COMPLETED',
                            'iterations': iteration + 1
                        }
                    else:
                        # Continue to next iteration for improvements
                        task_prompt = f"Validation feedback:\n{validation_text}\n\nPlease address the issues."
                        continue
            
            # No files created - check if we read any files
            files_read = any('read_file' in str(r) for r in all_tool_results)
            
            if files_read and not file_operations and not nudge_used:
                # We read files but didn't create/modify any - PROMPT FOR FILE OUTPUT!
                nudge_used = True  # Mark that we're using the nudge
                
                if callback:
                    callback({
                        'status': 'response',
                        'message': '⚠️ Files read but no modifications output. Requesting file creation...',
                        'response': 'Prompting LM Studio to output modified files'
                    })
                
                task_prompt = f"""⚠️⚠️⚠️ CRITICAL: You read files but didn't output any modifications! ⚠️⚠️⚠️

You MUST output the modified files using the File: format!

DO NOT output JSON like [] or [{...}]
DO NOT just explain what you would do
ACTUALLY OUTPUT THE FILE CONTENT!

Example - THIS IS WHAT YOU MUST DO:

File: main.py
```python
import pygame
from paddle import Paddle
# ... rest of the file with your fixes ...
```

Now output the COMPLETE fixed file(s) in this exact format!"""
                
                # If we're on the last normal iteration, allow one more
                if iteration >= max_iter - 1:
                    max_iter = iteration + 2  # Allow one more iteration after this one
                
                continue
            
            # No tools and no files - might be planning or needs clarification
            if iteration == 0:
                # Give another chance
                if callback:
                    callback({
                        'status': 'response',
                        'message': 'No files detected, prompting for file creation...',
                        'response': 'Asking LM Studio to create files in proper format'
                    })
                task_prompt = f"Previous response:\n{llm_response}\n\nPlease create the necessary files using the File: format, or use tools to explore the project first."
            else:
                # No files in later iterations - break and return what we have
                if callback:
                    callback({
                        'status': 'response',
                        'message': f'No files detected in iteration {iteration + 1}, ending...',
                        'response': f'Completed {iteration + 1} iterations'
                    })
                break
        
        # Completed iterations without clear success
        final_status = 'COMPLETED' if len(all_file_operations) > 0 else 'NEEDS_REVISION'
        
        if callback:
            callback({
                'status': 'validation',
                'message': f'Finalizing: {final_status}',
                'validation': f'Created {len(all_file_operations)} file(s), used {len(all_tool_results)} tool(s)'
            })
        
        return {
            'success': len(all_file_operations) > 0,
            'task_id': task_id,
            'response': llm_response if 'llm_response' in locals() else 'No response',
            'file_operations': all_file_operations,
            'tool_results': all_tool_results,
            'status': final_status,
            'iterations': iteration + 1 if 'iteration' in locals() else 0,  # Actual iterations completed
            'message': f'Completed {iteration + 1 if "iteration" in locals() else 0} iterations'
        }
    
    def validate_result(
        self,
        task_description: str,
        file_operations: List[Dict[str, Any]],
        tool_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Ask LM Studio to validate task completion.
        
        Args:
            task_description: Original task
            file_operations: Files created
            tool_results: Tools used
            
        Returns:
            Validation result
        """
        files_created = [op['filepath'] for op in file_operations if op.get('success')]
        
        files_list = '\n'.join(f"  - {f}" for f in files_created)
        
        validation_prompt = ("Task: " + task_description + "\n\n" +
                           "Files Created: " + str(len(files_created)) + "\n" +
                           files_list + "\n\n" +
                           "Tools Used: " + str(len(tool_results)) + "\n\n" +
                           "Please assess if this task is complete:\n" +
                           "1. Were all requirements met?\n" +
                           "2. Is the code quality good?\n" +
                           "3. Is anything missing?\n" +
                           "4. Overall confidence (0-100%)?\n\n" +
                           "Format:\n" +
                           "STATUS: [COMPLETED/NEEDS_REVISION/FAILED]\n" +
                           "CONFIDENCE: [0-100]\n" +
                           "NOTES: [your assessment]")
        
        response = self.llm.send_message(
            validation_prompt,
            system_prompt="You are a code reviewer. Be thorough but fair.",
            temperature=0.2,
            max_tokens=1024
        )
        
        validation_text = response.get('response', '')
        
        # Parse validation
        status = 'UNKNOWN'
        confidence = 50
        
        if 'STATUS: COMPLETED' in validation_text.upper():
            status = 'COMPLETED'
        elif 'STATUS: NEEDS_REVISION' in validation_text.upper():
            status = 'NEEDS_REVISION'
        elif 'STATUS: FAILED' in validation_text.upper():
            status = 'FAILED'
        
        # Extract confidence
        import re
        conf_match = re.search(r'CONFIDENCE:\s*(\d+)', validation_text, re.IGNORECASE)
        if conf_match:
            confidence = int(conf_match.group(1))
        
        return {
            'status': status,
            'confidence': confidence,
            'validation_text': validation_text,
            'files_created': files_created,
            'tools_used': len(tool_results)
        }

