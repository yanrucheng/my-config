"""LLM-specific configuration classes.

This module provides configuration classes for language models and their providers.
Follows jinnang SingletonFileLoader best practices for robust configuration management.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Any
import logging
from pathlib import Path

from my_config.base import BaseConfig
from jinnang.verbosity import Verbosity

logger = logging.getLogger(__name__)

@dataclass
class ModelConfig:
    """Configuration for a specific language model.
    
    This class represents a complete configuration for a language model,
    including provider details, API credentials, and metadata.
    
    Attributes:
        name: Unique identifier for the model (format: provider/model_name)
        model: API identifier used by the provider
        provider: Name of the model provider (e.g., 'openai', 'anthropic')
        api_key: API key for authentication
        base_url: Base URL for the provider's API
        tags: Optional list of tags for categorization
        description: Optional human-readable description
    """
    name: str
    model: str  # API identifier
    provider: str
    api_key: str
    base_url: str
    tags: Optional[List[str]] = None
    description: Optional[str] = None
    
    def __post_init__(self):
        """Validate and normalize the model configuration after initialization."""
        # Validate required fields
        if not self.name or not self.name.strip():
            raise ValueError("Model name cannot be empty")
        if not self.model or not self.model.strip():
            raise ValueError("Model API identifier cannot be empty")
        if not self.provider or not self.provider.strip():
            raise ValueError("Provider name cannot be empty")
        if not self.api_key or not self.api_key.strip():
            raise ValueError("API key cannot be empty")
        if not self.base_url or not self.base_url.strip():
            raise ValueError("Base URL cannot be empty")
        
        # Normalize strings
        self.name = self.name.strip()
        self.model = self.model.strip()
        self.provider = self.provider.strip()
        self.api_key = self.api_key.strip()
        self.base_url = self.base_url.strip().rstrip('/')
        
        # Normalize optional fields
        if self.description:
            self.description = self.description.strip()
        if self.tags:
            self.tags = [tag.strip() for tag in self.tags if tag and tag.strip()]
            if not self.tags:  # If all tags were empty after stripping
                self.tags = None
    
    def has_tag(self, tag: str) -> bool:
        """Check if the model has a specific tag.
        
        Args:
            tag: The tag to check for
            
        Returns:
            True if the model has the specified tag, False otherwise
        """
        return self.tags is not None and tag in self.tags
    
    def get_full_api_url(self, endpoint: str = "") -> str:
        """Get the full API URL for a specific endpoint.
        
        Args:
            endpoint: Optional endpoint to append to the base URL
            
        Returns:
            Complete API URL
        """
        if endpoint:
            endpoint = endpoint.lstrip('/')
            return f"{self.base_url}/{endpoint}"
        return self.base_url
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the model configuration to a dictionary.
        
        Returns:
            Dictionary representation of the model configuration
        """
        return {
            'name': self.name,
            'model': self.model,
            'provider': self.provider,
            'api_key': self.api_key,
            'base_url': self.base_url,
            'tags': self.tags,
            'description': self.description
        }


