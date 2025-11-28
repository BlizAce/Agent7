"""
Session Manager - Handles Claude CLI session limits and scheduling.
"""
import schedule
import time
from datetime import datetime, timedelta, time as dt_time
from typing import Optional, Dict, Any, Callable
from database import Database
import dateutil.parser


class SessionManager:
    """
    Manages Claude CLI session limits and schedules task resumption.
    Detects when Claude hits rate limits and schedules continuation.
    """
    
    def __init__(self, db: Database):
        """
        Initialize session manager.
        
        Args:
            db: Database instance
        """
        self.db = db
        self.scheduled_tasks = {}
        self.resume_callback = None
    
    def check_for_limit(self, claude_response: Dict[str, Any]) -> bool:
        """
        Check if Claude hit session limit.
        
        Args:
            claude_response: Response dict from Claude CLI
            
        Returns:
            True if session limit was hit
        """
        return claude_response.get('session_limited', False)
    
    def schedule_resume(
        self, 
        task_id: int, 
        reset_time_str: str,
        conversation_id: str,
        project_directory: str,
        remaining_prompt: str,
        additional_context: Optional[Dict] = None
    ) -> datetime:
        """
        Schedule task to resume at specified time.
        
        Args:
            task_id: Task ID to resume
            reset_time_str: Time string (e.g., "10pm", "10:30pm")
            conversation_id: Claude conversation ID to continue
            project_directory: Project directory path
            remaining_prompt: Prompt to send when resuming
            additional_context: Any additional context needed
            
        Returns:
            Scheduled datetime
        """
        # Parse reset time
        resume_time = self._parse_time_to_datetime(reset_time_str)
        
        # Build checkpoint data
        checkpoint_data = {
            'conversation_id': conversation_id,
            'project_directory': project_directory,
            'remaining_prompt': remaining_prompt,
            'context': additional_context or {}
        }
        
        # Save checkpoint to database
        self.db.save_checkpoint(
            task_id=task_id,
            conversation_id=conversation_id,
            project_directory=project_directory,
            remaining_prompt=remaining_prompt,
            scheduled_for=resume_time,
            checkpoint_data=checkpoint_data
        )
        
        # Schedule with schedule library
        schedule_time = resume_time.strftime("%H:%M")
        
        print(f"⏰ Task {task_id} scheduled to resume at {schedule_time} ({reset_time_str})")
        print(f"   Conversation ID: {conversation_id}")
        
        return resume_time
    
    def resume_task(self, task_id: int) -> Optional[Dict]:
        """
        Resume a scheduled task.
        
        Args:
            task_id: Task ID to resume
            
        Returns:
            Checkpoint data if found, None otherwise
        """
        checkpoint = self.db.load_checkpoint(task_id)
        
        if not checkpoint:
            print(f"⚠️  No checkpoint found for task {task_id}")
            return None
        
        print(f"▶️  Resuming task {task_id}")
        print(f"   Conversation: {checkpoint.get('conversation_id')}")
        print(f"   Project: {checkpoint.get('project_directory')}")
        
        return checkpoint
    
    def run_scheduler(self, check_interval: int = 60):
        """
        Run the scheduler loop. Checks for scheduled tasks periodically.
        
        Args:
            check_interval: How often to check for scheduled tasks (seconds)
        """
        print("📅 Scheduler started")
        print(f"   Checking every {check_interval} seconds")
        
        while True:
            try:
                # Check database for tasks that should run now
                current_time = datetime.now()
                scheduled_checkpoints = self.db.get_scheduled_checkpoints(current_time)
                
                for checkpoint in scheduled_checkpoints:
                    task_id = checkpoint['task_id']
                    print(f"\n⏰ Time to resume task {task_id}")
                    
                    # Call resume callback if set
                    if self.resume_callback:
                        try:
                            self.resume_callback(checkpoint)
                        except Exception as e:
                            print(f"❌ Error resuming task {task_id}: {e}")
                    
                    # Delete checkpoint after processing
                    self.db.delete_checkpoint(checkpoint['id'])
                
                # Also run any scheduled jobs
                schedule.run_pending()
                
                time.sleep(check_interval)
                
            except KeyboardInterrupt:
                print("\n⏹️  Scheduler stopped by user")
                break
            except Exception as e:
                print(f"⚠️  Scheduler error: {e}")
                time.sleep(check_interval)
    
    def set_resume_callback(self, callback: Callable):
        """
        Set callback function to call when resuming tasks.
        
        Args:
            callback: Function that takes checkpoint dict as argument
        """
        self.resume_callback = callback
    
    def get_pending_checkpoints(self) -> list:
        """
        Get all pending checkpoints.
        
        Returns:
            List of checkpoint dicts
        """
        future_time = datetime.now() + timedelta(days=365)  # Far future
        return self.db.get_scheduled_checkpoints(future_time)
    
    def cancel_scheduled_task(self, task_id: int) -> bool:
        """
        Cancel a scheduled task.
        
        Args:
            task_id: Task ID to cancel
            
        Returns:
            True if cancelled, False if not found
        """
        checkpoint = self.db.load_checkpoint(task_id)
        if checkpoint:
            self.db.delete_checkpoint(checkpoint['id'])
            print(f"🚫 Cancelled scheduled task {task_id}")
            return True
        return False
    
    def _parse_time_to_datetime(self, time_str: str) -> datetime:
        """
        Parse time string to datetime.
        
        Args:
            time_str: Time string like "10pm", "10:30pm", etc.
            
        Returns:
            Datetime object
        """
        # Clean up the time string
        time_str = time_str.strip().lower()
        
        # Try to parse with dateutil
        try:
            # If just a time, add today's date
            if not any(c.isdigit() and int(c) > 12 for c in time_str.split()):
                # Likely just a time, not a full datetime
                parsed_time = dateutil.parser.parse(time_str, default=datetime.now())
                
                # If the parsed time is in the past today, schedule for tomorrow
                now = datetime.now()
                scheduled = now.replace(
                    hour=parsed_time.hour,
                    minute=parsed_time.minute,
                    second=0,
                    microsecond=0
                )
                
                if scheduled <= now:
                    # Schedule for tomorrow
                    scheduled += timedelta(days=1)
                
                return scheduled
            else:
                return dateutil.parser.parse(time_str)
        except Exception as e:
            # Fallback: schedule for 10 PM today or tomorrow
            print(f"⚠️  Could not parse time '{time_str}': {e}")
            print("   Defaulting to 10:00 PM")
            
            now = datetime.now()
            scheduled = now.replace(hour=22, minute=0, second=0, microsecond=0)
            
            if scheduled <= now:
                scheduled += timedelta(days=1)
            
            return scheduled
    
    def _parse_time(self, time_str: str) -> dt_time:
        """
        Parse time string to time object.
        
        Args:
            time_str: Time string
            
        Returns:
            time object
        """
        dt = self._parse_time_to_datetime(time_str)
        return dt.time()


