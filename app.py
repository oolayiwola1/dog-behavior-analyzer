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

# --- TRANSLATION DICTIONARY ---
TRANSLATIONS = {
    "English": {
        "title": "🐕 Dog Micro-Body Language Analyzer (v2)",
        "account_header": "Account & Tier",
        "auth_title": "🔐 Account Login / Signup",
        "mode": "Mode",
        "login": "Log In",
        "signup": "Sign Up",
        "email": "Email",
        "password": "Password",
        "stay_logged_in": "Stay Logged In / Remember Me",
        "submit": "Submit",
        "logout": "Log Out",
        "plans_header": "Subscription Plans",
        "free_tier_msg": "You are on the **Free** tier.",
        "pro_tier_msg": "You are on the **Pro** tier.",
        "premium_tier_msg": "You are on the **Premium** tier (Unlimited)! 🌟",
        "btn_pro": "🚀 Generate Pro Checkout",
        "btn_premium": "🌟 Generate Premium Checkout",
        "btn_premium_upgrade": "🌟 Generate Premium Checkout (Upgrade)",
        "btn_complete_pro": "💳 Complete Pro Payment on Stripe",
        "btn_complete_premium": "💳 Complete Premium Payment on Stripe",
        "btn_manage_sub": "⚙️ Manage Subscription / Cancel",
        "btn_open_portal": "👉 Open Stripe Billing Portal",
        "login_prompt": "🔒 **Please log in or sign up using the sidebar to access the Dog Behavior Analyzer.**",
        "login_info": "Once logged in, you'll be able to upload videos, track your monthly usage, and analyze your dog's micro-body language.",
        "config_header": "Configuration",
        "mock_mode": "Use Mock Mode (Bypass API Quota)",
        "active_tier": "📋 **Active Tier: {tier}**",
        "max_length": "• Max video length: **{length}s**",
        "analyses_used": "• Analyses used this month: **{used}**",
        "app_intro": "Upload a short video of your dog to analyze posture, ears, tail signals, and emotional state.",
        "uploader_label": "Choose a video file (.mp4, .mov)",
        "uploaded_video_header": "Uploaded Video",
        "detected_length": "⏱️ Detected Length: **{duration:.1f}s** | Limit: **{limit}s**",
        "report_header": "Behavioral Analysis Report",
        "clip_exceeds": "⚠️ **Clip exceeds {tier} Tier limit!**\n\nThis video is **{duration:.1f} seconds long**, but your current **{tier} Tier** allows a maximum of **{limit} seconds**. Please upgrade your tier or upload a shorter clip to proceed.",
        "limit_reached": "🚫 **Monthly Analysis Limit Reached!**\n\nYou have used all **{used}** of your allowed analyses for the **{tier} Tier**. Upgrade your plan or wait until next month to run more analyses.",
        "btn_analyze": "Analyze Behavior",
        "initializing_pipeline": "Initializing Analysis Pipeline...",
        "analysis_complete": "Analysis Complete!",
        "analysis_failed": "Analysis Failed",
        "upload_prompt": "Please upload a video file to get started.",
        "disclaimer": "⚠️ **Disclaimer:** This application uses AI models to evaluate visual cues in video clips for educational and informational purposes only. It is not a substitute for professional veterinary advice, formal behavioral diagnosis, or certified dog training consultation. If your dog exhibits severe anxiety, aggression, or sudden behavioral changes, please consult a qualified veterinary behaviorist or certified professional trainer."
    },
    "Français": {
        "title": "🐕 Analyseur du micro-langage corporel canin (v2)",
        "account_header": "Compte et Forfait",
        "auth_title": "🔐 Connexion / Inscription",
        "mode": "Mode",
        "login": "Se connecter",
        "signup": "S'inscrire",
        "email": "E-mail",
        "password": "Mot de passe",
        "stay_logged_in": "Rester connecté",
        "submit": "Valider",
        "logout": "Se déconnecter",
        "plans_header": "Forfaits d'abonnement",
        "free_tier_msg": "Vous utilisez le forfait **Gratuit**.",
        "pro_tier_msg": "Vous utilisez le forfait **Pro**.",
        "premium_tier_msg": "Vous utilisez le forfait **Premium** (Illimité) ! 🌟",
        "btn_pro": "🚀 Passer au forfait Pro",
        "btn_premium": "🌟 Passer au forfait Premium",
        "btn_premium_upgrade": "🌟 Mettre à niveau vers Premium",
        "btn_complete_pro": "💳 Finaliser le paiement Pro sur Stripe",
        "btn_complete_premium": "💳 Finaliser le paiement Premium sur Stripe",
        "btn_manage_sub": "⚙️ Gérer l'abonnement / Annuler",
        "btn_open_portal": "👉 Ouvrir le portail Stripe",
        "login_prompt": "🔒 **Veuillez vous connecter ou vous inscrire dans la barre latérale pour accéder à l'application.**",
        "login_info": "Une fois connecté, vous pourrez télécharger des vidéos, suivre votre consommation mensuelle et analyser le langage corporel de votre chien.",
        "config_header": "Configuration",
        "mock_mode": "Utiliser le mode simulation (Bypass API)",
        "active_tier": "📋 **Forfait actif : {tier}**",
        "max_length": "• Durée max de la vidéo : **{length}s**",
        "analyses_used": "• Analyses utilisées ce mois-ci : **{used}**",
        "app_intro": "Téléchargez une courte vidéo de votre chien pour analyser sa posture, ses oreilles, sa queue et son état émotionnel.",
        "uploader_label": "Choisissez un fichier vidéo (.mp4, .mov)",
        "uploaded_video_header": "Vidéo téléchargée",
        "detected_length": "⏱️ Durée détectée : **{duration:.1f}s** | Limite : **{limit}s**",
        "report_header": "Rapport d'analyse comportementale",
        "clip_exceeds": "⚠️ **La vidéo dépasse la limite du forfait {tier} !**\n\nCette vidéo dure **{duration:.1f} secondes**, mais votre forfait **{tier}** autorise un maximum de **{limit} secondes**. Veuillez mettre à niveau votre forfait ou télécharger un extrait plus court.",
        "limit_reached": "🚫 **Limite mensuelle d'analyses atteinte !**\n\nVous avez utilisé les **{used}** analyses autorisées pour le forfait **{tier}**. Mettez à niveau votre abonnement ou attendez le mois prochain.",
        "btn_analyze": "Analyser le comportement",
        "initializing_pipeline": "Initialisation de l'analyse...",
        "analysis_complete": "Analyse terminée !",
        "analysis_failed": "Échec de l'analyse",
        "upload_prompt": "Veuillez télécharger une vidéo pour commencer.",
        "disclaimer": "⚠️ **Avertissement :** Cette application utilise des modèles d'IA à des fins éducatives et informatives uniquement. Elle ne remplace en aucun cas les conseils d'un vétérinaire ou d'un éducateur canin certifié en cas de changements comportementaux soudains."
    },
    "Español": {
        "title": "🐕 Analizador del micro-lenguaje corporal canino (v2)",
        "account_header": "Cuenta y Plan",
        "auth_title": "🔐 Iniciar Sesión / Registrarse",
        "mode": "Modo",
        "login": "Iniciar Sesión",
        "signup": "Registrarse",
        "email": "Correo Electrónico",
        "password": "Contraseña",
        "stay_logged_in": "Mantener sesión iniciada",
        "submit": "Enviar",
        "logout": "Cerrar Sesión",
        "plans_header": "Planes de Suscripción",
        "free_tier_msg": "Estás en el plan **Gratuito**.",
        "pro_tier_msg": "Estás en el plan **Pro**.",
        "premium_tier_msg": "¡Estás en el plan **Premium** (Ilimitado)! 🌟",
        "btn_pro": "🚀 Generar Pago Pro",
        "btn_premium": "🌟 Generar Pago Premium",
        "btn_premium_upgrade": "🌟 Actualizar a Premium",
        "btn_complete_pro": "💳 Completar Pago Pro en Stripe",
        "btn_complete_premium": "💳 Completar Pago Premium en Stripe",
        "btn_manage_sub": "⚙️ Gestionar Suscripción / Cancelar",
        "btn_open_portal": "👉 Abrir Portal de Facturación de Stripe",
        "login_prompt": "🔒 **Por favor, inicia sesión o regístrate en la barra lateral para acceder al analizador.**",
        "login_info": "Una vez que inicies sesión, podrás subir videos, ver tu uso mensual y analizar el lenguaje corporal de tu perro.",
        "config_header": "Configuración",
        "mock_mode": "Usar Modo Simulación (Bypass API)",
        "active_tier": "📋 **Plan Activo: {tier}**",
        "max_length": "• Duración máx. del video: **{length}s**",
        "analyses_used": "• Análisis usados este mes: **{used}**",
        "app_intro": "Sube un video corto de tu perro para analizar su postura, orejas, señales de la cola y estado emocional.",
        "uploader_label": "Selecciona un archivo de video (.mp4, .mov)",
        "uploaded_video_header": "Video Subido",
        "detected_length": "⏱️ Duración detectada: **{duration:.1f}s** | Límite: **{limit}s**",
        "report_header": "Informe de Análisis de Comportamiento",
        "clip_exceeds": "⚠️ **¡El video excede el límite del Plan {tier}!**\n\nEste video dura **{duration:.1f} segundos**, pero tu plan **{tier}** permite un máximo de **{limit} segundos**. Actualiza tu plan o sube un clip más corto.",
        "limit_reached": "🚫 **¡Límite de análisis mensual alcanzado!**\n\Has utilizado los **{used}** análisis permitidos para el plan **{tier}**. Actualiza tu plan o espera hasta el próximo mes.",
        "btn_analyze": "Analizar Comportamiento",
        "initializing_pipeline": "Iniciando análisis...",
        "analysis_complete": "¡Análisis completado!",
        "analysis_failed": "Error en el análisis",
        "upload_prompt": "Por favor, sube un video para comenzar.",
        "disclaimer": "⚠️ **Aviso legal:** Esta aplicación utiliza inteligencia artificial solo con fines educativos e informativos. No sustituye el diagnóstico ni la consulta de un veterinario o entrenador canino profesional."
    }
}

