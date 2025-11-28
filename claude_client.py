"""
Claude CLI integration module.
"""
import subprocess
import json
import re
from typing import Optional, Dict, Any, List, Generator


class ClaudeClient:
    """Client for interacting with Claude via CLI."""
    
    def __init__(self, cli_command: str = "claude"):
        """
        Initialize Claude CLI client.
        
        Args:
            cli_command: The command to invoke Claude CLI (default: 'claude')
        """
        self.cli_command = cli_command
    
    def send_message(self, prompt: str, 
                    conversation_id: Optional[str] = None,
                    model: Optional[str] = None,
                    max_tokens: int = 4096,
                    temperature: float = 1.0) -> Dict[str, Any]:
        """
        Send a message to Claude via CLI.
        
        Args:
            prompt: The prompt to send
            conversation_id: Optional conversation ID to continue a conversation
            model: Optional model name
            max_tokens: Maximum tokens in response
            temperature: Temperature for generation
            
        Returns:
            Dict with 'response' and 'metadata' keys
        """
        try:
            # Build command
            cmd = [self.cli_command]
            
            if conversation_id:
                cmd.extend(['--conversation-id', conversation_id])
            
            if model:
                cmd.extend(['--model', model])
            
            cmd.extend(['--max-tokens', str(max_tokens)])
            cmd.extend(['--temperature', str(temperature)])
            cmd.append(prompt)
            
            # Execute command
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode != 0:
                return {
                    'response': None,
                    'error': result.stderr,
                    'metadata': {'success': False}
                }
            
            return {
                'response': result.stdout.strip(),
                'metadata': {
                    'success': True,
                    'model': model,
                    'max_tokens': max_tokens,
                    'temperature': temperature
                }
            }
            
        except subprocess.TimeoutExpired:
            return {
                'response': None,
                'error': 'Request timed out',
                'metadata': {'success': False}
            }
        except Exception as e:
            return {
                'response': None,
                'error': str(e),
                'metadata': {'success': False}
            }
    
    def send_message_with_file_access(
        self, 
        prompt: str, 
        project_directory: str,
        conversation_id: Optional[str] = None,
        use_agents: Optional[List[str]] = None,
        model: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 1.0
    ) -> Dict[str, Any]:
        """
        Launch Claude CLI in project directory with file permissions.
        
        Args:
            prompt: The prompt/task for Claude
            project_directory: Path to project (becomes working directory)
            conversation_id: Continue existing conversation
            use_agents: List of agents to tell Claude to use
            model: Optional model name
            max_tokens: Maximum tokens in response
            temperature: Temperature for generation
            
        Returns:
            Dict with response, session_limited flag, reset_time, files_modified
        """
        try:
            # Build enhanced prompt with agent instructions
            enhanced_prompt = self._build_agent_prompt(prompt, use_agents)
            
            # Build command
            cmd = [
                self.cli_command,
                '--dangerously-skip-permissions'
            ]
            
            if conversation_id:
                cmd.extend(['--conversation-id', conversation_id])
            
            if model:
                cmd.extend(['--model', model])
            
            cmd.extend(['--max-tokens', str(max_tokens)])
            cmd.extend(['--temperature', str(temperature)])
            cmd.append(enhanced_prompt)
            
            # Execute in project directory with real-time output
            process = subprocess.Popen(
                cmd,
                cwd=project_directory,  # KEY: Set working directory
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1  # Line buffered for real-time output
            )
            
            # Collect output
            output_lines = []
            for line in process.stdout:
                output_lines.append(line)
            
            # Wait for completion
            process.wait(timeout=600)  # 10 minute timeout
            
            full_output = ''.join(output_lines)
            stderr_output = process.stderr.read()
            
            # Check for session limit
            if 'Session limit reached' in full_output or 'Session limit reached' in stderr_output:
                reset_time = self._parse_reset_time(full_output + stderr_output)
                return {
                    'response': full_output,
                    'session_limited': True,
                    'reset_time': reset_time,
                    'files_modified': self._parse_file_changes(full_output),
                    'conversation_id': conversation_id,
                    'metadata': {'success': False, 'reason': 'session_limit'}
                }
            
            if process.returncode != 0:
                return {
                    'response': full_output,
                    'error': stderr_output,
                    'session_limited': False,
                    'files_modified': [],
                    'metadata': {'success': False, 'returncode': process.returncode}
                }
            
            return {
                'response': full_output,
                'session_limited': False,
                'files_modified': self._parse_file_changes(full_output),
                'conversation_id': conversation_id,
                'metadata': {'success': True}
            }
            
        except subprocess.TimeoutExpired:
            return {
                'response': None,
                'error': 'Request timed out after 10 minutes',
                'session_limited': False,
                'files_modified': [],
                'metadata': {'success': False}
            }
        except Exception as e:
            return {
                'response': None,
                'error': str(e),
                'session_limited': False,
                'files_modified': [],
                'metadata': {'success': False}
            }
    
    def send_message_with_file_access_streaming(
        self, 
        prompt: str, 
        project_directory: str,
        conversation_id: Optional[str] = None,
        use_agents: Optional[List[str]] = None,
        **kwargs
    ) -> Generator[str, None, Dict[str, Any]]:
        """
        Same as send_message_with_file_access but yields output in real-time.
        
        Yields:
            Lines of output as they come
            
        Returns:
            Final result dict with metadata
        """
        try:
            enhanced_prompt = self._build_agent_prompt(prompt, use_agents)
            
            cmd = [
                self.cli_command,
                '--dangerously-skip-permissions'
            ]
            
            if conversation_id:
                cmd.extend(['--conversation-id', conversation_id])
            
            cmd.append(enhanced_prompt)
            
            process = subprocess.Popen(
                cmd,
                cwd=project_directory,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            
            output_lines = []
            for line in process.stdout:
                output_lines.append(line)
                yield line  # Stream to caller
            
            process.wait(timeout=600)
            full_output = ''.join(output_lines)
            stderr_output = process.stderr.read()
            
            # Return final result
            if 'Session limit reached' in full_output or 'Session limit reached' in stderr_output:
                reset_time = self._parse_reset_time(full_output + stderr_output)
                return {
                    'response': full_output,
                    'session_limited': True,
                    'reset_time': reset_time,
                    'files_modified': self._parse_file_changes(full_output),
                    'conversation_id': conversation_id
                }
            
            return {
                'response': full_output,
                'session_limited': False,
                'files_modified': self._parse_file_changes(full_output),
                'conversation_id': conversation_id
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'session_limited': False,
                'files_modified': []
            }
    
    def _build_agent_prompt(self, prompt: str, agents: Optional[List[str]]) -> str:
        """Enhance prompt to tell Claude which agents to use."""
        if not agents or len(agents) == 0:
            return prompt
        
        agent_instruction = f"\n\nIMPORTANT: Please use the following agents for this task: {', '.join(agents)}\n\n"
        return agent_instruction + prompt
    
    def _parse_reset_time(self, output: str) -> Optional[str]:
        """Extract session reset time from Claude's message."""
        # Look for patterns like "resets 10pm", "resets at 10:00pm", etc.
        match = re.search(r'resets?\s+(?:at\s+)?(\d+(?::\d+)?(?:\s*)?(?:am|pm|AM|PM)?)', output, re.IGNORECASE)
        if match:
            return match.group(1)
        return None
    
    def _parse_file_changes(self, output: str) -> List[str]:
        """
        Parse Claude's output to find which files were created/modified.
        Claude typically mentions files it's working on.
        """
        # Look for common patterns in Claude's output
        patterns = [
            r'Created (?:file )?[`"\']?([^\s`"\']+\.[a-zA-Z0-9]+)[`"\']?',
            r'Modified [`"\']?([^\s`"\']+\.[a-zA-Z0-9]+)[`"\']?',
            r'Writing to [`"\']?([^\s`"\']+\.[a-zA-Z0-9]+)[`"\']?',
            r'Saved [`"\']?([^\s`"\']+\.[a-zA-Z0-9]+)[`"\']?',
            r'Updated [`"\']?([^\s`"\']+\.[a-zA-Z0-9]+)[`"\']?',
            r'Editing [`"\']?([^\s`"\']+\.[a-zA-Z0-9]+)[`"\']?',
        ]
        
        files = []
        for pattern in patterns:
            matches = re.findall(pattern, output)
            files.extend(matches)
        
        return list(set(files))  # Remove duplicates
    
    def create_plan(self, task_description: str) -> Dict[str, Any]:
        """
        Ask Claude to create a plan for a task.
        
        Args:
            task_description: Description of the task to plan
            
        Returns:
            Dict with plan and metadata
        """
        prompt = f"""You are a software development planning assistant. 
Create a detailed plan for the following task:

{task_description}

Please structure your plan with:
1. Overview
2. Steps (numbered, specific, actionable)
3. Dependencies
4. Potential challenges
5. Success criteria

Be concise but thorough."""

        result = self.send_message(prompt, max_tokens=2048)
        return result
    
    def review_code(self, code: str, context: str = "") -> Dict[str, Any]:
        """
        Ask Claude to review code.
        
        Args:
            code: The code to review
            context: Additional context about the code
            
        Returns:
            Dict with review and metadata
        """
        prompt = f"""You are a code review assistant. Please review the following code:

Context: {context}

Code:
```
{code}
```

Please provide:
1. Code quality assessment
2. Potential bugs or issues
3. Suggestions for improvement
4. Security concerns (if any)
5. Performance considerations

Be constructive and specific."""

        result = self.send_message(prompt, max_tokens=2048)
        return result
    
    def generate_code(self, specification: str, language: str = "python") -> Dict[str, Any]:
        """
        Ask Claude to generate code based on specification.
        
        Args:
            specification: The code specification
            language: Programming language
            
        Returns:
            Dict with code and metadata
        """
        prompt = f"""You are a software development assistant. Generate {language} code for:

{specification}

Please provide:
1. Clean, well-documented code
2. Error handling
3. Comments explaining key logic
4. Any necessary imports

Return only the code, properly formatted."""

        result = self.send_message(prompt, max_tokens=4096)
        return result
    
    def generate_tests(self, code: str, language: str = "python") -> Dict[str, Any]:
        """
        Ask Claude to generate tests for code.
        
        Args:
            code: The code to test
            language: Programming language
            
        Returns:
            Dict with test code and metadata
        """
        prompt = f"""You are a test development assistant. Generate comprehensive unit tests for this {language} code:

```
{code}
```

Please provide:
1. Unit tests covering main functionality
2. Edge case tests
3. Error condition tests
4. Clear test names and documentation

Use pytest for Python. Return only the test code."""

        result = self.send_message(prompt, max_tokens=4096)
        return result

