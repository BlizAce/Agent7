// Agent7 Web UI JavaScript

// Initialize WebSocket connection
const socket = io();

// State
let currentProjectId = null;
let executionActive = false;

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    console.log('Agent7 UI initialized');
    updateStatus();
    refreshTasks();
    refreshStats();
    
    // Refresh periodically
    setInterval(updateStatus, 5000);
    setInterval(refreshStats, 10000);
});

// WebSocket event handlers

socket.on('connect', function() {
    console.log('Connected to Agent7 server');
    addOutput('🔌 Connected to Agent7 server\n');
});

socket.on('disconnect', function() {
    console.log('Disconnected from server');
    addOutput('⚠️  Disconnected from server\n');
});

socket.on('output', function(msg) {
    addOutput(msg.data);
});

socket.on('task_status', function(data) {
    console.log('Task status update:', data);
    refreshTasks();
    refreshStats();
});

socket.on('execution_complete', function() {
    executionActive = false;
    document.getElementById('execStatus').textContent = 'Idle';
    refreshTasks();
    refreshStats();
});

// API Functions

async function updateStatus() {
    try {
        const response = await fetch('/api/status');
        const status = await response.json();
        
        // Update LM Studio status
        const llmStatus = document.getElementById('llmStatus');
        if (status.local_llm_available) {
            llmStatus.textContent = '✅ Online';
            llmStatus.style.color = '#48bb78';
        } else {
            llmStatus.textContent = '❌ Offline';
            llmStatus.style.color = '#f56565';
        }
        
        // Update project status
        const projectStatus = document.getElementById('projectStatus');
        if (status.current_project_dir) {
            projectStatus.textContent = status.current_project_dir;
            currentProjectId = status.current_project_id;
            document.getElementById('currentProject').classList.remove('hidden');
            document.getElementById('currentProjectPath').textContent = status.current_project_dir;
        } else {
            projectStatus.textContent = 'None';
        }
        
        // Update execution status
        const execStatus = document.getElementById('execStatus');
        executionActive = status.execution_active;
        if (executionActive) {
            execStatus.textContent = 'Running';
            execStatus.style.color = '#ed8936';
            execStatus.classList.add('executing');
        } else {
            execStatus.textContent = 'Idle';
            execStatus.style.color = '#48bb78';
            execStatus.classList.remove('executing');
        }
        
    } catch (error) {
        console.error('Error updating status:', error);
    }
}

async function selectProject() {
    const projectDir = document.getElementById('projectDir').value;
    
    if (!projectDir) {
        alert('Please enter a project directory');
        return;
    }
    
    try {
        const response = await fetch('/api/project/select', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ directory: projectDir })
        });
        
        const result = await response.json();
        
        if (response.ok) {
            addOutput(`✅ Project selected: ${projectDir}\n`);
            currentProjectId = result.project_id;
            updateStatus();
            refreshFiles();
            refreshTasks();
        } else {
            alert('Error: ' + result.error);
        }
    } catch (error) {
        console.error('Error selecting project:', error);
        alert('Failed to select project');
    }
}

async function createTask() {
    const title = document.getElementById('taskTitle').value;
    const description = document.getElementById('taskDesc').value;
    const taskType = document.getElementById('taskType').value;
    const priority = parseInt(document.getElementById('taskPriority').value);
    
    if (!title || !description) {
        alert('Please fill in title and description');
        return;
    }
    
    if (!currentProjectId) {
        alert('Please select a project first');
        return;
    }
    
    try {
        const response = await fetch('/api/tasks', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                project_id: currentProjectId,
                title: title,
                description: description,
                task_type: taskType,
                priority: priority
            })
        });
        
        const result = await response.json();
        
        if (response.ok) {
            addOutput(`✅ Task created: ${title}\n`);
            document.getElementById('taskTitle').value = '';
            document.getElementById('taskDesc').value = '';
            refreshTasks();
            refreshStats();
        } else {
            alert('Error: ' + result.error);
        }
    } catch (error) {
        console.error('Error creating task:', error);
        alert('Failed to create task');
    }
}

async function refreshTasks() {
    try {
        let url = '/api/tasks';
        if (currentProjectId) {
            url += `?project_id=${currentProjectId}`;
        }
        
        const response = await fetch(url);
        const tasks = await response.json();
        
        const tasksList = document.getElementById('tasksList');
        
        if (tasks.length === 0) {
            tasksList.innerHTML = '<div style="padding: 20px; text-align: center; color: #999;">No tasks yet. Create one!</div>';
            return;
        }
        
        tasksList.innerHTML = tasks.map(task => `
            <div class="task-item ${task.task_type} ${task.status}" data-task-id="${task.id}">
                <div class="task-header">
                    <span class="task-title">${task.title}</span>
                    <span class="task-type ${task.task_type}">${task.task_type}</span>
                </div>
                <div class="task-status">
                    Status: ${getStatusEmoji(task.status)} ${task.status} | Priority: ${task.priority}
                </div>
                <div class="task-actions">
                    <button onclick="executeTask(${task.id})" class="btn btn-primary btn-small" ${task.status === 'in_progress' || executionActive ? 'disabled' : ''}>
                        ▶️ Execute
                    </button>
                    <button onclick="viewTaskDetails(${task.id})" class="btn btn-small">
                        📋 Details
                    </button>
                </div>
            </div>
        `).join('');
        
    } catch (error) {
        console.error('Error refreshing tasks:', error);
    }
}