# --- LANGUAGE SELECTOR ---
selected_lang = st.sidebar.selectbox("🌐 Language / Langue / Idioma", ["English", "Français", "Español"])
t = TRANSLATIONS[selected_lang]

st.title(t["title"])

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

# --- HANDLE STRIPE REDIRECT SUCCESS / CANCELLATION ---
query_params = st.query_params
if "success" in query_params:
    st.success("🎉 Payment successful! Verifying your subscription...")
    if st.session_state.user:
        try:
            session_id = query_params.get("session_id")
            new_tier = "Pro"
            customer_id = None

            if session_id:
                # Retrieve checkout session from Stripe to confirm details
                checkout_session = stripe.checkout.Session.retrieve(session_id)
                customer_id = checkout_session.customer
                
                # Check price ID to determine if Pro or Premium
                line_items = stripe.checkout.Session.list_line_items(session_id)
                if line_items.data:
                    price_id = line_items.data[0].price.id
                    if price_id == st.secrets.get("STRIPE_PREMIUM_PRICE_ID"):
                        new_tier = "Premium"

            # Update Supabase profile with new tier and customer ID
            update_data = {"tier": new_tier}
            if customer_id:
                update_data["stripe_customer_id"] = customer_id

            supabase.table("profiles").update(update_data).eq("id", st.session_state.user.id).execute()
            st.success(f"✨ Account successfully upgraded to **{new_tier}**!")
            st.query_params.clear()
            st.rerun()
        except Exception as e:
            st.error(f"Could not automatically sync tier: {e}")
