from __future__ import annotations

import asyncio
import json
import shutil
import unittest
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

from fastapi import UploadFile

from src.api import main as api_main
from src.infrastructure.utils.audio_hash_registry import AudioHashRegistry
from src.pipeline.audio_preprocessor import PreprocessResult
from src.pipeline.audio_transcriber import TranscriptionArtifact
from src.pipeline.transcription_runner import TranscriptionRunner

from tests.test_helpers import patched_config, workspace_temp_dir, write_wav


def _fake_preprocess(input_wav_path: Path, output_dir: Path) -> PreprocessResult:
    return PreprocessResult(
        output_path=input_wav_path,
        restoration_profile="disabled",
        snr_db=None,
        clipping_rate=None,
        speech_ratio=None,
        speech_preserved=True,
        clarity_preserved=True,
    )


def _fake_transcribe(chunk_path: Path, output_dir: Path, *, chunk_name: str, duration_sec: float, file_id: str | None = None) -> TranscriptionArtifact:
    output_dir.mkdir(parents=True, exist_ok=True)
    transcript_path = output_dir / f"{chunk_name}_transcript.json"
    text_path = output_dir / f"{chunk_name}_transcript.txt"
    turns = [
        {
            "speaker": "Agent",
            "start": 0.0,
            "end": max(min(duration_sec, 1.0), 0.5),
            "text": f"transcript {chunk_name}",
        }
    ]
    payload = {
        "source": "gemini (stub)",
        "full_text": f"Agent: transcript {chunk_name}",
        "structured_turns": turns,
        "segment_summary": "",
        "metadata": {
            "provider": "gemini",
            "model": "stub",
            "validation": {"is_valid": True, "issues": [], "total_turns": 1, "empty_segments_count": 0, "attempts_used": 1},
        },
    }
    transcript_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    text_path.write_text(payload["full_text"], encoding="utf-8")
    return TranscriptionArtifact(
        transcript_path=transcript_path,
        text_path=text_path,
        provider="gemini",
        model="stub",
        turns=turns,
        validation={"is_valid": True, "issues": [], "total_turns": 1, "empty_segments_count": 0, "attempts_used": 1},
        fallback_used=False,
        raw_payload=payload,
        attempts_used=1,
    )


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "ffmpeg and ffprobe are required")
class RunnerIntegrationTests(unittest.TestCase):
    def test_runner_processes_long_file_with_chunk_metadata(self):
        with workspace_temp_dir() as temp_dir:
            base_dir = Path(temp_dir)
            with patched_config(base_dir):
                wav_path = write_wav(base_dir / "input.wav", duration_sec=4.0)
                registry = AudioHashRegistry()
                with patch("src.pipeline.transcription_runner.hash_registry", registry), patch(
                    "src.pipeline.transcription_runner.preprocess_full_file",
                    side_effect=_fake_preprocess,
                ), patch(
                    "src.pipeline.transcription_runner.transcribe_chunk",
                    side_effect=_fake_transcribe,
                ):
                    runner = TranscriptionRunner()
                    result = runner.run_pipeline(wav_path, source="test")
                self.assertTrue(result.final_json_path.exists())
                self.assertGreater(result.chunk_summary["total_chunks"], 1)
                payload = json.loads(result.final_json_path.read_text(encoding="utf-8"))
                self.assertEqual(payload["file"], "input")

    def test_api_uses_shared_runner_output_contract(self):
        with workspace_temp_dir() as temp_dir:
            base_dir = Path(temp_dir)
            with patched_config(base_dir):
                registry = AudioHashRegistry()
                api_main.TEMP_DIR = base_dir / "temp_processing"
                seed_file = write_wav(base_dir / "seed.wav", duration_sec=3.0)
                upload = UploadFile(filename="api.wav", file=BytesIO(seed_file.read_bytes()))
                with patch("src.pipeline.transcription_runner.hash_registry", registry), patch(
                    "src.pipeline.transcription_runner.preprocess_full_file",
                    side_effect=_fake_preprocess,
                ), patch(
                    "src.pipeline.transcription_runner.transcribe_chunk",
                    side_effect=_fake_transcribe,
                ):
                    response = asyncio.run(api_main.transcribe_audio(upload))
                self.assertIn("segments", response)
                self.assertEqual(response["file"], "api")
