# Synapse VS (SVS) - Developer Guide

This document provides a technical deep dive into the Synapse VS backend, architecture, and extension patterns.

## 🏗️ Architecture Overview

SVS follows a modular "Engine-Bridge-GUI" architecture to ensure robustness and responsiveness.

### 1. Hybrid Execution Engine (`ExecutionEngine`)

The heart of SVS, responsible for graph pulsing and node execution.

- **Flow Control**: Managed by `FlowController`. It uses a **Priority Queue** (`heapq`) to schedule node execution. High-priority flows (e.g., UI interactions) run before background tasks.
- **Yielding**: Nodes can return `_YSWAIT` or `_YSYIELD` signals to pause execution without blocking the thread, allowing other ready nodes to run.
- **Context Management**: `ContextManager` handles nested scopes (loops, try/catch, subgraphs).
- **Node Dispatching**: `NodeDispatcher` routes nodes to either the **Native Track** (Worker Thread) or **Heavy Track** (Subprocess).

### 2. Synapse Bridge (`SynapseBridge`)

The IPC (Inter-Process Communication) layer.

- Uses `multiprocessing.Manager` to share data across process boundaries.
- **Variable Vault**: A thread-safe store for all port values and global variables.
- **Locking Protocol**: Prevents race conditions during shared resource access.
- **Identity & Session Manager (ISM)**: A secure registry in the Bridge that maps **App IDs** to `IdentityObject` dictionaries, managing multi-user contexts.

### 3. Architect UI (`MainWindow`)

The frontend built with PyQt6.

- **Minimap/Miniworld**: High-performance overview viewports.
- **Bridge Poller**: Syncs visual state with the backend at 33Hz.

---

## 🛠️ Extending Synapse VS

There are two primary ways to add new functionality to SVS.

### 1. Creating Code-Based Nodes (Python)

Written in Python and registered directly into the library. These are best for low-level system integrations or high-performance logic.

- **Location**: `synapse/nodes/lib/`
- **Pattern**:

    ```python
    from synapse.core.node import BaseNode
    from synapse.nodes.registry import NodeRegistry

    @NodeRegistry.register("My Custom Node", "My Category")
    class MyNode(BaseNode):
        def __init__(self, node_id, name, bridge):
            super().__init__(node_id, name, bridge)
            self.is_native = True # Run in thread (Native) vs process (Heavy)

        def execute(self, InputData=None, **kwargs):
            # Your Logic Here
            result = f"Processed: {InputData}"
            
            # Signal outputs via Bridge
            self.bridge.set(f"{self.node_id}_OutputData", result, self.name)
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
            return True
    ```

### 2. Creating Plugin-Based Nodes (.syp Graphs)

Any graph you create in the Architect can become a reusable node.

- **How it works**:
    1. Build your logic in a new tab.
    2. Set a **Project Name** and **Category** in the Project Tab (Right Dock).
    3. Save the graph to the `plugins/` folder.
- **Plugin Discovery**: On startup, SVS scans the `plugins/` directory and registers any `.syp` files as nodes in the Node Library.
- **Property Propagation**: Custom properties set on the parent "SubGraph Node" are automatically injected into the internal `Start Node` of the child graph.

### 3. Creating Custom AI Providers

AI Providers use a unified interface pattern. All providers inherit from `AIProvider` and implement the same methods.

- **Location**: `synapse/nodes/lib/ai_nodes.py`
- **Pattern**:

    ```python
    from synapse.nodes.lib.ai_nodes import AIProvider
    from synapse.nodes.registry import NodeRegistry
    from synapse.core.node import BaseNode
    from synapse.core.types import DataType

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
            return [(\"Flow\", DataType.FLOW), (\"API Key\", DataType.STRING), (\"Model\", DataType.STRING)]

        @property
        def default_outputs(self):
            return [(\"Flow\", DataType.FLOW), (\"Provider\", DataType.ANY)]

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

- **The DataBuffer**: Defined in `synapse/core/data.py`, this wrapper protects the UI from lagging. Huge binary payloads are masked as string `[data]` in the console and properties panel. They are only unpacked when needed by processing nodes.
- **ErrorObject**: A standardized container for exceptions that captures Project Name, Node Name, Inputs, and Stack Traces, passing them safely across the Bridge.

#### Proprietary Formats

- **Datetime `#[...]#`**: Time operations in `synapse/utils/datetime_utils.py` require strict wrapping (e.g., `#[2025-10-01]#`).
  - Supports dynamic arithmetic (e.g., `+ 1 Day`, `- 3 Years`).
  - Auto-detects `YYYY-MM-DD` vs `YYYY-MM-DD HH:MM:SS`.

#### SubGraph Intelligence

