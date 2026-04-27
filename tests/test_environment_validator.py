from __future__ import annotations

import shutil
import unittest
from pathlib import Path

from src.infrastructure.utils.environment_validator import AudioValidationError, validate_audio_or_raise

from tests.test_helpers import patched_config, write_wav, workspace_temp_dir


@unittest.skipUnless(shutil.which("ffprobe"), "ffprobe is required for validator tests")
class EnvironmentValidatorTests(unittest.TestCase):
    def test_valid_audio_passes_validation(self):
        with workspace_temp_dir() as temp_dir:
            with patched_config(Path(temp_dir)):
                wav_path = write_wav(Path(temp_dir) / "valid.wav", duration_sec=1.0)
                info = validate_audio_or_raise(wav_path)
                self.assertGreater(info.duration_sec, 0.5)

    def test_tiny_audio_file_is_rejected(self):
        with workspace_temp_dir() as temp_dir:
            with patched_config(Path(temp_dir)):
                bad_file = Path(temp_dir) / "bad.wav"
                bad_file.write_bytes(b"tiny")
                with self.assertRaises(AudioValidationError):
                    validate_audio_or_raise(bad_file)
