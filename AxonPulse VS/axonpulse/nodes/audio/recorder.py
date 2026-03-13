import wave
import threading
import time
import os
import struct
import math
from axonpulse.nodes.registry import NodeRegistry
from axonpulse.core.types import DataType
from axonpulse.nodes.lib.provider_node import ProviderNode
from axonpulse.core.dependencies import DependencyManager

# Lazy Global
pyaudio = None

def ensure_pyaudio():
    global pyaudio
    if pyaudio: return True
    if DependencyManager.ensure("pyaudio"):
        import pyaudio as _p; pyaudio = _p; return True
    return False

class WavObject:
    def __init__(self, filepath, duration=0.0):
        self.filepath = filepath
        self.duration = duration
        self.size = os.path.getsize(filepath) if os.path.exists(filepath) else 0

    def get_debug_info(self):
        return ["wav data", self.duration, self.size]

    def __str__(self):
        return "[wav data]"

    def __repr__(self):
        return self.__str__()

@NodeRegistry.register("Audio Record", "Media/Audio")
class AudioRecordNode(ProviderNode):
    """
    Captures live audio from the system's default input device and saves it to a WAV file.
    Operates as a Provider Node, establishing an audio recording scope.
    Supports intelligent auto-stop based on silence detection for hands-free operation.
    
    Inputs:
    - Flow: Start the recording and enter the Audio Provider scope.
    - Provider End: Manually stop the recording and exit the scope.
    - File Name: The destination path for the recorded .wav file (default: 'recording.wav').
    - Use Silence Exit: If True, automatically stops recording after sustained silence.
    - Silence Level: Sensitivity threshold for silence detection (0.0 to 1.0, where 1.0 is full level).
    - Sample Rate: Audio sampling frequency (e.g., 44100, 48000, 16000).
    - Channels: Number of audio channels (1 for Mono, 2 for Stereo).
    
    Outputs:
    - Flow: Triggered after the recording is successfully stopped and saved.
    - Wav Data: A WavObject containing the file path and metadata for the final recording.
    - Provider Flow: Active while the microphone is recording.
    - Provider ID: Unique identifier for this specific recording session.
    """
    version = "2.3.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.provider_type = "Audio Recorder"
        self.properties["File Name"] = "recording.wav"
        self.properties["Silence Level"] = 0.02
        self.properties["Silence Length"] = 2.0
        self.properties["Use Silence Exit"] = False
        self.properties["Sample Rate"] = 44100
        self.properties["Channels"] = 1
        self.properties["Input Device"] = -1 # Default
        self.properties["Wait For Sound"] = True
        self.properties["Blocking Mode"] = False
        self._use_silence_exit = False
        self._running = False
        self._stop_requested = False
        self._frames = []
        self._thread = None
        self._final_wav_object = None
        self.no_show = ["Sample Rate", "Channels"]

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Provider End": DataType.PROVIDER_FLOW,
            "File Name": DataType.STRING,
            "Use Silence Exit": DataType.BOOLEAN,
            "Silence Level": DataType.NUMBER,
            "Silence Length": DataType.NUMBER,
            "Sample Rate": DataType.NUMBER,
            "Channels": DataType.NUMBER,
            "Input Device": DataType.NUMBER,
            "Wait For Sound": DataType.BOOLEAN,
            "Blocking Mode": DataType.BOOLEAN
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "No Data": DataType.FLOW,
            "Wav Data": DataType.AUDIO,
            "Provider Flow": DataType.PROVIDER_FLOW,
            "Provider ID": DataType.STRING
        }

    def start_scope(self, **kwargs):
        if not ensure_pyaudio():
            self.logger.error("pyaudio not installed.")
            return False

        # Resolve parameters
        filename = kwargs.get("File Name") or self.properties.get("File Name", "recording.wav")
        silence_level = kwargs.get("Silence Level") if kwargs.get("Silence Level") is not None else self.properties.get("Silence Level", 0.1)
        silence_length = kwargs.get("Silence Length") if kwargs.get("Silence Length") is not None else self.properties.get("Silence Length", 3.0)
        use_silence = kwargs.get("Use Silence Exit") if kwargs.get("Use Silence Exit") is not None else self.properties.get("Use Silence Exit", False)
        sample_rate = kwargs.get("Sample Rate") if kwargs.get("Sample Rate") is not None else self.properties.get("Sample Rate")
        channels = kwargs.get("Channels") if kwargs.get("Channels") is not None else self.properties.get("Channels", 1)
        device_index = kwargs.get("Input Device") if kwargs.get("Input Device") is not None else self.properties.get("Input Device", -1)
        wait_for_sound = kwargs.get("Wait For Sound") if kwargs.get("Wait For Sound") is not None else self.properties.get("Wait For Sound", True)
        blocking_mode = kwargs.get("Blocking Mode") if kwargs.get("Blocking Mode") is not None else self.properties.get("Blocking Mode", False)

        # Normalize silence level if it's an old integer value
        if silence_level > 1.0:
            silence_level /= 100.0
            
        # Automatic Sample Rate Detection
        if not sample_rate or sample_rate <= 0:
            try:
                import pyaudio
                p = pyaudio.PyAudio()
                try:
                    target_idx = int(device_index)
                    if target_idx < 0:
                        target_idx = p.get_default_input_device_info()['index']
                    
                    device_info = p.get_device_info_by_index(target_idx)
                    sample_rate = int(device_info.get('defaultSampleRate', 44100))
                    self.logger.info(f"[{self.name}] Auto-detected Sample Rate: {sample_rate} for device {target_idx}")
                finally:
                    p.terminate()
            except Exception as e:
                self.logger.warning(f"[{self.name}] Failed to auto-detect sample rate: {e}. Falling back to 44100.")
                sample_rate = 44100

        self._use_silence_exit = use_silence
        self.logger.info(f"DEBUG Audio: start_scope resolved - Use Silence: {use_silence}, Level: {silence_level}, Length: {silence_length}, Device: {device_index}, Rate: {sample_rate}, Wait For Sound: {wait_for_sound}, Blocking: {blocking_mode}")
        self._start_recording(filename, use_silence, silence_level, silence_length, int(sample_rate), int(channels), int(device_index), wait_for_sound)
        
        # Standard Provider Setup
        self.bridge.set(f"{self.node_id}_Provider ID", self.node_id, self.name)
        self.bridge.set(f"{self.node_id}_Provider Type", self.provider_type, self.name)
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Provider Flow"], self.name)

        if blocking_mode:
            self.logger.info(f"[{self.name}] Blocking Mode enabled. Waiting for recording to finish...")
            while self._running:
                time.sleep(0.1)
                
        return True

    def cleanup_provider_context(self):
        """
        Force-stop the recording thread when the engine or provider terminates.
        """
        self.logger.info(f"[{self.name}] Cleaning up provider context...")
        self._stop_recording()
        
        # Ensure 'ActivePorts' is cleared so the minimap/canvas stops blinking
        self.bridge.set(f"{self.node_id}_ActivePorts", [], self.name)
        
        if self._thread and self._thread.is_alive():
            self.logger.info(f"[{self.name}] Waiting for audio thread to terminate...")
            self._thread.join(timeout=1.5)
            
        super().cleanup_provider_context()

    def end_scope(self, **kwargs):
        _trigger = kwargs.get("_trigger")
        
        # If natural end of scope (no manual stop pulse) and we are using silence exit,
        # we MUST wait for the background thread to finish its work.
        if _trigger != "Provider End" and self._use_silence_exit and self._running:
            self.logger.info("Natural scope end detected. Waiting for Silence Exit...")
            while self._running:
                time.sleep(0.1)

        self._stop_recording()
        # The thread will finish and save the file
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        
        # Branch based on duration or complete silence
        active_port = "Flow"
        
        # Criteria for No Data:
        # 1. Total duration < 1.0s
        # 2. OR (Use Silence Exit is on AND no sound was ever detected)
        is_too_short = self._final_wav_object and self._final_wav_object.duration < 1.0
        is_totally_silent = not self._sound_detected
        
        if is_too_short or is_totally_silent:
            active_port = "No Data"
            reason = "Too short" if is_too_short else "Completely silent"
            self.logger.info(f"Recording triggered '{active_port}' (Reason: {reason}, Duration: {self._final_wav_object.duration:.2f}s)")

        self.bridge.set(f"{self.node_id}_ActivePorts", [active_port], self.name)
        return True

    def _start_recording(self, filename, use_silence, silence_level, silence_length, sample_rate, channels, device_index, wait_for_sound):
        if self._running:
            return
        self._running = True
        self._stop_requested = False
        self._frames = []
        self._final_wav_object = None # Reset
        self._sound_detected = False # Track if any sound ever exceeded threshold
        
        self._thread = threading.Thread(
            target=self._record_loop, 
            args=(filename, use_silence, silence_level, silence_length, sample_rate, channels, device_index, wait_for_sound), 
            daemon=True
        )
        self._thread.start()

    def _stop_recording(self):
        self._running = False
        self._stop_requested = True

    def _record_loop(self, filename, use_silence, silence_level, silence_length, sample_rate, channels, device_index, wait_for_sound):
        CHUNK = 1024
        FORMAT = pyaudio.paInt16
        CHANNELS = channels
        RATE = sample_rate
        
        # Silence counters
        silence_chunks = 0
        THRESHOLD_CHUNKS = int(RATE / CHUNK * silence_length)
        MIN_RECORDING_CHUNKS = int(RATE / CHUNK * 0.5) # 0.5s grace period
        
        start_time = time.time()
        frames_captured = 0
        
        try:
            p = pyaudio.PyAudio()
            
            # Use default if -1 or invalid
            try:
                target_device = int(device_index)
            except:
                target_device = -1

            if target_device < 0:
                target_device = p.get_default_input_device_info()['index']
            
            stream = p.open(
                format=FORMAT, 
                channels=CHANNELS, 
                rate=RATE, 
                input=True, 
                frames_per_buffer=CHUNK,
                input_device_index=target_device
            )
            
            self.logger.info(f"Recording started: {filename} (Silence Exit: {use_silence}, Level: {silence_level}, Rate: {RATE}, Channels: {CHANNELS}, Device: {device_index})")
            
            while not self._stop_requested:
                data = stream.read(CHUNK)
                self._frames.append(data)
                
                frames_captured += 1
                
                if use_silence and frames_captured > MIN_RECORDING_CHUNKS:
                    rms = self._calculate_rms(data)
                    
                    # [DEBUG] Log levels periodically
                    if frames_captured % 20 == 0:
                        is_over = "YES" if rms >= silence_level else "NO"
                        self.logger.info(f"DEBUG Audio: RMS={rms:.4f} Threshold={silence_level} Over={is_over} Captured={frames_captured}")
                    
                    # Track if we ever hear anything
                    if rms >= silence_level:
                        if not self._sound_detected:
                            self.logger.info(f"DEBUG Audio: Initial sound detected! RMS={rms:.4f} >= {silence_level}")
                        self._sound_detected = True
                        silence_chunks = 0
                    else:
                        # Only count silence if either sound was already detected OR we aren't waiting for initial sound
                        if self._sound_detected or not wait_for_sound:
                            silence_chunks += 1
                        
                        if silence_chunks >= THRESHOLD_CHUNKS:
                            self.logger.info(f"Silence detected ({silence_length}s after grace period), breaking loop. Total Frames: {frames_captured}")
                            break # Fall through to save logic
            
            stream.stop_stream()
            stream.close()
            p.terminate()
            
            # Save and Output (Normal Stop)
            self._finish_recording(filename, CHANNELS, p.get_sample_size(FORMAT), RATE)

        except Exception as e:
            self.logger.error(f"Recording Error: {e}")
        finally:
            self._running = False

    def _finish_recording(self, filename, channels, sample_width, rate):
        self._save_wave(filename, channels, sample_width, rate)
        
        # Calculate Duration
        total_frames = sum(len(chunk) for chunk in self._frames) / sample_width
        duration = total_frames / rate
        
        self._final_wav_object = WavObject(filename, duration=duration)
        self.bridge.set(f"{self.node_id}_Wav Data", self._final_wav_object, self.name)
        self.logger.info(f"Recording saved to {filename} ({duration:.2f}s)")

    def _calculate_rms(self, data):
        # We assume 16-bit mono for RMS calculation even in stereo loops for simplicity,
        # or we could average the channels. For simplicity in silence detection, 
        # let's just use the raw buffer as if it were mono, which works fine as a threshold.
        count = len(data) // 2
        format = "<{}h".format(count)
        shorts = struct.unpack(format, data)
        sum_squares = 0.0
        for sample in shorts:
            sum_squares += sample * sample
        
        rms = math.sqrt(sum_squares / count)
        # Normalize to 0.0 - 1.0 (16-bit signed max is 32768)
        return rms / 32768.0

    def _save_wave(self, filename, channels, sample_width, rate):
        try:
            wf = wave.open(filename, 'wb')
            wf.setnchannels(channels)
            wf.setsampwidth(sample_width)
            wf.setframerate(rate)
            wf.writeframes(b''.join(self._frames))
            wf.close()
        except Exception as e:
            self.logger.error(f"Failed to save WAV: {e}")
