# AI Developer Assistant - Troubleshooting Guide

This guide provides detailed troubleshooting steps for common issues with the AI Developer Assistant.

## Quick Start Troubleshooting

### 1. Service Won't Start

**Symptoms**: `python main.py` fails or service doesn't start

**Quick Checks**:
```bash
# Check Python version
python --version  # Should be 3.8+

# Check dependencies
pip list | grep -E "(aiohttp|playwright|websockets)"

# Check workspace directory
ls -la workspace/
```

**Common Solutions**:
- Install missing dependencies: `pip install -r requirements.txt`
- Create workspace directory: `mkdir -p workspace`
- Check Python path: `which python`

### 2. WebSocket Connection Issues

**Symptoms**: VS Code extension can't connect, connection refused errors

**Quick Checks**:
```bash
# Check if service is running
ps aux | grep python | grep main.py

# Check port availability
netstat -tulpn | grep 8081

# Test WebSocket connection
wscat -c ws://localhost:8081
```

**Common Solutions**:
- Start the service: `python main.py`
- Check firewall: `sudo ufw status`
- Verify port configuration in `.env`

### 3. API Authentication Issues

**Symptoms**: OpenRouter API errors, authentication failures

**Quick Checks**:
```bash
# Check API key
echo $OPENROUTER_API_KEY

# Test API connection
curl -H "Authorization: Bearer $OPENROUTER_API_KEY" \
     -H "HTTP-Referer: https://ai-developer-assistant.local" \
     https://openrouter.ai/api/v1/models
```

**Common Solutions**:
- Verify API key in `.env`
- Check API key validity
- Test with a simple API call

## Detailed Troubleshooting

### Installation Issues

#### Problem: Dependencies Won't Install

**Error Messages**:
```
ERROR: Could not build wheels for some packages
ERROR: Failed to build package
```

**Solutions**:
1. **Update pip and setuptools**:
   ```bash
   pip install --upgrade pip setuptools wheel
   ```

2. **Install system dependencies**:
   ```bash
   # Ubuntu/Debian
   sudo apt-get update
   sudo apt-get install -y python3-dev build-essential
   
   # CentOS/RHEL
   sudo yum install -y python3-devel gcc-c++
   ```

3. **Use pre-built wheels**:
   ```bash
   pip install --only-binary=all -r requirements.txt
   ```

#### Problem: Playwright Installation Fails

**Error Messages**:
```
ERROR: Failed to install Playwright
ERROR: Browser installation failed
```

**Solutions**:
1. **Install system dependencies**:
   ```bash
   # Ubuntu/Debian
   sudo apt-get install -y \
       gconf-service \
       libasound2 \
       libatk1.0-0 \
       libc6 \
       libcairo2 \
       libcups2 \
       libdbus-1-3 \
       libexpat1 \
       libfontconfig1 \
       libgcc1 \
       libgconf-2-4 \
       libgdk-pixbuf2.0-0 \
       libglib2.0-0 \
       libgtk-3-0 \
       libnspr4 \
       libpango-1.0-0 \
       libpangocairo-1.0-0 \
       libstdc++6 \
       libx11-6 \
       libx11-xcb1 \
       libxcb1 \
       libxcomposite1 \
       libxcursor1 \
       libxdamage1 \
       libxext6 \
       libxfixes3 \
       libxi6 \
       libxrandr2 \
       libxrender1 \
       libxss1 \
       libxtst6 \
       ca-certificates \
       fonts-liberation \
       libappindicator1 \
       libnss3 \
       lsb-release \
       xdg-utils \
       wget
   ```

2. **Install Playwright manually**:
   ```bash
   pip install playwright
   playwright install --with-deps chromium
   ```

3. **Use headless mode**:
   ```bash
   # Set in .env
   PLAYWRIGHT_HEADLESS=true
   ```

### Configuration Issues

#### Problem: Environment Variables Not Loading

**Error Messages**:
```
ERROR: OPENROUTER_API_KEY not found
ERROR: Configuration validation failed
```

**Solutions**:
1. **Check .env file location**:
   ```bash
   ls -la .env
   cat .env
   ```

2. **Verify file format**:
   ```bash
   # Should be KEY=value format
   grep -E "^[A-Z_]+=" .env
   ```

3. **Test configuration loading**:
   ```python
   from src.config.settings import get_settings
   settings = get_settings()
   print(f"API Key: {settings.openrouter_api_key[:10]}...")
   ```

4. **Set environment variables manually**:
   ```bash
   export OPENROUTER_API_KEY="your_key_here"
   python main.py
   ```

