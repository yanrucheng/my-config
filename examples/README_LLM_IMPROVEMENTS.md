# Enhanced LLM Configuration - SingletonFileLoader Best Practices

This document outlines the improvements made to the LLM configuration system following the best practices demonstrated in the `jinnang.common.patterns.SingletonFileLoader` example.

## Key Improvements

### 1. **Flexible File Loading Options**

The enhanced `LLMConfig` class now supports multiple loading methods:

```python
# Load by filename with search locations
config = LLMConfig(
    filename="llm_config.yml",
    search_locations=["/path/to/configs", "./config"],
    verbosity=Verbosity.FULL
)

# Load by explicit path
config = LLMConfig(
    explicit_path="/full/path/to/llm_config.yml",
    verbosity=Verbosity.ONCE
)

# Use default search locations
config = LLMConfig()  # Searches common config directories
```

### 2. **Robust Error Handling and Validation**

#### Configuration Validation
- Comprehensive validation of provider and model configurations
- Clear error messages for missing or invalid fields
- Graceful handling of empty or malformed configuration files
- Duplicate model name detection

#### ModelConfig Validation
- Post-initialization validation with `__post_init__`
- String normalization (trimming whitespace, normalizing URLs)
- Empty field validation for required attributes
- Tag list cleanup and normalization

### 3. **Enhanced Search Capabilities**

The configuration now provides multiple ways to find models:

```python
# Get model by exact name
model = config.get("openai/gpt-4")

# Get model by name and provider
model = config.get_model("gpt-4", "openai")

# Get first model with specific tag
model = config.get_model_by_tag("fast")

# Get all models with specific tag
models = config.get_models_by_tag("premium")

# Get all models from a provider
models = config.get_models_by_provider("anthropic")

# Get summary of all models
summary = config.list_models()
```

### 4. **Improved ModelConfig Class**

The `ModelConfig` dataclass now includes:

- **Validation**: Automatic validation of required fields
- **Normalization**: String trimming and URL normalization
- **Utility Methods**: 
  - `has_tag(tag)`: Check if model has a specific tag
  - `get_full_api_url(endpoint)`: Build complete API URLs
  - `to_dict()`: Convert to dictionary representation

### 5. **Default Search Locations**

When no explicit path or search locations are provided, the system automatically searches:

- Current directory (`.`)
- `./config` subdirectory
- `./configs` subdirectory
- User config directory (`~/.config`)
- System config directory (`/etc`) on Unix-like systems

### 6. **Comprehensive Logging**

- Configurable verbosity levels using `jinnang.verbosity.Verbosity`
- Detailed debug logging for troubleshooting
- Warning messages for potential issues
- Error logging with context information

## Usage Examples

### Basic Usage

```python
from my_config.llm import LLMConfig
from jinnang.verbosity import Verbosity

# Load configuration with default settings
config = LLMConfig(verbosity=Verbosity.FULL)

# Get a fast model for quick responses
fast_model = config.get_model_by_tag("fast")
if fast_model:
    print(f"Using {fast_model.name} for quick responses")
    api_url = fast_model.get_full_api_url("chat/completions")
    print(f"API URL: {api_url}")
```

### Advanced Configuration

```python
# Load from specific locations with custom search
config = LLMConfig(
    filename="production_llm_config.yml",
    search_locations=[
        "/etc/myapp",
        "/opt/myapp/config",
        "./config"
    ],
    verbosity=Verbosity.ONCE
)

# Get all premium models for complex tasks
premium_models = config.get_models_by_tag("premium")
for model in premium_models:
    print(f"Premium model: {model.name} - {model.description}")
```

### Error Handling

```python
try:
    config = LLMConfig(
        explicit_path="/path/to/config.yml",
        verbosity=Verbosity.FULL
    )
    
    if not config.loaded_filepath:
        print("No configuration file was loaded")
        # Handle gracefully with empty configuration
    else:
        # Use loaded configuration
        providers = config.get_providers()
        print(f"Available providers: {providers}")
        
except ValueError as e:
    print(f"Configuration error: {e}")
    # Handle invalid configuration
except Exception as e:
    print(f"Unexpected error: {e}")
    # Handle other errors
```

## Configuration File Structure

See `sample_llm_config.yml` for a complete example. The structure follows this pattern:

```yaml
providers:
  provider_name:
    api_key: "${ENV_VAR_NAME}"  # Use environment variables
    base_url: "https://api.provider.com/v1"
    models:
      - name: "model-name"
        model: "api-model-identifier"
        tags: ["tag1", "tag2"]
        description: "Model description"
```

## Best Practices Implemented

1. **Singleton Pattern**: Efficient resource usage through SingletonFileLoader
2. **Flexible Loading**: Support for both filename-based and explicit path loading
3. **Robust Validation**: Comprehensive error checking and validation
4. **Clear Documentation**: Extensive docstrings and type hints
5. **Logging Integration**: Proper logging with configurable verbosity
6. **Security Considerations**: Support for environment variables in configuration
7. **Graceful Degradation**: Handles missing files and invalid configurations
8. **Extensible Design**: Easy to add new providers and model types

## Migration from Previous Version

The enhanced version is backward compatible, but you can take advantage of new features:

```python
# Old way (still works)
config = LLMConfig()
model = config.get("openai/gpt-4")

# New way (recommended)
config = LLMConfig(
    search_locations=["./config", "/etc/myapp"],
    verbosity=Verbosity.ONCE
)
model = config.get_model("gpt-4", "openai")
```

## Testing

Run the example to see all features in action:

```bash
python examples/llm_config_example.py
```

This will demonstrate:
- Loading configurations from different sources
- Error handling with invalid configurations
- Model retrieval using various methods
- Singleton behavior and caching

## Files Added/Modified

- **Enhanced**: `src/my_config/llm.py` - Main LLM configuration class
- **Added**: `examples/llm_config_example.py` - Comprehensive usage example
- **Added**: `examples/sample_llm_config.yml` - Sample configuration file
- **Added**: `examples/README_LLM_IMPROVEMENTS.md` - This documentation

These improvements make the LLM configuration system more robust, flexible, and easier to use while following the best practices demonstrated in the SingletonFileLoader example.