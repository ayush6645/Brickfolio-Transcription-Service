"""
Brickfolio Pipeline Configuration Engine

This module centralizes all configurable parameters for the audio intelligence pipeline.
It handles path resolution, API credentials, model selection, and the complex
prompt engineering required for real estate call analysis.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file for security and local development
load_dotenv()

# ==========================================
# 0. DATABASE CONFIGURATION
# ==========================================
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", None)
POSTGRES_DB = os.getenv("POSTGRES_DB", "brickfolio_intelligence")

# ==========================================
# 1. PATH RESOLUTION & DIRECTORY STRUCTURE
# ==========================================
# BASE_DIR is the root of the project
BASE_DIR = Path(os.getenv("PIPELINE_BASE_DIR", Path(__file__).resolve().parent.parent.parent.parent))
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"

# Standard Data Flow Directories
RAW_AUDIO_DIR = BASE_DIR / "Audio_Data"           # Where incoming raw calls land
STANDARDIZED_AUDIO_DIR = DATA_DIR / "standardized" # Audio converted to WAV/16k/Mono
CHUNKS_DIR = DATA_DIR / "chunks"                   # Temporary storage for long-call segments
CLEANED_DIR = DATA_DIR / "cleaned"                 # Audio after AI restoration/denoising
TRANSCRIPTS_DIR = DATA_DIR / "transcripts"         # Raw transcription outputs
FINAL_DIR = DATA_DIR / "final"                     # Aggregated final artifacts
RESULTS_DIR = DATA_DIR / "results"                 # Processed business intelligence (JSON/TXT)

# System & Metadata Directories
LOGS_DIR = BASE_DIR / "logs"
METADATA_DIR = BASE_DIR / "metadata"

# ==========================================
# 1.1 INGESTION & SOURCE CONFIGURATION
# ==========================================
# Options: "local", "s3" (future), "api" (future)
ACTIVE_AUDIO_SOURCE = os.getenv("ACTIVE_AUDIO_SOURCE", "local")
LOCAL_SOURCE_PATH = RAW_AUDIO_DIR 

# ==========================================
# 2. AUDIO PROCESSING SPECIFICATIONS
# ==========================================
# Standardization targets for the transcription engine (Google/Sarvam/AI)
TARGET_SAMPLE_RATE = 16000
TARGET_CHANNELS = 1 # mono
TARGET_FORMAT = "wav"

# Preprocessing / AI Denoiser Settings
ENABLE_HPF = True      # High-Pass Filter (removes low hum/thumps)
HPF_CUTOFF = 100       # Hz
ENABLE_LPF = True      # Low-Pass Filter (removes high-frequency static)
LPF_CUTOFF = 7500      # Hz
GATE_THRESHOLD = -45.0 # dB (removes background silence noise)
ENABLE_NORMALIZATION = True
ENABLE_SPEECH_RESTORATION = True  # Activates the AI enhancement core
ENABLE_ADAPTIVE_CLEANING = True    # Tunes cleaning based on SNR analysis

# Deepgram Settings
# DEEPGRAM_API_KEY removed as it is not used in the current pipeline version
# Default GEMINI_API_KEY to Trans Key if not explicitly set
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", os.getenv("GEMINI_TRANS_API_KEY"))

# Separate Keys for Cost Tracking (Transcription vs Summarization)
GEMINI_TRANS_API_KEY = os.getenv("GEMINI_TRANS_API_KEY")
GEMINI_SUMM_API_KEY = os.getenv("GEMINI_SUMM_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", GEMINI_TRANS_API_KEY)

# Models & Providers
DEEPGRAM_MODEL = "nova-2"
GEMINI_MODEL = "gemini-2.5-pro"

# Requested Configuration: Optimized for Quota & Cost
AUDIT_TRANSCRIPTION_MODEL = "gemini-2.5-flash"  # Flash for high-volume transcription
AUDIT_INTELLIGENCE_MODEL = "gemini-2.5-pro"     # Pro for deep-dive intelligence
SUMMARY_REFRESH_MODEL = "gemini-2.5-pro"

PROVIDER_MODEL_LABELS = {
  "gemini": "GEMINI_2.5-pro",
}

DEEPGRAM_LANGUAGE = "multi"  # Enable multilingual (Hindi/Marathi/English)
DEEPGRAM_DIARIZE = True   # Enable speaker identification

# Preprocessing Settings
ENABLE_HPF = True      # Enable High-Pass Filter to remove low-end noise
HPF_CUTOFF = 100       # Lowering to 100Hz for Hindi speech safety
ENABLE_LPF = True      # Enable Low-Pass Filter (requested for interference reduction)
LPF_CUTOFF = 7500      # 7.5kHz cutoff for natural speech
ENABLE_NORMALIZATION = True
ENABLE_SPEECH_RESTORATION = True  # Unified name for the bouncer logic
ENABLE_ADAPTIVE_CLEANING = True

# Adaptive Pre-processing Thresholds
SNR_BYPASS_THRESHOLD = 20.0  # dB
SNR_SAFE_THRESHOLD = 10.0    # dB
MAX_CLIPPING_RATE = 0.05
SPEECH_DROP_THRESHOLD_DB = -12.0 # Max allowed dB drop before triggering fallback
CLARITY_DROP_THRESHOLD_DB = 4.5  # Max allowed HF band loss before fallback

# Adaptive profile tuning
SAFE_NOISE_REDUCTION = 0.25
SAFE_COMPRESSOR_RATIO = 1.8
SAFE_GAIN_DB = 2.0
STRONG_COMPRESSOR_RATIO = 2.5
STRONG_GAIN_DB = 3.0

# ==========================================
# 3. CHUNKING & SEGMENTATION (Large Calls)
# ==========================================
# Strategy: Long calls are broken into segments to avoid LLM context limits
# and to allow parallel processing.
CHUNK_LENGTH_MS = 180 * 1000  # 3 Minutes
OVERLAP_MS = 5 * 1000        # 5 seconds overlap for context continuity
SEGMENT_THRESHOLD_SEC = 300  # Files > 5 mins automatically trigger chunking

# ==========================================
# 4. API & MODEL CONFIGURATIONS
# ==========================================
# DEEPGRAM_API_KEY removed as it is not used in the current pipeline version

# Primary Gemini API Key fallbacks
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", os.getenv("GEMINI_TRANS_API_KEY"))

# Separate keys allow fine-grained quota management for different stages
GEMINI_TRANS_API_KEY = os.getenv("GEMINI_TRANS_API_KEY", GEMINI_API_KEY)
GEMINI_SUMM_API_KEY = os.getenv("GEMINI_SUMM_API_KEY", GEMINI_API_KEY)

# Model Selection
GEMINI_MODEL = "gemini-2.5-pro"
AUDIT_TRANSCRIPTION_MODEL = "gemini-2.5-flash"
AUDIT_INTELLIGENCE_MODEL = "gemini-2.5-pro"
LEAD_BOUNCER_MODEL = "gemini-2.5-flash"

# ==========================================
# 5. PIPELINE BEHAVIOR & CONTROL
# ==========================================
ENABLED_PROVIDERS = ["gemini"]
STRICT_MODEL_LOCK = True
MAX_PARALLEL_WORKERS = 8      # Increased for high-speed batch processing
GENERIC_TIMEOUT_SEC = 300     # Global API timeout

STRUCTURED_TRANSCRIPTION_PROMPT = """
You are a high-fidelity audio transcription engine. 
Your goal is to generate a diarized transcript in strict JSON format, similar to subtitles.

Return strict JSON with this schema:
{
  "turns": [
    {
      "speaker": "Speaker Name/ID",
      "start": number, (seconds)
      "end": number, (seconds)
      "text": "The exact spoken text"
    }
  ]
}

Rules:
- Identify speakers accurately.
- Use start and end times in seconds.
- Transcribe the language spoken phonetically into Roman script.
- Do NOT translate.
- Do NOT include any commentary outside the JSON.
"""