async function executeTask(taskId) {
    if (executionActive) {
        alert('Another task is already executing');
        return;
    }
    
    if (!currentProjectId) {
        alert('Please select a project first');
        return;
    }
    
    try {
        const response = await fetch(`/api/execute/${taskId}`, {
            method: 'POST'
        });
        
        const result = await response.json();
        
        if (response.ok) {
            executionActive = true;
            document.getElementById('execStatus').textContent = 'Running';
            addOutput(`\n${'='.repeat(60)}\n`);
            addOutput(`🚀 Executing task ${taskId}\n`);
            addOutput(`${'='.repeat(60)}\n\n`);
        } else {
            alert('Error: ' + result.error);
        }
    } catch (error) {
        console.error('Error executing task:', error);
        alert('Failed to execute task');
    }
}

async function viewTaskDetails(taskId) {
    try {
        const response = await fetch(`/api/tasks/${taskId}`);
        const data = await response.json();
        
        if (response.ok) {
            // Show task details in output
            addOutput(`\n${'='.repeat(60)}\n`);
            addOutput(`📋 Task Details: ${data.task.title}\n`);
            addOutput(`${'='.repeat(60)}\n`);
            addOutput(`Type: ${data.task.task_type}\n`);
            addOutput(`Status: ${data.task.status}\n`);
            addOutput(`Description: ${data.task.description}\n`);
            
            if (data.results && data.results.length > 0) {
                addOutput(`\nResults:\n`);
                data.results.forEach((result, idx) => {
                    addOutput(`\n[${result.result_type}] ${result.created_at}\n`);
                    addOutput(`${result.content.substring(0, 500)}${result.content.length > 500 ? '...' : ''}\n`);
                });
            }
            
            if (data.file_modifications && data.file_modifications.length > 0) {
                addOutput(`\nFiles Modified:\n`);
                data.file_modifications.forEach(fm => {
                    addOutput(`  • ${fm.filepath} (${fm.action})\n`);
                });
            }
            
            addOutput(`${'='.repeat(60)}\n\n`);
        }
    } catch (error) {
        console.error('Error viewing task details:', error);
    }
}

async function refreshStats() {
    try {
        const response = await fetch('/api/stats');
        const stats = await response.json();
        
        document.getElementById('statTotal').textContent = stats.total_tasks;
        document.getElementById('statPending').textContent = stats.pending;
        document.getElementById('statCompleted').textContent = stats.completed;
        document.getElementById('statFailed').textContent = stats.failed;
        
    } catch (error) {
        console.error('Error refreshing stats:', error);
    }
}

async function refreshFiles() {
    try {
        const response = await fetch('/api/files');
        
        if (!response.ok) {
            return;
        }
        
        const files = await response.json();
        const filesList = document.getElementById('filesList');
        
        if (files.length === 0) {
            filesList.innerHTML = '<div style="padding: 10px; color: #999;">No files</div>';
            return;
        }
        
        filesList.innerHTML = files.slice(0, 50).map(file => `
            <div class="file-item">
                <span class="file-icon">${getFileIcon(file.name)}</span>
                <span>${file.path}</span>
            </div>
        `).join('');
        
        if (files.length > 50) {
            filesList.innerHTML += '<div style="padding: 10px; color: #999; text-align: center;">... and more</div>';
        }
        
    } catch (error) {
        console.error('Error refreshing files:', error);
    }
}

function addOutput(text) {
    const output = document.getElementById('output');
    const line = document.createElement('div');
    line.className = 'output-line';
    line.textContent = text;
    output.appendChild(line);
    output.scrollTop = output.scrollHeight;
}

function clearOutput() {
    const output = document.getElementById('output');
    output.innerHTML = '<div class="output-line">Output cleared.</div>';
}

function getStatusEmoji(status) {
    const emojis = {
        'pending': '⏳',
        'in_progress': '🔄',
        'completed': '✅',
        'failed': '❌'
    };
    return emojis[status] || '❓';
}

function getFileIcon(filename) {
    const ext = filename.split('.').pop().toLowerCase();
    const icons = {
        'py': '🐍',
        'js': '📜',
        'html': '🌐',
        'css': '🎨',
        'json': '📋',
        'md': '📝',
        'txt': '📄',
        'yml': '⚙️',
        'yaml': '⚙️',
    };
    return icons[ext] || '📄';
}


