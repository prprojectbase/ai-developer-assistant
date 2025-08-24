#!/usr/bin/env python3
"""
Example: OpenRouter API Integration

This script demonstrates how to use the OpenRouter API Integration module
to interact with AI models for various development tasks.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from modules.openrouter_integration import OpenRouterAPI, OpenRouterAgent


async def main():
    """Demonstrate OpenRouter API integration"""
    print("🧠 OpenRouter API Integration Example")
    print("=" * 40)
    
    # Initialize OpenRouter API
    api = OpenRouterAPI()
    try:
        await api.initialize()
    except Exception as e:
        print(f"❌ Error initializing OpenRouter API: {e}")
        print("   Make sure you have set OPENROUTER_API_KEY in your .env file")
        return
    
    # Create OpenRouter agent
    agent = OpenRouterAgent(api)
    
    try:
        # Example 1: Test connection
        print("\n1. Testing API connection...")
        result = await api.test_connection()
        if result["success"]:
            print(f"✅ Connection successful")
            print(f"   Response ID: {result['response_id']}")
            print(f"   Model used: {result['model_used']}")
        else:
            print(f"❌ Connection failed: {result['message']}")
            return
        
        # Example 2: Generate code
        print("\n2. Generating Python code...")
        try:
            code = await agent.generate_code(
                "Create a function that calculates the factorial of a number",
                "python"
            )
            print("✅ Code generated:")
            print("```python")
            print(code)
            print("```")
        except Exception as e:
            print(f"❌ Error generating code: {e}")
        
        # Example 3: Analyze code
        print("\n3. Analyzing code...")
        sample_code = """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

# Calculate first 10 Fibonacci numbers
for i in range(10):
    print(fibonacci(i))
        """
        
        try:
            analysis = await agent.analyze_code(sample_code, "python")
            if analysis["success"]:
                print("✅ Code analysis:")
                print(analysis["analysis"])
            else:
                print(f"❌ Error analyzing code: {analysis['error']}")
        except Exception as e:
            print(f"❌ Error analyzing code: {e}")
        
        # Example 4: Debug code
        print("\n4. Debugging code...")
        buggy_code = """
def calculate_average(numbers):
    total = 0
    for num in numbers:
        total += num
    return total / len(numbers)

# This will cause an error
result = calculate_average([])
print(result)
        """
        
        try:
            debug_result = await agent.debug_code(
                buggy_code,
                "ZeroDivisionError: division by zero",
                "python"
            )
            print("✅ Debugging suggestions:")
            print(debug_result)
        except Exception as e:
            print(f"❌ Error debugging code: {e}")
        
        # Example 5: Explain concept
        print("\n5. Explaining programming concept...")
        try:
            explanation = await agent.explain_concept(
                "recursion",
                "in the context of computer science and algorithms"
            )
            print("✅ Concept explanation:")
            print(explanation)
        except Exception as e:
            print(f"❌ Error explaining concept: {e}")
        
        # Example 6: Suggest improvements
        print("\n6. Suggesting code improvements...")
        improvable_code = """
def is_prime(n):
    if n < 2:
        return False
    for i in range(2, n):
        if n % i == 0:
            return False
    return True
        """
        
        try:
            improvements = await agent.suggest_improvements(improvable_code, "python")
            print("✅ Improvement suggestions:")
            print(improvements)
        except Exception as e:
            print(f"❌ Error suggesting improvements: {e}")
        
        # Example 7: Direct API usage
        print("\n7. Using API directly for chat completion...")
        messages = [
            {"role": "system", "content": "You are a helpful programming assistant."},
            {"role": "user", "content": "What are the main principles of Object-Oriented Programming?"}
        ]
        
        try:
            response = await api.create_chat_completion(
                messages=messages,
                max_tokens=500,
                temperature=0.7
            )
            
            if response["choices"]:
                answer = response["choices"][0]["message"]["content"]
                print("✅ Chat completion response:")
                print(answer)
                
                # Show usage statistics
                if response.get("usage"):
                    usage = response["usage"]
                    print(f"\n   Usage: {usage['total_tokens']} tokens "
                          f"({usage['prompt_tokens']} prompt, {usage['completion_tokens']} completion)")
            else:
                print("❌ No response received")
        except Exception as e:
            print(f"❌ Error with chat completion: {e}")
        
        # Example 8: Get available models
        print("\n8. Getting available models...")
        try:
            models = await api.get_available_models()
            print(f"✅ Available models: {len(models)}")
            
            # Show first 5 models
            for i, model in enumerate(models[:5]):
                print(f"   {i+1}. {model.get('id', 'Unknown')}")
                if model.get('description'):
                    print(f"      {model['description'][:80]}...")
            
            if len(models) > 5:
                print(f"   ... and {len(models) - 5} more models")
        except Exception as e:
            print(f"❌ Error getting models: {e}")
        
        # Example 9: Streaming chat completion
        print("\n9. Testing streaming chat completion...")
        try:
            messages = [
                {"role": "user", "content": "List 3 benefits of using Python for web development"}
            ]
            
            print("✅ Streaming response:")
            async for chunk in api.stream_chat_completion(messages, max_tokens=200):
                if chunk.get("choices"):
                    delta = chunk["choices"][0].get("delta", {})
                    if delta.get("content"):
                        print(delta["content"], end="", flush=True)
            print()  # New line after streaming
        except Exception as e:
            print(f"❌ Error with streaming: {e}")
        
        # Example 10: Get API statistics
        print("\n10. Getting API statistics...")
        try:
            stats = await api.get_statistics()
            if stats["success"]:
                print("✅ API Statistics:")
                stat_data = stats["statistics"]
                print(f"   Total requests: {stat_data['total_requests']}")
                print(f"   Successful requests: {stat_data['successful_requests']}")
                print(f"   Failed requests: {stat_data['failed_requests']}")
                print(f"   Total tokens used: {stat_data['total_tokens_used']}")
                print(f"   Average response time: {stat_data['average_response_time']:.2f}s")
                
                rate_limit = stats["rate_limit_info"]
                print(f"   Requests in last minute: {rate_limit['requests_in_last_minute']}")
                print(f"   Max requests per minute: {rate_limit['max_requests_per_minute']}")
                print(f"   Available models: {stats['available_models_count']}")
            else:
                print(f"❌ Error getting statistics: {stats.get('error', 'Unknown error')}")
        except Exception as e:
            print(f"❌ Error getting statistics: {e}")
        
    finally:
        # Clean up
        await api.stop()
    
    print("\n✅ OpenRouter API integration example completed!")


if __name__ == "__main__":
    asyncio.run(main())