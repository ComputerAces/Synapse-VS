from playwright.sync_api import sync_playwright
import sys

def test():
    with sync_playwright() as p:
        try:
            print("Attempting launch with devtools...")
            # For standard launch
            browser = p.chromium.launch(devtools=True)
            print("SUCCESS: Standard launch supports devtools")
            browser.close()
        except TypeError as e:
            print(f"TYPE ERROR (Standard): {e}")
        except Exception as e:
            print(f"OTHER ERROR (Standard): {e}")

        try:
            print("Attempting persistent context with devtools...")
            # For persistent context
            context = p.chromium.launch_persistent_context("temp_profile", devtools=True)
            print("SUCCESS: Persistent context supports devtools")
            context.close()
        except TypeError as e:
            print(f"TYPE ERROR (Persistent): {e}")
        except Exception as e:
            print(f"OTHER ERROR (Persistent): {e}")

if __name__ == "__main__":
    test()