- **Hot Reloading & Cache Invalidation**: The `SubGraphNode` monitors the source `.syp` file. If the data changes, it invalidates the current `ExecutionEngine` and `SynapseBridge` cache, performing a fresh reload to ensure the graph executes the newest logic.
- **Robust Loading**: Utilizes a shared `load_graph_data` utility in `synapse/core/loader.py` that handles unregistered node types via a generic fallback.
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

Synapse VS uses a lightweight **Hot Package** system to manage optional dependencies. Only 4 packages are required (`PyQt6`, `requests`, `psutil`, `numpy`) — everything else is installed on-demand.

### How It Works

- **`synapse/core/dependencies.py`** contains the `DependencyManager` class.
- `DependencyManager.ensure(pip_name, import_name)` checks if a package is installed. If not, it prompts the user via a GUI dialog (or auto-installs in headless mode).
- Each node file defines `ensure_*()` helper functions at module level that wrap `DependencyManager.ensure()` and cache the imported module in a global variable.

### Pattern for Adding Optional Dependencies

When creating a new node that needs a package not in `requirements.txt`:

```python
from synapse.core.dependencies import DependencyManager

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
| **ExecutionEngine** | Core logic & loop | `synapse/core/engine.py` |
| **SynapseBridge** | Data sharing & IPC | `synapse/core/bridge.py` |
| **NodeRegistry** | Node discovery | `synapse/nodes/registry.py` |
| **FlowController** | Queueing & Branching | `synapse/core/flow_controller.py` |
| **DependencyManager** | Hot Package install & lazy loading | `synapse/core/dependencies.py` |
| **DataBuffer** | Large Data protection | `synapse/core/data.py` |
| **TypeCaster** | Type validation & casting | `synapse/core/types.py` |
| **ErrorObject** | Standardized error container | `synapse/core/data.py` |
| **NamespaceGenerator** | Collision-safe worker naming | `synapse/utils/namespace.py` |

---

## ⚡ Parallel Execution Architecture

The `ParallelRunnerNode` enables batch parallel processing using Python's `multiprocessing.Pool`.

### Worker Isolation

Each worker runs in its own process with:

- **Isolated Bridge**: Fresh `multiprocessing.Manager` + `SynapseBridge` — no shared state with parent.
- **Scoped Name**: Unique `[Name]_[Index]_[4HexDigits]` identifier via `synapse/utils/namespace.py`.
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

## 🌐 Synapse Connectivity & Identity Architecture (SCIA)

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

Synapse VS includes a powerful **Interactive Node Auditor** located at `tools/audit_nodes.py`. It provides an isolated CLI Sandbox to execute and test nodes safely without booting the full UI.

### 1. General Sandbox Execution

By default, the Auditor will instantiate an isolated `ExecutionEngine` and `SynapseBridge`. It reads the node's `input_schema` and auto-prompts the developer for mock inputs via the terminal.

- **Watchdog Protection**: Executions are wrapped in a 10-second watchdog thread. If a node infinite loops or a Native Thread blocks indefinitely, the Sandbox catches the hang and auto-fails the run without crashing the script.
- **Provider Sub-Testing**: The Sandbox automatically detects nodes that require a Provider context. You cannot test these nodes on their own. Instead, testing a Provider Node directly will first start it, hold it alive, and recursively prompt to test any child node that depends on its connection!

### 2. "One-Shot" CLI Mode

You can bypass the interactive menu entirely and instantly execute a Sandbox (or Custom Test) via the command line:

`python tools/audit_nodes.py -n "Node Name"`

This triggers **One-Shot Mode**, which is ideal for rapidly debugging a specific Native Node or SuperNode handler during development. It forcefully auto-mocks inputs and guarantees that it won't track logs to the `audit_state.json` LEDGER.

### 3. Creating Custom Test Scripts

For complex nodes (like loops or external script executors), you may want to bypass the generic Sandbox prompt and inject custom execution limits, bridge arrays, or forced condition breaks to ensure the Watchdog doesn't trip on an empty dummy run.

- **Location**: `tools/auditor/custom_tests/`
- **Naming**: Convert the node's class name to snake_case (e.g., `while_node.py`).
- **Pattern**: When the Auditor audits your node, it will dynamically detect this file and route execution to the `run_test` method instead of the generic Sandbox.

```python
from tools.auditor.utils import Colors, DummyBridge

def run_test(namespaced_id, node_cls, is_os_mode):
    print(f"{Colors.YELLOW}Running custom test for {namespaced_id}...{Colors.RESET}")
    
    # Example: Build an isolated mock engine and inject variables early
    # ...
    
    # Return True for Success, False for Failure
    return True
```

---

&nbsp;
SVS Developer Docs - v1.4.0
