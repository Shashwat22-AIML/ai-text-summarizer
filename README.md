# 📝 AI Text Summarizer

A clean, beginner-friendly web application that summarizes any text using
**NVIDIA's Nemotron Ultra** model via the **NVIDIA NIM API**. Built with
Python and Streamlit — no web-framework expertise required.

---

## ✨ Features

| Feature | Details |
|---|---|
| **Paste & Summarize** | Large textbox + one-click Summarize button |
| **Output Mode** | Bullet points or short paragraph |
| **Length Control** | Short, Medium, Detailed |
| **Style Selector** | Student Notes, Executive Brief, Simple (ELI5) |
| **Long-text Chunking** | Texts split into ~700-word chunks → merged into one final summary |
| **Statistics** | Original words, summary words, compression ratio |
| **Copy** | Expandable code block for easy copying |
| **Download** | One-click `.txt` download of the result |
| **Input Validation** | Clear message for empty or very short input (< 30 words) |
| **Error Handling** | Automatic retry + friendly messages for API errors, rate limits, timeouts |

---

## 🗂️ Project Structure

```
ai-text-summarizer/
│
├── app.py            ← Streamlit UI (layout, controls, button logic)
├── summarizer.py     ← API calls, prompt builder, chunking, retry logic
├── utils.py          ← Text cleaning, word counting, validation
│
├── requirements.txt  ← Python dependencies
├── .env.example      ← Template for your API key (copy → .env)
├── .gitignore        ← Keeps .env and cache out of Git
│
├── samples/
│   ├── input_1_evolution.txt
│   ├── output_1_evolution.txt
│   ├── input_2_board_meeting.txt
│   ├── output_2_board_meeting.txt
│   ├── input_3_black_holes.txt
│   └── output_3_black_holes.txt
│
└── README.md
```

---

## 🚀 Setup & Installation

### 1. Prerequisites
- Python 3.10 or newer
- A free NVIDIA NIM API key (see below)

### 2. Get an NVIDIA API Key
1. Go to [https://build.nvidia.com/](https://build.nvidia.com/)
2. Sign up / log in.
3. Click on any model → **Get API Key**.
4. Copy the key (starts with `nvapi-…`).

### 3. Clone or download this project
```bash
git clone <your-repo-url>
cd ai-text-summarizer
```

### 4. Create a virtual environment (recommended)
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
```

### 5. Install dependencies
```bash
pip install -r requirements.txt
```

### 6. Set up your API key
```bash
# Copy the example file
copy .env.example .env       # Windows
# cp .env.example .env       # macOS / Linux

# Open .env in any text editor and replace the placeholder with your real key:
# NVIDIA_API_KEY=nvapi-xxxxxxxxxxxxxxxxxxxx
```

### 7. Run the app
```bash
streamlit run app.py
```

The app will open automatically in your browser at `http://localhost:8501`.

---

## ⚙️ How It Works

### High-level flow

```
User Input (app.py)
      │
      ▼
utils.clean_text()          ← normalize whitespace
utils.validate_input()      ← reject empty / too-short texts
      │
      ▼
summarizer.summarize()
      │
      ├─ Short text (≤700 words) ──► Single API call ──► Summary
      │
      └─ Long text (>700 words)
              │
              ▼
        _split_into_chunks()     ← split into ~700-word pieces with 50-word overlap
              │
              ▼
        _call_api() × N          ← summarize each chunk independently
              │
              ▼
        Final merge _call_api()  ← merge partial summaries into one coherent result
              │
              ▼
            Summary
      │
      ▼
utils.format_stats()        ← compute word counts + compression ratio
      │
      ▼
Display in app.py (metrics, summary box, download button)
```

### Key design decisions

| Decision | Reason |
|---|---|
| **OpenAI package for NVIDIA NIM** | NIM exposes an OpenAI-compatible REST API, so no separate SDK is needed. Just set `base_url`. |
| **~700-word chunks** | Balances context quality (too small = loses meaning) with token limits and cost. |
| **50-word overlap** | Prevents ideas at chunk boundaries from being lost. |
| **Retry on 429 / 5xx** | Rate limits and transient server errors are common in free-tier APIs; one retry with a backoff handles most cases. |
| **`python-dotenv`** | Loads `.env` automatically so the key is never hardcoded. |
| **`MODEL_NAME` constant** | Changing the model requires editing only one line in `summarizer.py`. |

---

## ⚠️ Limitations

- **Free-tier rate limits:** NVIDIA NIM free accounts have strict rate limits. If you see a rate-limit error, wait 30–60 seconds and try again.
- **Very long documents:** Texts with thousands of words may take 30–60 seconds and consume significant API quota.
- **Internet required:** The app calls the NVIDIA cloud API; it does not run a local model.
- **English only:** The prompts and output styles are optimized for English text. Other languages may produce lower-quality results.
- **No streaming:** The full response is received before anything is displayed (Streamlit limitation without custom components).

---

## 📂 Sample Input / Output Pairs

### Sample 1 — Evolution by Natural Selection

**Input:** (`samples/input_1_evolution.txt` — ~380 words)
> "The theory of evolution by natural selection, first formulated in Charles Darwin's book 'On the Origin of Species' in 1859, is the process by which organisms change over time…"

**Options:** Bullet Points | Medium | Student Notes

**Output:** (`samples/output_1_evolution.txt` — ~110 words, 29% compression)
> - **Darwin's Theory (1859):** Evolution = organisms change over time due to heritable trait changes…
> - **Natural Selection:** The primary driver of evolution. Organisms with advantageous inherited traits leave more offspring…
> - **Genetic Drift:** Random fluctuation in trait frequencies — not driven by survival advantage…
> *(and 5 more bullets covering gene flow, mutations, fossil record, comparative anatomy, molecular biology)*

---

### Sample 2 — Q3 2024 Board Meeting Notes

**Input:** (`samples/input_2_board_meeting.txt` — ~380 words)
> "Revenue for Q3 2024 reached $42.7 million, representing a 14% year-over-year increase…"

**Options:** Short Paragraph | Short | Executive Brief

**Output:** (`samples/output_2_board_meeting.txt` — ~85 words, 22% compression)
> Q3 2024 delivered strong results: $42.7M revenue (+14% YoY), 64% gross margin… Net new ARR of $6.4M slightly missed the $7M target… Approved actions: share buyback, 12 additional engineers by year-end, Singapore and Frankfurt data centers in H1 2025…

---

### Sample 3 — What is a Black Hole?

**Input:** (`samples/input_3_black_holes.txt` — ~350 words)
> "A black hole is a region in space where the pull of gravity is so strong that nothing — not even light — can escape from it…"

**Options:** Bullet Points | Short | Simple (ELI5)

**Output:** (`samples/output_3_black_holes.txt` — ~90 words, 26% compression)
> - A black hole is like a super-strong vacuum cleaner in space — its gravity is so powerful that nothing, not even light, can escape…
> - The "point of no return" is called the event horizon. Cross it, and you're gone!
> *(and 3 more fun, simple bullets)*

---

## 📄 License

MIT — free to use, modify, and distribute.
