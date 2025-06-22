import os
import tempfile
import unittest
from unittest.mock import patch
import yaml

from my_config.env_aware import EnvAwareConfig
from jinnang.verbosity import Verbosity


class TestEnvAwareConfig(unittest.TestCase):
    """Tests for the EnvAwareConfig class."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.prod_config_path = os.path.join(self.temp_dir.name, "config.prod.yml")
        self.boe_config_path = os.path.join(self.temp_dir.name, "config.boe.yml")
        self.dev_config_path = os.path.join(self.temp_dir.name, "config.dev.yml")

        self.prod_config_data = {
            "app_env": "production",
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
            "app_env": "boe",
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
            "app_env": "development",
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


    @patch.dict(os.environ, {'APP_ENV': 'development'})
    def test_env_aware_config_with_app_env_dev(self):
        """Test that dev config is loaded when APP_ENV is set to development."""
        with patch('jinnang.path.path.RelPathSeeker.resolve_file_path') as mock_resolve:
            def side_effect(filename=None, **kwargs):
                if filename == "config.dev.yml":
                    return self.dev_config_path
                raise FileNotFoundError(f"File {filename} not found")
            
            mock_resolve.side_effect = side_effect
            
            config = EnvAwareConfig(
                base_filename="config.yml",
                caller_module_path=__file__,
                verbosity=Verbosity.ONCE
            )
            
            # Should load dev config based on APP_ENV
            self.assertEqual(config.loaded_filepath, self.dev_config_path)
            self.assertEqual(config.data["app_env"], "development")

    @patch.dict(os.environ, {'APP_ENV': 'production'})
    def test_env_aware_config_with_app_env_prod(self):
        """Test that prod config is loaded when APP_ENV is set to production."""
        with patch('jinnang.path.path.RelPathSeeker.resolve_file_path') as mock_resolve:
            def side_effect(filename=None, **kwargs):
                if filename == "config.prod.yml":
                    return self.prod_config_path
                raise FileNotFoundError(f"File {filename} not found")
            
            mock_resolve.side_effect = side_effect
            
            config = EnvAwareConfig(
                base_filename="config.yml",
                caller_module_path=__file__,
                verbosity=Verbosity.ONCE
            )
            
            # Should load prod config based on APP_ENV
            self.assertEqual(config.loaded_filepath, self.prod_config_path)
            self.assertEqual(config.data["app_env"], "production")

    @patch.dict(os.environ, {'APP_ENV': 'boe'})
    def test_env_aware_config_with_app_env_boe(self):
        """Test that boe config is loaded when APP_ENV is set to boe."""
        with patch('jinnang.path.path.RelPathSeeker.resolve_file_path') as mock_resolve:
            def side_effect(filename=None, **kwargs):
                if filename == "config.boe.yml":
                    return self.boe_config_path
                raise FileNotFoundError(f"File {filename} not found")
            
            mock_resolve.side_effect = side_effect
            
            config = EnvAwareConfig(
                base_filename="config.yml",
                caller_module_path=__file__,
                verbosity=Verbosity.ONCE
            )
            
            # Should load boe config based on APP_ENV
            self.assertEqual(config.loaded_filepath, self.boe_config_path)
            self.assertEqual(config.data["app_env"], "boe")

    def test_env_aware_config_fallback_order(self):
        """Test fallback order when APP_ENV is not set."""
        with patch.dict(os.environ, {}, clear=True):  # Clear APP_ENV
            with patch('jinnang.path.path.RelPathSeeker.resolve_file_path') as mock_resolve:
                def side_effect(filename=None, **kwargs):
                    if filename == "config.prod.yml":
                        raise FileNotFoundError(f"File {filename} not found")
                    elif filename == "config.boe.yml":
                        raise FileNotFoundError(f"File {filename} not found")
                    elif filename == "config.dev.yml":
                        return self.dev_config_path
                    raise FileNotFoundError(f"File {filename} not found")
                
                mock_resolve.side_effect = side_effect
                
                config = EnvAwareConfig(
                    base_filename="config.yml",
                    caller_module_path=__file__,
                    verbosity=Verbosity.ONCE
                )
                
                # Should load dev config as fallback
                self.assertEqual(config.loaded_filepath, self.dev_config_path)

    def test_env_aware_config_no_files_found(self):
        """Test that FileNotFoundError is raised when no config files exist."""
        with patch('jinnang.path.path.RelPathSeeker.resolve_file_path') as mock_resolve:
            mock_resolve.side_effect = FileNotFoundError("File not found")
            
            with self.assertRaises(FileNotFoundError) as context:
                EnvAwareConfig(
                    base_filename="config.yml",
                    caller_module_path=__file__,
                    verbosity=Verbosity.ONCE
                )
            
            self.assertIn("Could not find any environment-specific config file", str(context.exception))


if __name__ == "__main__":
    unittest.main()