#### Problem: Port Already in Use

**Error Messages**:
```
ERROR: Port 8081 already in use
ERROR: Address already in use
```

**Solutions**:
1. **Find process using the port**:
   ```bash
   # Linux/macOS
   lsof -i :8081
   netstat -tulpn | grep 8081
   
   # Windows
   netstat -ano | findstr :8081
   ```

2. **Kill the process**:
   ```bash
   # Linux/macOS
   kill -9 <PID>
   
   # Windows
   taskkill /PID <PID> /F
   ```

3. **Change port in configuration**:
   ```bash
   # In .env
   AGENT_PORT=8082
   VSCODE_PORT=8083
   ```

### Runtime Issues

#### Problem: Memory Usage Too High

**Symptoms**: System becomes slow, memory errors

**Diagnosis**:
```bash
# Monitor memory usage
top
htop
ps aux --sort=-%mem | head

# Check memory leaks
valgrind --leak-check=full --show-leak-kinds=all python main.py
```

**Solutions**:
1. **Reduce concurrent tasks**:
   ```bash
   # In .env
   MAX_CONCURRENT_TASKS=3
   ```

2. **Adjust cache settings**:
   ```python
   # In code
   from src.utils.cache import cache_manager
   cache_manager.max_size = 1000  # Reduce cache size
   cache_manager.default_ttl = 300  # Reduce TTL
   ```

3. **Increase system memory**:
   - Add more RAM to the system
   - Use swap space

4. **Implement memory limits**:
   ```bash
   # Linux ulimit
   ulimit -v 1048576  # 1GB virtual memory limit
   ```

#### Problem: High CPU Usage

**Symptoms**: System becomes unresponsive, CPU usage near 100%

**Diagnosis**:
```bash
# Monitor CPU usage
top
htop
ps aux --sort=-%cpu | head

# Check process threads
ps -T -p <PID>
```

**Solutions**:
1. **Identify resource-intensive tasks**:
   ```python
   # Check task manager statistics
   from src.modules.task_manager import TaskManager
   task_manager = TaskManager()
   stats = await task_manager.get_statistics()
   print(stats)
   ```

2. **Optimize task execution**:
   ```python
   # Reduce task timeout
   TASK_TIMEOUT=60000  # 1 minute instead of 5
   ```

3. **Implement rate limiting**:
   ```python
   # Limit API calls
   from src.modules.openrouter_integration import OpenRouterAPI
   api = OpenRouterAPI()
   api.max_requests_per_minute = 30  # Reduce from 60
   ```

#### Problem: Disk Space Issues

**Symptoms**: File operations fail, disk full errors

**Diagnosis**:
```bash
# Check disk space
df -h
du -sh workspace/
du -sh logs/
```

**Solutions**:
1. **Clean up workspace**:
   ```bash
   # Remove old files
   find workspace/ -type f -mtime +30 -delete
   
   # Clean logs
   find logs/ -name "*.log" -mtime +7 -delete
   ```

2. **Configure log rotation**:
   ```python
   # In logging configuration
   from logging.handlers import RotatingFileHandler
   
   handler = RotatingFileHandler(
       'assistant.log',
       maxBytes=10*1024*1024,  # 10MB
       backupCount=5
   )
   ```

3. **Set file size limits**:
   ```bash
   # In .env
   MAX_FILE_SIZE=5242880  # 5MB instead of 10MB
   ```

### Network Issues

#### Problem: WebSocket Connection Drops

**Symptoms**: VS Code extension disconnects, connection timeouts

**Diagnosis**:
```bash
# Test WebSocket connection
wscat -c ws://localhost:8081

# Check network stability
ping localhost
telnet localhost 8081
```

**Solutions**:
1. **Increase timeout settings**:
   ```bash
   # In .env
   WEBSOCKET_TIMEOUT=60
   ```

2. **Enable keep-alive**:
   ```python
   # In WebSocket configuration
   websocket.ping_interval = 30
   ```

3. **Check firewall settings**:
   ```bash
   # Linux
   sudo ufw status
   sudo ufw allow 8081
   
   # Check iptables
   sudo iptables -L
   ```

#### Problem: API Rate Limiting

**Symptoms**: OpenRouter API errors, request timeouts

**Diagnosis**:
```bash
# Check API rate limits
curl -H "Authorization: Bearer $OPENROUTER_API_KEY" \
     -H "HTTP-Referer: https://ai-developer-assistant.local" \
     https://openrouter.ai/api/v1/rate_limits
```

