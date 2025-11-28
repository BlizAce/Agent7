"""
Flask web server for Agent7 UI.
"""
import os
import json
import threading
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_socketio import SocketIO, emit
from werkzeug.utils import secure_filename
from datetime import datetime

# Import Agent7 modules
from database import Database
from local_llm_client import LocalLLMClient
from test_runner import TestRunner
from lm_studio_executor import LMStudioExecutor
from chat_agent import ChatAgent

# Claude integration - Future feature (v3.0)
# from claude_client import ClaudeClient
# from orchestration_brain import OrchestrationBrain
# from session_manager import SessionManager

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'agent7-secret-key-change-in-production'
socketio = SocketIO(app, cors_allowed_origins="*")

# Global state
state = {
    'db': None,
    'claude': None,
    'local_llm': None,
    'brain': None,
    'orchestrator': None,
    'session_manager': None,
    'test_runner': None,
    'current_project_dir': None,
    'current_project_id': None,
    'execution_active': False
}


def initialize_components():
    """Initialize all Agent7 components."""
    state['db'] = Database('agent7.db')
    state['local_llm'] = LocalLLMClient('http://localhost:1234/v1')
    state['test_runner'] = TestRunner(state['db'])
    state['lm_executor'] = None  # Initialized per project
    state['chat_agent'] = ChatAgent(state['local_llm'], state['db'])
    
    # Legacy components (for reference, not used in v2.2)
    # state['claude'] = ClaudeClient()
    # state['brain'] = OrchestrationBrain(state['local_llm'])
    # state['session_manager'] = SessionManager(state['db'])
    # state['orchestrator'] = TaskOrchestrator(...)


# Routes

@app.route('/')
def index():
    """Main dashboard page."""
    return render_template('index.html')


@app.route('/api/status')
def get_status():
    """Get system status."""
    llm_available = False
    if state['local_llm']:
        llm_available = state['local_llm'].check_availability()
    
    projects = state['db'].list_projects() if state['db'] else []
    tasks = state['db'].list_tasks() if state['db'] else []
    pending_checkpoints = state['session_manager'].get_pending_checkpoints() if state['session_manager'] else []
    
    return jsonify({
        'local_llm_available': llm_available,
        'claude_available': True,  # Assume available if configured
        'current_project_dir': state['current_project_dir'],
        'current_project_id': state['current_project_id'],
        'execution_active': state['execution_active'],
        'total_projects': len(projects),
        'total_tasks': len(tasks),
        'pending_tasks': len([t for t in tasks if t['status'] == 'pending']),
        'scheduled_tasks': len(pending_checkpoints)
    })


@app.route('/api/project/select', methods=['POST'])
def select_project():
    """Set the current project directory."""
    data = request.json
    project_dir = data.get('directory')
    
    if not project_dir or not os.path.exists(project_dir):
        return jsonify({'error': 'Invalid directory'}), 400
    
    state['current_project_dir'] = project_dir
    
    # Try to find or create project in database
    project_name = os.path.basename(project_dir)
    projects = state['db'].list_projects()
    
    project_id = None
    for p in projects:
        if p['name'] == project_name:
            project_id = p['id']
            break
    
    if not project_id:
        project_id = state['db'].create_project(project_name, f"Project at {project_dir}")
    
    state['current_project_id'] = project_id
    
    return jsonify({
        'success': True,
        'project_id': project_id,
        'project_dir': project_dir
    })


@app.route('/api/project/current')
def get_current_project():
    """Get current project information."""
    if not state['current_project_id']:
        return jsonify({'error': 'No project selected'}), 404
    
    project = state['db'].get_project(state['current_project_id'])
    return jsonify(project)


@app.route('/api/projects')
def list_projects():
    """List all projects."""
    projects = state['db'].list_projects()
    return jsonify(projects)


@app.route('/api/projects', methods=['POST'])
def create_project():
    """Create a new project."""
    data = request.json
    name = data.get('name')
    description = data.get('description', '')
    
    if not name:
        return jsonify({'error': 'Name required'}), 400
    
    project_id = state['db'].create_project(name, description)
    project = state['db'].get_project(project_id)
    
    return jsonify(project)


