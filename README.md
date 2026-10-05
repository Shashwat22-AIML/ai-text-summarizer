# ⚡ AI Text Summarizer v2.0

> An intelligent, multi-engine neural text summarization platform built with **Streamlit**, **Groq LPU**, and **NVIDIA NIM**.

[![Streamlit](https://img.shields.io/badge/Streamlit-1.35+-FF4B4B.svg?style=flat&logo=streamlit)](https://streamlit.io)
[![Groq](https://img.shields.io/badge/Groq-LPU%20Inference-f55036.svg?style=flat)](https://groq.com)
[![NVIDIA](https://img.shields.io/badge/NVIDIA-NIM%20Nemotron-76B900.svg?style=flat&logo=nvidia)](https://build.nvidia.com)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

---

## 🌟 Key Features

- **⚡ Dual AI Engine Architecture**:
  - **Groq LPU (Llama 3.3 70B)**: Ultra-fast, sub-second summarization.
  - **NVIDIA NIM (Nemotron 3 Ultra 550B)**: Deep reasoning for complex documents.
- **📡 Real-Time Token Streaming**: Watch summaries generate live with typewriter-style streaming (`st.write_stream`).
- **📁 Multi-Format Ingestion**: Upload `.pdf`, `.docx`, or `.txt` documents or paste raw text.
- **🎨 Custom Summarization Controls**:
  - **Format**: Bullet points or structured paragraphs.
  - **Length**: Short (concise), Medium (balanced), or Detailed (comprehensive).
  - **Audience Style**: Student Notes, Executive Brief, or Simple (ELI5).
- **📊 Analytics & Metrics**: Word counts, compression ratio %, reduction %, and estimated reading time.
- **📥 One-Click Multi-Format Export**: Download summaries directly as **PDF**, **Word (.docx)**, or **Markdown (.md)**.
- **💎 Clean Cyberpunk Aesthetic**: Modern White + Cyan ClubFlux-inspired theme.

---

## 🚀 Quick Start (Local Setup)

### 1. Clone Repository
```bash
git clone https://github.com/YOUR_USERNAME/ai-text-summarizer.git
cd ai-text-summarizer
```

### 2. Create Virtual Environment & Install Dependencies
```bash
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Configure API Keys
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Fill in your API keys (get free keys from [Groq Console](https://console.groq.com) and [NVIDIA Build](https://build.nvidia.com)):
```env
GROQ_API_KEY=gsk_...
NVIDIA_API_KEY=nvapi-...
```

### 4. Run the Application
```bash
streamlit run app.py
```
Open **`http://localhost:8501`** in your browser.

---

## 🌐 Free Deployment (Streamlit Community Cloud)

Streamlit Community Cloud is the official, free hosting platform optimized for Streamlit applications with live WebSockets and token streaming.

1. **Push your code to GitHub**:
   ```bash
   git add .
   git commit -m "Deploy AI Text Summarizer"
   git push origin main
   ```
2. **Go to [share.streamlit.io](https://share.streamlit.io)** and log in with GitHub.
3. Click **"New app"**, select your repository, branch (`main`), and set **Main file path** to `app.py`.
4. Under **"Advanced settings" -> "Secrets"**, add your API keys:
   ```toml
   GROQ_API_KEY = "gsk_..."
   NVIDIA_API_KEY = "nvapi-..."
   ```
5. Click **"Deploy"**! Your app will be live with a free HTTPS URL in seconds.

---

## 📁 Project Structure

```
ai-text-summarizer/
├── .streamlit/
│   └── config.toml          # Light theme & cyan primary colors
├── samples/                 # Sample documents for testing
├── app.py                   # Streamlit UI with streaming & reactive controls
├── summarizer.py            # AI Engine logic (Groq / NVIDIA) & token streaming
├── exporters.py             # PDF, DOCX, and Markdown export builders
├── utils.py                 # File parsers (.pdf, .docx, .txt) & metrics
├── requirements.txt         # Python dependencies
├── .env.example             # Template for API keys
├── .gitignore               # Secrets and build ignore rules
└── README.md
```

---

## 📄 License

Distributed under the MIT License.
