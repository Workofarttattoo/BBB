import sys
import os

def check_for_bolt():
    for root, _, files in os.walk('src'):
        for file in files:
            if file.endswith('.py'):
                path = os.path.join(root, file)
                with open(path, 'r') as f:
                    content = f.read()
                    if 'Bolt Optimization' in content:
                        print(f"===========================================================")
                        print(f"Found bolt optimization in {path}")
                        lines = content.split('\n')
                        for i, line in enumerate(lines):
                            if 'Bolt Optimization' in line:
                                print('\n'.join(lines[i-2:i+5]))

check_for_bolt()
