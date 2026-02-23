# Synapse VS (SVS) - Visual Scripting

![Synapse VS Logo](f:/Synapse%20OS/synapse/gui/node_library/icons/app_icon.png)

**Synapse VS (Visual Script)** is a powerful, node-based automation and data processing platform. It allows users to build complex workflows using a visual interface, combining AI, system operations, and data transformations into cohesive "graphs".

## 🚀 Key Features

* **Universal AI Nodes**: Seamlessly switch between **Ollama (local)**, **OpenAI**, and **Google Gemini** using a unified `Ask AI` provider pattern.
* **Hybrid Execution Engine**: High-performance "Native" threading for lightweight nodes and isolated "Heavy" processes for custom scripts and unstable tasks.
* **Hot Packages**: Optional dependencies are installed on-demand — the first time you use a node that needs an extra library, SVS prompts you to install it automatically. No manual `pip install` needed.
* **Secure API Management**: Pass API keys dynamically via input ports or securely fetch them from OS **Environment Variables**.
* **Dynamic Subgraphs**: Build reusable tools and "favorited" subgraphs with full property propagation from parent nodes.
* **Architect UI**:
  * **Miniworld & Layout**: Asymmetric layout with 2 large and 4 small viewports. Slots track "Offline/Disconnected" graphs and must be manually assigned via right-click context menu.
  * **Deep Search**: Top-right search box scans Node Names, Types, and *Properties* (e.g., URLs). Press Enter to cycle logically through matches with a "pulse" animation.
  * **Visual Feedback**:
    * **Purple Highlight**: Running Native Service (e.g., Flask).
    * **Green Border**: Active SubGraph execution.
    * **Kinetic Fading**: Wires fade out over 1 second to trace execution paths.
  * **Smart Features**:
    * **Hot-Reloading**: Auto-updates subgraphs when files change.
    * **Auto-Save**: Triggers 3 seconds after metadata changes.
    * **Session Restore**: Reopens previous tabs, layout, and viewports on launch.
* **Extensible Plugin System**: Easily add new nodes and providers in Python.

## 🚀 Getting Started

### 1. Installation

1. **Clone the Repo**: `git clone https://github.com/Antigravity-Team/SynapseVS.git`
2. **Run**: Double-click `synapse.bat` (Windows) or run `python synapse.py` (Linux/Mac).
    * *Note: First run will prompt you to choose between **Minimal** (online hot-loading) or **Full** (offline capable) installation.*

### 2. Hello World

Let's build your first graph:

1. **Create New Graph**: Click `File -> New Graph`.
2. **Add Nodes**:
    * Right-click the canvas to open the context menu.
    * Search for **Start** and add it. (Required for every graph)
    * Search for **Toast Notification** (under GUI) and add it.
    * Search for **Return** and add it. (Ends the execution)
3. **Connect Flow**:
    * Drag a wire from **Start**'s "im" (Flow) port to **Toast Notification**'s "im" port.
    * Drag a wire from **Toast Notification**'s "out" port to **Return**'s "im" port.
4. **Configure Properties**:
    * Click the **Toast Notification** node.
    * In the **Properties Panel** (right side), set the "Message" property to `"Hello World"`.
5. **Run**: Press **F5** or click the Play button (▶). You should see a Windows notification pop up!
    * *Tip: Use the **Speed Slider** in the toolbar to slow down execution and watch the flow move node-to-node.*

### 3. Build Your Logic

1. **Open or Create a Graph**: Start with a new graph or open an existing `.syp` file.
2. **Build Your Logic**: Drag nodes from the Library, wire them together, and configure their properties.
3. **Execute**: Hit **F5** or the Play button to run your graph and observe real-time flow highlights.

## 📖 Documentation

For detailed guides, check the `docs/` folder:

* [Getting Started](file:///f:/My%20Programs/Synapse%20VS/docs/Installing.md) - Install and launch SVS.
* [How to Use](file:///f:/My%20Programs/Synapse%20VS/docs/UI_Usage.md) - Learn the Architect interface.
* [Node Reference](file:///f:/My%20Programs/Synapse%20VS/docs/nodes/Index.md) - Complete guide to available nodes.

* [Power User Guide](file:///f:/My%20Programs/Synapse%20VS/docs/PowerUser.md) - Advanced tips, tricks, and example graphs.
* [Developer Guide](file:///f:/My%20Programs/Synapse%20VS/docs/developer.md) - Technical breakdown for backend and extensions.

## ⚖️ License

SVS Alpha is provided for **single use** only. For commercial use inquiries, please email **<compaces79@gmail.com>**.

See [License](file:///f:/My%20Programs/Synapse%20VS/license.md) for full details.
