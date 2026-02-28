# 🧩 Media Nodes

This document covers nodes within the **Media** core category.

## 📂 Audio

### Audio Record

**Version**: `2.1.0`

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

---

### TTS KaniTTS2

**Version**: `2.1.0`

Registers the KaniTTS-2 engine for speech synthesis.

Initializes a provider context for KaniTTS-2, which supports high-quality 
voice cloning. Other 'Speak' nodes can use this provider by specifying 
the 'TTS Provider' relationship.

Inputs:
- Flow: Trigger the provider initialization.
- Model: The HuggingFace model ID or local path for KaniTTS.
- Temperature: Generation temperature (default 1.0).
- TopP: Top-P sampling threshold (default 0.95).
- Repetition Penalty: Penalty for repeating tokens (default 1.1).

Outputs:
- Done: Pulse triggered once the engine is ready.

---

### TTS Parler

**Version**: `2.1.0`

Registers the Parler-TTS engine for speech synthesis.

Initializes a provider context for Parler-TTS, which generates 
highly expressive speech based on text descriptions.

Inputs:
- Flow: Trigger the provider initialization.
- Model: The HuggingFace model ID for Parler-TTS.
- Description: Natural language description of the target voice.

Outputs:
- Done: Pulse triggered once the engine is ready.

---

### TTS Speak

**Version**: `2.1.0`

Synthesizes speech from text using a registered TTS Provider.

Acts as a consumer node that sends text to a 'TTS System', 'Parler', 
or 'KaniTTS' engine and returns the resulting audio data.

Inputs:
- Flow: Trigger the synthesis.
- Text: The text string to speak.
- Voice Reference: Optional audio sample or embedding for voice cloning.
- Save Path: Optional file path to save the resulting .wav file.

Outputs:
- Flow: Pulse triggered after synthesis completion.
- Audio: Raw audio data or numpy array.
- Sample Rate: The sample rate of the generated audio.

---

### TTS System

**Version**: `2.1.0`

Registers the system's native Text-to-Speech engine.

Initializes a provider context using pyttsx3. This engine is cross-platform
and does not require an internet connection. Other 'Speak' nodes use 
this provider to synthesize audio.

Inputs:
- Flow: Trigger the provider initialization.
- Rate: Speech rate in words per minute (default 200).
- Volume: Speech volume from 0.0 to 1.0 (default 1.0).
- VoiceIndex: Index of the system voice to use (default 0).

Outputs:
- Done: Pulse triggered once the engine is ready.

---

## 📂 Color

### Color Constant

**Version**: `2.1.0`

Outputs a fixed color value.
Supports RGBA hex strings (e.g., "#800080FF") and manages the color data type.

Inputs:
- Flow: Trigger the output.
- Color: Optional input to override the constant value.

Outputs:
- Flow: Triggered after output.
- Result: The specified color in RGBA hex format.

---

### Merge Color

**Version**: `2.1.0`

Combines individual Red, Green, Blue, and Alpha components into a single color value.
Resulting output is an RGBA hex string.

Inputs:
- Flow: Trigger the merge.
- R, G, B, A: Numerical components (0-255).

Outputs:
- Flow: Triggered after merge.
- Color: The combined color in RGBA hex format.

---

### Split Color

**Version**: `2.1.0`

Deconstructs a color value into its individual Red, Green, Blue, and Alpha components.
Supports both RGBA hex strings and list formats.

Inputs:
- Flow: Trigger the split.
- Color: The color value to split.

Outputs:
- Flow: Triggered after split.
- R, G, B, A: The numerical components (0-255).

---

## 📂 Graphics

### Average Image Pixels

**Version**: `2.1.0`

Calculates the average brightness/intensity of an image.
Converts the image to grayscale and returns a normalized value (0.0 to 1.0).

Inputs:
- Flow: Trigger the calculation.
- Image Data: The image to analyze (path string or PIL Image object).

Outputs:
- Flow: Triggered after the calculation is complete.
- Average: The normalized average pixel value (0.0 = black, 1.0 = white).

---

### Image Preview

**Version**: `2.1.0`

Visualizes image and video data directly within the node interface.

Generates a high-performance thumbnail from local file paths, video frames, 
or memory-resident PIL objects. Displays the preview on the node canvas 
for immediate feedback.

Inputs:
- Flow: Trigger the preview generation.
- Image Data: The source path or image object to preview.

Outputs:
- Flow: Triggered after the thumbnail is generated.
- Image Path: The resolved absolute path to the previewed resource.

---

### Image Processor

**Version**: `2.1.0`

Performs common image manipulation actions like resizing, cropping, or color conversion.

