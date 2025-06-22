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

# --- Load LLMConfig ---
llm_config = LLMConfig(
    filename='conf/llm.yml',
    verbosity=Verbosity.FULL,
    caller_module_path=__file__,
)
print("\n--- LLMConfig ---")
print(f"Loaded from: {llm_config.loaded_filepath}")
print(f"Number of models: {len(llm_config.data)}")
if llm_config.data:
    # Demonstrate LLMConfig-specific model access methods
    print(f"Available models: {list(llm_config.data.keys())}")
    
    # Get specific model by name
    gpt4_model = llm_config.get('openai/gpt-4')
    if gpt4_model:
        print(f"GPT-4 model: {gpt4_model.name} ({gpt4_model.model}) - Tags: {gpt4_model.tags}")
    
    # Get model by tag
    large_model = llm_config.get_model_by_tag('large')
    if large_model:
        print(f"First large model: {large_model.name}")
    
    # Get all models with specific tag
    chat_models = llm_config.get_models_by_tag('chat')
    print(f"Chat models: {[model.name for model in chat_models]}")
    
    # Show model API URL construction
    if gpt4_model:
        print(f"GPT-4 API URL: {gpt4_model.get_full_api_url()}")

    # Get primary LLM model
    primary_llm = llm_config.get_primary_model_config('llm')
    if primary_llm:
        print(f"Primary LLM model: {primary_llm.name} ({primary_llm.model}) - Tags: {primary_llm.tags}")

    # Get primary VLM model
    primary_vlm = llm_config.get_primary_model_config('vlm')
    if primary_vlm:
        print(f"Primary VLM model: {primary_vlm.name} ({primary_vlm.model}) - Tags: {primary_vlm.tags}")