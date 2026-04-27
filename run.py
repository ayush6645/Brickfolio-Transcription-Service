"""
Brickfolio Transcription Pipeline - Main Entry Point

Usage:
    python run.py

This script scans the 'Audio_Data' folder for new recordings, 
processes them through the transcription pipeline, and saves 
the resulting JSON data to 'data/final/'.
"""

import os
import sys
from pathlib import Path

# Ensure src directory is in path
sys.path.append(str(Path(__file__).parent))

from src.pipeline.ingestion_engine import engine
from src.infrastructure.utils.logger import get_logger

logger = get_logger("main_runner")

def main():
    logger.info("Starting Brickfolio Transcription Runner...")
    
    try:
        # Trigger the ingestion engine to find and process new files
        engine.run_full_pipeline_on_new()
        
    except KeyboardInterrupt:
        logger.info("Process interrupted by user.")
    except Exception as e:
        logger.error(f"A critical error occurred: {e}")
        sys.exit(1)
        
    logger.info("Batch processing finished.")

if __name__ == "__main__":
    main()
