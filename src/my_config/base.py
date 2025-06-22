"""Base configuration classes for the application.

This module provides the foundation for all configuration classes in the application.
"""

from typing import Dict, Optional, TypeVar, Generic, Any
import logging
import yaml
import os
import inspect

from jinnang.common.patterns import SingletonFileLoader
from jinnang.verbosity import Verbosity

logger = logging.getLogger(__name__)

T = TypeVar('T')

class BaseConfig(SingletonFileLoader, Generic[T]):
    """Base configuration class with caller-aware file loading"""
    
    def __init__(
        self, 
        filename: Optional[str] = None,
        caller_module_path: Optional[str] = None,
        verbosity: Verbosity = Verbosity.FULL,
        **kwargs: Any
    ):
        # Set default filename if none provided
        if filename is None:
            filename = 'conf/conf.yml'
            logger.warning(f'It is not recommended to pass empty filename to BaseConfig. filename is set to default value: {filename}')
        
        # Determine the path of the calling module dynamically if not provided
        if caller_module_path is None:
            frame = inspect.currentframe()
            if frame is not None and frame.f_back is not None:
                caller_module_path = frame.f_back.f_globals.get('__file__')
            if caller_module_path is None:
                logger.warning("Could not determine caller_module_path automatically. Please provide it explicitly.")

        # Initialize SingletonFileLoader with proper parameters
        super().__init__(
            filename=filename,
            caller_module_path=caller_module_path,
            verbosity=verbosity,
            **kwargs
        )
        
        # Initialize data attributes only once per singleton instance
        if not hasattr(self, '_config_initialized'):
            self._data: Dict[str, T] = {}
            self.data: Dict[str, T] = {}
            self.load_from_file()
            self.config = self._process_config(self._data)
            self.data = self.config  # Make data accessible via get() method
            self._config_initialized = True

    
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
        # Check if file was successfully loaded by SingletonFileLoader
        if not self.loaded_filepath:
            logger.warning("No configuration file was loaded by SingletonFileLoader")
            self._data = {}
            return
            
        try:
            path = self.loaded_filepath
            
            # Use a try-except block for logging to prevent recursion
            try:
                logger.info(f"Loading configuration from: {path}")
            except Exception:
                pass  # Ignore logging errors
            
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    config_data = yaml.safe_load(f) or {}
                self._data = self._resolve_env_vars(config_data)
                
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

    def _process_config(self, config: T) -> T:
        """Hook for subclasses to process the loaded configuration."""
        return config

    def _resolve_env_vars(self, data: Any) -> Any:
        """Recursively resolves environment variable placeholders in the config data.

        Placeholders are in the format ${ENV_VAR_NAME}.
        """
        if isinstance(data, dict):
            return {k: self._resolve_env_vars(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._resolve_env_vars(elem) for elem in data]
        elif isinstance(data, str):
            if data.startswith('${') and data.endswith('}'):
                env_var_name = data[2:-1]
                env_value = os.getenv(env_var_name)
                if env_value is not None:
                    logger.info(f"Resolved environment variable '{env_var_name}' for config value.")
                    return env_value
                else:
                    logger.warning(f"Environment variable '{env_var_name}' not found. Keeping placeholder as is.")
                    return data
            return data
        else:
            return data


class DefaultConfig(BaseConfig):
    """Default configuration class with automatic caller detection"""
    pass