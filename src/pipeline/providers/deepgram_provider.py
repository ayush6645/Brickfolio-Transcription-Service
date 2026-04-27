"""
Deepgram-backed transcription provider used as a fallback.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import requests

from ...infrastructure.config import settings as config
from .base import BaseTranscriptionProvider, ProviderResponse


class DeepgramProvider(BaseTranscriptionProvider):
    name = "deepgram"

    def is_available(self) -> bool:
        return bool(config.DEEPGRAM_API_KEY)

    def transcribe(self, input_file_path: Path, *, prompt: str, audio_duration_sec: float) -> ProviderResponse:
        if not self.is_available():
            raise RuntimeError("DEEPGRAM_API_KEY is not configured.")

        url = (
            "https://api.deepgram.com/v1/listen"
            f"?model={config.DEEPGRAM_MODEL}"
            "&diarize=true"
            "&utterances=true"
            "&smart_format=true"
            "&punctuate=true"
            "&detect_language=true"
        )
        headers = {
            "Authorization": f"Token {config.DEEPGRAM_API_KEY}",
            "Content-Type": "audio/wav",
        }
        import time
        start_time = time.perf_counter()
        with Path(input_file_path).open("rb") as audio_handle:
            response = requests.post(
                url,
                headers=headers,
                data=audio_handle,
                timeout=config.GENERIC_TIMEOUT_SEC,
            )
        latency_ms = int((time.perf_counter() - start_time) * 1000)
        response.raise_for_status()
        payload: Dict[str, Any] = response.json()

        turns: List[Dict[str, Any]] = []
        utterances = payload.get("results", {}).get("utterances", [])
        for utterance in utterances:
            transcript = (utterance.get("transcript") or "").strip()
            if not transcript:
                continue
            speaker = utterance.get("speaker")
            turns.append(
                {
                    "speaker": f"Speaker {speaker}" if speaker is not None else "Unknown",
                    "start": float(utterance.get("start", 0.0)),
                    "end": float(utterance.get("end", 0.0)),
                    "text": transcript,
                }
            )

        if not turns:
            alternative = (
                payload.get("results", {})
                .get("channels", [{}])[0]
                .get("alternatives", [{}])[0]
            )
            transcript = (alternative.get("transcript") or "").strip()
            if transcript:
                turns = [
                    {
                        "speaker": "Unknown",
                        "start": 0.0,
                        "end": audio_duration_sec,
                        "text": transcript,
                    }
                ]

        raw_text = "\n".join(f"{turn['speaker']}: {turn['text']}" for turn in turns)
        return ProviderResponse(
            provider=self.name,
            model=config.DEEPGRAM_MODEL,
            turns=turns,
            raw_text=raw_text,
            raw_payload=payload,
            latency_ms=latency_ms,
        )
