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

    def find(self, target_string: str, payload: Any = None) -> Any:
        try:
            element = None
            
            # Robust Native Selection: Try Playwright's engine (CSS/XPath) with prefix + frame fallbacks
            selectors = [target_string]
            if target_string.startswith('/') or target_string.startswith('//'):
                if not target_string.startswith('xpath='):
                    selectors.insert(0, f"xpath={target_string}") # Ensure explicit XPath prefix for absolute paths
            
            all_found = []
            
            # 1. Search Main Page
            for sel in selectors:
                try:
                    found = self.page.query_selector_all(sel)
                    if found: all_found.extend(found)
                except: pass
            
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
                
            # Fallback path: Custom syntax resolution
            if not element:
                tokens = self._parse_syntax(target_string)
                element = self._resolve_waterfall(tokens)
            
            if not element:
                logger.warning(f"MagicFind failed to resolve: {target_string}")
                return None if payload is not None else {"path": None, "data": None}

            # If payload is provided, act on it
            if payload is not None:
                # Detect surgical intent (absolute XPath)
                surgical = target_string.startswith('/') or target_string.startswith('//') or target_string.startswith('xpath=/') or target_string.startswith('xpath=//')
                return self._act_contextual(element, payload, surgical=surgical)
            
            # If no payload, return resolve metadata
            return self._resolve_metadata(element)
            
        except Exception as e:
            logger.error(f"MagicFind Error on '{target_string}': {e}")
            return None

    def _parse_syntax(self, target: str) -> List[Dict[str, Any]]:
        """Parses 'parent.child[n]' into tokens."""
        tokens = []
        parts = target.split('.')
        for part in parts:
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
                    if (n.id) {
                        sel += '#' + n.id;
                    }
                    let sib = n, nth = 1;
                    while (sib = sib.previousElementSibling) {
                        if (sib.nodeName.toLowerCase() === sel.split('#')[0]) nth++;
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
