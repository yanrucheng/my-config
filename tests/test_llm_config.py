import os
import tempfile
import unittest
from unittest.mock import patch
import yaml

from my_config.llm import LLMConfig
from jinnang.verbosity import Verbosity


class TestLLMConfigEnvVars(unittest.TestCase):
    """Tests for environment variable resolution in LLMConfig."""
    
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config_path = os.path.join(self.temp_dir.name, "test_llm_env_config.yml")
        
    def tearDown(self):
        self.temp_dir.cleanup()

    
    @patch.dict(os.environ, {'OPENAI_API_KEY': 'sk-test-openai-key-123', 'ANTHROPIC_API_KEY': 'sk-ant-test-key-456'})
    def test_llm_config_with_env_vars(self):
        """Test LLM configuration with environment variable resolution for API keys."""
        config_data = {
             "providers": {
                 "openai": {
                     "api_key": "${OPENAI_API_KEY}",
                     "base_url": "https://api.openai.com/v1",
                     "models": [
                         {
                             "name": "gpt-4",
                             "model": "gpt-4",
                             "tags": ["chat", "large", "primary", "llm"]
                         }
                     ]
                 },
                 "anthropic": {
                     "api_key": "${ANTHROPIC_API_KEY}",
                     "base_url": "https://api.anthropic.com",
                     "models": [
                         {
                             "name": "claude-3-sonnet",
                             "model": "claude-3-sonnet-20240229",
                             "tags": ["chat", "large", "primary", "vlm"]
                         }
                     ]
                 }
             }
         }
        
        with open(self.config_path, "w") as f:
            yaml.dump(config_data, f)
            
        with patch('jinnang.path.path.RelPathSeeker.resolve_file_path', return_value=self.config_path):
            llm_config = LLMConfig(
                filename="test_llm_env_config.yml",
                verbosity=Verbosity.ONCE
            )
            
            # Check that environment variables were resolved in model configs
            gpt4_model = llm_config.get("openai/gpt-4")
            claude_model = llm_config.get("anthropic/claude-3-sonnet")
            
            self.assertIsNotNone(gpt4_model)
            self.assertIsNotNone(claude_model)
            
            # Verify API keys were resolved from environment variables
            self.assertEqual(gpt4_model.api_key, "sk-test-openai-key-123")
            self.assertEqual(claude_model.api_key, "sk-ant-test-key-456")
            
            # Verify other fields remain unchanged
            self.assertEqual(gpt4_model.base_url, "https://api.openai.com/v1")
            self.assertEqual(claude_model.base_url, "https://api.anthropic.com")
            self.assertEqual(gpt4_model.model, "gpt-4")
            self.assertEqual(claude_model.model, "claude-3-sonnet-20240229")


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
                            "tags": ["chat", "large", "primary", "llm"],
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
                            "tags": ["chat", "large", "primary", "vlm"],
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


    def test_llm_config_loading(self):
        """Test that LLMConfig loads and processes models correctly."""
        with patch('jinnang.path.path.RelPathSeeker.resolve_file_path', return_value=self.llm_config_path):
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
        with patch('jinnang.path.path.RelPathSeeker.resolve_file_path', return_value=self.llm_config_path):
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
        with patch('jinnang.path.path.RelPathSeeker.resolve_file_path', return_value=self.llm_config_path):
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
        with patch('jinnang.path.path.RelPathSeeker.resolve_file_path', return_value=self.llm_config_path):
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
        with patch('jinnang.path.path.RelPathSeeker.resolve_file_path', return_value=self.llm_config_path):
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