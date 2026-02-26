import threading
import time
import os
import struct
import math
from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType
from synapse.nodes.lib.provider_node import ProviderNode
from synapse.core.dependencies import DependencyManager

cv2 = None
pyaudio = None
wave = None
np = None
Image = None

def ensure_dependencies():
    global cv2, pyaudio, wave, np, Image
    if cv2 and pyaudio and wave and np and Image: return True
    
    deps_ok = True
    if DependencyManager.ensure("opencv-python", "cv2"):
        import cv2 as _cv; cv2 = _cv
        import numpy as _np; np = _np
    else:
        deps_ok = False

    if DependencyManager.ensure("pyaudio"):
        import pyaudio as _p; pyaudio = _p
        import wave as _w; wave = _w
    else:
        deps_ok = False
        
    if DependencyManager.ensure("Pillow", "PIL.Image"):
        from PIL import Image as _Img; Image = _Img
    else:
        deps_ok = False
        
    # Windows-specific: pygrabber for camera names
    if os.name == 'nt':
            if not DependencyManager.is_installed("pygrabber"):
                DependencyManager.ensure("pygrabber")
    
    if deps_ok:
        print("[Synapse Camera] Dependencies verified.")
    return deps_ok

def resolve_camera_index(input_val, logger=None):
    """
    Resolves a camera index from various input formats:
    - Integer/Float: Returns as-is (e.g., 1.0 -> 1).
    - String "Camera N": Extracts N.
    - String "Device Name": Scans for matching device name (Windows).
    """
    # 1. Direct Number (Int/Float)
    if isinstance(input_val, (int, float)):
        return int(input_val)
        
    # 2. String Parsing
    if isinstance(input_val, str):
        val_str = input_val.strip()
        
        # Case A: "Camera 1" or "1" (or "1.0")
        try:
            # Handle string as float first if possible
            try:
                f_val = float(val_str)
                return int(f_val)
            except ValueError:
                pass # Not a number string
                
            import re
            # Check for "Camera \d+" pattern specifically
            match = re.search(r'Camera\s+(\d+)', val_str, re.IGNORECASE)
            if match:
                return int(match.group(1))
        except: pass
        
        # Case B: Hardware Name (Windows)
        if os.name == 'nt':
            try:
                from pygrabber.dshow_graph import FilterGraph
                graph = FilterGraph()
                devices = graph.get_input_devices()
                
                # Exact match first
                for i, name in enumerate(devices):
                    if name == val_str:
                        return i
                        
                # Partial match/Case-insensitive fallback
                input_lower = val_str.lower()
                for i, name in enumerate(devices):
                    if input_lower in name.lower():
                        if logger: logger.info(f"Resolved '{val_str}' to index {i} ({name})")
                        return i
            except Exception as e:
                # Fallback purely to checking for ending digits if name matching fails
                # e.g., "Fancy Webcam 2" -> 2 (dangerous but common fallback request)
                # match = re.search(r'(\d+)$', val_str)
                # if match: return int(match.group(1))
                if logger: logger.warning(f"Name resolution failed: {e}")
                
    # Fallback
    return 0

class ImageObject:
    def __init__(self, pil_image):
        self.image = pil_image
        self.size = pil_image.size # (width, height)

    def save(self, path, **kwargs):
        """Delegates save to the underlying PIL Image.
        Format is inferred from the file extension."""
        self.image.save(path, **kwargs)

    def get_debug_info(self):
        return ["image data", self.size]

    def __str__(self):
        return f"[image data {self.size}]"

    def __repr__(self):
        return self.__str__()

class VideoObject:
    def __init__(self, filepath, duration=0.0):
        self.filepath = filepath
        self.duration = duration
        self.size = os.path.getsize(filepath) if os.path.exists(filepath) else 0

    def get_debug_info(self):
        return ["video data", self.duration, self.size]

    def __str__(self):
        return "[video data]"

    def __repr__(self):
        return self.__str__()

class WavObject:
    def __init__(self, filepath):
        self.filepath = filepath

    def __str__(self):
        return "[wav data]"

    def __repr__(self):
        return self.__str__()

