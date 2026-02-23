# 🚀 Getting Started with Synapse VS

Welcome to Synapse VS! Setting it up is quick and easy.

## 1. Prerequisites

You only need one thing:

- **Python 3.10 or newer**: [Download it here](https://www.python.org/downloads/) if you don't have it. During installation, make sure to check the box that says **"Add Python to PATH"**.

## 2. Installation & Launch

1. **Download** the Synapse VS folder to your computer.
2. Find the file named `synapse.bat` (it might just look like `synapse`) and **double-click it**.

**That's it!** The first time you run it, SVS will ask you to choose an installation mode:

- **[1] Minimal (Online Hot-Loading)**: Installs only core dependencies. Extra libraries are downloaded on-demand when you use them. Best for fast setup.
- **[2] Full (Offline Capable)**: Installs **all** supported libraries and browsers immediately. Best for offline use or complete feature processing.

After selection, it will set up the virtual environment and launch the Architect window.

## 3. Basic Troubleshooting

- **Script closes immediately?** Try right-clicking the folder background, selecting "Open in Terminal", and typing `./synapse.bat` to see what went wrong.
- **Missing Python?** If nothing happens, you likely need to install Python from the link above.

## 4. Optional Dependencies (Hot Packages)

 If you chose the **Minimal** installation, Synapse VS ships with only core dependencies. Everything else is installed **on-demand**.

- **How it works**: The first time you use a node that needs an extra library (like `opencv-python` or `flask`), a dialog will pop up asking if you'd like to install it.
- **Click Yes**: SVS will download and install it automatically.
- **Click No**: The node will gracefully skip that feature.

 > **Note**: If you chose the **Full** installation, all these "Hot Packages" are pre-installed, so you won't see these prompts unless you add custom nodes with new requirements.

## Next Steps

- Now that you're set up, check out the [UI Usage Guide](file:///f:/My%20Programs/Synapse%20VS/docs/UI_Usage.md) to learn how to navigate the Architect interface.

---
[Return to README](file:///f:/My%20Programs/Synapse%20VS/README.md)

- See what the nodes do in the [Node Reference](file:///f:/My%20Programs/Synapse%20VS/docs/NodeList.md).
- Advanced tricks and example graphs in the [Power User Guide](file:///f:/My%20Programs/Synapse%20VS/docs/PowerUser.md).
- Developers can check the [Technical Guide](file:///f:/My%20Programs/Synapse%20VS/docs/developer.md).
