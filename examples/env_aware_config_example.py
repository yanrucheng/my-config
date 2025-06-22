#!/usr/bin/env python3
"""
Example demonstrating the improved EnvAwareConfig implementation following
SingletonFileLoader best practices.

This example shows how to use the enhanced EnvAwareConfig class with proper
parameter handling, verbosity control, and environment-specific file loading.
"""

import os
import tempfile
from pathlib import Path

from my_config.env_aware import EnvAwareConfig
from jinnang.verbosity import Verbosity

def run_example():
    print("--- EnvAwareConfig Example ---")

    # 1. Create a temporary directory and environment-specific config files
    with tempfile.TemporaryDirectory() as tmpdir_name:
        temp_path = Path(tmpdir_name)
        
        # Create different environment config files
        prod_content = "environment: production\nlog_level: ERROR\ndb_pool_size: 20"
        boe_content = "environment: boe\nlog_level: WARN\ndb_pool_size: 10"
        dev_content = "environment: development\nlog_level: DEBUG\ndb_pool_size: 5"
        
        # Create only dev and boe files (prod will be missing to test fallback)
        boe_file = temp_path / "app.boe.yml"
        dev_file = temp_path / "app.dev.yml"
        
        with open(boe_file, "w") as f:
            f.write(boe_content)
        with open(dev_file, "w") as f:
            f.write(dev_content)
        
        print(f"Created config files in: {temp_path}")
        print(f"  - {boe_file.name}")
        print(f"  - {dev_file.name}")
        print(f"  - app.prod.yml (missing - will test fallback)")

        # 2. Demonstrate environment-aware loading with base filename
        print("\n=== Test 1: Loading with base filename (fallback order: prod -> boe -> dev) ===")
        try:
            config = EnvAwareConfig(
                base_filename="app.yml",
                search_locations=[str(temp_path)],
                verbosity=Verbosity.FULL
            )
            print(f"✓ Successfully loaded: {config.loaded_filepath}")
            print(f"  File found: {Path(config.loaded_filepath).name}")
        except FileNotFoundError as e:
            print(f"✗ Failed to load config: {e}")

        # 3. Demonstrate explicit environment filenames
        print("\n=== Test 2: Loading with explicit environment filenames ===")
        try:
            # Clear singleton cache for new test
            EnvAwareConfig._instances.clear()
            
            custom_config = EnvAwareConfig(
                prod_filename="custom.prod.yml",  # This won't exist
                boe_filename="app.boe.yml",       # This exists
                dev_filename="app.dev.yml",       # This exists
                search_locations=[str(temp_path)],
                verbosity=Verbosity.DETAIL
            )
            print(f"✓ Successfully loaded: {custom_config.loaded_filepath}")
            print(f"  File found: {Path(custom_config.loaded_filepath).name}")
        except FileNotFoundError as e:
            print(f"✗ Failed to load config: {e}")

        # 4. Demonstrate minimal verbosity
        print("\n=== Test 3: Loading with minimal verbosity ===")
        try:
            # Clear singleton cache for new test
            EnvAwareConfig._instances.clear()
            
            quiet_config = EnvAwareConfig(
                base_filename="app.yml",
                search_locations=[str(temp_path)],
                verbosity=Verbosity.ONCE  # Minimal logging
            )
            print(f"✓ Successfully loaded with minimal verbosity: {Path(quiet_config.loaded_filepath).name}")
        except FileNotFoundError as e:
            print(f"✗ Failed to load config: {e}")

        # 5. Demonstrate singleton behavior
        print("\n=== Test 4: Singleton behavior ===")
        try:
            # Get another instance - should be the same object
            same_config = EnvAwareConfig.get_instance()
            print(f"✓ Singleton check: {quiet_config is same_config}")
            print(f"  Both instances point to: {Path(same_config.loaded_filepath).name}")
        except Exception as e:
            print(f"✗ Singleton test failed: {e}")

        # 6. Demonstrate failure case (no matching files)
        print("\n=== Test 5: Failure case (no matching environment files) ===")
        try:
            # Clear singleton cache for new test
            EnvAwareConfig._instances.clear()
            
            # Try to load files that don't exist
            fail_config = EnvAwareConfig(
                base_filename="nonexistent.yml",
                search_locations=[str(temp_path)],
                verbosity=Verbosity.FULL
            )
            print(f"✗ Unexpectedly succeeded: {fail_config.loaded_filepath}")
        except FileNotFoundError as e:
            print(f"✓ Correctly failed with expected error: {e}")

        # 7. Create all environment files and test priority
        print("\n=== Test 6: Priority testing (prod > boe > dev) ===")
        try:
            # Clear singleton cache for new test
            EnvAwareConfig._instances.clear()
            
            # Create prod file
            prod_file = temp_path / "priority.prod.yml"
            with open(prod_file, "w") as f:
                f.write(prod_content)
            
            # Create boe and dev files too
            boe_priority_file = temp_path / "priority.boe.yml"
            dev_priority_file = temp_path / "priority.dev.yml"
            with open(boe_priority_file, "w") as f:
                f.write(boe_content)
            with open(dev_priority_file, "w") as f:
                f.write(dev_content)
            
            priority_config = EnvAwareConfig(
                base_filename="priority.yml",
                search_locations=[str(temp_path)],
                verbosity=Verbosity.DETAIL
            )
            
            loaded_file = Path(priority_config.loaded_filepath).name
            print(f"✓ Priority test - loaded: {loaded_file}")
            if "prod" in loaded_file:
                print("  ✓ Correctly prioritized production config")
            else:
                print(f"  ⚠ Expected prod file, but got: {loaded_file}")
                
        except Exception as e:
            print(f"✗ Priority test failed: {e}")

    print("\n--- Example Finished ---")

if __name__ == "__main__":
    run_example()