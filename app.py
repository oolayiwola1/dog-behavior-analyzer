import os
import uuid
import tempfile
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

# --- ENVIRONMENT & STRIPE CONFIGURATION ---
# Check the DEBUG flag (True = Test Mode, False = Live Mode)
# Defaults to False (live) if not explicitly set
DEBUG_MODE = st.secrets.get("DEBUG", False)
current_env = "test" if DEBUG_MODE else "live"

# Automatically pull the correct stripe keys based on the active environment block
if current_env in st.secrets and "STRIPE_SECRET_KEY" in st.secrets[current_env]:
    stripe.api_key = st.secrets[current_env]["STRIPE_SECRET_KEY"]
elif "STRIPE_SECRET_KEY" in st.secrets:
    # Fallback to top-level key if blocks aren't used
    stripe.api_key = st.secrets["STRIPE_SECRET_KEY"]
else:
    st.error("⚠️ STRIPE_SECRET_KEY is missing from your Streamlit secrets!")

# Fetch active price IDs dynamically based on test/live mode
stripe_pro_price_id = st.secrets[current_env].get("STRIPE_PRO_PRICE_ID") if current_env in st.secrets else st.secrets.get("STRIPE_PRO_PRICE_ID")
stripe_premium_price_id = st.secrets[current_env].get("STRIPE_PREMIUM_PRICE_ID") if current_env in st.secrets else st.secrets.get("STRIPE_PREMIUM_PRICE_ID")

# Automatically switch between localhost and your live cloud URL via secrets.toml
BASE_URL = st.secrets.get("REDIRECT_URL", "http://localhost:8501")

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
        "btn_pro": "🚀 Complete Pro Checkout",
        "btn_premium": "🌟 Complete Premium Checkout",
        "btn_premium_upgrade": "🌟 Upgrade to Premium",
        "btn_manage_sub": "⚙️ Manage Subscription / Cancel",
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
        "btn_pro": "🚀 Payer le forfait Pro",
        "btn_premium": "🌟 Payer le forfait Premium",
        "btn_premium_upgrade": "🌟 Mettre à niveau vers Premium",
        "btn_manage_sub": "⚙️ Gérer l'abonnement / Annuler",
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
        "btn_pro": "🚀 Pagar Plan Pro",
        "btn_premium": "🌟 Pagar Plan Premium",
        "btn_premium_upgrade": "🌟 Actualizar a Premium",
        "btn_manage_sub": "⚙️ Gestionar Suscripción / Cancelar",
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
        "limit_reached": "🚫 **¡Límite de análisis mensual alcanzado!**\n\nHas utilizado los **{used}** análisis permitidos para el plan **{tier}**. Actualiza tu plan o espera hasta el próximo mes.",
        "btn_analyze": "Analizar Comportamiento",
        "initializing_pipeline": "Iniciando análisis...",
        "analysis_complete": "¡Análisis completado!",
        "analysis_failed": "Error en el análisis",
        "upload_prompt": "Por favor, sube un video para comenzar.",
        "disclaimer": "⚠️ **Aviso legal:** Esta aplicación utiliza inteligencia artificial solo con fines educativos e informativos. No sustituye el diagnóstico ni la consulta de un veterinario o entrenador canino profesional."
    }
}

# --- HELPER FUNCTIONS ---
def downsample_video(input_path: str, target_fps: int = 10, max_height: int = 720) -> str:
    cap = cv2.VideoCapture(input_path)
    original_fps = cap.get(cv2.CAP_PROP_FPS)
    if original_fps <= 0:
        original_fps = 30.
