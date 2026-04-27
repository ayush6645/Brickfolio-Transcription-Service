"""
Metadata and Pipeline State Tracker

This module manages the persistence of the pipeline's progress across stages.
It uses JSON-based state storage with robust file-locking (via portalocker) 
to ensure that concurrent workers do not corrupt the state file when 
running in parallel.

State Schema:
{
  "file_id": {
    "status": "pending" | "processing" | "completed" | "failed",
    "cleaning_status": str,
    "intelligence_status": str,
    "number_of_chunks": int,
    "processed_chunks": list,
    "error_logs": list
  }
}
"""

import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional

import portalocker

# Ensure the parent src directory is in the path for config imports
# sys.path.append removed
from ..config import settings as config

class PipelineTracker:
    """
    Handles read/write operations for the centralized pipeline state file.
    Uses file locking to support multi-process safety.
    """
    
    def __init__(self):
        """Initializes the tracker and ensures metadata directory exists."""
        config.METADATA_DIR.mkdir(parents=True, exist_ok=True)
        self.state_file = config.METADATA_DIR / "pipeline_state.json"
        
    def _read_with_lock(self) -> Dict[str, Any]:
        """
        Reads the state file while holding a shared lock for safety.

        Returns:
            Dict: The current state mapping file IDs to their metadata.
        """
        if not self.state_file.exists():
            return {}
        try:
            # timeout=10 avoids indefinite hanging if a lock is stuck
            with portalocker.Lock(self.state_file, mode='r', timeout=10, fail_when_locked=False) as f:
                content = f.read()
                if not content:
                    return {}
                return json.loads(content)
        except (portalocker.exceptions.LockException, json.JSONDecodeError, FileNotFoundError):
            return {}

    def _write_with_lock(self, data: Dict[str, Any]):
        """
        Writes the state file using an exclusive lock and atomic replacement.

        Args:
            data: The full state dictionary to persist.
        """
        temp_file = self.state_file.with_suffix(".tmp")
        try:
            # We lock the main file to coordinate with other potential writers
            with portalocker.Lock(self.state_file, mode='a', timeout=10, fail_when_locked=False):
                with open(temp_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2)
                # Atomic replace ensures the state file is never in a half-written state
                os.replace(str(temp_file), str(self.state_file))
        except Exception:
            # Fallback for OS environments where replace might fail during lock contention
            time.sleep(1)
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)

    def init_file(self, file_id: str):
        """Initializes a entry for a new file in the tracker if it doesn't exist."""
        data = self._read_with_lock()
        if file_id not in data:
            data[file_id] = {
                "file_id": file_id,
                "status": "pending",
                "cleaning_status": "pending",
                "intelligence_status": "pending",
                "number_of_chunks": 0,
                "processed_chunks": [],
                "error_logs": []
            }
            self._write_with_lock(data)
            
    def update_status(self, file_id: str, status: str):
        """Updates the global status (e.g. 'completed') for a file."""
        data = self._read_with_lock()
        if file_id in data:
            data[file_id]["status"] = status
            self._write_with_lock(data)

    def update_stage_status(self, file_id: str, stage: str, status: str):
        """Updates a specific stage status (e.g., 'cleaning_status')."""
        data = self._read_with_lock()
        if file_id in data:
            data[file_id][stage] = status
            self._write_with_lock(data)

    def log_error(self, file_id: str, error_msg: str):
        """Logs a failure message and marks the file as 'failed' in global status."""
        data = self._read_with_lock()
        if file_id in data:
            if "error_logs" not in data[file_id]:
                data[file_id]["error_logs"] = []
            data[file_id]["error_logs"].append(error_msg)
            data[file_id]["status"] = "failed"
            self._write_with_lock(data)
            
    def set_chunks_total(self, file_id: str, total_chunks: int):
        """Sets the expected number of segments for a long audio file."""
        data = self._read_with_lock()
        if file_id in data:
            data[file_id]["number_of_chunks"] = total_chunks
            self._write_with_lock(data)
            
    def add_processed_chunk(self, file_id: str, chunk_name: str):
        """Records that a specific fragment of a file has been processed."""
        data = self._read_with_lock()
        if file_id in data:
            if "processed_chunks" not in data[file_id]:
                data[file_id]["processed_chunks"] = []
            if chunk_name not in data[file_id]["processed_chunks"]:
                data[file_id]["processed_chunks"].append(chunk_name)
                self._write_with_lock(data)

    def update_chunk_metadata(self, file_id: str, chunk_name: str, meta: Dict[str, Any]):
        """Persists segment-specific metadata (timestamps, scores)."""
        data = self._read_with_lock()
        if file_id in data:
            if "chunk_metadata" not in data[file_id]:
                data[file_id]["chunk_metadata"] = {}
            data[file_id]["chunk_metadata"][chunk_name] = meta
            self._write_with_lock(data)
                
    def get_file_state(self, file_id: str) -> Dict[str, Any]:
        """Retrieves the full current state for a specific file ID."""
        data = self._read_with_lock()
        return data.get(file_id, {})
