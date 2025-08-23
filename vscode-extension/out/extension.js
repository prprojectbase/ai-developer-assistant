"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || function (mod) {
    if (mod && mod.__esModule) return mod;
    var result = {};
    if (mod != null) for (var k in mod) if (k !== "default" && Object.prototype.hasOwnProperty.call(mod, k)) __createBinding(result, mod, k);
    __setModuleDefault(result, mod);
    return result;
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.deactivate = exports.activate = exports.AIDeveloperAssistantExtension = void 0;
const vscode = __importStar(require("vscode"));
const WebSocket = __importStar(require("ws"));
class TasksProvider {
    constructor(tasks) {
        this.tasks = tasks;
        this._onDidChangeTreeData = new vscode.EventEmitter();
        this.onDidChangeTreeData = this._onDidChangeTreeData.event;
    }
    refresh() {
        this._onDidChangeTreeData.fire();
    }
    getTreeItem(element) {
        return element;
    }
    getChildren(element) {
        if (!element) {
            return Promise.resolve(this.tasks.map(task => new TaskItem(task)));
        }
        return Promise.resolve([]);
    }
}
class TaskItem extends vscode.TreeItem {
    constructor(task) {
        super(`${task.name} (${task.status})`, vscode.TreeItemCollapsibleState.None);
        this.task = task;
        this.tooltip = `${task.description}\nProgress: ${Math.round(task.progress * 100)}%`;
        this.iconPath = new vscode.ThemeIcon(this.getIconForStatus(task.status));
        this.contextValue = task.status;
    }
    getIconForStatus(status) {
        switch (status) {
            case 'completed': return 'check';
            case 'failed': return 'error';
            case 'running': return 'loading~spin';
            default: return 'tasklist';
        }
    }
}
class AgentsProvider {
    constructor(agents) {
        this.agents = agents;
        this._onDidChangeTreeData = new vscode.EventEmitter();
        this.onDidChangeTreeData = this._onDidChangeTreeData.event;
    }
    refresh() {
        this._onDidChangeTreeData.fire();
    }
    getTreeItem(element) {
        return element;
    }
    getChildren(element) {
        if (!element) {
            return Promise.resolve(this.agents.map(agent => new AgentItem(agent)));
        }
        return Promise.resolve([]);
    }
}
class AgentItem extends vscode.TreeItem {
    constructor(agent) {
        super(agent, vscode.TreeItemCollapsibleState.None);
        this.agent = agent;
        this.tooltip = `Agent: ${agent}`;
        this.iconPath = new vscode.ThemeIcon('account');
        this.contextValue = 'agent';
    }
}
class MessagesProvider {
    constructor(messages) {
        this.messages = messages;
        this._onDidChangeTreeData = new vscode.EventEmitter();
        this.onDidChangeTreeData = this._onDidChangeTreeData.event;
    }
    refresh() {
        this._onDidChangeTreeData.fire();
    }
    getTreeItem(element) {
        return element;
    }
    getChildren(element) {
        if (!element) {
            return Promise.resolve(this.messages.map(message => new MessageItem(message)));
        }
        return Promise.resolve([]);
    }
}
class MessageItem extends vscode.TreeItem {
    constructor(message) {
        super(`${message.sender} -> ${message.recipient}: ${message.message_type}`, vscode.TreeItemCollapsibleState.None);
        this.message = message;
        this.tooltip = `${new Date(message.timestamp).toLocaleString()}`;
        this.iconPath = new vscode.ThemeIcon('mail');
    }
}
class AIDeveloperAssistantExtension {
    constructor(context) {
        this.ws = null;
        this.tasks = [];
        this.agents = [];
        this.messages = [];
        this.disposables = [];
        this.context = context;
        this.statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 100);
        this.statusBarItem.text = "$(robot) AI Assistant";
        this.statusBarItem.command = 'ai-assistant.start';
        this.statusBarItem.show();
        // Initialize tree providers
        this.tasksProvider = new TasksProvider(this.tasks);
        this.agentsProvider = new AgentsProvider(this.agents);
        this.messagesProvider = new MessagesProvider(this.messages);
        this.initialize();
    }
    async initialize() {
        // Register commands
        this.registerCommands();
        // Register tree views
        this.registerTreeViews();
        // Auto-start if configured
        const config = vscode.workspace.getConfiguration('ai-assistant');
        if (config.get('autoStart', false)) {
            await this.startAssistant();
        }
    }
    registerCommands() {
        // Start assistant
        const startCommand = vscode.commands.registerCommand('ai-assistant.start', async () => {
            await this.startAssistant();
        });
        this.disposables.push(startCommand);
        // Stop assistant
        const stopCommand = vscode.commands.registerCommand('ai-assistant.stop', async () => {
            await this.stopAssistant();
        });
        this.disposables.push(stopCommand);
        // Generate code
        const generateCodeCommand = vscode.commands.registerCommand('ai-assistant.generateCode', async () => {
            await this.generateCode();
        });
        this.disposables.push(generateCodeCommand);
        // Analyze code
        const analyzeCodeCommand = vscode.commands.registerCommand('ai-assistant.analyzeCode', async () => {
            await this.analyzeCode();
        });
        this.disposables.push(analyzeCodeCommand);
        // Debug code
        const debugCodeCommand = vscode.commands.registerCommand('ai-assistant.debugCode', async () => {
            await this.debugCode();
        });
        this.disposables.push(debugCodeCommand);
        // Explain code
        const explainCodeCommand = vscode.commands.registerCommand('ai-assistant.explainCode', async () => {
            await this.explainCode();
        });
        this.disposables.push(explainCodeCommand);
        // Create task
        const createTaskCommand = vscode.commands.registerCommand('ai-assistant.createTask', async () => {
            await this.createTask();
        });
        this.disposables.push(createTaskCommand);
        // Show tasks
        const showTasksCommand = vscode.commands.registerCommand('ai-assistant.showTasks', async () => {
            await this.showTasks();
        });
        this.disposables.push(showTasksCommand);
    }
    registerTreeViews() {
        // Tasks tree view
        vscode.window.registerTreeDataProvider('ai-assistant.tasks', this.tasksProvider);
        // Agents tree view
        vscode.window.registerTreeDataProvider('ai-assistant.agents', this.agentsProvider);
        // Messages tree view
        vscode.window.registerTreeDataProvider('ai-assistant.messages', this.messagesProvider);
    }
    async startAssistant() {
        try {
            const config = vscode.workspace.getConfiguration('ai-assistant');
            const host = config.get('host', 'localhost');
            const port = config.get('port', 8081);
            this.ws = new WebSocket(`ws://${host}:${port}`);
            if (this.ws) {
                this.ws.on('open', () => {
                    this.updateStatus('Connected', 'ai-assistant.active');
                    vscode.commands.executeCommand('setContext', 'ai-assistant.active', true);
                    this.showNotification('AI Assistant connected successfully!', 'success');
                });
                this.ws.on('message', (data) => {
                    this.handleMessage(data.toString());
                });
                this.ws.on('close', () => {
                    this.updateStatus('Disconnected', '');
                    vscode.commands.executeCommand('setContext', 'ai-assistant.active', false);
                    this.showNotification('AI Assistant disconnected', 'warning');
                });
                this.ws.on('error', (error) => {
                    this.showNotification(`Connection error: ${error.message}`, 'error');
                });
            }
        }
        catch (error) {
            this.showNotification(`Failed to start assistant: ${error.message}`, 'error');
        }
    }
    async stopAssistant() {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
        this.updateStatus('Disconnected', '');
        vscode.commands.executeCommand('setContext', 'ai-assistant.active', false);
        this.showNotification('AI Assistant stopped', 'info');
    }
    async generateCode() {
        const editor = vscode.window.activeTextEditor;
        if (!editor) {
            this.showNotification('No active editor', 'warning');
            return;
        }
        const selection = editor.selection;
        const selectedText = editor.document.getText(selection);
        const prompt = await vscode.window.showInputBox({
            prompt: 'What code would you like to generate?',
            placeHolder: 'e.g., Create a function that calculates factorial'
        });
        if (!prompt) {
            return;
        }
        const language = await vscode.window.showQuickPick([
            'python', 'javascript', 'typescript', 'java', 'cpp', 'c', 'go', 'rust'
        ], {
            placeHolder: 'Select programming language'
        });
        if (!language) {
            return;
        }
        await this.sendTask({
            name: 'Generate Code',
            description: `Generate ${language} code for: ${prompt}`,
            type: 'generate_code',
            parameters: {
                prompt,
                language,
                context: selectedText
            }
        });
    }
    async analyzeCode() {
        const editor = vscode.window.activeTextEditor;
        if (!editor) {
            this.showNotification('No active editor', 'warning');
            return;
        }
        const selection = editor.selection;
        const selectedText = editor.document.getText(selection);
        if (!selectedText) {
            this.showNotification('No code selected', 'warning');
            return;
        }
        const language = this.detectLanguage(editor.document.languageId);
        await this.sendTask({
            name: 'Analyze Code',
            description: 'Analyze selected code',
            type: 'analyze_code',
            parameters: {
                code: selectedText,
                language
            }
        });
    }
    async debugCode() {
        const editor = vscode.window.activeTextEditor;
        if (!editor) {
            this.showNotification('No active editor', 'warning');
            return;
        }
        const selection = editor.selection;
        const selectedText = editor.document.getText(selection);
        if (!selectedText) {
            this.showNotification('No code selected', 'warning');
            return;
        }
        const errorMessage = await vscode.window.showInputBox({
            prompt: 'What error are you encountering?',
            placeHolder: 'e.g., TypeError: cannot concatenate str and int'
        });
        if (!errorMessage) {
            return;
        }
        const language = this.detectLanguage(editor.document.languageId);
        await this.sendTask({
            name: 'Debug Code',
            description: 'Debug selected code',
            type: 'debug_code',
            parameters: {
                code: selectedText,
                error: errorMessage,
                language
            }
        });
    }
    async explainCode() {
        const editor = vscode.window.activeTextEditor;
        if (!editor) {
            this.showNotification('No active editor', 'warning');
            return;
        }
        const selection = editor.selection;
        const selectedText = editor.document.getText(selection);
        if (!selectedText) {
            this.showNotification('No code selected', 'warning');
            return;
        }
        await this.sendTask({
            name: 'Explain Code',
            description: 'Explain selected code',
            type: 'explain_concept',
            parameters: {
                concept: 'Code Explanation',
                context: selectedText
            }
        });
    }
    async createTask() {
        const name = await vscode.window.showInputBox({
            prompt: 'Task name',
            placeHolder: 'e.g., Process data files'
        });
        if (!name) {
            return;
        }
        const description = await vscode.window.showInputBox({
            prompt: 'Task description',
            placeHolder: 'e.g., Process all CSV files in the data directory'
        });
        if (!description) {
            return;
        }
        const taskType = await vscode.window.showQuickPick([
            'file_operation',
            'terminal_command',
            'generate_code',
            'analyze_code',
            'playwright_action'
        ], {
            placeHolder: 'Select task type'
        });
        if (!taskType) {
            return;
        }
        await this.sendTask({
            name,
            description,
            type: taskType,
            parameters: {}
        });
    }
    async showTasks() {
        // Show tasks in a quick pick
        const taskItems = this.tasks.map(task => ({
            label: `${task.name} (${task.status})`,
            description: task.description,
            detail: `Progress: ${Math.round(task.progress * 100)}%`,
            task
        }));
        const selected = await vscode.window.showQuickPick(taskItems, {
            placeHolder: 'Select a task to view details'
        });
        if (selected) {
            this.showTaskDetails(selected.task);
        }
    }
    async sendTask(taskData) {
        if (!this.ws || this.ws.readyState !== 1) { // WebSocket.OPEN = 1
            this.showNotification('AI Assistant not connected', 'warning');
            return;
        }
        const message = {
            sender: 'vscode',
            recipient: 'main',
            message_type: 'task_create',
            content: taskData,
            timestamp: new Date().toISOString()
        };
        this.ws.send(JSON.stringify(message));
        this.showNotification('Task created successfully', 'success');
    }
    handleMessage(data) {
        try {
            const message = JSON.parse(data);
            switch (message.message_type) {
                case 'task_update':
                    this.updateTask(message.content);
                    break;
                case 'agent_update':
                    this.updateAgents(message.content);
                    break;
                case 'message':
                    this.addMessage(message);
                    break;
                case 'notification':
                    this.showNotification(message.content.message, message.content.type);
                    break;
            }
        }
        catch (error) {
            console.error('Error handling message:', error);
        }
    }
    updateTask(taskData) {
        const existingIndex = this.tasks.findIndex(t => t.id === taskData.id);
        if (existingIndex >= 0) {
            this.tasks[existingIndex] = taskData;
        }
        else {
            this.tasks.push(taskData);
        }
        this.refreshViews();
    }
    updateAgents(agentsData) {
        this.agents = agentsData.agents || [];
        this.refreshViews();
    }
    addMessage(message) {
        this.messages.push(message);
        this.refreshViews();
    }
    refreshViews() {
        this.tasksProvider.refresh();
        this.agentsProvider.refresh();
        this.messagesProvider.refresh();
    }
    showTaskDetails(task) {
        const panel = vscode.window.createWebviewPanel('taskDetails', `Task: ${task.name}`, vscode.ViewColumn.One, {});
        panel.webview.html = this.getTaskDetailsHtml(task);
    }
    getTaskDetailsHtml(task) {
        return `
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Task Details</title>
                <style>
                    body { font-family: Arial, sans-serif; padding: 20px; }
                    .header { border-bottom: 1px solid #ccc; padding-bottom: 10px; margin-bottom: 20px; }
                    .status-${task.status} { color: ${this.getStatusColor(task.status)}; }
                    .progress { width: 100%; background-color: #f0f0f0; border-radius: 4px; }
                    .progress-bar { height: 20px; background-color: #007acc; border-radius: 4px; width: ${task.progress * 100}%; }
                    .section { margin-bottom: 15px; }
                    pre { background-color: #f5f5f5; padding: 10px; border-radius: 4px; overflow-x: auto; }
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>${task.name}</h1>
                    <p><strong>Status:</strong> <span class="status-${task.status}">${task.status}</span></p>
                    <p><strong>Created:</strong> ${new Date(task.created_at).toLocaleString()}</p>
                    ${task.completed_at ? `<p><strong>Completed:</strong> ${new Date(task.completed_at).toLocaleString()}</p>` : ''}
                </div>
                
                <div class="section">
                    <h2>Description</h2>
                    <p>${task.description}</p>
                </div>
                
                <div class="section">
                    <h2>Progress</h2>
                    <div class="progress">
                        <div class="progress-bar"></div>
                    </div>
                    <p>${Math.round(task.progress * 100)}% complete</p>
                </div>
                
                ${task.result ? `
                <div class="section">
                    <h2>Result</h2>
                    <pre>${JSON.stringify(task.result, null, 2)}</pre>
                </div>
                ` : ''}
                
                ${task.error ? `
                <div class="section">
                    <h2>Error</h2>
                    <pre style="color: red;">${task.error}</pre>
                </div>
                ` : ''}
            </body>
            </html>
        `;
    }
    getStatusColor(status) {
        switch (status) {
            case 'completed': return '#28a745';
            case 'failed': return '#dc3545';
            case 'running': return '#007bff';
            case 'pending': return '#6c757d';
            default: return '#000000';
        }
    }
    detectLanguage(languageId) {
        const languageMap = {
            'python': 'python',
            'javascript': 'javascript',
            'typescript': 'typescript',
            'java': 'java',
            'cpp': 'cpp',
            'c': 'c',
            'go': 'go',
            'rust': 'rust',
            'html': 'html',
            'css': 'css',
            'json': 'json',
            'xml': 'xml',
            'yaml': 'yaml',
            'markdown': 'markdown'
        };
        return languageMap[languageId] || 'text';
    }
    updateStatus(text, context) {
        this.statusBarItem.text = `$(robot) ${text}`;
        this.statusBarItem.command = context === 'ai-assistant.active' ? 'ai-assistant.stop' : 'ai-assistant.start';
    }
    showNotification(message, type) {
        if (type === 'error') {
            vscode.window.showErrorMessage(message);
        }
        else if (type === 'warning') {
            vscode.window.showWarningMessage(message);
        }
        else if (type === 'success') {
            vscode.window.showInformationMessage(message);
        }
        else {
            vscode.window.showInformationMessage(message);
        }
    }
    dispose() {
        this.stopAssistant();
        this.disposables.forEach(d => d.dispose());
        this.statusBarItem.dispose();
    }
}
exports.AIDeveloperAssistantExtension = AIDeveloperAssistantExtension;
// Extension activation
function activate(context) {
    const extension = new AIDeveloperAssistantExtension(context);
    context.subscriptions.push(extension);
}
exports.activate = activate;
function deactivate() { }
exports.deactivate = deactivate;
//# sourceMappingURL=extension.js.map