class LLMConfig(BaseConfig[ModelConfig]):
    """LLM-specific configuration with provider processing.
    
    Follows SingletonFileLoader best practices:
    - Supports both filename-based and explicit path loading
    - Provides flexible search locations
    - Includes proper error handling and validation
    - Uses singleton pattern for efficient resource usage
    """
    CONFIG_FILENAME = "conf/llm.yml"
    
    def __init__(
        self,
        filename: Optional[str] = None,
        verbosity: Verbosity = Verbosity.ONCE,
        caller_module_path: Optional[str] = None,
        **kwargs: Any
    ):
        """Initialize LLM configuration with flexible loading options.
        
        Args:
            filename: Name of the config file to search for (default: llm_config.yml)
            verbosity: Logging verbosity level
            **kwargs: Additional arguments passed to BaseConfig
        """
        # Set default filename if none provided
        if filename is None:
            filename = self.CONFIG_FILENAME
            
        super().__init__(
            filename=filename,
            verbosity=verbosity,
            caller_module_path=caller_module_path or __file__,
            **kwargs
        )
    

    def _process_config(self, config_data: Dict[str, Any]) -> Dict[str, ModelConfig]:
        """Process LLM-specific provider configuration.
        
        Args:
            config_data: Raw configuration data loaded from file
            
        Returns:
            Processed configuration as a dictionary of ModelConfig objects
            
        Raises:
            ValueError: If configuration is invalid or missing required sections
        """
        if not config_data:
            logger.warning("Empty configuration data provided")
            return {}
            
        if "providers" not in config_data:
            raise ValueError("Configuration missing 'providers' section")
            
        try:
            processed_data = self._process_providers(config_data["providers"])
            # ensure config is correctly set by validating primary models
            self._validate_primary_models(processed_data)
            return processed_data
        except Exception as e:
            logger.error(f"Failed to process LLM configuration: {e}")
            raise ValueError(f"Invalid LLM configuration: {e}") from e
    
    def _process_providers(self, providers_data: Dict[str, Any]) -> Dict[str, ModelConfig]:
        """Provider-specific processing with comprehensive validation.
        
        Args:
            providers_data: Dictionary containing provider configurations
            
        Returns:
            Dictionary mapping model names to ModelConfig objects
            
        Raises:
            ValueError: If provider or model configuration is invalid
        """
        if not isinstance(providers_data, dict):
            raise ValueError("Providers data must be a dictionary")
            
        data = {}
        required_provider_fields = ["api_key", "base_url", "models"]
        required_model_fields = ["name", "model"]
        
        for provider_name, provider_data in providers_data.items():
            if not isinstance(provider_data, dict):
                raise ValueError(f"Provider '{provider_name}' configuration must be a dictionary")
                
            # Validate required provider fields
            missing_fields = [field for field in required_provider_fields if field not in provider_data]
            if missing_fields:
                raise ValueError(f"Provider '{provider_name}' missing required fields: {', '.join(missing_fields)}")
            
            # Validate models list
            models = provider_data.get("models", [])
            if not isinstance(models, list):
                raise ValueError(f"Provider '{provider_name}' models must be a list")
                
            if not models:
                logger.warning(f"Provider '{provider_name}' has no models configured")
                continue
            
            # Process each model
            for i, model_data in enumerate(models):
                if not isinstance(model_data, dict):
                    raise ValueError(f"Model {i} in provider '{provider_name}' must be a dictionary")
                    
                # Validate required model fields
                missing_model_fields = [field for field in required_model_fields if field not in model_data]
                if missing_model_fields:
                    raise ValueError(f"Model {i} in provider '{provider_name}' missing required fields: {', '.join(missing_model_fields)}")
                
                model_name = f"{provider_name}/{model_data['name']}"
                
                # Check for duplicate model names
                if model_name in data:
                    raise ValueError(f"Duplicate model name: '{model_name}'")
                
                try:
                    data[model_name] = ModelConfig(
                        name=model_name,
                        model=model_data["model"],
                        provider=provider_name,
                        api_key=provider_data["api_key"],
                        base_url=provider_data["base_url"],
                        tags=model_data.get("tags"),
                        description=model_data.get("description")
                    )
                    logger.debug(f"Successfully configured model: {model_name}")
                except Exception as e:
                    raise ValueError(f"Failed to create ModelConfig for '{model_name}': {e}") from e
        
        if not data:
            logger.warning("No valid models were configured")
            
        logger.info(f"Successfully processed {len(data)} models from {len(providers_data)} providers")
        return data

    def _validate_primary_models(self, processed_data: Dict[str, ModelConfig]) -> None:
        """Validate that there is exactly one primary model for each type (llm and vlm).
        
        Args:
            processed_data: Dictionary of processed ModelConfig objects
            
        Raises:
            AssertionError: If there is not exactly one primary model of each type
        """
        for model_type in ['llm', 'vlm']:
            primary_models = [model for model in processed_data.values()
                            if model.tags and ('primary' in model.tags) and (model_type in model.tags)]
            assert len(primary_models) == 1, (
                f'There should be one and only one primary {model_type} model. '
                f'Got {len(primary_models)}. Includes: {[m.name for m in primary_models]}'
            )

    def get_primary_model_config(self, model_type: str = 'llm') -> ModelConfig:
        """Get the primary model configuration for a given type (llm or vlm).

        Args:
            model_type: The type of model to retrieve ('llm' or 'vlm').

        Returns:
            The primary ModelConfig object.

        Raises:
            AssertionError: If there is not exactly one primary model of the specified type.
        """
        ms = [model for model in self.data.values()
                if model.tags and ('primary' in model.tags) and (model_type in model.tags)]
        assert len(ms) == 1, (
            f'There should be one and only one primary {model_type} model. '
            f'Got {len(ms)}. Includes: {[m.name for m in ms]}'
        )
        return ms[0]
    
    def get_model_by_tag(self, tag: str) -> Optional[ModelConfig]:
        """Get the first model configuration that has the specified tag.
        
        Args:
            tag: The tag to search for
            
        Returns:
            First ModelConfig with the specified tag, or None if not found
        """
        if not tag:
            logger.warning("Empty tag provided to get_model_by_tag")
            return None
            
        for model in self.data.values():
            if model.tags and tag in model.tags:
                logger.debug(f"Found model '{model.name}' with tag '{tag}'")
                return model
                
        logger.debug(f"No model found with tag '{tag}'")
        return None
    
    def get_models_by_tag(self, tag: str) -> List[ModelConfig]:
        """Get all model configurations that have the specified tag.
        
        Args:
            tag: The tag to search for
            
        Returns:
            List of ModelConfig objects with the specified tag
        """
        if not tag:
            logger.warning("Empty tag provided to get_models_by_tag")
            return []
            
        models = [model for model in self.data.values() if model.tags and tag in model.tags]
        logger.debug(f"Found {len(models)} models with tag '{tag}'")
        return models
    
    def get_model(self, model_name: str, provider_name: Optional[str] = None) -> Optional[ModelConfig]:
        """Get a model configuration by name and optional provider.
        
        Args:
            model_name: The name of the model to find
            provider_name: Optional provider name to narrow the search
            
        Returns:
            ModelConfig if found, None otherwise
        """
        if not model_name:
            logger.warning("Empty model_name provided to get_model")
            return None
            
        # If provider is specified, try exact match first
        if provider_name:
            full_name = f"{provider_name}/{model_name}"
            model = self.get(full_name)
            if model:
                logger.debug(f"Found model by full name: {full_name}")
                return model
            logger.debug(f"No model found with full name: {full_name}")
            return None
        
        # Search by model name or API identifier
        for model in self.data.values():
            if model.name.endswith(f"/{model_name}") or model.model == model_name:
                logger.debug(f"Found model '{model.name}' matching '{model_name}'")
                return model
                
        logger.debug(f"No model found matching '{model_name}'")
        return None
    
    def get_providers(self) -> List[str]:
        """Get a list of all configured providers.
        
        Returns:
            List of provider names
        """
        providers = set(model.provider for model in self.data.values())
        return sorted(list(providers))
    
    def get_models_by_provider(self, provider_name: str) -> List[ModelConfig]:
        """Get all models for a specific provider.
        
        Args:
            provider_name: The name of the provider
            
        Returns:
            List of ModelConfig objects for the specified provider
        """
        if not provider_name:
            logger.warning("Empty provider_name provided to get_models_by_provider")
            return []
            
        models = [model for model in self.data.values() if model.provider == provider_name]
        logger.debug(f"Found {len(models)} models for provider '{provider_name}'")
        return models
    
    def list_models(self) -> Dict[str, List[str]]:
        """Get a summary of all configured models grouped by provider.
        
        Returns:
            Dictionary mapping provider names to lists of model names
        """
        result = {}
        for model in self.data.values():
            if model.provider not in result:
                result[model.provider] = []
            result[model.provider].append(model.name.split('/')[-1])  # Just the model name without provider prefix
            
        return result
