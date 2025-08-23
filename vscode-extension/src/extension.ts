import * as vscode from 'vscode';
import * as WebSocket from 'ws';

interface AgentMessage {
    sender: string;
    recipient: string;
    message_type: string;
    content: any;
    timestamp: string;
    message_id?: string;
}

interface Task {
    id: string;
    name: string;
    description: string;
    status: string;
    progress: number;
    created_at: string;
    completed_at?: string;
    result?: any;
    error?: string;
}

export class AIDeveloperAssistantExtension {
    private context: vscode.ExtensionContext;
    private ws: WebSocket | null = null;
    private statusBarItem: vscode.StatusBarItem;
    private tasks: Task[] = [];
    private agents: string[] = [];
    private messages: AgentMessage[] = [];
    private disposables: vscode.Disposable[] = [];

    constructor(context: vscode.ExtensionContext) {
        this.context = context;
        this.statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 100);
        this.statusBarItem.text = "$(robot) AI Assistant";
        this.statusBarItem.command = 'ai-assistant.start';
        this.statusBarItem.show();
        
        this.initialize();
    }

    private async initialize() {
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

    private registerCommands() {
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

    private registerTreeViews() {
        // Tasks tree view
        const tasksProvider = new TasksProvider(this.tasks);
        vscode.window.registerTreeDataProvider('ai-assistant.tasks', tasksProvider);

        // Agents tree view
        const agentsProvider = new AgentsProvider(this.agents);
        vscode.window.registerTreeDataProvider('ai-assistant.agents', agentsProvider);

        // Messages tree view
        const messagesProvider = new MessagesProvider(this.messages);
        vscode.window.registerTreeDataProvider('ai-assistant.messages', messagesProvider);
    }

    private async startAssistant() {
        try {
            const config = vscode.workspace.getConfiguration('ai-assistant');
            const host = config.get('host', 'localhost');
            const port = config.get('port', 8081);

            this.ws = new WebSocket(`ws://${host}:${port}`);

            this.ws.on('open', () => {
                this.updateStatus('Connected', 'ai-assistant.active');
                vscode.commands.executeCommand('setContext', 'ai-assistant.active', true);
                this.showNotification('AI Assistant connected successfully!', 'success');
            });

            this.ws.on('message', (data: WebSocket.Data) => {
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

        } catch (error) {
            this.showNotification(`Failed to start assistant: ${error}`, 'error');
        }
    }

    private async stopAssistant() {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
        this.updateStatus('Disconnected', '');
        vscode.commands.executeCommand('setContext', 'ai-assistant.active', false);
        this.showNotification('AI Assistant stopped', 'info');
    }

    private async generateCode() {
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

    private async analyzeCode() {
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

    private async debugCode() {
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

    private async explainCode() {
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

    private async createTask() {
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

    private async showTasks() {
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

    private async sendTask(taskData: any) {
        if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
            this.showNotification('AI Assistant not connected', 'warning');
            return;
        }

        const message: AgentMessage = {
            sender: 'vscode',
            recipient: 'main',
            message_type: 'task_create',
            content: taskData,
            timestamp: new Date().toISOString()
        };

        this.ws.send(JSON.stringify(message));
        this.showNotification('Task created successfully', 'success');
    }

    private handleMessage(data: string) {
        try {
            const message: AgentMessage = JSON.parse(data);

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
        } catch (error) {
            console.error('Error handling message:', error);
        }
    }

    private updateTask(taskData: any) {
        const existingIndex = this.tasks.findIndex(t => t.id === taskData.id);
        if (existingIndex >= 0) {
            this.tasks[existingIndex] = taskData;
        } else {
            this.tasks.push(taskData);
        }
        this.refreshViews();
    }

    private updateAgents(agentsData: any) {
        this.agents = agentsData.agents || [];
        this.refreshViews();
    }

    private addMessage(message: AgentMessage) {
        this.messages.push(message);
        this.refreshViews();
    }

    private refreshViews() {
        vscode.commands.executeCommand('ai-assistant.tasks.refresh');
        vscode.commands.executeCommand('ai-assistant.agents.refresh');
        vscode.commands.executeCommand('ai-assistant.messages.refresh');
    }

    private showTaskDetails(task: Task) {
        const panel = vscode.window.createWebviewPanel(
            'taskDetails',
            `Task: ${task.name}`,
            vscode.ViewColumn.One,
            {}
        );

        panel.webview.html = this.getTaskDetailsHtml(task);
    }

    private getTaskDetailsHtml(task: Task): string {
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

    private getStatusColor(status: string): string {
        switch (status) {
            case 'completed': return '#28a745';
            case 'failed': return '#dc3545';
            case 'running': return '#007acc';
            case 'pending': return '#6c757d';
            default: return '#000000';
        }
    }

    private detectLanguage(languageId: string): string {
        const languageMap: { [key: string]: string } = {
            'python': 'python',
            'javascript': 'javascript',
            'typescript': 'typescript',
            'java': 'java',
            'cpp': 'cpp',
            'c': 'c',
            'go': 'go',
            'rust': 'rust'
        };
        return languageMap[languageId] || 'python';
    }

    private updateStatus(text: string, context: string) {
        this.statusBarItem.text = `$(robot) ${text}`;
        vscode.commands.executeCommand('setContext', context, true);
    }

    private showNotification(message: string, type: 'info' | 'warning' | 'error' | 'success' = 'info') {
        const config = vscode.workspace.getConfiguration('ai-assistant');
        if (!config.get('showNotifications', true)) {
            return;
        }

        switch (type) {
            case 'error':
                vscode.window.showErrorMessage(message);
                break;
            case 'warning':
                vscode.window.showWarningMessage(message);
                break;
            case 'success':
                vscode.window.showInformationMessage(message);
                break;
            default:
                vscode.window.showInformationMessage(message);
        }
    }

    public dispose() {
        this.stopAssistant();
        this.disposables.forEach(d => d.dispose());
        this.statusBarItem.dispose();
    }
}

// Tree View Providers
class TasksProvider implements vscode.TreeDataProvider<TaskItem> {
    private _onDidChangeTreeData: vscode.EventEmitter<TaskItem | undefined | null | void> = new vscode.EventEmitter<TaskItem | undefined | null | void>();
    readonly onDidChangeTreeData: vscode.Event<TaskItem | undefined | null | void> = this._onDidChangeTreeData.event;

    constructor(private tasks: Task[]) {}

    refresh(): void {
        this._onDidChangeTreeData.fire();
    }

    getTreeItem(element: TaskItem): vscode.TreeItem {
        return element;
    }

    getChildren(element?: TaskItem): Thenable<TaskItem[]> {
        if (!element) {
            return Promise.resolve(this.tasks.map(task => new TaskItem(task)));
        }
        return Promise.resolve([]);
    }
}

class TaskItem extends vscode.TreeItem {
    constructor(public task: Task) {
        super(task.name, vscode.TreeItemCollapsibleState.None);
        this.description = task.description;
        this.tooltip = `Status: ${task.status} (${Math.round(task.progress * 100)}%)`;
        this.contextValue = task.status;
        this.iconPath = new vscode.ThemeIcon(this.getIconForStatus(task.status));
    }

    private getIconForStatus(status: string): string {
        switch (status) {
            case 'completed': return 'check';
            case 'failed': return 'error';
            case 'running': return 'loading~spin';
            case 'pending': return 'circle-outline';
            default: return 'circle-outline';
        }
    }
}

class AgentsProvider implements vscode.TreeDataProvider<AgentItem> {
    private _onDidChangeTreeData: vscode.EventEmitter<AgentItem | undefined | null | void> = new vscode.EventEmitter<AgentItem | undefined | null | void>();
    readonly onDidChangeTreeData: vscode.Event<AgentItem | undefined | null | void> = this._onDidChangeTreeData.event;

    constructor(private agents: string[]) {}

    refresh(): void {
        this._onDidChangeTreeData.fire();
    }

    getTreeItem(element: AgentItem): vscode.TreeItem {
        return element;
    }

    getChildren(element?: AgentItem): Thenable<AgentItem[]> {
        if (!element) {
            return Promise.resolve(this.agents.map(agent => new AgentItem(agent)));
        }
        return Promise.resolve([]);
    }
}

class AgentItem extends vscode.TreeItem {
    constructor(public agent: string) {
        super(agent, vscode.TreeItemCollapsibleState.None);
        this.tooltip = `Agent: ${agent}`;
        this.iconPath = new vscode.ThemeIcon('account');
    }
}

class MessagesProvider implements vscode.TreeDataProvider<MessageItem> {
    private _onDidChangeTreeData: vscode.EventEmitter<MessageItem | undefined | null | void> = new vscode.EventEmitter<MessageItem | undefined | null | void>();
    readonly onDidChangeTreeData: vscode.Event<MessageItem | undefined | null | void> = this._onDidChangeTreeData.event;

    constructor(private messages: AgentMessage[]) {}

    refresh(): void {
        this._onDidChangeTreeData.fire();
    }

    getTreeItem(element: MessageItem): vscode.TreeItem {
        return element;
    }

    getChildren(element?: MessageItem): Thenable<MessageItem[]> {
        if (!element) {
            return Promise.resolve(this.messages.slice(-10).map(msg => new MessageItem(msg)));
        }
        return Promise.resolve([]);
    }
}

class MessageItem extends vscode.TreeItem {
    constructor(public message: AgentMessage) {
        super(`${message.sender} -> ${message.recipient}: ${message.message_type}`, vscode.TreeItemCollapsibleState.None);
        this.tooltip = `${new Date(message.timestamp).toLocaleString()}`;
        this.iconPath = new vscode.ThemeIcon('mail');
    }
}

// Extension activation
export function activate(context: vscode.ExtensionContext) {
    const extension = new AIDeveloperAssistantExtension(context);
    context.subscriptions.push(extension);
}

export function deactivate() {}