"""Tests for the my_config package.

This module contains tests for the configuration classes.
"""

import os
import tempfile
import unittest
import yaml
from unittest.mock import patch

from my_config import BaseConfig, EnvAwareConfig, Env, get_env
from my_config.utils.singleton import GenericSingletonFactory


class TestBaseConfig(unittest.TestCase):
    """Tests for the BaseConfig class."""
    
    def setUp(self):
        # Create a temporary config file
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config_path = os.path.join(self.temp_dir.name, "test_config.yml")
        
        # Sample configuration data
        self.config_data = {
            "database": {
                "host": "localhost",
                "port": 5432,
                "username": "test_user",
                "password": "test_password"
            },
            "api": {
                "url": "https://api.example.com",
                "timeout": 30
            }
        }
        
        # Write the configuration to the file
        with open(self.config_path, "w") as f:
            yaml.dump(self.config_data, f)

        # Patch the resolve_file_path method to return our temporary config path
        self.patcher = patch('my_config.utils.singleton.GenericSingletonFactory.resolve_file_path', return_value=self.config_path)
        self.mock_resolve_file_path = self.patcher.start()

    def tearDown(self):
        # Clean up the temporary directory
        self.temp_dir.cleanup()
        self.patcher.stop()

    def test_base_config_loading(self):
        """Test that BaseConfig loads configuration correctly."""
        # Create a test config class
        class TestConfig(BaseConfig):
            CONFIG_FILENAME = "test_config.yml"

        # Get the singleton instance
        config = TestConfig.get_instance()
        
        # Check that the configuration was loaded correctly
        self.assertEqual(config.get("database")["host"], "localhost")
        self.assertEqual(config.get("api")["url"], "https://api.example.com")
    
    def test_singleton_behavior(self):
        """Test that BaseConfig behaves as a singleton."""
        # Create a test config class
        class TestConfig(BaseConfig):
            CONFIG_FILENAME = "test_config.yml"

        # Get two instances
        config1 = TestConfig.get_instance()
        config2 = TestConfig.get_instance()
        
        # Check that they are the same object
        self.assertIs(config1, config2)


if __name__ == "__main__":
    unittest.main()