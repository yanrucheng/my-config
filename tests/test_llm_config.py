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
                             "notes": ["chat", "large"],
                             "purpose": ["llm_primary"]
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
                             "notes": ["chat", "large"],
                             "purpose": ["vlm_primary"]
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
                            "notes": ["chat", "large"],
                            "purpose": ["llm_primary"],
                            "description": "OpenAI GPT-4 model"
                        },
                        {
                            "name": "gpt-3.5-turbo",
                            "model": "gpt-3.5-turbo",
                            "notes": ["chat", "small"],
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
                            "notes": ["chat", "large"],
                            "purpose": ["vlm_primary"],
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

    def test_get_model_by_name(self):
        """Test getting a model by its name."""
        with patch('jinnang.path.path.RelPathSeeker.resolve_file_path', return_value=self.llm_config_path):
            config = LLMConfig(filename="llm.yml", verbosity=Verbosity.ONCE)
            model = config.get_model(model_name="gpt-4")
            self.assertIsNotNone(model)
            self.assertEqual(model.name, "openai/gpt-4")

    def test_get_model_by_purpose(self):
        """Test getting a model by its purpose."""
        with patch('jinnang.path.path.RelPathSeeker.resolve_file_path', return_value=self.llm_config_path):
            config = LLMConfig(filename="llm.yml", verbosity=Verbosity.ONCE)
            model = config.get_model(purpose="llm_primary")
            self.assertIsNotNone(model)
            self.assertEqual(model.name, "openai/gpt-4")

    def test_get_model_by_purpose_vlm(self):
        """Test getting a vlm model by its purpose."""
        with patch('jinnang.path.path.RelPathSeeker.resolve_file_path', return_value=self.llm_config_path):
            config = LLMConfig(filename="llm.yml", verbosity=Verbosity.ONCE)
            model = config.get_model(purpose="vlm_primary")
            self.assertIsNotNone(model)
            self.assertEqual(model.name, "anthropic/claude-3-opus")

    def test_get_model_conflict(self):
        """Test error when providing both name and purpose."""
        with patch('jinnang.path.path.RelPathSeeker.resolve_file_path', return_value=self.llm_config_path):
            config = LLMConfig(filename="llm.yml", verbosity=Verbosity.ONCE)
            with self.assertRaises(ValueError):
                config.get_model(model_name="gpt-4", purpose="llm_primary")

    def test_get_model_no_params(self):
        """Test error when providing no parameters."""
        with patch('jinnang.path.path.RelPathSeeker.resolve_file_path', return_value=self.llm_config_path):
            config = LLMConfig(filename="llm.yml", verbosity=Verbosity.ONCE)
            with self.assertRaises(ValueError):
                config.get_model()




if __name__ == "__main__":
    unittest.main()