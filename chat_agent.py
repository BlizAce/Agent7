"""
Chat Agent - Conversational interface for Agent7.

Allows users to chat with LM Studio which can:
- Answer questions
- Create tasks
- Execute tasks
- Provide project status
"""
import re
from typing import Dict, Any, Optional, List
from local_llm_client import LocalLLMClient
from database import Database


class ChatAgent:
    """
    Conversational agent that can chat with users and manage tasks.
    """
    
    def __init__(self, llm_client: LocalLLMClient, db: Database):
        """
        Initialize chat agent.
        
        Args:
            llm_client: LM Studio client
            db: Database for task management
        """
        self.llm = llm_client
        self.db = db
        self.conversation_history = []
    
    def get_system_prompt(self) -> str:
        """
        Get system prompt for chat mode.
        
        Returns:
            System prompt string
        """
        return """You are Agent7's conversational assistant - a helpful AI that manages software development tasks.

Your capabilities:
1. **Chat**: Have natural conversations with users about their projects
2. **Create Tasks**: Parse user requests and create tasks
3. **Execute Tasks**: Trigger task execution when appropriate
4. **Status**: Provide updates on project status and task progress
5. **Guidance**: Help users structure their work effectively

TASK MANAGEMENT COMMANDS:
When the user wants to create or execute tasks, you MUST respond with special commands.

⚠️ CRITICAL: You MUST include the full JSON block after the command label. Just saying "CREATE_TASK:" without the JSON will NOT work!

CORRECT FORMAT for CREATE_TASK:
```json
{
    "action": "create_task",
    "title": "Task title here",
    "type": "coding",
    "description": "Detailed description of what to do",
    "priority": 1
}
```

CORRECT FORMAT for EXECUTE_TASK:
```json
{
    "action": "execute_task",
    "task_id": 123
}
```

CORRECT FORMAT for LIST_TASKS:
```json
{
    "action": "list_tasks",
    "filter": "all"
}
```

⚠️ DO NOT just say "CREATE_TASK:" without the JSON block!
⚠️ ALWAYS include the complete JSON object in a ```json code block!

EXAMPLES:

User: "I want to create a Pong game"
You: I'll help you create that! Let me set up the tasks.

CREATE_TASK:
```json
{
    "action": "create_task",
    "title": "Plan Pong Game",
    "type": "planning",
    "description": "Create detailed plan for Pong game with requirements, architecture, and TODO list",
    "priority": 1
}
```

I've created a planning task. Once this completes, we'll have a comprehensive plan to follow. Should I execute it now?

---

User: "Yes, execute it"
You: EXECUTE_TASK:
```json
{
    "action": "execute_task",
    "task_id": 1
}
```

Task execution started! I'll let you know when it's complete.

---

User: "What tasks do we have?"
You: LIST_TASKS:
```json
{
    "action": "list_tasks",
    "filter": "all"
}
```

---

Be conversational, helpful, and proactive. When users describe what they want, create appropriate tasks automatically.

Break large projects into phases:
1. Planning task first (creates PLAN.md, TODO.md)
2. Then coding tasks for each phase
3. Finally testing tasks

Always confirm before executing tasks."""
    
    def send_message(
        self,
        user_message: str,
        project_directory: Optional[str] = None,
        project_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Process a chat message from the user.
        
        Args:
            user_message: User's message
            project_directory: Current project directory (optional)
            
        Returns:
            Dict with 'response', 'actions', and 'metadata'
        """
        # Add user message to history
        self.conversation_history.append({
            'role': 'user',
            'content': user_message
        })
        
        # Build context
        context = ""
        if project_directory:
            context += f"\nCurrent project: {project_directory}"
        
        # Get recent tasks
        all_tasks = self.db.list_tasks()
        tasks = all_tasks[:5] if all_tasks else []
        if tasks:
            context += f"\n\nRecent tasks:"
            for task in tasks:
                context += f"\n- [{task['id']}] {task['title']} ({task['status']})"
        
        # Send to LM Studio
        full_message = user_message
        if context:
            full_message += f"\n\nContext:{context}"
        
        response = self.llm.send_message(
            full_message,
            system_prompt=self.get_system_prompt(),
            temperature=0.7,
            max_tokens=1024,
            history=self.conversation_history
        )
        
        if not response.get('response'):
            return {
                'response': "I'm sorry, I couldn't process that. Is LM Studio running?",
                'actions': [],
                'error': response.get('error')
            }
        
        assistant_response = response['response']
        
        # Add to history
        self.conversation_history.append({
            'role': 'assistant',
            'content': assistant_response
        })
        
        # Parse actions from response
        actions = self.parse_actions(assistant_response)
        
        # Check if fallback parsing was used
        used_fallback = '```json' not in assistant_response and len(actions) > 0
        
        # Add project_id to actions if provided
        if project_id:
            for action in actions:
                if action.get('action') == 'create_task':
                    action['project_id'] = project_id
        
        # Execute actions
        action_results = []
        for action in actions:
            result = self.execute_action(action)
            
            # Add note if fallback parsing was used
            if used_fallback and result.get('success'):
                result['note'] = '(Auto-extracted from conversation)'
            
            action_results.append(result)
        
        # Clean response (remove action JSON from display)
        display_response = self.clean_response(assistant_response)
        
        return {
            'response': display_response,
            'actions': action_results,
            'metadata': {
                'success': True,
                'actions_count': len(actions)
            }
        }
    
    def parse_actions(self, response: str) -> List[Dict[str, Any]]:
        """
        Parse action commands from LM Studio's response.
        
        Args:
            response: LM Studio's response
            
        Returns:
            List of action dictionaries
        """
        actions = []
        
        # Look for JSON action blocks
        # Pattern: ```json\n{...}\n```
        pattern = r'```json\s*\n(.*?)\n```'
        matches = re.findall(pattern, response, re.DOTALL)
        
        for match in matches:
            try:
                import json
                action = json.loads(match)
                if 'action' in action:
                    actions.append(action)
            except json.JSONDecodeError:
                continue
        
        # FALLBACK: If no JSON found but keywords present, try to extract intent
        if not actions:
            actions.extend(self._parse_fallback_actions(response))
        
        return actions
    
    def _parse_fallback_actions(self, response: str) -> List[Dict[str, Any]]:
        """
        Fallback parser for when LM Studio mentions actions but doesn't format JSON.
        
        Args:
            response: LM Studio's response
            
        Returns:
            List of extracted action dictionaries
        """
        actions = []
        import json
        
        # Look for "CREATE_TASK:" without JSON
        if 'CREATE_TASK:' in response or 'create a task' in response.lower():
            # Try to extract task details from surrounding text
            lines = response.split('\n')
            task_info = {
                'action': 'create_task',
                'title': 'Extracted Task',
                'type': 'coding',
                'description': '',
                'priority': 1
            }
            
            # Look for common patterns
            for i, line in enumerate(lines):
                line_lower = line.lower()
                
                # Extract title from patterns like "Define Color Constants" or "Fix the BLACK error"
                if 'define' in line_lower or 'fix' in line_lower or 'create' in line_lower or 'add' in line_lower:
                    # Remove common prefixes
                    clean_line = line.strip()
                    for prefix in ['I\'ll ', 'Let\'s ', 'We should ', 'I will ', 'We\'ll ']:
                        if clean_line.startswith(prefix):
                            clean_line = clean_line[len(prefix):]
                    
                    # Remove trailing punctuation
                    clean_line = clean_line.rstrip('.!?')
                    
                    if len(clean_line) > 5 and len(clean_line) < 100:
                        task_info['title'] = clean_line[:80]  # Limit length
                        break
            
            # Extract description from context
            if 'error' in response.lower() or 'traceback' in response.lower():
                task_info['description'] = 'Fix error identified in conversation'
                task_info['title'] = task_info.get('title', 'Fix Error')
            
            # Look for specific mentions
            if 'color' in response.lower() and 'constant' in response.lower():
                task_info['title'] = 'Define Color Constants'
                task_info['description'] = 'Define missing color constants like BLACK, WHITE, etc.'
            
            if task_info['title'] != 'Extracted Task':
                actions.append(task_info)
        
        # Look for "EXECUTE_TASK:" without JSON
        if 'EXECUTE_TASK:' in response or 'execute' in response.lower():
            # Try to find task ID in conversation history
            # Look for recent task creation
            if len(self.conversation_history) >= 2:
                # Check last few messages for task IDs
                for msg in reversed(self.conversation_history[-5:]):
                    content = msg.get('content', '')
                    # Look for "task #N" or "task N"
                    match = re.search(r'task\s*#?(\d+)', content, re.IGNORECASE)
                    if match:
                        task_id = int(match.group(1))
                        actions.append({
                            'action': 'execute_task',
                            'task_id': task_id
                        })
                        break
        
        return actions
    
    def execute_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute an action requested by the chat agent.
        
        Args:
            action: Action dictionary
            
        Returns:
            Result of action execution
        """
        action_type = action.get('action')
        
        if action_type == 'create_task':
            return self.action_create_task(action)
        elif action_type == 'execute_task':
            return self.action_execute_task(action)
        elif action_type == 'list_tasks':
            return self.action_list_tasks(action)
        else:
            return {
                'success': False,
                'action': action_type,
                'error': f"Unknown action: {action_type}"
            }
    
    def action_create_task(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new task.
        
        Args:
            action: Action details
            
        Returns:
            Result with task_id
        """
        try:
            # Use provided project_id or default to 1
            proj_id = action.get('project_id', 1)
            
            task_id = self.db.create_task(
                project_id=proj_id,
                title=action.get('title', 'Untitled Task'),
                description=action.get('description', ''),
                task_type=action.get('type', 'coding'),
                priority=action.get('priority', 0)
            )
            
            return {
                'success': True,
                'action': 'create_task',
                'task_id': task_id,
                'title': action.get('title'),
                'message': f"Created task #{task_id}: {action.get('title')}"
            }
        except Exception as e:
            return {
                'success': False,
                'action': 'create_task',
                'error': str(e)
            }
    
    def action_execute_task(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """
        Request task execution.
        
        Args:
            action: Action details with task_id
            
        Returns:
            Result indicating execution requested
        """
        task_id = action.get('task_id')
        
        if not task_id:
            return {
                'success': False,
                'action': 'execute_task',
                'error': 'No task_id provided'
            }
        
        # Check if task exists
        task = self.db.get_task(task_id)
        if not task:
            return {
                'success': False,
                'action': 'execute_task',
                'error': f"Task #{task_id} not found"
            }
        
        return {
            'success': True,
            'action': 'execute_task',
            'task_id': task_id,
            'message': f"Execution requested for task #{task_id}: {task['title']}",
            'execute': True  # Signal to web server to execute
        }
    
    def action_list_tasks(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """
        List tasks with optional filter.
        
        Args:
            action: Action details with optional filter
            
        Returns:
            Result with task list
        """
        filter_type = action.get('filter', 'all')
        
        # Get tasks (limited to 20 most recent)
        all_tasks = self.db.list_tasks()[:20]
        
        # Filter if needed
        if filter_type != 'all':
            filtered_tasks = [t for t in all_tasks if t['status'] == filter_type]
        else:
            filtered_tasks = all_tasks
        
        return {
            'success': True,
            'action': 'list_tasks',
            'tasks': filtered_tasks,
            'count': len(filtered_tasks),
            'message': f"Found {len(filtered_tasks)} tasks"
        }
    
    def clean_response(self, response: str) -> str:
        """
        Remove action JSON blocks from response for display.
        
        Args:
            response: Full response with action blocks
            
        Returns:
            Clean response without JSON blocks
        """
        # Remove ```json...``` blocks
        pattern = r'```json\s*\n.*?\n```'
        cleaned = re.sub(pattern, '', response, flags=re.DOTALL)
        
        # Remove empty lines
        lines = [line for line in cleaned.split('\n') if line.strip()]
        
        return '\n'.join(lines).strip()
    
    def reset_conversation(self):
        """Reset conversation history."""
        self.conversation_history = []

