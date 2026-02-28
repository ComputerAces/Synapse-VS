import re

path = r'f:\My Programs\Synapse VS\synapse\nodes\browser\actions.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Pattern to find the class __init__ body
# We want to replace any sequence of self.is_browser_node = True (one or more)
# and ensure it's there exactly once after self.is_native = True

# First, remove all existing is_browser_node assignments to start fresh
content = re.sub(r'\s+self\.is_browser_node = True', '', content)

# Now, add it exactly once after self.is_native = True
content = content.replace('self.is_native = True', 'self.is_native = True\n        self.is_browser_node = True')

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Standardized is_browser_node flags in actions.py")
