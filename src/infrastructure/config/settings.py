"""
Central configuration for the Brickfolio transcription pipeline.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    return int(value) if value is not None else default


def _env_float(name: str, default: float) -> float:
    value = os.getenv(name)
    return float(value) if value is not None else default


# ==========================================
# 0. DATABASE CONFIGURATION
# ==========================================
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_DB = os.getenv("POSTGRES_DB", "brickfolio_intelligence")

# ==========================================
# 1. PATHS & DIRECTORIES
# ==========================================
BASE_DIR = Path(os.getenv("PIPELINE_BASE_DIR", Path(__file__).resolve().parents[3]))
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"
TEMP_PROCESSING_DIR = BASE_DIR / "temp_processing"

RAW_AUDIO_DIR = BASE_DIR / "Audio_Data"
STANDARDIZED_AUDIO_DIR = DATA_DIR / "standardized"
CHUNKS_DIR = DATA_DIR / "chunks"
CLEANED_DIR = DATA_DIR / "cleaned"
TRANSCRIPTS_DIR = DATA_DIR / "transcripts"
FINAL_DIR = DATA_DIR / "final"
RESULTS_DIR = DATA_DIR / "results"
OUTPUT_TRANSCRIPTS_DIR = OUTPUT_DIR / "transcripts"
OUTPUT_SUMMARIES_DIR = OUTPUT_DIR / "summaries"

LOGS_DIR = BASE_DIR / "logs"
METADATA_DIR = BASE_DIR / "metadata"
BILLING_DIR = METADATA_DIR / "billing"
PIPELINE_STATE_FILE = METADATA_DIR / "pipeline_state.json"
HASH_REGISTRY_FILE = METADATA_DIR / "audio_hash_registry.json"
AUDIO_QUALITY_AUDIT_FILE = METADATA_DIR / "audio_quality_audit.json"
AI_VALIDATION_LOG_FILE = LOGS_DIR / "ai_validation.jsonl"
PERFORMANCE_REPORT_FILE = LOGS_DIR / "performance_report.csv"

# ==========================================
# 2. SOURCE CONFIGURATION
# ==========================================
ACTIVE_AUDIO_SOURCE = os.getenv("ACTIVE_AUDIO_SOURCE", "local")
LOCAL_SOURCE_PATH = RAW_AUDIO_DIR

# ==========================================
# 3. AUDIO VALIDATION & STANDARDIZATION
# ==========================================
SUPPORTED_AUDIO_EXTENSIONS = (".mp3", ".wav", ".m4a", ".aac", ".ogg", ".flac")
MIN_AUDIO_BYTES = _env_int("MIN_AUDIO_BYTES", 1024)
MIN_AUDIO_DURATION_SEC = _env_float("MIN_AUDIO_DURATION_SEC", 0.5)

TARGET_SAMPLE_RATE = _env_int("TARGET_SAMPLE_RATE", 16000)
TARGET_CHANNELS = _env_int("TARGET_CHANNELS", 1)
TARGET_FORMAT = os.getenv("TARGET_FORMAT", "wav")

# ==========================================
# 4. PREPROCESSING / RESTORATION
# ==========================================
ENABLE_SPEECH_RESTORATION = _env_bool("ENABLE_SPEECH_RESTORATION", True)
ENABLE_ADAPTIVE_CLEANING = _env_bool("ENABLE_ADAPTIVE_CLEANING", True)
ENABLE_HPF = _env_bool("ENABLE_HPF", True)
HPF_CUTOFF = _env_float("HPF_CUTOFF", 100.0)
ENABLE_LPF = _env_bool("ENABLE_LPF", True)
LPF_CUTOFF = _env_float("LPF_CUTOFF", 7500.0)
GATE_THRESHOLD = _env_float("GATE_THRESHOLD", -45.0)
ENABLE_NORMALIZATION = _env_bool("ENABLE_NORMALIZATION", True)

SNR_BYPASS_THRESHOLD = _env_float("SNR_BYPASS_THRESHOLD", 20.0)
SNR_SAFE_THRESHOLD = _env_float("SNR_SAFE_THRESHOLD", 10.0)
MAX_CLIPPING_RATE = _env_float("MAX_CLIPPING_RATE", 0.05)
SPEECH_DROP_THRESHOLD_DB = _env_float("SPEECH_DROP_THRESHOLD_DB", -12.0)
CLARITY_DROP_THRESHOLD_DB = _env_float("CLARITY_DROP_THRESHOLD_DB", 4.5)

SAFE_NOISE_REDUCTION = _env_float("SAFE_NOISE_REDUCTION", 0.25)
SAFE_COMPRESSOR_RATIO = _env_float("SAFE_COMPRESSOR_RATIO", 1.8)
SAFE_GAIN_DB = _env_float("SAFE_GAIN_DB", 2.0)
STRONG_COMPRESSOR_RATIO = _env_float("STRONG_COMPRESSOR_RATIO", 2.5)
STRONG_GAIN_DB = _env_float("STRONG_GAIN_DB", 3.0)

# ==========================================
# 5. CHUNKING
# ==========================================
CHUNK_LENGTH_SEC = _env_int("CHUNK_LENGTH_SEC", 180)
CHUNK_LENGTH_MS = CHUNK_LENGTH_SEC * 1000
OVERLAP_SEC = _env_int("OVERLAP_SEC", 5)
OVERLAP_MS = OVERLAP_SEC * 1000
SEGMENT_THRESHOLD_SEC = _env_int("SEGMENT_THRESHOLD_SEC", 300)

# ==========================================
# 6. PROVIDERS / MODELS
# ==========================================
GEMINI_TRANS_API_KEY = os.getenv("GEMINI_TRANS_API_KEY")
GEMINI_SUMM_API_KEY = os.getenv("GEMINI_SUMM_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", GEMINI_TRANS_API_KEY)
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")

PRIMARY_TRANSCRIPTION_PROVIDER = os.getenv("PRIMARY_TRANSCRIPTION_PROVIDER", "gemini").lower()
FALLBACK_TRANSCRIPTION_PROVIDER = os.getenv("FALLBACK_TRANSCRIPTION_PROVIDER", "deepgram").lower()
ENABLE_PROVIDER_FALLBACK = _env_bool("ENABLE_PROVIDER_FALLBACK", True)

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-pro")
AUDIT_TRANSCRIPTION_MODEL = os.getenv("AUDIT_TRANSCRIPTION_MODEL", "gemini-2.5-flash")
AUDIT_INTELLIGENCE_MODEL = os.getenv("AUDIT_INTELLIGENCE_MODEL", "gemini-2.5-pro")
SUMMARY_REFRESH_MODEL = os.getenv("SUMMARY_REFRESH_MODEL", "gemini-2.5-pro")
DEEPGRAM_MODEL = os.getenv("DEEPGRAM_MODEL", "nova-2")
DEEPGRAM_LANGUAGE = os.getenv("DEEPGRAM_LANGUAGE", "multi")
DEEPGRAM_DIARIZE = _env_bool("DEEPGRAM_DIARIZE", True)

PROVIDER_MODEL_LABELS = {
    "gemini": AUDIT_TRANSCRIPTION_MODEL,
    "deepgram": DEEPGRAM_MODEL,
}

# ==========================================
# 7. PIPELINE CONTROL
# ==========================================
STRICT_MODEL_LOCK = _env_bool("STRICT_MODEL_LOCK", True)
MAX_CONCURRENT_CHUNKS = _env_int("MAX_CONCURRENT_CHUNKS", 4)
MAX_PARALLEL_WORKERS = MAX_CONCURRENT_CHUNKS
MAX_TRANSCRIPTION_VALIDATION_RETRIES = _env_int("MAX_TRANSCRIPTION_VALIDATION_RETRIES", 2)
GENERIC_TIMEOUT_SEC = _env_int("GENERIC_TIMEOUT_SEC", 300)
TRANSIENT_MAX_RETRIES = _env_int("TRANSIENT_MAX_RETRIES", 10)
ENABLE_PIPELINE_RESUME = _env_bool("ENABLE_PIPELINE_RESUME", True)

STRUCTURED_TRANSCRIPTION_PROMPT = """
You are a high-fidelity audio transcription engine.
Your goal is to generate a diarized transcript in strict JSON format, similar to subtitles.

Return strict JSON with this schema:
{
  "turns": [
    {
      "speaker": "Speaker Name/ID",
      "start": number,
      "end": number,
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
