"""
Logging Utility for Brickfolio Pipeline

This module provides a centralized logging configuration used across all 
pipeline stages. It ensures logs are simultaneously directed to:
1. The standard output (Console) for real-time monitoring.
2. A persistent file (`logs/pipeline.log`) for historical audit and debugging.
"""

import logging
import sys
from pathlib import Path

# Add src directory to path to ensure config is importable during nested module loads
# sys.path.append removed
from ..config import settings as config

def get_logger(name: str) -> logging.Logger:
    """
    Initializes and returns a standard logger instance.

    Args:
        name: The name used to identify the logger (usually the module name).

    Returns:
        logging.Logger: A configured logger object.
    """
    logger = logging.getLogger(name)
    
    # Avoid duplicate handlers if the logger is already initialized
    if logger.handlers:
        return logger
        
    logger.setLevel(logging.INFO)
    
    # Standard format: timestamp | level | [module_name] message
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | [%(name)s] %(message)s'
    )
    
    # Create logs directory dynamically if it doesn't exist
    config.LOGS_DIR.mkdir(parents=True, exist_ok=True)
    log_file = config.LOGS_DIR / "pipeline.log"
    
    # 1. File Handler: Writes UTF-8 encoded logs to the pipeline.log file
    file_handler = logging.FileHandler(str(log_file), encoding='utf-8')
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)
    logger.addHandler(file_handler)
    
    # 2. Console Handler: Outputs logs to stdout for IDE/CLI monitoring
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)
    logger.addHandler(console_handler)
    
    return logger
