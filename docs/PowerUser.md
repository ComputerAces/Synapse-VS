# Synapse VS: Power User Guide

Welcome to the deep end. This guide covers advanced tricks, troubleshooting tips, and fun graph ideas to maximize your creativity with Synapse VS.

## ⚡ Tricks & Tips

### 1. The "Passthrough" Debug

Want to see data flowing without breaking the connection?

- **Trick**: Use a **Data Buffer** node (or `String` node in pass-through) between two nodes. It acts as a monitoring point. You can click it to see the last value flowing through.

### 2. Hot-Reloading SubGraphs

Synapse caches SubGraphs for performance. If you edit a SubGraph file while the parent is running, it won't verify immediately.

- **Tip**: Toggle the **"Hot Reload"** property on the `SubGraph Node` (if available) or simply Stop and Start the parent graph to flush the cache.

### 3. Smart Typing

The Engine now enforces types strictly on Math ports to prevent silent errors.

- **Trick**: If you have a string "123" and need to Add it, use a **Python Script** node to cast it: `return int(A)`, OR rely on the Engine's new auto-caster which handles string-to-number conversion gracefully.

### 4. Parallel Processing

The **Dispatcher** runs heavy nodes (like `Shell Command`) in separate threads/processes.

- **Tip**: Connect multiple `Shell` nodes to the same `Start` flow to run them simultaneously! Use a `Barrier` or `Join` pattern (using logic nodes) to wait for all of them.

### 5. Safe Mode Override

Opened a graph and got the "Security Alert"?

- **Tricks**:
  - **Audit**: Read the JSON file in a text editor to verify the command arguments.
  - **Sandbox**: Run Synapse inside a VM if you test untrusted graphs frequently.

### 6. Batch File Processing

Need to process hundreds of files? Use the **Batch Iterator** node.

- **Tip**: Set Pattern to `*.png` and toggle Recursive to process an entire folder tree. Outputs give you File Path, File Name, Index, and Count for each iteration.

### 7. Rolling Logs for Services

Running a long-lived graph (like a web server or monitoring service)?

- **Tip**: Use the **Log Node** with rotation enabled. Files auto-rotate at 1MB by default, keeping the last 5 backups. Set `Level` to "ERROR" to capture only critical events, or "DEBUG" for verbose output.

-> [!TIP]
> Use the **Miniworld** to jump between these complex logic blocks quickly.

