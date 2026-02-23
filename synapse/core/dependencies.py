
import sys
import subprocess
import importlib
try:
    from PyQt6.QtWidgets import QApplication, QMessageBox, QProgressDialog
    from PyQt6.QtCore import Qt
    HAS_QT = True
except ImportError:
    HAS_QT = False
    QApplication = None
    QMessageBox = None
    QProgressDialog = None
    Qt = None

class DependencyManager:
    """
    Manages dynamic installation of Python packages.
    """
    @staticmethod
    def is_installed(package_name):
        try:
            # Use find_spec to check without actually importing/executing
            spec = importlib.util.find_spec(package_name)
            return spec is not None
        except (ImportError, ValueError, AttributeError):
            return False

    @staticmethod
    def ensure(package_name, import_name=None):
        """
        Checks if a package is installed. If not, prompts user to install.
        Returns True if installed/successfully installed, False otherwise.
        params:
            package_name: pip package name (e.g. 'opencv-python')
            import_name: python module name (e.g. 'cv2'). Defaults to package_name.
        """
        module_target = import_name if import_name else package_name
        
        try:
            importlib.import_module(module_target)
            return True
        except ImportError:
            pass

        # Not found. Prompt user.
        if HAS_QT:
            app = QApplication.instance()
        else:
            app = None

        if not app:
            # Headless: Auto-install or fail? 
            # User said "when we run... we load it".
            print(f"Installing missing dependency: {package_name}...")
            return DependencyManager.install(package_name)

        # GUI Prompt
        reply = QMessageBox.question(
            None, 
            "Missing Dependency",
            f"This feature requires additional package: '{package_name}'.\n\nInstall it now? (This may take a moment)",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            return DependencyManager.install(package_name)
        else:
            return False

    @staticmethod
    def install(package_name):
        """
        Installs a package via pip.
        """
        # Show specific UI for valid GUI context
        if HAS_QT:
            app = QApplication.instance()
        else:
            app = None
            
        progress = None
        if app and HAS_QT:
            progress = QProgressDialog(f"Installing {package_name}...", None, 0, 0)
            progress.setWindowTitle("Installing Dependency")
            progress.setWindowModality(Qt.WindowModality.ApplicationModal)
            progress.setCancelButton(None)
            progress.show()
            QApplication.processEvents()

        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
            
            # [NEW] Persist to requirements.txt
            try:
                import os
                req_path = os.path.join(os.getcwd(), "requirements.txt")
                
                # Check if already in file
                exists = False
                if os.path.exists(req_path):
                    with open(req_path, "r") as f:
                        if package_name in f.read():
                            exists = True
                
                if not exists:
                    with open(req_path, "a") as f:
                        f.write(f"\n{package_name}")
                    print(f"Added {package_name} to requirements.txt for persistence.")
            except Exception as re:
                print(f"Warning: Could not update requirements.txt: {re}")

            # Close progress
            if progress: progress.close()
            
            # Verify import
            importlib.invalidate_caches()
            return True
        except subprocess.CalledProcessError as e:
            if progress: progress.close()
            print(f"Failed to install {package_name}: {e}")
            if app:
                QMessageBox.critical(None, "Install Failed", f"Could not install '{package_name}'.\nCheck console for details.")
            return False
