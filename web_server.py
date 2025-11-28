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
from claude_client import ClaudeClient
from local_llm_client import LocalLLMClient
from orchestration_brain import OrchestrationBrain
from task_orchestrator import TaskOrchestrator
from session_manager import SessionManager
from test_runner import TestRunner

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
    state['claude'] = ClaudeClient()
    state['local_llm'] = LocalLLMClient('http://localhost:1234/v1')
    state['brain'] = OrchestrationBrain(state['local_llm'])
    state['session_manager'] = SessionManager(state['db'])
    state['test_runner'] = TestRunner(state['db'])
    
    # Set up orchestrator
    state['orchestrator'] = TaskOrchestrator(
        state['db'],
        state['claude'],
        state['local_llm'],
        prefer_local=False
    )


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
        
        # Get orchestration from brain
        socketio.emit('output', {'data': "🧠 Planning approach with LM Studio...\n"})
        
        # Get list of files in project
        files_in_project = []
        for root, dirs, files in os.walk(project_dir):
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            for f in files:
                if not f.startswith('.'):
                    rel_path = os.path.relpath(os.path.join(root, f), project_dir)
                    files_in_project.append(rel_path)
        
        orchestration = state['brain'].create_claude_prompt_for_task(
            task['description'],
            task['task_type'],
            f"Working in: {project_dir}",
            files_in_project=files_in_project[:50]  # Limit to avoid token issues
        )
        
        socketio.emit('output', {'data': f"✅ Using agents: {', '.join(orchestration['agents'])}\n"})
        socketio.emit('output', {'data': "🤖 Launching Claude CLI...\n\n"})
        
        # Execute with Claude
        result = state['claude'].send_message_with_file_access(
            prompt=orchestration['prompt'],
            project_directory=project_dir,
            use_agents=orchestration['agents']
        )
        
        # Stream output
        if result.get('response'):
            socketio.emit('output', {'data': result['response'] + "\n"})
        
        # Check for session limit
        if result.get('session_limited'):
            reset_time = result.get('reset_time', '10pm')
            socketio.emit('output', {'data': f"\n⏸️  Session limit reached. Scheduling resume at {reset_time}\n"})
            
            state['session_manager'].schedule_resume(
                task_id=task_id,
                reset_time_str=reset_time,
                conversation_id=result.get('conversation_id', ''),
                project_directory=project_dir,
                remaining_prompt=orchestration['prompt']
            )
            
            state['db'].update_task_status(task_id, 'pending')
            socketio.emit('task_status', {'task_id': task_id, 'status': 'scheduled'})
            return
        
        # Save conversation
        state['db'].save_conversation(
            task_id,
            'claude_cli',
            orchestration['prompt'],
            result.get('response', ''),
            result.get('metadata')
        )
        
        # Save file modifications
        files_modified = result.get('files_modified', [])
        for filepath in files_modified:
            state['db'].save_file_modification(task_id, filepath, 'modified')
        
        if files_modified:
            socketio.emit('output', {'data': f"\n📝 Files modified: {', '.join(files_modified)}\n"})
        
        # Execute tests if applicable
        if task['task_type'] in ['coding', 'testing']:
            socketio.emit('output', {'data': "\n🧪 Running tests...\n"})
            
            test_results = state['test_runner'].execute_pytest(project_dir)
            test_summary = state['test_runner'].format_results_summary(test_results)
            socketio.emit('output', {'data': test_summary + "\n"})
            
            # Validate with brain
            socketio.emit('output', {'data': "\n🧠 Validating with LM Studio...\n"})
            test_validation = state['brain'].validate_test_results(
                test_results.get('full_output', ''),
                test_results.get('passed', False),
                task['description']
            )
            socketio.emit('output', {'data': f"Assessment: {test_validation['assessment']}\n"})
        
        # Validate Claude's work
        socketio.emit('output', {'data': "\n🧠 Validating results with LM Studio...\n"})
        validation = state['brain'].validate_claude_work(
            task['task_type'],
            task['description'],
            result.get('response', ''),
            files_modified,
            orchestration['validation_criteria']
        )
        
        socketio.emit('output', {'data': f"Status: {validation['status']}\n"})
        socketio.emit('output', {'data': f"Confidence: {validation['confidence']}%\n"})
        
        if validation['issues']:
            socketio.emit('output', {'data': f"Issues: {', '.join(validation['issues'])}\n"})
        
        # Save result
        state['db'].save_result(
            task_id,
            task['task_type'],
            result.get('response', ''),
            {'validation': validation, 'files_modified': files_modified}
        )
        
        # Update task status
        if validation['status'] == 'COMPLETE':
            state['db'].update_task_status(task_id, 'completed')
            socketio.emit('output', {'data': "\n✅ Task completed successfully!\n"})
            socketio.emit('task_status', {'task_id': task_id, 'status': 'completed'})
        else:
            state['db'].update_task_status(task_id, 'failed')
            socketio.emit('output', {'data': "\n❌ Task needs revision\n"})
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


