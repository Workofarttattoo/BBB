#!/usr/bin/env python3
"""
BBB Semantic Framework
Adopts the $.Subject.predicate.Object pattern from the .do platform.
"""

import threading
import queue
import time
import json
import os
from typing import Any, Callable, Dict, List, Optional, Union

class SemanticProxy:
    """Implements the $.Subject.predicate.Object pattern."""
    def __init__(self, path: List[str] = []):
        self._path = path

    def __getattr__(self, name: str) -> 'SemanticProxy':
        return SemanticProxy(self._path + [name])

    def __getitem__(self, key: str) -> 'SemanticProxy':
        return SemanticProxy(self._path + [key])

    def __str__(self) -> str:
        return "$." + ".".join(self._path)

    def __repr__(self) -> str:
        return f"SemanticProxy({self._path})"

    @property
    def path(self) -> List[str]:
        return self._path

# Root proxy
semantic = SemanticProxy()

class SemanticBus:
    """Semantic event bus for on/send patterns."""
    def __init__(self):
        self._listeners: Dict[str, List[Callable]] = {}
        self._lock = threading.Lock()

    def on(self, pattern: Union[SemanticProxy, str], handler: Callable):
        pattern_str = str(pattern)
        with self._lock:
            if pattern_str not in self._listeners:
                self._listeners[pattern_str] = []
            self._listeners[pattern_str].append(handler)
            print(f"[SemanticBus] Registered listener for: {pattern_str}")

    def send(self, pattern: Union[SemanticProxy, str], data: Any):
        pattern_str = str(pattern)
        print(f"[SemanticBus] Sending event: {pattern_str}")
        with self._lock:
            handlers = self._listeners.get(pattern_str, [])
            # Also support wildcard matching (simple implementation)
            if "$." in pattern_str:
                parts = pattern_str.split(".")
                for i in range(1, len(parts)):
                    wildcard = ".".join(parts[:i]) + ".*"
                    handlers.extend(self._listeners.get(wildcard, []))

        for handler in handlers:
            try:
                # Run in thread to avoid blocking
                threading.Thread(target=handler, args=(data,), daemon=True).start()
            except Exception as e:
                print(f"[ERROR] SemanticBus handler failed: {e}")

bus = SemanticBus()
on = bus.on
send = bus.send

class SemanticScheduler:
    """Semantic scheduler for 'every' patterns."""
    def __init__(self):
        self._tasks = []
        self._running = False
        self._thread = None

    def every(self, interval: Union[SemanticProxy, str, int], handler: Callable):
        # Default intervals if using $.Daily etc
        interval_seconds = 3600 # Default
        pattern = str(interval)
        if pattern == "$.Daily":
            interval_seconds = 86400
        elif pattern == "$.Hourly":
            interval_seconds = 3600
        elif isinstance(interval, int):
            interval_seconds = interval
            
        def wrapper():
            while self._running:
                try:
                    handler()
                except Exception as e:
                    print(f"[ERROR] Scheduled task failed: {e}")
                time.sleep(interval_seconds)

        self._tasks.append(wrapper)
        if not self._running:
            self.start()

    def start(self):
        self._running = True
        for task in self._tasks:
            t = threading.Thread(target=task, daemon=True)
            t.start()
        print("[SemanticScheduler] Started")

scheduler = SemanticScheduler()
every = scheduler.every

# AI and DB wrappers will be integrated with existing BBB modules
class SemanticAI:
    def __init__(self):
        from .ech0_service import ECH0Service
        self.engine = ECH0Service()

    async def generate(self, prompt: str, schema: Optional[SemanticProxy] = None):
        print(f"[AI] Generating with prompt: {prompt}")
        return await self.engine.generate(prompt, schema=schema)

ai = SemanticAI()

class SemanticDB:
    def list(self, type_proxy: SemanticProxy):
        print(f"[DB] Listing all: {type_proxy}")
        return []

    def get(self, type_proxy: SemanticProxy, id: str):
        print(f"[DB] Getting {type_proxy} with ID: {id}")
        return None

db = SemanticDB()

if __name__ == "__main__":
    # Test patterns
    print(f"Pattern test: {semantic.Order.created}")
    
    on(semantic.Order.created, lambda data: print(f"Handler received: {data}"))
    send(semantic.Order.created, {"id": "123", "total": 100})
    
    every(2, lambda: print("Heartbeat..."))
    
    time.sleep(5)
