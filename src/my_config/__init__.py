"""Configuration module for Python applications.

This module provides configuration management classes for different aspects of applications.
"""

from my_config.base import BaseConfig, DefaultConfig
from my_config.env_aware import EnvAwareConfig, APIConfig
from my_config.llm import ModelConfig, LLMConfig
from my_config.env import Env, get_env, is_dev, is_boe, is_prod

__version__ = '0.1.0'

__all__ = [
    'BaseConfig',
    'DefaultConfig',
    'EnvAwareConfig',
    'APIConfig',
    'ModelConfig',
    'LLMConfig',
    'Env',
    'get_env',
    'is_dev',
    'is_boe',
    'is_prod',
]