from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import patch

from src.pipeline.audio_transcriber import normalize_turns, transcribe_chunk, validate_turns
from src.pipeline.providers.base import BaseTranscriptionProvider, ProviderResponse

from tests.test_helpers import workspace_temp_dir, write_wav


class _AlwaysFailProvider(BaseTranscriptionProvider):
    name = "gemini"

    def is_available(self) -> bool:
        return True

    def transcribe(self, input_file_path: Path, *, prompt: str, audio_duration_sec: float) -> ProviderResponse:
        raise RuntimeError("provider down")


class _SuccessProvider(BaseTranscriptionProvider):
    name = "deepgram"

    def is_available(self) -> bool:
        return True

    def transcribe(self, input_file_path: Path, *, prompt: str, audio_duration_sec: float) -> ProviderResponse:
        return ProviderResponse(
            provider=self.name,
            model="stub-model",
            turns=[
                {"speaker": "Speaker 1", "start": 0.0, "end": min(audio_duration_sec or 1.0, 1.0), "text": "hello world"}
            ],
            raw_text="Speaker 1: hello world",
            raw_payload={"turns": [{"speaker": "Speaker 1", "start": 0.0, "end": 1.0, "text": "hello world"}]},
        )


class AudioTranscriberTests(unittest.TestCase):
    def test_turn_validation_flags_non_monotonic_timestamps(self):
        turns = normalize_turns(
            [
                {"speaker": "A", "start": 2.0, "end": 3.0, "text": "later"},
                {"speaker": "B", "start": 1.0, "end": 1.5, "text": "earlier"},
            ]
        )
        validation = validate_turns(turns, duration_hint_sec=3.0)
        self.assertTrue(validation["is_valid"])

    def test_fallback_provider_is_used_after_primary_failure(self):
        with workspace_temp_dir() as temp_dir:
            wav_path = write_wav(Path(temp_dir) / "sample.wav", duration_sec=1.0)
            output_dir = Path(temp_dir) / "transcripts"
            with patch("src.pipeline.audio_transcriber._provider_sequence", return_value=[_AlwaysFailProvider(), _SuccessProvider()]):
                artifact = transcribe_chunk(
                    wav_path,
                    output_dir,
                    chunk_name="chunk_000",
                    duration_sec=1.0,
                    file_id="file_123",
                )
            self.assertTrue(artifact.fallback_used)
            self.assertEqual(artifact.provider, "deepgram")
            self.assertTrue(artifact.transcript_path.exists())