@app.route('/api/tasks')
def list_tasks():
    """List tasks."""
    project_id = request.args.get('project_id', type=int)
    status = request.args.get('status')
    
    tasks = state['db'].list_tasks(project_id, status)
    return jsonify(tasks)


@app.route('/api/tasks', methods=['POST'])
def create_task():
    """Create a new task."""
    data = request.json
    
    project_id = data.get('project_id') or state['current_project_id']
    if not project_id:
        return jsonify({'error': 'No project selected'}), 400
    
    title = data.get('title')
    description = data.get('description')
    task_type = data.get('task_type')
    priority = data.get('priority', 0)
    
    if not all([title, description, task_type]):
        return jsonify({'error': 'Missing required fields'}), 400
    
    task_id = state['db'].create_task(project_id, title, description, task_type, priority)
    task = state['db'].get_task(task_id)
    
    return jsonify(task)


@app.route('/api/tasks/<int:task_id>')
def get_task(task_id):
    """Get task details."""
    task = state['db'].get_task(task_id)
    if not task:
        return jsonify({'error': 'Task not found'}), 404
    
    # Include conversations and results
    conversations = state['db'].get_conversations(task_id)
    results = state['db'].get_results(task_id)
    file_mods = state['db'].get_file_modifications(task_id)
    test_execs = state['db'].get_test_executions(task_id)
    
    return jsonify({
        'task': task,
        'conversations': conversations,
        'results': results,
        'file_modifications': file_mods,
        'test_executions': test_execs
    })


