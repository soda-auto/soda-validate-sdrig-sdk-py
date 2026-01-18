"""
Logging utilities for SDRIG SDK

This module provides centralized logging configuration and utilities.
"""

import logging
import sys
from typing import Optional
from pathlib import Path


class SDRIGLogger:
    """Centralized logger for SDRIG SDK"""

    _instance: Optional['SDRIGLogger'] = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self._setup_logging()
            SDRIGLogger._initialized = True

    def _setup_logging(self):
        """Setup default logging configuration"""
        self.logger = logging.getLogger('sdrig')

        # Check environment variable for log level
        import os
        log_level = os.getenv('SDRIG_LOG_LEVEL', 'INFO').upper()
        level = getattr(logging, log_level, logging.INFO)
        self.logger.setLevel(level)

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)

        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(formatter)

        # Add handler if not already added
        if not self.logger.handlers:
            self.logger.addHandler(console_handler)

    @classmethod
    def get_logger(cls, name: Optional[str] = None) -> logging.Logger:
        """
        Get a logger instance

        Args:
            name: Optional logger name, will be appended to 'sdrig'

        Returns:
            Logger instance
        """
        instance = cls()
        if name:
            return logging.getLogger(f'sdrig.{name}')
        return instance.logger

    @classmethod
    def set_level(cls, level: int):
        """
        Set logging level

        Args:
            level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        instance = cls()
        instance.logger.setLevel(level)

    @classmethod
    def add_file_handler(cls, log_file: Path, level: int = logging.DEBUG):
        """
        Add file handler for logging to file

        Args:
            log_file: Path to log file
            level: Logging level for file handler
        """
        instance = cls()
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)

        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        instance.logger.addHandler(file_handler)

    @classmethod
    def enable_debug_mode(cls):
        """Enable debug mode with verbose logging"""
        cls.set_level(logging.DEBUG)
        instance = cls()
        instance.logger.debug("Debug mode enabled")

    @classmethod
    def enable_packet_dumps(cls):
        """Enable packet dump logging"""
        instance = cls()
        packet_logger = logging.getLogger('sdrig.packets')
        packet_logger.setLevel(logging.DEBUG)
        instance.logger.info("Packet dumps enabled")


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Convenience function to get a logger

    Args:
        name: Optional logger name

    Returns:
        Logger instance
    """
    return SDRIGLogger.get_logger(name)
