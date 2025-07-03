import os

from my_config.base import BaseConfig
from my_config.env_aware import EnvAwareConfig
from my_config.llm import LLMConfig
from jinnang.verbosity import Verbosity

# Set APP_ENV for EnvAwareConfig to load the dev config
os.environ['APP_ENV'] = 'development'

# --- Load BaseConfig ---
base_config = BaseConfig(
    filename='conf/base.yml',
    verbosity=Verbosity.FULL,
    caller_module_path=__file__,
)
print("\n--- BaseConfig ---")
print(f"Loaded from: {base_config.loaded_filepath}")
print(f"Content (first 2 keys): {list(base_config.data.keys())[:2]}")

# --- Load EnvAwareConfig ---
env_aware_config = EnvAwareConfig(
    base_filename='conf/my_app.yml', # Base name for env-aware config
    dev_filename='conf/my_app.dev.yml', # Explicitly specify dev filename
    verbosity=Verbosity.FULL,
    caller_module_path=__file__,
)
print("\n--- EnvAwareConfig ---")
print(f"Loaded from: {env_aware_config.loaded_filepath}")
print(f"Content (app_env): {env_aware_config.data.get('app_env')}")

import os
from my_config.llm import LLMConfig

# Example Usage:
# Set the environment variable (in a real scenario, this would be set outside the script)
os.environ["LLM_API_KEY"] = "sk-YOUR_ACTUAL_API_KEY_HERE"

# 1. Load LLM configuration
llm_config = LLMConfig(
    filename='conf/llm.yml',
    verbosity=Verbosity.FULL,
    caller_module_path=__file__,
)

# Access a specific model configuration by name
openai_gpt4_config = llm_config.get_model(model_name="gpt-4")

if openai_gpt4_config:
    print(f"OpenAI GPT-4 API Key (by name): {openai_gpt4_config.api_key}")
    print(f"OpenAI GPT-4 Base URL (by name): {openai_gpt4_config.base_url}")
else:
    print("OpenAI GPT-4 configuration not found by name.")

# Access a model by purpose
primary_llm = llm_config.get_model(purpose="llm_primary")
if primary_llm:
    print(f"Primary LLM ({primary_llm.name}) API Key (by purpose): {primary_llm.api_key}")
else:
    print("Primary LLM not found by purpose.")

# Clean up the environment variable (optional, for script execution)
del os.environ["LLM_API_KEY"]

# 2. Load My App configuration
# my_app_config = MyAppConfig()
# print(f"My App Name: {my_app_config.get('app_name')}")
# print(f"My App Version: {my_app_config.get('version')}")
# print(f"My App Debug Mode: {my_app_config.get('debug_mode')}")