**Solutions**:
1. **Reduce request frequency**:
   ```python
   # In OpenRouter integration
   api.max_requests_per_minute = 30
   ```

2. **Implement caching**:
   ```python
   # Cache API responses
   from src.utils.cache import cache_manager
   
   @cached(ttl=300)  # 5 minute cache
   async def cached_api_call():
       return await api.create_chat_completion(messages)
   ```

3. **Use batch requests**:
   ```python
   # Combine multiple requests
   batch_messages = [
       {"role": "user", "content": "Question 1"},
       {"role": "user", "content": "Question 2"}
   ]
   ```

### Security Issues

#### Problem: Command Execution Blocked

**Symptoms**: Terminal commands fail with security errors

**Diagnosis**:
```bash
# Check command whitelist
python -c "
from src.utils.security import security_manager
print('Allowed commands:', len(security_manager.get_allowed_commands()))
"
```

**Solutions**:
1. **Check command against whitelist**:
   ```python
   from src.utils.security import security_manager
   
   security_check = security_manager.check_command_safety("ls -la")
   print(security_check)
   ```

2. **Add custom command rules**:
   ```python
   from src.utils.security import CommandRule, CommandRiskLevel
   
   security_manager.add_custom_rule(CommandRule(
       pattern=r"^your-command$",
       risk_level=CommandRiskLevel.LOW_RISK,
       description="Custom allowed command"
   ))
   ```

3. **Temporarily disable security**:
   ```bash
   # In .env (not recommended for production)
   ENABLE_COMMAND_WHITELISTING=false
   ```

#### Problem: Authentication Failures

**Symptoms**: WebSocket authentication fails, token errors

**Diagnosis**:
```bash
# Check authentication logs
grep "auth" logs/assistant.log

# Test token generation
python -c "
from src.utils.auth import auth_manager
token = auth_manager.create_token('test_agent')
print('Token created:', token.token_id)
"
```

**Solutions**:
1. **Verify token configuration**:
   ```python
   # Check token expiration
   from datetime import datetime, timedelta
   print('Token expires:', token.expires_at > datetime.now())
   ```

2. **Regenerate tokens**:
   ```python
   # Revoke old tokens
   auth_manager.revoke_agent_tokens('agent_id')
   
   # Create new token
   new_token = auth_manager.create_token('agent_id')
   ```

3. **Check timestamp synchronization**:
   ```bash
   # Check system time
   date
   ntpq -p  # Check NTP synchronization
   ```

### VS Code Extension Issues

#### Problem: Extension Won't Load

**Symptoms**: VS Code extension doesn't appear, errors in developer console

**Diagnosis**:
```bash
# Check extension installation
code --list-extensions | grep ai-developer-assistant

# Check extension logs
code --verbose
```

**Solutions**:
1. **Reinstall extension**:
   ```bash
   cd vscode-extension
   npm run compile
   code --uninstall-extension ai-developer-assistant
   code --install-extension .
   ```

2. **Check VS Code version compatibility**:
   ```bash
   code --version
   # Requires VS Code 1.74+
   ```

3. **Clear extension cache**:
   ```bash
   # Linux/macOS
   rm -rf ~/.vscode/extensions/ai-developer-assistant*
   
   # Windows
   rmdir /s "%USERPROFILE%\.vscode\extensions\ai-developer-assistant*"
   ```

#### Problem: Extension Can't Connect to Assistant

**Symptoms**: Connection errors, timeout messages

**Diagnosis**:
```bash
# Check extension settings
code --show-settings

# Test connection manually
curl http://localhost:8081/health
```

**Solutions**:
1. **Check extension configuration**:
   ```json
   // In VS Code settings (settings.json)
   {
       "ai-assistant.host": "localhost",
       "ai-assistant.port": 8081,
       "ai-assistant.autoStart": false
   }
   ```

2. **Verify assistant is running**:
   ```bash
   ps aux | grep python | grep main.py
   ```

3. **Check network connectivity**:
   ```bash
   # Test connection to assistant
   telnet localhost 8081
   ```

### Performance Issues

#### Problem: Slow File Operations

**Symptoms**: File operations take too long to complete

**Diagnosis**:
```bash
# Test disk I/O
dd if=/dev/zero of=testfile bs=1M count=100 conv=fdatasync
rm testfile

# Check file system
df -T /workspace
```

