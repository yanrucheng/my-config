#!/usr/bin/env python3
"""
Example demonstrating the improved BaseConfig implementation following
SingletonFileLoader best practices.

This example shows how to use the enhanced BaseConfig class with proper
parameter handling, verbosity control, and multiple initialization methods.
"""

import os
import tempfile
from pathlib import Path

from jinnang.verbosity import Verbosity
from my_config.base import BaseConfig


class ExampleConfig(BaseConfig):
    """Example configuration class extending BaseConfig"""
    
    def get_database_url(self) -> str:
        """Get database URL from configuration"""
        return self.get('database_url', 'sqlite:///default.db')
    
    def get_debug_mode(self) -> bool:
        """Get debug mode setting"""
        return self.get('debug', False)
    
    def get_api_key(self) -> str:
        """Get API key from configuration"""
        return self.get('api_key', '')


def run_example():
    print("--- Improved BaseConfig Example ---")

    # Create a temporary directory and configuration file for demonstration
    with tempfile.TemporaryDirectory() as tmpdir_name:
        temp_path = Path(tmpdir_name)
        config_filename = "app_config.yml"
        config_content = """
# Example application configuration
database_url: "postgresql://user:pass@localhost/myapp"
debug: true
api_key: "your-secret-api-key-here"
log_level: "INFO"
features:
  - "feature_a"
  - "feature_b"
  - "feature_c"
"""
        
        # Create the configuration file
        config_file_path = temp_path / config_filename
        with open(config_file_path, "w") as f:
            f.write(config_content)
        
        print(f"Created temporary config file: {config_file_path}")

        # 1. Demonstrate loading config by filename and search locations
        print("\n1. Loading config using filename and search locations...")
        config1 = ExampleConfig(
            filename=config_filename,
            search_locations=[str(temp_path)],
            verbosity=Verbosity.FULL
        )
        
        if config1.loaded_filepath:
            print(f"✓ Successfully loaded config: {config1.loaded_filepath}")
            print(f"  Database URL: {config1.get_database_url()}")
            print(f"  Debug Mode: {config1.get_debug_mode()}")
            print(f"  Log Level: {config1.get('log_level')}")
        else:
            print("✗ Failed to load config by filename")

        # 2. Demonstrate loading config by explicit path
        print("\n2. Loading config using explicit path...")
        config2 = ExampleConfig(
            explicit_path=str(config_file_path),
            verbosity=Verbosity.FULL
        )
        
        if config2.loaded_filepath:
            print(f"✓ Successfully loaded config: {config2.loaded_filepath}")
            print(f"  Features: {config2.get('features')}")
        else:
            print("✗ Failed to load config by explicit path")

        # 3. Demonstrate singleton behavior
        print("\n3. Demonstrating singleton behavior...")
        config3 = ExampleConfig(
            filename=config_filename,
            search_locations=[str(temp_path)],
            verbosity=Verbosity.ONCE
        )
        
        print(f"config1 is config2: {config1 is config2}")
        print(f"config1 is config3: {config1 is config3}")
        print(f"All configs point to same instance: {config1 is config2 is config3}")

        # 4. Demonstrate handling of non-existent file
        print("\n4. Attempting to load non-existent config...")
        
        # Clear singleton cache to test new instance
        ExampleConfig._instances.clear()
        
        try:
            config_missing = ExampleConfig(
                filename="missing_config.yml",
                search_locations=[str(temp_path)],
                verbosity=Verbosity.FULL
            )
            
            if config_missing.loaded_filepath:
                print("✗ Unexpectedly loaded missing file")
            else:
                print("✓ Correctly handled missing config file")
                print(f"  Database URL (default): {config_missing.get_database_url()}")
                print(f"  Debug Mode (default): {config_missing.get_debug_mode()}")
        except Exception as e:
            print(f"✓ Properly handled missing file with exception: {e}")

        # 5. Demonstrate different verbosity levels
        print("\n5. Testing different verbosity levels...")
        
        # Clear singleton cache
        ExampleConfig._instances.clear()
        
        print("\n  With ONCE verbosity:")
        config_once = ExampleConfig(
            filename=config_filename,
            search_locations=[str(temp_path)],
            verbosity=Verbosity.ONCE
        )
        
        # Clear singleton cache
        ExampleConfig._instances.clear()
        
        print("\n  With DETAIL verbosity:")
        config_detail = ExampleConfig(
            filename=config_filename,
            search_locations=[str(temp_path)],
            verbosity=Verbosity.DETAIL
        )

    print("\n--- Example Finished ---")


if __name__ == "__main__":
    run_example()