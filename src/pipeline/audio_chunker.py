"""
Stage 02: Audio Chunking (Segmentation)

This stage splits long-form standardized audio files into smaller, overlapping 
segments. This is necessary because:
1. LLM contexts have practical attention limits for high-fidelity audio logic.
2. Parallelizing transcription requires manageable file fragments.
3. Overlap (e.g., 5 seconds) ensures that words spoken at the split point 
   are captured fully in at least one segment.

Uses pydub for millisecond-precision audio slicing.
"""

import os
import math
import sys
from pathlib import Path
from typing import List

from pydub import AudioSegment

# Ensure internal modules are discoverable
sys.path.append(str(Path(__file__).parent.parent))
from ..infrastructure.config import settings as config
from ..infrastructure.utils.logger import get_logger

# Initialize stage-specific logger
logger = get_logger("audio_chunker")

def chunk_audio(input_file_path: Path, output_dir: Path) -> List[Path]:
    """
    Slices an audio file into manageable segments with defined overlap.

    Args:
        input_file_path: Path to the standardized WAV recording.
        output_dir: Directory where fragments will be saved.

    Returns:
        List[Path]: A list of file paths to the generated chunks.

    Raises:
        RuntimeError: If audio loading or export fails.
    """
    input_file_path = Path(input_file_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        logger.info(f"Segmenting '{input_file_path.name}' -> {output_dir.name} [Target: {config.CHUNK_LENGTH_MS/1000}s fragments]")
        
        # Load audio into memory. Note: Ensure TARGET_CHANNELS is Mono to keep RAM usage low.
        audio = AudioSegment.from_file(input_file_path)
        
        chunk_length = config.CHUNK_LENGTH_MS
        overlap = config.OVERLAP_MS
        step = chunk_length - overlap # How far we move the 'window' each time
        
        total_length = len(audio)
        chunk_paths = []
        
        # Scenario A: Audio is already shorter than or equal to the target chunk size
        if total_length <= chunk_length:
            output_file = output_dir / f"{input_file_path.stem}_chunk_000.wav"
            audio.export(output_file, format=config.TARGET_FORMAT)
            chunk_paths.append(output_file)
            logger.info("Recording is short. Created 1 single fragment.")
            return chunk_paths
    
        # Scenario B: Audio requires multi-part segmentation
        num_chunks = math.ceil((total_length - overlap) / step)
        
        for i in range(num_chunks):
            start_ms = i * step
            end_ms = start_ms + chunk_length
            
            # Bound the window to the actual audio length
            if end_ms > total_length:
                end_ms = total_length
                
            # Quality Check: Skip the final tail if it's virtually silent/tiny (< 1s)
            # This prevents AI hallucinations on very short residual noise.
            if i == num_chunks - 1 and (end_ms - start_ms) < 1000 and num_chunks > 1:
                logger.debug(f"Discarding negligible tail fragment: chunk_{i:03d}")
                break
                
            chunk = audio[start_ms:end_ms]
            output_file = output_dir / f"{input_file_path.stem}_chunk_{i:03d}.wav"
            
            # Export the slice to the results directory
            chunk.export(output_file, format=config.TARGET_FORMAT)
            chunk_paths.append(output_file)
            
        logger.info(f"Generated {len(chunk_paths)} fragments for pipeline consumption.")
        return chunk_paths
        
    except Exception as e:
        logger.error(f"Critical error during audio segmentation for {input_file_path.name}: {e}")
        raise
