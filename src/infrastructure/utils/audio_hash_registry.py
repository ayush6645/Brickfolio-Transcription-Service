"""
Audio Hash Registry for Duplicate Detection

This module prevents the pipeline from re-processing the same audio recordings,
saving significant API costs. It computes a SHA-256 fingerprint of each file
and maintains a persistent registry of all seen hashes.
"""

import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any

import portalocker

# Add parent directory to path for config imports
# sys.path.append removed
from ..config import settings as config

class AudioHashRegistry:
    """
    Handles file-level deduplication using content hashing.
    Uses file locking to support multi-process safety.
    """
    
    def __init__(self):
        """Initializes the registry and ensures metadata directory exists."""
        config.METADATA_DIR.mkdir(parents=True, exist_ok=True)
        self.registry_file = config.METADATA_DIR / "audio_hash_registry.json"
        
    def _read_with_lock(self) -> Dict[str, str]:
        """
        Reads the hash registry while holding a shared lock.

        Returns:
            Dict: Mapping of file hashes to the original filename.
        """
        if not self.registry_file.exists():
            return {}
        try:
            with portalocker.Lock(self.registry_file, mode='r', timeout=10, fail_when_locked=False) as f:
                content = f.read()
                return json.loads(content) if content else {}
        except Exception:
            return {}
            
    def _write_with_lock(self, data: Dict[str, str]):
        """
        Writes the hash registry using an exclusive lock.

        Args:
            data: The registry dictionary to persist.
        """
        try:
            with portalocker.Lock(self.registry_file, mode='w', timeout=10, fail_when_locked=False) as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"FAILED TO WRITE HASH REGISTRY: {e}", file=sys.stderr)
            
    def compute_file_hash(self, file_path: Path) -> str:
        """
        Computes a SHA-256 fingerprint for a local file.
        Uses chunked reading to support large audio files without memory exhaustion.

        Args:
            file_path: Path to the audio file.

        Returns:
            str: Hexadecimal hash string.
        """
        hasher = hashlib.sha256()
        with open(file_path, 'rb') as f:
            while chunk := f.read(65536): # 64KB chunks
                hasher.update(chunk)
        return hasher.hexdigest()
        
    def check_and_register(self, file_path: Path) -> bool:
        """
        Determines if a file is a duplicate and registers it if new.

        Args:
            file_path: Path to the file to check.

        Returns:
            bool: True if the file has already been processed (duplicate).
                  False if the file is new (successfully registered).
        """
        file_hash = self.compute_file_hash(file_path)
        data = self._read_with_lock()
        
        if file_hash in data:
            # Duplicate detected
            return True
        else:
            # Register the new file
            data[file_hash] = file_path.name
            self._write_with_lock(data)
            return False

# Global singleton instance for easy import across pipeline start stages
registry = AudioHashRegistry()
