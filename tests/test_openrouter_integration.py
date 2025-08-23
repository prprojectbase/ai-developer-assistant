"""
Unit tests for OpenRouter Integration module
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.modules.openrouter_integration import (
    OpenRouterAPI, OpenRouterAgent, 
    ChatMessage, ChatCompletionRequest, ChatCompletionResponse
)
from src.config.settings import get_settings


class TestOpenRouterAPI:
    """Test cases for OpenRouterAPI class"""
    
    @pytest.fixture
    def api(self):
        """Create an OpenRouterAPI instance for testing"""
        settings = get_settings()
        settings.openrouter_api_key = "test_api_key"
        settings.openrouter_base_url = "https://api.openrouter.ai/api/v1"
        settings.openrouter_model = "test_model"
        
        return OpenRouterAPI()
    
    @pytest.fixture
    def sample_messages(self):
        """Sample chat messages for testing"""
        return [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello, how are you?"}
        ]
    
    @pytest.fixture
    def mock_response_data(self):
        """Mock API response data"""
        return {
            "id": "chatcmpl-123",
            "object": "chat.completion",
            "created": 1234567890,
            "model": "test_model",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "I'm doing well, thank you for asking!"
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": 20,
                "completion_tokens": 10,
                "total_tokens": 30
            },
            "system_fingerprint": "fp_123"
        }
    
    @pytest.mark.asyncio
    async def test_initialize(self, api):
        """Test OpenRouterAPI initialization"""
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session
            
            with patch('src.modules.openrouter_integration.logging.getLogger') as mock_logger:
                mock_logger.return_value = Mock()
                
                await api.initialize()
                
                assert api.session is not None
                mock_session_class.assert_called_once()
                
                # Check headers
                call_kwargs = mock_session_class.call_args[1]
                headers = call_kwargs['headers']
                assert headers['Authorization'] == 'Bearer test_api_key'
                assert headers['HTTP-Referer'] == 'https://ai-developer-assistant.local'
                assert headers['X-Title'] == 'AI Developer Assistant'
                
                mock_logger.return_value.info.assert_called()
    
    @pytest.mark.asyncio
    async def test_stop(self, api):
        """Test OpenRouterAPI stop"""
        # Initialize first
        with patch('aiohttp.ClientSession'):
            await api.initialize()
        
        # Mock session close
        api.session = Mock()
        api.session.close = AsyncMock()
        
        with patch('src.modules.openrouter_integration.logging.getLogger') as mock_logger:
            mock_logger.return_value = Mock()
            
            await api.stop()
            
            api.session.close.assert_called_once()
            mock_logger.return_value.info.assert_called()
    
    @pytest.mark.asyncio
    async def test_chat_completion_success(self, api, sample_messages, mock_response_data):
        """Test successful chat completion"""
        # Initialize API
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session
            await api.initialize()
        
        # Mock successful response
        mock_response = Mock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=mock_response_data)
        
        mock_session.post.return_value.__aenter__.return_value = mock_response
        
        # Create request
        request = ChatCompletionRequest(
            model="test_model",
            messages=[ChatMessage(**msg) for msg in sample_messages]
        )
        
        # Make request
        response = await api.chat_completion(request)
        
        assert response.id == "chatcmpl-123"
        assert response.object == "chat.completion"
        assert response.model == "test_model"
        assert len(response.choices) == 1
        assert response.choices[0]["message"]["content"] == "I'm doing well, thank you for asking!"
        assert response.usage["total_tokens"] == 30
        
        # Check statistics
        assert api.stats["total_requests"] == 1
        assert api.stats["successful_requests"] == 1
        assert api.stats["failed_requests"] == 0
        assert api.stats["total_tokens_used"] == 30
    
    @pytest.mark.asyncio
    async def test_chat_completion_api_error(self, api, sample_messages):
        """Test chat completion with API error"""
        # Initialize API
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session
            await api.initialize()
        
        # Mock error response
        mock_response = Mock()
        mock_response.status = 400
        mock_response.text = AsyncMock(return_value="Bad Request")
        
        mock_session.post.return_value.__aenter__.return_value = mock_response
        
        # Create request
        request = ChatCompletionRequest(
            model="test_model",
            messages=[ChatMessage(**msg) for msg in sample_messages]
        )
        
        # Make request (should raise exception)
        with pytest.raises(Exception, match="API request failed: 400"):
            await api.chat_completion(request)
        
        # Check statistics
        assert api.stats["total_requests"] == 1
        assert api.stats["successful_requests"] == 0
        assert api.stats["failed_requests"] == 1
    
    @pytest.mark.asyncio
    async def test_chat_completion_timeout(self, api, sample_messages):
        """Test chat completion timeout"""
        # Initialize API
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session
            await api.initialize()
        
        # Mock timeout
        mock_session.post.return_value.__aenter__.side_effect = asyncio.TimeoutError()
        
        # Create request
        request = ChatCompletionRequest(
            model="test_model",
            messages=[ChatMessage(**msg) for msg in sample_messages]
        )
        
        # Make request (should raise exception)
        with pytest.raises(Exception, match="Request timeout"):
            await api.chat_completion(request)
        
        # Check statistics
        assert api.stats["total_requests"] == 1
        assert api.stats["successful_requests"] == 0
        assert api.stats["failed_requests"] == 1
    
    @pytest.mark.asyncio
    async def test_create_chat_completion(self, api, sample_messages, mock_response_data):
        """Test simplified chat completion interface"""
        # Initialize API
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session
            await api.initialize()
        
        # Mock successful response
        mock_response = Mock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=mock_response_data)
        
        mock_session.post.return_value.__aenter__.return_value = mock_response
        
        # Make request
        response = await api.create_chat_completion(sample_messages)
        
        assert response["id"] == "chatcmpl-123"
        assert response["model"] == "test_model"
        assert response["choices"][0]["message"]["content"] == "I'm doing well, thank you for asking!"
    
    @pytest.mark.asyncio
    async def test_get_available_models(self, api):
        """Test getting available models"""
        # Initialize API
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session
            await api.initialize()
        
        # Mock models response
        models_data = {
            "data": [
                {"id": "model1", "name": "Test Model 1"},
                {"id": "model2", "name": "Test Model 2"}
            ]
        }
        
        mock_response = Mock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=models_data)
        
        mock_session.get.return_value.__aenter__.return_value = mock_response
        
        # Get models
        models = await api.get_available_models()
        
        assert len(models) == 2
        assert models[0]["id"] == "model1"
        assert models[1]["id"] == "model2"
        
        # Check that models are cached
        assert len(api.available_models) == 2
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self, api, sample_messages, mock_response_data):
        """Test rate limiting functionality"""
        # Initialize API
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session
            await api.initialize()
        
        # Mock successful response
        mock_response = Mock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=mock_response_data)
        
        mock_session.post.return_value.__aenter__.return_value = mock_response
        
        # Set up rate limiting (max 2 requests per minute)
        api.max_requests_per_minute = 2
        
        # Make 3 requests quickly
        request = ChatCompletionRequest(
            model="test_model",
            messages=[ChatMessage(**msg) for msg in sample_messages]
        )
        
        # First two requests should succeed
        await api.chat_completion(request)
        await api.chat_completion(request)
        
        # Third request should trigger rate limiting
        with patch('asyncio.sleep') as mock_sleep:
            await api.chat_completion(request)
            mock_sleep.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_stream_chat_completion(self, api, sample_messages):
        """Test streaming chat completion"""
        # Initialize API
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session
            await api.initialize()
        
        # Mock streaming response
        mock_response = Mock()
        mock_response.status = 200
        
        # Create mock streaming content
        stream_chunks = [
            b'data: {"id": "chunk1", "choices": [{"delta": {"content": "Hello"}}]}\n\n',
            b'data: {"id": "chunk2", "choices": [{"delta": {"content": " world"}}]}\n\n',
            b'data: [DONE]\n\n'
        ]
        
        mock_response.content = AsyncMock()
        mock_response.content.__aiter__.return_value = stream_chunks
        
        mock_session.post.return_value.__aenter__.return_value = mock_response
        
        # Make streaming request
        chunks = []
        async for chunk in api.stream_chat_completion(sample_messages):
            chunks.append(chunk)
        
        assert len(chunks) == 2
        assert chunks[0]["choices"][0]["delta"]["content"] == "Hello"
        assert chunks[1]["choices"][0]["delta"]["content"] == " world"
    
    @pytest.mark.asyncio
    async def test_test_connection_success(self, api, mock_response_data):
        """Test successful connection test"""
        # Initialize API
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session
            await api.initialize()
        
        # Mock successful response
        mock_response = Mock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=mock_response_data)
        
        mock_session.post.return_value.__aenter__.return_value = mock_response
        
        # Test connection
        result = await api.test_connection()
        
        assert result["success"] is True
        assert result["message"] == "API connection successful"
        assert result["response_id"] == "chatcmpl-123"
        assert result["model_used"] == "test_model"
    
    @pytest.mark.asyncio
    async def test_test_connection_failure(self, api):
        """Test failed connection test"""
        # Initialize API
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session
            await api.initialize()
        
        # Mock error response
        mock_response = Mock()
        mock_response.status = 401
        mock_response.text = AsyncMock(return_value="Unauthorized")
        
        mock_session.post.return_value.__aenter__.return_value = mock_response
        
        # Test connection
        result = await api.test_connection()
        
        assert result["success"] is False
        assert "API connection failed" in result["message"]
        assert "401" in result["message"]
    
    @pytest.mark.asyncio
    async def test_get_statistics(self, api):
        """Test getting API statistics"""
        # Initialize API
        with patch('aiohttp.ClientSession'):
            await api.initialize()
        
        # Add some request timestamps
        import time
        current_time = time.time()
        api.request_timestamps = [current_time - 30, current_time - 10]  # 2 requests in last minute
        
        # Get statistics
        result = await api.get_statistics()
        
        assert result["success"] is True
        assert "statistics" in result
        assert "rate_limit_info" in result
        assert "available_models_count" in result
        
        stats = result["statistics"]
        assert stats["total_requests"] == 0
        assert stats["successful_requests"] == 0
        assert stats["failed_requests"] == 0
        
        rate_limit = result["rate_limit_info"]
        assert rate_limit["requests_in_last_minute"] == 2
        assert rate_limit["max_requests_per_minute"] == 60


class TestOpenRouterAgent:
    """Test cases for OpenRouterAgent class"""
    
    @pytest.fixture
    def agent(self):
        """Create an OpenRouterAgent instance for testing"""
        mock_api = Mock()
        return OpenRouterAgent(mock_api)
    
    @pytest.mark.asyncio
    async def test_generate_code(self, agent):
        """Test code generation"""
        # Mock API response
        mock_response = {
            "id": "test",
            "choices": [{"message": {"content": "def hello():\n    print('Hello, World!')"}}]
        }
        agent.api.create_chat_completion = AsyncMock(return_value=mock_response)
        
        # Generate code
        result = await agent.generate_code("Create a hello world function", "python")
        
        assert "def hello():" in result
        assert "print('Hello, World!')" in result
        
        # Check API call
        agent.api.create_chat_completion.assert_called_once()
        call_args = agent.api.create_chat_completion.call_args[0]
        messages = call_args[0]
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
        assert "python" in messages[1]["content"]
    
    @pytest.mark.asyncio
    async def test_analyze_code(self, agent):
        """Test code analysis"""
        # Mock API response
        mock_response = {
            "id": "test",
            "choices": [{"message": {"content": "The code is well-structured and follows best practices."}}]
        }
        agent.api.create_chat_completion = AsyncMock(return_value=mock_response)
        
        # Analyze code
        code = "def add(a, b):\n    return a + b"
        result = await agent.analyze_code(code, "python")
        
        assert "well-structured" in result
        
        # Check API call
        agent.api.create_chat_completion.assert_called_once()
        call_args = agent.api.create_chat_completion.call_args[0]
        messages = call_args[0]
        assert len(messages) == 2
        assert "python" in messages[1]["content"]
        assert code in messages[1]["content"]
    
    @pytest.mark.asyncio
    async def test_debug_code(self, agent):
        """Test code debugging"""
        # Mock API response
        mock_response = {
            "id": "test",
            "choices": [{"message": {"content": "The issue is missing parentheses in the print statement."}}]
        }
        agent.api.create_chat_completion = AsyncMock(return_value=mock_response)
        
        # Debug code
        code = "print 'Hello, World!'"
        result = await agent.debug_code(code, "python")
        
        assert "missing parentheses" in result
        
        # Check API call
        agent.api.create_chat_completion.assert_called_once()
        call_args = agent.api.create_chat_completion.call_args[0]
        messages = call_args[0]
        assert len(messages) == 2
        assert "python" in messages[1]["content"]
        assert code in messages[1]["content"]
    
    @pytest.mark.asyncio
    async def test_explain_concept(self, agent):
        """Test concept explanation"""
        # Mock API response
        mock_response = {
            "id": "test",
            "choices": [{"message": {"content": "A list comprehension is a concise way to create lists in Python."}}]
        }
        agent.api.create_chat_completion = AsyncMock(return_value=mock_response)
        
        # Explain concept
        result = await agent.explain_concept("list comprehension", "python")
        
        assert "concise way" in result
        
        # Check API call
        agent.api.create_chat_completion.assert_called_once()
        call_args = agent.api.create_chat_completion.call_args[0]
        messages = call_args[0]
        assert len(messages) == 2
        assert "python" in messages[1]["content"]
        assert "list comprehension" in messages[1]["content"]
    
    @pytest.mark.asyncio
    async def test_handle_message(self, agent):
        """Test message handling"""
        # This is a placeholder implementation
        mock_message = Mock()
        
        # Should not raise an exception
        await agent.handle_message(mock_message)