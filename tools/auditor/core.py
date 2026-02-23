import os
import sys
import time
import json
import inspect
import multiprocessing

try:
    import msvcrt
except ImportError:
    msvcrt = None

from synapse.nodes.registry import NodeRegistry
from synapse.utils.cleanup import CleanupManager
from synapse.core.types import DataType

from .utils import Colors, DummyBridge, requires_provider
from .static_checks import run_pre_flight_check
from .sandbox import run_sandbox

class NodeAuditor:
    def __init__(self, target_version=None, target_exact=None, log_file="bad_node.log", from_start=False, target_node=None, show_list=False, view_mode=False):
        self.target_version = target_version
        self.target_exact = target_exact
        self.log_file = log_file
        self.from_start = from_start
        self.target_node = target_node
        self.show_list = show_list
        self.view_mode = view_mode
        self.state_file = "audit_state.json"
        self.error_file = "audit_errors.json"
        
        # OS Mode = One Shot Mode
        # Only True if user provided a specific -n --node AND it's not a list command
        self.os_mode = bool(self.target_node) and not self.show_list
        
        self.state = {
            "passed": [],
            "failed": {},
            "skipped": [],
            "last_used_errors": []
        }
        
        self.error_history = {}
        self.last_used_errors = [] # In-memory cache for speed, synced with state
        
        self.node_queue = []
        self.current_idx = 0
        
        CleanupManager.cleanup_all = lambda: None
        
        if not self.os_mode:
            self._load_state()
            
        self._load_registry()

        # [REFINEMENT] Set initial start point to first pending node if not in special modes
        if not self.os_mode and not self.view_mode and not self.show_list:
            for i, (nid, _) in enumerate(self.node_queue):
                if nid not in self.state["passed"] and nid not in self.state["failed"]:
                    self.current_idx = i
                    break

    def _load_state(self):
        if self.from_start and os.path.exists(self.state_file):
            print(f"{Colors.YELLOW}Warning: Wiping audit_state.json via --from_start{Colors.RESET}")
            os.remove(self.state_file)
            
        if os.path.exists(self.state_file):
            with open(self.state_file, 'r') as f:
                data = json.load(f)
                if isinstance(data.get("failed"), list):
                    mig_failed = {}
                    for item in data.get("failed", []):
                        mig_failed[item] = []
                    data["failed"] = mig_failed
                self.state.update(data)
                
        if os.path.exists(self.error_file):
            with open(self.error_file, 'r') as f:
                self.error_history = json.load(f)
                
        # Sync in-memory cache
        self.last_used_errors = self.state.get("last_used_errors", [])
                
    def _save_state(self):
        if self.os_mode: return # Do not dirty state in One-Shot Mode
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f, indent=4)
            
    def _save_errors(self):
        if self.os_mode: return
        with open(self.error_file, 'w') as f:
            json.dump(self.error_history, f, indent=4)

    def _log_failure(self, namespaced_id, reason):
        print(f"{Colors.RED}[FAIL] {namespaced_id}: {reason}{Colors.RESET}")
        if self.os_mode: return # Do not log to files in One-Shot
        
        if not isinstance(self.state.get("failed"), dict):
            self.state["failed"] = {}
            
        if namespaced_id not in self.state["failed"]:
            self.state["failed"][namespaced_id] = []
            
        if reason not in self.state["failed"][namespaced_id]:
            self.state["failed"][namespaced_id].append(reason)
            
        if namespaced_id in self.state["passed"]:
            self.state["passed"].remove(namespaced_id)
        if namespaced_id in self.state["skipped"]:
            self.state["skipped"].remove(namespaced_id)
            
        self._save_state()
        self._rewrite_log_file()

    def _rewrite_log_file(self):
        if self.os_mode: return
        try:
            with open(self.log_file, 'w', encoding="utf-8") as f:
                failed = self.state.get("failed", {})
                if isinstance(failed, dict):
                    for nid, reasons in failed.items():
                        for r in reasons:
                            f.write(f"[{nid}] {r}\n")
        except: pass

    def _handle_failure(self, namespaced_id):
        history = self.error_history
        
        if not isinstance(self.state.get("failed"), dict):
            self.state["failed"] = {}
            
        reasons = self.state["failed"].get(namespaced_id, []).copy()
        added_new = False
        
        while True:
            # Full listing of historical errors sorted by count
            all_history = sorted(history.items(), key=lambda x: x[1], reverse=True)
            
            # Unified mapping: reasons [1...N] then last_used then history [N+1...M]
            last_used_overlap = [err for err in self.last_used_errors if err not in reasons]
            other_history = [err for err, count in all_history if err not in reasons and err not in self.last_used_errors]
            
            unified_list = reasons + last_used_overlap + other_history
            
            print(f"\n{Colors.RED}--- Enter reason for failure [{namespaced_id}] ---{Colors.RESET}")
            
            if reasons:
                print(f"{Colors.RED}Current Failures (1-{len(reasons)}):{Colors.RESET}")
                for i, r in enumerate(reasons):
                    print(f"  {i+1}. {r}")
                    
            if all_history:
                # We show Top 10 by default but indices allow selecting any
                display_count = 10
                print(f"\n{Colors.YELLOW}Recent/Common Errors (Starting at {len(reasons)+1}):{Colors.RESET}")
                
                # Show only top 10 for brevity, but indices apply to the full unified_list
                for i, err in enumerate(unified_list[len(reasons):]):
                    if i >= display_count: break
                    
                    real_idx = len(reasons) + i
                    prefix = "*" if err in self.last_used_errors else " "
                    hl = Colors.CYAN if err in self.last_used_errors else ""
                    res = Colors.RESET if err in self.last_used_errors else ""
                    count = history.get(err, 0)
                    print(f"  {prefix} {real_idx+1}. {hl}{err} (used {count} times){res}")
                    
            print(f"{Colors.GRAY}Enter reason, 'q' to finish, 'd #' to delete, 's *' to search, 'e' [page] for full list, 'dl #' to delete from main.{Colors.RESET}")
            val = input(f"{Colors.RED}> {Colors.RESET}").strip()
            
            if val.lower() == 'q':
                break
                
            if val.lower().startswith('s '):
                search_term = val[2:].strip().lower()
                if not search_term:
                    print(f"{Colors.YELLOW}Please provide a search term (e.g., 's connection').{Colors.RESET}")
                    continue
                
                print(f"\n{Colors.CYAN}--- SEARCH RESULTS FOR '{search_term}' ---{Colors.RESET}")
                matches = 0
                for i, err in enumerate(unified_list):
                    if search_term in err.lower():
                        matches += 1
                        count = history.get(err, 0)
                        if i < len(reasons):
                            hl = Colors.RED
                        elif err in self.last_used_errors:
                            hl = Colors.CYAN
                        else:
                            hl = Colors.YELLOW
                        print(f"  {hl}{i+1}. {err} (used {count} times){Colors.RESET}")
                
                if matches == 0:
                    print(f"  {Colors.GRAY}No matches found.{Colors.RESET}")
                print("=" * 60)
                continue
                
            if val.lower() == 'e' or val.lower().startswith('e '):
                # Pagination logic
                page_num = 1
                if val.lower().startswith('e '):
                    try: page_num = int(val[2:].strip())
                    except: page_num = 1
                
                items_per_page = 20
                total_pages = (len(unified_list) + items_per_page - 1) // items_per_page
                page_num = max(1, min(page_num, total_pages)) if total_pages > 0 else 1
                
                start_idx = (page_num - 1) * items_per_page
                end_idx = start_idx + items_per_page
                
                print(f"\n{Colors.CYAN}--- ALL SAVED ERRORS (Page {page_num}/{total_pages}) ---{Colors.RESET}")
                for i, err in enumerate(unified_list[start_idx:end_idx]):
                    real_idx = start_idx + i
                    count = history.get(err, 0)
                    if real_idx < len(reasons):
                        hl = Colors.RED
                    elif err in self.last_used_errors:
                        hl = Colors.CYAN
                    else:
                        hl = Colors.YELLOW
                        
                    print(f"  {hl}{real_idx+1}. {err} (used {count} times){Colors.RESET}")
                
                if total_pages > 1:
                    print(f"\n{Colors.GRAY}Type 'e [number]' to see another page (1-{total_pages}){Colors.RESET}")
                print("=" * 60)
                continue
                
            if val.lower().startswith('dl '):
                del_str = val[3:].strip().lower()
                if del_str.isdigit():
                    idx = int(del_str) - 1
                    if 0 <= idx < len(unified_list):
                        del_err = unified_list[idx]
                        if del_err in history:
                            del history[del_err]
                            self.error_history = history
                            self._save_errors()
                            print(f"{Colors.YELLOW}Removed error '{del_err}' from main list.{Colors.RESET}")
                            if del_err in reasons:
                                reasons.remove(del_err)
                                added_new = True
                        else:
                            print(f"{Colors.YELLOW}Cannot delete '{del_err}' from main list (it might only be on this node).{Colors.RESET}")
                    else:
                        print(f"{Colors.YELLOW}Invalid index for error list.{Colors.RESET}")
                else:
                    match_reason = None
                    for err in history.keys():
                        if err.lower() == del_str:
                            match_reason = err
                            break
                    if match_reason:
                        del history[match_reason]
                        self.error_history = history
                        self._save_errors()
                        print(f"{Colors.YELLOW}Removed error '{match_reason}' from main list.{Colors.RESET}")
                    else:
                        print(f"{Colors.YELLOW}Error '{val[3:].strip()}' not found in main error list.{Colors.RESET}")
                continue
                
            if val.lower().startswith('d '):
                del_str = val[2:].strip().lower()
                if del_str.isdigit():
                    idx = int(del_str) - 1
                    if 0 <= idx < len(reasons):
                        del_err = reasons[idx]
                        reasons.pop(idx)
                        history[del_err] = max(0, history.get(del_err, 0) - 1)
                        if history[del_err] == 0:
                            del history[del_err]
                        self.error_history = history
                        self._save_errors()
                        print(f"{Colors.YELLOW}Removed problem: {del_err}{Colors.RESET}")
                        added_new = True
                        continue
                    else:
                        print(f"{Colors.YELLOW}Invalid index to delete (must be 1-{len(reasons)}).{Colors.RESET}")
                        continue
                
                match_reason = None
                for r in reasons:
                    if r.lower() == del_str:
                        match_reason = r
                        break
                        
                if match_reason:
                    reasons.remove(match_reason)
                    history[match_reason] = max(0, history.get(match_reason, 0) - 1)
                    if history[match_reason] == 0:
                        del history[match_reason]
                    self.error_history = history
                    self._save_errors()
                    print(f"{Colors.YELLOW}Removed problem: {match_reason}{Colors.RESET}")
                    added_new = True
                else:
                    print(f"{Colors.YELLOW}Problem '{val[2:].strip()}' not found in current session list to delete.{Colors.RESET}")
                continue
                
            if val.isdigit():
                idx = int(val) - 1
                if 0 <= idx < len(unified_list):
                    reason = unified_list[idx]
                else:
                    print(f"{Colors.YELLOW}Invalid index. Enter a valid number or type the reason.{Colors.RESET}")
                    continue
            elif val:
                reason = val
            else:
                continue
                
            if reason not in reasons:
                reasons.append(reason)
                history[reason] = history.get(reason, 0) + 1
                self.error_history = history
                self._save_errors()
                print(f"{Colors.GREEN}Added problem: {reason}{Colors.RESET}")
                added_new = True
            else:
                print(f"{Colors.YELLOW}Problem already added to this node.{Colors.RESET}")
            
        if reasons or added_new:
            self.state["failed"][namespaced_id] = reasons
            if reasons:
                self.last_used_errors = reasons.copy()
                self.state["last_used_errors"] = self.last_used_errors
                
            if not reasons:
                if namespaced_id in self.state["failed"]:
                    del self.state["failed"][namespaced_id]
                
            if namespaced_id in self.state["passed"]:
                self.state["passed"].remove(namespaced_id)
            if namespaced_id in self.state["skipped"]: 
                self.state["skipped"].remove(namespaced_id)
                
            self._save_state()
            self._rewrite_log_file()
            return True if reasons else False
        else:
            print(f"{Colors.YELLOW}Cancelled adding failure reasons.{Colors.RESET}")
            return False

    def _load_registry(self):
        nodes_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'synapse', 'nodes'))
        for root, _, files in os.walk(nodes_dir):
            for f in files:
                 if f.endswith('.py') and not f.startswith('__'):
                     rel_path = os.path.relpath(os.path.join(root, f), os.path.join(nodes_dir, "..", ".."))
                     mod_name = rel_path.replace(os.sep, '.')[:-3]
                     try: __import__(mod_name)
                     except Exception: pass

        processed = set()
        for namespaced_id, node_cls in sorted(NodeRegistry._nodes.items()):
            if node_cls in processed: continue
            processed.add(node_cls)
            
            node_ver = getattr(node_cls, "version", "1.0.0")
            
            if self.target_node:
                if self.target_node.lower() not in namespaced_id.lower():
                    continue
                    
            if self.target_exact and node_ver != self.target_exact:
                continue
                
            if self.target_version:
                if node_ver < self.target_version:
                    continue
            
            # [REFINEMENT] Do not skip passed/failed here; we include all matching nodes in queue 
            # so the user can backtrack 'b' past their start point.
                       
            if self.view_mode:
                if namespaced_id not in self.state["failed"] and namespaced_id not in self.state["skipped"]:
                    continue

            self.node_queue.append((namespaced_id, node_cls))

    def _render_ascii(self, namespaced_id, node_cls):
        bridge = DummyBridge()
        node = node_cls("ascii", namespaced_id.split('.')[-1], bridge)
        
        if not self.os_mode:
            os.system('cls' if os.name == 'nt' else 'clear')
            
        ver = getattr(node_cls, "version", "1.0.0")
        
        cat_parts = namespaced_id.split('.')
        category = cat_parts[0] if len(cat_parts) > 1 else "General"
        
        print(f"\n{Colors.BOLD}{Colors.YELLOW}[{namespaced_id}] - v{ver}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.CYAN}Category: {category}{Colors.RESET}")
        print("=" * 60)
        
        doc = inspect.getdoc(node_cls)
        if doc: print(f"{Colors.GRAY}{doc}{Colors.RESET}\n")
        else: print(f"{Colors.RED}[NO DOCSTRING FOUND]{Colors.RESET}\n")

        p_type = getattr(node, "provider_type", None)
        if p_type:
             print(f"{Colors.BOLD}{Colors.MAGENTA}>>> [PROVIDER TYPE: {p_type}] <<<{Colors.RESET}\n")
        
        provider_type_req = None
        if hasattr(node, "required_providers") and node.required_providers:
             provider_type_req = ", ".join(node.required_providers)
        else:
            for key, typ in node.input_schema.items():
                 k_l = key.lower()
                 if "provider" in k_l or "connection" in k_l or "session" in k_l:
                      provider_type_req = str(typ).split('.')[-1]
                      break
        
        if provider_type_req:
             print(f"{Colors.BOLD}{Colors.YELLOW}>>> [REQUIRES PROVIDER: {provider_type_req}] <<<{Colors.RESET}\n")

        if getattr(node, "allow_dynamic_inputs", False) or getattr(node, "allow_dynamic_outputs", False):
            dyn_msg = []
            if getattr(node, "allow_dynamic_inputs", False): dyn_msg.append("INPUTS")
            if getattr(node, "allow_dynamic_outputs", False): dyn_msg.append("OUTPUTS")
            
            msg = " + ".join(dyn_msg)
            print(f"{Colors.BOLD}{Colors.BG_YELLOW}{Colors.BLACK}  DYNAMIC {msg} SUPPORTED  {Colors.RESET}")
            
            if "INPUTS" in dyn_msg:
                 # Check if it supports dynamic Flow specifically
                 if getattr(node, "allow_dynamic_inputs", False):
                      # We check the actual logic in the node or registry if we can, 
                      # but for now a general warning that this node supports dynamic flow expansion
                      print(f"{Colors.YELLOW}NOTE: This node supports adding dynamic Input Flows.{Colors.RESET}")
            print()

        print(f"{'INPUTS':<35} | {'OUTPUTS':>35}")
        print("-" * 75)
        
        ins = list(node.input_schema.items())
        outs = list(node.output_schema.items())
        max_len = max(len(ins), len(outs))
        
        for i in range(max_len):
            if i < len(ins):
                name, typ = ins[i]
                c = Colors.GREEN if typ == DataType.FLOW else Colors.CYAN
                t_str = str(typ).split('.')[-1]
                raw_in = f"o ({t_str}) {name}"
                in_str = f"{c}{raw_in:<35}{Colors.RESET}"
            else:
                in_str = " " * 35
            
            if i < len(outs):
                name, typ = outs[i]
                c = Colors.GREEN if typ == DataType.FLOW else Colors.CYAN
                t_str = str(typ).split('.')[-1]
                raw_out = f"{name} ({t_str}) o"
                out_str = f"{c}{raw_out:>35}{Colors.RESET}"
            else:
                out_str = " " * 35
                
            print(f"{in_str} | {out_str}")
            
        print("\n" + "=" * 60)
        print("PROPERTIES & FALLBACKS")
        print("-" * 60)
        for p, default_val in node.properties.items():
            ptype = node.input_schema.get(p, "Untyped")
            print(f"  - {Colors.BOLD}{p}{Colors.RESET} [{ptype}]: {default_val}")
        print("=" * 60)
        
        # Display current reasons if in view mode and has failed OR if they just added fail reasons
        if namespaced_id in self.state.get("failed", {}):
            reasons = self.state["failed"].get(namespaced_id, [])
            if reasons:
                print(f"\n{Colors.RED}--- CURRENT FAILURES ---{Colors.RESET}")
                for r in reasons:
                    print(f"  {Colors.YELLOW}- {r}{Colors.RESET}")
                print("=" * 60)
            elif self.view_mode:
                print(f"\n{Colors.RED}--- CURRENT FAILURES ---{Colors.RESET}")
                print(f"  {Colors.GRAY}(No detailed reasons found){Colors.RESET}")
                print("=" * 60)

    def _prompt(self, namespaced_id, node_cls):
        while True:
            print(f"\n{Colors.BOLD}Action [p=Pass, f=Fail, t=Test, s=Skip, b=Back, o=Open Code, q=Quit]: {Colors.RESET}", end="", flush=True)
            
            if msvcrt and sys.stdin.isatty():
                try:
                    char = msvcrt.getch()
                    if char in [b'\x00', b'\xe0']:
                        msvcrt.getch() # Drain special key sequence
                        continue
                    key = char.decode('utf-8').lower()
                    print(key)
                except UnicodeDecodeError:
                    continue
            else:
                try: key = input().strip().lower()
                except EOFError:
                    time.sleep(1)
                    continue

            if key == 'p' or key == 'y':
                if namespaced_id not in self.state["passed"]: self.state["passed"].append(namespaced_id)
                if namespaced_id in self.state["skipped"]: self.state["skipped"].remove(namespaced_id)
                if namespaced_id in self.state["failed"]: 
                    del self.state["failed"][namespaced_id]
                    self._rewrite_log_file()
                self._save_state()
                return 1
            elif key == 'f' or key == 'n':
                self._handle_failure(namespaced_id)
                return 0
            elif key == 's':
                 if namespaced_id not in self.state["passed"] and namespaced_id not in self.state["failed"]:
                      if namespaced_id not in self.state["skipped"]:
                           self.state["skipped"].append(namespaced_id)
                           self._save_state()
                 return 1
            elif key == 'b': return -1
            elif key == 't':
                 bridge = DummyBridge()
                 try:
                     node_inst = node_cls("test", namespaced_id.split('.')[-1], bridge)
                     is_prov = hasattr(node_inst, 'cleanup_provider_context')
                     req_prov = requires_provider(node_inst)
                 except: 
                     is_prov, req_prov = False, False
                     
                 if not is_prov and req_prov:
                     print(f"\n{Colors.YELLOW}This node requires a Provider. Skipping sandbox. Test it via its Provider node.{Colors.RESET}")
                 else:
                     run_sandbox(namespaced_id, node_cls, is_os_mode=False, render_cb=self._render_ascii)
                     
                 self._render_ascii(namespaced_id, node_cls)
            elif key == 'o':
                 try:
                     file_path = inspect.getfile(node_cls)
                     os.startfile(file_path) if os.name == 'nt' else os.system(f"open {file_path}")
                     print(f"Opened {file_path}")
                 except Exception as e:
                     print(f"Failed to open source: {e}")
            elif key == 'q':
                 return -2
            else: print("Invalid command.")

    def run(self):
         if self.show_list:
             self._display_node_list()
             return
             
         total = len(self.node_queue)
         if total == 0:
             print(f"{Colors.GREEN}All nodes checked! No unchecked nodes in queue.{Colors.RESET}")
             return
             
         if self.os_mode:
              print(f"\n{Colors.YELLOW}--- ONE SHOT MODE ({total} Targets) ---{Colors.RESET}")
              for namespaced_id, node_cls in self.node_queue:
                  if not run_pre_flight_check(namespaced_id, node_cls, self._log_failure):
                      continue
                  self._render_ascii(namespaced_id, node_cls)
                  
                  bridge = DummyBridge()
                  try:
                      node_inst = node_cls("test", namespaced_id.split('.')[-1], bridge)
                      if not hasattr(node_inst, 'cleanup_provider_context') and requires_provider(node_inst):
                           print(f"\n{Colors.YELLOW}This node requires a Provider. Cannot run in One-Shot OS mode dynamically.{Colors.RESET}")
                           continue
                  except: pass
                  
                  run_sandbox(namespaced_id, node_cls, is_os_mode=True, render_cb=self._render_ascii)
              return
             
         print(f"Starting audit. {total} nodes in queue...")
         time.sleep(1)
         
         while 0 <= self.current_idx < total:
              namespaced_id, node_cls = self.node_queue[self.current_idx]
              
              if not run_pre_flight_check(namespaced_id, node_cls, self._log_failure):
                  print(f"{Colors.YELLOW}Node [{namespaced_id}] failed static pre-flight. Skipping to next.{Colors.RESET}")
                  time.sleep(0.5)
                  self.current_idx += 1
                  continue
                  
              self._render_ascii(namespaced_id, node_cls)
              print(f"\n{Colors.GRAY}Progress: {self.current_idx + 1} / {total}{Colors.RESET}")
              
              move = self._prompt(namespaced_id, node_cls)
              if move == -2:
                  print(f"\n{Colors.YELLOW}Auditing saved. Exiting...{Colors.RESET}")
                  self._save_state()
                  return
                  
              self.current_idx += move
              
              if move == 0:
                  # Force clear screen explicitly here so it looks like it did loop
                  if not self.os_mode:
                      os.system('cls' if os.name == 'nt' else 'clear')

         print(f"\n{Colors.GREEN}End of queue reached. Run tool again if revisions were skipped.{Colors.RESET}")

    def _display_node_list(self):
         all_nodes = sorted(NodeRegistry._nodes.items())
         total = len(all_nodes)
         if total == 0:
             print("No nodes registered.")
             return
             
         print(f"{Colors.CYAN}--- SYNAPSE NODE LIBRARY ({total} Nodes) ---{Colors.RESET}")
         chunk_size = 15
         for i in range(0, total, chunk_size):
             chunk = all_nodes[i : i + chunk_size]
             for nid, n_cls in chunk:
                 parts = nid.split('.')
                 cat = parts[0]
                 name = parts[-1]
                 print(f"{Colors.YELLOW}{name:<30}{Colors.RESET} | {Colors.GRAY}{cat}{Colors.RESET}")
                 
             if i + chunk_size < total:
                 try:
                     print(f"\n[{i + 1} to {i + len(chunk)} of {total}]")
                     if msvcrt and sys.stdin.isatty():
                         print(f"{Colors.BOLD}Press any key to show next 15... (or 'q' to quit){Colors.RESET}", end="", flush=True)
                         key = msvcrt.getch().decode('utf-8').lower()
                         print()
                         if key == 'q': break
                     else:
                         val = input(f"{Colors.BOLD}Press Enter to show next 15... (or 'q' to quit) {Colors.RESET}").strip().lower()
                         if val == 'q': break
                 except EOFError: break
             else: print(f"\n{Colors.GREEN}End of catalog.{Colors.RESET}")
