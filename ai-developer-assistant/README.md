# AI Developer Assistant

A comprehensive AI-powered development assistant with file operations, terminal commands, multi-agent communication, task management, Playwright integration, OpenRouter API, and VS Code integration.

## Features

### 📁 File Operations
- Read, write, create, and delete files
- Directory management and navigation
- File search and pattern matching
- File information and metadata
- Directory tree visualization

### 💻 Terminal Operations
- Execute shell commands
- Interactive terminal sessions
- Process management and monitoring
- System information retrieval
- Working directory management

### 🤝 Multi-Agent Communication
- WebSocket-based agent communication
- Two-way message passing
- Agent registry and discovery
- Message history and persistence
- Client-server architecture

### 📋 Task Manager
- Asynchronous task execution
- Task scheduling and prioritization
- Task dependencies and workflows
- Progress tracking and monitoring
- Task persistence and recovery

### 🌐 Playwright Integration
- Browser automation and testing
- Web scraping and interaction
- Screenshot capture and recording
- Form filling and submission
- Multi-tab management

### 🧠 OpenRouter API Integration
- Access to multiple AI models
- Code generation and analysis
- Debugging assistance
- Concept explanation
- Code improvement suggestions

### 💻 VS Code Integration
- File editing and management
- Workspace operations
- Extension management
- Terminal integration
- Debugging support

## Installation

### Prerequisites
- Python 3.8 or higher
- Node.js (for Playwright)
- VS Code (optional, for IDE integration)

### Setup

1. Clone the repository:
```bash
git clone https://github.com/ai-developer/assistant.git
cd ai-developer-assistant
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Install Playwright browsers:
```bash
playwright install
```

5. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

## Configuration

Create a `.env` file based on `.env.example`:

```env
# OpenRouter API Configuration
OPENROUTER_API_KEY=your_openrouter_api_key_here
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_MODEL=anthropic/claude-3-sonnet

# VS Code Integration
VSCODE_PORT=8080
VSCODE_HOST=localhost

# Multi-Agent Communication
AGENT_PORT=8081
AGENT_HOST=localhost

# Playwright Configuration
PLAYWRIGHT_HEADLESS=false
PLAYWRIGHT_TIMEOUT=30000

# File Operations
WORKSPACE_DIR=./workspace
MAX_FILE_SIZE=10485760  # 10MB

# Task Manager
MAX_CONCURRENT_TASKS=5
TASK_TIMEOUT=300000  # 5 minutes

# Logging
LOG_LEVEL=INFO
LOG_FILE=./logs/assistant.log
```

## Usage

### Starting the Assistant

```bash
python main.py
```

The assistant will start and display the available integrations and connection information.

### Basic Usage Examples

#### File Operations

```python
from src.modules.file_operations import FileOperations

# Initialize file operations
file_ops = FileOperations()
await file_ops.initialize()

# Read a file
result = await file_ops.read_file("example.txt")
print(result["content"])

# Write a file
result = await file_ops.write_file("new_file.txt", "Hello, World!")
print(result["success"])

# List directory contents
result = await file_ops.list_directory(".")
for item in result["items"]:
    print(f"{item['name']} ({item['type']})")
```

#### Terminal Operations

```python
from src.modules.terminal_operations import TerminalOperations

# Initialize terminal operations
terminal_ops = TerminalOperations()
await terminal_ops.initialize()

# Run a command
result = await terminal_ops.run_command("ls -la")
print(result["stdout"])

# Start an interactive process
result = await terminal_ops.run_interactive_command("python")
process_id = result["process_id"]

# Send input to the process
await terminal_ops.send_input_to_process(process_id, "print('Hello')")
```

#### Task Management

```python
from src.modules.task_manager import TaskManager

# Initialize task manager
task_manager = TaskManager(max_concurrent_tasks=3)
await task_manager.initialize()

# Create a task
task_data = {
    "name": "Generate Code",
    "description": "Generate Python code for a calculator",
    "type": "generate_code",
    "parameters": {
        "prompt": "Create a simple calculator class",
        "language": "python"
    }
}

result = await task_manager.create_task(task_data)
task_id = result["task_id"]

# Check task status
status = await task_manager.get_task_status(task_id)
print(f"Task status: {status['status']}")
```

#### Playwright Integration

```python
from src.modules.playwright_integration import PlaywrightIntegration

# Initialize Playwright
playwright = PlaywrightIntegration()
await playwright.initialize()

