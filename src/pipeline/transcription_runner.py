"""
Transcription Runner (Master Orchestrator)

This module handles the simplified, focus-driven pipeline:
1. Standardization (FFmpeg)
2. Chunking (For long files)
3. Transcription (Gemini Multimodal)
4. Reconstruction (Merging segments)
5. Cleanup

Goal: Audio Input -> JSON "Subtitle" Data.
"""

import os
import shutil
from pathlib import Path
from typing import List, Optional
import sys

# Ensure internal modules are discoverable
from ..infrastructure.config import settings as config
from ..infrastructure.utils.logger import get_logger
from ..infrastructure.utils.pipeline_tracker import PipelineTracker

# Stage Imports
from . import audio_standardizer as standardizer
from . import audio_chunker as chunker
from . import audio_transcriber as transcriber
from . import transcript_reconstructor as reconstructor

logger = get_logger("transcription_runner")

class TranscriptionRunner:
    """
    Coordinates the end-to-end transcription process for a single audio file.
    """
    
    def __init__(self, session_id: Optional[str] = None):
        self.tracker = PipelineTracker()
        self.session_id = session_id or "default_session"

    def run_pipeline(self, input_path: Path) -> Path:
        """
        Runs the full transcription pipeline on a single file.
        
        Args:
            input_path: Path to the raw audio file.
            
        Returns:
            Path to the final JSON output.
        """
        input_path = Path(input_path)
        base_name = input_path.stem
        file_id = input_path.name
        
        logger.info(f"--- Starting Pipeline for: {file_id} ---")
        
        # 1. Standardization
        std_path = config.STANDARDIZED_AUDIO_DIR / f"{base_name}_std.wav"
        standardizer.standardize_audio(input_path, std_path)
        self.tracker.update_stage_status(file_id, "standardization", "completed")
        
        # 2. Chunking (Check if needed)
        # We'll use the chunker to split it if it exceeds the threshold
        chunks_output_dir = config.CHUNKS_DIR / base_name
        chunk_files = chunker.chunk_audio(std_path, chunks_output_dir)
        
        if not chunk_files:
             # If chunk_audio returned empty (e.g. error), or we just want to treat it as one chunk
             chunk_files = [std_path]
             is_chunked = False
        else:
             is_chunked = True
        
        self.tracker.set_chunks_total(file_id, len(chunk_files))
        
        # 3. Transcription (Per Chunk)
        transcripts_dir = config.TRANSCRIPTS_DIR / base_name
        transcripts_dir.mkdir(parents=True, exist_ok=True)
        
        for idx, chunk_path in enumerate(chunk_files):
            logger.info(f"Transcribing chunk {idx+1}/{len(chunk_files)}: {chunk_path.name}")
            # The transcriber saves its own output in the dir
            transcriber.transcribe_full_audio(chunk_path, transcripts_dir)
            self.tracker.add_processed_chunk(file_id, chunk_path.name)
            
        # 4. Reconstruction
        final_json_output = config.FINAL_DIR / f"{base_name}_final.json"
        reconstructor.reconstruct_transcript(transcripts_dir, final_json_output, base_name)
        
        self.tracker.update_status(file_id, "completed")
        logger.info(f"--- Pipeline Complete: {final_json_output} ---")
        
        return final_json_output

def run_transcription(file_path: Path) -> Path:
    """Entry point for running transcription on a single file."""
    runner = TranscriptionRunner()
    return runner.run_pipeline(file_path)
