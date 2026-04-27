from __future__ import annotations

import json
import unittest
from pathlib import Path

from src.pipeline.transcript_reconstructor import reconstruct_transcript
from tests.test_helpers import workspace_temp_dir


class TranscriptReconstructorTests(unittest.TestCase):
    def test_overlap_duplicates_are_collapsed(self):
        with workspace_temp_dir() as temp_dir:
            temp_path = Path(temp_dir)
            transcript_a = temp_path / "chunk_000_transcript.json"
            transcript_b = temp_path / "chunk_001_transcript.json"
            transcript_a.write_text(
                json.dumps(
                    {
                        "structured_turns": [
                            {"speaker": "Agent", "start": 0.0, "end": 1.2, "text": "hello there"},
                            {"speaker": "Customer", "start": 1.2, "end": 2.0, "text": "yes"},
                        ]
                    }
                ),
                encoding="utf-8",
            )
            transcript_b.write_text(
                json.dumps(
                    {
                        "structured_turns": [
                            {"speaker": "Agent", "start": 0.0, "end": 1.1, "text": "hello there"},
                            {"speaker": "Customer", "start": 1.1, "end": 2.0, "text": "absolutely"},
                        ]
                    }
                ),
                encoding="utf-8",
            )

            output_path = temp_path / "final.json"
            reconstruct_transcript(
                [
                    {
                        "chunk": {"chunk_index": 0, "start_sec": 0.0},
                        "transcript_path": str(transcript_a),
                    },
                    {
                        "chunk": {"chunk_index": 1, "start_sec": 1.0},
                        "transcript_path": str(transcript_b),
                    },
                ],
                output_path,
                "call",
            )
            result = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertLessEqual(len(result["segments"]), 3)
            self.assertEqual(result["file"], "call")
