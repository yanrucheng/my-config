"""LLM-specific configuration classes.

This module provides configuration classes for language models and their providers.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Any
import logging

from my_config.base import BaseConfig

logger = logging.getLogger(__name__)

@dataclass
class ModelConfig:
    """Configuration for a specific language model"""
    name: str
    model: str  # API identifier
    provider: str
    api_key: str
    base_url: str
    tags: List[str] = None
    description: str = None


class LLMConfig(BaseConfig[ModelConfig]):
    """LLM-specific configuration with provider processing"""
    CONFIG_FILENAME = "llm_config.yml"
    
    def _process_config(self) -> None:
        """Process LLM-specific provider configuration"""
        config_data = self._data
        if "providers" not in config_data:
            raise ValueError("Configuration missing 'providers' section")
        self.data = self._process_providers(config_data["providers"])
    
    def _process_providers(self, providers_data: Dict[str, Any]) -> Dict[str, ModelConfig]:
        """Provider-specific processing"""
        data = {}
        for provider_name, provider_data in providers_data.items():
            if not all(field in provider_data for field in ["api_key", "base_url", "models"]):
                raise ValueError(f"Provider {provider_name} missing required fields")
            
            for model_data in provider_data["models"]:
                if "name" not in model_data or "model" not in model_data:
                    raise ValueError(f"Model in provider {provider_name} missing required fields")
                
                model_name = f"{provider_name}/{model_data['name']}"
                data[model_name] = ModelConfig(
                    name=model_name,
                    model=model_data["model"],
                    provider=provider_name,
                    api_key=provider_data["api_key"],
                    base_url=provider_data["base_url"],
                    tags=model_data.get("tags"),
                    description=model_data.get("description")
                )
        
        return data
    
    def get_model_by_tag(self, tag: str) -> Optional[ModelConfig]:
        """Get a model configuration by tag"""
        for model in self.data.values():
            if model.tags and tag in model.tags:
                return model
        return None