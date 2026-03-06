# AxonPulse VS (SVS) - Developer Guide

This document provides a technical deep dive into the AxonPulse VS backend, architecture, and extension patterns.

## 🏗️ Architecture Overview

SVS follows a modular "Engine-Bridge-GUI" architecture to ensure robustness and responsiveness.

### 1. Hybrid Execution Engine (`ExecutionEngine`)

The heart of SVS, responsible for graph pulsing and node execution.

- **Flow Control**: Managed by `FlowController`. It uses a **Priority Queue** (`heapq`) to schedule node execution. High-priority flows (e.g., UI interactions) run before background tasks.
- **Yielding**: Nodes can return `_YSWAIT` or `_YSYIELD` signals to pause execution without blocking the thread, allowing other ready nodes to run.
- **Context Management**: `ContextManager` handles nested scopes (loops, try/catch, subgraphs).
- **Node Dispatching**: `NodeDispatcher` routes nodes to either the **Native Track** (Worker Thread) or **Heavy Track** (Subprocess).
- **Lifecycle Management (v2.1.0)**: Nodes strictly follow the `define_schema() -> register_handlers() -> __init__` sequence. 
  - **Defensive Data Resolution**: If `execute()` receives a `kwargs` mismatch, it automatically checks `self.properties` for fallback values before failing.

### 2. AxonPulse Bridge (`AxonPulseBridge`)

The IPC (Inter-Process Communication) layer.

- Uses `multiprocessing.Manager` to share data across process boundaries.
- **Variable Vault**: A thread-safe store for all port values and global variables.
- **Object Contexts**: The Bridge supports `set_object`/`get_object` for sharing complex, thread-bound objects (like Browser handles) across modular nodes without pickling overhead.
- **Locking Protocol**: Prevents race conditions during shared resource access.
- **Identity & Session Manager (ISM)**: A secure registry in the Bridge that maps **App IDs** to `IdentityObject` dictionaries, managing multi-user contexts.
- **Interactive Prompts**: `request_asset_password(zip_path)` allows background discovery threads to block and wait for UI password entry via atomic `AssetPasswordRequest/Response` signals.

### 3. Architect UI (`MainWindow`)

The frontend built with PyQt6.

- **Minimap/Miniworld**: Detachable high-performance overview viewports with independent OS window grouping.
- **Bridge Poller**: Syncs visual state with the backend at 33Hz.
- **Canvas Rendering (Viewport Culling)**: Your approach to only drawing visible nodes (with a slight buffer margin for smooth panning) is exactly the right path. In PyQt6, the QGraphicsScene relies heavily on bounding rects. By explicitly telling the canvas to suspend complex paint operations (like drop shadows, antialiasing on thick wires, or live text updates) when a node's bounding box intersects outside the visible viewport, you can keep the framerate locked at 60 FPS even with thousands of nodes. It is highly effective and requires far less overhead than writing custom OpenGL shaders.

---

## 🛠️ Extending AxonPulse VS

There are two primary ways to add new functionality to SVS.

### 1. Creating Code-Based Nodes (Python)

Written in Python and registered directly into the library. These are best for low-level system integrations or high-performance logic.

- **Location**: `axonpulse/nodes/lib/`
- **Pattern**:

    ```python
    from axonpulse.core.super_node import SuperNode
    from axonpulse.nodes.registry import NodeRegistry
    from axonpulse.core.types import DataType

    @NodeRegistry.register("My Custom Node", "My Category")
    class MyNode(SuperNode):
        version = "2.1.0"

        def __init__(self, node_id, name, bridge):
            super().__init__(node_id, name, bridge)
            self.define_schema()
            self.register_handlers()

        def define_schema(self):
            self.input_schema = { "Flow": DataType.FLOW, "Data": DataType.STRING }
            self.output_schema = { "Flow": DataType.FLOW, "Result": DataType.STRING }

        def register_handlers(self):
            self.register_handler("Flow", self.do_work)

        def do_work(self, Data=None, **kwargs):
            # 1. Resolve inputs (auto-unwrapped from bridge)
            val = Data or self.properties.get("Data", "Default")
            
            # 2. Logic
            result = f"Hello {val}!"
            
            # 3. Set outputs
            self.set_output("Result", result)
            
            # 4. Signal next flow
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
            return True
    ```

