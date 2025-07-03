import os
import tempfile
import unittest
from unittest.mock import patch
import yaml
import threading
import time

from jinnang.verbosity import Verbosity
from my_config.base import BaseConfig
from my_config.env_aware import EnvAwareConfig
from my_config.llm import LLMConfig


class TestEnvVarIntegration(unittest.TestCase):
    """Integration tests for environment variable resolution across different config types"""
    
    def setUp(self):

        
        # Create temporary directory for test files
        self.temp_dir = tempfile.TemporaryDirectory()
        
        # Set up test environment variables
        os.environ['INTEGRATION_API_KEY'] = 'sk-integration-test-key'
        os.environ['INTEGRATION_BASE_URL'] = 'https://integration.api.com'
        os.environ['INTEGRATION_TIMEOUT'] = '30'
        os.environ['INTEGRATION_DEBUG'] = 'true'
        
    def tearDown(self):
        self.temp_dir.cleanup()
        
        # Clean up environment variables
        integration_vars = ['INTEGRATION_API_KEY', 'INTEGRATION_BASE_URL', 
                           'INTEGRATION_TIMEOUT', 'INTEGRATION_DEBUG']
        for var in integration_vars:
            if var in os.environ:
                del os.environ[var]
        

    
    def test_base_config_integration(self):
        """Test environment variable resolution in BaseConfig with file loading"""
        config_data = {
            'api': {
                'key': '${INTEGRATION_API_KEY}',
                'base_url': '${INTEGRATION_BASE_URL}',
                'timeout': '${INTEGRATION_TIMEOUT}'
            },
            'debug': '${INTEGRATION_DEBUG}',
            'static_value': 'unchanged'
        }
        
        config_path = os.path.join(self.temp_dir.name, 'integration_config.yml')
        with open(config_path, 'w') as f:
            yaml.dump(config_data, f)
        
        with patch('jinnang.path.path.RelPathSeeker.resolve_file_path', return_value=config_path):
            config = BaseConfig(
                filename='integration_config.yml',
                caller_module_path=__file__,
                verbosity=Verbosity.ONCE
            )
            
            # Verify environment variables were resolved
            self.assertEqual(config.get('api')['key'], 'sk-integration-test-key')
            self.assertEqual(config.get('api')['base_url'], 'https://integration.api.com')
            self.assertEqual(config.get('api')['timeout'], '30')
            self.assertEqual(config.get('debug'), 'true')
            self.assertEqual(config.get('static_value'), 'unchanged')
    
    def test_env_aware_config_integration(self):
        """Test environment variable resolution in EnvAwareConfig"""
        # Create environment-specific configs with env vars
        dev_config = {
            'database': {
                'host': '${INTEGRATION_BASE_URL}',
                'port': 5432,
                'debug': '${INTEGRATION_DEBUG}'
            }
        }
        
        prod_config = {
            'database': {
                'host': '${INTEGRATION_BASE_URL}',
                'port': 5432,
                'debug': 'false'
            }
        }
        
        # Write config files
        dev_path = os.path.join(self.temp_dir.name, 'integration_config.dev.yml')
        prod_path = os.path.join(self.temp_dir.name, 'integration_config.prod.yml')
        
        with open(dev_path, 'w') as f:
            yaml.dump(dev_config, f)
        with open(prod_path, 'w') as f:
            yaml.dump(prod_config, f)
        
        # Test with DEV environment
        with patch.dict(os.environ, {'APP_ENV': 'development'}):
            with patch('jinnang.path.path.RelPathSeeker.resolve_file_path') as mock_resolve:
                def side_effect(filename=None, **kwargs):
                    if filename == "integration_config.dev.yml":
                        return dev_path
                    raise FileNotFoundError(f"File {filename} not found")
                
                mock_resolve.side_effect = side_effect
                
                config = EnvAwareConfig(
                    base_filename='integration_config.yml',
                    caller_module_path=__file__,
                    verbosity=Verbosity.ONCE
                )
                
                self.assertEqual(config.get('database')['host'], 'https://integration.api.com')
                self.assertEqual(config.get('database')['debug'], 'true')
    
    def test_llm_config_integration_comprehensive(self):
        """Test comprehensive LLM configuration with environment variables"""
        llm_config_data = {
            'providers': {
                'openai': {
                    'api_key': '${INTEGRATION_API_KEY}',
                    'base_url': '${INTEGRATION_BASE_URL}',
                    'models': [
                        {
                            'name': 'gpt-4-integration',
                            'model': 'gpt-4',
                            'notes': ['chat', 'large'],
                            'purpose': ['llm_primary'],
                            'description': 'Integration test model'
                        }
                    ]
                },
                'custom': {
                    'api_key': '${MISSING_API_KEY}',  # Missing env var
                    'base_url': 'https://custom.api.com',
                    'models': [
                        {
                            'name': 'custom-model',
                            'model': 'custom-1',
                            'notes': ['chat'],
                            'purpose': ['vlm_primary'],
                            'description': 'Custom model with missing env var'
                        }
                    ]
                }
            }
        }
        
        config_path = os.path.join(self.temp_dir.name, 'llm_integration_config.yml')
        with open(config_path, 'w') as f:
            yaml.dump(llm_config_data, f)
        
        with patch('jinnang.path.path.RelPathSeeker.resolve_file_path', return_value=config_path):
            config = LLMConfig(
                filename='llm_integration_config.yml',
                caller_module_path=__file__,
                verbosity=Verbosity.ONCE
            )
            
            # Test resolved environment variables
            openai_model = config.get_model(model_name='gpt-4-integration')
            self.assertIsNotNone(openai_model)
            self.assertEqual(openai_model.api_key, 'sk-integration-test-key')
            self.assertEqual(openai_model.base_url, 'https://integration.api.com')

            # Test getting by purpose
            primary_llm = config.get_model(purpose='llm_primary')
            self.assertIsNotNone(primary_llm)
            self.assertEqual(primary_llm.name, 'openai/gpt-4-integration')
            
            # Test missing environment variable (should remain as placeholder)
            custom_model = config.get_model(model_name='custom-model')
            self.assertIsNotNone(custom_model)
            self.assertEqual(custom_model.api_key, '${MISSING_API_KEY}')
            self.assertEqual(custom_model.base_url, 'https://custom.api.com')
    
    def test_concurrent_config_loading(self):
        """Test environment variable resolution with concurrent config loading"""
        config_data = {
            'shared_key': '${INTEGRATION_API_KEY}',
            'timestamp': '${INTEGRATION_TIMEOUT}'
        }
        
        config_path = os.path.join(self.temp_dir.name, 'concurrent_config.yml')
        with open(config_path, 'w') as f:
            yaml.dump(config_data, f)
        
        results = []
        errors = []
        
        def load_config(thread_id):
            try:
                with patch('jinnang.path.path.RelPathSeeker.resolve_file_path', return_value=config_path):
                    config = BaseConfig(
                        filename='concurrent_config.yml',
                        caller_module_path=__file__,
                        verbosity=Verbosity.ONCE
                    )
                    
                    result = {
                        'thread_id': thread_id,
                        'shared_key': config.get('shared_key'),
                        'timestamp': config.get('timestamp')
                    }
                    results.append(result)
            except Exception as e:
                errors.append(f'Thread {thread_id}: {str(e)}')
        
        # Create and start multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=load_config, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify no errors occurred
        self.assertEqual(len(errors), 0, f'Errors in concurrent loading: {errors}')
        
        # Verify all threads got correct resolved values
        self.assertEqual(len(results), 5)
        for result in results:
            self.assertEqual(result['shared_key'], 'sk-integration-test-key')
            self.assertEqual(result['timestamp'], '30')
    
    def test_env_var_resolution_with_file_changes(self):
        """Test environment variable resolution when config files change"""
        config_path = os.path.join(self.temp_dir.name, 'dynamic_config.yml')
        
        # Initial config
        initial_config = {'key': '${INTEGRATION_API_KEY}'}
        with open(config_path, 'w') as f:
            yaml.dump(initial_config, f)
        
        with patch('jinnang.path.path.RelPathSeeker.resolve_file_path', return_value=config_path):
            config = BaseConfig(
                filename='dynamic_config.yml',
                caller_module_path=__file__,
                verbosity=Verbosity.ONCE
            )
            
            self.assertEqual(config.get('key'), 'sk-integration-test-key')
        
        # Update config file with different env var
        updated_config = {'key': '${INTEGRATION_BASE_URL}', 'new_key': '${INTEGRATION_TIMEOUT}'}
        with open(config_path, 'w') as f:
            yaml.dump(updated_config, f)
        
        with patch('jinnang.path.path.RelPathSeeker.resolve_file_path', return_value=config_path):
            config = BaseConfig(
                filename='dynamic_config.yml',
                caller_module_path=__file__,
                verbosity=Verbosity.ONCE
            )
            
            self.assertEqual(config.get('key'), 'https://integration.api.com')
            self.assertEqual(config.get('new_key'), '30')


if __name__ == "__main__":
    unittest.main()