Applies the selected 'Action' to an input image. Supported actions include:
- Grayscale: Convert to 8-bit black and white.
- Single Channel: Extract R, G, or B channel.
- Brightness: Adjust intensity using 'factor' in Action Data.
- Resize: Scale image to W x H dimensions.
- Crop: Extract region [x, y, w, h] from Box input.

Inputs:
- Flow: Trigger the image process.
- Image Path: Path to the source file.
- Action: The visual effect or transformation to apply.
- Action Data: Custom parameters for the effect (JSON).
- W: Target width (for Resize action).
- H: Target height (for Resize action).
- Box: Crop boundaries [x, y, w, h] (for Crop action).

Outputs:
- Flow: Triggered after processing completes.
- Result Path: Path to the modified temporary image file.

---

### Image Segmentation Anything

**Version**: `2.1.0`

Automated image segmentation using the Segment Anything Model (SAM).

This node can automatically identify and mask all objects in an image or perform 
targeted segmentation based on coordinate prompts (points), bounding boxes, or labels.

Inputs:
- Flow: Trigger the segmentation process.
- Image: The source image (Path, PIL Object, or Numpy Array).
- Points: List of [x, y] coordinates for targeted segmentation.
- Labels: List of labels for the points (1 for foreground, 0 for background).
- Box: Bounding box for targeted segmentation [x, y, w, h].
- Model Type: The SAM model variant (vit_b, vit_l, vit_h).
- Checkpoint: Path to the model's .pth checkpoint file.
- Points Per Side: Grid density for automatic mask generation (auto mode).

Outputs:
- Flow: Triggered after segmentation completes.
- Segments: List of detected mask objects with bbox and compliance data.
- Count: The total number of identified segments.

---

### Subtract Image

**Version**: `2.1.0`

Performs pixel-wise subtraction between multiple images.

Takes 'Image A' and subtracts 'Image B', 'Image C', etc., from it. 
Useful for motion detection, background removal, or graphical effects. 
Supports dynamic image inputs.

Inputs:
- Flow: Trigger the subtraction.
- Image A: The base image to subtract from.
- Image B, Image C...: Images to subtract.

Outputs:
- Flow: Pulse triggered after subtraction.
- Result Path: Path where the resulting image is saved.
- Result Image: The processed ImageObject.

---

## 📂 Video

### Camera Capture

**Version**: `2.1.0`

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

---

### Camera Image

**Version**: `2.1.0`

Retrieves the most recent frame from an active Camera Provider.
This node acts as a consumer, pulling frames published by a capture service.

Inputs:
- Flow: Trigger the frame retrieval.

Outputs:
- Flow: Pulse triggered after the image is retrieved.
- Image: The captured image object.

---

### Camera Image Capture

**Version**: `2.1.0`

Captures a single still image from a specified camera.
This node is self-contained and does not require a Camera Provider to be active.
It opens the camera, grabs a frame, and coordinates immediate closure.

Inputs:
- Flow: Trigger the image capture.
- Camera Index: Integer index or hardware name of the camera.

Outputs:
- Flow: Triggered after the capture attempt.
- Image: The captured image object.

---

### Camera List

**Version**: `2.1.0`

Scans the system for available camera devices (OpenCV indices and hardware names).
Returns a list of friendly names or indices that can be used by other Camera nodes.

Inputs:
- Flow: Trigger the scan.
- Max Search: The maximum number of indices to probe.

Outputs:
- Flow: Triggered after the scan is complete.
- Cameras: List of identified camera names.
- Count: Total number of cameras found.

---

### Render Timeline

**Version**: `2.1.0`

Renders a compiled timeline into a video file.

Uses MoviePy to process a 'SceneList' (timeline) and export it 
as an MP4, GIF, or other video format. Supports resolution, FPS, 
and audio ducking controls.

Inputs:
- Flow: Trigger the render.
- Compiled Timeline: The SceneList data to render.
- Output Path: Destination file path (default 'output.mp4').
- Width: Output video width (default 1920).
- Height: Output video height (default 1080).
- FPS: Frames per second (default 24).
- Auto Ducking: Whether to automatically lower background music for speech.

Outputs:
- Flow: Pulse triggered once rendering completes.

---

### Timeline Start

**Version**: `2.1.0`

Initiates a new video timeline session.

Creates an empty 'SceneList' object that can be populated with 
clips, graphics, and audio by downstream nodes. Acts as a 
provider for video building tasks.

Inputs:
- Flow: Trigger the timeline start.

Outputs:
- Flow: Pulse triggered once the timeline is initialized.
- SceneList: The empty SceneList object.

---

[Back to Node Index](Index.md)
