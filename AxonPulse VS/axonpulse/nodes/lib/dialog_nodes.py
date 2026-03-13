import os

import sys

import ctypes

import subprocess

import platform

from axonpulse.core.super_node import SuperNode

from axonpulse.nodes.registry import NodeRegistry

from axonpulse.core.types import DataType, DialogMode

from typing import Any, List, Dict, Optional

from axonpulse.core.types import DataType, TypeCaster

from axonpulse.nodes.decorators import axon_node

'\nMulti-System Selection Dialog Node.\n\nProvides native OS file/folder picker dialogs without heavy dependencies.\n    - Windows: ctypes Win32 API (comdlg32)\n    - macOS:   osascript (AppleScript)\n    - Linux:   zenity subprocess / tkinter fallback\n'

def _pick_file_windows(title, filter_str, mode):
    """Native Windows file dialog using comdlg32 (ctypes)."""
    if mode == 'folder':
        return _pick_folder_windows(title)
    import ctypes.wintypes
    if filter_str and filter_str.strip():
        parts = filter_str.replace(',', ';').strip()
        ofn_filter = f'Selected ({parts})\x00{parts}\x00All Files (*.*)\x00*.*\x00\x00'
    else:
        ofn_filter = 'All Files (*.*)\x00*.*\x00\x00'
    buf = ctypes.create_unicode_buffer(512)

    class OPENFILENAME(ctypes.Structure):
        """Win32 API structure for file dialogs."""
        _fields_ = [('lStructSize', ctypes.c_uint32), ('hwndOwner', ctypes.wintypes.HWND), ('hInstance', ctypes.wintypes.HINSTANCE), ('lpstrFilter', ctypes.c_wchar_p), ('lpstrCustomFilter', ctypes.c_wchar_p), ('nMaxCustFilter', ctypes.c_uint32), ('nFilterIndex', ctypes.c_uint32), ('lpstrFile', ctypes.c_wchar_p), ('nMaxFile', ctypes.c_uint32), ('lpstrFileTitle', ctypes.c_wchar_p), ('nMaxFileTitle', ctypes.c_uint32), ('lpstrInitialDir', ctypes.c_wchar_p), ('lpstrTitle', ctypes.c_wchar_p), ('Flags', ctypes.c_uint32), ('nFileOffset', ctypes.c_uint16), ('nFileExtension', ctypes.c_uint16), ('lpstrDefExt', ctypes.c_wchar_p), ('lCustData', ctypes.c_void_p), ('lpfnHook', ctypes.c_void_p), ('lpTemplateName', ctypes.c_wchar_p)]
    ofn = OPENFILENAME()
    ofn.lStructSize = ctypes.sizeof(OPENFILENAME)
    ofn.hwndOwner = None
    ofn.lpstrFilter = ofn_filter
    ofn.lpstrFile = ctypes.cast(buf, ctypes.c_wchar_p)
    ofn.nMaxFile = 512
    ofn.lpstrTitle = title or 'Select File'
    ofn.Flags = 524288 | 4096 | 4 | 8
    if mode == 'save':
        ofn.Flags = 524288 | 2 | 4 | 8
        result = ctypes.windll.comdlg32.GetSaveFileNameW(ctypes.byref(ofn))
    else:
        result = ctypes.windll.comdlg32.GetOpenFileNameW(ctypes.byref(ofn))
    if result:
        return buf.value
    return None

def _pick_folder_windows(title):
    """Windows folder picker using SHBrowseForFolder."""
    try:
        import ctypes.wintypes
        BIF_RETURNONLYFSDIRS = 1
        BIF_NEWDIALOGSTYLE = 64
        MAX_PATH = 260

        class BROWSEINFO(ctypes.Structure):
            """Win32 API structure for folder browsing."""
            _fields_ = [('hwndOwner', ctypes.wintypes.HWND), ('pidlRoot', ctypes.c_void_p), ('pszDisplayName', ctypes.c_wchar_p), ('lpszTitle', ctypes.c_wchar_p), ('ulFlags', ctypes.c_uint32), ('lpfn', ctypes.c_void_p), ('lParam', ctypes.c_void_p), ('iImage', ctypes.c_int)]
        buf = ctypes.create_unicode_buffer(MAX_PATH)
        bi = BROWSEINFO()
        bi.hwndOwner = None
        bi.pszDisplayName = ctypes.cast(buf, ctypes.c_wchar_p)
        bi.lpszTitle = title or 'Select Folder'
        bi.ulFlags = BIF_RETURNONLYFSDIRS | BIF_NEWDIALOGSTYLE
        shell32 = ctypes.windll.shell32
        ole32 = ctypes.windll.ole32
        ole32.CoInitialize(None)
        pidl = shell32.SHBrowseForFolderW(ctypes.byref(bi))
        if pidl:
            path_buf = ctypes.create_unicode_buffer(MAX_PATH)
            shell32.SHGetPathFromIDListW(pidl, path_buf)
            ole32.CoTaskMemFree(pidl)
            return path_buf.value if path_buf.value else None
        return None
    except Exception:
        return None

