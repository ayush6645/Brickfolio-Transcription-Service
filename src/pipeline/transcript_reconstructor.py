"""
Stage 05: Transcript reconstruction and overlap-aware deduplication.
"""

from __future__ import annotations

import json
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Dict, Iterable, List

from ..infrastructure.utils.logger import get_logger

logger = get_logger("transcript_reconstructor")


def _normalize_text(value: str) -> str:
    return " ".join((value or "").lower().split())


def _text_similarity(text1: str, text2: str) -> float:
    s1 = _normalize_text(text1)
    s2 = _normalize_text(text2)
    if not s1 or not s2:
        return 0.0
    return SequenceMatcher(None, s1, s2).ratio()


def _is_duplicate_segment(
    previous: Dict[str, Any],
    current: Dict[str, Any],
) -> bool:
    time_overlap = min(previous["end"], current["end"]) - max(previous["start"], current["start"])
    similarity = _text_similarity(previous["text"], current["text"])
    same_speaker = previous.get("speaker") == current.get("speaker")

    if time_overlap >= 0.25 and similarity >= 0.82 and (same_speaker or time_overlap >= 1.0):
        return True

    if abs(previous["start"] - current["start"]) <= 1.0 and similarity >= 0.92:
        return True

    return False


def _iter_artifacts(chunk_artifacts: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    normalized = list(chunk_artifacts)
    normalized.sort(key=lambda item: item["chunk"]["chunk_index"])
    return normalized


def reconstruct_transcript(
    chunk_artifacts: Iterable[Dict[str, Any]],
    output_file: Path,
    base_filename: str,
    *,
    metadata: Dict[str, Any] | None = None,
) -> Path:
    output_file = Path(output_file)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    artifacts = _iter_artifacts(chunk_artifacts)
    if not artifacts:
        logger.warning(f"No transcript artifacts available for '{base_filename}'.")
        return output_file

    final_segments: List[Dict[str, Any]] = []
    for artifact in artifacts:
        chunk = artifact["chunk"]
        transcript_path = Path(artifact["transcript_path"])
        data = json.loads(transcript_path.read_text(encoding="utf-8"))
        segments = data.get("structured_turns", data.get("segments", []))
        chunk_start = float(chunk["start_sec"])
        chunk_index = int(chunk["chunk_index"])

        for segment in segments:
            text = str(segment.get("text", "")).strip()
            if not text:
                continue

            local_start = float(segment.get("start", segment.get("start_ms", 0) / 1000.0))
            local_end = float(segment.get("end", segment.get("end_ms", 0) / 1000.0))
            if local_end <= local_start:
                continue

            current = {
                "start": round(chunk_start + local_start, 2),
                "end": round(chunk_start + local_end, 2),
                "speaker": segment.get("speaker", "Unknown"),
                "text": text,
                "chunk_ref": chunk_index,
            }

            duplicate_match = None
            for previous in reversed(final_segments[-6:]):
                if _is_duplicate_segment(previous, current):
                    duplicate_match = previous
                    break

            if duplicate_match is not None:
                if len(current["text"]) > len(duplicate_match["text"]):
                    duplicate_match["text"] = current["text"]
                duplicate_match["end"] = max(duplicate_match["end"], current["end"])
                continue

            final_segments.append(current)

    diarized_lines = []
    for segment in final_segments:
        timestamp = f"[{segment['start']:06.2f} - {segment['end']:06.2f}]"
        diarized_lines.append(f"{timestamp} {segment['speaker']}: {segment['text']}")

    full_diarized_text = "\n".join(diarized_lines)
    total_duration = max((segment["end"] for segment in final_segments), default=0.0)
    final_output = {
        "file": base_filename,
        "total_duration_seconds": round(total_duration, 2),
        "segments": final_segments,
        "full_text": " ".join(segment["text"] for segment in final_segments),
        "diarized_html_compatible": full_diarized_text,
    }
    
    if metadata:
        final_output.update(metadata)

    output_file.write_text(json.dumps(final_output, ensure_ascii=False, indent=2), encoding="utf-8")
    output_file.with_suffix(".txt").write_text(full_diarized_text, encoding="utf-8")
    logger.info(f"Successfully reconstructed transcript for '{base_filename}' into '{output_file.name}'.")
    return output_file