### 2. Creating Plugin-Based Nodes (.syp Graphs)

Any graph you create in the Architect can become a reusable node.

- **How it works**:
    1. Build your logic in a new tab.
    2. Set a **Project Name** and **Category** in the Project Tab (Right Dock).
    3. Save the graph to the `plugins/` folder.
- **Plugin Discovery**:
    - **Phase 1 (Boot)**: Scans for `.syp` and unencrypted `.spy` nodes for instant availability. Uses `SourceFileLoader` to bypass `.py` extension requirements.
    - **Phase 2 (Bridge Up)**: Performs a second pass with a `bridge` handle to process encrypted `.zip` packages.
- **ZIP Extraction Lifecycle**:
    - Enforces extraction to `plugins/extracted/<zip_name>/`.
    - Uses a directory-existence guard to prevent redundant extractions.
    - Supports AES-256 via `pyzipper` with a manual password request flow.
- **Property Propagation**: Custom properties set on the parent "SubGraph Node" are automatically injected into the internal `Start Node` of the child graph.

### 3. Creating Custom AI Providers

AI Providers use a unified interface pattern. All providers inherit from `AIProvider` and implement the same methods.

- **Location**: `axonpulse/nodes/lib/ai_nodes.py`
- **Pattern**:

    ```python
    from axonpulse.nodes.lib.ai_nodes import AIProvider
    from axonpulse.nodes.registry import NodeRegistry
    from axonpulse.core.node import BaseNode
    from axonpulse.core.types import DataType

    class MyCustomProvider(AIProvider):
        def __init__(self, api_key, model, endpoint):
            self.api_key = api_key
            self.model = model
            self.endpoint = endpoint

        def generate(self, system_prompt, user_prompt, files, model_override=None, **kwargs):
            """Synchronous generation. Returns full text response."""
            model = model_override or self.model
            # Build your API request here
            # Return the generated text string
            return "Generated response text"

        def stream(self, system_prompt, user_prompt, files, model_override=None, **kwargs):
            """Streaming generation. Yields text chunks."""
            model = model_override or self.model
            # Build your API request with stream=True
            # Yield chunks as they arrive
            for chunk in your_stream_response:
                yield chunk

        def get_models(self):
            """Optional: Returns list of available models."""
            return ["model-a", "model-b"]

    @NodeRegistry.register("My Provider", "AI")
    class MyProviderNode(BaseNode):
        def __init__(self, node_id, name, bridge):
            super().__init__(node_id, name, bridge)
            self.properties["api_key"] = ""
            self.properties["model"] = "default-model"
            self.properties["endpoint"] = "https://api.example.com"

        @property
        def default_inputs(self):
            return [("Flow", DataType.FLOW), ("API Key", DataType.STRING), ("Model", DataType.STRING)]

        @property
        def default_outputs(self):
            return [("Flow", DataType.FLOW), ("Provider", DataType.ANY)]

        def execute(self, **kwargs):
            api_key = kwargs.get("API Key") or self.properties.get("api_key")
            
            # [ENV VAR FALLBACK] Check environment variable if empty
            if not api_key:
                api_key = os.environ.get("MY_API_KEY")

            model = kwargs.get("Model") or self.properties.get("model")
            provider = MyCustomProvider(api_key, model, self.properties.get("endpoint"))
            self.bridge.set(f"{self.node_id}_Provider", provider, self.name)
            return True
    ```

- **Usage**: The `Ask AI` node automatically works with any provider that implements the `generate()` and `stream()` methods.
- **Streaming**: If your API supports SSE (Server-Sent Events), implement proper line parsing in `stream()`.
- **Files**: Handle the `files` parameter to support image/document inputs if your API supports them.

