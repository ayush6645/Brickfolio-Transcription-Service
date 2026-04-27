"""
Stage 05: Transcript Reconstruction and Deduplication

This stage merges multiple diarized transcript fragments back into a single 
unified document. It handles the complex logic of resolving overlaps 
(where the end of one chunk contains the beginning of the next).

Algorithm:
1. Sorts chunks chronologically using integer-based index extraction.
2. Identifies overlap regions based on global timestamps.
3. Uses difflib.SequenceMatcher to fuzzy-match spoken text in overlap buffers.
4. Deduplicates matching segments while preserving speaker consistency.
5. Generates both structured JSON and human-readable text diarized reports.
"""

import json
import re
import sys
from difflib import SequenceMatcher
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Ensure internal modules are discoverable
sys.path.append(str(Path(__file__).parent.parent))
from ..infrastructure.config import settings as config
from ..infrastructure.utils.logger import get_logger

# Initialize specialized logger for the reconstruction logic
logger = get_logger("transcript_reconstructor")

def is_similar_text(text1: str, text2: str) -> bool:
    """
    Determines if two text strings are fundamentally describing the same speech.
    Uses SequenceMatcher to handle minor phonetic variations or timing gaps.

    Args:
        text1: First transcript segment text.
        text2: Second transcript segment text.

    Returns:
        bool: True if the overlap is significant enough to be a duplicate.
    """
    # Normalize for comparison: lowercase and single-spaced
    s1 = " ".join(text1.lower().split())
    s2 = " ".join(text2.lower().split())
    
    if not s1 or not s2: 
        return False
        
    matcher = SequenceMatcher(None, s1, s2)
    
    # Find the longest contiguous matching block between the two fragments
    match = matcher.find_longest_match(0, len(s1), 0, len(s2))
    
    # We consider it a duplicate if the shared block is >60% of the shorter string
    shorter_len = min(len(s1), len(s2))
    if match.size >= (shorter_len * 0.6):
        return True
    return False

def reconstruct_transcript(json_dir: Path, output_file: Path, base_filename: str) -> Path:
    """
    Aggregates chunk-level transcripts into a master lead interaction document.

    Args:
        json_dir: Directory containing individual chunk JSONs.
        output_file: Target path for the final reconstructed JSON.
        base_filename: Original audio name used to filter artifacts.

    Returns:
        Path: The file path to the final reconstructed transcript.
    """
    json_dir = Path(json_dir)
    output_file = Path(output_file)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        logger.info(f"Reconstructing unified timeline for '{base_filename}'...")
        
        # Locate all processed fragments for this specific file
        chunk_files_raw = list(json_dir.glob(f"{base_filename}_chunk_*_transcript.json"))
        
        if not chunk_files_raw:
            logger.warning(f"No processed transcript chunks found in {json_dir}. Reconstruction aborted.")
            return output_file
            
        # Extract integer indices to ensure absolute numerical sorting order (e.g., 9 before 10)
        files_with_idx: List[Tuple[int, Path]] = []
        for file_path in chunk_files_raw:
            match = re.search(r"_chunk_(\d+)_transcript", file_path.stem)
            if match:
                files_with_idx.append((int(match.group(1)), file_path))
                
        files_with_idx.sort(key=lambda x: x[0])
        
        # Constants for global timestamp alignment
        step_s = (config.CHUNK_LENGTH_MS - config.OVERLAP_MS) / 1000.0
        
        final_segments: List[Dict[str, Any]] = []
        last_global_end = 0.0
        
        for chunk_idx, file_path in files_with_idx:
            global_offset = chunk_idx * step_s
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # 'structured_turns' is the modern schema from Stage 04
            segments = data.get("structured_turns", data.get("segments", []))
            
            for seg in segments:
                # Calculate absolute time in the master recording
                # Handles both 'start/end' (seconds) and 'start_ms/end_ms'
                seg_start = seg.get("start", seg.get("start_ms", 0) / 1000.0)
                seg_end = seg.get("end", seg.get("end_ms", 0) / 1000.0)
                
                global_start = global_offset + seg_start
                global_end = global_offset + seg_end
                text = seg.get("text", "").strip()
                
                if not text:
                    continue

                # Deduplication logic for overlapping windows
                is_duplicate = False
                if global_start < last_global_end:
                    # Look back at recently added segments to see if we've already heard this
                    for prev_seg in reversed(final_segments[-5:]):
                        if global_start < prev_seg["end"] and is_similar_text(text, prev_seg["text"]):
                            is_duplicate = True
                            break
                            
                if not is_duplicate:
                    final_segments.append({
                        "start": round(global_start, 2),
                        "end": round(global_end, 2),
                        "speaker": seg.get("speaker", "Unknown"),
                        "text": text,
                        "chunk_ref": chunk_idx
                    })
                    last_global_end = max(last_global_end, global_end)

        # Generate Human-Readable diarized text report
        diarized_lines = []
        for seg in final_segments:
            timestamp = f"[{seg['start']:06.2f} - {seg['end']:06.2f}]"
            diarized_lines.append(f"{timestamp} {seg['speaker']}: {seg['text']}")
            
        full_diarized_text = "\n".join(diarized_lines)
        
        # Build final artifact
        final_output = {
            "file": base_filename,
            "total_duration_seconds": round(last_global_end, 2),
            "segments": final_segments,
            "full_text": " ".join([s["text"] for s in final_segments]),
            "diarized_html_compatible": full_diarized_text
        }
        
        # Save JSON for programmatic access (Frontend/Database)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(final_output, f, ensure_ascii=False, indent=2)
            
        # Save TXT for manager logs
        txt_output_file = output_file.with_suffix('.txt')
        with open(txt_output_file, 'w', encoding='utf-8') as f:
            f.write(full_diarized_text)
            
        logger.info(f"Successfully reconstructed timeline into '{output_file.name}' with fuzzy deduplication.")
        return output_file
        
    except Exception as e:
        logger.error(f"Critical error during timeline reconstruction for '{base_filename}': {e}")
        raise
