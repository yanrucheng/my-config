"""Example demonstrating improved LLM configuration using SingletonFileLoader best practices.

This example shows how to use the enhanced LLMConfig class with various loading methods,
error handling, and configuration management features.
"""

import os
import tempfile
from pathlib import Path
from typing import Dict, Any

from jinnang.verbosity import Verbosity
from my_config.llm import LLMConfig, ModelConfig


def create_sample_config() -> Dict[str, Any]:
    """Create a sample LLM configuration for demonstration."""
    return {
        "providers": {
            "openai": {
                "api_key": "sk-example-openai-key",
                "base_url": "https://api.openai.com/v1",
                "models": [
                    {
                        "name": "gpt-4",
                        "model": "gpt-4-0613",
                        "tags": ["chat", "reasoning", "premium"],
                        "description": "GPT-4 model for complex reasoning tasks"
                    },
                    {
                        "name": "gpt-3.5-turbo",
                        "model": "gpt-3.5-turbo-0613",
                        "tags": ["chat", "fast", "cost-effective"],
                        "description": "Fast and cost-effective chat model"
                    }
                ]
            },
            "anthropic": {
                "api_key": "sk-example-anthropic-key",
                "base_url": "https://api.anthropic.com",
                "models": [
                    {
                        "name": "claude-3",
                        "model": "claude-3-opus-20240229",
                        "tags": ["chat", "reasoning", "premium"],
                        "description": "Claude 3 Opus for advanced reasoning"
                    },
                    {
                        "name": "claude-3-haiku",
                        "model": "claude-3-haiku-20240307",
                        "tags": ["chat", "fast", "cost-effective"],
                        "description": "Claude 3 Haiku for quick responses"
                    }
                ]
            }
        }
    }


def run_example():
    """Run the LLM configuration example."""
    print("--- Enhanced LLM Configuration Example ---")
    
    # Create a temporary directory and config file for demonstration
    with tempfile.TemporaryDirectory() as tmpdir_name:
        temp_path = Path(tmpdir_name)
        config_filename = "llm_config.yml"
        config_file_path = temp_path / config_filename
        
        # Create sample configuration file
        import yaml
        sample_config = create_sample_config()
        with open(config_file_path, 'w') as f:
            yaml.dump(sample_config, f, default_flow_style=False)
        
        print(f"Created sample config file: {config_file_path}")
        
        # 1. Demonstrate loading by filename with search locations
        print("\n=== Loading by filename with search locations ===")
        try:
            llm_config = LLMConfig(
                filename=config_filename,
                search_locations=[str(temp_path)],
                verbosity=Verbosity.FULL
            )
            
            if llm_config.loaded_filepath:
                print(f"✓ Successfully loaded config from: {llm_config.loaded_filepath}")
                print(f"✓ Configured providers: {llm_config.get_providers()}")
                print(f"✓ Total models: {len(llm_config.data)}")
            else:
                print("✗ Failed to load configuration")
                
        except Exception as e:
            print(f"✗ Error loading config: {e}")
        
        # 2. Demonstrate loading by explicit path
        print("\n=== Loading by explicit path ===")
        try:
            # Clear singleton cache for fresh instance
            LLMConfig._instances.clear()
            
            llm_config_explicit = LLMConfig(
                explicit_path=str(config_file_path),
                verbosity=Verbosity.ONCE
            )
            
            if llm_config_explicit.loaded_filepath:
                print(f"✓ Successfully loaded config from explicit path")
                
                # Demonstrate model retrieval methods
                print("\n--- Model Retrieval Examples ---")
                
                # Get model by full name
                gpt4_model = llm_config_explicit.get("openai/gpt-4")
                if gpt4_model:
                    print(f"✓ Found GPT-4: {gpt4_model.model} (Provider: {gpt4_model.provider})")
                
                # Get model by name and provider
                claude_model = llm_config_explicit.get_model("claude-3", "anthropic")
                if claude_model:
                    print(f"✓ Found Claude-3: {claude_model.model}")
                
                # Get model by tag
                fast_model = llm_config_explicit.get_model_by_tag("fast")
                if fast_model:
                    print(f"✓ Found fast model: {fast_model.name}")
                
                # Get all models with a specific tag
                premium_models = llm_config_explicit.get_models_by_tag("premium")
                print(f"✓ Found {len(premium_models)} premium models")
                
                # Get models by provider
                openai_models = llm_config_explicit.get_models_by_provider("openai")
                print(f"✓ OpenAI has {len(openai_models)} models")
                
                # List all models
                all_models = llm_config_explicit.list_models()
                print(f"✓ Model summary: {all_models}")
                
            else:
                print("✗ Failed to load configuration from explicit path")
                
        except Exception as e:
            print(f"✗ Error with explicit path loading: {e}")
        
        # 3. Demonstrate error handling with invalid config
        print("\n=== Error Handling with Invalid Configuration ===")
        try:
            # Create invalid config file
            invalid_config_path = temp_path / "invalid_config.yml"
            invalid_config = {"invalid": "structure"}
            
            with open(invalid_config_path, 'w') as f:
                yaml.dump(invalid_config, f)
            
            # Clear singleton cache
            LLMConfig._instances.clear()
            
            invalid_llm_config = LLMConfig(
                explicit_path=str(invalid_config_path),
                verbosity=Verbosity.FULL
            )
            
            print("✗ Should have failed with invalid configuration")
            
        except ValueError as e:
            print(f"✓ Correctly caught configuration error: {e}")
        except Exception as e:
            print(f"✗ Unexpected error: {e}")
        
        # 4. Demonstrate loading non-existent file
        print("\n=== Handling Non-existent Configuration File ===")
        try:
            # Clear singleton cache
            LLMConfig._instances.clear()
            
            nonexistent_config = LLMConfig(
                filename="nonexistent_config.yml",
                search_locations=[str(temp_path)],
                verbosity=Verbosity.FULL
            )
            
            if not nonexistent_config.loaded_filepath:
                print("✓ Correctly handled non-existent file")
                print(f"✓ Config has {len(nonexistent_config.data)} models (should be 0)")
            else:
                print("✗ Unexpectedly loaded a file")
                
        except Exception as e:
            print(f"✓ Handled non-existent file gracefully: {e}")
        
        # 5. Demonstrate default search locations
        print("\n=== Using Default Search Locations ===")
        try:
            # Copy config to current directory for default search
            current_dir_config = Path(".") / "llm_config.yml"
            
            # Only proceed if we can write to current directory
            if os.access(".", os.W_OK):
                with open(current_dir_config, 'w') as f:
                    yaml.dump(sample_config, f)
                
                # Clear singleton cache
                LLMConfig._instances.clear()
                
                default_config = LLMConfig(verbosity=Verbosity.ONCE)
                
                if default_config.loaded_filepath:
                    print(f"✓ Found config using default search: {default_config.loaded_filepath}")
                else:
                    print("✗ Failed to find config with default search")
                
                # Clean up
                if current_dir_config.exists():
                    current_dir_config.unlink()
            else:
                print("⚠ Skipped default search test (no write permission)")
                
        except Exception as e:
            print(f"✗ Error with default search: {e}")
            # Clean up on error
            if 'current_dir_config' in locals() and current_dir_config.exists():
                current_dir_config.unlink()
    
    print("\n--- Example Finished ---")


if __name__ == "__main__":
    run_example()