import os
import re

for root, _, files in os.walk('src'):
    for file in files:
        if file.endswith('.py'):
            with open(os.path.join(root, file), 'r') as f:
                lines = f.readlines()
                in_loop = False
                loop_indent = 0
                for i, line in enumerate(lines):
                    stripped = line.strip()
                    if stripped.startswith('for ') and line.endswith(':\n'):
                        in_loop = True
                        loop_indent = len(line) - len(stripped)
                    elif in_loop:
                        curr_indent = len(line) - len(line.lstrip())
                        if curr_indent <= loop_indent and stripped:
                            in_loop = False
                        elif 'db.query(' in stripped or 'await db.' in stripped:
                            print(f"{os.path.join(root, file)}:{i+1} {stripped}")
