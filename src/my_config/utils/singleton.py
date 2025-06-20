"""Singleton utility for configuration classes.

This module provides a generic singleton factory implementation that can be used
to ensure only one instance of a configuration class exists.
"""

import os
from typing import TypeVar, Type, Dict, Optional, List, Any

T = TypeVar('T')

class GenericSingletonFactory:
    """
    Generic singleton factory base class compatible with Python 3.8+
    """
    
    _instances: Dict[Type['GenericSingletonFactory'], 'GenericSingletonFactory'] = {}
    
    @classmethod
    def get_instance(cls: Type[T], *args, **kwargs) -> T:
        """Get or create the singleton instance"""
        # Check if we're already in the process of creating this instance
        # This prevents infinite recursion when logging during initialization
        creating_key = f"_creating_{cls.__name__}"
        if hasattr(cls, creating_key) and getattr(cls, creating_key):
            # Return a temporary empty instance to break the recursion
            # This is only used during initialization
            return cls.__new__(cls)
            
        if cls not in cls._instances:
            # Mark that we're in the process of creating this instance
            setattr(cls, creating_key, True)
            try:
                cls._instances[cls] = cls(*args, **kwargs)
            finally:
                # Always clean up the creating flag
                setattr(cls, creating_key, False)
        return cls._instances[cls]
    
    @staticmethod
    def resolve_file_path(
        explicit_path: Optional[str] = None,
        filename: str = "",
        search_locations: Optional[List[str]] = None,
        env_var_name: Optional[str] = None
    ) -> str:
        """
        File path resolution helper for Python 3.8+
        
        Priority order for file path resolution:
        1. Explicitly specified path in code (highest priority)
        2. Path from environment variable (if specified and exists)
        3. Search in provided or default locations
        
        Args:
            explicit_path: Path explicitly specified in code (highest priority)
            filename: Name of the file to find
            search_locations: List of directories to search in
            env_var_name: Name of environment variable that might contain the file path
        """
        # Import logging inside the function to avoid circular imports
        import logging
        
        # Use a try-except block for all logging operations to prevent recursion
        try:
            logger = logging.getLogger(__name__)
            log_enabled = True
        except Exception:
            # If logging setup fails, disable logging for this function
            log_enabled = False
        
        found_paths = []
        
        # 1. Check explicit path (highest priority)
        if explicit_path:
            if os.path.exists(explicit_path):
                if log_enabled:
                    try:
                        logger.info(f"Using explicitly specified config path: {explicit_path}")
                    except Exception:
                        pass  # Ignore logging errors
                return explicit_path
            else:
                if log_enabled:
                    try:
                        logger.warning(f"Explicitly specified path does not exist: {explicit_path}")
                    except Exception:
                        pass  # Ignore logging errors
                found_paths.append(("explicit_path", explicit_path, False))
        
        # 2. Check environment variable
        if env_var_name:
            env_path = os.getenv(env_var_name)
            if env_path and os.path.exists(env_path):
                if log_enabled:
                    try:
                        logger.info(f"Using config path from environment variable {env_var_name}: {env_path}")
                    except Exception:
                        pass  # Ignore logging errors
                return env_path
            elif env_path:
                if log_enabled:
                    try:
                        logger.warning(f"Path from environment variable {env_var_name} does not exist: {env_path}")
                    except Exception:
                        pass  # Ignore logging errors
                found_paths.append((f"env_var:{env_var_name}", env_path, False))
        
        # 3. Search in locations
        default_locations = [
            '.',  # Current directory
            os.path.dirname(__file__),  # Current file directory
            os.path.join(os.path.dirname(__file__), '..'),  # Parent dir
            os.path.join(os.path.dirname(__file__), '../..'),  # Grandparent dir
        ]
        
        locations = search_locations if search_locations is not None else default_locations
        
        for directory in locations:
            potential_path = os.path.join(directory, filename)
            if os.path.exists(potential_path):
                if log_enabled:
                    try:
                        logger.info(f"Found config file in search location: {potential_path}")
                    except Exception:
                        pass  # Ignore logging errors
                return potential_path
            else:
                found_paths.append(("search_location", potential_path, False))
        
        # Log all attempted paths for debugging
        if log_enabled:
            try:
                logger.error(f"Config file resolution failed. Attempted paths:")
                for source, path, exists in found_paths:
                    logger.error(f"  - [{source}] {path} (exists: {exists})")
            except Exception:
                pass  # Ignore logging errors
                
        raise FileNotFoundError(
            f"Could not find {filename} in any of these locations: {locations}"
        )