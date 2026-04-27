"""
Base Audio Source Adapter

Defines the interface for discovering and retrieving audio files from 
different storage backends (Local, S3, etc).
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class AudioFileMetadata:
    """Metadata for an audio file discovered by an adapter."""
    file_path: Path
    filename: str
    source_type: str
    size_bytes: int
    additional_meta: Dict[str, Any]

class AudioSource(ABC):
    """Abstract Base Class for all audio sources."""
    
    @abstractmethod
    def list_files(self) -> List[AudioFileMetadata]:
        """
        Scans the source and returns a list of available audio files.
        """
        pass

    @abstractmethod
    def get_source_identifier(self) -> str:
        """Returns a unique identifier for this source instance."""
        pass
