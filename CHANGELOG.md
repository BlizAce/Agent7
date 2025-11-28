# Changelog

## [2.0.0] - 2025-11-28

### Added - Major Features

#### Web Interface
- **Web-based UI** accessible at `http://localhost:5000`
- Real-time output streaming via WebSocket
- Modern dashboard with status indicators
- Project directory selector
- Task creation interface
- Live file explorer
- Statistics dashboard
- Responsive design

#### Intelligent Orchestration
- **Orchestration Brain** using LM Studio to manage Claude
- Automatic prompt optimization
- Agent selection (coding, testing, review, planning)
- AI validation of Claude's outputs
- Test result validation
- Decision making for next actions

#### Session Management
- Automatic detection of Claude session limits
- Parse reset time from Claude output
- Checkpoint system for state preservation
- Automatic scheduling of task resumption
- Windows service for background operation
- Survives system reboots

#### File Operations
- Claude runs with `--dangerously-skip-permissions`
- Direct file creation and modification
- Automatic detection of file changes
- File modifications tracked in database
- Project directory as working directory

#### Testing
- Automatic pytest execution
- Test result parsing
- AI validation of test results
- Support for unittest
- Test execution history tracking

#### Windows Service
- Scheduler runs as Windows service
- Background operation
- Automatic startup
- Service management scripts
- Logging to file

### Enhanced

#### Database
- New `checkpoints` table for session recovery
- New `file_modifications` table for tracking changes
- New `test_executions` table for test history
- Additional methods for checkpoint management
- File modification tracking
- Test execution storage

#### Claude Client
- `send_message_with_file_access()` method
- Real-time output streaming
- Session limit detection
- File modification parsing
- Agent instruction support
- Project directory support

#### Task Orchestrator
- Integration with orchestration brain
- Integration with session manager
- Integration with test runner
- New `execute_task_with_file_access()` method
- Full workflow orchestration
- Session recovery handling

#### Configuration
- Comprehensive `config.py` with all settings
- Validation functions
- Centralized configuration
- Web UI settings
- Scheduler settings
- Test execution settings

### New Files

#### Core Modules
- `orchestration_brain.py` - AI orchestration layer
- `session_manager.py` - Session and scheduling management
- `scheduler_service.py` - Windows service wrapper
- `test_runner.py` - Test execution engine
- `web_server.py` - Flask web application
- `config.py` - Configuration management

#### Web Interface
- `templates/index.html` - Main dashboard
- `static/css/style.css` - Styling
- `static/js/app.js` - Client-side JavaScript

#### Scripts
- `launch_agent7.bat` - Easy launcher
- `install_service.bat` - Service installation
- `uninstall_service.bat` - Service removal

#### Documentation
- `IMPLEMENTATION_SUMMARY.md` - Implementation details
- `CHANGELOG.md` - This file

### Updated

#### Dependencies
- Added `flask>=3.0.0`
- Added `flask-socketio>=5.3.0`
- Added `python-socketio>=5.10.0`
- Added `schedule>=1.2.0`
- Added `pywin32>=306`
- Added `pytest>=7.4.0`
- Added `python-dateutil>=2.8.2`

#### Documentation
- Updated `README.md` with web UI instructions
- Updated architecture section
- Added troubleshooting for new features
- Added Windows service documentation

### Technical Details

#### Architecture Changes
- Shifted to dual AI architecture (LM Studio + Claude)
- LM Studio acts as orchestrator/brain
- Claude acts as executor/hands
- Web-based monitoring and control
- Background service for scheduling

#### Workflow Changes
- Tasks now execute with full orchestration
- File access enabled by default
- Automatic test execution
- AI validation of all outputs
- Session recovery built-in

#### Database Schema Changes
```sql
-- New tables
CREATE TABLE checkpoints (...);
CREATE TABLE file_modifications (...);
CREATE TABLE test_executions (...);
```

### Backward Compatibility

- Original CLI (`agent7.py`) still works
- Existing tasks and projects compatible
- Database schema auto-upgrades
- No breaking changes to core modules

### Breaking Changes

None - fully backward compatible

### Migration Guide

No migration needed. Simply:
1. Install new dependencies: `pip install -r requirements.txt`
2. Run `launch_agent7.bat` to start with new features
3. Existing data and tasks will work automatically

---

## [1.0.0] - Initial Release

### Features
- CLI-based task management
- Claude CLI integration
- Local LLM (LM Studio) integration
- SQLite database
- Project management
- Task types: planning, coding, testing
- Conversation history
- Result storage
- Manual task execution
- Workflow automation

---

**Note**: Version 2.0 is a major enhancement that adds a complete web interface, intelligent orchestration, session management, and automated testing while maintaining full backward compatibility with version 1.0.


