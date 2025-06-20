#!/usr/bin/env python3
"""
Example demonstrating the fix for recursive configuration loading.

This script shows how the configuration system handles potential recursive
loading scenarios, such as when a logger tries to access configuration
during the configuration loading process.
"""

import os
import sys
import logging
import tempfile

# Add the parent directory to the path so we can import my_config
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from my_config.base import BaseConfig, DefaultConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Create a custom formatter that uses configuration
class ConfigAwareFormatter(logging.Formatter):
    def __init__(self, fmt=None, datefmt=None, style='%'):
        super().__init__(fmt, datefmt, style)
    
    def formatTime(self, record, datefmt=None):
        # This will try to access configuration during formatting
        # which could cause recursion if not handled properly
        try:
            timezone = DefaultConfig.get_instance().get('timezone', 'UTC')
            logger.debug(f"Using timezone from config: {timezone}")
        except Exception as e:
            logger.debug(f"Error getting timezone from config: {e}")
            timezone = 'UTC'
        
        return super().formatTime(record, datefmt)

# Create a test configuration class
class TestConfig(BaseConfig):
    CONFIG_FILENAME = "test_config.yml"

def create_temp_config_file():
    """Create a temporary configuration file for testing."""
    temp_dir = tempfile.TemporaryDirectory()
    config_path = os.path.join(temp_dir.name, "test_config.yml")
    
    with open(config_path, 'w') as f:
        f.write("""# Test configuration
timezone: America/New_York
database:
  host: localhost
  port: 5432
  username: test_user
  password: test_password
""")
    
    return temp_dir, config_path

def test_recursive_config_loading():
    """Test that the configuration system handles recursive loading correctly."""
    # Create a temporary configuration file
    temp_dir, config_path = create_temp_config_file()
    
    try:
        # Set up a handler with our custom formatter
        handler = logging.StreamHandler()
        formatter = ConfigAwareFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        
        # Add the handler to the root logger
        root_logger = logging.getLogger()
        root_logger.addHandler(handler)
        
        # Override the CONFIG_FILENAME for our test
        TestConfig.CONFIG_FILENAME = config_path
        
        # This should not cause infinite recursion
        logger.info("Loading configuration...")
        config = TestConfig.get_instance()
        
        # Access some configuration values
        timezone = config.get('timezone')
        db_host = config.get('database', {}).get('host')
        
        logger.info(f"Loaded configuration with timezone: {timezone} and database host: {db_host}")
        
        # Test DefaultConfig with a non-existent file
        # This should not cause errors even though the file doesn't exist
        default_config = DefaultConfig.get_instance()
        default_timezone = default_config.get('timezone', 'UTC')
        
        logger.info(f"Default configuration timezone: {default_timezone}")
        
        return True
    except Exception as e:
        logger.error(f"Error in test: {e}")
        return False
    finally:
        # Clean up
        temp_dir.cleanup()

def main():
    """Run the example."""
    success = test_recursive_config_loading()
    
    if success:
        logger.info("Test completed successfully!")
    else:
        logger.error("Test failed!")

if __name__ == "__main__":
    main()