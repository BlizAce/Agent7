"""
Orchestration Brain - Uses LM Studio to manage Claude CLI tasks.
"""
import re
from typing import Dict, List, Optional, Any
from local_llm_client import LocalLLMClient


class OrchestrationBrain:
    """
    Uses local LLM (LM Studio) to orchestrate Claude CLI tasks.
    The brain decides what prompts to send to Claude, which agents to use,
    and validates Claude's work.
    """
    
    def __init__(self, local_llm: LocalLLMClient):
        """
        Initialize orchestration brain.
        
        Args:
            local_llm: Local LLM client (LM Studio)
        """
        self.local_llm = local_llm
    
    def create_claude_prompt_for_task(
        self, 
        task_description: str,
        task_type: str,
        project_context: str = "",
        previous_work: Optional[str] = None,
        files_in_project: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Use LM Studio to create an optimal prompt for Claude.
        
        Args:
            task_description: Description of the task
            task_type: Type of task (planning, coding, testing)
            project_context: Context about the project
            previous_work: Any previous work done
            files_in_project: List of existing files in project
            
        Returns:
            Dict with 'agents', 'prompt', 'validation_criteria'
        """
        
        files_context = ""
        if files_in_project:
            files_context = f"\n\nExisting files in project:\n" + "\n".join(files_in_project)
        
        prev_work = ""
        if previous_work:
            prev_work = f"\n\nPrevious work completed:\n{previous_work}"
        
        meta_prompt = f"""You are an AI orchestration system managing Claude AI. Your job is to create 
a detailed, clear prompt that will help Claude accomplish this task effectively.

Task Type: {task_type}
Task Description: {task_description}

Project Context: {project_context}{files_context}{prev_work}

Create instructions for Claude that:
1. Specify which Claude agents to use (options: coding, testing, review, planning, analysis)
2. Give clear, actionable instructions
3. Specify any file operations needed (Claude will have file access)
4. Include validation criteria for checking success
5. Be specific about expected outputs

CRITICAL: In your PROMPT, tell Claude to format ANY file creation/modification like this:
File: filename.ext
```language
code content
```

This format is REQUIRED so our system can automatically create the files.

Claude also has access to PROJECT EXPLORATION TOOLS:
- list_files(path, extensions) - List files in directory
- read_file(filepath, start_line, end_line) - Read file contents
- search_in_files(pattern, extensions) - Search for text/patterns
- find_files(name_pattern) - Find files by name
- find_definitions(name, type) - Find functions/classes
- get_project_structure(max_depth) - Get directory tree
- get_file_info(filepath) - Get file metadata

Tell Claude to request tools explicitly like: "TOOL: read_file(filepath='main.py')"
or naturally like: "I need to use read_file on main.py to understand the structure"

IMPORTANT: Format your response EXACTLY as follows:

AGENTS: [comma-separated list of agent names]
PROMPT: [the actual detailed prompt to send to Claude - MUST include file format instructions]
VALIDATION: [criteria to check if task was completed successfully]

Be concise but specific. Claude will run with --dangerously-skip-permissions so it can create/modify files."""
        
        response = self.local_llm.send_message(
            meta_prompt,
            system_prompt="You are an expert at orchestrating AI systems for software development.",
            temperature=0.3,
            max_tokens=2048
        )
        
        if not response.get('response'):
            # Fallback if LM Studio fails
            return self._create_fallback_prompt(task_description, task_type)
        
        return self._parse_orchestration_response(response['response'], task_type)
    
    def _create_fallback_prompt(self, task_description: str, task_type: str) -> Dict[str, Any]:
        """Create a fallback prompt if LM Studio fails."""
        agent_map = {
            'planning': ['planning', 'analysis'],
            'coding': ['coding'],
            'testing': ['testing', 'coding']
        }
        
        return {
            'agents': agent_map.get(task_type, ['coding']),
            'prompt': task_description,
            'validation_criteria': f"Task completed successfully for {task_type}"
        }
    
    def _parse_orchestration_response(self, response: str, task_type: str) -> Dict[str, Any]:
        """Parse the structured response from LM Studio."""
        result = {
            'agents': [],
            'prompt': '',
            'validation_criteria': ''
        }
        
        # Extract AGENTS
        agents_match = re.search(r'AGENTS:\s*([^\n]+)', response, re.IGNORECASE)
        if agents_match:
            agents_str = agents_match.group(1).strip()
            # Remove brackets and split
            agents_str = agents_str.strip('[]')
            result['agents'] = [a.strip() for a in agents_str.split(',')]
        else:
            # Default agents based on task type
            result['agents'] = ['coding'] if task_type == 'coding' else ['planning']
        
        # Extract PROMPT
        prompt_match = re.search(r'PROMPT:\s*(.+?)(?=\nVALIDATION:|$)', response, re.IGNORECASE | re.DOTALL)
        if prompt_match:
            result['prompt'] = prompt_match.group(1).strip()
        else:
            # If parsing fails, use the whole response as prompt
            result['prompt'] = response
        
        # Extract VALIDATION
        validation_match = re.search(r'VALIDATION:\s*(.+?)$', response, re.IGNORECASE | re.DOTALL)
        if validation_match:
            result['validation_criteria'] = validation_match.group(1).strip()
        else:
            result['validation_criteria'] = "Check if task objectives were met"
        
        return result
    
    def determine_required_agents(self, task_type: str, task_description: str) -> List[str]:
        """
        Determine which Claude agents are needed for a task.
        
        Args:
            task_type: Type of task
            task_description: Description of the task
            
        Returns:
            List of agent names
        """
        prompt = f"""Given this task, which Claude AI agents should be used?

Task Type: {task_type}
Description: {task_description}

Available agents: coding, testing, review, planning, analysis

Return ONLY a comma-separated list of agent names, nothing else."""
        
        response = self.local_llm.send_message(
            prompt,
            temperature=0.1,
            max_tokens=100
        )
        
        if response.get('response'):
            agents_str = response['response'].strip().lower()
            return [a.strip() for a in agents_str.split(',')]
        
        # Default fallback
        agent_map = {
            'planning': ['planning', 'analysis'],
            'coding': ['coding'],
            'testing': ['testing']
        }
        return agent_map.get(task_type, ['coding'])
    
    def validate_claude_work(
        self, 
        task_type: str,
        task_description: str,
        claude_output: str,
        files_modified: List[str],
        expected_criteria: str
    ) -> Dict[str, Any]:
        """
        Use LM Studio to validate Claude's work.
        
        Args:
            task_type: Type of task that was performed
            task_description: Original task description
            claude_output: Claude's response/output
            files_modified: List of files Claude created/modified
            expected_criteria: Expected validation criteria
            
        Returns:
            Dict with 'status', 'issues', 'next_action', 'confidence'
        """
        
        files_list = "\n".join(files_modified) if files_modified else "None detected"
        
        validation_prompt = f"""Review the work Claude AI just completed:

Task Type: {task_type}
Original Task: {task_description}

Claude's Output:
{claude_output[:2000]}  # Limit to avoid token issues

Files Modified: 
{files_list}

Expected Criteria: {expected_criteria}

Analyze and determine:
1. Was the task completed successfully?
2. Were appropriate files created/modified?
3. Are there any issues or concerns?
4. Should we continue or does Claude need to make revisions?

Format your response as:
STATUS: [COMPLETE|NEEDS_REVISION|FAILED]
CONFIDENCE: [0-100]
ISSUES: [list any problems, or "None"]
NEXT_ACTION: [what should happen next]
"""
        
        response = self.local_llm.send_message(
            validation_prompt,
            system_prompt="You are a quality assurance expert reviewing AI-generated work.",
            temperature=0.2,
            max_tokens=1024
        )
        
        if not response.get('response'):
            # Fallback: assume success if no validation possible
            return {
                'status': 'COMPLETE',
                'confidence': 50,
                'issues': ['Could not validate - LM Studio unavailable'],
                'next_action': 'Manual review recommended'
            }
        
        return self._parse_validation_response(response['response'])
    
    def _parse_validation_response(self, response: str) -> Dict[str, Any]:
        """Parse validation response from LM Studio."""
        result = {
            'status': 'COMPLETE',
            'confidence': 70,
            'issues': [],
            'next_action': 'Continue'
        }
        
        # Extract STATUS
        status_match = re.search(r'STATUS:\s*(\w+)', response, re.IGNORECASE)
        if status_match:
            result['status'] = status_match.group(1).upper()
        
        # Extract CONFIDENCE
        confidence_match = re.search(r'CONFIDENCE:\s*(\d+)', response, re.IGNORECASE)
        if confidence_match:
            result['confidence'] = int(confidence_match.group(1))
        
        # Extract ISSUES
        issues_match = re.search(r'ISSUES:\s*(.+?)(?=\nNEXT_ACTION:|$)', response, re.IGNORECASE | re.DOTALL)
        if issues_match:
            issues_text = issues_match.group(1).strip()
            if issues_text.lower() != 'none':
                # Split by newlines or bullets
                issues = [i.strip('- •\t') for i in issues_text.split('\n') if i.strip()]
                result['issues'] = issues
        
        # Extract NEXT_ACTION
        action_match = re.search(r'NEXT_ACTION:\s*(.+?)$', response, re.IGNORECASE | re.DOTALL)
        if action_match:
            result['next_action'] = action_match.group(1).strip()
        
        return result
    
    def validate_test_results(
        self,
        test_output: str,
        tests_passed: bool,
        task_description: str
    ) -> Dict[str, Any]:
        """
        Validate test execution results using LM Studio.
        
        Args:
            test_output: Output from test execution
            tests_passed: Whether tests passed
            task_description: Original task description
            
        Returns:
            Dict with validation assessment
        """
        
        validation_prompt = f"""Review these test execution results:

Task: {task_description}

Test Output:
{test_output[:1500]}

Tests Passed: {tests_passed}

Evaluate:
1. Are the tests comprehensive?
2. Do the results make sense?
3. Are there any red flags?
4. Should we accept these results or investigate further?

Format response as:
ASSESSMENT: [ACCEPTABLE|NEEDS_INVESTIGATION|INSUFFICIENT]
REASONING: [brief explanation]
RECOMMENDATIONS: [any suggestions]
"""
        
        response = self.local_llm.send_message(
            validation_prompt,
            temperature=0.2,
            max_tokens=512
        )
        
        if not response.get('response'):
            return {
                'assessment': 'ACCEPTABLE' if tests_passed else 'NEEDS_INVESTIGATION',
                'reasoning': 'Default assessment - validation unavailable',
                'recommendations': []
            }
        
        return self._parse_test_validation(response['response'], tests_passed)
    
    def _parse_test_validation(self, response: str, tests_passed: bool) -> Dict[str, Any]:
        """Parse test validation response."""
        result = {
            'assessment': 'ACCEPTABLE' if tests_passed else 'NEEDS_INVESTIGATION',
            'reasoning': '',
            'recommendations': []
        }
        
        # Extract ASSESSMENT
        assessment_match = re.search(r'ASSESSMENT:\s*(\w+)', response, re.IGNORECASE)
        if assessment_match:
            result['assessment'] = assessment_match.group(1).upper()
        
        # Extract REASONING
        reasoning_match = re.search(r'REASONING:\s*(.+?)(?=\nRECOMMENDATIONS:|$)', response, re.IGNORECASE | re.DOTALL)
        if reasoning_match:
            result['reasoning'] = reasoning_match.group(1).strip()
        
        # Extract RECOMMENDATIONS
        rec_match = re.search(r'RECOMMENDATIONS:\s*(.+?)$', response, re.IGNORECASE | re.DOTALL)
        if rec_match:
            rec_text = rec_match.group(1).strip()
            recommendations = [r.strip('- •\t') for r in rec_text.split('\n') if r.strip()]
            result['recommendations'] = recommendations
        
        return result
    
    def decide_next_action(
        self,
        current_state: Dict[str, Any],
        task_history: List[Dict[str, Any]]
    ) -> str:
        """
        Decide what action to take next based on current state.
        
        Args:
            current_state: Current task state
            task_history: History of actions taken
            
        Returns:
            Action to take: 'continue', 'complete', 'retry', 'fail'
        """
        
        history_summary = "\n".join([
            f"- {h.get('action', 'unknown')}: {h.get('result', 'unknown')}"
            for h in task_history[-5:]  # Last 5 actions
        ])
        
        decision_prompt = f"""Based on the current state of a task, decide what to do next.

Current State:
Status: {current_state.get('status', 'unknown')}
Confidence: {current_state.get('confidence', 0)}%
Issues: {current_state.get('issues', [])}

Recent History:
{history_summary}

What should we do next?
- CONTINUE: Keep working on the task
- COMPLETE: Task is done successfully
- RETRY: Try again with different approach
- FAIL: Task cannot be completed

Return ONLY one word: CONTINUE, COMPLETE, RETRY, or FAIL"""
        
        response = self.local_llm.send_message(
            decision_prompt,
            temperature=0.1,
            max_tokens=50
        )
        
        if response.get('response'):
            decision = response['response'].strip().upper()
            if decision in ['CONTINUE', 'COMPLETE', 'RETRY', 'FAIL']:
                return decision.lower()
        
        # Default fallback based on status
        status = current_state.get('status', 'UNKNOWN').upper()
        if status == 'COMPLETE':
            return 'complete'
        elif status == 'FAILED':
            return 'fail'
        else:
            return 'continue'


