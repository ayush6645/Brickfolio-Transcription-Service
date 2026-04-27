# 🎙️ Brickfolio Audio Intelligence Pipeline
### *High-Fidelity Diarized Transcription Engine*

This repository provides a robust, production-grade pipeline for converting raw audio recordings into structured **JSON subtitle data**. It is optimized for high-volume ingestion, multilingual support (Hindi/English), and extreme cost-efficiency using Google's **Gemini 2.5 Flash**.

---

## 🚀 Core Mission
To transform unstructured real estate calls into clean, speaker-labeled JSON data:
- **Who spoke?** (Speaker Diarization)
- **When did they speak?** (Precise Timestamps)
- **What did they say?** (Phonetic Roman Script Transcription)

---

## 🛠️ System Architecture

The pipeline follows a **Hexagonal (Ports & Adapters) Architecture**, making it highly modular and flexible.

### 1. Ingestion Layer (The Input)
The `IngestionEngine` monitors data sources for new files.
- **Local Adapter**: Watches the `Audio_Data/` folder for new `.mp3`, `.wav`, or `.m4a` files.
- **Deduplication**: Uses SHA-256 content hashing to ensure the same file is never processed (or billed) twice.

### 2. Processing Pipeline (The Core)
1. **Standardization**: FFmpeg-powered conversion to 16kHz Mono WAV.
2. **Chunking**: Automatically splits long calls (e.g., >5 mins) into overlapping segments to maintain LLM context and allow parallel processing.
3. **Multimodal Transcription**: Leverages **Gemini 2.5 Flash** to "hear" the audio directly, preserving accents and code-switching (Hinglish) phonetically.
4. **Reconstruction**: Uses fuzzy logic (`difflib`) to stitch segments back into a single, unified timeline with overlapping speech deduplicated.

### 3. Output Layer
Generates clean JSON and human-readable TXT artifacts in the `data/final/` directory.

---

## 📁 Project Structure

```text
brickfolio-transcription/
├── Audio_Data/             # 📥 Drop raw audio files here
├── data/
│   ├── standardized/       # Normalized audio artifacts
│   ├── chunks/             # Temporary fragments for long calls
│   └── final/              # 📤 Final JSON and TXT outputs
├── src/
│   ├── infrastructure/     # Config, adapters, and system utilities
│   ├── pipeline/           # Core processing stages
│   └── api/                # FastAPI endpoint (optional)
└── scratch/                # Test and verification scripts
```

---

## ⚙️ Setup & Installation

### 1. Prerequisites
- **Python 3.10+**
- **FFmpeg**: Must be installed and added to your system `PATH`.
- **Google Gemini API Key**: Get one from [Google AI Studio](https://aistudio.google.com/).

### 2. Installation
```bash
# Clone the repository
git clone <repo-url>
cd brickfolio-transcription

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration
Create a `.env` file in the root directory:
```env
GEMINI_API_KEY=your_gemini_api_key_here
POSTGRES_HOST=localhost (optional)
...
```

---

## 🏃 Usage

### Batch Processing (Recommended)
Simply place your audio files in the `Audio_Data/` folder and run the ingestion engine:
```bash
# Example command (create a run.py or use the engine directly)
python -c "from src.pipeline.ingestion_engine import engine; engine.run_full_pipeline_on_new()"
```

### API Access
You can also run the service as a web API:
```bash
python -m src.api.main
```
Endpoint: `POST http://localhost:8001/transcribe`

---

## 📊 Output Format
The final JSON output follows a clean "subtitle" schema:

```json
{
  "file": "call_recording_01",
  "total_duration_seconds": 124.5,
  "segments": [
    {
      "start": 0.0,
      "end": 4.2,
      "speaker": "Agent",
      "text": "Hello sir, mera naam sachi hai Brickfolio se."
    },
    {
      "start": 4.5,
      "end": 8.1,
      "speaker": "Customer",
      "text": "Haan ji, boliye, project ke baare mein janna tha."
    }
  ]
}
```

---

## 💡 Key Features
- **Cost Efficiency**: Optimized for Gemini 2.5 Flash (~$0.02 per audio hour).
- **Phonetic Preservation**: Transcribes Indian languages into Roman script for easy LLM analysis.
- **Robustness**: Handles file locking and concurrent processing safely.
- **Extensible**: Easily add S3 or Cloud Storage sources via the Adapter pattern.

---

## 🔒 Security & Best Practices

To ensure a safe deployment and version control:
- **Environment Variables**: Never commit your `.env` file. It is included in `.gitignore` by default.
- **Data Privacy**: The `Audio_Data/`, `data/`, and `logs/` directories are ignored to prevent leaking raw recordings or sensitive transcripts.
- **API Keys**: Ensure all API keys are managed via environment variables and never hardcoded in the source.

## 📤 Preparing for GitHub

1. Ensure `.env` is NOT tracked: `git status` should not show it.
2. Verify `.gitignore` covers all local data folders.
3. Use `.env.example` as a template for other contributors.
4. Run a final check for any hardcoded strings using tools like `grep`.
