import os
import json
from axonpulse.utils.logger import setup_logger

logger = setup_logger("SHMTracker")

class SHMTracker:
    """
    Registry for active Shared Memory blocks to prevent OS-level leaks on Windows.
    Stores metadata in 'axonpulse_shm.registry'.
    """
    REGISTRY_FILE = "axonpulse_shm.registry"

    @classmethod
    def _read_registry(cls):
        if not os.path.exists(cls.REGISTRY_FILE):
            return set()
        try:
            with open(cls.REGISTRY_FILE, "r") as f:
                data = json.load(f)
                return set(data) if isinstance(data, list) else set()
        except:
            return set()

    @classmethod
    def _write_registry(cls, names):
        try:
            with open(cls.REGISTRY_FILE, "w") as f:
                json.dump(list(names), f)
        except Exception as e:
            logger.error(f"Failed to write SHM registry: {e}")

    @classmethod
    def register(cls, name):
        """Adds a shared memory block name to the registry."""
        names = cls._read_registry()
        if name not in names:
            names.add(name)
            cls._write_registry(names)

    @classmethod
    def unregister(cls, name):
        """Removes a shared memory block name from the registry."""
        names = cls._read_registry()
        if name in names:
            names.remove(name)
            cls._write_registry(names)

    @classmethod
    def get_all(cls):
        """Returns a list of all tracked SHM block names."""
        return list(cls._read_registry())

    @classmethod
    def clear(cls):
        """Wipes the registry file."""
        if os.path.exists(cls.REGISTRY_FILE):
            try:
                os.remove(cls.REGISTRY_FILE)
            except:
                pass
