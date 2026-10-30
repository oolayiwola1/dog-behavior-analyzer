import os
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

# File uploader
uploaded_file = st.file_uploader("Choose a video file (.mp4, .mov)", type=["mp4", "mov", "avi"])

if uploaded_file is not None:
    # Save uploaded file locally to a temp path so OpenCV can read it
    temp_video_path = "temp_uploaded_video.mp4"
    with open(temp_video_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("Uploaded Video")
        st.video(temp_video_path)

    with col2:
        st.subheader("Behavioral Analysis Report")
        if st.button("Analyze Behavior", type="primary"):
            with st.spinner("Extracting frames and consulting AI behaviorist..."):
                try:
                    report = analyze_dog_behavior(temp_video_path, use_mock=use_mock_mode)
                    st.markdown(report)
                except Exception as e:
                    st.error(f"An error occurred during analysis: {e}")

else:
    st.info("Please upload a video file to get started.")

