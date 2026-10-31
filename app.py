import os
import cv2
import streamlit as st

if "GEMINI_API_KEY" in st.secrets:
    os.environ["GEMINI_API_KEY"] = st.secrets["GEMINI_API_KEY"]
from analyzer import analyze_dog_behavior

st.set_page_config(
    page_title="Dog Behavior Analyzer v2",
    page_icon="🐕",
    layout="wide"
)

st.title("🐕 Dog Micro-Body Language Analyzer (v2)")
st.markdown("Upload a short video of your dog to analyze posture, ears, tail signals, and emotional state.")

# Sidebar configuration
st.sidebar.header("Configuration")
use_mock_mode = st.sidebar.checkbox("Use Mock Mode (Bypass API Quota)", value=False)

# Tier selection & limit mappings
user_tier = st.sidebar.selectbox("Subscription Tier", ["Free", "Pro", "Premium"])
tier_limits = {
    "Free": 15.0,     # Max 15 seconds
    "Pro": 45.0,      # Max 45 seconds
    "Premium": 120.0  # Max 2 minutes
}
max_duration = tier_limits[user_tier]

st.sidebar.info(f"📋 **{user_tier} Tier Rules:** Max video length is **{int(max_duration)} seconds**.")

# File uploader
uploaded_file = st.file_uploader("Choose a video file (.mp4, .mov)", type=["mp4", "mov", "avi"])

if uploaded_file is not None:
    # Save uploaded file locally to a temp path so OpenCV can read it
    temp_video_path = "temp_uploaded_video.mp4"
    with open(temp_video_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    # Calculate video duration using OpenCV
    cap = cv2.VideoCapture(temp_video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = frame_count / fps if fps > 0 else 0
    cap.release()

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("Uploaded Video")
        st.video(temp_video_path)
        st.caption(f"⏱️ Detected Length: **{duration:.1f}s** | Limit: **{int(max_duration)}s**")

    with col2:
        st.subheader("Behavioral Analysis Report")
        
        # Enforce tier-wise duration limit
        if duration > max_duration:
            st.warning(
                f"⚠️ **Clip exceeds {user_tier} Tier limit!**\n\n"
                f"This video is **{duration:.1f} seconds long**, but your current **{user_tier} Tier** allows a maximum of **{int(max_duration)} seconds**. "
                f"Please switch to a higher tier in the sidebar or upload a shorter clip to proceed."
            )
        else:
            if st.button("Analyze Behavior", type="primary"):
                # Step-by-step streaming status indicator
                with st.status("Initializing Analysis Pipeline...", expanded=True) as status_box:
                    def update_status_ui(msg):
                        status_box.write(f"👉 {msg}")

                    try:
                        report = analyze_dog_behavior(
                            temp_video_path, 
                            use_mock=use_mock_mode, 
                            status_callback=update_status_ui
                        )
                        status_box.update(label="Analysis Complete!", state="complete", expanded=False)
                        st.markdown(report)
                    except Exception as e:
                        status_box.update(label="Analysis Failed", state="error", expanded=True)
                        st.error(f"An error occurred during analysis: {e}")

    # Disclaimer Footer
    st.markdown("---")
    st.caption(
        "⚠️ **Disclaimer:** This application uses AI models to evaluate visual cues in video clips for educational "
        "and informational purposes only. It is not a substitute for professional veterinary advice, formal behavioral "
        "diagnosis, or certified dog training consultation. If your dog exhibits severe anxiety, aggression, or sudden "
        "behavioral changes, please consult a qualified veterinary behaviorist or certified professional trainer."
    )

else:
    st.info("Please upload a video file to get started.")
