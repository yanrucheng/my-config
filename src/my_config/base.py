"""Base configuration classes for the application.

This module provides the foundation for all configuration classes in the application.
"""

from typing import Dict, Optional, TypeVar, Generic, Any
import logging
import yaml
import os

from jinnang.common import SingletonFileLoader

logger = logging.getLogger(__name__)

T = TypeVar('T')

class BaseConfig(SingletonFileLoader, Generic[T]):
    """Base configuration class with caller-aware file loading"""
    
    def __init__(self, filename: str = None,  caller_module_path: Optional[str] = None):
        
        if filename is None:
            filename = 'conf/conf.yml'
            logger.warning(f'It is not recommended to pass empty filename to BaseConfig. filename is set to default value: {filename}')
        
        super().__init__(filename, caller_module_path)
        self._data: Dict[str, T] = {}
        self.data: Dict[str, T] = {}
        self.load_from_file()
        self._process_config()
    
    def get(self, name: str, default: Optional[T] = None) -> Optional[T]:
        """Get a configuration value by name.
        
        Args:
            name: The name of the configuration value to get
            default: The default value to return if the configuration value is not found
            
        Returns:
            The configuration value, or the default value if not found
        """
        try:
            return self.data.get(name, default)
        except Exception:
            # If data access fails for any reason, return the default value
            return default

    def load_from_file(self) -> None:
        """Generic file loading that child classes can use"""
        try:
            path = self.filepath
            
            # Use a try-except block for logging to prevent recursion
            try:
                logger.info(f"Loading configuration from: {path}")
            except Exception:
                pass  # Ignore logging errors
            
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    config_data = yaml.safe_load(f) or {}
                self._data = config_data
                
                # Log configuration details - wrapped in try-except to prevent recursion
                try:
                    config_keys = list(config_data.keys())
                    logger.info(f"Successfully loaded configuration from {path}")
                    logger.info(f"Configuration contains {len(config_keys)} top-level keys: {', '.join(config_keys)}")
                except Exception:
                    pass  # Ignore logging errors
            except FileNotFoundError:
                try:
                    logger.warning(f"Configuration file not found: {path}")
                except Exception:
                    pass  # Ignore logging errors
                self._data = {}
            except Exception as e:
                try:
                    logger.error(f"Error loading configuration from {path}: {e}")
                except Exception:
                    pass  # Ignore logging errors
                self._data = {}
        except Exception as e:
            # If even getting the config path fails, set empty data
            self._data = {}
            try:
                logger.error(f"Critical error in configuration loading: {e}")
            except Exception:
                pass  # Ignore logging errors

    def _process_config(self) -> None:
        """Process the loaded configuration data.
        
        This method can be overridden by child classes to implement
        custom processing logic.
        """
        self.data = {**self._data}


class DefaultConfig(BaseConfig):
    """Default configuration class with automatic caller detection"""
    pass