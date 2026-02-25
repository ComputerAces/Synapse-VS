import os
import importlib.util
from synapse.utils.logger import main_logger as logger

def run_migrations(data):
    """
    Scans the migrations directory and executes all valid migration scripts sequentially.
    Returns: (modified_data, was_modified)
    """
    was_modified = False
    migrations_dir = os.path.dirname(__file__)
    
    # Discovery: find files matching 'v*_*.py'
    migration_files = []
    for f in os.listdir(migrations_dir):
        if f.startswith("v") and f.endswith(".py") and "_" in f:
            migration_files.append(f)
            
    # Sort by version number (assuming format vX_Y_Z_description.py)
    # We'll just do simple alphabetical for now which works for v2_1_0 etc.
    migration_files.sort()
    
    current_version = data.get("version", "2.0.0")
    
    for f in migration_files:
        module_name = f[:-3]
        # Check if we should run this based on version (optional logic)
        
        try:
            full_path = os.path.join(migrations_dir, f)
            spec = importlib.util.spec_from_file_location(module_name, full_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            if hasattr(module, "migrate"):
                data, modified = module.migrate(data)
                if modified:
                    was_modified = True
                    logger.info(f"Migration {module_name} applied.")
        except Exception as e:
            logger.error(f"Failed to run migration {module_name}: {e}")
            
    return data, was_modified
