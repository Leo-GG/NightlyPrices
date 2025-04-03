"""
Logger configuration module.
"""
import os
import logging
from typing import Optional


def setup_logger(
    name: Optional[str] = None,
    level: int = logging.INFO,
    log_file: Optional[str] = None,
    console_output: bool = True
) -> logging.Logger:
    """
    Set up a logger with file and/or console handlers.
    
    Args:
        name: Logger name
        level: Logging level
        log_file: Path to log file
        console_output: Whether to output logs to console
        
    Returns:
        Configured logger
    """
    # Get logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Add file handler if log_file is specified
    if log_file:
        # Create log directory if it doesn't exist
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # Create file handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # Add console handler if console_output is True
    if console_output:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    return logger


def configure_root_logger(
    level: int = logging.INFO,
    log_file: Optional[str] = None,
    console_output: bool = True
) -> None:
    """
    Configure the root logger.
    
    Args:
        level: Logging level
        log_file: Path to log file
        console_output: Whether to output logs to console
    """
    # Configure root logger
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler() if console_output else logging.NullHandler(),
            logging.FileHandler(log_file) if log_file else logging.NullHandler()
        ]
    )
