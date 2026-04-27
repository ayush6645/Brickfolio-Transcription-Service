"""
Shared orchestration runner for batch and API transcription flows.
"""

from __future__ import annotations

import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

from ..infrastructure.config import settings as config
from ..infrastructure.utils.audio_hash_registry import registry as hash_registry
from ..infrastructure.utils.environment_validator import AudioValidationError, init_directories, validate_audio_or_raise
from ..infrastructure.utils.logger import get_logger
from ..infrastructure.utils.pipeline_telemetry import record_audio_quality, record_performance
from ..infrastructure.utils.pipeline_tracker import PipelineTracker
from .audio_chunker import ChunkMetadata, chunk_audio
from .audio_preprocessor import PreprocessResult, preprocess_full_file
from .audio_standardizer import standardize_audio
from .audio_transcriber import TranscriptionArtifact, transcribe_chunk
from .transcript_reconstructor import reconstruct_transcript

logger = get_logger("transcription_runner")


@dataclass(frozen=True)
class PipelineResult:
    tracker_id: str
    file_hash: str
    final_json_path: Path
    final_txt_path: Path
    duration_sec: float
    chunk_summary: Dict[str, int]
    provider_summary: Dict[str, int]


class TranscriptionRunner:
    def __init__(self, session_id: str | None = None):
        self.tracker = PipelineTracker()
        self.session_id = session_id

    def _make_file_id(self, input_path: Path, file_hash: str) -> str:
        return f"{input_path.stem}_{file_hash[:12]}"

    def _load_existing_result(self, final_output_path: Path, file_id: str, file_hash: str) -> PipelineResult:
        data = json.loads(final_output_path.read_text(encoding="utf-8"))
        state = self.tracker.get_file_state(file_id)
        provider_summary = state.get("provider_summary", {})
        retries = 0
        for chunk in state.get("chunks", {}).values():
            retries += max(int(chunk.get("validation", {}).get("attempts_used", 1)) - 1, 0)
        chunk_summary = {
            "total_chunks": int(state.get("number_of_chunks", 0)),
            "processed_chunks": len(state.get("processed_chunks", [])),
            "fallback_chunks": sum(
                1
                for chunk in state.get("chunks", {}).values()
                if chunk.get("status") == "fallback_completed"
            ),
            "retry_count": retries,
        }
        return PipelineResult(
            tracker_id=file_id,
            file_hash=file_hash,
            final_json_path=final_output_path,
            final_txt_path=final_output_path.with_suffix(".txt"),
            duration_sec=float(data.get("total_duration_seconds", 0.0)),
            chunk_summary=chunk_summary,
            provider_summary=provider_summary,
        )

    def _process_chunk(
        self,
        *,
        file_id: str,
        chunk: ChunkMetadata,
        transcripts_dir: Path,
    ) -> Dict[str, object]:
        state = self.tracker.get_file_state(file_id)
        chunk_state = state.get("chunks", {}).get(chunk.chunk_name, {})
        existing_transcript = chunk_state.get("transcript_path")
        existing_status = chunk_state.get("status")
        if (
            config.ENABLE_PIPELINE_RESUME
            and existing_status in {"completed", "fallback_completed"}
            and existing_transcript
            and Path(existing_transcript).exists()
        ):
            return {
                "chunk": chunk.to_dict(),
                "transcript_path": existing_transcript,
                "provider": chunk_state.get("provider", "unknown"),
                "fallback_used": existing_status == "fallback_completed",
                "attempts_used": chunk_state.get("validation", {}).get("attempts_used", 1),
            }

        self.tracker.mark_chunk_processing(
            file_id,
            chunk.chunk_name,
            provider=config.PRIMARY_TRANSCRIPTION_PROVIDER,
        )
        try:
            artifact = transcribe_chunk(
                chunk.path,
                transcripts_dir,
                chunk_name=chunk.chunk_name,
                duration_sec=max(chunk.end_sec - chunk.start_sec, 0.0),
                file_id=file_id,
            )
            self.tracker.complete_chunk(
                file_id,
                chunk.chunk_name,
                provider=artifact.provider,
                transcript_path=str(artifact.transcript_path),
                validation=artifact.validation,
                fallback_used=artifact.fallback_used,
            )
            return {
                "chunk": chunk.to_dict(),
                "transcript_path": str(artifact.transcript_path),
                "provider": artifact.provider,
                "fallback_used": artifact.fallback_used,
                "attempts_used": artifact.attempts_used,
            }
        except Exception as exc:
            self.tracker.fail_chunk(
                file_id,
                chunk.chunk_name,
                error_msg=str(exc),
                provider=config.PRIMARY_TRANSCRIPTION_PROVIDER,
            )
            raise

    def run_pipeline(
        self,
        input_path: Path,
        *,
        source: str,
        session_id: str | None = None,
        lead_id: str | None = None,
        agent_id: str | None = None,
        recording_id: str | None = None,
    ) -> PipelineResult:
        init_directories()
        input_path = Path(input_path)
        pipeline_started_at = time.perf_counter()
        file_hash = hash_registry.compute_file_hash(input_path)
        file_id = self._make_file_id(input_path, file_hash)
        active_session_id = session_id or self.session_id

        self.tracker.init_file(
            file_id,
            file_hash=file_hash,
            source_path=str(input_path),
            source=source,
            input_filename=input_path.name,
            session_id=active_session_id,
            lead_id=lead_id,
            agent_id=agent_id,
            recording_id=recording_id,
        )

        final_json_output = config.FINAL_DIR / f"{input_path.stem}_final.json"
        registration = hash_registry.prepare_processing(file_hash, input_path, file_id)
        if not registration.should_process and registration.final_output_path:
            existing_output = Path(registration.final_output_path)
            if existing_output.exists():
                logger.info("Duplicate audio detected for '%s'; returning existing artifact.", input_path.name)
                return self._load_existing_result(existing_output, file_id, file_hash)

        current_stage = "validating"
        self.tracker.start_stage(file_id, current_stage)
        try:
            validation_info = validate_audio_or_raise(input_path)
            self.tracker.set_total_audio_duration(file_id, validation_info.duration_sec)
            self.tracker.complete_stage(file_id, current_stage, details=validation_info.to_dict())

            current_stage = "standardized"
            self.tracker.start_stage(file_id, current_stage)
            standardized_path = config.STANDARDIZED_AUDIO_DIR / f"{file_id}_std.wav"
            standardized_path = standardize_audio(input_path, standardized_path)
            self.tracker.complete_stage(
                file_id,
                current_stage,
                details={"standardized_path": str(standardized_path)},
            )

            current_stage = "cleaned"
            self.tracker.start_stage(file_id, current_stage)
            preprocess_result = preprocess_full_file(standardized_path, config.CLEANED_DIR / file_id)
            processed_audio_path = preprocess_result.output_path
            self.tracker.complete_stage(
                file_id,
                current_stage,
                details=preprocess_result.to_dict(),
            )
            if preprocess_result.snr_db is not None:
                record_audio_quality(
                    file_id,
                    {
                        "file_name": input_path.name,
                        "snr_db": preprocess_result.snr_db,
                        "clipping_rate": preprocess_result.clipping_rate,
                        "voice_percentage": preprocess_result.speech_ratio,
                        "restoration_profile_used": preprocess_result.restoration_profile,
                    },
                )

            current_stage = "chunked"
            self.tracker.start_stage(file_id, current_stage)
            chunks = chunk_audio(processed_audio_path, config.CHUNKS_DIR / file_id)
            self.tracker.set_chunks(file_id, [chunk.to_dict() for chunk in chunks])
            self.tracker.complete_stage(
                file_id,
                current_stage,
                details={"chunk_count": len(chunks)},
            )

            current_stage = "transcribing"
            self.tracker.start_stage(file_id, current_stage)
            transcripts_dir = config.TRANSCRIPTS_DIR / file_id
            transcript_artifacts: List[Dict[str, object]] = []
            with ThreadPoolExecutor(max_workers=min(config.MAX_CONCURRENT_CHUNKS, len(chunks) or 1)) as executor:
                futures = {
                    executor.submit(
                        self._process_chunk,
                        file_id=file_id,
                        chunk=chunk,
                        transcripts_dir=transcripts_dir,
                    ): chunk
                    for chunk in chunks
                }
                for future in as_completed(futures):
                    transcript_artifacts.append(future.result())
            transcript_artifacts.sort(key=lambda item: int(item["chunk"]["chunk_index"]))
            provider_summary: Dict[str, int] = {}
            total_attempts = 0
            for artifact in transcript_artifacts:
                provider = str(artifact["provider"])
                provider_summary[provider] = provider_summary.get(provider, 0) + 1
                total_attempts += int(artifact.get("attempts_used", 1))
            self.tracker.set_provider_summary(file_id, provider_summary)
            
            # Aggregate metrics for dashboard
            total_latency_ms = 0
            total_tokens_in = 0
            total_tokens_out = 0
            for item in transcript_artifacts:
                total_latency_ms += int(item.get("latency_ms", 0))
                total_tokens_in += int(item.get("tokens_in", 0))
                total_tokens_out += int(item.get("tokens_out", 0))

            self.tracker.record_metrics(
                file_id,
                {
                    "total_tokens_in": total_tokens_in,
                    "total_tokens_out": total_tokens_out,
                    "provider_latency_ms": total_latency_ms,
                    "retry_count": max(total_attempts - len(transcript_artifacts), 0),
                },
            )

            self.tracker.complete_stage(
                file_id,
                current_stage,
                details={"provider_summary": provider_summary, "attempts_used": total_attempts},
            )

            # Stage 05: Reconstruct
            current_stage = "reconstructing"
            self.tracker.start_stage(file_id, current_stage)
            
            # Prepare metadata for final JSON
            file_state = self.tracker.get_file_state(file_id)
            metadata_for_json = {
                "file_id": file_id,
                "lead_id": file_state.get("lead_id"),
                "agent_id": file_state.get("agent_id"),
                "recording_id": file_state.get("recording_id"),
                "status": "completed",
                "metrics": file_state.get("metrics"),
            }

            reconstruct_transcript(
                transcript_artifacts,
                final_json_output,
                input_path.stem,
                metadata=metadata_for_json
            )
            self.tracker.set_final_output(file_id, final_json_output)
            self.tracker.complete_stage(
                file_id,
                current_stage,
                details={"final_output_path": str(final_json_output)},
            )

            self.tracker.update_status(file_id, "completed")
            hash_registry.mark_completed(file_hash, file_id, final_json_output)

            total_runtime_sec = time.perf_counter() - pipeline_started_at
            chunk_summary = {
                "total_chunks": len(chunks),
                "processed_chunks": len(transcript_artifacts),
                "fallback_chunks": sum(1 for artifact in transcript_artifacts if artifact["fallback_used"]),
                "retry_count": max(total_attempts - len(transcript_artifacts), 0),
            }
            
            self.tracker.record_metrics(
                file_id,
                {
                    "total_processing_time_ms": int(total_runtime_sec * 1000),
                },
            )

            record_performance(
                {
                    "file_id": file_id,
                    "file_name": input_path.name,
                    "audio_duration_sec": round(validation_info.duration_sec, 3),
                    "pipeline_runtime_sec": round(total_runtime_sec, 3),
                    "rtf_score": round(total_runtime_sec / max(validation_info.duration_sec, 0.001), 4),
                    "chunk_count": len(chunks),
                    "retry_count": chunk_summary["retry_count"],
                    "fallback_chunks": chunk_summary["fallback_chunks"],
                    "providers": ",".join(f"{name}:{count}" for name, count in sorted(provider_summary.items())),
                }
            )

            logger.info(f"Pipeline complete for '{input_path.name}' -> '{final_json_output.name}'.")
            return PipelineResult(
                tracker_id=file_id,
                file_hash=file_hash,
                final_json_path=final_json_output,
                final_txt_path=final_json_output.with_suffix(".txt"),
                duration_sec=validation_info.duration_sec,
                chunk_summary=chunk_summary,
                provider_summary=provider_summary,
            )
        except Exception as exc:
            error_message = str(exc)
            logger.error(f"Pipeline failed for '{input_path.name}' during stage '{current_stage}': {error_message}")
            if isinstance(exc, AudioValidationError):
                self.tracker.fail_stage(file_id, "validating", error_message, error_code="INVALID_AUDIO")
            else:
                self.tracker.fail_stage(file_id, current_stage, error_message, error_code="PIPELINE_CRASH")
            self.tracker.log_error(file_id, error_message)
            hash_registry.mark_failed(file_hash, file_id, error_message)
            raise


def run_transcription(
    file_path: Path,
    *,
    source: str = "batch",
    session_id: str | None = None,
    lead_id: str | None = None,
    agent_id: str | None = None,
    recording_id: str | None = None,
) -> Path:
    runner = TranscriptionRunner(session_id=session_id)
    result = runner.run_pipeline(
        file_path,
        source=source,
        session_id=session_id,
        lead_id=lead_id,
        agent_id=agent_id,
        recording_id=recording_id,
    )
    return result.final_json_path