---

## 🔬 Core Components Summary

### 4. Engine Mechanics & Safety

#### Strict Validation

- **Production Mode**: To run in production, a graph *must* have exactly one **Start Node** and at least one **Return Node**.
- **Panic Routing**: The `ExecutionEngine` checks for node failures. If a node crashes and the Start Node has an **Error Flow** or **Panic** port wired, execution is redirected there instead of halting.

#### Data Safety Systems

- **The DataBuffer**: Defined in `axonpulse/core/data.py`, this wrapper protects the UI from lagging. Huge binary payloads are masked as string `[data]` in the console and properties panel. They are only unpacked when needed by processing nodes.
- **ErrorObject**: A standardized container for exceptions that captures Project Name, Node Name, Inputs, and Stack Traces, passing them safely across the Bridge.

#### Proprietary Formats

- **Datetime `#[...]#`**: Time operations in `axonpulse/utils/datetime_utils.py` require strict wrapping (e.g., `#[2025-10-01]#`).
  - Supports dynamic arithmetic (e.g., `+ 1 Day`, `- 3 Years`).
  - Auto-detects `YYYY-MM-DD` vs `YYYY-MM-DD HH:MM:SS`.

#### SubGraph Intelligence

- **Hot Reloading & Cache Invalidation**: The `SubGraphNode` monitors the source `.syp` file. If the data changes, it invalidates the current `ExecutionEngine` and `AxonPulseBridge` cache, performing a fresh reload to ensure the graph executes the newest logic.
- **Robust Loading**: Utilizes a shared `load_graph_data` utility in `axonpulse/core/loader.py` that handles unregistered node types via a generic fallback.
- **Hot-Loading**: Contents (nodes and subgraphs) are instantly registered into the active library upon successful authentication.
  - **Node Versioning (v2.2.0)**: Tracks the schema version of each node instance.
- **Version Conflict**: It compares the `project_version` of the external file vs the embedded data, always choosing the newer version.
- **Error Bubbling**: Exceptions in a subgraph bubble up to the parent node's "Error Flow" port if connected.
- **Dynamic Outputs**: SubGraph nodes scan child graph Return nodes and build outputs dynamically:
  - Each Return node's **label** becomes a named **Flow output** on the SubGraph.
  - Return node **variables** (`additional_inputs`) appear as data outputs grouped below their Flow.
  - Return nodes are sorted **top-left to bottom-right** (Y then X).
  - Falls back to `[Flow, Return, Done, Success]` if no specific flow is triggered.

#### Switch Node Architecture

- **Case Storage**: Cases are stored as `[{"name": "Display Name", "value": "match_value"}, ...]` in `properties["cases"]`.
- **Matching**: Case-insensitive string matching + numeric comparison. Falls back to "Default" port.
- **GUI Integration**: "Add Case" context menu updates both the port and the property list.

#### Log Rotation

- **Rolling Files**: The Log Node rotates files when they exceed `max_size_kb`.
- **Rotation Chain**: `log.txt` → `log.txt.1` → `log.txt.2` → ... → deleted at `backup_count`.
- **Levels**: INFO, WARN, ERROR, DEBUG, TRACE with millisecond timestamps.

#### File System Context

- **Relative Path Resolution**: Nodes like `Read File` automatically resolve relative paths against the global Project Variables.
- **Fallback**: If no project path is set, it defaults to `os.getcwd()`.
- **Auto-Creation**: `Write File` automatically calls `os.makedirs` for missing parent directories.

---

## 📦 Hot Packages & DependencyManager

AxonPulse VS uses a lightweight **Hot Package** system to manage optional dependencies. Only 4 packages are required (`PyQt6`, `requests`, `psutil`, `numpy`) — everything else is installed on-demand.

### How It Works

- **`axonpulse/core/dependencies.py`** contains the `DependencyManager` class.
- `DependencyManager.ensure(pip_name, import_name)` checks if a package is installed. If not, it prompts the user via a GUI dialog (or auto-installs in headless mode).
- Each node file defines `ensure_*()` helper functions at module level that wrap `DependencyManager.ensure()` and cache the imported module in a global variable.

