"""Environment detection module.

This module provides utilities for detecting and working with different environments.
"""

from enum import Enum, auto
import os
import functools

class Env(Enum):
    """Environment enumeration for application environments."""
    BOE = auto()
    PROD = auto()
    DEV = auto()

def is_dev() -> bool:
    """Check if current environment is development."""
    return get_env() == Env.DEV

def is_boe() -> bool:
    """Check if current environment is BOE (Beta/Staging)."""
    return get_env() == Env.BOE

def is_prod() -> bool:
    """Check if current environment is production."""
    return get_env() == Env.PROD

@functools.lru_cache(maxsize=64)
def get_env() -> Env:
    """
    Returns environment classification based on APP_ENV:
    - "BOE" if APP_ENV is "boe"
    - "PROD" if APP_ENV is "production"
    - "DEV" otherwise (default)
    
    The environment variable name can be customized by setting
    the ENV_VAR_NAME environment variable.
    """
    env_var_name = os.getenv("ENV_VAR_NAME", "APP_ENV")
    app_env = os.getenv(env_var_name, "").lower()
    
    if app_env == "boe":
        return Env.BOE
    elif app_env == "production":
        return Env.PROD
    else:
        return Env.DEV