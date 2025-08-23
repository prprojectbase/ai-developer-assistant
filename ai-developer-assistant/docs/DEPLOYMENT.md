# AI Developer Assistant - Deployment Guide

This guide provides comprehensive instructions for deploying the AI Developer Assistant in production environments.

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Deployment Options](#deployment-options)
5. [Security Considerations](#security-considerations)
6. [Performance Optimization](#performance-optimization)
7. [Monitoring and Logging](#monitoring-and-logging)
8. [Troubleshooting](#troubleshooting)
9. [Backup and Recovery](#backup-and-recovery)

## System Requirements

### Minimum Requirements
- **CPU**: 2 cores
- **RAM**: 4GB
- **Storage**: 10GB free space
- **OS**: Linux, macOS, or Windows 10+
- **Python**: 3.8 or higher
- **Network**: Internet connection for AI API access

### Recommended Requirements
- **CPU**: 4+ cores
- **RAM**: 8GB+
- **Storage**: 50GB+ SSD
- **OS**: Ubuntu 20.04+ or CentOS 8+
- **Python**: 3.9+
- **Network**: Stable internet connection

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/ai-developer-assistant.git
cd ai-developer-assistant
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Install Playwright Browsers

```bash
playwright install
```

### 5. Install VS Code Extension (Optional)

```bash
cd vscode-extension
npm install
npm run compile
code --install-extension .
```

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# OpenRouter API Configuration
OPENROUTER_API_KEY=your_openrouter_api_key_here
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_MODEL=anthropic/claude-3-sonnet

# Communication Settings
AGENT_PORT=8081
AGENT_HOST=localhost

# VS Code Integration
VSCODE_PORT=8080
VSCODE_HOST=localhost

# Playwright Configuration
PLAYWRIGHT_HEADLESS=true
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

# Security Settings
ENABLE_COMMAND_WHITELISTING=true
MAX_COMMAND_LENGTH=1000
BLOCK_NETWORK_COMMANDS=true
ENABLE_WEBSOCKET_AUTH=true
```

### Configuration Validation

Validate your configuration:

```bash
python -c "
from src.config.settings import get_settings
settings = get_settings()
print('Configuration loaded successfully')
print(f'Workspace: {settings.workspace_dir}')
print(f'Agent Port: {settings.agent_port}')
"
```

## Deployment Options

### 1. Development Deployment

For development and testing:

```bash
python main.py
```

### 2. Production Deployment with Systemd

Create a systemd service file:

```ini
# /etc/systemd/system/ai-developer-assistant.service
[Unit]
Description=AI Developer Assistant
After=network.target

[Service]
Type=simple
User=ai-assistant
WorkingDirectory=/opt/ai-developer-assistant
Environment=PATH=/opt/ai-developer-assistant/venv/bin
ExecStart=/opt/ai-developer-assistant/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable ai-developer-assistant
sudo systemctl start ai-developer-assistant
```

### 3. Docker Deployment

Create a Dockerfile:

```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright
RUN playwright install --with-deps

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 ai-assistant && \
    chown -R ai-assistant:ai-assistant /app
USER ai-assistant

# Create workspace directory
RUN mkdir -p /app/workspace

# Expose ports
EXPOSE 8081 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8081/health || exit 1

CMD ["python", "main.py"]
```

Build and run:

```bash
docker build -t ai-developer-assistant .
docker run -d \
  --name ai-developer-assistant \
  -p 8081:8081 \
  -p 8080:8080 \
  -v $(pwd)/workspace:/app/workspace \
  --env-file .env \
  ai-developer-assistant
```

### 4. Kubernetes Deployment

Create a deployment manifest:

```yaml
# ai-developer-assistant-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ai-developer-assistant
spec:
  replicas: 2
  selector:
    matchLabels:
      app: ai-developer-assistant
  template:
    metadata:
      labels:
        app: ai-developer-assistant
    spec:
      containers:
      - name: ai-developer-assistant
        image: ai-developer-assistant:latest
        ports:
        - containerPort: 8081
        - containerPort: 8080
        env:
        - name: OPENROUTER_API_KEY
          valueFrom:
            secretKeyRef:
              name: ai-assistant-secrets
              key: openrouter-api-key
        - name: AGENT_PORT
          value: "8081"
        - name: WORKSPACE_DIR
          value: "/workspace"
        volumeMounts:
        - name: workspace
          mountPath: /workspace
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8081
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8081
          initialDelaySeconds: 5
          periodSeconds: 5
      volumes:
      - name: workspace
        persistentVolumeClaim:
          claimName: ai-assistant-workspace
---
apiVersion: v1
kind: Service
metadata:
  name: ai-developer-assistant-service
spec:
  selector:
    app: ai-developer-assistant
  ports:
  - name: agent-port
    port: 8081
    targetPort: 8081
  - name: vscode-port
    port: 8080
    targetPort: 8080
  type: LoadBalancer
```

## Security Considerations

### 1. API Key Management

- **Never commit API keys to version control**
- **Use environment variables or secret management systems**
- **Rotate API keys regularly**
- **Use different keys for development and production**

### 2. Network Security

- **Use HTTPS in production**
- **Configure firewall rules to restrict access**
- **Use VPN for internal access**
- **Enable SSL/TLS for WebSocket connections**

### 3. Command Security

The system includes built-in command whitelisting:

```python
# Enable command whitelisting in configuration
ENABLE_COMMAND_WHITELISTING=true

# Customize allowed commands
from src.utils.security import TerminalSecurityManager, CommandRule, CommandRiskLevel

security_manager = TerminalSecurityManager()
security_manager.add_custom_rule(CommandRule(
    pattern=r"^python3\s+",
    risk_level=CommandRiskLevel.LOW_RISK,
    description="Python execution",
    require_confirmation=True
))
```

### 4. File System Security

- **Restrict file operations to workspace directory**
- **Set appropriate file permissions**
- **Monitor for suspicious file access patterns**
- **Regular security audits**

### 5. Authentication

- **WebSocket authentication is enabled by default**
- **Use strong authentication tokens**
- **Implement token expiration**
- **Monitor for unauthorized access attempts**

## Performance Optimization

### 1. Caching

The system includes intelligent caching:

```python
# Configure cache settings
from src.utils.cache import cache_manager

# Adjust cache size and TTL
cache_manager.max_size = 2000  # Increase cache size
cache_manager.default_ttl = 600  # 10 minute TTL
```

### 2. Connection Pooling

```python
# Configure HTTP connection pooling for API calls
from src.modules.openrouter_integration import OpenRouterAPI

api = OpenRouterAPI()
# Connection pooling is automatically enabled
```

### 3. Resource Management

- **Monitor memory usage**
- **Set appropriate limits on concurrent tasks**
- **Implement graceful degradation under load**
- **Use resource quotas**

### 4. Database Optimization (if using external database)

- **Index frequently accessed data**
- **Use connection pooling**
- **Implement query optimization**
- **Regular database maintenance**

## Monitoring and Logging

### 1. Logging Configuration

```python
# Configure logging levels
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('assistant.log'),
        logging.StreamHandler()
    ]
)
```

### 2. Health Checks

The system provides health endpoints:

```bash
# Check system health
curl http://localhost:8081/health

# Check specific module health
curl http://localhost:8081/health/modules
```

### 3. Metrics Collection

```python
# Get system statistics
from src.modules.task_manager import TaskManager

task_manager = TaskManager()
stats = await task_manager.get_statistics()
print(f"Task statistics: {stats}")
```

### 4. External Monitoring

Integrate with monitoring tools:

- **Prometheus** for metrics collection
- **Grafana** for visualization
- **ELK Stack** for log analysis
- **Datadog** or **New Relic** for APM

## Troubleshooting

### Common Issues and Solutions

#### 1. Connection Issues

**Problem**: WebSocket connection fails
```bash
Error: Connection refused to ws://localhost:8081
```

**Solution**:
- Check if the service is running: `systemctl status ai-developer-assistant`
- Verify port configuration: `netstat -tulpn | grep 8081`
- Check firewall rules: `sudo ufw status`

#### 2. API Key Issues

**Problem**: OpenRouter API authentication fails
```bash
Error: Invalid API key or authentication failed
```

**Solution**:
- Verify API key in `.env` file
- Check API key validity
- Test API connection manually
- Review API rate limits

#### 3. Memory Issues

**Problem**: System runs out of memory
```bash
Error: MemoryError: Unable to allocate array
```

**Solution**:
- Monitor memory usage: `htop` or `top`
- Reduce concurrent tasks: `MAX_CONCURRENT_TASKS=3`
- Increase system memory
- Implement memory limits

#### 4. File Permission Issues

**Problem**: File operations fail with permission errors
```bash
Error: Permission denied: '/workspace/file.txt'
```

**Solution**:
- Check file permissions: `ls -la /workspace`
- Verify user permissions: `whoami`
- Adjust ownership: `sudo chown -R ai-assistant:ai-assistant /workspace`

#### 5. Command Execution Issues

**Problem**: Terminal commands are blocked
```bash
Error: Command blocked by security policy
```

**Solution**:
- Check command whitelist configuration
- Verify command syntax
- Review security logs
- Adjust security settings if needed

### Debug Mode

Enable debug logging:

```bash
LOG_LEVEL=DEBUG python main.py
```

### Performance Issues

#### 1. Slow Response Times

**Symptoms**: Commands take too long to execute

**Diagnosis**:
```bash
# Check system resources
top
htop

# Check disk I/O
iostat -x 1

# Check network latency
ping openrouter.ai
```

**Solutions**:
- Increase system resources
- Optimize caching settings
- Reduce concurrent operations
- Check network connectivity

#### 2. High Memory Usage

**Symptoms**: Memory usage continuously increases

**Diagnosis**:
```bash
# Monitor memory usage
free -h
ps aux --sort=-%mem | head

# Check for memory leaks
valgrind --leak-check=full python main.py
```

**Solutions**:
- Restart the service
- Adjust cache settings
- Monitor for memory leaks
- Implement memory limits

### Log Analysis

Analyze logs for issues:

```bash
# View recent logs
tail -f logs/assistant.log

# Search for errors
grep "ERROR" logs/assistant.log

# Analyze performance
grep "performance" logs/assistant.log
```

## Backup and Recovery

### 1. Configuration Backup

```bash
# Backup configuration files
tar -czf config-backup-$(date +%Y%m%d).tar.gz .env vscode-extension/

# Backup workspace
tar -czf workspace-backup-$(date +%Y%m%d).tar.gz workspace/
```

### 2. Automated Backup Script

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/backups/ai-developer-assistant"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Backup configuration
tar -czf "$BACKUP_DIR/config-$DATE.tar.gz" .env vscode-extension/

# Backup workspace
tar -czf "$BACKUP_DIR/workspace-$DATE.tar.gz" workspace/

# Backup logs
tar -czf "$BACKUP_DIR/logs-$DATE.tar.gz" logs/

# Keep only last 7 days of backups
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +7 -delete

echo "Backup completed: $DATE"
```

### 3. Recovery Procedures

#### Configuration Recovery

```bash
# Restore configuration
tar -xzf config-backup-YYYYMMDD.tar.gz

# Restart service
sudo systemctl restart ai-developer-assistant
```

#### Workspace Recovery

```bash
# Restore workspace
tar -xzf workspace-backup-YYYYMMDD.tar.gz

# Set correct permissions
sudo chown -R ai-assistant:ai-assistant workspace/
```

### 4. Disaster Recovery

1. **System Failure**: Restore from backup on new server
2. **Data Loss**: Restore workspace and configuration
3. **Security Incident**: Change API keys, review logs, restore from clean backup

## Support

For additional support:

1. **Documentation**: Check the main README.md
2. **Issues**: Report bugs on GitHub
3. **Community**: Join our Discord community
4. **Enterprise**: Contact support@ai-developer-assistant.com

---

Remember to regularly update your deployment and follow security best practices to ensure optimal performance and security.