#!/usr/bin/env python3
"""
Example demonstrating the configuration file resolution process.

This script shows how the my_config package resolves configuration files
with the following priority order:
1. Explicitly specified path in code (highest priority)
2. Path from environment variable (if specified and exists)
3. Search in provided or default locations
"""

import os
import sys
import logging
import tempfile
import yaml

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Add the parent directory to sys.path to import my_config
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from my_config import BaseConfig
from my_config.utils.singleton import GenericSingletonFactory

# Clear any existing singleton instances
GenericSingletonFactory._instances = {}

# Create temporary configuration files for demonstration
def create_temp_config_files():
    """Create temporary configuration files for demonstration"""
    # Create a temporary directory
    temp_dir = tempfile.mkdtemp(prefix="my_config_example_")
    print(f"Created temporary directory: {temp_dir}")
    
    # Create a config file in the temp directory
    temp_config_path = os.path.join(temp_dir, "config.yml")
    with open(temp_config_path, "w") as f:
        yaml.dump({
            "database": {
                "host": "localhost",
                "port": 5432,
                "name": "example_db"
            },
            "api": {
                "url": "https://api.example.com",
                "timeout": 30
            }
        }, f)
    
    # Create an environment-specific config file
    env_config_path = os.path.join(temp_dir, "env_config.yml")
    with open(env_config_path, "w") as f:
        yaml.dump({
            "database": {
                "host": "env-db.example.com",
                "port": 5432,
                "name": "env_example_db"
            },
            "api": {
                "url": "https://env-api.example.com",
                "timeout": 60
            }
        }, f)
    
    # Create a code-specified config file
    code_config_path = os.path.join(temp_dir, "code_config.yml")
    with open(code_config_path, "w") as f:
        yaml.dump({
            "database": {
                "host": "code-db.example.com",
                "port": 5432,
                "name": "code_example_db"
            },
            "api": {
                "url": "https://code-api.example.com",
                "timeout": 90
            }
        }, f)
    
    return temp_dir, temp_config_path, env_config_path, code_config_path

# Example 1: Default resolution (search in default locations)
def example_default_resolution():
    print("\n=== Example 1: Default Resolution ===\n")
    
    # Define a custom config class that overrides the default location
    class DefaultResolutionConfig(BaseConfig):
        CONFIG_FILENAME = "config.yml"  # This will be searched in default locations
    
    # Clear any existing singleton instances
    GenericSingletonFactory._instances = {}
    
    # Load the configuration
    config = DefaultResolutionConfig.get_instance()
    
    # Print the loaded configuration
    print(f"Loaded configuration: {config.data}")

# Example 2: Environment variable resolution
def example_env_var_resolution(env_config_path):
    print("\n=== Example 2: Environment Variable Resolution ===\n")
    
    # Set the environment variable
    os.environ["CONFIG_PATH"] = env_config_path
    print(f"Set CONFIG_PATH environment variable to: {env_config_path}")
    
    # Define a custom config class
    class EnvVarConfig(BaseConfig):
        CONFIG_FILENAME = "non_existent_config.yml"  # This file doesn't exist
    
    # Clear any existing singleton instances
    GenericSingletonFactory._instances = {}
    
    # Load the configuration
    config = EnvVarConfig.get_instance()
    
    # Print the loaded configuration
    print(f"Loaded configuration: {config.data}")
    
    # Clean up
    del os.environ["CONFIG_PATH"]

# Example 3: Code-specified path (highest priority)
def example_code_specified_path(code_config_path, env_config_path):
    print("\n=== Example 3: Code-Specified Path (Highest Priority) ===\n")
    
    # Set the environment variable (which should be ignored)
    os.environ["CONFIG_PATH"] = env_config_path
    print(f"Set CONFIG_PATH environment variable to: {env_config_path}")
    
    # Define a custom config class with an explicit path
    class CodeSpecifiedConfig(BaseConfig):
        CONFIG_FILENAME = code_config_path  # This should take highest priority
    
    # Clear any existing singleton instances
    GenericSingletonFactory._instances = {}
    
    # Load the configuration
    config = CodeSpecifiedConfig.get_instance()
    
    # Print the loaded configuration
    print(f"Loaded configuration: {config.data}")
    
    # Clean up
    del os.environ["CONFIG_PATH"]

# Main function
def main():
    # Create temporary configuration files
    temp_dir, temp_config_path, env_config_path, code_config_path = create_temp_config_files()
    
    try:
        # Run the examples
        example_default_resolution()
        example_env_var_resolution(env_config_path)
        example_code_specified_path(code_config_path, env_config_path)
    finally:
        # Clean up temporary files
        import shutil
        shutil.rmtree(temp_dir)
        print(f"\nCleaned up temporary directory: {temp_dir}")

if __name__ == "__main__":
    main()