def _pick_file_macos(title, filter_str, mode):
    """macOS file dialog using osascript (AppleScript)."""
    if mode == 'folder':
        script = f'''choose folder with prompt "{title or 'Select Folder'}"'''
    elif mode == 'save':
        script = f'''choose file name with prompt "{title or 'Save As'}"'''
    else:
        type_clause = ''
        if filter_str and '*.' in filter_str:
            exts = []
            for part in filter_str.replace(',', ';').split(';'):
                part = part.strip().lstrip('*.')
                if part and part != '*':
                    exts.append(f'"{part}"')
            if exts:
                type_clause = f" of type {{{', '.join(exts)}}}"
        script = f'''choose file with prompt "{title or 'Select File'}"{type_clause}'''
    try:
        result = subprocess.run(['osascript', '-e', script], capture_output=True, text=True, timeout=120)
        if result.returncode == 0 and result.stdout.strip():
            path = result.stdout.strip()
            if path.startswith('alias '):
                path = path[6:]
            path = path.replace(':', '/')
            if not path.startswith('/'):
                path = '/' + path
            return path
    except Exception:
        pass
    return None

def _pick_file_linux(title, filter_str, mode):
    """Linux file dialog using zenity, with tkinter fallback."""
    try:
        cmd = ['zenity']
        if mode == 'folder':
            cmd.append('--file-selection')
            cmd.append('--directory')
        elif mode == 'save':
            cmd.append('--file-selection')
            cmd.append('--save')
            cmd.append('--confirm-overwrite')
        else:
            cmd.append('--file-selection')
        if title:
            cmd.extend(['--title', title])
        if filter_str and mode != 'folder':
            cmd.extend(['--file-filter', filter_str])
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except FileNotFoundError:
        pass
    except Exception:
        pass
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        if mode == 'folder':
            path = filedialog.askdirectory(title=title or 'Select Folder')
        elif mode == 'save':
            path = filedialog.asksaveasfilename(title=title or 'Save As')
        else:
            path = filedialog.askopenfilename(title=title or 'Select File')
        root.destroy()
        return path if path else None
    except Exception:
        pass
    return None

@axon_node(category="UI/Dialogs", version="2.3.0", node_label="File Dialog", outputs=['Cancelled', 'Path'])
def FileDialogNode(Mode: Any = DialogMode.OPEN_FILE, Title: str = '', Filter: str = '', _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Triggers a native operating system dialog for selecting files or folders.
Supports 'Open File', 'Save File', and 'Open Folder' modes across Windows, macOS, and Linux.

This node provides a bridge to the underlying host OS GUI, allowing users to select 
existing files for reading, define new file paths for saving, or choosing entire 
directories for batch operations.

Inputs:
- Flow: Execution trigger (Pulse).
- Mode: The dialog behavior (Open File, Save File, or Open Folder).
- Title: Custom text shown in the dialog window's header.
- Filter: Optional file extension filters (e.g., 'Text Files (*.txt), *.txt; *.csv').

Outputs:
- Flow: Pulse triggered if a valid path was selected.
- Cancelled: Pulse triggered if the user closed the window or clicked 'Cancel'.
- Path: The absolute path to the selected item."""
    title_val = Title if Title is not None else kwargs.get('Title') or _node.properties.get('Title', '')
    filter_val = Filter if Filter is not None else kwargs.get('Filter') or _node.properties.get('Filter', '')
    mode_val = Mode if Mode is not None else kwargs.get('Mode') or _node.properties.get('Mode', 'Open File')
    mode_val = mode_val.lower()
    if 'folder' in mode_val:
        mode = 'folder'
    elif 'save' in mode_val:
        mode = 'save'
    else:
        mode = 'open'
    system = platform.system()
    selected_path = None
    try:
        if system == 'Windows':
            selected_path = _pick_file_windows(title_val, filter_val, mode)
        elif system == 'Darwin':
            selected_path = _pick_file_macos(title_val, filter_val, mode)
        else:
            selected_path = _pick_file_linux(title_val, filter_val, mode)
    except Exception as e:
        _node.logger.error(f'Dialog Error: {e}')
    finally:
        pass
    if selected_path:
        _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
        _node.logger.info(f'Selected: {selected_path}')
    else:
        _bridge.set(f'{_node_id}_ActivePorts', ['Cancelled'], _node.name)
        _node.logger.info('Cancelled.')
    return {'Path': selected_path, 'Path': ''}