**Solutions**:
1. **Enable caching**:
   ```python
   # Cache is enabled by default
   from src.utils.cache import cache_manager
   stats = await cache_manager.get_stats()
   print(f"Cache hit rate: {stats['hit_rate']:.2%}")
   ```

2. **Optimize file operations**:
   ```python
   # Use async file operations
   import aiofiles
   
   async def read_large_file():
       async with aiofiles.open('large_file.txt', 'r') as f:
           content = await f.read()
   ```

3. **Check disk health**:
   ```bash
   # Check disk health
   smartctl -a /dev/sda  # Linux
   diskutil verifyVolume /  # macOS
   ```

#### Problem: High Latency in AI Responses

**Symptoms**: AI API calls take too long

**Diagnosis**:
```bash
# Test network latency
ping openrouter.ai
traceroute openrouter.ai

# Test API response time
curl -w "@curl-format.txt" -o /dev/null -s \
     -H "Authorization: Bearer $OPENROUTER_API_KEY" \
     https://openrouter.ai/api/v1/chat/completions \
     -d '{"model":"anthropic/claude-3-sonnet","messages":[{"role":"user","content":"test"}]}'
```

**Solutions**:
1. **Use faster models**:
   ```bash
   # In .env
   OPENROUTER_MODEL=anthropic/claude-3-haiku
   ```

2. **Implement response streaming**:
   ```python
   # Use streaming for faster feedback
   async for chunk in api.stream_chat_completion(messages):
       print(chunk['choices'][0]['delta']['content'])
   ```

3. **Cache AI responses**:
   ```python
   # Cache similar queries
   @cached(ttl=1800)  # 30 minute cache
   async def cached_ai_response(prompt):
       return await api.create_chat_completion([
           {"role": "user", "content": prompt}
       ])
   ```

## Advanced Troubleshooting

### Debug Mode

Enable comprehensive debugging:

```bash
# Enable debug logging
LOG_LEVEL=DEBUG python main.py

# Enable debug mode for specific modules
DEBUG_MODULES=terminal,cache python main.py
```

### Performance Profiling

Profile the application:

```bash
# Use cProfile
python -m cProfile -s cumtime main.py

# Use memory profiler
pip install memory-profiler
python -m memory_profiler main.py

# Use line profiler
pip install line_profiler
python -m line_profiler main.py
```

### Network Debugging

Debug network issues:

```bash
# Capture network traffic
tcpdump -i any port 8081 -w network_capture.pcap

# Analyze with Wireshark
wireshark network_capture.pcap

# Check SSL/TLS
openssl s_client -connect localhost:8081 -showcerts
```

### Log Analysis

Analyze logs systematically:

```bash
# Extract error messages
grep "ERROR" logs/assistant.log | sort | uniq -c

# Extract warnings
grep "WARN" logs/assistant.log | sort | uniq -c

# Analyze performance issues
grep "performance\|slow\|timeout" logs/assistant.log

# Monitor security events
grep "auth\|security\|blocked" logs/assistant.log
```

## Getting Help

### When to Ask for Help

- **Critical Issues**: Service down, data loss, security breaches
- **Persistent Issues**: Problems that recur after multiple restarts
- **Performance Issues**: Consistently slow performance
- **Configuration Issues**: Unable to resolve configuration problems

### How to Ask for Help

1. **Gather Information**:
   ```bash
   # System information
   uname -a
   python --version
   pip list | grep -E "(aiohttp|playwright|websockets)"
   
   # Service status
   systemctl status ai-developer-assistant
   
   # Recent logs
   tail -50 logs/assistant.log
   ```

2. **Describe the Problem**:
   - What were you trying to do?
   - What happened instead?
   - What error messages did you see?
   - When did the problem start?

3. **Provide Context**:
   - Operating system and version
   - Python version
   - Application version
   - Configuration settings
   - Recent changes

### Support Channels

1. **GitHub Issues**: Report bugs and feature requests
2. **Documentation**: Check README.md and this guide
3. **Community**: Join our Discord server
4. **Enterprise Support**: Contact support@ai-developer-assistant.com

### Common Solutions Summary

| Issue | Common Solution |
|-------|------------------|
| Service won't start | Check dependencies, create workspace directory |
| Connection refused | Check if service is running, verify port |
| API authentication failed | Verify API key, test API connection |
| Memory issues | Reduce concurrent tasks, adjust cache settings |
| Command blocked | Check command whitelist, add custom rules |
| Slow performance | Enable caching, optimize settings |
| Extension issues | Reinstall extension, check configuration |

---

Remember to always check the logs first, as they contain the most detailed information about what's happening in the system.