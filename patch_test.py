with open("tests/test_expert_system_optimized.py", "r") as f:
    content = f.read()

content = content.replace("self.assertEqual(self.system.vector_store.search.call_count, 2)", "self.assertEqual(self.system.vector_store.search.call_count, 1)")
content = content.replace("We expect 2 calls: 1 global search + 1 expert search", "We expect 1 call: 1 global search, and the result is passed to the expert")

with open("tests/test_expert_system_optimized.py", "w") as f:
    f.write(content)
