
import sys
import os
import time
import logging

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.curdir))

from playwright.sync_api import sync_playwright
from synapse.nodes.browser.magic import MagicFinder

# Setup logging to see our new diagnostics
logging.basicConfig(level=logging.INFO)

def verify_fix():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # Create a deep DOM structure
        content = """
        <html><body><div id="app"><main><article>
            <div class="container">
                <form>
                    <div class="row">
                        <button type="button">
                            <span>Icon</span>
                            <span class="label">Target Button</span>
                        </button>
                    </div>
                </form>
            </div>
        </article></main></div></body></html>
        """
        page.set_content(content)
        
        finder = MagicFinder(page)
        
        # The exact XPath from the user's log (abbreviated/simulated)
        xpath = "/html/body/div/main/article/div/form/div/button/span[2]"
        
        print(f"\n--- Testing XPath: {xpath} ---")
        
        # Test 1: Wait for element
        print("Testing wait_for...")
        found = finder.wait_for(xpath, timeout=2000)
        print(f"Wait result: {found}")
        
        # Test 2: Find and Read Metadata
        print("\nTesting find (Read mode)...")
        resolved = finder.find(xpath)
        print(f"Resolved Metadata: {resolved}")
        
        # Test 3: Find and Click (Action mode with micro-retry)
        print("\nTesting find (Action mode - Click)...")
        # We'll simulate a click by passing True as payload
        try:
            # We need to mock or ensure the element is actually clickable in this headless environment
            success = finder.find(xpath, payload=True)
            print(f"Click Action Result: {success}")
        except Exception as e:
            print(f"Click Action FAILED: {e}")

        # Test 4: Diagnostic triggering (Non-existent path)
        print("\nTesting diagnostics for failing path...")
        bad_xpath = "/html/body/div/main/article/div/form/div/button/span[99]"
        finder.find(bad_xpath)

        browser.close()

if __name__ == "__main__":
    verify_fix()
