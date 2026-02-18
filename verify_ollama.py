import asyncio
import os
import sys

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.getcwd(), 'src')))

from blank_business_builder.integrations import IntegrationFactory
from blank_business_builder.ech0_service import ECH0Service
from blank_business_builder.config import settings

async def test_ollama_reasoning():
    print(f"Testing reasoning via Ollama (Model: {settings.OLLAMA_MODEL}, Provider: {settings.LLM_PROVIDER})")
    
    # Test 1: Direct ECH0Service
    echo = ECH0Service()
    print("\n1. Testing ECH0Service.generate...")
    try:
        response = await echo.generate("Why should all agents use local reasoning?")
        print(f"Response: {response[:100]}...")
    except Exception as e:
        print(f"Error: {e}")

    # Test 2: IntegrationFactory
    print("\n2. Testing IntegrationFactory.get_openai_service...")
    try:
        openai_proxy = IntegrationFactory.get_openai_service()
        print(f"Service Type: {type(openai_proxy).__name__}")
        if hasattr(openai_proxy, 'generate'):
            response = await openai_proxy.generate("Tell me a business joke.")
            print(f"Response: {response[:100]}...")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_ollama_reasoning())
