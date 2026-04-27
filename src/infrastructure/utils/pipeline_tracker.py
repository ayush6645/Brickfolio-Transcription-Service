"""
Persistent tracker for pipeline state, checkpoints, and chunk progress.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List

import portalocker

from ..config import settings as config


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sanitize_for_json(data: Any) -> Any:
    """Recursively converts numpy types to standard Python types for JSON serialization."""
    if isinstance(data, dict):
        return {k: _sanitize_for_json(v) for k, v in data.items()}
    if isinstance(data, list):
        return [_sanitize_for_json(v) for v in data]
    if hasattr(data, "item") and callable(getattr(data, "item")):
        # Handles numpy.bool_, numpy.int64, etc.
        return data.item()
    return data


class PipelineTracker:
    """Stores resumable pipeline state in JSON with file locking."""

    def __init__(self) -> None:
        config.METADATA_DIR.mkdir(parents=True, exist_ok=True)
        self.state_file = config.PIPELINE_STATE_FILE

    def _update_locked(self, mutator):
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        with portalocker.Lock(self.state_file, mode="a+", timeout=10, encoding="utf-8") as handle:
            handle.seek(0)
            content = handle.read()
            data = json.loads(content) if content.strip() else {}
            result = mutator(data)
            data = _sanitize_for_json(data)
            handle.seek(0)
            handle.truncate()
            json.dump(data, handle, indent=2, ensure_ascii=False)
            handle.flush()
            return result

    def _read_locked(self) -> Dict[str, Any]:
        if not self.state_file.exists():
            return {}
        with portalocker.Lock(self.state_file, mode="r", timeout=10, encoding="utf-8") as handle:
            content = handle.read()
            return json.loads(content) if content.strip() else {}

    def _default_state(
        self,
        file_id: str,
        *,
        file_hash: str | None = None,
        source_path: str | None = None,
        source: str | None = None,
        input_filename: str | None = None,
        session_id: str | None = None,
        lead_id: str | None = None,
        agent_id: str | None = None,
        recording_id: str | None = None,
    ) -> Dict[str, Any]:
        now = _utc_now()
        return {
            "file_id": file_id,
            "file_hash": file_hash,
            "lead_id": lead_id,
            "agent_id": agent_id,
            "recording_id": recording_id,
            "input_filename": input_filename,
            "source": source,
            "source_path": source_path,
            "session_id": session_id,
            "status": "queued",
            "current_stage": "queued",
            "total_audio_duration_sec": 0.0,
            "number_of_chunks": 0,
            "processed_chunks": [],
            "error_logs": [],
            "error_structured": None,
            "final_output_path": None,
            "created_at": now,
            "updated_at": now,
            "stages": {},
            "chunks": {},
            "checkpoint": {"stage": "queued", "chunk": None},
            "metrics": {
                "total_processing_time_ms": 0,
                "total_tokens_in": 0,
                "total_tokens_out": 0,
                "total_cost_usd": 0.0,
                "provider_latency_ms": 0,
                "retry_count": 0,
            },
        }

    def init_file(
        self,
        file_id: str,
        *,
        file_hash: str | None = None,
        source_path: str | None = None,
        source: str | None = None,
        input_filename: str | None = None,
        session_id: str | None = None,
        lead_id: str | None = None,
        agent_id: str | None = None,
        recording_id: str | None = None,
    ) -> None:
        def mutate(data: Dict[str, Any]) -> None:
            state = data.get(file_id) or self._default_state(
                file_id,
                file_hash=file_hash,
                source_path=source_path,
                source=source,
                input_filename=input_filename,
                session_id=session_id,
                lead_id=lead_id,
                agent_id=agent_id,
                recording_id=recording_id,
            )
            state["file_hash"] = file_hash or state.get("file_hash")
            state["source_path"] = source_path or state.get("source_path")
            state["source"] = source or state.get("source")
            state["input_filename"] = input_filename or state.get("input_filename")
            state["session_id"] = session_id or state.get("session_id")
            state["lead_id"] = lead_id or state.get("lead_id")
            state["agent_id"] = agent_id or state.get("agent_id")
            state["recording_id"] = recording_id or state.get("recording_id")
            state["updated_at"] = _utc_now()
            data[file_id] = state

        self._update_locked(mutate)

    def get_file_state(self, file_id: str) -> Dict[str, Any]:
        return self._read_locked().get(file_id, {})

    def update_status(self, file_id: str, status: str) -> None:
        def mutate(data: Dict[str, Any]) -> None:
            state = data.setdefault(file_id, self._default_state(file_id))
            state["status"] = status
            state["checkpoint"]["stage"] = status
            state["updated_at"] = _utc_now()

        self._update_locked(mutate)

    def set_total_audio_duration(self, file_id: str, duration_sec: float) -> None:
        def mutate(data: Dict[str, Any]) -> None:
            state = data.setdefault(file_id, self._default_state(file_id))
            state["total_audio_duration_sec"] = round(float(duration_sec), 3)
            state["updated_at"] = _utc_now()

        self._update_locked(mutate)

    def start_stage(self, file_id: str, stage: str, details: Dict[str, Any] | None = None) -> None:
        def mutate(data: Dict[str, Any]) -> None:
            state = data.setdefault(file_id, self._default_state(file_id))
            now = _utc_now()
            stage_state = state["stages"].setdefault(stage, {})
            stage_state.update(
                {
                    "status": "processing",
                    "started_at": stage_state.get("started_at") or now,
                    "completed_at": None,
                    "error": None,
                }
            )
            if details:
                stage_state["details"] = {**stage_state.get("details", {}), **details}
            state["status"] = stage
            state["current_stage"] = stage
            state["checkpoint"] = {"stage": stage, "chunk": state.get("checkpoint", {}).get("chunk")}
            state["updated_at"] = now

        self._update_locked(mutate)

    def complete_stage(self, file_id: str, stage: str, details: Dict[str, Any] | None = None) -> None:
        def mutate(data: Dict[str, Any]) -> None:
            state = data.setdefault(file_id, self._default_state(file_id))
            now = _utc_now()
            stage_state = state["stages"].setdefault(stage, {})
            started_at = stage_state.get("started_at")
            duration_sec = None
            if started_at:
                duration_sec = max(
                    0.0,
                    (datetime.fromisoformat(now) - datetime.fromisoformat(started_at)).total_seconds(),
                )
            stage_state.update(
                {
                    "status": "completed",
                    "completed_at": now,
                    "duration_sec": round(duration_sec, 3) if duration_sec is not None else None,
                    "error": None,
                }
            )
            if details:
                stage_state["details"] = {**stage_state.get("details", {}), **details}
            state["checkpoint"] = {"stage": stage, "chunk": None}
            state["updated_at"] = now

        self._update_locked(mutate)

    def fail_stage(self, file_id: str, stage: str, error_msg: str, error_code: str | None = None) -> None:
        def mutate(data: Dict[str, Any]) -> None:
            state = data.setdefault(file_id, self._default_state(file_id))
            now = _utc_now()
            stage_state = state["stages"].setdefault(stage, {})
            stage_state.update(
                {
                    "status": "failed",
                    "completed_at": now,
                    "error": error_msg,
                    "error_code": error_code,
                }
            )
            state["status"] = "failed"
            state["current_stage"] = stage
            state["checkpoint"] = {"stage": stage, "chunk": state.get("checkpoint", {}).get("chunk")}
            state["error_logs"].append(error_msg)
            state["error_structured"] = {
                "error_code": error_code or "PIPELINE_ERROR",
                "error_message": error_msg,
                "stage": stage,
            }
            state["updated_at"] = now

        self._update_locked(mutate)

    def update_stage_status(self, file_id: str, stage: str, status: str) -> None:
        if status == "completed":
            self.complete_stage(file_id, stage)
        elif status == "failed":
            self.fail_stage(file_id, stage, f"{stage} failed")
        else:
            self.start_stage(file_id, stage)

    def set_chunks(self, file_id: str, chunks: Iterable[Dict[str, Any]]) -> None:
        chunk_list = list(chunks)

        def mutate(data: Dict[str, Any]) -> None:
            state = data.setdefault(file_id, self._default_state(file_id))
            existing = state.setdefault("chunks", {})
            for chunk in chunk_list:
                chunk_name = chunk["chunk_name"]
                existing_chunk = existing.get(chunk_name, {})
                existing[chunk_name] = {
                    **existing_chunk,
                    **chunk,
                    "status": existing_chunk.get("status", "pending"),
                    "retries": existing_chunk.get("retries", 0),
                    "provider": existing_chunk.get("provider"),
                    "transcript_path": existing_chunk.get("transcript_path"),
                    "validation": existing_chunk.get("validation"),
                    "error": existing_chunk.get("error"),
                    "updated_at": _utc_now(),
                }
            state["number_of_chunks"] = len(chunk_list)
            state["updated_at"] = _utc_now()

        self._update_locked(mutate)

    def set_chunks_total(self, file_id: str, total_chunks: int) -> None:
        def mutate(data: Dict[str, Any]) -> None:
            state = data.setdefault(file_id, self._default_state(file_id))
            state["number_of_chunks"] = total_chunks
            state["updated_at"] = _utc_now()

        self._update_locked(mutate)

    def mark_chunk_processing(self, file_id: str, chunk_name: str, provider: str) -> None:
        def mutate(data: Dict[str, Any]) -> None:
            state = data.setdefault(file_id, self._default_state(file_id))
            chunk = state.setdefault("chunks", {}).setdefault(chunk_name, {"chunk_name": chunk_name})
            chunk["status"] = "processing"
            chunk["provider"] = provider
            chunk["updated_at"] = _utc_now()
            state["checkpoint"] = {"stage": "transcribing", "chunk": chunk_name}
            state["updated_at"] = _utc_now()

        self._update_locked(mutate)

    def increment_chunk_retry(self, file_id: str, chunk_name: str) -> None:
        def mutate(data: Dict[str, Any]) -> None:
            state = data.setdefault(file_id, self._default_state(file_id))
            chunk = state.setdefault("chunks", {}).setdefault(chunk_name, {"chunk_name": chunk_name})
            chunk["retries"] = int(chunk.get("retries", 0)) + 1
            chunk["updated_at"] = _utc_now()
            state["updated_at"] = _utc_now()

        self._update_locked(mutate)

    def complete_chunk(
        self,
        file_id: str,
        chunk_name: str,
        *,
        provider: str,
        transcript_path: str,
        validation: Dict[str, Any] | None = None,
        fallback_used: bool = False,
    ) -> None:
        def mutate(data: Dict[str, Any]) -> None:
            state = data.setdefault(file_id, self._default_state(file_id))
            chunk = state.setdefault("chunks", {}).setdefault(chunk_name, {"chunk_name": chunk_name})
            chunk["status"] = "fallback_completed" if fallback_used else "completed"
            chunk["provider"] = provider
            chunk["transcript_path"] = transcript_path
            if validation is not None:
                chunk["validation"] = validation
            chunk["error"] = None
            chunk["updated_at"] = _utc_now()
            processed_chunks: List[str] = state.setdefault("processed_chunks", [])
            if chunk_name not in processed_chunks:
                processed_chunks.append(chunk_name)
            state["updated_at"] = _utc_now()

        self._update_locked(mutate)

    def add_processed_chunk(self, file_id: str, chunk_name: str) -> None:
        self.complete_chunk(file_id, chunk_name, provider="unknown", transcript_path="", validation=None)

    def fail_chunk(self, file_id: str, chunk_name: str, error_msg: str, provider: str | None = None) -> None:
        def mutate(data: Dict[str, Any]) -> None:
            state = data.setdefault(file_id, self._default_state(file_id))
            chunk = state.setdefault("chunks", {}).setdefault(chunk_name, {"chunk_name": chunk_name})
            chunk["status"] = "failed"
            if provider:
                chunk["provider"] = provider
            chunk["error"] = error_msg
            chunk["updated_at"] = _utc_now()
            state["checkpoint"] = {"stage": "transcribing", "chunk": chunk_name}
            state["error_logs"].append(f"{chunk_name}: {error_msg}")
            state["updated_at"] = _utc_now()

        self._update_locked(mutate)

    def update_chunk_metadata(self, file_id: str, chunk_name: str, meta: Dict[str, Any]) -> None:
        def mutate(data: Dict[str, Any]) -> None:
            state = data.setdefault(file_id, self._default_state(file_id))
            chunk = state.setdefault("chunks", {}).setdefault(chunk_name, {"chunk_name": chunk_name})
            chunk.update(meta)
            chunk["updated_at"] = _utc_now()
            state["updated_at"] = _utc_now()

        self._update_locked(mutate)

    def get_pending_chunks(self, file_id: str) -> List[Dict[str, Any]]:
        state = self.get_file_state(file_id)
        chunk_states = list(state.get("chunks", {}).values())
        return [chunk for chunk in chunk_states if chunk.get("status") not in {"completed", "fallback_completed"}]

    def set_final_output(self, file_id: str, final_output_path: Path) -> None:
        def mutate(data: Dict[str, Any]) -> None:
            state = data.setdefault(file_id, self._default_state(file_id))
            state["final_output_path"] = str(final_output_path)
            state["updated_at"] = _utc_now()

        self._update_locked(mutate)

    def set_provider_summary(self, file_id: str, provider_summary: Dict[str, int]) -> None:
        def mutate(data: Dict[str, Any]) -> None:
            state = data.setdefault(file_id, self._default_state(file_id))
            state["provider_summary"] = provider_summary
            state["updated_at"] = _utc_now()

        self._update_locked(mutate)

    def record_metrics(self, file_id: str, metrics: Dict[str, Any]) -> None:
        def mutate(data: Dict[str, Any]) -> None:
            state = data.setdefault(file_id, self._default_state(file_id))
            state_metrics = state.setdefault("metrics", {})
            state_metrics.update(metrics)
            state["updated_at"] = _utc_now()

        self._update_locked(mutate)

    def log_error(self, file_id: str, error_msg: str, error_code: str | None = None) -> None:
        def mutate(data: Dict[str, Any]) -> None:
            state = data.setdefault(file_id, self._default_state(file_id))
            state["status"] = "failed"
            state["error_logs"].append(error_msg)
            if not state.get("error_structured"):
                state["error_structured"] = {
                    "error_code": error_code or "UNKNOWN_ERROR",
                    "error_message": error_msg,
                    "stage": state.get("current_stage", "unknown"),
                }
            state["updated_at"] = _utc_now()

        self._update_locked(mutate)
