import zipfile
import pyzipper
import os

plugins_dir = "plugins"
os.makedirs(plugins_dir, exist_ok=True)

# 1. Create a dummy .spy file
spy_content = """
from axonpulse.core.super_node import SuperNode
from axonpulse.core.types import DataType

class ZipTestNode(SuperNode):
    node_label = "Zip Test Node"
    node_category = "Plugins/Testing"
    
    def define_schema(self):
        self.input_schema["Input"] = DataType.STRING
        self.output_schema["Output"] = DataType.STRING
        
    def main(self, Input="Zip Success", **kwargs):
        print(f"[ZipTestNode] Running with Input: {Input}")
        self.set_output("Output", f"PKG_SUCCESS: {Input}")
        return True
"""

# 2. Package into unencrypted zip
unencrypted_zip = os.path.join(plugins_dir, "test_pkg_open.zip")
with zipfile.ZipFile(unencrypted_zip, 'w') as zf:
    zf.writestr("test_node_open.spy", spy_content)
print(f"Created unencrypted package: {unencrypted_zip}")

# 3. Package into encrypted zip (AES-256)
encrypted_zip = os.path.join(plugins_dir, "test_pkg_locked.zip")
with pyzipper.AESZipFile(encrypted_zip, 'w', compression=pyzipper.ZIP_DEFLATED, encryption=pyzipper.ENCRYPTION_AES) as zf:
    zf.setpassword(b"secret123")
    zf.writestr("test_node_locked.spy", spy_content.replace("Zip Test Node", "Zip Locked Node"))
print(f"Created encrypted package: {encrypted_zip}")
