class ErrorRegistry:
    """
    Electronic Registry for Exception mapping and resolution.
    Supports legacy integer codes and modern string-based identifiers.
    """
    _instance = None
    
    # Default mappings for backward compatibility
    _DEFAULT_MAPPINGS = {
        "ZeroDivisionError": 1,
        "ValueError": 2,
        "TypeError": 3,
        "KeyError": 4,
        "IndexError": 5,
        "FileNotFoundError": 6,
        "PermissionError": 7,
        "RuntimeError": 8,
        "AbortedError": 9,
        "TimeoutError": 10
    }

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ErrorRegistry, cls).__new__(cls)
            cls._instance.mappings = cls._DEFAULT_MAPPINGS.copy()
        return cls._instance

    @classmethod
    def register_error(cls, error_name: str, code: int):
        """Registers a custom error mapping."""
        inst = cls()
        inst.mappings[error_name] = code

    @classmethod
    def get_code(cls, error_name: str):
        """
        Returns the mapped code (int) if it exists.
        Otherwise, returns the error name itself (extensible string ident).
        """
        inst = cls()
        return inst.mappings.get(error_name, error_name)

    @classmethod
    def get_all_mappings(cls):
        return cls().mappings.copy()
