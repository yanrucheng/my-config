"""Test module for configuration classes.

This module contains tests for the configuration classes.
"""

import os
import tempfile
import unittest
import yaml
from unittest.mock import patch, MagicMock

from my_config.base import BaseConfig
from my_config.env_aware import EnvAwareConfig
from my_config.llm import LLMConfig
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
        from jinnang.common.patterns import Singleton
        Singleton._instances.clear()

    def test_base_config_loading(self):
        """Test that BaseConfig loads configuration correctly."""
        with patch('jinnang.common.patterns.SingletonFileLoader.resolve_file_path', return_value=self.config_path):
            config = BaseConfig(
                filename="test_config.yml",
                caller_module_path=__file__,
                verbosity=Verbosity.ONCE
            )
            
            # Check that the configuration was loaded correctly
            self.assertEqual(config.get("database")["host"], "localhost")
            self.assertEqual(config.get("api")["url"], "https://api.example.com")
            self.assertEqual(config.data["database"]["port"], 5432)
    
    def test_base_config_get_method(self):
        """Test the get method with default values."""
        with patch('jinnang.common.patterns.SingletonFileLoader.resolve_file_path', return_value=self.config_path):
            config = BaseConfig(
                filename="test_config.yml",
                caller_module_path=__file__,
                verbosity=Verbosity.ONCE
            )
            
            # Test existing key
            self.assertEqual(config.get("database")["host"], "localhost")
            
            # Test non-existing key with default
            self.assertEqual(config.get("nonexistent", "default_value"), "default_value")
            
            # Test non-existing key without default
            self.assertIsNone(config.get("nonexistent"))


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
        # Clear singleton instances to ensure fresh instances for each test
        from jinnang.common.patterns import Singleton
        Singleton._instances.clear()

    @patch.dict(os.environ, {'APP_ENV': 'development'})
    def test_env_aware_config_with_app_env_dev(self):
        """Test that dev config is loaded when APP_ENV is set to development."""
        with patch('jinnang.common.patterns.SingletonFileLoader.resolve_file_path') as mock_resolve:
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
        with patch('jinnang.common.patterns.SingletonFileLoader.resolve_file_path') as mock_resolve:
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
        with patch('jinnang.common.patterns.SingletonFileLoader.resolve_file_path') as mock_resolve:
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
            with patch('jinnang.common.patterns.SingletonFileLoader.resolve_file_path') as mock_resolve:
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
        with patch('jinnang.common.patterns.SingletonFileLoader.resolve_file_path') as mock_resolve:
            mock_resolve.side_effect = FileNotFoundError("File not found")
            
            with self.assertRaises(FileNotFoundError) as context:
                EnvAwareConfig(
                    base_filename="config.yml",
                    caller_module_path=__file__,
                    verbosity=Verbosity.ONCE
                )
            
            self.assertIn("Could not find any environment-specific config file", str(context.exception))


