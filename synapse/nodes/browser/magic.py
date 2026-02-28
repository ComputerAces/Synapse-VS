import re
import logging
from typing import Any, Optional, Dict, List, Union
from playwright.sync_api import Page, ElementHandle, Locator

logger = logging.getLogger("MagicFinder")

class MagicFinder:
    """
    Context-aware DOM resolution engine for SVS.
    Handles dot-notation, structural piercing, and intent inference.
    """
    def __init__(self, page: Page):
        self.page = page

    def wait_for(self, target_string: str, state: str = "visible", timeout: int = 30000) -> bool:
        """
        Pauses until the target element matches the state.
        Supports standard selectors and Magic targets.
        """
        try:
            # 1. Standard Selector Optimization (Fast path)
            sel = target_string
            if sel.startswith('/') or sel.startswith('//'):
                sel = f"xpath={sel}" if not sel.startswith('xpath=') else sel
            
            try:
                # Try Playwright's native wait first
                self.page.wait_for_selector(sel, state=state, timeout=min(timeout, 2000))
                return True
            except:
                pass # Fallback to polling for Magic targets or frame-piercing

            # 2. Polling Fallback (Support for frames and complex intents)
            import time
            start = time.time()
            while (time.time() - start) * 1000 < timeout:
                resolved = self.find(target_string)
                
                # Metadata check for visibility/existence
                if resolved and isinstance(resolved, dict):
                    is_present = resolved.get("path") is not None
                    is_visible = resolved.get("visible", False)
                    
                    if state == "visible" and is_visible: return True
                    if state == "attached" and is_present: return True
                    if state == "hidden" and not is_visible: return True
                    if state == "detached" and not is_present: return True
                
                time.sleep(0.5)
            
            return False
        except Exception as e:
            logger.error(f"Wait failed for '{target_string}': {e}")
            return False

    def find(self, target_string: str, payload: Any = None) -> Any:
        try:
            element = None
            
            # Robust Native Selection: Try Playwright's engine (CSS/XPath) with prefix + frame fallbacks
            selectors = [target_string]
            if target_string.startswith('/') or target_string.startswith('//'):
                # Ensure it has the xpath= prefix for Playwright
                if not target_string.startswith('xpath='):
                    selectors.insert(0, f"xpath={target_string}")
            
            all_found = []
            
            # [RETRY LOOP] If payload is provided (Intent: Action), we retry briefly 
            # to accommodate DOM shifts or micro-latencies after a successful Wait.
            import time
            attempts = 3 if payload is not None else 1
            
            for attempt in range(attempts):
                all_found = []
                # 1. Search Main Page
                for sel in selectors:
                    try:
                        # [FIX] query_selector_all fails on raw XPaths without /xpath= prefix
                        # if it starts with / or // but isn't prefixed, we skip it here as it was already handled or prefixed above
                        if (sel.startswith('/') or sel.startswith('//')) and not (sel.startswith('xpath=') or sel.startswith('css=')):
                            continue

                        found = self.page.query_selector_all(sel)
                        if found: all_found.extend(found)
                    except Exception as e:
                        import threading
                        curr_thread = threading.current_thread().name
                        logger.error(f"MagicFind Query Failed (Thread: {curr_thread}) for '{sel}': {e}")
                
                # 2. Search Frames if still searching
                if not all_found:
                    for frame in self.page.frames:
                        if frame == self.page.main_frame: continue
                        for sel in selectors:
                            try:
                                found = frame.query_selector_all(sel)
                                if found: all_found.extend(found)
                            except: pass
                
                if all_found:
                    # Priority: Real (visible) vs Exists
                    valid_elements = [el for el in all_found if self._is_real(el)]
                    element = valid_elements[0] if valid_elements else all_found[0]
                    break
                
                if attempt < attempts - 1:
                    time.sleep(0.2)
                
            # Fallback path: Custom syntax resolution
            if not element:
                tokens = self._parse_syntax(target_string)
                element = self._resolve_waterfall(tokens)
            
            if not element:
                # [DIAGNOSTICS] Log more details on what was tried
                logger.warning(f"MagicFind failed to resolve: {target_string} (Selectors tried: {selectors})")
                
                # If it's a deep XPath, maybe log if any part of it was found?
                if '/' in target_string:
                    parts = [p for p in target_string.split('/') if p]
                    if len(parts) > 1:
                        # Try to find the parent to see where it broke
                        parent_xpath = '/' + '/'.join(parts[:-1])
                        try:
                            parent = self.page.query_selector(f"xpath={parent_xpath}")
                            if parent:
                                logger.info(f"Diagnostic: Parent element {parent_xpath} WAS found, but child {parts[-1]} was not.")
                            else:
                                logger.info(f"Diagnostic: Parent element {parent_xpath} was ALSO not found.")
                        except: pass

                return None if payload is not None else {"path": None, "data": None}

            # If payload is provided, act on it
            if payload is not None:
                # Detect surgical intent (absolute XPath)
                surgical = target_string.startswith('/') or target_string.startswith('//') or target_string.startswith('xpath=/') or target_string.startswith('xpath=//')
                return self._act_contextual(element, payload, surgical=surgical)
            
            # If no payload, return resolve metadata
            return self._resolve_metadata(element)
            
        except Exception as e:
            import threading
            logger.error(f"MagicFind Error on '{target_string}' (Thread: {threading.current_thread().name}): {e}")
            return None

    def _parse_syntax(self, target: str) -> List[Dict[str, Any]]:
        """Parses hierarchical paths (e.g., 'parent.child[n]', 'parent/child', 'parent,child')."""
        tokens = []
        # [FIX] Remove any leading dots/slashes/commas
        clean_target = target.lstrip('./,')
        # [REFINED] Support dot, slash, and comma as interchangeable separators
        parts = re.split(r'[./,]', clean_target)
        for part in parts:
            if not part: continue # Skip empty parts from double separators like //
            match = re.match(r"([\*\w\-]+)(?:\[(\d+)\])?", part)
            if match:
                name = match.group(1)
                index = int(match.group(2)) if match.group(2) else 0
                tokens.append({"name": name, "index": index})
        return tokens

    def _resolve_waterfall(self, tokens: List[Dict[str, Any]], scope: Union[Page, ElementHandle] = None) -> Optional[ElementHandle]:
        current_scope = scope or self.page
        
        for i, token in enumerate(tokens):
            name = token["name"]
            index = token["index"]
            is_wildcard = name == "*"
            
            # Waterfall strategies
            strategies = [
                lambda s, n: s.query_selector_all(n),                                 # Exact Tag
                lambda s, n: s.query_selector_all(f"#{n}"),                           # ID
                lambda s, n: s.query_selector_all(f"[name='{n}']"),                  # Name
                lambda s, n: s.query_selector_all(f"[placeholder*='{n}']"),          # Placeholder
                lambda s, n: s.query_selector_all(f".{n}"),                           # Class
                lambda s, n: s.query_selector_all(f"[data-testid='{n}']"),            # Data Test ID
                lambda s, n: [el for el in s.query_selector_all("*") if n in (el.inner_text() or "")] # Fuzzy Text
            ]

            matches = []
            if is_wildcard:
                # If wildcard, we just skip to next part if any, or find "all"
                # But usually wildcard is followed by something like *.button
                continue 

            for strategy in strategies:
                try:
                    found = strategy(current_scope, name)
                    valid_matches = [m for m in found if self._is_real(m)]
                    if valid_matches:
                        matches.extend(valid_matches)
                        break # Found at this priority level
                except:
                    continue

            # Check Iframes/Shadow DOM if no matches
            if not matches:
                matches = self._pierce_structural(current_scope, name)

            # [NEW] Attribute Bridge (Graceful skipping for non-DOM JSON metadata keys)
            # If no matches found, but we are inside an ElementHandle scope (not a Page),
            # we assume this token was an auxiliary metadata key (e.g. .action, .class, .text) 
            # outputted by JSON Search. We keep the current scope and advance to the next token. 
            if not matches and not isinstance(current_scope, Page):
                continue

            if not matches or index >= len(matches):
                return None
            
            current_scope = matches[index]
            
        return current_scope if not isinstance(current_scope, Page) else None

    def _is_real(self, element: ElementHandle) -> bool:
        """Validates visibility and interactivity."""
        try:
            return element.is_visible() and element.is_enabled()
        except:
            return False

    def _pierce_structural(self, scope: Union[Page, ElementHandle], name: str) -> List[ElementHandle]:
        """Scans Shadow DOM and Iframes recursively."""
        matches = []
        
        # 1. Search Frames
        frames = self.page.frames if isinstance(scope, Page) else []
        for frame in frames:
            if frame == self.page.main_frame: continue
            try:
                found = frame.query_selector_all(f"#{name}, [name='{name}'], .{name}, {name}")
                matches.extend([m for m in found if self._is_real(m)])
            except: pass

        # 2. Shadow DOM handling usually requires JS or specific selectors in Playwright
        # But we'll keep it simple for now or implement direct JS lookup if needed.
        return matches

    def _act_contextual(self, element: ElementHandle, payload: Any, surgical: bool = False) -> bool:
        tag = element.evaluate("el => el.tagName.toLowerCase()")
        e_type = element.get_attribute("type") or ""
        e_type = e_type.lower()

        # Deep find for interactive child if needed (Skip if surgical)
        if not surgical and tag not in ["input", "textarea", "select", "button", "a", "form", "div"]:
             child = element.query_selector("input, textarea, select, button, a, form, div")
             if child:
                 element = child
                 tag = element.evaluate("el => el.tagName.toLowerCase()")
                 e_type = (element.get_attribute("type") or "").lower()

        # 1. Write / Input
        if isinstance(payload, str) and tag in ["input", "textarea", "form", "div"]:
            try: element.fill(payload)
            except: pass # Fallback
            return True

        # 2. Dropdown Select
        if isinstance(payload, str) and tag == "select":
            element.select_option(label=payload)
            return True

        # 3. Click / Toggle
        if isinstance(payload, bool) or payload is True:
            if tag == "input" and e_type in ["checkbox", "radio"]:
                element.set_checked(payload if isinstance(payload, bool) else True)
            else:
                try:
                    # Stage 1: Standard Click
                    element.click(timeout=3000)
                except Exception as e:
                    logger.debug(f"Standard click failed, retrying with force: {e}")
                    try:
                        # Stage 2: Force Click (Bypass actionability checks)
                        element.click(force=True, timeout=3000)
                    except Exception as e2:
                        logger.debug(f"Force click failed, retrying with mouse: {e2}")
                        try:
                            # Stage 3: Coordinate Click (Center of bounding box)
                            box = element.bounding_box()
                            if box:
                                self.page.mouse.click(box['x'] + box['width']/2, box['y'] + box['height']/2)
                            else:
                                logger.warning("Could not calculate bounding box for fallback click.")
                        except Exception as e3:
                            logger.error(f"All click strategies failed: {e3}")
            return True

        return False

    def _resolve_metadata(self, element: ElementHandle) -> Dict[str, Any]:
        """Generates resolution JSON with hierarchical path and value."""
        try:
            js_path_script = """
            (el) => {
                let path = [];
                let n = el;
                while (n && n.nodeType === Node.ELEMENT_NODE) {
                    let sel = n.nodeName.toLowerCase();
                    // We remove the ID-based root shortcut to ensure full tag-based paths
                    let sib = n, nth = 1;
                    while (sib = sib.previousElementSibling) {
                        if (sib.nodeName.toLowerCase() === sel) nth++;
                    }
                    if (nth !== 1) sel += "[" + nth + "]";
                    path.unshift(sel);
                    n = n.parentNode;
                }
                return path.join('.');
            }
            """
            path = element.evaluate(js_path_script)
            val = element.evaluate("el => el.value || el.innerText")
            visible = element.is_visible()
            
            return {
                "path": path or "Resolved Element", 
                "data": val,
                "visible": visible
            }
        except Exception as e:
            logger.debug(f"Metadata Resolution failed: {e}")
            return {"path": None, "data": None}
