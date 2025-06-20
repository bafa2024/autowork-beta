import os
import re

def fix_type_hints(filename):
    """Fix type hints for Python 3.9+"""
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace typing imports
    content = re.sub(r'from typing import .*List.*', 
                     'from typing import Optional, Dict, Set, List', content)
    
    # For Python 3.9+, you can also use:
    # content = content.replace('List[', 'list[')
    # content = content.replace('Dict[', 'dict[')
    # content = content.replace('Set[', 'set[')
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Fixed {filename}")

# Fix all Python files
for file in ['monitor.py', 'autowork.py', 'config.py', 'database.py']:
    if os.path.exists(file):
        fix_type_hints(file)