import os
import cv2
from PIL import Image
from google import genai
from google.genai import types

def extract_frames(video_path, frame_rate=1.0, max_frames=15, resize_dim=(640, 360)):
    """
    Extracts frames from video, downsampling FPS, capping total frame count,
    and downscaling resolution to optimize payload size and processing speed.
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Could not open video file: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0:
        fps = 30
        
    total_video_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    # Calculate step based on requested frame rate
    frame_interval = int(fps * frame_rate)
    
    # Safeguard: If interval yields more than max_frames, adjust interval step
    max_interval = max(1, frame_interval)
    estimated_frames = total_video_frames // max_interval if max_interval else 1
    if estimated_frames > max_frames:
        frame_interval = max(1, total_video_frames // max_frames)

    frames_data = []
    frame_count = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
            
        if frame_count % frame_interval == 0:
            # Resize resolution to lower network payload & speed up Gemini processing
            if resize_dim:
                frame = cv2.resize(frame, resize_dim, interpolation=cv2.INTER_AREA)

            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(rgb_frame)
            timestamp = frame_count / fps
            frames_data.append((timestamp, pil_img))

            if len(frames_data) >= max_frames:
                break
            
        frame_count += 1

    cap.release()
    return frames_data

def analyze_dog_behavior(video_path, use_mock=False, status_callback=None):
    """
    Analyzes dog behavior frames using Gemini Flash or returns mock data.
    """
    if use_mock:
        if status_callback:
            status_callback("Using Mock Data (Bypassing Gemini API)...")
        return (
            "### 1. Overall Mood / Emotional State (MOCK DATA)\n"
            "- **State:** Mildly Alert / Curious\n"
            "- **Confidence:** High\n\n"
            "### 2. Timeline Breakdown\n"
            "- **0.0s - 2.0s:** Ears forward, soft eyes, loose tail posture indicating calm engagement.\n"
            "- **3.0s - 5.0s:** Brief moment of lip licking and head turn, suggesting mild appeasement behavior.\n\n"
            "### 3. Actionable Advice\n"
            "- Give the dog space if appeasement signals continue.\n"
            "- Maintain a calm, low-pressure environment."
        )

    try:
        if status_callback:
            status_callback("Extracting and optimizing video frames (1 FPS downsampled)...")

        frames_data = extract_frames(video_path, frame_rate=1.0, max_frames=15, resize_dim=(640, 360))
        if not frames_data:
            return "No frames could be extracted from the video."

        if status_callback:
            status_callback(f"Extracted {len(frames_data)} keyframes. Formatting request for Gemini...")

        contents = [
            "You are an expert certified veterinary behaviorist (IAABC/CBCC-KA). "
            "Analyze the micro-body language signals across these frames (ear posture, tail movement, whale eye, mouth tension).\n\n"
            "Provide a structured analysis for a NEW DOG OWNER with:\n"
            "1. **Overall Mood / Emotional State**\n"
            "2. **Timeline Breakdown**\n"
            "3. **Actionable Advice**\n"
        ]

        for timestamp, img in frames_data:
            contents.append(f"\n--- Frame at {timestamp:.1f} seconds ---")
            contents.append(img)

        if status_callback:
            status_callback("Consulting AI Behaviorist (gemini-flash-latest)...")

        client = genai.Client()
        response = client.models.generate_content(
            model='gemini-flash-latest',
            contents=contents,
            config=types.GenerateContentConfig(temperature=0.2)
        )
        return response.text

    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg or "ResourceExhausted" in error_msg:
            return (
                "⚠️ **API Quota Exceeded (Rate Limit Reached)**\n\n"
                "The Gemini API rate limit was hit. Try enabling **Mock Mode** (`use_mock=True`) "
                "to continue testing your pipeline and frontend without consuming quota."
            )
        return f"❌ **An error occurred during analysis:** {error_msg}"
