# 🎨 How to Use Synapse VS

Synapse VS Architect is your creative workspace for building automated workflows. Here’s a quick guide to getting around.

## 🖱️ Navigating the Canvas

This is where you build your graphs.

- **Move around**: Right-click and drag anywhere on the background.
- **Zoom In/Out**: Use your mouse scroll wheel.
- **Select a Node**: Click any node to select it.
- **Select many**: Click and drag a box around multiple nodes.
- **Duplicate**: Select a node and press **Ctrl+D**.
- **Delete**: Select a node and press **Delete**.

## 🏗️ Adding & Connecting Nodes

- **Connecting logic**: Click a port (the small circles) and drag a wire to another port.
  - **Green wires**: These decide the *order* of events (Do this, then do that).
  - **Colored wires**: These pass *data* (like a name, a number, or a message).

## ⚡ Advanced Flow Design

Synapse VS allows for complex, multi-threaded logic through its flexible wiring system:

- **Branching (Split Tasks)**: You can hook a single **Flow Output** into multiple different paths. This "splits" the execution, allowing multiple tasks to run in parallel.
- **Merging (Join Tasks)**: A single **Flow Input** can accept wires from multiple different output ports. This is useful for creating consolidated join points or "multi-trigger" nodes.
- **Loops & Back-Checking**: You can wire a Flow Output *back* to an earlier node in the graph. This creates a loop-back system (e.g., retrying an AI prompt if the result is invalid).
- **Background Tasks**: By splitting a flow, you can start a continuous loop or background process while the main task proceeds unaffected on a different path.

## 🖥️ The Interface

### Left Side: Node Library

Search for anything here! You can find AI tools, math, system commands, and more.

### Right Side: Settings & Properties

- **Properties Tab**: This is where you configure the selected node (e.g., typing a message for the AI).
- **Project Tab**: Change your project name or category here.

### Top Right: Smart Search

The search bar in the top-right corner is a deep **Magic Search** tool that understands your graph's structure:

- **Find Nodes**: Type a name like "Ask AI" to highlight those nodes.
- **Find Types**: Type "System" or "Flow" to see all nodes of that category.
- **Find Properties**: Type a value (e.g., `https://` or `MyVar`) to find every node that uses that specific URL or variable!
- **Magic Targets**: Use dot-notation (e.g., `login.button`) to navigate through complex functional clusters.
- **Navigation**: Press **Enter** to cycle through matches. The view will automatically pan and "pulse" the matching node.

### Bottom: Console & Minimap

- **Console**: See the results of your work (like messages from a `Print` node).
- **Minimap**: A small map to help you find your way around large graphs.
  - **Detached Mode**: Right-click the Minimap or mini-viewport to **Detach** it. This opens the telemetry map in a separate OS window that you can drag to a second monitor for permanent monitoring.

## 📦 Grouping & Organization

Keep your graphs clean and readable with these tools:

### Frames

Frames allow you to group related nodes together visually.

- **Create**: Right-click on the canvas and select **Add Frame**.
- **Resize**: Drag the edges of the frame.
- **Hot-Reloading**: Subgraphs update instantly when the source `.syp` file is saved.

---
[Return to README](file:///f:/My%20Programs/Synapse%20VS/README.md)

- **Move**: Drag the frame header to move all nodes inside it.
- **Color**: Right-click the header to change the frame color.
- **Auto-Fit**: Double-click the frame header to automatically resize it to fit its contents.

### Customizing Nodes

Make your important nodes stand out!

- **Rename**: Double-click a node's header or use the Properties panel to give it a meaningful name (e.g., "Main Loop" instead of "Loop").
- **Colors**: Right-click a node and select **Set Color** to choose a custom header color.
- **Reset**: Right-click and choose **Reset Style** to revert to default code-based coloring.

## ⌨️ Helpful Shortcuts

- **F5**: Run your graph!
- **F9 / Shift+F9**: Step Forward / Step Backward during debugging.
- **Ctrl+S**: Save your work.
- **F2**: Zoom out to see the whole graph at once.
- **F11**: Go fullscreen for a distraction-free experience.

## 📦 Install Dialogs

Some nodes require optional libraries (like `opencv-python` or `flask`). The first time you run one of these nodes, a dialog will appear asking to install the missing package. Click **Yes** to install it automatically — the node will work immediately after installation.