@app.route('/api/task/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    """Delete a task."""
    try:
        # Get task first to check if it exists
        task = state['db'].get_task(task_id)
        if not task:
            return jsonify({'error': 'Task not found'}), 404
        
        # Delete from database
        with state['db'].get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
            conn.commit()
        
        return jsonify({'success': True, 'message': f'Task #{task_id} deleted'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/task/<int:task_id>/archive', methods=['POST'])
def archive_task(task_id):
    """Archive a task by setting status to 'archived'."""
    try:
        task = state['db'].get_task(task_id)
        if not task:
            return jsonify({'error': 'Task not found'}), 404
        
        # Update status to archived
        state['db'].update_task_status(task_id, 'archived')
        
        return jsonify({'success': True, 'message': f'Task #{task_id} archived'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/execute/<int:task_id>', methods=['POST'])
def execute_task(task_id):
    """Execute a task."""
    if state['execution_active']:
        return jsonify({'error': 'Execution already in progress'}), 409
    
    task = state['db'].get_task(task_id)
    if not task:
        return jsonify({'error': 'Task not found'}), 404
    
    if not state['current_project_dir']:
        return jsonify({'error': 'No project directory selected'}), 400
    
    # Start execution in background thread
    thread = threading.Thread(
        target=execute_task_thread,
        args=(task_id, state['current_project_dir'])
    )
    thread.daemon = True
    thread.start()
    
    return jsonify({'success': True, 'message': 'Execution started'})


def execute_task_thread(task_id, project_dir):
    """Execute task in background thread."""
    state['execution_active'] = True
    
    try:
        task = state['db'].get_task(task_id)
        socketio.emit('output', {'data': f"🚀 Starting task: {task['title']}\n"})
        socketio.emit('output', {'data': f"📁 Project: {project_dir}\n"})
        
        # Update task status
        state['db'].update_task_status(task_id, 'in_progress')
        socketio.emit('task_status', {'task_id': task_id, 'status': 'in_progress'})
        
        # Initialize LM Studio executor for this project
        if not state['lm_executor'] or state['lm_executor'].project_directory != project_dir:
            socketio.emit('output', {'data': "🔧 Initializing LM Studio executor...\n"})
            state['lm_executor'] = LMStudioExecutor(
                state['local_llm'],
                state['db'],
                project_dir
            )
        
        # Callback for progress updates
        def progress_callback(update):
            status = update.get('status')
            message = update.get('message', '')
            
            if status == 'starting':
                socketio.emit('output', {'data': f"⚙️  {message}\n"})
            elif status == 'executing':
                socketio.emit('output', {'data': f"\n🤖 {message}\n"})
            elif status == 'response':
                response = update.get('response', '')
                socketio.emit('output', {'data': f"\n{response}\n"})
            elif status == 'tools':
                socketio.emit('output', {'data': f"\n🔧 {message}\n"})
            elif status == 'tool_results':
                results = update.get('results', '')
                socketio.emit('output', {'data': f"\n{results}\n"})
            elif status == 'files':
                summary = update.get('summary', '')
                operations = update.get('operations', [])
                if summary:
                    socketio.emit('output', {'data': f"\n📝 {message}\n{summary}\n"})
                else:
                    socketio.emit('output', {'data': f"\n📝 {message} ({len(operations)} operations)\n"})
            elif status == 'validation':
                validation = update.get('validation', '')
                socketio.emit('output', {'data': f"\n🧠 {message}\n{validation}\n"})
        
        # Execute with LM Studio
        socketio.emit('output', {'data': "🤖 Executing with LM Studio...\n\n"})
        
        result = state['lm_executor'].execute_task(
            task_id=task_id,
            task_description=task['description'],
            task_type=task['task_type'],
            max_iterations=3,
            callback=progress_callback
        )
        
        # Get status and files
        status = result.get('status', 'UNKNOWN')
        file_operations = result.get('file_operations', [])
        files_modified = [op['filepath'] for op in file_operations if op.get('success')]
        
        # Save conversation
        state['db'].save_conversation(
            task_id,
            'lm_studio',
            result.get('response', ''),
            result.get('response', ''),
            {'iterations': result.get('iterations', 1)}
        )
        
        # Execute tests if applicable
        if task['task_type'] in ['coding', 'testing'] and files_modified:
            socketio.emit('output', {'data': "\n🧪 Running tests...\n"})
            
            test_results = state['test_runner'].execute_pytest(project_dir)
            test_summary = state['test_runner'].format_results_summary(test_results)
            socketio.emit('output', {'data': test_summary + "\n"})
        
        socketio.emit('output', {'data': f"\n{'='*60}\n"})
        socketio.emit('output', {'data': f"✅ Status: {status}\n"})
        socketio.emit('output', {'data': f"📝 Files Created: {len(files_modified)}\n"})
        socketio.emit('output', {'data': f"🔄 Iterations: {result.get('iterations', 1)}\n"})
        
        # Save result
        state['db'].save_result(
            task_id,
            task['task_type'],
            result.get('response', ''),
            {
                'status': status,
                'files_modified': files_modified,
                'iterations': result.get('iterations', 1),
                'tool_results': len(result.get('tool_results', []))
            }
        )
        
        # Update task status
        if status == 'COMPLETED':
            state['db'].update_task_status(task_id, 'completed')
            socketio.emit('output', {'data': "\n✅ Task completed successfully!\n"})
            socketio.emit('task_status', {'task_id': task_id, 'status': 'completed'})
        elif status == 'NEEDS_REVISION':
            state['db'].update_task_status(task_id, 'pending')
            socketio.emit('output', {'data': "\n⚠️  Task needs revision\n"})
            socketio.emit('task_status', {'task_id': task_id, 'status': 'pending'})
        else:
            state['db'].update_task_status(task_id, 'failed')
            socketio.emit('output', {'data': "\n❌ Task failed\n"})
            socketio.emit('task_status', {'task_id': task_id, 'status': 'failed'})
    
    except Exception as e:
        socketio.emit('output', {'data': f"\n❌ Error: {e}\n"})
        state['db'].update_task_status(task_id, 'failed')
        state['db'].save_result(task_id, 'error', str(e))
        socketio.emit('task_status', {'task_id': task_id, 'status': 'failed'})
    
    finally:
        state['execution_active'] = False
        socketio.emit('execution_complete', {})


@app.route('/api/files')
def list_files():
    """List files in current project directory."""
    if not state['current_project_dir']:
        return jsonify([])  # Return empty list instead of error
    
    if not os.path.exists(state['current_project_dir']):
        return jsonify({'error': 'Project directory does not exist'}), 400
    
    files = []
    try:
        for root, dirs, filenames in os.walk(state['current_project_dir']):
            # Skip hidden directories
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            
            for filename in filenames:
                if not filename.startswith('.'):
                    filepath = os.path.join(root, filename)
                    try:
                        rel_path = os.path.relpath(filepath, state['current_project_dir'])
                        files.append({
                            'path': rel_path,
                            'name': filename,
                            'size': os.path.getsize(filepath),
                            'modified': datetime.fromtimestamp(os.path.getmtime(filepath)).isoformat()
                        })
                    except Exception as e:
                        # Skip files we can't access
                        continue
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
    return jsonify(files)


@app.route('/api/stats')
def get_stats():
    """Get statistics."""
    if not state['db']:
        return jsonify({'error': 'Database not initialized'}), 500
    
    tasks = state['db'].list_tasks()
    
    stats = {
        'total_tasks': len(tasks),
        'pending': len([t for t in tasks if t['status'] == 'pending']),
        'in_progress': len([t for t in tasks if t['status'] == 'in_progress']),
        'completed': len([t for t in tasks if t['status'] == 'completed']),
        'failed': len([t for t in tasks if t['status'] == 'failed']),
        'by_type': {
            'planning': len([t for t in tasks if t['task_type'] == 'planning']),
            'coding': len([t for t in tasks if t['task_type'] == 'coding']),
            'testing': len([t for t in tasks if t['task_type'] == 'testing'])
        }
    }
    
    return jsonify(stats)


@app.route('/api/chat', methods=['POST'])
def chat():
    """Send a chat message to the agent."""
    if not state['chat_agent']:
        return jsonify({'error': 'Chat agent not initialized'}), 500
    
    data = request.get_json()
    message = data.get('message', '')
    
    if not message:
        return jsonify({'error': 'No message provided'}), 400
    
    # Get current project directory and ID
    project_dir = state.get('current_project_directory')
    project_id = state.get('current_project_id')
    
    # Send message to chat agent
    result = state['chat_agent'].send_message(message, project_dir, project_id)
    
    # Handle any actions
    actions = result.get('actions', [])
    for action in actions:
        # If task was created, notify UI to refresh task list
        if action.get('action') == 'create_task' and action.get('success'):
            socketio.emit('task_created', {
                'task_id': action.get('task_id'),
                'title': action.get('title')
            })
        
        # If execution was requested, actually execute the task
        if action.get('execute') and action.get('task_id'):
            task_id = action['task_id']
            
            # Get task details
            task = state['db'].get_task(task_id)
            if task and state.get('current_project_directory'):
                # Execute in background thread
                thread = threading.Thread(
                    target=execute_task_thread,
                    args=(task_id, task, state['current_project_directory'])
                )
                thread.daemon = True
                thread.start()
                
                # Mark action as executed
                action['executed'] = True
                action['message'] = f"Task #{task_id} execution started"
    
    return jsonify({
        'success': True,
        'response': result.get('response'),
        'actions': actions
    })


@app.route('/api/chat/reset', methods=['POST'])
def reset_chat():
    """Reset chat conversation history."""
    if state['chat_agent']:
        state['chat_agent'].reset_conversation()
        return jsonify({'success': True, 'message': 'Chat history reset'})
    return jsonify({'error': 'Chat agent not initialized'}), 500


# WebSocket events

@socketio.on('connect')
def handle_connect():
    """Handle client connection."""
    emit('connected', {'data': 'Connected to Agent7'})


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection."""
    pass


# Main entry point

if __name__ == '__main__':
    print("🚀 Starting Agent7 Web Server")
    print("=" * 60)
    
    # Initialize components
    initialize_components()
    print("✅ Components initialized")
    
    # Check LM Studio
    if state['local_llm'] and state['local_llm'].check_availability():
        print("✅ LM Studio connected")
    else:
        print("⚠️  LM Studio not available at http://localhost:1234")
    
    print("=" * 60)
    print("🌐 Web UI will be available at: http://localhost:5000")
    print("=" * 60)
    
    # Run server
    socketio.run(app, host='0.0.0.0', port=5000, debug=False, allow_unsafe_werkzeug=True)


