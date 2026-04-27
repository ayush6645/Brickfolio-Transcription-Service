# 📋 Brickfolio Pipeline Logging & Tracking Guide

This document serves as the central reference for debugging and monitoring the Brickfolio Audio Intelligence Pipeline. It details the existing logging mechanisms and provides an analysis of future tracking requirements.

---

## 🔍 1. Existing Log Files & State Trackers

### A. Central Pipeline Log
*   **File Path**: `logs/pipeline.log`
*   **Purpose**: Real-time operational monitoring. Captures the high-level execution flow, including startup sequence, file discovery, and critical failures (e.g., FFmpeg errors).
*   **Key Attributes**:
    *   `Timestamp`: Precise time of event.
    *   `Level`: INFO, WARNING, ERROR, CRITICAL.
    *   `Component`: The module generating the log (e.g., `[ingestion_engine]`, `[audio_standardizer]`).
    *   `Message`: Descriptive text or raw error output from external tools like FFmpeg.
*   **Example Content**:
    ```text
    2026-04-25 16:00:00,455 | INFO | [transcription_runner] --- Starting Pipeline for: pipeline_test.wav ---
    2026-04-25 16:00:02,924 | ERROR | [audio_standardizer] FFmpeg conversion failed. Code: 3199971767
    ```

### B. Pipeline State Tracker
*   **File Path**: `metadata/pipeline_state.json`
*   **Purpose**: Persistent state management. Ensures the pipeline can resume if interrupted and tracks the progress of every file across all 11+ stages.
*   **Key Attributes**:
    *   `file_id`: Unique identifier (filename).
    *   `status`: Global state (`pending`, `processing`, `completed`, `failed`).
    *   `cleaning_status`: Status of audio restoration.
    *   `intelligence_status`: Status of Gemini audit pass.
    *   `processed_chunks`: List of segments already transcribed (for long calls).
    *   `error_logs`: Captured exceptions for that specific file.
*   **Example Content**:
    ```json
    {
      "call_recording_01.wav": {
        "status": "completed",
        "number_of_chunks": 3,
        "processed_chunks": ["part_00.wav", "part_01.wav"],
        "ingestion": "completed"
      }
    }
    ```

### C. Gemini Billing & Usage Log
*   **File Path**: `metadata/billing/usage_{PID}.jsonl` (Aggregated to `billing_report.json`)
*   **Purpose**: Cost auditing and quota monitoring. Tracks every single API call made to Google Gemini.
*   **Key Attributes**:
    *   `model`: Model name (Flash vs Pro).
    *   `tokens_in` / `tokens_out`: Exact token consumption.
    *   `audio_sec`: Billable audio duration.
    *   `cost_usd`: Real-time cost estimation based on current pricing.
*   **Example Content**:
    ```json
    {"timestamp": "2026-04-27T11:15:02", "model": "gemini-2.5-flash", "tokens_in": 1204, "cost_usd": 0.00015}
    ```

### D. Deduplication Registry
*   **File Path**: `metadata/audio_hash_registry.json`
*   **Purpose**: Fraud and cost prevention. Maps SHA-256 file hashes to filenames to ensure the same recording isn't processed twice.
*   **Key Attributes**:
    *   `hash`: SHA-256 fingerprint of the audio file content.
    *   `filename`: The name of the file associated with that hash.
*   **Example Content**:
    ```json
    { "a1b2c3d4...": "recording_fixed.wav" }
    ```

---

## 🧪 2. Pipeline Analysis & Suggested Tracking Improvements

To ensure production-grade reliability, the following additional log scripts and trackers are recommended:

### 1. API Latency & Performance Log
*   **Requirement**: Track the response time of Gemini API calls.
*   **Benefit**: Identifies regional latency issues or model-specific slowdowns that could affect batch processing speed.
*   **Attribute to Add**: `latency_ms` in the billing log.

### 2. Diarization Confidence Monitor
*   **Requirement**: Extract the `confidence` score for speaker labeling from the AI JSON.
*   **Benefit**: Alerts managers to "Low Confidence" transcripts that require human verification before being sent to the client.

### 3. CRM Handover Audit
*   **Requirement**: Log the status of data ingestion into the CRM (Service 2 output).
*   **Benefit**: Ensures that even if the transcription is perfect, we track if the data successfully landed in the timeline dashboard.

### 4. Audio Quality (SNR) Log
*   **Requirement**: Log the Signal-to-Noise Ratio (SNR) calculated by the preprocessor.
*   **Benefit**: Helps identify if certain recording devices (e.g., specific agent phones) are consistently producing low-quality audio that degrades AI accuracy.

### 5. Prompt Versioning & A/B Testing Log
*   **Requirement**: Log the version of the `ANALYSIS_SYSTEM_PROMPT` used for each audit.
*   **Benefit**: As you refine your business intelligence logic, this allows you to compare the "Intelligence Quality" of old reports vs. new reports.

### 6. Diarization Metadata (Speaker Count)
*   **Requirement**: Log how many unique speakers Gemini detected vs. how many were expected.
*   **Benefit**: Automatically flags calls where the AI failed to distinguish between the agent and the client.

---

## 🛠️ How to use these logs for Debugging
1.  **Check `pipeline_state.json` first**: See which stage failed.
2.  **Search `pipeline.log`**: Look for the `ERROR` timestamp corresponding to the file ID.
3.  **Check `usage_*.jsonl`**: Verify if the error was a "Quota Exceeded" or "Safety Filter" trigger from Gemini.
4.  **Verify FFmpeg**: Check the log for "Error opening input" which usually indicates a corrupted raw file.
