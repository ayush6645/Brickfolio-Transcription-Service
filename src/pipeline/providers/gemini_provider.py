"""
Gemini-backed transcription provider.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict

from ...infrastructure.config import settings as config
from ...infrastructure.utils.gemini_client import resilient_generate
from .base import BaseTranscriptionProvider, ProviderResponse


def _parse_json_payload(raw_text: str) -> Dict[str, Any]:
    try:
        payload = json.loads(raw_text)
    except json.JSONDecodeError:
        start = raw_text.find("{")
        end = raw_text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise
        payload = json.loads(raw_text[start : end + 1])
    if isinstance(payload, list):
        return {"turns": payload}
    return payload


class GeminiProvider(BaseTranscriptionProvider):
    name = "gemini"

    def is_available(self) -> bool:
        return bool(config.GEMINI_API_KEY)

    def transcribe(self, input_file_path: Path, *, prompt: str, audio_duration_sec: float) -> ProviderResponse:
        if not self.is_available():
            raise RuntimeError("GEMINI_API_KEY is not configured.")

        from google import genai
        from google.genai import types

        client = genai.Client(api_key=config.GEMINI_API_KEY)
        uploaded_file = client.files.upload(path=str(input_file_path))
        try:
            while uploaded_file.state == "PROCESSING":
                time.sleep(5)
                uploaded_file = client.files.get(name=uploaded_file.name)

            if uploaded_file.state == "FAILED":
                error_message = getattr(uploaded_file.error, "message", "Unknown Gemini file processing error")
                raise RuntimeError(f"Gemini failed to process audio: {error_message}")

            start_time = time.perf_counter()
            response = resilient_generate(
                client=client,
                model=config.AUDIT_TRANSCRIPTION_MODEL,
                contents=[
                    types.Content(
                        role="user",
                        parts=[
                            types.Part.from_text(text=prompt),
                            types.Part.from_uri(file_uri=uploaded_file.uri, mime_type=uploaded_file.mime_type),
                        ],
                    )
                ],
                config_params=types.GenerateContentConfig(
                    temperature=0.1,
                    response_mime_type="application/json",
                ),
                max_retries=config.TRANSIENT_MAX_RETRIES,
                timeout_sec=config.GENERIC_TIMEOUT_SEC,
                audio_duration_sec=audio_duration_sec,
            )
            latency_ms = int((time.perf_counter() - start_time) * 1000)
            raw_text = response.text or ""
            payload = _parse_json_payload(raw_text)

            tokens_in = 0
            tokens_out = 0
            if hasattr(response, "usage_metadata") and response.usage_metadata:
                tokens_in = response.usage_metadata.prompt_token_count or 0
                tokens_out = response.usage_metadata.candidates_token_count or 0

            return ProviderResponse(
                provider=self.name,
                model=config.AUDIT_TRANSCRIPTION_MODEL,
                turns=payload.get("turns", []),
                raw_text=raw_text,
                raw_payload=payload,
                tokens_in=tokens_in,
                tokens_out=tokens_out,
                latency_ms=latency_ms,
            )
        finally:
            try:
                client.files.delete(name=uploaded_file.name)
            except Exception:
                pass