@NodeRegistry.register("Camera Capture", "Media/Video")
class CameraCaptureNode(ProviderNode):
    """
    Starts a continuous video and/or audio capture session from a camera device.
    Provides a "Provider Flow" for downstream nodes to access live frames or perform
    actions while the camera is active. Consumes the camera resource until stopped.
    
    Inputs:
    - Flow: Start the capture session.
    - Provider End: Close the session and stop recording.
    - Camera Index: Integer index or hardware name of the camera.
    - Record Audio: Whether to capture audio alongside video.
    - Use Memory: If True, saves to a temporary file (RAM disk/temp).
    - File Name: The base filename for the saved recording.
    
    Outputs:
    - Flow: Triggered after the session is successfully closed.
    - Video Data: The resulting video file or bytes.
    - Provider Flow: Active pulse during the session.
    - Provider ID: Used by downstream nodes to identify this capture source.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.provider_type = "CAMERA"
        self.properties["Camera Index"] = 0
        self.properties["Record Audio"] = True
        self.properties["Use Memory"] = True
        self.properties["File Name"] = "capture"
        
        self._running = False
        self._video_thread = None
        self._audio_thread = None
        self._start_time = 0.0
        
        # Shared State
        self._last_frame = None
        self._frame_lock = threading.Lock()
        
        self.define_schema()
        self.register_handlers()

    def register_handlers(self):
        self.register_handler("Flow", self.start_capture)
        self.register_handler("Provider End", self.stop_capture_handler)

        self.input_schema = {
            "Flow": DataType.FLOW,
            "Provider End": DataType.PROVIDER_FLOW,
            "Camera Index": DataType.NUMBER,
            "Record Audio": DataType.BOOLEAN,
            "Use Memory": DataType.BOOLEAN,
            "File Name": DataType.STRING
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Video Data": DataType.ANY,
            "Provider Flow": DataType.PROVIDER_FLOW,
            "Provider ID": DataType.STRING
        }

    def get_current_frame(self):
        """Thread-safe access to the latest captured frame (numpy array BGR)."""
        with self._frame_lock:
            return self._last_frame.copy() if self._last_frame is not None else None

    def start_capture(self, **kwargs):
        if not ensure_dependencies(): return False

        # Read camera index: property is the user-facing setting
        # Fallback with legacy support
        cam_idx_in = self.properties.get("Camera Index", 0)
        # Allow wired input to override (if a non-zero value was explicitly wired)
        wired = kwargs.get("Camera Index")
        if wired is not None and wired != 0:
            cam_idx_in = wired
        
        cam_idx = resolve_camera_index(cam_idx_in, self.logger)
        self.logger.info(f"Resolved Camera Index: {cam_idx} (Input: {cam_idx_in})")
        
        rec_audio = bool(kwargs.get("Record Audio") if kwargs.get("Record Audio") is not None else self.properties.get("Record Audio", True))
        self.use_memory = bool(kwargs.get("Use Memory") if kwargs.get("Use Memory") is not None else self.properties.get("Use Memory", True))
        base_name = kwargs.get("File Name") or self.properties.get("File Name", "capture")
        
        # Paths (using temp file for RAM mode)
        if self.use_memory:
             import tempfile
             self.video_path = os.path.join(tempfile.gettempdir(), f"synp_cam_{self.node_id}.avi")
             self.audio_path = os.path.join(tempfile.gettempdir(), f"synp_cam_{self.node_id}.wav")
        else:
             self.video_path = f"{base_name}.avi"
             self.audio_path = f"{base_name}.wav"

        self._start_recording(cam_idx, rec_audio)
        
        # Register Provider in Scope
        self.register_provider_context()
        self.bridge.set(f"{self.node_id}_Provider ID", self.node_id, self.name)
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Provider Flow"], self.name)
        return True

    def stop_capture_handler(self, **kwargs):
        self._stop_recording()
        self._wait_for_threads()
        
        # Final Output Processing
        video_data = None
        if os.path.exists(self.video_path):
            if self.use_memory:
                with open(self.video_path, "rb") as f:
                    video_data = f.read()
                try: os.remove(self.video_path)
                except: pass
                # Note: We skip audio for RAM mode in 1.6.0 for simplicity unless requested
            else:
                video_data = self.video_path

        self.bridge.set(f"{self.node_id}_Video Data", video_data, self.name)
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        
        # Clean up context
        self.remove_provider_context()
        return True

    def _start_recording(self, cam_idx, rec_audio):
        if self._running: return
        self._running = True
        self._start_time = time.time()
        
        self._video_thread = threading.Thread(
            target=self._video_loop,
            args=(self.video_path, cam_idx),
            daemon=True
        )
        self._video_thread.start()
        
        if rec_audio:
            self._audio_thread = threading.Thread(
                target=self._audio_loop,
                args=(self.audio_path,),
                daemon=True
            )
            self._audio_thread.start()

    def _stop_recording(self):
        self._running = False

    def _wait_for_threads(self):
        if self._video_thread: self._video_thread.join(timeout=2.0)
        if self._audio_thread: self._audio_thread.join(timeout=2.0)

    def _video_loop(self, filename, cam_idx):
        # Priority on Windows: DSHOW usually handles resource sharing better. 
        # Fall back to MSMF or Any.
        cap = cv2.VideoCapture(cam_idx, cv2.CAP_DSHOW)
        if not cap.isOpened():
            cap = cv2.VideoCapture(cam_idx, cv2.CAP_MSMF)
        if not cap.isOpened():
            cap = cv2.VideoCapture(cam_idx)

        if not cap.isOpened():
            self.logger.error(f"Failed to open video device {cam_idx}")
            self._running = False
            return

        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        fps = 20.0
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        if width == 0 or height == 0:
            # Fallback for weird driver reports
            width, height = 640, 480
            
        out = cv2.VideoWriter(filename, fourcc, fps, (width, height))
        
        try:
            frame_counter = 0
            while self._running:
                ret, frame = cap.read()
                if not ret: break
                
                # Update Shared State
                with self._frame_lock:
                    self._last_frame = frame
                
                # Publish frame to bridge every 5 frames for consumers
                frame_counter += 1
                if frame_counter % 5 == 0:
                    try:
                        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        pil_img = Image.fromarray(rgb)
                        img_obj = ImageObject(pil_img)
                        self.bridge.set(f"{self.node_id}_CurrentFrame", img_obj, self.name)
                    except: pass
                
                out.write(frame)
        finally:
            cap.release()
            out.release()

    def _audio_loop(self, filename):
        CHUNK = 1024
        FORMAT = pyaudio.paInt16
        CHANNELS = 1
        RATE = 44100
        frames = []
        try:
            p = pyaudio.PyAudio()
            stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
            while self._running:
                frames.append(stream.read(CHUNK))
            stream.stop_stream(); stream.close(); p.terminate()
            wf = wave.open(filename, 'wb')
            wf.setnchannels(CHANNELS); wf.setsampwidth(p.get_sample_size(FORMAT))
            wf.setframerate(RATE); wf.writeframes(b''.join(frames)); wf.close()
        except: pass

@NodeRegistry.register("Camera List", "Media/Video")
class CameraListNode(SuperNode):
    """
    Scans the system for available camera devices (OpenCV indices and hardware names).
    Returns a list of friendly names or indices that can be used by other Camera nodes.
    
    Inputs:
    - Flow: Trigger the scan.
    - Max Search: The maximum number of indices to probe.
    
    Outputs:
    - Flow: Triggered after the scan is complete.
    - Cameras: List of identified camera names.
    - Count: Total number of cameras found.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties["Max Search"] = 5
        self.define_schema()
        self.register_handlers()

    def register_handlers(self):
        self.register_handler("Flow", self.scan_cameras)

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Max Search": DataType.NUMBER
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Cameras": DataType.LIST,
            "Count": DataType.NUMBER
        }

    def scan_cameras(self, **kwargs):
        if not ensure_dependencies():
            self.logger.error("Missing dependencies.")
            return False

        max_search = kwargs.get("Max Search")
        if max_search is None: 
            # Fallback with legacy support
            max_search = self.properties.get("Max Search", 5)
        
        # Validation
        try:
            max_search = int(max_search)
        except:
            max_search = 5
        if max_search <= 0: max_search = 5
        
        available = []
        
        # Backend priority
        import cv2
        backends = [
            (cv2.CAP_DSHOW, "DSHOW"),
            (cv2.CAP_MSMF, "MSMF"),
            (cv2.CAP_ANY, "Default")
        ]

        # 1. Scan Indices
        for i in range(max_search):
            cap = None
            for backend_id, backend_name in backends:
                try:
                    cap = cv2.VideoCapture(i, backend_id)
                    if cap.isOpened():
                        available.append(i)
                        cap.release()
                        break 
                except: pass
            
            if cap and cap.isOpened():
                 cap.release()
            
            time.sleep(0.05)
                
        self.logger.info(f"[{self.name}] Scan Complete. Indices Found: {available}")
        
        # 2. Get Hardware Names (Windows)
        hardware_names = {}
        if os.name == 'nt':
            try:
                from pygrabber.dshow_graph import FilterGraph
                graph = FilterGraph()
                devices = graph.get_input_devices()
                for i, name in enumerate(devices):
                    hardware_names[i] = name
            except Exception as e:
                self.logger.warning(f"[{self.name}] Failed to get hardware names: {e}")

        # 3. Format Output
        camera_names = []
        for i in available:
            if i in hardware_names:
                # Use Name Only if available
                name = hardware_names[i]
            else:
                name = f"Camera {i}"
            camera_names.append(name)
        
        self.bridge.set(f"{self.node_id}_Cameras", camera_names, self.name)
        self.bridge.set(f"{self.node_id}_Count", len(available), self.name)
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True