### Pattern for Adding Optional Dependencies

When creating a new node that needs a package not in `requirements.txt`:

```python
from axonpulse.core.dependencies import DependencyManager

# Lazy Global
my_lib = None

def ensure_my_lib():
    global my_lib
    if my_lib: return True
    if DependencyManager.ensure("pip-package-name", "import_name"):
        import import_name as _m; my_lib = _m; return True
    return False

# In your node's execute()
def execute(self, **kwargs):
    if not ensure_my_lib():
        print(f"[{self.name}] Error: pip-package-name not installed.")
        return False
    # Use my_lib safely here
```

### Key Rules

- **Never** add `try/except ImportError` blocks for optional packages — always use `DependencyManager`.
- The `import_name` parameter is needed when the pip name differs from the Python module (e.g., `pip: opencv-python` → `import: cv2`).
- The helper function should be called in `execute()` before any use of the library.

---

## 📊 Core Components Table

| Component | Responsibility | Key File |
| :--- | :--- | :--- |
| **ExecutionEngine** | Core logic & loop | `axonpulse/core/engine.py` |
| **AxonPulseBridge** | Data sharing & IPC | `axonpulse/core/bridge.py` |
| **NodeRegistry** | Node discovery | `axonpulse/nodes/registry.py` |
| **FlowController** | Queueing & Branching | `axonpulse/core/flow_controller.py` |
| **DependencyManager** | Hot Package install & lazy loading | `axonpulse/core/dependencies.py` |
| **DataBuffer** | Large Data protection | `axonpulse/core/data.py` |
| **TypeCaster** | Type validation & casting | `axonpulse/core/types.py` |
| **ErrorObject** | Standardized error container | `axonpulse/core/data.py` |
| **NamespaceGenerator** | Collision-safe worker naming | `axonpulse/utils/namespace.py` |

---

## ⚡ Parallel Execution Architecture

The `ParallelRunnerNode` enables batch parallel processing using Python's `multiprocessing.Pool`.

### Worker Isolation

Each worker runs in its own process with:

- **Isolated Bridge**: Fresh `multiprocessing.Manager` + `AxonPulseBridge` — no shared state with parent.
- **Scoped Name**: Unique `[Name]_[Index]_[4HexDigits]` identifier via `axonpulse/utils/namespace.py`.
- **Scoped Logger**: All console output prefixed with worker name (e.g., `[OCR_Worker_1_A2B3] Found text`).

### Worker Bootstrap

1. Worker receives a payload: `{graph_data, item, item_index, scoped_name}`
2. Creates isolated Manager + Bridge
3. Injects `_PARALLEL_ITEM`, `_PARALLEL_INDEX`, `_PARALLEL_WORKER` into Bridge
4. Instantiates headless `ExecutionEngine` from graph data
5. Runs engine → returns result dict `{index, item, scoped_name, result, error, success}`

### Collision Prevention

The `generate_scoped_name()` function uses `os.urandom(2)` for the hex suffix and checks against an `active_names` set, regenerating on collision (up to 1000 attempts).

---

## 🧩 Strategy Patterns

### NLP Chunking Strategy

The Chunking system uses a **Provider-Strategy** pattern to allow dynamic text segmentation.

1. **Provider Node**: (e.g., `Fixed Size Chunking`)
    - Registers itself as `Chunking Provider`.
    - Stores a **Strategy Name** (e.g., `FixedSizeChunkingNode`) and **Configuration JSON** in the Bridge.
2. **Consumer Node**: (`Chunk String`)
    - Locates the active Provider ID via Context Stack.
    - Retrieves the Strategy Name and Config.
    - Executes the logic locally using a static helper class (`ChunkingStrategy`).
    - **Benefit**: Decouples the specialized logic from the generic consumer node, allowing new chunking methods to be added without modifying the consumer.

---

