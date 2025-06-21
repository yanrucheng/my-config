"""Environment-aware configuration classes.

This module provides configuration classes that load different files based on the current environment.
"""

from typing import Dict, Optional, TypeVar, Generic, Any
import logging
import os

from my_config.env import get_env, Env
from my_config.base import BaseConfig
from jinnang.common.patterns import SingletonFileLoader

logger = logging.getLogger(__name__)

T = TypeVar('T')

class EnvAwareConfig(BaseConfig[T]):
    """Environment-aware configuration that loads different files based on environment"""
    DEV_CONFIG_FILENAME = "./conf/conf.yml"
    BOE_CONFIG_FILENAME = "./conf/boe_conf.yml"
    PROD_CONFIG_FILENAME = "./conf/prod_conf.yml"
    
    def __init__(self, caller_module_path: Optional[str] = None):
        filename = self._determine_config_filename()
        # If filename is an absolute path (from ENV_CONFIG_PATH), handle it specially
        if os.path.isabs(filename):
            # Initialize the SingletonFileLoader part without calling BaseConfig.__init__
            from jinnang.common.patterns import SingletonFileLoader
            SingletonFileLoader.__init__(self, filename=None, caller_module_path=caller_module_path)
            # Set the filepath directly
            self.loaded_filepath = filename if os.path.exists(filename) else None
            # Initialize BaseConfig data structures
            self._data = {}
            self.data = {}
            # Load the file
            self.load_from_file()
            self._process_config()
        else:
            super().__init__(filename=filename, caller_module_path=caller_module_path)
    
    def _determine_config_filename(self) -> str:
        """Determine which config file to use with fallback logic
        
        Priority order:
        1. Path from ENV_CONFIG_PATH environment variable (if exists and file exists)
        2. Environment-specific config file with fallback order
        
        Returns:
            str: The filename to use for configuration
        """
        env = get_env()
        env_var_name = "ENV_CONFIG_PATH"
        
        # First check environment variable
        env_path = os.getenv(env_var_name)
        if env_path and os.path.exists(env_path):
            logger.info(f"Using configuration from environment variable {env_var_name}: {env_path}")
            return env_path
        elif env_path:
            logger.warning(f"Path from environment variable {env_var_name} does not exist: {env_path}")
        
        # Determine fallback order based on environment
        if env == Env.PROD:
            fallback_order = [
                self.PROD_CONFIG_FILENAME,
                self.BOE_CONFIG_FILENAME,
                self.DEV_CONFIG_FILENAME
            ]
            logger.info("PROD environment detected, using fallback order: PROD -> BOE -> DEV")
        elif env == Env.BOE:
            fallback_order = [
                self.BOE_CONFIG_FILENAME,
                self.DEV_CONFIG_FILENAME
            ]
            logger.info("BOE environment detected, using fallback order: BOE -> DEV")
        else:  # DEV
            fallback_order = [self.DEV_CONFIG_FILENAME]
            logger.info("DEV environment detected, using only DEV config")
        
        logger.info(f"Searching for configuration files in {len(fallback_order)} possible locations")
        
        # Try each file in order until one is found
        for config_file in fallback_order:
            try:
                # Use the static method from SingletonFileLoader to check if file exists
                resolved_path = SingletonFileLoader.resolve_file_path(filename=config_file)
                logger.info(f"Found configuration file: {resolved_path} (from {config_file})")
                return config_file  # Return the filename, not the resolved path
            except FileNotFoundError:
                logger.debug(f"Configuration file not found: {config_file}")
                continue
        
        # If no config file is found, return the primary config for the environment
        # The file loading will handle the FileNotFoundError appropriately
        if env == Env.PROD:
            logger.warning(f"No configuration files found, defaulting to: {self.PROD_CONFIG_FILENAME}")
            return self.PROD_CONFIG_FILENAME
        elif env == Env.BOE:
            logger.warning(f"No configuration files found, defaulting to: {self.BOE_CONFIG_FILENAME}")
            return self.BOE_CONFIG_FILENAME
        else:
            logger.warning(f"No configuration files found, defaulting to: {self.DEV_CONFIG_FILENAME}")
            return self.DEV_CONFIG_FILENAME


class APIConfig(EnvAwareConfig[Dict[str, Any]]):
    """API-specific configuration with environment awareness"""
    DEV_CONFIG_FILENAME = "./conf/api.yml"
    BOE_CONFIG_FILENAME = "./conf/boe_api.yml"
    PROD_CONFIG_FILENAME = "./conf/prod_api.yml"
    
    def __init__(self, caller_module_path: Optional[str] = None):
        super().__init__(caller_module_path=caller_module_path)