class SchedulerDaemon:
    """
    Wrapper for running scheduler as a daemon/service.
    """
    
    def __init__(self, db_path: str = "agent7.db", check_interval: int = 60):
        """
        Initialize scheduler daemon.
        
        Args:
            db_path: Path to database
            check_interval: Check interval in seconds
        """
        self.db_path = db_path
        self.check_interval = check_interval
        self.session_manager = None
    
    def start(self, resume_callback: Optional[Callable] = None):
        """
        Start the scheduler daemon.
        
        Args:
            resume_callback: Optional callback for resuming tasks
        """
        from database import Database
        
        db = Database(self.db_path)
        self.session_manager = SessionManager(db)
        
        if resume_callback:
            self.session_manager.set_resume_callback(resume_callback)
        
        print("🚀 Starting Agent7 Scheduler Daemon")
        print(f"   Database: {self.db_path}")
        print(f"   Check interval: {self.check_interval}s")
        
        try:
            self.session_manager.run_scheduler(self.check_interval)
        except KeyboardInterrupt:
            print("\n👋 Scheduler daemon stopped")
    
    def stop(self):
        """Stop the scheduler daemon."""
        # This will be handled by KeyboardInterrupt
        pass


if __name__ == '__main__':
    """Allow running as standalone daemon."""
    import sys
    
    db_path = sys.argv[1] if len(sys.argv) > 1 else "agent7.db"
    check_interval = int(sys.argv[2]) if len(sys.argv) > 2 else 60
    
    daemon = SchedulerDaemon(db_path, check_interval)
    daemon.start()


