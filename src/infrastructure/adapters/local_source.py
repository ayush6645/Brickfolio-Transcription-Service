"""
Local Folder Audio Source Adapter

Implements the AudioSource interface for reading files from a local directory.
"""

from pathlib import Path
from typing import List, Optional

from .base import AudioSource, AudioFileMetadata
from ..config import settings as config
from ..utils.logger import get_logger

logger = get_logger("local_source")

class LocalFolderSource(AudioSource):
    """Discovers audio files in a local directory."""
    
    def __init__(self, folder_path: Optional[Path] = None):
        self.folder_path = folder_path or config.LOCAL_SOURCE_PATH
        if not self.folder_path.exists():
            logger.warning(f"Source folder does not exist: {self.folder_path}")
            self.folder_path.mkdir(parents=True, exist_ok=True)

    def list_files(self) -> List[AudioFileMetadata]:
        """Scans the folder for supported audio files."""
        discovered = []
        
        # Supported extensions (can be expanded)
        SUPPORTED_EXTENSIONS = set(config.SUPPORTED_AUDIO_EXTENSIONS)
        
        logger.info(f"Scanning local directory: {self.folder_path}")
        
        for file in self.folder_path.iterdir():
            if file.is_file() and file.suffix.lower() in SUPPORTED_EXTENSIONS:
                try:
                    stats = file.stat()
                    discovered.append(AudioFileMetadata(
                        file_path=file,
                        filename=file.name,
                        source_type="local",
                        size_bytes=stats.st_size,
                        additional_meta={
                            "created_at": stats.st_ctime,
                            "modified_at": stats.st_mtime
                        }
                    ))
                except Exception as e:
                    logger.error(f"Error reading file metadata for {file}: {e}")
        
        logger.info(f"Discovered {len(discovered)} files in {self.folder_path}")
        return discovered

    def get_source_identifier(self) -> str:
        return f"local://{self.folder_path.absolute()}"
