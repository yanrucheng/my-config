#!/usr/bin/env python3
"""Example usage of the my_config package.

This script demonstrates how to use the my_config package in a real application.
"""

import os
import logging
from typing import Dict, Any

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import the my_config package
from my_config import BaseConfig, EnvAwareConfig, LLMConfig, is_dev, is_prod

# Example 1: Basic Configuration
class AppConfig(BaseConfig[Dict[str, Any]]):
    CONFIG_FILENAME = "sample_config.yml"

# Example 2: Environment-Aware Configuration
class EnvConfig(EnvAwareConfig[Dict[str, Any]]):
    DEV_CONFIG_FILENAME = "sample_config.yml"
    BOE_CONFIG_FILENAME = "sample_config.yml"  # In a real app, these would be different files
    PROD_CONFIG_FILENAME = "sample_config.yml"

# Example 3: LLM Configuration
class MyLLMConfig(LLMConfig):
    CONFIG_FILENAME = "sample_llm_config.yml"

def main():
    # Print the current environment
    logger.info(f"Current environment: {'DEV' if is_dev() else 'PROD' if is_prod() else 'BOE'}")
    
    # Example 1: Basic Configuration
    app_config = AppConfig.get_instance()
    db_config = app_config.get("database")
    logger.info(f"Database host: {db_config['host']}")
    logger.info(f"Database port: {db_config['port']}")
    
    # Example 2: Environment-Aware Configuration
    env_config = EnvConfig.get_instance()
    api_config = env_config.get("api")
    logger.info(f"API base URL: {api_config['base_url']}")
    logger.info(f"API timeout: {api_config['timeout']}")
    
    # Example 3: LLM Configuration
    llm_config = MyLLMConfig.get_instance()
    
    # Get a specific model
    gpt4_model = llm_config.get("openai/gpt-4")
    if gpt4_model:
        logger.info(f"GPT-4 model ID: {gpt4_model.model}")
        logger.info(f"GPT-4 provider: {gpt4_model.provider}")
    
    # Get a model by tag
    fast_model = llm_config.get_model_by_tag("fast")
    if fast_model:
        logger.info(f"Fast model: {fast_model.name}")
        logger.info(f"Fast model description: {fast_model.description}")

if __name__ == "__main__":
    main()