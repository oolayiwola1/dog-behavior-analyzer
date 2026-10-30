import os
import cv2
from PIL import Image
from google import genai
from google.genai import types

def extract_frames(video_path, frame_rate=1.0):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Could not open video file: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0:
        fps = 30
        
    frame_interval = int(fps * frame_rate)
    frames_data = []
    
    frame_count = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
            
        if frame_count % frame_interval == 0:
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(rgb_frame)
            timestamp = frame_count / fps
            frames_data.append((timestamp, pil_img))
            
        frame_count += 1

    cap.release()
    return frames_data

def analyze_dog_behavior(video_path, use_mock=False):
    if use_mock:
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
        frames_data = extract_frames(video_path, frame_rate=1.0)
        if not frames_data:
            return "No frames could be extracted from the video."

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