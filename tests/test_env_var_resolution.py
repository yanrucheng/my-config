"""Tests for environment variable resolution functionality."""

import os
import tempfile
import unittest
import yaml
import copy
import gc
import time

from my_config.base import BaseConfig


class TestEnvVarResolution(unittest.TestCase):
    """Test environment variable resolution in BaseConfig"""
    
    def setUp(self):

        
        # Set up test environment variables
        os.environ['TEST_VAR'] = 'test_value'
        os.environ['NESTED_VAR'] = 'nested_value'
        os.environ['EMPTY_VAR'] = ''
        os.environ['SPECIAL_CHARS'] = 'value!@#$%^&*()'
        os.environ['UNICODE_VAR'] = 'café_测试_🚀'
        os.environ['WHITESPACE_VAR'] = '  spaced value  '
        os.environ['NUMERIC_VAR'] = '12345'
        os.environ['JSON_LIKE'] = '{"key": "value"}'
        
    def tearDown(self):
        # Clean up environment variables
        test_vars = ['TEST_VAR', 'NESTED_VAR', 'EMPTY_VAR', 'SPECIAL_CHARS', 
                    'UNICODE_VAR', 'WHITESPACE_VAR', 'NUMERIC_VAR', 'JSON_LIKE']
        for var in test_vars:
            if var in os.environ:
                del os.environ[var]
        

    
    def test_resolve_env_vars_success(self):
        """Test successful environment variable resolution"""
        config = BaseConfig()
        data = {
            'api_key': '${TEST_VAR}',
            'url': 'https://api.example.com',
            'timeout': 30
        }
        
        resolved = config._resolve_env_vars(data)
        
        self.assertEqual(resolved['api_key'], 'test_value')
        self.assertEqual(resolved['url'], 'https://api.example.com')
        self.assertEqual(resolved['timeout'], 30)
    
    def test_resolve_env_vars_missing(self):
        """Test handling of missing environment variables"""
        config = BaseConfig()
        data = {
            'api_key': '${MISSING_VAR}',
            'backup_key': '${TEST_VAR}'
        }
        
        resolved = config._resolve_env_vars(data)
        
        # Missing variables should remain as placeholders
        self.assertEqual(resolved['api_key'], '${MISSING_VAR}')
        self.assertEqual(resolved['backup_key'], 'test_value')
    
    def test_resolve_env_vars_nested(self):
        """Test environment variable resolution in nested structures"""
        config = BaseConfig()
        data = {
            'database': {
                'host': '${TEST_VAR}',
                'port': 5432,
                'credentials': {
                    'username': '${NESTED_VAR}',
                    'password': '${MISSING_VAR}'
                }
            },
            'services': ['${TEST_VAR}', 'static_service', '${NESTED_VAR}']
        }
        
        resolved = config._resolve_env_vars(data)
        
        self.assertEqual(resolved['database']['host'], 'test_value')
        self.assertEqual(resolved['database']['port'], 5432)
        self.assertEqual(resolved['database']['credentials']['username'], 'nested_value')
        self.assertEqual(resolved['database']['credentials']['password'], '${MISSING_VAR}')
        self.assertEqual(resolved['services'], ['test_value', 'static_service', 'nested_value'])
    
    def test_resolve_env_vars_non_string(self):
        """Test that non-string values are not affected"""
        config = BaseConfig()
        data = {
            'number': 42,
            'boolean': True,
            'null_value': None,
            'list': [1, 2, 3],
            'string_var': '${TEST_VAR}'
        }
        
        resolved = config._resolve_env_vars(data)
        
        self.assertEqual(resolved['number'], 42)
        self.assertEqual(resolved['boolean'], True)
        self.assertEqual(resolved['null_value'], None)
        self.assertEqual(resolved['list'], [1, 2, 3])
        self.assertEqual(resolved['string_var'], 'test_value')
    
    def test_resolve_env_vars_malformed_placeholders(self):
        """Test that malformed placeholders are not resolved"""
        config = BaseConfig()
        data = {
            'malformed1': '${TEST_VAR',  # Missing closing brace
            'malformed2': '$TEST_VAR}',  # Missing opening brace
            'malformed3': '${TEST_VAR}}', # Extra closing brace
            'malformed4': '${{TEST_VAR}', # Extra opening brace
            'empty_placeholder': '${}',
            'just_dollar': '$',
            'just_braces': '{}',
            'nested_braces': '${${TEST_VAR}}',
            'invalid_chars': '${TEST-VAR}',  # Hyphen in var name
            'spaces_in_var': '${TEST VAR}',  # Space in var name
        }
        
        resolved = config._resolve_env_vars(data)
        
        # All malformed placeholders should remain unchanged
        self.assertEqual(resolved['malformed1'], '${TEST_VAR')
        self.assertEqual(resolved['malformed2'], '$TEST_VAR}')
        self.assertEqual(resolved['malformed3'], '${TEST_VAR}}')
        self.assertEqual(resolved['malformed4'], '${{TEST_VAR}')
        self.assertEqual(resolved['empty_placeholder'], '${}')
        self.assertEqual(resolved['just_dollar'], '$')
        self.assertEqual(resolved['just_braces'], '{}')
        self.assertEqual(resolved['nested_braces'], '${${TEST_VAR}}')
        self.assertEqual(resolved['invalid_chars'], '${TEST-VAR}')
        self.assertEqual(resolved['spaces_in_var'], '${TEST VAR}')
    
    def test_resolve_env_vars_partial_and_multiple(self):
        """Test partial matches and multiple variables in one string"""
        config = BaseConfig()
        data = {
            'partial': 'prefix_${TEST_VAR}_suffix',
            'multiple': '${TEST_VAR}_${NESTED_VAR}',
            'mixed': 'start_${TEST_VAR}_middle_${MISSING_VAR}_end',
            'repeated': '${TEST_VAR}_${TEST_VAR}',
            'complex': 'https://${TEST_VAR}.example.com:${NUMERIC_VAR}/path'
        }
        
        resolved = config._resolve_env_vars(data)
        
        self.assertEqual(resolved['partial'], 'prefix_test_value_suffix')
        self.assertEqual(resolved['multiple'], 'test_value_nested_value')
        self.assertEqual(resolved['mixed'], 'start_test_value_middle_${MISSING_VAR}_end')
        self.assertEqual(resolved['repeated'], 'test_value_test_value')
        self.assertEqual(resolved['complex'], 'https://test_value.example.com:12345/path')
    
    def test_resolve_env_vars_special_values(self):
        """Test resolution of environment variables with special values"""
        config = BaseConfig()
        data = {
            'empty': '${EMPTY_VAR}',
            'special_chars': '${SPECIAL_CHARS}',
            'unicode': '${UNICODE_VAR}',
            'whitespace': '${WHITESPACE_VAR}',
            'numeric': '${NUMERIC_VAR}',
            'json_like': '${JSON_LIKE}'
        }
        
        resolved = config._resolve_env_vars(data)
        
        self.assertEqual(resolved['empty'], '')
        self.assertEqual(resolved['special_chars'], 'value!@#$%^&*()')
        self.assertEqual(resolved['unicode'], 'café_测试_🚀')
        self.assertEqual(resolved['whitespace'], '  spaced value  ')
        self.assertEqual(resolved['numeric'], '12345')
        self.assertEqual(resolved['json_like'], '{"key": "value"}')
    
    def test_resolve_env_vars_deep_nesting(self):
        """Test environment variable resolution in deeply nested structures"""
        config = BaseConfig()
        data = {
            'level1': {
                'level2': {
                    'level3': {
                        'level4': {
                            'value': '${TEST_VAR}',
                            'list': ['${NESTED_VAR}', {'nested_dict': '${TEST_VAR}'}]
                        }
                    }
                }
            }
        }
        
        resolved = config._resolve_env_vars(data)
        
        self.assertEqual(resolved['level1']['level2']['level3']['level4']['value'], 'test_value')
        self.assertEqual(resolved['level1']['level2']['level3']['level4']['list'][0], 'nested_value')
        self.assertEqual(resolved['level1']['level2']['level3']['level4']['list'][1]['nested_dict'], 'test_value')
    
    def test_resolve_env_vars_edge_cases(self):
        """Test edge cases and boundary conditions"""
        config = BaseConfig()
        data = {
            'empty_string': '',
            'only_placeholder': '${TEST_VAR}',
            'case_sensitive': '${test_var}',  # Different case
            'underscore_var': '${TEST_VAR}',
            'long_var_name': '${VERY_LONG_VARIABLE_NAME_THAT_DOES_NOT_EXIST}',
            'dollar_escape': '$$${TEST_VAR}',  # Multiple dollars
            'brace_escape': '\\${TEST_VAR}',   # Escaped brace
        }
        
        resolved = config._resolve_env_vars(data)
        
        self.assertEqual(resolved['empty_string'], '')
        self.assertEqual(resolved['only_placeholder'], 'test_value')
        self.assertEqual(resolved['case_sensitive'], '${test_var}')  # Should not resolve
        self.assertEqual(resolved['underscore_var'], 'test_value')
        self.assertEqual(resolved['long_var_name'], '${VERY_LONG_VARIABLE_NAME_THAT_DOES_NOT_EXIST}')
        self.assertEqual(resolved['dollar_escape'], '$$test_value')  # Only last placeholder resolved
        self.assertEqual(resolved['brace_escape'], '\\${TEST_VAR}')  # Should remain escaped
    
    def test_resolve_env_vars_immutability(self):
        """Test that original data is not modified"""
        config = BaseConfig()
        original_data = {
            'api_key': '${TEST_VAR}',
            'nested': {
                'value': '${NESTED_VAR}'
            }
        }
        
        # Create a deep copy to compare
        original_copy = copy.deepcopy(original_data)
        
        resolved = config._resolve_env_vars(original_data)
        
        # Original data should be unchanged
        self.assertEqual(original_data, original_copy)
        
        # Resolved data should be different
        self.assertEqual(resolved['api_key'], 'test_value')
        self.assertEqual(resolved['nested']['value'], 'nested_value')
        self.assertNotEqual(resolved, original_data)
    
    def test_resolve_env_vars_performance_large_data(self):
        """Test performance with large data structures"""
        config = BaseConfig()
        
        # Create a large nested structure
        large_data = {}
        for i in range(100):
            large_data[f'section_{i}'] = {
                'config': f'value_{i}',
                'env_var': '${TEST_VAR}',
                'nested': {
                    'deep_value': '${NESTED_VAR}',
                    'items': [f'item_{j}' for j in range(10)]
                }
            }
        
        # Should complete without timeout or memory issues
        start_time = time.time()
        resolved = config._resolve_env_vars(large_data)
        end_time = time.time()
        
        # Basic performance check (should complete in reasonable time)
        self.assertLess(end_time - start_time, 1.0)  # Should take less than 1 second
        
        # Verify some resolutions worked
        self.assertEqual(resolved['section_0']['env_var'], 'test_value')
        self.assertEqual(resolved['section_50']['nested']['deep_value'], 'nested_value')
    
    def test_resolve_env_vars_circular_references(self):
        """Test handling of potential circular reference scenarios"""
        config = BaseConfig()
        
        # Set up environment variables that could create circular references
        os.environ['CIRCULAR_A'] = '${CIRCULAR_B}'
        os.environ['CIRCULAR_B'] = '${CIRCULAR_A}'
        
        try:
            data = {
                'value_a': '${CIRCULAR_A}',
                'value_b': '${CIRCULAR_B}',
                'safe_value': '${TEST_VAR}'
            }
            
            resolved = config._resolve_env_vars(data)
            
            # Should not crash, but circular references should remain unresolved
            # or resolve to the literal env var values
            self.assertEqual(resolved['value_a'], '${CIRCULAR_B}')
            self.assertEqual(resolved['value_b'], '${CIRCULAR_A}')
            self.assertEqual(resolved['safe_value'], 'test_value')
            
        finally:
            # Clean up circular reference env vars
            if 'CIRCULAR_A' in os.environ:
                del os.environ['CIRCULAR_A']
            if 'CIRCULAR_B' in os.environ:
                del os.environ['CIRCULAR_B']
    
    def test_resolve_env_vars_type_preservation(self):
        """Test that data types are preserved during resolution"""
        config = BaseConfig()
        data = {
            'string': '${TEST_VAR}',
            'integer': 42,
            'float': 3.14,
            'boolean_true': True,
            'boolean_false': False,
            'none_value': None,
            'list_mixed': [1, '${TEST_VAR}', True, None],
            'dict_mixed': {
                'num': 123,
                'str': '${NESTED_VAR}',
                'bool': False
            }
        }
        
        resolved = config._resolve_env_vars(data)
        
        # Check types are preserved
        self.assertIsInstance(resolved['string'], str)
        self.assertIsInstance(resolved['integer'], int)
        self.assertIsInstance(resolved['float'], float)
        self.assertIsInstance(resolved['boolean_true'], bool)
        self.assertIsInstance(resolved['boolean_false'], bool)
        self.assertIsNone(resolved['none_value'])
        self.assertIsInstance(resolved['list_mixed'], list)
        self.assertIsInstance(resolved['dict_mixed'], dict)
        
        # Check values
        self.assertEqual(resolved['string'], 'test_value')
        self.assertEqual(resolved['integer'], 42)
        self.assertEqual(resolved['float'], 3.14)
        self.assertTrue(resolved['boolean_true'])
        self.assertFalse(resolved['boolean_false'])
        self.assertEqual(resolved['list_mixed'], [1, 'test_value', True, None])
        self.assertEqual(resolved['dict_mixed']['str'], 'nested_value')
    
    def test_resolve_env_vars_regex_edge_cases(self):
        """Test regex pattern matching edge cases"""
        config = BaseConfig()
        data = {
            'normal': '${TEST_VAR}',
            'with_numbers': '${TEST_VAR123}',  # Non-existent
            'with_underscore': '${TEST_VAR_SUFFIX}',  # Non-existent
            'multiple_consecutive': '${TEST_VAR}${NESTED_VAR}',
            'separated': '${TEST_VAR} ${NESTED_VAR}',
            'regex_special': '${TEST_VAR}.*+?[]{}()^$|\\',
            'very_long': '${' + 'A' * 1000 + '}',  # Very long var name
        }
        
        resolved = config._resolve_env_vars(data)
        
        self.assertEqual(resolved['normal'], 'test_value')
        self.assertEqual(resolved['with_numbers'], '${TEST_VAR123}')
        self.assertEqual(resolved['with_underscore'], '${TEST_VAR_SUFFIX}')
        self.assertEqual(resolved['multiple_consecutive'], 'test_valuenested_value')
        self.assertEqual(resolved['separated'], 'test_value nested_value')
        self.assertEqual(resolved['regex_special'], 'test_value.*+?[]{}()^$|\\')
        self.assertEqual(resolved['very_long'], '${' + 'A' * 1000 + '}')
    
    def test_resolve_env_vars_memory_efficiency(self):
        """Test memory efficiency with repeated calls"""
        config = BaseConfig()
        data = {
            'key1': '${TEST_VAR}',
            'key2': '${NESTED_VAR}',
            'nested': {
                'deep': '${TEST_VAR}'
            }
        }
        
        # Multiple calls should not accumulate memory
        gc.collect()
        initial_objects = len(gc.get_objects())
        
        for _ in range(100):
            resolved = config._resolve_env_vars(data)
            self.assertEqual(resolved['key1'], 'test_value')
        
        gc.collect()
        final_objects = len(gc.get_objects())
        
        # Object count should not grow significantly
        # Allow some tolerance for test framework overhead
        self.assertLess(final_objects - initial_objects, 1000)


if __name__ == '__main__':
    unittest.main()