from __future__ import annotations

import unittest
from pathlib import Path

from src.infrastructure.utils.audio_hash_registry import AudioHashRegistry

from tests.test_helpers import patched_config, write_wav, workspace_temp_dir


class AudioHashRegistryTests(unittest.TestCase):
    def test_hash_lifecycle_allows_retry_after_failure(self):
        with workspace_temp_dir() as temp_dir:
            base_dir = Path(temp_dir)
            with patched_config(base_dir):
                registry = AudioHashRegistry()
                wav_path = write_wav(base_dir / "sample.wav", duration_sec=1.0)
                file_hash = registry.compute_file_hash(wav_path)

                first = registry.prepare_processing(file_hash, wav_path, "sample_123")
                self.assertTrue(first.should_process)

                registry.mark_failed(file_hash, "sample_123", "boom")
                retry = registry.prepare_processing(file_hash, wav_path, "sample_123")
                self.assertTrue(retry.should_process)

                registry.mark_completed(file_hash, "sample_123", base_dir / "final.json")
                duplicate = registry.prepare_processing(file_hash, wav_path, "sample_123")
                self.assertFalse(duplicate.should_process)
