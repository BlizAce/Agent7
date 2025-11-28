"""
Database module for tracking tasks, conversations, and results.
"""
import sqlite3
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from contextlib import contextmanager


class Database:
    """SQLite database manager for the agent system."""
    
    def __init__(self, db_path: str = "agent7.db"):
        self.db_path = db_path
        self.init_database()
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def init_database(self):
        """Initialize database tables."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Projects table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS projects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Tasks table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER,
                    title TEXT NOT NULL,
                    description TEXT,
                    task_type TEXT NOT NULL,  -- planning, coding, testing
                    status TEXT DEFAULT 'pending',  -- pending, in_progress, completed, failed
                    priority INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    FOREIGN KEY (project_id) REFERENCES projects(id)
                )
            """)
            
            # Conversations table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id INTEGER,
                    model_type TEXT NOT NULL,  -- claude_cli, local_llm
                    prompt TEXT NOT NULL,
                    response TEXT,
                    metadata TEXT,  -- JSON string
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (task_id) REFERENCES tasks(id)
                )
            """)
            
            # Results table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id INTEGER,
                    result_type TEXT NOT NULL,  -- code, test, plan, error
                    content TEXT NOT NULL,
                    metadata TEXT,  -- JSON string
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (task_id) REFERENCES tasks(id)
                )
            """)
            
            # Checkpoints table (for session resumption)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS checkpoints (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id INTEGER,
                    conversation_id TEXT,
                    project_directory TEXT,
                    remaining_prompt TEXT,
                    scheduled_for TIMESTAMP,
                    checkpoint_data TEXT,  -- JSON string
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (task_id) REFERENCES tasks(id)
                )
            """)
            
            # File modifications table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS file_modifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id INTEGER,
                    filepath TEXT NOT NULL,
                    action TEXT NOT NULL,  -- created, modified, deleted
                    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (task_id) REFERENCES tasks(id)
                )
            """)
            
            # Test executions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS test_executions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id INTEGER,
                    test_code TEXT,
                    execution_output TEXT,
                    passed BOOLEAN,
                    validation_notes TEXT,  -- From LM Studio
                    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (task_id) REFERENCES tasks(id)
                )
            """)
    
    # Project operations
    def create_project(self, name: str, description: str = "") -> int:
        """Create a new project."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO projects (name, description) VALUES (?, ?)",
                (name, description)
            )
            return cursor.lastrowid
    
    def get_project(self, project_id: int) -> Optional[Dict]:
        """Get a project by ID."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def list_projects(self) -> List[Dict]:
        """List all projects."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM projects ORDER BY updated_at DESC")
            return [dict(row) for row in cursor.fetchall()]
    
    # Task operations
    def create_task(self, project_id: int, title: str, description: str,
                    task_type: str, priority: int = 0) -> int:
        """Create a new task."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO tasks (project_id, title, description, task_type, priority)
                   VALUES (?, ?, ?, ?, ?)""",
                (project_id, title, description, task_type, priority)
            )
            return cursor.lastrowid
    
    def update_task_status(self, task_id: int, status: str):
        """Update task status."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            completed_at = datetime.now() if status == 'completed' else None
            cursor.execute(
                """UPDATE tasks SET status = ?, updated_at = CURRENT_TIMESTAMP,
                   completed_at = ? WHERE id = ?""",
                (status, completed_at, task_id)
            )
    
    def get_task(self, task_id: int) -> Optional[Dict]:
        """Get a task by ID."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def list_tasks(self, project_id: Optional[int] = None,
                   status: Optional[str] = None) -> List[Dict]:
        """List tasks, optionally filtered by project and status."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM tasks WHERE 1=1"
            params = []
            
            if project_id:
                query += " AND project_id = ?"
                params.append(project_id)
            
            if status:
                query += " AND status = ?"
                params.append(status)
            
            query += " ORDER BY priority DESC, created_at ASC"
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    # Conversation operations
    def save_conversation(self, task_id: int, model_type: str,
                         prompt: str, response: str,
                         metadata: Optional[Dict] = None) -> int:
        """Save a conversation."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            metadata_json = json.dumps(metadata) if metadata else None
            cursor.execute(
                """INSERT INTO conversations (task_id, model_type, prompt, response, metadata)
                   VALUES (?, ?, ?, ?, ?)""",
                (task_id, model_type, prompt, response, metadata_json)
            )
            return cursor.lastrowid
    
    def get_conversations(self, task_id: int) -> List[Dict]:
        """Get all conversations for a task."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM conversations WHERE task_id = ? ORDER BY created_at ASC",
                (task_id,)
            )
            conversations = []
            for row in cursor.fetchall():
                conv = dict(row)
                if conv['metadata']:
                    conv['metadata'] = json.loads(conv['metadata'])
                conversations.append(conv)
            return conversations
    
    # Results operations
    def save_result(self, task_id: int, result_type: str,
                   content: str, metadata: Optional[Dict] = None) -> int:
        """Save a task result."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            metadata_json = json.dumps(metadata) if metadata else None
            cursor.execute(
                """INSERT INTO results (task_id, result_type, content, metadata)
                   VALUES (?, ?, ?, ?)""",
                (task_id, result_type, content, metadata_json)
            )
            return cursor.lastrowid
    
    def get_results(self, task_id: int) -> List[Dict]:
        """Get all results for a task."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM results WHERE task_id = ? ORDER BY created_at ASC",
                (task_id,)
            )
            results = []
            for row in cursor.fetchall():
                result = dict(row)
                if result['metadata']:
                    result['metadata'] = json.loads(result['metadata'])
                results.append(result)
            return results
    
    # Checkpoint operations
    def save_checkpoint(self, task_id: int, conversation_id: str,
                       project_directory: str, remaining_prompt: str,
                       scheduled_for: datetime, checkpoint_data: Dict) -> int:
        """Save a checkpoint for task resumption."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            checkpoint_json = json.dumps(checkpoint_data)
            cursor.execute(
                """INSERT INTO checkpoints (task_id, conversation_id, project_directory,
                   remaining_prompt, scheduled_for, checkpoint_data)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (task_id, conversation_id, project_directory, remaining_prompt,
                 scheduled_for, checkpoint_json)
            )
            return cursor.lastrowid
    
    def load_checkpoint(self, task_id: int) -> Optional[Dict]:
        """Load the most recent checkpoint for a task."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT * FROM checkpoints WHERE task_id = ?
                   ORDER BY created_at DESC LIMIT 1""",
                (task_id,)
            )
            row = cursor.fetchone()
            if row:
                checkpoint = dict(row)
                if checkpoint['checkpoint_data']:
                    checkpoint['checkpoint_data'] = json.loads(checkpoint['checkpoint_data'])
                return checkpoint
            return None
    
    def get_scheduled_checkpoints(self, current_time: datetime) -> List[Dict]:
        """Get checkpoints that are scheduled to run at or before current time."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT * FROM checkpoints WHERE scheduled_for <= ?
                   ORDER BY scheduled_for ASC""",
                (current_time,)
            )
            checkpoints = []
            for row in cursor.fetchall():
                checkpoint = dict(row)
                if checkpoint['checkpoint_data']:
                    checkpoint['checkpoint_data'] = json.loads(checkpoint['checkpoint_data'])
                checkpoints.append(checkpoint)
            return checkpoints
    
    def delete_checkpoint(self, checkpoint_id: int):
        """Delete a checkpoint after it's been processed."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM checkpoints WHERE id = ?", (checkpoint_id,))
    
    # File modification operations
    def save_file_modification(self, task_id: int, filepath: str, action: str) -> int:
        """Record a file modification."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO file_modifications (task_id, filepath, action)
                   VALUES (?, ?, ?)""",
                (task_id, filepath, action)
            )
            return cursor.lastrowid
    
    def get_file_modifications(self, task_id: int) -> List[Dict]:
        """Get all file modifications for a task."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT * FROM file_modifications WHERE task_id = ?
                   ORDER BY detected_at ASC""",
                (task_id,)
            )
            return [dict(row) for row in cursor.fetchall()]
    
    # Test execution operations
    def save_test_execution(self, task_id: int, test_code: str,
                           execution_output: str, passed: bool,
                           validation_notes: Optional[str] = None) -> int:
        """Save a test execution result."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO test_executions (task_id, test_code, execution_output,
                   passed, validation_notes)
                   VALUES (?, ?, ?, ?, ?)""",
                (task_id, test_code, execution_output, passed, validation_notes)
            )
            return cursor.lastrowid
    
    def get_test_executions(self, task_id: int) -> List[Dict]:
        """Get all test executions for a task."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT * FROM test_executions WHERE task_id = ?
                   ORDER BY executed_at ASC""",
                (task_id,)
            )
            return [dict(row) for row in cursor.fetchall()]

