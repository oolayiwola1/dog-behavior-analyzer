# 🐕 Canine Behavior AI Audit (v2)

An open-source, production-ready Streamlit web application that analyzes canine micro-body language indicators (ear posture, tail movement, whale eye, mouth tension) from short video clips using computer vision and multimodal AI.

![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=Streamlit&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Gemini](https://img.shields.io/badge/Gemini_AI-8E75B2?style=for-the-badge&logo=google&logoColor=white)
![Supabase](https://img.shields.io/badge/Supabase-3ECF8E?style=for-the-badge&logo=supabase&logoColor=white)
![Stripe](https://img.shields.io/badge/Stripe-008CDD?style=for-the-badge&logo=stripe&logoColor=white)

---

## ✨ Key Features

* **⚡ Optimized Video Processing Pipeline:** Multi-stage downsampling using `opencv-python-headless` (pruning videos to max 720p at 10 FPS, followed by secondary downscaling to `640x360`) to ensure lightning-fast Gemini multimodal payload handling.
* **🤖 Multimodal AI Insights:** Powered by **Gemini Flash**, acting as an expert certified veterinary behaviorist (IAABC/CBCC-KA) to break down timelines, moods, and actionable advice.
* **🌍 Multilingual Support:** Fully localized UI and AI report generation in **English, Français, and Español**.
* **🔐 Secure Auth & Tier Management:** Built-in user authentication, Row Level Security (RLS), and monthly usage limits tracked via **Supabase**.
* **💳 Automated SaaS Billing:** Seamless subscription integration with **Stripe Checkout** and the Stripe Customer Portal for automated tier upgrades.

---

## 🛠️ Tech Stack

* **Frontend & App Framework:** Streamlit (Python)
* **Video Processing:** OpenCV (`opencv-python-headless`) & Pillow
* **AI Model:** Google GenAI SDK (`gemini-2.5-flash` / `gemini-flash-latest`)
* **Database & Auth:** Supabase (`supabase-py`)
* **Payments:** Stripe Python SDK & Webhooks

---

## 🚀 Local Development Setup

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/olayiwola1/dog-behavior-analyzer.git](https://github.com/olayiwola1/dog-behavior-analyzer.git)
   cd dog-behavior-analyzer
