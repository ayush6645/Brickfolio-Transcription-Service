# 📋 Brickfolio Transcription Service: Logging & Observability Manifest

This document provides a comprehensive overview of the logging, tracking, and debugging mechanisms implemented in the Brickfolio Audio Intelligence Pipeline.

---

## 1. Primary Log Files

### 📂 `logs/pipeline.log`
*   **Purpose**: The central nervous system for human-readable execution history.
*   **Format**: Plain text with timestamps and module identifiers.
*   **Attributes**:
    *   `Timestamp`: ISO format (e.g., `2026-04-27 11:45:02,123`)
    *   `Level`: INFO, WARNING, ERROR, DEBUG
    *   `Module`: The specific part of the code generating the log (e.g., `[audio_transcriber]`)
    *   `Message`: Descriptive text of the event.
*   **Example**:
    ```text
    2026-04-27 11:45:02 | INFO     | [ingestion_engine] Successfully ingested: call_record_001.mp3
    2026-04-27 11:45:10 | ERROR    | [audio_transcriber] Critical failure: Gemini API Timeout.
    ```

---

## 2. Metadata & State Tracking (JSON)

### 📂 `metadata/pipeline_state.json`
*   **Purpose**: Tracks the granular progress of every file through the pipeline to allow for crash recovery and status reporting.
*   **Attributes**:
    *   `file_id`: Unique identifier (usually filename).
    *   `status`: Global state (`pending`, `completed`, `failed`).
    *   `cleaning_status`: State of the AI audio restoration stage.
    *   `intelligence_status`: State of the transcription/analysis stage.
    *   `error_logs`: List of specific errors encountered by this file.
*   **Example**:
    ```json
    {
      "call_01.wav": {
        "status": "completed",
        "cleaning_status": "completed",
        "intelligence_status": "completed",
        "processed_chunks": [1, 2, 3],
        "error_logs": []
      }
    }
    ```

### 📂 `metadata/audio_hash_registry.json`
*   **Purpose**: Prevents duplicate processing (and duplicate billing) by tracking SHA-256 content hashes.
*   **Attributes**:
    *   `Key`: SHA-256 hash of the audio content.
    *   `Value`: The first filename associated with that hash.
*   **Example**:
    ```json
    {
      "ee1dd2655...": "test_audio.wav"
    }
    ```

---

## 3. Financial & Quota Auditing

### 📂 `metadata/billing/usage_{pid}.jsonl`
*   **Purpose**: High-concurrency tracking of API costs. Each process writes its own file to avoid locking issues.
*   **Attributes**:
    *   `model`: The AI model used (Gemini Flash vs Pro).
    *   `tokens_in/out`: Exact token counts for billing accuracy.
    *   `audio_sec`: Duration of audio processed.
    *   `cost_usd`: Estimated cost in USD.
*   **Example**:
    ```json
    {"timestamp": "2026-04-27T11:45:02", "model": "gemini-2.5-flash", "tokens_in": 1200, "cost_usd": 0.00009}
    ```

---

## 4. Pipeline Analysis & Observation Gaps

After analyzing the complete transcription pipeline, I have identified several critical observation gaps that could be filled with specialized log scripts:

### 🚀 A. Audio Quality Metric Registry (`metadata/audio_quality_audit.json`)
*   **Context**: The `audio_preprocessor.py` currently calculates SNR (Signal-to-Noise Ratio), Clipping Rate, and Speech Ratio, but these are only written to the text logs.
*   **Requirement**: Develop a JSON-based audit log for these metrics.
*   **Why**: This allows management to see if recording hardware (phones/mics) is degrading over time and identify "Impossible to Clean" recordings automatically.
*   **Attributes**: `file_name`, `snr_db`, `clipping_rate`, `voice_percentage`, `restoration_profile_used`.

### 📊 B. Latency & Efficiency Benchmark (`logs/performance_report.csv`)
*   **Context**: Large audio files (e.g., 30+ minutes) can take significant time.
*   **Requirement**: A script that calculates "Real-Time Factor" (RTF = Processing Time / Audio Duration).
*   **Why**: To optimize cloud costs. If RTF is > 1.0, the pipeline is slower than the audio itself, which is a bottleneck for high-volume CRM ingestion.
*   **Attributes**: `audio_duration_sec`, `ingestion_time`, `transcription_time`, `rtf_score`.

### 🚨 C. AI Logic "Hallucination" Monitor (`logs/ai_validation.jsonl`)
*   **Context**: The pipeline handles "Hinglish" and multilingual switching.
*   **Requirement**: Track the `confidence_score` (if available) or the "Structure Validity" of the returned JSON.
*   **Why**: To identify if Gemini is "hallucinating" or returning empty turns due to high noise.
*   **Attributes**: `file_name`, `json_validity`, `total_turns_captured`, `empty_segments_count`.

### 🔄 D. Checkpoint Resume Log
*   **Requirement**: A log that tracks "Partially Processed" files.
*   **Why**: Currently, if the system crashes during the 5th chunk of a 10-chunk file, we should know exactly where to resume without re-billing for the first 4 chunks.

---

## 5. Summary of Recommended New Scripts

| Script Name | Target Directory | Primary Metric | Frequency |
| :--- | :--- | :--- | :--- |
| `audit_audio_quality.py` | `metadata/` | Signal-to-Noise Ratio (SNR) | Per File |
| `calculate_pipeline_rtf.py` | `logs/` | Real-Time Factor (Speed) | Per Batch |
| `validate_ai_outputs.py` | `logs/` | JSON Schema Integrity | Per Request |
| `aggregate_billing_audit.py`| `metadata/billing/` | Total USD Cost | Weekly/Monthly |
