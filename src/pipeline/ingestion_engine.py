"""
Audio Ingestion Engine

This is the central entry point for the "Audio Database" input.
It abstracts the source of audio files and orchestrates the initial 
stages of the pipeline (deduplication, state initialization).
"""

from pathlib import Path
from typing import List, Optional, Type
import sys

# Ensure internal modules are discoverable
from ..infrastructure.config import settings as config
from ..infrastructure.adapters.base import AudioSource, AudioFileMetadata
from ..infrastructure.adapters.local_source import LocalFolderSource
from ..infrastructure.utils.audio_hash_registry import registry as hash_registry
from ..infrastructure.utils.pipeline_tracker import PipelineTracker
from ..infrastructure.utils.logger import get_logger

logger = get_logger("ingestion_engine")

class IngestionEngine:
    """
    Orchestrates the discovery and registration of audio files.
    """
    
    def __init__(self, source: Optional[AudioSource] = None):
        """
        Initializes the engine with a specific source.
        If no source is provided, it uses the default from settings.
        """
        self.tracker = PipelineTracker()
        self.source = source or self._get_default_source()
        logger.info(f"Ingestion Engine initialized with source: {self.source.get_source_identifier()}")

    def _get_default_source(self) -> AudioSource:
        """Factory method to create the default source based on config."""
        source_type = config.ACTIVE_AUDIO_SOURCE.lower()
        if source_type == "local":
            return LocalFolderSource()
        # Add future sources here (e.g., S3, API)
        else:
            logger.error(f"Unsupported source type: {source_type}. Falling back to local.")
            return LocalFolderSource()

    def ingest_new_files(self) -> List[AudioFileMetadata]:
        """
        Scans the source, filters duplicates, and registers new files in the tracker.
        
        Returns:
            List of metadata for newly registered files.
        """
        all_files = self.source.list_files()
        newly_registered = []

        for file_meta in all_files:
            file_id = file_meta.filename # Using filename as ID for now, can be hash-based
            
            # 1. Deduplication Check (File Content Hash)
            is_duplicate = hash_registry.check_and_register(file_meta.file_path)
            
            if is_duplicate:
                logger.debug(f"Skipping duplicate file: {file_meta.filename}")
                continue
                
            # 2. Register in Pipeline Tracker
            self.tracker.init_file(file_id)
            self.tracker.update_stage_status(file_id, "ingestion", "completed")
            
            logger.info(f"Successfully ingested: {file_meta.filename}")
            newly_registered.append(file_meta)
            
        return newly_registered

    def run_full_pipeline_on_new(self):
        """
        Scans for new files and executes the full transcription pipeline for each.
        """
        from .transcription_runner import run_transcription
        
        new_files = self.ingest_new_files()
        if not new_files:
            logger.info("No new files found to process.")
            return
            
        logger.info(f"Triggering pipeline for {len(new_files)} new files...")
        
        for file_meta in new_files:
            try:
                run_transcription(file_meta.file_path)
            except Exception as e:
                logger.error(f"Failed to process {file_meta.filename}: {e}")

# Global instance for easy use as a singleton entry point
engine = IngestionEngine()

def get_ingestion_endpoint() -> IngestionEngine:
    """Returns the primary ingestion engine instance."""
    return engine
