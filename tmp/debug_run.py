import sys, os
sys.path.insert(0, os.path.abspath('.'))
os.chdir(r'F:\My Programs\Synapse VS')

# Redirect output to a file
log_file = open(r'F:\My Programs\Synapse VS\tmp\debug_output.txt', 'w')

from synapse.core.core import SynapseCore
core = SynapseCore(headless=True)
try:
    node_map, was_modified, data = core.load("sub_graphs/Bot/enviroment_watch.syp", delay=0.0)
    core.run()
except KeyboardInterrupt:
    pass
except Exception as e:
    log_file.write(f"ERROR: {e}\n")
finally:
    log_file.close()
