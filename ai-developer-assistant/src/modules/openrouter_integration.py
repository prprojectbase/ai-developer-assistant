import asyncio
import logging
import json
import time
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, field
from datetime import datetime
import aiohttp
import async_timeout

from ..config.settings import get_settings


@dataclass
class ChatMessage:
    """Chat message structure"""
    role: str
    content: str
    name: Optional[str] = None
    function_call: Optional[Dict[str, Any]] = None


@dataclass
class ChatCompletionRequest:
    """Chat completion request structure"""
    model: str
    messages: List[ChatMessage]
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    stop: Optional[Union[str, List[str]]] = None
    stream: bool = False
    functions: Optional[List[Dict[str, Any]]] = None
    function_call: Optional[Union[str, Dict[str, str]]] = None


@dataclass
class ChatCompletionResponse:
    """Chat completion response structure"""
    id: str
    object: str
    created: int
    model: str
    choices: List[Dict[str, Any]]
    usage: Optional[Dict[str, int]] = None
    system_fingerprint: Optional[str] = None


class OpenRouterAPI:
    """OpenRouter API integration for the AI Developer Assistant"""
    
    def __init__(self):
        self.settings = get_settings()
        self.logger = logging.getLogger(__name__)
        
        # API configuration - get API key securely
        from ..config.settings import get_openrouter_api_key
        self.api_key = get_openrouter_api_key()
        if not self.api_key:
            self.logger.warning("No OpenRouter API key found. Some features may not work.")
        
        self.base_url = self.settings.openrouter_base_url
        self.default_model = self.settings.openrouter_model
        
        # HTTP session with connection pooling
        self.session: Optional[aiohttp.ClientSession] = None
        self.connector: Optional[aiohttp.TCPConnector] = None
        
        # Connection pooling settings
        self.max_connections = 100
        self.max_per_host = 30
        self.connection_timeout = 30
        self.read_timeout = 60
        
        # Rate limiting
        self.request_timestamps: List[float] = []
        self.max_requests_per_minute = 60
        
        # Statistics
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_tokens_used": 0,
            "average_response_time": 0.0,
            "connection_pool_size": 0,
            "active_connections": 0
        }
        
        # Available models
        self.available_models: List[Dict[str, Any]] = []
        
    async def initialize(self) -> None:
        """Initialize the OpenRouter API integration"""
        self.logger.info("Initializing OpenRouter API integration...")
        
        # Check if API key is available
        if not self.api_key:
            self.logger.error("No OpenRouter API key available. Cannot initialize API integration.")
            return
        
        # Create connection pool
        self.connector = aiohttp.TCPConnector(
            limit=self.max_connections,
            limit_per_host=self.max_per_host,
            ttl_dns_cache=300,
            use_dns_cache=True,
            keepalive_timeout=30,
            enable_cleanup_closed=True
        )
        
        # Create HTTP session with connection pooling
        timeout = aiohttp.ClientTimeout(
            total=self.read_timeout,
            connect=self.connection_timeout,
            sock_read=self.read_timeout
        )
        
        self.session = aiohttp.ClientSession(
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "HTTP-Referer": "https://ai-developer-assistant.local",
                "X-Title": "AI Developer Assistant"
            },
            connector=self.connector,
            timeout=timeout,
            trust_env=True
        )
        
        # Update connection pool statistics
        self.stats["connection_pool_size"] = self.max_connections
        
        # Fetch available models
        await self._fetch_available_models()
        
        self.logger.info("OpenRouter API integration initialized successfully")
    
    async def stop(self) -> None:
        """Stop the OpenRouter API integration"""
        self.logger.info("Stopping OpenRouter API integration...")
        
        # Close HTTP session
        if self.session:
            await self.session.close()
        
        # Close connection pool
        if self.connector:
            await self.connector.close()
        
        self.logger.info("OpenRouter API integration stopped")
    
    async def chat_completion(self, request: ChatCompletionRequest) -> ChatCompletionResponse:
        """Create a chat completion"""
        if not self.session:
            raise RuntimeError("OpenRouter API not initialized or no API key available")
        
        # Apply rate limiting
        await self._apply_rate_limit()
        
        # Prepare request data
        request_data = {
            "model": request.model,
            "messages": [
                {
                    "role": msg.role,
                    "content": msg.content,
                    "name": msg.name
                }
                for msg in request.messages
            ],
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "top_p": request.top_p,
            "frequency_penalty": request.frequency_penalty,
            "presence_penalty": request.presence_penalty,
            "stream": request.stream
        }
        
        if request.stop:
            request_data["stop"] = request.stop
        
        if request.functions:
            request_data["functions"] = request.functions
        
        if request.function_call:
            request_data["function_call"] = request.function_call
        
        # Make API request
        start_time = time.time()
        
        try:
            async with async_timeout.timeout(60):  # 60 second timeout
                async with self.session.post(
                    f"{self.base_url}/chat/completions",
                    json=request_data
                ) as response:
                    
                    # Update statistics
                    self.stats["total_requests"] += 1
                    
                    if response.status == 200:
                        self.stats["successful_requests"] += 1
                        
                        # Parse response
                        response_data = await response.json()
                        
                        # Update token usage
                        if "usage" in response_data:
                            usage = response_data["usage"]
                            self.stats["total_tokens_used"] += usage.get("total_tokens", 0)
                        
                        # Calculate response time
                        response_time = time.time() - start_time
                        self._update_average_response_time(response_time)
                        
                        # Create response object
                        completion_response = ChatCompletionResponse(
                            id=response_data["id"],
                            object=response_data["object"],
                            created=response_data["created"],
                            model=response_data["model"],
                            choices=response_data["choices"],
                            usage=response_data.get("usage"),
                            system_fingerprint=response_data.get("system_fingerprint")
                        )
                        
                        self.logger.info(f"Chat completion successful: {completion_response.id}")
                        return completion_response
                    
                    else:
                        self.stats["failed_requests"] += 1
                        error_text = await response.text()
                        self.logger.error(f"OpenRouter API error: {response.status} - {error_text}")
                        raise Exception(f"API request failed: {response.status} - {error_text}")
                        
        except asyncio.TimeoutError:
            self.stats["failed_requests"] += 1
            self.logger.error("OpenRouter API request timeout")
            raise Exception("Request timeout")
        except Exception as e:
            self.stats["failed_requests"] += 1
            self.logger.error(f"OpenRouter API request failed: {e}")
            raise
    
    async def create_chat_completion(self, messages: List[Dict[str, str]], 
                                   model: Optional[str] = None,
                                   **kwargs) -> Dict[str, Any]:
        """Create a chat completion with simplified interface"""
        if not model:
            model = self.default_model
        
        # Convert messages to ChatMessage objects
        chat_messages = []
        for msg in messages:
            chat_messages.append(ChatMessage(
                role=msg["role"],
                content=msg["content"],
                name=msg.get("name")
            ))
        
        # Create request
        request = ChatCompletionRequest(
            model=model,
            messages=chat_messages,
            **kwargs
        )
        
        # Make request
        response = await self.chat_completion(request)
        
        # Convert to dictionary
        return {
            "id": response.id,
            "object": response.object,
            "created": response.created,
            "model": response.model,
            "choices": response.choices,
            "usage": response.usage,
            "system_fingerprint": response.system_fingerprint
        }
    
    async def get_available_models(self) -> List[Dict[str, Any]]:
        """Get list of available models"""
        if not self.available_models:
            await self._fetch_available_models()
        
        return self.available_models.copy()
    
    async def _fetch_available_models(self) -> None:
        """Fetch available models from OpenRouter"""
        if not self.session:
            return
        
        try:
            async with self.session.get(f"{self.base_url}/models") as response:
                if response.status == 200:
                    data = await response.json()
                    self.available_models = data.get("data", [])
                    self.logger.info(f"Fetched {len(self.available_models)} available models")
                else:
                    self.logger.error(f"Failed to fetch models: {response.status}")
                    
        except Exception as e:
            self.logger.error(f"Error fetching models: {e}")
    
    async def _apply_rate_limit(self) -> None:
        """Apply rate limiting to API requests"""
        current_time = time.time()
        
        # Remove old timestamps (older than 1 minute)
        self.request_timestamps = [
            ts for ts in self.request_timestamps 
            if current_time - ts < 60
        ]
        
        # Check if we need to wait
        if len(self.request_timestamps) >= self.max_requests_per_minute:
            # Wait until the oldest request is more than 1 minute old
            wait_time = 60 - (current_time - self.request_timestamps[0])
            if wait_time > 0:
                self.logger.info(f"Rate limiting: waiting {wait_time:.2f} seconds")
                await asyncio.sleep(wait_time)
        
        # Add current timestamp
        self.request_timestamps.append(current_time)
    
    def _update_average_response_time(self, response_time: float) -> None:
        """Update average response time"""
        if self.stats["successful_requests"] == 1:
            self.stats["average_response_time"] = response_time
        else:
            # Calculate weighted average
            alpha = 0.1  # Smoothing factor
            self.stats["average_response_time"] = (
                (1 - alpha) * self.stats["average_response_time"] + 
                alpha * response_time
            )
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get API usage statistics"""
        # Update connection pool statistics
        if self.connector:
            self.stats["active_connections"] = len(self.connector._conns)
        
        return {
            "success": True,
            "statistics": self.stats.copy(),
            "rate_limit_info": {
                "requests_in_last_minute": len(self.request_timestamps),
                "max_requests_per_minute": self.max_requests_per_minute
            },
            "connection_pool_info": {
                "max_connections": self.max_connections,
                "max_per_host": self.max_per_host,
                "active_connections": self.stats["active_connections"],
                "connection_timeout": self.connection_timeout,
                "read_timeout": self.read_timeout
            },
            "available_models_count": len(self.available_models)
        }
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test API connection"""
        try:
            # Simple test request
            test_messages = [
                {"role": "user", "content": "Hello, this is a test message."}
            ]
            
            response = await self.create_chat_completion(
                messages=test_messages,
                max_tokens=10
            )
            
            return {
                "success": True,
                "message": "API connection successful",
                "response_id": response["id"],
                "model_used": response["model"]
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"API connection failed: {str(e)}"
            }
    
    async def stream_chat_completion(self, messages: List[Dict[str, str]], 
                                   model: Optional[str] = None,
                                   **kwargs) -> Any:
        """Stream chat completion responses"""
        if not model:
            model = self.default_model
        
        # Convert messages to ChatMessage objects
        chat_messages = []
        for msg in messages:
            chat_messages.append(ChatMessage(
                role=msg["role"],
                content=msg["content"],
                name=msg.get("name")
            ))
        
        # Create request with streaming enabled
        request = ChatCompletionRequest(
            model=model,
            messages=chat_messages,
            stream=True,
            **kwargs
        )
        
        # Prepare request data
        request_data = {
            "model": request.model,
            "messages": [
                {
                    "role": msg.role,
                    "content": msg.content,
                    "name": msg.name
                }
                for msg in request.messages
            ],
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "top_p": request.top_p,
            "frequency_penalty": request.frequency_penalty,
            "presence_penalty": request.presence_penalty,
            "stream": True
        }
        
        if request.stop:
            request_data["stop"] = request.stop
        
        # Make streaming request
        try:
            async with self.session.post(
                f"{self.base_url}/chat/completions",
                json=request_data
            ) as response:
                
                if response.status == 200:
                    async for line in response.content:
                        line = line.decode('utf-8').strip()
                        if line.startswith("data: "):
                            data = line[6:]  # Remove "data: " prefix
                            if data == "[DONE]":
                                break
                            try:
                                chunk = json.loads(data)
                                yield chunk
                            except json.JSONDecodeError:
                                continue
                else:
                    error_text = await response.text()
                    raise Exception(f"Streaming request failed: {response.status} - {error_text}")
                    
        except Exception as e:
            self.logger.error(f"Streaming request failed: {e}")
            raise


