"""
Example configuration file for Agent7.
Copy this to config.py and customize for your setup.
"""

# Database configuration
DATABASE_PATH = "agent7.db"

# Claude CLI configuration
CLAUDE_CLI_COMMAND = "claude"
CLAUDE_ENABLED = True

# Local LLM configuration  
LOCAL_LLM_URL = "http://localhost:1234/v1"
LOCAL_LLM_ENABLED = True

# AI preference
PREFER_LOCAL_LLM = False  # Set to True to prefer local LLM over Claude

# Default settings
DEFAULT_LANGUAGE = "python"
DEFAULT_MAX_TOKENS = 4096
DEFAULT_TEMPERATURE = 0.7

# Task execution settings
TASK_EXECUTION_DELAY = 1  # seconds between tasks in workflow
REQUEST_TIMEOUT = 300  # seconds (5 minutes)

# Local LLM specific settings
LOCAL_LLM_MODEL = "local-model"  # Model name (usually doesn't matter for LM Studio)
LOCAL_LLM_MAX_TOKENS = 2048
LOCAL_LLM_TEMPERATURE = 0.7


