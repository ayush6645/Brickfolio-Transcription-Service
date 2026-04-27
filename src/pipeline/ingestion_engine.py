"""
Audio ingestion engine for batch folder processing.
"""

from __future__ import annotations

from typing import List, Optional

from ..infrastructure.adapters.base import AudioFileMetadata, AudioSource
from ..infrastructure.adapters.local_source import LocalFolderSource
from ..infrastructure.config import settings as config
from ..infrastructure.utils.audio_hash_registry import registry as hash_registry
from ..infrastructure.utils.environment_validator import is_valid_audio
from ..infrastructure.utils.logger import get_logger
from ..infrastructure.utils.pipeline_tracker import PipelineTracker

logger = get_logger("ingestion_engine")


class IngestionEngine:
    def __init__(self, source: Optional[AudioSource] = None):
        self.tracker = PipelineTracker()
        self.source = source or self._get_default_source()
        logger.info(f"Ingestion Engine initialized with source: {self.source.get_source_identifier()}")

    def _get_default_source(self) -> AudioSource:
        source_type = config.ACTIVE_AUDIO_SOURCE.lower()
        if source_type == "local":
            return LocalFolderSource()
        logger.error(f"Unsupported source type '{source_type}'. Falling back to local.")
        return LocalFolderSource()

    def ingest_new_files(self) -> List[AudioFileMetadata]:
        discovered_files = self.source.list_files()
        newly_registered: List[AudioFileMetadata] = []

        for file_meta in discovered_files:
            if not is_valid_audio(file_meta.file_path):
                logger.warning(f"Skipping invalid audio file during ingestion: {file_meta.filename}")
                continue

            file_hash = hash_registry.compute_file_hash(file_meta.file_path)
            file_id = f"{file_meta.file_path.stem}_{file_hash[:12]}"
            registration = hash_registry.prepare_processing(file_hash, file_meta.file_path, file_id)
            if not registration.should_process:
                logger.info(f"Skipping duplicate completed file: {file_meta.filename}")
                continue

            file_meta.additional_meta["file_hash"] = file_hash
            file_meta.additional_meta["file_id"] = file_id
            self.tracker.init_file(
                file_id,
                file_hash=file_hash,
                source_path=str(file_meta.file_path),
                source=self.source.get_source_identifier(),
                input_filename=file_meta.filename,
            )
            logger.info(f"Queued file for processing: {file_meta.filename}")
            newly_registered.append(file_meta)

        return newly_registered

    def run_full_pipeline_on_new(self) -> None:
        from .transcription_runner import TranscriptionRunner

        new_files = self.ingest_new_files()
        if not new_files:
            logger.info("No new files found to process.")
            return

        runner = TranscriptionRunner()
        logger.info(f"Triggering pipeline for {len(new_files)} new files.")
        for file_meta in new_files:
            try:
                runner.run_pipeline(
                    file_meta.file_path,
                    source=self.source.get_source_identifier(),
                )
            except Exception as exc:
                logger.error(f"Failed to process {file_meta.filename}: {exc}")


engine = IngestionEngine()


def get_ingestion_endpoint() -> IngestionEngine:
    return engine
