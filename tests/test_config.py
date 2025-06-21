"""Tests for the my_config package.

This module contains tests for the configuration classes.
"""

import os
import tempfile
import unittest
import yaml
from unittest.mock import patch

from my_config import BaseConfig, EnvAwareConfig
from jinnang.common import SingletonFileLoader


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
        self.patcher = patch('jinnang.common.patterns.SingletonFileLoader.resolve_file_path', return_value=self.config_path)
        self.mock_resolve_file_path = self.patcher.start()

    def tearDown(self):
        # Clean up the temporary directory
        self.temp_dir.cleanup()
        self.patcher.stop()
        # Clear singleton instances to ensure fresh instances for each test
        from my_config.base import BaseConfig
        BaseConfig._instances.clear()

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




class TestEnvAwareConfig(unittest.TestCase):
    """Tests for the EnvAwareConfig class."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.prod_config_path = os.path.join(self.temp_dir.name, "config.prod.yml")
        self.boe_config_path = os.path.join(self.temp_dir.name, "config.boe.yml")
        self.dev_config_path = os.path.join(self.temp_dir.name, "config.dev.yml")

        self.prod_config_data = {
            "app": {
                "name": "MyApp",
                "environment": "production",
                "version": "1.0.0"
            },
            "database": {
                "host": "prod_db.example.com",
                "port": 5432
            },
            "feature_flags": {
                "new_ui": False,
                "beta_features": False
            }
        }

        self.boe_config_data = {
            "app": {
                "name": "MyApp",
                "environment": "boe",
                "version": "1.0.0-boe"
            },
            "database": {
                "host": "boe_db.example.com",
                "port": 5432
            },
            "feature_flags": {
                "new_ui": True,
                "beta_features": True
            }
        }

        self.dev_config_data = {
            "app": {
                "name": "MyApp",
                "environment": "development",
                "version": "1.0.0-dev"
            },
            "database": {
                "host": "localhost",
                "port": 5433
            },
            "feature_flags": {
                "new_ui": True,
                "beta_features": True,
                "debug_mode": True
            }
        }

        # Write config files
        with open(self.prod_config_path, "w") as f:
            yaml.dump(self.prod_config_data, f)
        with open(self.boe_config_path, "w") as f:
            yaml.dump(self.boe_config_data, f)
        with open(self.dev_config_path, "w") as f:
            yaml.dump(self.dev_config_data, f)

    def tearDown(self):
        self.temp_dir.cleanup()
        # Clear singleton instances to ensure fresh instances for each test
        from my_config.env_aware import EnvAwareConfig
        if EnvAwareConfig in EnvAwareConfig._instances:
            del EnvAwareConfig._instances[EnvAwareConfig]

    def test_env_aware_config_prod_priority(self):
        """Test that prod config is loaded when all files exist."""
        with patch('my_config.env_aware.EnvAwareConfig.resolve_file_path') as mock_resolve:
            def side_effect(filename, **kwargs):
                if filename == "config.prod.yml":
                    return self.prod_config_path
                elif filename == "config.boe.yml":
                    return self.boe_config_path
                elif filename == "config.dev.yml":
                    return self.dev_config_path
                raise FileNotFoundError(f"File {filename} not found")
            
            mock_resolve.side_effect = side_effect
            
            config = EnvAwareConfig(base_filename="config.yml", caller_module_path=__file__)
            
            # Should load prod config (highest priority)
            self.assertEqual(config.filepath, self.prod_config_path)

    def test_env_aware_config_boe_fallback(self):
        """Test that boe config is loaded when prod doesn't exist."""
        with patch('my_config.env_aware.EnvAwareConfig.resolve_file_path') as mock_resolve:
            def side_effect(filename, **kwargs):
                if filename == "config.prod.yml":
                    raise FileNotFoundError(f"File {filename} not found")
                elif filename == "config.boe.yml":
                    return self.boe_config_path
                elif filename == "config.dev.yml":
                    return self.dev_config_path
                raise FileNotFoundError(f"File {filename} not found")
            
            mock_resolve.side_effect = side_effect
            
            config = EnvAwareConfig(base_filename="config.yml", caller_module_path=__file__)
            
            # Should load boe config (fallback from prod)
            self.assertEqual(config.filepath, self.boe_config_path)

    def test_env_aware_config_dev_fallback(self):
        """Test that dev config is loaded when prod and boe don't exist."""
        with patch('my_config.env_aware.EnvAwareConfig.resolve_file_path') as mock_resolve:
            def side_effect(filename, **kwargs):
                if filename in ["config.prod.yml", "config.boe.yml"]:
                    raise FileNotFoundError(f"File {filename} not found")
                elif filename == "config.dev.yml":
                    return self.dev_config_path
                raise FileNotFoundError(f"File {filename} not found")
            
            mock_resolve.side_effect = side_effect
            
            config = EnvAwareConfig(base_filename="config.yml", caller_module_path=__file__)
            
            # Should load dev config (final fallback)
            self.assertEqual(config.filepath, self.dev_config_path)

    def test_env_aware_config_custom_filenames(self):
        """Test custom filenames for each environment."""
        custom_prod_path = os.path.join(self.temp_dir.name, "app.production.yml")
        custom_boe_path = os.path.join(self.temp_dir.name, "app.boe.yml")
        custom_dev_path = os.path.join(self.temp_dir.name, "app.development.yml")
        
        # Create custom config files
        with open(custom_prod_path, "w") as f:
            yaml.dump(self.prod_config_data, f)
        with open(custom_boe_path, "w") as f:
            yaml.dump(self.boe_config_data, f)
        with open(custom_dev_path, "w") as f:
            yaml.dump(self.dev_config_data, f)
        
        with patch('my_config.env_aware.EnvAwareConfig.resolve_file_path') as mock_resolve:
            def side_effect(filename, **kwargs):
                if filename == "app.production.yml":
                    return custom_prod_path
                elif filename == "app.boe.yml":
                    return custom_boe_path
                elif filename == "app.development.yml":
                    return custom_dev_path
                raise FileNotFoundError(f"File {filename} not found")
            
            mock_resolve.side_effect = side_effect
            
            config = EnvAwareConfig(
                prod_filename="app.production.yml",
                boe_filename="app.boe.yml",
                dev_filename="app.development.yml",
                caller_module_path=__file__
            )
            
            # Should load custom prod config
            self.assertEqual(config.filepath, custom_prod_path)

    def test_env_aware_config_no_files_found(self):
        """Test that FileNotFoundError is raised when no config files exist."""
        with patch('my_config.env_aware.EnvAwareConfig.resolve_file_path') as mock_resolve:
            mock_resolve.side_effect = FileNotFoundError("File not found")
            
            with self.assertRaises(FileNotFoundError) as context:
                EnvAwareConfig(base_filename="config.yml", caller_module_path=__file__)
            
            self.assertIn("Could not find any environment-specific config file", str(context.exception))

    def test_env_aware_config_singleton_behavior(self):
        """Test that EnvAwareConfig maintains singleton behavior."""
        with patch('my_config.env_aware.EnvAwareConfig.resolve_file_path') as mock_resolve:
            mock_resolve.return_value = self.prod_config_path
            
            config1 = EnvAwareConfig(base_filename="config.yml", caller_module_path=__file__)
            config2 = EnvAwareConfig.get_instance()
            
            # Should be the same instance
            self.assertIs(config1, config2)
            self.assertEqual(config1.filepath, config2.filepath)


if __name__ == "__main__":
    unittest.main()