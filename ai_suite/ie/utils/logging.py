import json
import logging
import os
from datetime import datetime

def setup_logger(name: str, log_dir: str = "logs", log_file: str = None, level=logging.INFO) -> logging.Logger:
    """
    Configure logging for the application.
    
    Args:
        name: Logger name
        log_dir: Directory to store log files
        log_file: Optional specific log file name. If None, generates timestamped name
        level: Logging level
        
    Returns:
        Logger instance
    """
    # Create logs directory if it doesn't exist
    os.makedirs(log_dir, exist_ok=True)
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Clear any existing handlers to prevent double logging
    logger.handlers.clear()
    
    # Prevent propagation to root logger
    logger.propagate = False
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # File handler
    if log_file is None:
        log_file = os.path.join(
            log_dir, 
            f"{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        )
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)
    logger.addHandler(file_handler)
    
    # Stream handler (console)
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    stream_handler.setLevel(logging.INFO)
    logger.addHandler(stream_handler)
    
    return logger

