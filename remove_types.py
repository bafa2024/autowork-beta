import re
import os

def remove_type_hints(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Remove type hints
    content = re.sub(r' -> List\[.*?\]:', ':', content)
    content = re.sub(r' -> Dict\[.*?\]:', ':', content)
    content = re.sub(r' -> List\[Dict\]:', ':', content)
    content = re.sub(r': List\[.*?\]', '', content)
    content = re.sub(r': Dict\[.*?\]', '', content)
    content = re.sub(r': Set\[.*?\]', '', content)
    
    with open(filename + '.bak', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Created {filename}.bak without type hints")

# Remove types from problem files
for file in ['monitor.py', 'autowork.py', 'config.py']:
    if os.path.exists(file):
        remove_type_hints(file)