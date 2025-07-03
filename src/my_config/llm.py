"""LLM-specific configuration classes.

This module provides configuration classes for language models and their providers.
Follows jinnang RelPathSeeker best practices for robust configuration management.
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
        notes: Optional list of notes for human readability
        description: Optional human-readable description
        purpose: Optional list of purposes (e.g., ['llm_primary', 'vlm_primary'])
    """
    name: str
    model: str  # API identifier
    provider: str
    api_key: str
    base_url: str
    notes: Optional[List[str]] = None
    description: Optional[str] = None
    purpose: Optional[List[str]] = None
    
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
        if self.notes:
            self.notes = [note.strip() for note in self.notes if note and note.strip()]
            if not self.notes:
                self.notes = None
        if self.purpose:
            self.purpose = [p.strip() for p in self.purpose if p and p.strip()]
            if not self.purpose:
                self.purpose = None
    



class LLMConfig(BaseConfig[ModelConfig]):
    """LLM-specific configuration with provider processing.
    
    Follows RelPathSeeker best practices:
    - Supports both filename-based and explicit path loading
    - Provides flexible search locations
    - Includes proper error handling and validation

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
            
        BaseConfig.__init__(
            self,
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
                        notes=model_data.get("notes"),
                        description=model_data.get("description"),
                        purpose=model_data.get("purpose")
                    )
                    logger.debug(f"Successfully configured model: {model_name}")
                except Exception as e:
                    raise ValueError(f"Failed to create ModelConfig for '{model_name}': {e}") from e
        
        if not data:
            logger.warning("No valid models were configured")
            
        logger.info(f"Successfully processed {len(data)} models from {len(providers_data)} providers")
        return data

    def _validate_primary_models(self, processed_data: Dict[str, ModelConfig]) -> None:
        """Validate that there is exactly one primary model for each purpose type (llm_primary and vlm_primary).
        
        Args:
            processed_data: Dictionary of processed ModelConfig objects
            
        Raises:
            AssertionError: If there is not exactly one primary model of each type
        """
        for purpose_type in ['llm_primary', 'vlm_primary']:
            primary_models = [model for model in processed_data.values()
                            if model.purpose and purpose_type in model.purpose]
            assert len(primary_models) == 1, (
                f'There should be one and only one model with purpose \'{purpose_type}\'. '
                f'Got {len(primary_models)}. Includes: {[m.name for m in primary_models]}'
            )

    def get_model(
        self,
        model_name: Optional[str] = None,
        purpose: Optional[str] = None,
        provider_name: Optional[str] = None
    ) -> Optional[ModelConfig]:
        """Get a model configuration by name or purpose.

        Args:
            model_name: The name of the model to find.
            purpose: The purpose of the model to find (e.g., 'llm_primary').
            provider_name: Optional provider name to narrow the search (only used with model_name).

        Returns:
            ModelConfig if found, None otherwise.

        Raises:
            ValueError: If both or neither of model_name and purpose are provided.
        """
        if (model_name and purpose) or (not model_name and not purpose):
            raise ValueError("Provide either model_name or purpose, but not both.")

        if model_name:
            return self._get_model_by_name(model_name, provider_name)
        
        if purpose:
            return self._get_model_by_purpose(purpose)

        return None

    def _get_model_by_purpose(self, purpose: str) -> Optional[ModelConfig]:
        """Get a model by its purpose.

        Args:
            purpose: The purpose of the model to find.

        Returns:
            ModelConfig if found, None otherwise.
        """
        for model in self.data.values():
            if model.purpose and purpose in model.purpose:
                return model
        return None

    def _get_model_by_name(self, model_name: str, provider_name: Optional[str] = None) -> Optional[ModelConfig]:
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
