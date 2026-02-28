
from playwright.sync_api import sync_playwright

def test_xpath():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_content("<html><body><div><button><span>Target</span></button></div></body></html>")
        
        xpath = "/html/body/div/button/span"
        
        print(f"Testing XPath: {xpath}")
        
        # Test wait_for_selector
        try:
            page.wait_for_selector(f"xpath={xpath}", timeout=1000)
            print("wait_for_selector(xpath=...) SUCCEEDED")
        except Exception as e:
            print(f"wait_for_selector(xpath=...) FAILED: {e}")
            
        try:
            page.wait_for_selector(xpath, timeout=1000)
            print("wait_for_selector(raw) SUCCEEDED")
        except Exception as e:
            print(f"wait_for_selector(raw) FAILED: {e}")
            
        # Test query_selector_all
        try:
            res = page.query_selector_all(f"xpath={xpath}")
            print(f"query_selector_all(xpath=...) found {len(res)} elements")
        except Exception as e:
            print(f"query_selector_all(xpath=...) FAILED: {e}")
            
        try:
            res = page.query_selector_all(xpath)
            print(f"query_selector_all(raw) found {len(res)} elements")
        except Exception as e:
            print(f"query_selector_all(raw) FAILED: {e}")
            
        browser.close()

if __name__ == "__main__":
    test_xpath()
