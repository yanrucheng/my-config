# My Config

A reusable configuration management package for Python applications.

## Features

- Base configuration with file loading capabilities
- Environment-aware configuration (DEV/BOE/PROD)
- Specialized configuration for LLM models
- Singleton pattern implementation for efficient configuration management

## Installation

This package is not published to PyPI. You can install it using one of the following methods:

### From Git Repository

```bash
pip install git+https://github.com/yourusername/my-config.git
```

Or specify it in requirements.txt:

```
git+https://github.com/yourusername/my-config.git@v0.1.0
```

### Local Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/my-config.git
cd my-config

# Install in development mode
pip install -e .
```

# My Config

A robust configuration management library for Python applications.

## Features

- Singleton-based configuration classes
- File-based configuration with YAML support
- Environment-aware configuration loading
- Recursive configuration loading protection
- Robust error handling

## Usage

### Basic Configuration

```python
from my_config import BaseConfig

class MyAppConfig(BaseConfig):
    CONFIG_FILENAME = "./conf/my_app_config.yml"

# Get the singleton instance
config = MyAppConfig.get_instance()

# Get configuration values with defaults
db_host = config.get('database', {}).get('host', 'localhost')
port = config.get('port', 8080)

# Access configuration values
db_url = config.get("database_url")
```

### Environment-Aware Configuration

```python
from my_config import EnvAwareConfig

class MyEnvConfig(EnvAwareConfig):
    DEV_CONFIG_FILENAME = "./conf/dev_config.yml"
    BOE_CONFIG_FILENAME = "./conf/boe_config.yml"
    PROD_CONFIG_FILENAME = "./conf/prod_config.yml"

# Configuration will be loaded based on APP_ENV environment variable
config = MyEnvConfig.get_instance()
```

## Extending

You can create your own configuration classes by extending the base classes:

```python
from my_config import BaseConfig
from typing import Dict, Any

class CustomConfig(BaseConfig[Dict[str, Any]]):
    CONFIG_FILENAME = "./custom_config.yml"
    
    def _process_config(self) -> None:
        # Custom processing logic
        self.data = {k.upper(): v for k, v in self._data.items()}
```

## Environment Variables

The package uses the following environment variables:

- `APP_ENV`: Determines the environment ("dev", "boe", or "production")
- `CONFIG_PATH`: Specifies the path to a configuration file for BaseConfig
- `ENV_CONFIG_PATH`: Specifies the path to a configuration file for EnvAwareConfig

## Configuration File Resolution

The package uses a priority-based approach to locate configuration files:

1. **Code-specified path** (highest priority): Paths explicitly set in the code
2. **Environment variable**: Path specified via environment variables
3. **Default locations**: Search in standard locations

### Example

```bash
# Set the configuration file path
export CONFIG_PATH=/path/to/your/config.yml

# Run your application
python your_app.py
```

Detailed logging is provided to show which configuration files were detected and which one was ultimately selected.