class TestLLMConfig(unittest.TestCase):
    """Tests for the LLMConfig class."""
    
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.llm_config_path = os.path.join(self.temp_dir.name, "llm.yml")
        
        # Sample LLM configuration data
        self.llm_config_data = {
            "providers": {
                "openai": {
                    "api_key": "test_openai_key",
                    "base_url": "https://api.openai.com/v1",
                    "models": [
                        {
                            "name": "gpt-4",
                            "model": "gpt-4",
                            "tags": ["chat", "large"],
                            "description": "OpenAI GPT-4 model"
                        },
                        {
                            "name": "gpt-3.5-turbo",
                            "model": "gpt-3.5-turbo",
                            "tags": ["chat", "small"],
                            "description": "OpenAI GPT-3.5 Turbo model"
                        }
                    ]
                },
                "anthropic": {
                    "api_key": "test_anthropic_key",
                    "base_url": "https://api.anthropic.com/v1",
                    "models": [
                        {
                            "name": "claude-3-opus",
                            "model": "claude-3-opus-20240229",
                            "tags": ["chat", "large"],
                            "description": "Anthropic Claude 3 Opus model"
                        }
                    ]
                }
            }
        }
        
        # Write the configuration to the file
        with open(self.llm_config_path, "w") as f:
            yaml.dump(self.llm_config_data, f)

    def tearDown(self):
        self.temp_dir.cleanup()
        # Clear singleton instances to ensure fresh instances for each test
        from jinnang.common.patterns import Singleton
        Singleton._instances.clear()

    def test_llm_config_loading(self):
        """Test that LLMConfig loads and processes models correctly."""
        with patch('jinnang.common.patterns.SingletonFileLoader.resolve_file_path', return_value=self.llm_config_path):
            config = LLMConfig(
                filename="llm.yml",
                caller_module_path=__file__,
                verbosity=Verbosity.ONCE
            )
            
            # Check that models were loaded correctly
            self.assertEqual(len(config.data), 3)  # 2 OpenAI + 1 Anthropic
            self.assertIn("openai/gpt-4", config.data)
            self.assertIn("openai/gpt-3.5-turbo", config.data)
            self.assertIn("anthropic/claude-3-opus", config.data)

    def test_llm_config_get_model(self):
        """Test getting specific models by name."""
        with patch('jinnang.common.patterns.SingletonFileLoader.resolve_file_path', return_value=self.llm_config_path):
            config = LLMConfig(
                filename="llm.yml",
                caller_module_path=__file__,
                verbosity=Verbosity.ONCE
            )
            
            # Test getting existing model
            gpt4_model = config.get("openai/gpt-4")
            self.assertIsNotNone(gpt4_model)
            self.assertEqual(gpt4_model.name, "openai/gpt-4")
            self.assertEqual(gpt4_model.model, "gpt-4")
            self.assertEqual(gpt4_model.provider, "openai")
            self.assertEqual(gpt4_model.api_key, "test_openai_key")
            
            # Test getting non-existing model
            non_existing = config.get("nonexistent/model")
            self.assertIsNone(non_existing)

    def test_llm_config_get_model_by_tag(self):
        """Test getting models by tag."""
        with patch('jinnang.common.patterns.SingletonFileLoader.resolve_file_path', return_value=self.llm_config_path):
            config = LLMConfig(
                filename="llm.yml",
                caller_module_path=__file__,
                verbosity=Verbosity.ONCE
            )
            
            # Test getting model by tag
            large_model = config.get_model_by_tag("large")
            self.assertIsNotNone(large_model)
            self.assertIn("large", large_model.tags)
            
            # Test getting model by non-existing tag
            non_existing = config.get_model_by_tag("nonexistent")
            self.assertIsNone(non_existing)

    def test_llm_config_get_models_by_tag(self):
        """Test getting multiple models by tag."""
        with patch('jinnang.common.patterns.SingletonFileLoader.resolve_file_path', return_value=self.llm_config_path):
            config = LLMConfig(
                filename="llm.yml",
                caller_module_path=__file__,
                verbosity=Verbosity.ONCE
            )
            
            # Test getting models by tag
            chat_models = config.get_models_by_tag("chat")
            self.assertEqual(len(chat_models), 3)  # All models have 'chat' tag
            
            large_models = config.get_models_by_tag("large")
            self.assertEqual(len(large_models), 2)  # gpt-4 and claude-3-opus
            
            small_models = config.get_models_by_tag("small")
            self.assertEqual(len(small_models), 1)  # gpt-3.5-turbo

    def test_llm_config_model_api_url(self):
        """Test model API URL construction."""
        with patch('jinnang.common.patterns.SingletonFileLoader.resolve_file_path', return_value=self.llm_config_path):
            config = LLMConfig(
                filename="llm.yml",
                caller_module_path=__file__,
                verbosity=Verbosity.ONCE
            )
            
            gpt4_model = config.get("openai/gpt-4")
            self.assertEqual(gpt4_model.get_full_api_url(), "https://api.openai.com/v1")
            
            claude_model = config.get("anthropic/claude-3-opus")
            self.assertEqual(claude_model.get_full_api_url(), "https://api.anthropic.com/v1")


if __name__ == "__main__":
    unittest.main()