import os
import uuid
import cv2
import streamlit as st
import stripe
from supabase import create_client, Client

# --- SUPABASE & STRIPE INITIALIZATION ---
@st.cache_resource
def init_supabase() -> Client:
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = init_supabase()

if "GEMINI_API_KEY" in st.secrets:
    os.environ["GEMINI_API_KEY"] = st.secrets["GEMINI_API_KEY"]

if "STRIPE_SECRET_KEY" in st.secrets:
    stripe.api_key = st.secrets["STRIPE_SECRET_KEY"]

from analyzer import analyze_dog_behavior

st.set_page_config(
    page_title="Dog Behavior Analyzer v2",
    page_icon="🐕",
    layout="wide"
)

st.title("🐕 Dog Micro-Body Language Analyzer (v2)")

# --- HANDLE STRIPE REDIRECT SUCCESS / CANCELLATION ---
query_params = st.query_params
if "success" in query_params:
    st.success("🎉 Payment successful! Your subscription is updating in the background. Please log back in if prompted to view your new tier.")
elif "canceled" in query_params:
    st.info("Checkout canceled. Feel free to try again whenever you're ready!")

# --- SESSION & AUTH STATE RESTORATION ---
if "user" not in st.session_state:
    st.session_state.user = None

if "session" not in st.session_state:
    st.session_state.session = None

if "analysis_report" not in st.session_state:
    st.session_state.analysis_report = None

# Restore Supabase auth session across reruns so RLS updates succeed
if st.session_state.session:
    try:
        supabase.auth.set_session(
            st.session_state.session.access_token, 
            st.session_state.session.refresh_token
        )
    except Exception:
        pass

# --- SIDEBAR: AUTHENTICATION & CONFIGURATION ---
st.sidebar.header("Account & Tier")

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
        
        # "Stay Logged In" preference option
        stay_logged_in = st.checkbox("Stay Logged In / Remember Me", value=True)
        
        if st.button("Submit"):
            try:
                if auth_mode == "Sign Up":
                    res = supabase.auth.sign_up({"email": email, "password": password})
                    st.success("Check your email for confirmation, or log in if confirmation is disabled!")
                else:
                    res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                    st.session_state.user = res.user
                    st.session_state.session = res.session
                    st.success("Logged in successfully!")
                    st.rerun()
            except Exception as e:
                st.error(f"Authentication error: {e}")
    else:
        st.write(f"Logged in as: **{st.session_state.user.email}**")
        
        # --- STRIPE CHECKOUT INTEGRATION (LINK BUTTONS) ---
        st.markdown("---")
        st.subheader("Subscription Plans")
        
        if user_tier == "Free":
            st.write("You are on the **Free** tier.")
            
            if st.button("🚀 Generate Pro Checkout"):
                try:
                    checkout_session = stripe.checkout.Session.create(
                        line_items=[{
                            "price": st.secrets["STRIPE_PRO_PRICE_ID"],
                            "quantity": 1,
                        }],
                        mode="subscription",
                        success_url="http://localhost:8501/?success=true",
                        cancel_url="http://localhost:8501/?canceled=true",
                        client_reference_id=st.session_state.user.id,
                    )
                    st.success("Checkout link ready!")
                    st.link_button("💳 Complete Pro Payment on Stripe", checkout_session.url)
                except Exception as e:
                    st.error(f"Checkout error: {e}")

            if st.button("🌟 Generate Premium Checkout"):
                try:
                    checkout_session = stripe.checkout.Session.create(
                        line_items=[{
                            "price": st.secrets["STRIPE_PREMIUM_PRICE_ID"],
                            "quantity": 1,
                        }],
                        mode="subscription",
                        success_url="http://localhost:8501/?success=true",
                        cancel_url="http://localhost:8501/?canceled=true",
                        client_reference_id=st.session_state.user.id,
                    )
                    st.success("Checkout link ready!")
                    st.link_button("💳 Complete Premium Payment on Stripe", checkout_session.url)
                except Exception as e:
                    st.error(f"Checkout error: {e}")

        elif user_tier == "Pro":
            st.write("You are on the **Pro** tier.")
            if st.button("🌟 Generate Premium Checkout"):
                try:
                    checkout_session = stripe.checkout.Session.create(
                        line_items=[{
                            "price": st.secrets["STRIPE_PREMIUM_PRICE_ID"],
                            "quantity": 1,
                        }],
                        mode="subscription",
                        success_url="http://localhost:8501/?success=true",
                        cancel_url="http://localhost:8501/?canceled=true",
                        client_reference_id=st.session_state.user.id,
                    )
                    st.success("Checkout link ready!")
                    st.link_button("💳 Complete Premium Payment on Stripe", checkout_session.url)
                except Exception as e:
                    st.error(f"Checkout error: {e}")
        else:
            st.write("You are on the **Premium** tier (Unlimited)! 🌟")

        st.markdown("---")
        if st.button("Log Out"):
            supabase.auth.sign_out()
            st.session_state.user = None
            st.session_state.session = None
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
        "Free": 15.0,      # Max 15 seconds
        "Pro": 45.0,       # Max 45 seconds
        "Premium": 120.0   # Max 2 minutes
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
