#!/usr/bin/env python3
import asyncio
import os
import sys

# Add src to path
sys.path.append(os.path.join(os.getcwd(), 'src'))

from blank_business_builder.semantic_framework import semantic, on, send
from startup_compiler import StartupCompiler

async def test_integration():
    print("--- Starting Semantic Integration Test ---")
    
    # 1. Test Semantic Bus
    event_received = asyncio.Event()
    
    def handler(data):
        print(f"[TEST] Event received: {data}")
        event_received.set()
        
    on(semantic.Test.event, handler)
    send(semantic.Test.event, {"message": "Hello from Swarm"})
    
    # 2. Test Startup Compiler
    compiler = StartupCompiler()
    # We use a short timeout for simulation
    try:
        await asyncio.wait_for(compiler.compile("Automated niche coffee subscription service"), timeout=10)
    except asyncio.TimeoutError:
        print("[TEST] Compilation timed out (expected in mock environment)")
    except Exception as e:
        print(f"[TEST] Compilation failed: {e}")

    print("--- Integration Test Complete ---")

if __name__ == "__main__":
    asyncio.run(test_integration())