@NodeRegistry.register("Camera Image Capture", "Media/Video")
class CameraImageCaptureNode(SuperNode):
    """
    Captures a single still image from a specified camera.
    This node is self-contained and does not require a Camera Provider to be active.
    It opens the camera, grabs a frame, and coordinates immediate closure.
    
    Inputs:
    - Flow: Trigger the image capture.
    - Camera Index: Integer index or hardware name of the camera.
    
    Outputs:
    - Flow: Triggered after the capture attempt.
    - Image: The captured image object.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties["Camera Index"] = 0
        self.define_schema()
        self.register_handlers()

    def register_handlers(self):
        self.register_handler("Flow", self.capture_image)

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Camera Index": DataType.NUMBER
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Image": DataType.IMAGE
        }

    def capture_image(self, **kwargs):
        if not ensure_dependencies():
            self.logger.error("Missing dependencies.")
            return False

        import cv2
        # Fallback to local property or wired input
        cam_idx_in = kwargs.get("Camera Index") if kwargs.get("Camera Index") is not None else self.properties.get("Camera Index", 0)
        
        # Robust Parsing using helper
        cam_idx = resolve_camera_index(cam_idx_in, self.logger)
        self.logger.info(f"Resolved Camera Index: {cam_idx} (Input: {cam_idx_in})")
        
        # [LOCK] Ensure exclusive access to the hardware camera index
        lock_id = f"CAMERA_INDEX_{cam_idx}"
        camera_lock = self.bridge.get_provider_lock(lock_id)
        
        with camera_lock:
            try:
                # Priority on Windows: DSHOW -> MSMF -> Default
                cap = cv2.VideoCapture(cam_idx, cv2.CAP_DSHOW)
                if not cap.isOpened():
                    cap = cv2.VideoCapture(cam_idx, cv2.CAP_MSMF)
                if not cap.isOpened():
                    cap = cv2.VideoCapture(cam_idx)

                if not cap.isOpened():
                    self.logger.error(f"Cannot open camera {cam_idx}. Check connection or index.")
                    self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
                    return True
                
                # Extended warm-up wait
                time.sleep(0.5) 
                
                # Increased warm-up frames for high-res/slow cameras
                ret = False
                for _ in range(10):
                    ret, frame = cap.read()
                    if ret: break
                    time.sleep(0.1)
                    
                if ret:
                    # Convert BGR (OpenCV) to RGB (PIL)
                    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    pil_img = Image.fromarray(rgb_frame)
                    img_obj = ImageObject(pil_img)
                    
                    self.bridge.set(f"{self.node_id}_Image", img_obj, self.name)
                else:
                    self.logger.error("Failed to capture frame after warm-up.")
                    
                cap.release()
                
            except Exception as e:
                self.logger.error(f"Capture Error: {e}")
                if 'cap' in locals() and cap: cap.release()

        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True