import os
path = r"f:\My Programs\AxonPulse VS\axonpulse\gui\project_panel.py"
if os.path.exists(path):
    os.remove(path)
    print(f"Deleted {path}")
else:
    print(f"File {path} not found")
