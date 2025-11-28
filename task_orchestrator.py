"""
Task orchestration engine for managing planning, coding, and testing workflows.
"""
import time
import os
from typing import Optional, Dict, Any, List
from database import Database
from claude_client import ClaudeClient
from local_llm_client import LocalLLMClient
from orchestration_brain import OrchestrationBrain
from session_manager import SessionManager
from test_runner import TestRunner


class TaskOrchestrator:
    """Orchestrates tasks using Claude CLI and/or local LLM."""
    
    def __init__(self, db: Database, 
                 claude_client: Optional[ClaudeClient] = None,
                 local_llm_client: Optional[LocalLLMClient] = None,
                 prefer_local: bool = False,
                 orchestration_brain: Optional[OrchestrationBrain] = None,
                 session_manager: Optional[SessionManager] = None,
                 test_runner: Optional[TestRunner] = None):
        """
        Initialize task orchestrator.
        
        Args:
            db: Database instance
            claude_client: Optional Claude CLI client
            local_llm_client: Optional local LLM client
            prefer_local: Prefer local LLM over Claude when both available
            orchestration_brain: Optional orchestration brain for intelligent task management
            session_manager: Optional session manager for handling Claude limits
            test_runner: Optional test runner for executing tests
        """
        self.db = db
        self.claude = claude_client
        self.local_llm = local_llm_client
        self.prefer_local = prefer_local
        
        # Initialize enhanced components
        self.brain = orchestration_brain or (OrchestrationBrain(local_llm_client) if local_llm_client else None)
        self.session_manager = session_manager or SessionManager(db)
        self.test_runner = test_runner or TestRunner(db)
    
    def _get_client(self, prefer_claude: bool = False):
        """
        Get the appropriate client based on availability and preference.
        
        Args:
            prefer_claude: Prefer Claude over local LLM for this request
            
        Returns:
            Tuple of (client, client_type)
        """
        if prefer_claude:
            if self.claude:
                return self.claude, "claude_cli"
            elif self.local_llm and self.local_llm.check_availability():
                return self.local_llm, "local_llm"
        else:
            if self.prefer_local and self.local_llm and self.local_llm.check_availability():
                return self.local_llm, "local_llm"
            elif self.claude:
                return self.claude, "claude_cli"
            elif self.local_llm:
                return self.local_llm, "local_llm"
        
        return None, None
    
    def execute_planning_task(self, task_id: int) -> bool:
        """
        Execute a planning task.
        
        Args:
            task_id: Task ID
            
        Returns:
            True if successful, False otherwise
        """
        task = self.db.get_task(task_id)
        if not task:
            print(f"Task {task_id} not found")
            return False
        
        print(f"🎯 Planning: {task['title']}")
        self.db.update_task_status(task_id, 'in_progress')
        
        client, client_type = self._get_client(prefer_claude=True)
        if not client:
            print("❌ No LLM client available")
            self.db.update_task_status(task_id, 'failed')
            return False
        
        try:
            # Create plan
            if client_type == "claude_cli":
                result = client.create_plan(task['description'])
            else:
                system_prompt = "You are a software planning expert. Create detailed, actionable plans."
                result = client.send_message(
                    f"Create a detailed plan for: {task['description']}\n\n"
                    "Include: Overview, Steps, Dependencies, Challenges, Success Criteria",
                    system_prompt=system_prompt
                )
            
            if result.get('response'):
                # Save conversation
                self.db.save_conversation(
                    task_id,
                    client_type,
                    task['description'],
                    result['response'],
                    result.get('metadata')
                )
                
                # Save result
                self.db.save_result(
                    task_id,
                    'plan',
                    result['response'],
                    {'client': client_type}
                )
                
                self.db.update_task_status(task_id, 'completed')
                print("✅ Planning completed")
                return True
            else:
                error = result.get('error', 'Unknown error')
                print(f"❌ Planning failed: {error}")
                self.db.save_result(task_id, 'error', error)
                self.db.update_task_status(task_id, 'failed')
                return False
                
        except Exception as e:
            print(f"❌ Error during planning: {e}")
            self.db.save_result(task_id, 'error', str(e))
            self.db.update_task_status(task_id, 'failed')
            return False
    
    def execute_coding_task(self, task_id: int, language: str = "python") -> bool:
        """
        Execute a coding task.
        
        Args:
            task_id: Task ID
            language: Programming language
            
        Returns:
            True if successful, False otherwise
        """
        task = self.db.get_task(task_id)
        if not task:
            print(f"Task {task_id} not found")
            return False
        
        print(f"💻 Coding: {task['title']}")
        self.db.update_task_status(task_id, 'in_progress')
        
        client, client_type = self._get_client()
        if not client:
            print("❌ No LLM client available")
            self.db.update_task_status(task_id, 'failed')
            return False
        
        try:
            # Generate code
            if client_type == "claude_cli":
                result = client.generate_code(task['description'], language)
            else:
                result = client.code_generation(task['description'], language)
            
            if result.get('response'):
                # Save conversation
                self.db.save_conversation(
                    task_id,
                    client_type,
                    task['description'],
                    result['response'],
                    result.get('metadata')
                )
                
                # Save result
                self.db.save_result(
                    task_id,
                    'code',
                    result['response'],
                    {'client': client_type, 'language': language}
                )
                
                self.db.update_task_status(task_id, 'completed')
                print("✅ Code generation completed")
                return True
            else:
                error = result.get('error', 'Unknown error')
                print(f"❌ Code generation failed: {error}")
                self.db.save_result(task_id, 'error', error)
                self.db.update_task_status(task_id, 'failed')
                return False
                
        except Exception as e:
            print(f"❌ Error during coding: {e}")
            self.db.save_result(task_id, 'error', str(e))
            self.db.update_task_status(task_id, 'failed')
            return False
    
    def execute_testing_task(self, task_id: int, language: str = "python") -> bool:
        """
        Execute a testing task.
        
        Args:
            task_id: Task ID
            language: Programming language
            
        Returns:
            True if successful, False otherwise
        """
        task = self.db.get_task(task_id)
        if not task:
            print(f"Task {task_id} not found")
            return False
        
        print(f"🧪 Testing: {task['title']}")
        self.db.update_task_status(task_id, 'in_progress')
        
        # Get the code to test from description or previous results
        code_to_test = task['description']
        
        client, client_type = self._get_client()
        if not client:
            print("❌ No LLM client available")
            self.db.update_task_status(task_id, 'failed')
            return False
        
        try:
            # Generate tests
            if client_type == "claude_cli":
                result = client.generate_tests(code_to_test, language)
            else:
                system_prompt = f"You are a test development expert for {language}. Generate comprehensive tests."
                result = client.send_message(
                    f"Generate unit tests for this {language} code:\n\n{code_to_test}\n\n"
                    "Include: unit tests, edge cases, error conditions. Use pytest for Python.",
                    system_prompt=system_prompt,
                    temperature=0.3
                )
            
            if result.get('response'):
                # Save conversation
                self.db.save_conversation(
                    task_id,
                    client_type,
                    code_to_test,
                    result['response'],
                    result.get('metadata')
                )
                
                # Save result
                self.db.save_result(
                    task_id,
                    'test',
                    result['response'],
                    {'client': client_type, 'language': language}
                )
                
                self.db.update_task_status(task_id, 'completed')
                print("✅ Test generation completed")
                return True
            else:
                error = result.get('error', 'Unknown error')
                print(f"❌ Test generation failed: {error}")
                self.db.save_result(task_id, 'error', error)
                self.db.update_task_status(task_id, 'failed')
                return False
                
        except Exception as e:
            print(f"❌ Error during testing: {e}")
            self.db.save_result(task_id, 'error', str(e))
            self.db.update_task_status(task_id, 'failed')
            return False
    
    def execute_task(self, task_id: int, language: str = "python") -> bool:
        """
        Execute a task based on its type.
        
        Args:
            task_id: Task ID
            language: Programming language (for coding/testing tasks)
            
        Returns:
            True if successful, False otherwise
        """
        task = self.db.get_task(task_id)
        if not task:
            return False
        
        task_type = task['task_type']
        
        if task_type == 'planning':
            return self.execute_planning_task(task_id)
        elif task_type == 'coding':
            return self.execute_coding_task(task_id, language)
        elif task_type == 'testing':
            return self.execute_testing_task(task_id, language)
        else:
            print(f"❌ Unknown task type: {task_type}")
            return False
    
    def execute_workflow(self, project_id: int, language: str = "python") -> Dict[str, Any]:
        """
        Execute a complete workflow: planning -> coding -> testing.
        
        Args:
            project_id: Project ID
            language: Programming language
            
        Returns:
            Dict with workflow results
        """
        tasks = self.db.list_tasks(project_id=project_id, status='pending')
        
        results = {
            'total': len(tasks),
            'completed': 0,
            'failed': 0,
            'task_results': []
        }
        
        # Sort tasks by type: planning first, then coding, then testing
        type_order = {'planning': 0, 'coding': 1, 'testing': 2}
        tasks.sort(key=lambda t: (type_order.get(t['task_type'], 99), t['priority']))
        
        for task in tasks:
            print(f"\n{'='*60}")
            success = self.execute_task(task['id'], language)
            
            results['task_results'].append({
                'task_id': task['id'],
                'title': task['title'],
                'type': task['task_type'],
                'success': success
            })
            
            if success:
                results['completed'] += 1
            else:
                results['failed'] += 1
            
            # Small delay between tasks
            time.sleep(1)
        
        print(f"\n{'='*60}")
        print(f"✨ Workflow complete: {results['completed']}/{results['total']} tasks successful")
        
        return results
    
    def execute_task_with_file_access(
        self, 
        task_id: int,
        project_directory: str,
        language: str = "python"
    ) -> Dict[str, Any]:
        """
        Execute a task with full orchestration: brain planning, Claude with file access,
        session management, and test execution.
        
        Args:
            task_id: Task ID
            project_directory: Project directory path
            language: Programming language
            
        Returns:
            Dict with execution results
        """
        task = self.db.get_task(task_id)
        if not task:
            return {'success': False, 'error': 'Task not found'}
        
        print(f"🚀 Executing task: {task['title']}")
        print(f"📁 Project: {project_directory}")
        
        self.db.update_task_status(task_id, 'in_progress')
        
        try:
            # Get list of files in project for context
            files_in_project = []
            if os.path.exists(project_directory):
                for root, dirs, files in os.walk(project_directory):
                    dirs[:] = [d for d in dirs if not d.startswith('.')]
                    for f in files:
                        if not f.startswith('.'):
                            rel_path = os.path.relpath(os.path.join(root, f), project_directory)
                            files_in_project.append(rel_path)
            
            # Use orchestration brain to create optimal prompt
            print("🧠 Planning approach with LM Studio...")
            if self.brain:
                orchestration = self.brain.create_claude_prompt_for_task(
                    task['description'],
                    task['task_type'],
                    f"Working in: {project_directory}",
                    files_in_project=files_in_project[:50]  # Limit to avoid token issues
                )
                print(f"✅ Using agents: {', '.join(orchestration['agents'])}")
            else:
                # Fallback if no brain
                orchestration = {
                    'agents': [task['task_type']],
                    'prompt': task['description'],
                    'validation_criteria': 'Task completed successfully'
                }
            
            # Execute with Claude using file access
            print("🤖 Launching Claude CLI with file access...")
            result = self.claude.send_message_with_file_access(
                prompt=orchestration['prompt'],
                project_directory=project_directory,
                use_agents=orchestration['agents']
            )
            
            # Check for session limit
            if result.get('session_limited'):
                reset_time = result.get('reset_time', '10pm')
                print(f"⏸️  Session limit reached. Scheduling resume at {reset_time}")
                
                self.session_manager.schedule_resume(
                    task_id=task_id,
                    reset_time_str=reset_time,
                    conversation_id=result.get('conversation_id', ''),
                    project_directory=project_directory,
                    remaining_prompt=orchestration['prompt']
                )
                
                self.db.update_task_status(task_id, 'pending')
                return {
                    'success': False,
                    'scheduled': True,
                    'reset_time': reset_time
                }
            
            # Save conversation
            self.db.save_conversation(
                task_id,
                'claude_cli',
                orchestration['prompt'],
                result.get('response', ''),
                result.get('metadata')
            )
            
            # Save file modifications
            files_modified = result.get('files_modified', [])
            for filepath in files_modified:
                self.db.save_file_modification(task_id, filepath, 'modified')
            
            if files_modified:
                print(f"📝 Files modified: {', '.join(files_modified)}")
            
            # Execute tests if applicable
            test_passed = True
            if task['task_type'] in ['coding', 'testing']:
                print("\n🧪 Running tests...")
                test_results = self.test_runner.execute_pytest(project_directory)
                test_summary = self.test_runner.format_results_summary(test_results)
                print(test_summary)
                
                test_passed = test_results.get('passed', False)
                
                # Validate tests with brain
                if self.brain:
                    print("\n🧠 Validating test results with LM Studio...")
                    test_validation = self.brain.validate_test_results(
                        test_results.get('full_output', ''),
                        test_passed,
                        task['description']
                    )
                    print(f"Assessment: {test_validation['assessment']}")
                    
                    if test_validation['recommendations']:
                        print("Recommendations:")
                        for rec in test_validation['recommendations']:
                            print(f"  • {rec}")
            
            # Validate Claude's work with brain
            validation = {'status': 'COMPLETE', 'confidence': 70, 'issues': []}
            if self.brain:
                print("\n🧠 Validating results with LM Studio...")
                validation = self.brain.validate_claude_work(
                    task['task_type'],
                    task['description'],
                    result.get('response', ''),
                    files_modified,
                    orchestration['validation_criteria']
                )
                
                print(f"Status: {validation['status']}")
                print(f"Confidence: {validation['confidence']}%")
                
                if validation['issues']:
                    print(f"Issues: {', '.join(validation['issues'])}")
            
            # Save result
            self.db.save_result(
                task_id,
                task['task_type'],
                result.get('response', ''),
                {
                    'validation': validation,
                    'files_modified': files_modified,
                    'test_passed': test_passed
                }
            )
            
            # Update task status based on validation
            if validation['status'] == 'COMPLETE' and (test_passed or task['task_type'] == 'planning'):
                self.db.update_task_status(task_id, 'completed')
                print("\n✅ Task completed successfully!")
                return {'success': True, 'validation': validation}
            else:
                self.db.update_task_status(task_id, 'failed')
                print("\n❌ Task needs revision")
                return {'success': False, 'validation': validation}
                
        except Exception as e:
            print(f"\n❌ Error: {e}")
            self.db.update_task_status(task_id, 'failed')
            self.db.save_result(task_id, 'error', str(e))
            return {'success': False, 'error': str(e)}

