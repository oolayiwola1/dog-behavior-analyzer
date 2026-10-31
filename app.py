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
                        success_url="https://your-app.streamlit.app/?success=true",
                        cancel_url="https://your-app.streamlit.app/?canceled=true",
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
                        success_url="https://your-app.streamlit.app/?success=true",
                        cancel_url="https://your-app.streamlit.app/?canceled=true",
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
                        success_url="https://your-app.streamlit.app/?success=true",
                        cancel_url="https://your-app.streamlit.app/?canceled=true",
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
                                    
                                    # 1. Fetch fresh count right before incrementing to avoid stale state
                                    fresh_profile = supabase.table("profiles").select("analyses_used").eq("id", st.session_state.user.id).execute()
                                    current_used = 0
                                    if fresh_profile.data:
                                        current_used = fresh_profile.data[0].get("analyses_used", 0)

                                    new_count = current_used + 1

                                    # 2. Update Supabase (authenticated session now allows RLS update)
                                    supabase.table("profiles").update({"analyses_used": new_count}).eq("id", st.session_state.user.id).execute()
                                    
                                    # 3. Save report to session state and rerun
                                    st.session_state.analysis_report = report
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
