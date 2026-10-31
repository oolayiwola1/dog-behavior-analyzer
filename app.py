import os
import uuid
import cv2
import streamlit as st
from supabase import create_client, Client

# --- SUPABASE INITIALIZATION ---
@st.cache_resource
def init_supabase() -> Client:
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = init_supabase()

if "GEMINI_API_KEY" in st.secrets:
    os.environ["GEMINI_API_KEY"] = st.secrets["GEMINI_API_KEY"]
from analyzer import analyze_dog_behavior

st.set_page_config(
    page_title="Dog Behavior Analyzer v2",
    page_icon="🐕",
    layout="wide"
)

st.title("🐕 Dog Micro-Body Language Analyzer (v2)")

# --- SIDEBAR: AUTHENTICATION & CONFIGURATION ---
st.sidebar.header("Account & Tier")

if "user" not in st.session_state:
    st.session_state.user = None

if "analysis_report" not in st.session_state:
    st.session_state.analysis_report = None

# Fetch user tier and usage FIRST if logged in
user_tier = "Free"
analyses_used = 0

if st.session_state.user:
    try:
        profile_res = supabase.table("profiles").select("tier, analyses_used").eq("id", st.session_state.user.id).execute()
        if profile_res.data:
            user_tier = profile_res.data[0].get("tier", "Free")
            analyses_used = profile_res.data[0].get("analyses_used", 0)
    except Exception as e:
        st.sidebar.error(f"Could not fetch profile: {e}")
        user_tier = "Free"

# Simple Auth Expander in Sidebar
with st.sidebar.expander("🔐 Account Login / Signup", expanded=not st.session_state.user):
    if st.session_state.user is None:
        auth_mode = st.radio("Mode", ["Log In", "Sign Up"], horizontal=True)
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        
        if st.button("Submit"):
            try:
                if auth_mode == "Sign Up":
                    res = supabase.auth.sign_up({"email": email, "password": password})
                    st.success("Check your email for confirmation, or log in if confirmation is disabled!")
                else:
                    res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                    st.session_state.user = res.user
                    st.success("Logged in successfully!")
                    st.rerun()
            except Exception as e:
                st.error(f"Authentication error: {e}")
    else:
        st.write(f"Logged in as: **{st.session_state.user.email}**")
        
        # Quick Tier Upgrade Simulation for Testing
        tier_options = ["Free", "Pro", "Premium"]
        current_tier_index = tier_options.index(user_tier) if user_tier in tier_options else 0
        selected_upgrade = st.selectbox("Change Tier (Test)", tier_options, index=current_tier_index)
        
        if selected_upgrade != user_tier:
            if st.button("Update Tier"):
                try:
                    supabase.table("profiles").update({"tier": selected_upgrade}).eq("id", st.session_state.user.id).execute()
                    st.success(f"Tier updated to {selected_upgrade}!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to update tier: {e}")

        if st.button("Log Out"):
            supabase.auth.sign_out()
            st.session_state.user = None
            st.session_state.analysis_report = None
            st.rerun()

# --- ENFORCE LOGIN BEFORE APP ACCESS ---
if st.session_state.user is None:
    st.warning("🔒 **Please log in or sign up using the sidebar to access the Dog Behavior Analyzer.**")
    st.info("Once logged in, you'll be able to upload videos, track your monthly usage, and analyze your dog's micro-body language.")
else:
    # Sidebar configuration controls
    st.sidebar.header("Configuration")
    use_mock_mode = st.sidebar.checkbox("Use Mock Mode (Bypass API Quota)", value=False)

    # Tier limit mappings
    tier_limits = {
        "Free": 15.0,     # Max 15 seconds
        "Pro": 45.0,      # Max 45 seconds
        "Premium": 120.0  # Max 2 minutes
    }
    max_duration = tier_limits.get(user_tier, 15.0)

    st.sidebar.info(
        f"📋 **Active Tier: {user_tier}**\n\n"
        f"• Max video length: **{int(max_duration)}s**\n"
        f"• Analyses used this month: **{analyses_used}**"
    )

    st.markdown("Upload a short video of your dog to analyze posture, ears, tail signals, and emotional state.")

    # File uploader
    uploaded_file = st.file_uploader("Choose a video file (.mp4, .mov)", type=["mp4", "mov", "avi"])

    if uploaded_file is not None:
        # Generate a unique file path using UUID to prevent multi-user overwrites
        file_extension = os.path.splitext(uploaded_file.name)[1]
        if not file_extension:
            file_extension = ".mp4"
        unique_filename = f"temp_video_{uuid.uuid4().hex}{file_extension}"

        try:
            # Save uploaded file with unique name
            with open(unique_filename, "wb") as f:
                f.write(uploaded_file.getbuffer())

            # Calculate video duration using OpenCV
            cap = cv2.VideoCapture(unique_filename)
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = frame_count / fps if fps > 0 else 0
            cap.release()

            col1, col2 = st.columns([1, 1])

            with col1:
                st.subheader("Uploaded Video")
                st.video(unique_filename)
                st.caption(f"⏱️ Detected Length: **{duration:.1f}s** | Limit: **{int(max_duration)}s**")

            with col2:
                st.subheader("Behavioral Analysis Report")
                
                # Enforce tier-wise duration limit
                if duration > max_duration:
                    st.warning(
                        f"⚠️ **Clip exceeds {user_tier} Tier limit!**\n\n"
                        f"This video is **{duration:.1f} seconds long**, but your current **{user_tier} Tier** allows a maximum of **{int(max_duration)} seconds**. "
                        f"Please upgrade your tier or upload a shorter clip to proceed."
                    )
                else:
                    # Define monthly analysis count limits
                    analysis_limits = {
                        "Free": 5,
                        "Pro": 15,
                        "Premium": 999999  # Unlimited
                    }
                    max_analyses = analysis_limits.get(user_tier, 5)
                    
                    # Check monthly usage limit if user is logged in
                    limit_reached = False
                    if user_tier != "Premium" and analyses_used >= max_analyses:
                        limit_reached = True

                    if limit_reached:
                        st.error(
                            f"🚫 **Monthly Analysis Limit Reached!**\n\n"
                            f"You have used all **{analyses_used}** of your allowed analyses for the **{user_tier} Tier**. "
                            f"Upgrade your plan or wait until next month to run more analyses."
                        )
                    else:
                        if st.button("Analyze Behavior", type="primary"):
                            # Step-by-step streaming status indicator
                            with st.status("Initializing Analysis Pipeline...", expanded=True) as status_box:
                                def update_status_ui(msg):
                                    status_box.write(f"👉 {msg}")

                                try:
                                    report = analyze_dog_behavior(
                                        unique_filename, 
                                        use_mock=use_mock_mode, 
                                        status_callback=update_status_ui
                                    )
                                    status_box.update(label="Analysis Complete!", state="complete", expanded=False)
                                    
                                    # Save report to session state so it persists across reruns
                                    st.session_state.analysis_report = report
                                    
                                    # Increment usage count in Supabase and trigger rerun to update sidebar count
                                    new_count = analyses_used + 1
                                    supabase.table("profiles").update({"analyses_used": new_count}).eq("id", st.session_state.user.id).execute()
                                    st.rerun()
                                        
                                except Exception as e:
                                    status_box.update(label="Analysis Failed", state="error", expanded=True)
                                    st.error(f"An error occurred during analysis: {e}")

                # Display the saved report if available
                if st.session_state.analysis_report:
                    st.markdown(st.session_state.analysis_report)

        finally:
            # Clean up local temporary file after stream renders
            if os.path.exists(unique_filename):
                os.remove(unique_filename)

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
