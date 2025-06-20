"""Environment-aware configuration classes.

This module provides configuration classes that load different files based on the current environment.
"""

from typing import Dict, Optional, TypeVar, Generic, Any
import logging
import os

from my_config.env import get_env, Env
from my_config.base import BaseConfig

logger = logging.getLogger(__name__)

T = TypeVar('T')

class EnvAwareConfig(BaseConfig[T]):
    """Environment-aware configuration that loads different files based on environment"""
    DEV_CONFIG_FILENAME = "./conf/conf.yml"
    BOE_CONFIG_FILENAME = "./conf/boe_conf.yml"
    PROD_CONFIG_FILENAME = "./conf/prod_conf.yml"
    
    def __init__(self):
        super().__init__()
    
    def get_config_file_path(self) -> str:
        """Determine which config file to use with fallback logic
        
        Priority order:
        1. Explicitly specified path in code (environment-specific CONFIG_FILENAME)
        2. Path from ENV_CONFIG_PATH environment variable (if exists)
        3. Search in default locations with environment-specific fallback order
        """
        env = get_env()
        fallback_order = []
        env_var_name = "ENV_CONFIG_PATH"
        
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
        
        # First check environment variable (lower priority than code-specified paths)
        env_path = os.getenv(env_var_name)
        if env_path:
            logger.info(f"Found environment variable {env_var_name}={env_path}")
            if os.path.exists(env_path):
                logger.info(f"Using configuration from environment variable: {env_path}")
                return env_path
            else:
                logger.warning(f"Path from environment variable {env_var_name} does not exist: {env_path}")
        
        # Try each file in order until one is found
        found_files = []
        for config_file in fallback_order:
            try:
                resolved_path = self.resolve_file_path(filename=config_file)
                found_files.append((config_file, resolved_path, True))
                logger.info(f"Selected configuration file: {resolved_path} (from {config_file})")
                return resolved_path
            except FileNotFoundError:
                found_files.append((config_file, None, False))
                continue
        
        # Log all attempted paths for debugging
        logger.error(f"Configuration file resolution failed. Attempted files:")
        for config_name, path, exists in found_files:
            status = "Found" if exists else "Not found"
            logger.error(f"  - {config_name}: {status} {path if path else ''}")
        
        # If no config file is found, return the default for the environment
        # This will likely raise an error when trying to load, but that's handled in BaseConfig
        if env == Env.PROD:
            return self.resolve_file_path(filename=self.PROD_CONFIG_FILENAME)
        elif env == Env.BOE:
            return self.resolve_file_path(filename=self.BOE_CONFIG_FILENAME)
        else:
            return self.resolve_file_path(filename=self.DEV_CONFIG_FILENAME)


class APIConfig(EnvAwareConfig[Dict[str, Any]]):
    """API-specific configuration with environment awareness"""
    DEV_CONFIG_FILENAME = "./conf/api.yml"
    BOE_CONFIG_FILENAME = "./conf/boe_api.yml"
    PROD_CONFIG_FILENAME = "./conf/prod_api.yml"