# Navigate to a website
result = await playwright.navigate_to_url("https://example.com")
print(f"Page title: {result['title']}")

# Take a screenshot
result = await playwright.take_screenshot()
print(f"Screenshot saved to: {result['path']}")

# Fill a form
await playwright.fill_form("input[name='search']", "AI Assistant")
await playwright.click_element("button[type='submit']")
```

#### OpenRouter API Integration

```python
from src.modules.openrouter_integration import OpenRouterAPI

# Initialize OpenRouter API
api = OpenRouterAPI()
await api.initialize()

# Create chat completion
messages = [
    {"role": "user", "content": "Write a Python function to calculate factorial"}
]

response = await api.create_chat_completion(messages)
print(response["choices"][0]["message"]["content"])
```

#### VS Code Integration

```python
from src.modules.vscode_integration import VSCodeIntegration

# Initialize VS Code integration
vscode = VSCodeIntegration()
await vscode.initialize()

# Open a file
result = await vscode.open_file("example.py")
print(result["message"])

# Execute a VS Code command
result = await vscode.execute_vscode_command("editor.action.formatDocument")
print(result["message"])

# Get workspace information
info = await vscode.get_workspace_info()
print(f"Workspace: {info['workspace_info']['workspace_path']}")
```

### Multi-Agent Communication

The assistant supports multi-agent communication through WebSocket connections. You can create custom agents that communicate with each other:

```python
from src.agents.communication_agent import AgentClient

# Create a custom agent client
agent = AgentClient("custom_agent")
await agent.connect()

# Register message handlers
async def handle_file_message(message):
    print(f"Received file operation: {message.content}")

agent.register_message_handler("file_operation", handle_file_message)

# Send a message to another agent
from src.agents.main_agent import AgentMessage

message = AgentMessage(
    sender="custom_agent",
    recipient="main",
    message_type="file_operation",
    content={"type": "read_file", "path": "example.txt"}
)

await agent.send_message(message)
```

## API Reference

### Core Classes

#### AIDeveloperAssistant
Main orchestrator class that coordinates all modules and agents.

**Methods:**
- `initialize()`: Initialize all modules
- `start()`: Start the assistant
- `stop()`: Stop the assistant
- `register_agent(agent_id, agent)`: Register a new agent
- `send_message_to_agent(agent_id, message)`: Send message to agent

#### FileOperations
Handles file system operations.

**Methods:**
- `read_file(file_path)`: Read file contents
- `write_file(file_path, content)`: Write content to file
- `list_directory(dir_path)`: List directory contents
- `search_files(pattern, directory)`: Search for files

#### TerminalOperations
Manages terminal command execution.

**Methods:**
- `run_command(command, cwd, timeout)`: Run a command
- `run_interactive_command(command, cwd)`: Start interactive process
- `send_input_to_process(process_id, input)`: Send input to process

#### TaskManager
Coordinates asynchronous task execution.

**Methods:**
- `create_task(task_data)`: Create a new task
- `get_task_status(task_id)`: Get task status
- `cancel_task(task_id)`: Cancel a task
- `register_task_handler(task_type, handler)`: Register task handler

#### PlaywrightIntegration
Provides browser automation capabilities.

**Methods:**
- `navigate_to_url(url)`: Navigate to URL
- `click_element(selector)`: Click on element
- `take_screenshot()`: Take screenshot
- `fill_form(selector, value)`: Fill form field

#### OpenRouterAPI
Integrates with OpenRouter for AI capabilities.

**Methods:**
- `create_chat_completion(messages, model)`: Create chat completion
- `stream_chat_completion(messages, model)`: Stream completion
- `get_available_models()`: Get available models

#### VSCodeIntegration
Provides VS Code IDE integration.

**Methods:**
- `open_file(file_path)`: Open file in VS Code
- `execute_vscode_command(command, args)`: Execute VS Code command
- `get_workspace_info()`: Get workspace information

## Development

### Running Tests

```bash
# Install development dependencies
pip install -e .[dev]

# Run tests
pytest tests/

# Run tests with coverage
pytest --cov=src tests/
```

### Code Formatting

```bash
# Format code
black src/

# Sort imports
isort src/

# Lint code
flake8 src/

# Type checking
mypy src/
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support, please open an issue on GitHub or contact the development team.

## Changelog

### v1.0.0
- Initial release
- File operations module
- Terminal operations module
- Multi-agent communication system
- Task manager
- Playwright integration
- OpenRouter API integration
- VS Code integration
- WebSocket-based communication
- Comprehensive configuration management