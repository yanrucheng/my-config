"""Tests for BaseConfig class."""

import os
import tempfile
import unittest
import yaml
from unittest.mock import patch, MagicMock

from my_config.base import BaseConfig
from jinnang.verbosity import Verbosity


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

    def tearDown(self):
        # Clean up the temporary directory
        self.temp_dir.cleanup()
        # Clear singleton instances to ensure fresh instances for each test
        BaseConfig._instances.clear()

    def test_config_loading(self):
        """Test that configuration is loaded correctly from file."""
        config = BaseConfig(filename="test_config.yml", config_dir=self.temp_dir.name)
        config.load_from_file()
        
        # Test that the configuration data is loaded correctly
        self.assertEqual(config.get("database.host"), "localhost")
        self.assertEqual(config.get("database.port"), 5432)
        self.assertEqual(config.get("api.url"), "https://api.example.com")
        self.assertEqual(config.get("api.timeout"), 30)

    def test_get_method(self):
        """Test the get method with various key formats."""
        config = BaseConfig(filename="test_config.yml", config_dir=self.temp_dir.name)
        config.config_dir = self.temp_dir.name
        config.load_from_file()
        
        # Test nested key access
        self.assertEqual(config.get("database.host"), "localhost")
        self.assertEqual(config.get("database.port"), 5432)
        
        # Test non-existent key
        self.assertIsNone(config.get("non_existent_key"))
        
        # Test default value
        self.assertEqual(config.get("non_existent_key", "default"), "default")


if __name__ == '__main__':
    unittest.main()