class OpenRouterAgent:
    """Agent that uses OpenRouter API for AI-powered tasks"""
    
    def __init__(self, openrouter_api: OpenRouterAPI):
        self.api = openrouter_api
        self.logger = logging.getLogger(__name__)
        
        # Agent configuration
        self.system_prompt = """You are an AI Developer Assistant. You help with software development tasks including:
- Code generation and analysis
- Debugging and troubleshooting
- File operations and management
- Terminal command execution
- Web automation and testing
- Project management and organization

Be helpful, concise, and provide practical solutions. Always consider security best practices."""
    
    async def handle_message(self, message) -> None:
        """Handle incoming messages"""
        # This would be implemented based on the message structure
        pass
    
    async def generate_code(self, prompt: str, language: str = "python") -> str:
        """Generate code based on a prompt"""
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": f"Generate {language} code for: {prompt}"}
        ]
        
        response = await self.api.create_chat_completion(
            messages=messages,
            max_tokens=1000,
            temperature=0.3
        )
        
        if response["choices"]:
            return response["choices"][0]["message"]["content"]
        else:
            raise Exception("No response generated")
    
    async def analyze_code(self, code: str, language: str = "python") -> Dict[str, Any]:
        """Analyze code and provide insights"""
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": f"Analyze this {language} code and provide insights:\n\n{code}"}
        ]
        
        response = await self.api.create_chat_completion(
            messages=messages,
            max_tokens=1500,
            temperature=0.5
        )
        
        if response["choices"]:
            analysis = response["choices"][0]["message"]["content"]
            return {
                "success": True,
                "analysis": analysis,
                "language": language,
                "code_length": len(code)
            }
        else:
            return {"error": "No analysis generated"}
    
    async def debug_code(self, code: str, error_message: str, language: str = "python") -> str:
        """Help debug code with error information"""
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": f"Debug this {language} code. Error: {error_message}\n\nCode:\n{code}"}
        ]
        
        response = await self.api.create_chat_completion(
            messages=messages,
            max_tokens=1000,
            temperature=0.3
        )
        
        if response["choices"]:
            return response["choices"][0]["message"]["content"]
        else:
            raise Exception("No debugging suggestions generated")
    
    async def explain_concept(self, concept: str, context: Optional[str] = None) -> str:
        """Explain programming concepts"""
        prompt = f"Explain the programming concept: {concept}"
        if context:
            prompt += f"\n\nContext: {context}"
        
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": prompt}
        ]
        
        response = await self.api.create_chat_completion(
            messages=messages,
            max_tokens=800,
            temperature=0.5
        )
        
        if response["choices"]:
            return response["choices"][0]["message"]["content"]
        else:
            raise Exception("No explanation generated")
    
    async def suggest_improvements(self, code: str, language: str = "python") -> str:
        """Suggest code improvements"""
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": f"Suggest improvements for this {language} code:\n\n{code}"}
        ]
        
        response = await self.api.create_chat_completion(
            messages=messages,
            max_tokens=1000,
            temperature=0.4
        )
        
        if response["choices"]:
            return response["choices"][0]["message"]["content"]
        else:
            raise Exception("No improvement suggestions generated")