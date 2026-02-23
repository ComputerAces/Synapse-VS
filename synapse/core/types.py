from enum import Enum
import json

class DataType(Enum):
    FLOW = "flow"
    ANY = "any"
    STRING = "string"
    NUMBER = "number"
    INT = "number"
    INTEGER = "number"
    FLOAT = "number"
    BOOLEAN = "boolean"
    LIST = "list"
    DICT = "dict"
    IMAGE = "image"
    COLOR = "color"
    BYTES = "bytes"
    SCENEOBJECT = "sceneobject"
    SCENELIST = "scenelist"
    WRITEMODE = "write_type"
    WRITE_TYPE = "write_type"
    FTPACTIONS = "ftpactions"
    PASSWORD = "password"
    PROVIDER_FLOW = "provider_flow"
    DB_CONNECTION = "db_connection"
    COMPARE_TYPE = "compare_type"
    COMPARE = "compare_type"
    AUDIO = "audio"
    PROVIDER = "provider"
    TRIGGER = "trigger"
    DIALOG_MODE = "dialog_mode"
    DRAW_EFFECT = "draw_effect"
    MSGTYPE = "msgtype"
    MOUSEACTION = "mouseaction"
    SENDKEYMODE = "sendkey_mode"
    SENDKEY_MODE = "sendkey_mode"
    WINSTATEACTION = "winstateaction"

class SortType(Enum):
    NUMBER = "Number"
    STRING = "String"
    DATE = "Date"

class SortDirection(Enum):
    ASCENDING = "Ascending"
    DESCENDING = "Descending"

class DialogMode(Enum):
    OPEN_FILE = "Open File"
    SAVE_FILE = "Save File"
    OPEN_FOLDER = "Open Folder"

TYPE_COLORS = {
    DataType.FLOW: "#006400",   # Dark Green
    DataType.NUMBER: "#A0A0A0", # Gray
    DataType.STRING: "#B8860B", # Dark Goldenrod
    DataType.BOOLEAN: "#8B0000",# Dark Red
    DataType.LIST: "#8B008B",   # Dark Magenta
    DataType.DICT: "#00008B",   # Dark Blue
    DataType.IMAGE: "#008B8B",  # Dark Cyan
    DataType.COLOR: "#FF00FF",  # Magenta
    DataType.BYTES: "#4B0082",  # Indigo
    DataType.SCENEOBJECT: "#FF1493", # Deep Pink
    DataType.SCENELIST: "#00CED1", # Dark Turquioise
    DataType.WRITE_TYPE: "#32CD32", # LimeGreen
    DataType.WRITEMODE: "#32CD32",  # LimeGreen
    DataType.FTPACTIONS: "#FF8C00", # DarkOrange
    DataType.PASSWORD: "#708090",  # SlateGray
    DataType.ANY: "#696969",     # Dim Gray
    DataType.PROVIDER_FLOW: "#D11575", # Deep Pink (Darkened)
    DataType.DB_CONNECTION: "#4682B4", # Steel Blue
    DataType.COMPARE_TYPE: "#FFD700",  # Gold
    DataType.AUDIO: "#1E90FF",         # Dodger Blue
    DataType.TRIGGER: "#FF4500",       # OrangeRed
    DataType.DIALOG_MODE: "#7B68EE",    # MediumSlateBlue
    DataType.DRAW_EFFECT: "#FFD700",    # Gold
    DataType.MSGTYPE: "#FF69B4",        # HotPink
    DataType.MOUSEACTION: "#ADFF2F",    # GreenYellow
    DataType.SENDKEYMODE: "#FFB000", # Amber
    DataType.WINSTATEACTION: "#00E5FF" # Cyan
}

# [FIX] Robust Lookup: Support both Enum and String keys
for k, v in list(TYPE_COLORS.items()):
    if isinstance(k, DataType):
        TYPE_COLORS[k.value] = v

TYPE_COLORS[DataType.IMAGE] = "#00FFFF"
TYPE_COLORS["image"] = "#00FFFF"

class TypeCaster:
    """Safe runtime type conversion."""
    
    @staticmethod
    def to_number(val):
        """Attempts to convert to float/int."""
        if isinstance(val, (int, float)):
            return val
        if isinstance(val, bool):
            return 1 if val else 0
        if val is None:
            return 0
        try:
            s = str(val).strip()
            if "." in s:
                return float(s)
            return int(s)
        except:
            return 0 # Fail safe

    @staticmethod
    def to_bool(val):
        """
        Broad boolean conversion.
        "false", "0", 0, None, Empty -> False.
        """
        if isinstance(val, bool): return val
        if isinstance(val, (int, float)): return val != 0
        if val is None: return False
        
        s = str(val).lower().strip()
        if s in ["false", "0", "no", "off", ""]:
            return False
        return True

    @staticmethod
    def to_string(val):
        if isinstance(val, str): return val
        if val is None: return ""
        if isinstance(val, (list, dict)):
            try:
                return json.dumps(val)
            except:
                return str(val)
        return str(val)

    @staticmethod
    def to_list(val):
        if isinstance(val, list): return val
        if isinstance(val, (tuple, set)): return list(val)
        if val is None: return []
        # Try JSON parse if string
        if isinstance(val, str):
            if val.strip().startswith("["):
                try: return json.loads(val)
                except: pass
        return [val] # Wrap single item

    @staticmethod
    def to_dict(val):
        if isinstance(val, dict): return val
        if val is None: return {}
        if isinstance(val, str):
            if val.strip().startswith("{"):
                try: return json.loads(val)
                except: pass
        return {}

    @staticmethod
    def cast(val, target_type):
        if target_type == DataType.ANY or target_type == DataType.FLOW or target_type == DataType.PROVIDER_FLOW:
            return val
        if target_type == DataType.STRING:
            return TypeCaster.to_string(val)
        if target_type == DataType.NUMBER:
            return TypeCaster.to_number(val)
        if target_type == DataType.BOOLEAN:
            return TypeCaster.to_bool(val)
        if target_type == DataType.LIST:
            return TypeCaster.to_list(val)
        if target_type == DataType.DICT:
            return TypeCaster.to_dict(val)
        if target_type == DataType.PASSWORD:
            # Automatic hashing if not already looks like a hash (32+ chars hex)
            s_val = TypeCaster.to_string(val)
            if len(s_val) < 32: # Simple heuristic
                import hashlib
                return hashlib.sha256(s_val.encode()).hexdigest()
            return s_val
        # Image? usually object / bytes. No easy cast unless path string.
        return val

class SynapseJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle Synapse Enums and potential non-serializable types."""
    def default(self, obj):
        if isinstance(obj, Enum):
            return obj.value
        # Handle set/tuple to list conversion implicitly
        if isinstance(obj, (set, tuple)):
            return list(obj)
        try:
            return super().default(obj)
        except TypeError:
            # Final fallback to string
            return str(obj)