elif "canceled" in query_params:
    st.info("Checkout canceled. Feel free to try again whenever you're ready!")
    st.query_params.clear()

# --- SIDEBAR: AUTHENTICATION & CONFIGURATION ---
st.sidebar.header(t["account_header"])

# Fetch user tier, analyses used, and stripe customer ID FIRST if logged in
user_tier = "Free"
analyses_used = 0
stripe_customer_id = None

if st.session_state.user:
    try:
        profile_res = supabase.table("profiles").select("tier, analyses_used, stripe_customer_id").eq("id", st.session_state.user.id).execute()
        if profile_res.data:
            user_tier = profile_res.data[0].get("tier", "Free")
            analyses_used = profile_res.data[0].get("analyses_used", 0)
            stripe_customer_id = profile_res.data[0].get("stripe_customer_id")
    except Exception as e:
        st.sidebar.error(f"Could not fetch profile: {e}")
        user_tier = "Free"

# Simple Auth Expander in Sidebar
with st.sidebar.expander(t["auth_title"], expanded=not st.session_state.user):
    if st.session_state.user is None:
        auth_mode = st.radio(t["mode"], [t["login"], t["signup"]], horizontal=True)
        email = st.text_input(t["email"])
        password = st.text_input(t["password"], type="password")
        
        # "Stay Logged In" preference option
        stay_logged_in = st.checkbox(t["stay_logged_in"], value=True)
        
        if st.button(t["submit"]):
            try:
                if auth_mode == t["signup"]:
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
        
        # --- STRIPE CHECKOUT & PORTAL INTEGRATION ---
        st.markdown("---")
        st.subheader(t["plans_header"])
        
        if user_tier == "Free":
            st.write(t["free_tier_msg"])
            
            if st.button(t["btn_pro"]):
                try:
                    checkout_session = stripe.checkout.Session.create(
                        line_items=[{
                            "price": st.secrets["STRIPE_PRO_PRICE_ID"],
                            "quantity": 1,
                        }],
                        mode="subscription",
                        success_url="http://localhost:8501/?success=true&session_id={CHECKOUT_SESSION_ID}",
                        cancel_url="http://localhost:8501/?canceled=true",
                        client_reference_id=st.session_state.user.id,
                    )
                    st.success("Checkout link ready!")
                    st.link_button(t["btn_complete_pro"], checkout_session.url)
                except Exception as e:
                    st.error(f"Checkout error: {e}")

            if st.button(t["btn_premium"]):
                try:
                    checkout_session = stripe.checkout.Session.create(
                        line_items=[{
                            "price": st.secrets["STRIPE_PREMIUM_PRICE_ID"],
                            "quantity": 1,
                        }],
                        mode="subscription",
                        success_url="http://localhost:8501/?success=true&session_id={CHECKOUT_SESSION_ID}",
                        cancel_url="http://localhost:8501/?canceled=true",
                        client_reference_id=st.session_state.user.id,
                    )
                    st.success("Checkout link ready!")
                    st.link_button(t["btn_complete_premium"], checkout_session.url)
                except Exception as e:
                    st.error(f"Checkout error: {e}")

        elif user_tier == "Pro":
            st.write(t["pro_tier_msg"])
            if st.button(t["btn_premium_upgrade"]):
                try:
                    checkout_session = stripe.checkout.Session.create(
                        line_items=[{
                            "price": st.secrets["STRIPE_PREMIUM_PRICE_ID"],
                            "quantity": 1,
                        }],
                        mode="subscription",
                        success_url="http://localhost:8501/?success=true&session_id={CHECKOUT_SESSION_ID}",
                        cancel_url="http://localhost:8501/?canceled=true",
                        client_reference_id=st.session_state.user.id,
                    )