---
[Return to README](file:///f:/My%20Programs/Synapse%20VS/README.md)

### 8. Smart Switch Routing

The **Switch Node** supports named cases with separate display names and match values.

- **Tip**: Add a case named "Success" that matches value "200". Add another named "Not Found" matching "404". Connect each to different handling paths. The "Default" output catches everything else.

### 9. Parallel Processing with the Parallel Runner

Want to process a list of items simultaneously instead of one-by-one? The **Parallel Runner** node spawns multiple workers to run a subgraph in parallel.

### Step 1: Create your Worker Subgraph

Build a small graph in a new tab that does the work for **one item**:

```text
[Start] → [Get Variable: "_PARALLEL_ITEM"] → [Your Logic] → [Return]
```

- The `_PARALLEL_ITEM` variable is automatically set by the Parallel Runner to the current item.
- `_PARALLEL_INDEX` gives you the item's position in the list (0, 1, 2...).
- Save this graph as something like `worker.syp`.

### Step 2: Wire up the Parallel Runner

In your main graph:

```text
[Start] → [Build your list] → [Parallel Runner] → [Print / CSV Write / etc.]
```

- **Items**: Connect your list (e.g., file paths, URLs, data records).
- **Graph**: Path to `worker.syp`.
- **Threads**: Number of workers (e.g., 4 for a quad-core CPU).

### Step 3: Handle Results

- **Results** output gives you a list (same order as input) of each worker's return value.
- **Errors** output gives you a list of `{index, item, worker, error}` dicts for any failures.
- **Flow** fires if all workers succeeded; **Error Flow** fires if any failed.

**Example — Parallel URL Checker:**

```text
[Start]
  → [String: "https://google.com, https://github.com, https://example.com"]
  → [Split by ","]
  → [Parallel Runner (Graph: "url_checker.syp", Threads: 3)]
  → [Print: Results]
```

Where `url_checker.syp` is:

```text
[Start] → [Get Var: _PARALLEL_ITEM] → [HTTP Request (GET)] → [Return: Status Code]
```

Each URL is checked simultaneously — 3x faster than sequential!

---

### 10. Hot Packages (On-Demand Install)

Synapse VS doesn't install every library upfront. The first time you use a node that needs an extra package, you'll see an **Install Dialog**.

- **Tip**: Click **Yes** and it installs in seconds. The node will work immediately after.
- **Pre-install**: If you want packages ready ahead of time, open a terminal in the SVS virtual environment and run `pip install <package>`.
- **Headless**: When running graphs from the CLI (no GUI), missing packages are auto-installed without prompts.

---

### 11. The Provider System (Scoped Context)

The **Provider System** is a cornerstone of advanced architecture in Synapse VS. It allows you to define global configurations (API keys, ports, file paths) that are "pushed" to all downstream nodes automatically.

- **The Problem**: Wiring an "API Key" to 20 different AI nodes is messy and prone to errors.
- **The Solution**: Use a **Provider Node** at the start of your flow.

#### How It Works

1. **The Provider**: Nodes like `Gemini Provider`, `Browser Provider`, or `Logging Provider` set a context (e.g., specific API Key or Log Path).
2. **The Provider Flow**: These nodes have a special `Provider Flow` output. When this fires, all nodes inside that "sub-path" automatically detect the provider's settings.
3. **Auto-Injection (Zero-Wiring)**: Handlers like `Ask AI` or `Log` check for an active provider context before looking at their own local properties. If a provider is active, they "hijack" the settings automatically.

#### Pro Tips

- **Nesting**: You can nest providers! A `Logging Provider` can wrap a flow that contains multiple `AI Providers`.
- **Cleanup**: When the logic inside a `Provider Flow` finishes, it returns to the provider's standard `Flow` output, and the context is safely cleared.
- **Port Order**: All providers follow a standard layout:
  1. **Flow** (Exit signal)
  2. **Provider Flow** (The scoped sub-path)
  3. **Provider ID** (Explicit handle)

---

## 🔧 Troubleshooting

### "Node Process Failed with Exit Code 1"

- **Cause**: The Python script inside the node crashed.
- **Fix**: Check the **Debug** tab in the bottom panel. It captures the `stderr` from the process.

### "AI Response Hanging"

- **Cause**: Large models take time to generate.
- **Fix**: Use the new **Stream** port on the `Ask AI` node! It outputs text chunk-by-chunk, giving you that satisfying sci-fi typewriter effect.

---

## 🎲 Fun Graphs to Make

### 1. The "Auto-Coder" Loop

- **Nodes**: `Ask AI` (Ollama/Coder) <-> `Write File` <-> `Shell Command` (Run Test) <-> `Read File` (Error Log).
- **Logic**:
    1. AI writes code.
    2. Shell runs code.
    3. If Error, read log and feed back to AI to fix.
    4. Loop until success!

### 2. Daily News Digest

- **Nodes**: `Web Scraper` -> `Ask AI` (Summarize) -> `Send Email` (or Append to File).
- **Logic**: Scrape your favorite tech site, ask standard LLM to "Summarize in 3 bullet points", and save it to your desktop.

### 3. "Jarvis" Desktop Assistant

- **Nodes**: `Speech to Text` (if plugin exists) -> `Ask AI` -> `Text to Speech`.
- **Logic**: Create a voice-activated loop. Use `Math` nodes to detect specific trigger words like "Computer!" in the text stream.

### 4. Batch Image Processor

- **Nodes**: `Batch Iterator` (Pattern: `*.png`) -> `Image Load` -> `Universal OCR` -> `CSV Write`.
- **Logic**: Iterate all images in a folder, extract text via OCR, and write results to a CSV file for auditing.

### 5. Parallel OCR Pipeline

- **Nodes**: `Batch Iterator` -> collect file list -> `Parallel Runner` (Graph: `ocr_worker.syp`, Threads: 4) -> `CSV Write`.
- **Logic**: Scan a folder for images, then process them in parallel across 4 workers. Each worker loads and OCRs one image. Results aggregate back as a list for CSV export. 4x faster than sequential!

---

*Found a new trick? Share it with the community or add it to your personal `Notes.md`!*
