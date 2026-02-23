# Synapse OS System Constants
# These are cached at startup to avoid repeated system calls.

import platform
import os

# Cached OS Detection
PLATFORM_SYSTEM = platform.system()  # "Windows", "Linux", "Darwin"
OS_NAME = os.name  # "nt", "posix", etc.

# Convenience Booleans
IS_WINDOWS = PLATFORM_SYSTEM == "Windows"
IS_LINUX = PLATFORM_SYSTEM == "Linux"
IS_MACOS = PLATFORM_SYSTEM == "Darwin"
IS_NT = OS_NAME == "nt"
IS_POSIX = OS_NAME == "posix"
