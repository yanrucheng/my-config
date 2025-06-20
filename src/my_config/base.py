"""Base configuration classes for the application.

This module provides the foundation for all configuration classes in the application.
"""

from typing import Dict, Optional, TypeVar, Generic, Any
import logging
import yaml
import os

from my_config.utils.singleton import GenericSingletonFactory

logger = logging.getLogger(__name__)

T = TypeVar('T')

class BaseConfig(GenericSingletonFactory, Generic[T]):
    """Base configuration class with generic file loading"""
    CONFIG_FILENAME = "config.yml"
    
    def __init__(self):
        self._data: Dict[str, T] = {}
        self.data: Dict[str, T] = {}
        self.load_from_file()
        self._process_config()
    
    def get(self, name: str) -> Optional[T]:
        """Get a configuration value by name."""
        return self.data.get(name)

    def get_config_file_path(self) -> str:
        """Get the path to the configuration file.
        
        Priority order:
        1. Explicitly specified path in code (CONFIG_FILENAME)
        2. Path from CONFIG_PATH environment variable (if exists)
        3. Search in default locations
        """
        return GenericSingletonFactory.resolve_file_path(
            filename=self.CONFIG_FILENAME,
            env_var_name="CONFIG_PATH"
        )
    
    def load_from_file(self) -> None:
        """Generic file loading that child classes can use"""
        path = self.get_config_file_path()
        logger.info(f"Loading configuration from: {path}")
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f) or {}
            self._data = config_data
            
            # Log configuration details
            config_keys = list(config_data.keys())
            logger.info(f"Successfully loaded configuration from {path}")
            logger.info(f"Configuration contains {len(config_keys)} top-level keys: {', '.join(config_keys)}")
        except FileNotFoundError:
            logger.warning(f"Configuration file not found: {path}")
            self._data = {}
        except Exception as e:
            logger.error(f"Error loading configuration from {path}: {e}")
            self._data = {}

    def _process_config(self) -> None:
        """Process the loaded configuration data.
        
        This method can be overridden by child classes to implement
        custom processing logic.
        """
        self.data = {**self._data}


class DefaultConfig(BaseConfig):
    """Default configuration class with predefined config file path"""
    CONFIG_FILENAME = "./conf/conf.yml"