## 🌐 AxonPulse Connectivity & Identity Architecture (SCIA)

SCIA is a protocol-agnostic framework for handling secure, multi-tenant connectivity.

### 1. Identity Management

- **`IdentityObject`**: A standard dictionary containing `uid`, `username`, `roles`, and an `auth_payload` for session-specific tokens.
- **App ID (Session Scope)**: Ingress nodes (like `Flask Route`) generate a unique `App ID` for every request, which is used to scope variables and identities in the ISM.

### 2. Provider-Action Pattern

- **Providers**: Config nodes (REST, WSS, gRPC) that output a **Connection Handle**.
- **Actions**: Handling nodes (e.g., `Net Request`) that use the handle to perform operations. They automatically look up the current session's identity in the ISM and inject appropriate auth headers.

### 3. Middleware Security

- **Gatekeeper Node**: An RBAC barrier that checks if the identity associated with an `App ID` has the required roles before allowing the flow to continue.

### 4. Provider Ports (Standard)

All `ProviderNode` instances follow a standardized port order for predictable wiring:

1. **Flow** (Output 1): Standard completion signal after the sub-graph (Provider Flow) completes.
2. **Provider Flow** (Output 2): Trigger for the scoped sub-graph logic.
3. **Provider ID** (Output 3): Unique handle for explicit wiring if needed.

---

## 🧪 Node Testing & Auditing

AxonPulse VS includes a powerful **Interactive Node Auditor** located at `tools/audit_nodes.py`. It provides an isolated CLI Sandbox to execute and test nodes safely without booting the full UI.

### 1. General Sandbox Execution

By default, the Auditor will instantiate an isolated `ExecutionEngine` and `AxonPulseBridge`. It reads the node's `input_schema` and auto-prompts the developer for mock inputs via the terminal.

- **Watchdog Protection**: Executions are wrapped in a 10-second watchdog thread. If a node infinite loops or a Native Thread blocks indefinitely, the Sandbox catches the hang and auto-fails the run without crashing the script.
- **Provider Sub-Testing**: The Sandbox automatically detects nodes that require a Provider context. You cannot test these nodes on their own. Instead, testing a Provider Node directly will first start it, hold it alive, and recursively prompt to test any child node that depends on its connection!

### 2. "One-Shot" CLI Mode

You can bypass the interactive menu entirely and instantly execute a Sandbox (or Custom Test) via the command line:

`python tools/audit_nodes.py -n "Node Name"`

This triggers **One-Shot Mode**, which is ideal for rapidly debugging a specific Native Node or SuperNode handler during development.

### 4. Version Auditing

Use `tools/audit_node_versions.py` to ensure all library nodes meet the current standard:

`python tools/audit_node_versions.py [min_version] [--sync]`

The `--sync` flag will automatically inject the missing `version` attribute into any outdated node files to bring them into compliance.

---

&nbsp;
SVS Developer Docs - v1.7.0

## 📈 Node Versioning (Future-Proofing)

To prevent graph breakage when a node's Python implementation is updated (e.g., adding a required port), SVS uses a schema-based versioning system.

### 1. Version Definition
Nodes define their version at the class level:
```python
class MyNode(SuperNode):
    node_version = 2
```

### 2. Mismatch Detection (Loader)
During `load_graph_data`, the engine compares the `node_version` stored in the graph JSON with the registry version. 
- If `Graph Version < Registry Version`: The node is marked as `is_legacy = True`.
- `version_mismatch` and `latest_version` properties are injected for the Architect UI to display a warning icon.

### 3. Interactive Upgrade Path
The UI can request an upgrade via the Bridge:
```python
bridge.request_node_upgrade(node_id, latest_version)
```

The `ExecutionEngine` polls for these requests in its control loop. When found, it:
1. Re-instantiates the node using the latest class.
2. Migrates compatible properties (preserving existing user configuration).
3. Re-registers ports via `PortRegistry` to maintain wire integrity.
4. Auto-restarts the service if the node is a `Provider` or `Service`.
