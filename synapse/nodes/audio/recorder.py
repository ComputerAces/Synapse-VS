import wave
import threading
import time
import os
import struct
import math
from synapse.core.node import BaseNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType
from synapse.nodes.lib.provider_node import ProviderNode
from synapse.core.dependencies import DependencyManager

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
    - Silence Level: Sensitivity threshold for silence detection (higher = more sensitive).
    
    Outputs:
    - Flow: Triggered after the recording is successfully stopped and saved.
    - Wav Data: A WavObject containing the file path and metadata for the final recording.
    - Provider Flow: Active while the microphone is recording.
    - Provider ID: Unique identifier for this specific recording session.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.provider_type = "Audio Recorder"
        self.properties["File Name"] = "recording.wav"
        self.properties["Silence Level"] = 500
        self.properties["Use Silence Exit"] = False
        self._running = False
        self._frames = []
        self._thread = None
        self._final_wav_object = None

        self.define_schema()
        # ProviderNode registers "Flow" -> start_scope, "Provider End" -> end_scope
        # We override the methods to inject our logic.

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Provider End": DataType.PROVIDER_FLOW,
            "File Name": DataType.STRING,
            "Use Silence Exit": DataType.BOOLEAN,
            "Silence Level": DataType.NUMBER
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Wav Data": DataType.AUDIO,
            "Provider Flow": DataType.PROVIDER_FLOW,
            "Provider ID": DataType.STRING
        }

    def start_scope(self, **kwargs):
        if not ensure_pyaudio():
            self.logger.error("pyaudio not installed.")
            return False

        filename = kwargs.get("File Name") or self.properties.get("File Name", "recording.wav")
        use_silence = kwargs.get("Use Silence Exit") if kwargs.get("Use Silence Exit") is not None else self.properties.get("Use Silence Exit", False)
        silence_level = kwargs.get("Silence Level") if kwargs.get("Silence Level") is not None else self.properties.get("Silence Level", 500)

        self._start_recording(filename, use_silence, silence_level)
        
        # Standard Provider Setup
        self.bridge.set(f"{self.node_id}_Provider ID", self.node_id, self.name)
        self.bridge.set(f"{self.node_id}_Provider Type", self.provider_type, self.name)
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Provider Flow"], self.name)
        return True

    def end_scope(self, **kwargs):
        self._stop_recording()
        # The thread will finish and save the file
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
        
        self.bridge.set(f"{self.node_id}_Wav Data", self._final_wav_object, self.name)
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True

    def _start_recording(self, filename, use_silence, silence_level):
        if self._running:
            return

        self._running = True
        self._frames = []
        self._final_wav_object = None # Reset
        
        self._thread = threading.Thread(
            target=self._record_loop, 
            args=(filename, use_silence, silence_level), 
            daemon=True
        )
        self._thread.start()

    def _stop_recording(self):
        self._running = False

    def _record_loop(self, filename, use_silence, silence_level):
        CHUNK = 1024
        FORMAT = pyaudio.paInt16
        CHANNELS = 1
        RATE = 44100
        
        # Silence counters
        silence_chunks = 0
        MAX_SILENCE_CHUNKS = int(RATE / CHUNK * 2) 
        
        try:
            p = pyaudio.PyAudio()
            stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
            
            self.logger.info(f"Recording started: {filename} (Silence Exit: {use_silence}, Level: {silence_level})")
            
            while self._running:
                data = stream.read(CHUNK)
                self._frames.append(data)
                
                if use_silence:
                    rms = self._calculate_rms(data)
                    if rms < silence_level:
                        silence_chunks += 1
                        if silence_chunks > 20: # ~0.5 seconds of silence
                            self.logger.info("Silence detected, stopping recording.")
                            self._running = False 
                            
                            # Stop Stream
                            stream.stop_stream()
                            stream.close()
                            p.terminate()

                            # Save and Output
                            self._finish_recording(filename, CHANNELS, p.get_sample_size(FORMAT), RATE)
                            
                            # Force Flow Exit (Async)
                            # Note: This relies on Engine checking active ports from services
                            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
                            return

                    else:
                        silence_chunks = 0
            
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
        count = len(data) // 2
        format = "<{}h".format(count)
        shorts = struct.unpack(format, data)
        sum_squares = 0.0
        for sample in shorts:
            sum_squares += sample * sample
        return math.sqrt(sum_squares / count)

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
