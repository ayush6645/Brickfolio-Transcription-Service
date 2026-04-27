# Infrastructure Layer

The **Infrastructure Layer** provides cross-cutting concerns and system-wide utilities that support the entire application.

## Features
- **Configuration**: Centralized management of paths, keys, and model parameters.
- **Logging**: Unified logging system for debugging and monitoring.
- **Utilities**: Generic helper functions for audio processing, validation, and reporting.

## Uses
- Used to configure the environment variables and project paths.
- Provides the "glue" that keeps the system running reliably.

## Why Created
Infrastructure logic (like how a logger is initialized or how a file hash is calculated) shouldn't be mixed with business logic. This layer provides a clean place for these essential system tools.

## File Manifest

### `config/`
- **`settings.py`**: The heart of the project configuration. Handles `.env` loading and recursive path resolution.

### `logging/`
- **`__init__.py`**: (Placeholder for future structured logging enhancements).

### `utils/`
- **`environment_validator.py`**: Ensures the system is ready (folders exist, audio files are valid) before processing.
- **`restoration_engine.py`**: Core DSP logic for AI-based audio restoration.
- **`gemini_client.py`**: Low-level client for interacting with the Google Gemini API.
- **`pipeline_tracker.py`**: Tracks the state of each file as it moves through the pipeline.
- **`report_generator.py`**: Aggregates data into human-readable reports and summaries.
- **`billing_tracker.py`**: Monitors and reports API token usage and estimated costs.
- **`hash_registry.py`**: Prevents double-billing by fingerprinting audio files.
