"""
Logging Utility Module

This module provides centralized logging configuration for all components.
"""

import os
import sys
import logging
from logging.handlers import RotatingFileHandler
from typing import Optional, Dict, Any

# Default log format
DEFAULT_LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# Default log levels
LOG_LEVELS = {
    'debug': logging.DEBUG,
    'info': logging.INFO,
    'warning': logging.WARNING,
    'error': logging.ERROR,
    'critical': logging.CRITICAL
}

class LoggingManager:
    """Manages logging configuration across the application."""
    
    def __init__(self, log_dir: str = None, log_level: str = 'info', 
                 log_to_console: bool = True, log_to_file: bool = True):
        """
        Initialize the LoggingManager.
        
        Args:
            log_dir: Directory to store log files (default: ./logs)
            log_level: Logging level (debug, info, warning, error, critical)
            log_to_console: Whether to output logs to console
            log_to_file: Whether to output logs to file
        """
        # Set log directory
        if log_dir is None:
            self.log_dir = os.path.abspath(os.path.join(
                os.path.dirname(__file__), '..', '..', 'logs'))
        else:
            self.log_dir = log_dir
            
        # Create log directory if it doesn't exist
        if log_to_file:
            os.makedirs(self.log_dir, exist_ok=True)
        
        # Set log level
        self.log_level = LOG_LEVELS.get(log_level.lower(), logging.INFO)
        
        # Configure root logger
        self.configure_root_logger(log_to_console, log_to_file)
        
        # Keep track of configured module loggers
        self.configured_loggers = {}
    
    def configure_root_logger(self, log_to_console: bool, log_to_file: bool):
        """Configure the root logger with console and/or file handlers."""
        # Get the root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(self.log_level)
        
        # Remove any existing handlers
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # Create formatter
        formatter = logging.Formatter(DEFAULT_LOG_FORMAT)
        
        # Add console handler
        if log_to_console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            root_logger.addHandler(console_handler)
        
        # Add file handler
        if log_to_file:
            log_file = os.path.join(self.log_dir, 'ai_portfolio_manager.log')
            file_handler = RotatingFileHandler(
                log_file, maxBytes=10*1024*1024, backupCount=5)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
    
    def get_logger(self, name: str, module_log_level: Optional[str] = None) -> logging.Logger:
        """
        Get a logger for a specific module.
        
        Args:
            name: Logger name (typically module name)
            module_log_level: Optional specific log level for this module
            
        Returns:
            Configured logger instance
        """
        # Get or create logger
        logger = logging.getLogger(name)
        
        # Set module-specific log level if provided
        if module_log_level:
            level = LOG_LEVELS.get(module_log_level.lower(), self.log_level)
            logger.setLevel(level)
        
        # Track configured loggers
        self.configured_loggers[name] = logger
        
        return logger
    
    def set_global_log_level(self, log_level: str):
        """
        Change the log level for all configured loggers.
        
        Args:
            log_level: New log level (debug, info, warning, error, critical)
        """
        level = LOG_LEVELS.get(log_level.lower(), logging.INFO)
        
        # Update root logger
        logging.getLogger().setLevel(level)
        
        # Update all configured module loggers
        for name, logger in self.configured_loggers.items():
            logger.setLevel(level)

# Create a singleton instance
logging_manager = LoggingManager()

def get_logger(name: str, module_log_level: Optional[str] = None) -> logging.Logger:
    """
    Get a logger for a specific module.
    
    Args:
        name: Logger name (typically module name)
        module_log_level: Optional specific log level for this module
        
    Returns:
        Configured logger instance
    """
    return logging_manager.get_logger(name, module_log_level)

def configure_logging(log_dir: str = None, log_level: str = 'info',
                     log_to_console: bool = True, log_to_file: bool = True):
    """
    Configure global logging settings.
    
    Args:
        log_dir: Directory to store log files
        log_level: Logging level (debug, info, warning, error, critical)
        log_to_console: Whether to output logs to console
        log_to_file: Whether to output logs to file
    """
    global logging_manager
    logging_manager = LoggingManager(log_dir, log_level, log_to_console, log_to_file)
    
    # Return configured root logger
    return logging.getLogger()