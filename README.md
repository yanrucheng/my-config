# my-config

`my-config` is a robust and flexible configuration management library for Python applications, designed to simplify the loading and management of application settings. It supports environment-aware configurations, secret management via environment variables, and structured loading for various application components like Language Model (LLM) configurations.

## Features

-   **Base Configuration**: Load configurations from YAML files with environment variable resolution.
-   **Environment-Aware Configuration**: Automatically load environment-specific configurations (e.g., `dev`, `prod`) based on the `APP_ENV` environment variable.
-   **LLM Configuration**: Specialized support for managing Language Model API keys, base URLs, and model-specific settings.
-   **Efficient Resource Usage**: Configuration files are loaded efficiently, ensuring optimal resource utilization.
-   **Caller-Aware File Loading**: Intelligently locates configuration files relative to the calling module.
-   **Environment Variable Resolution**: Seamlessly injects environment variables into configuration values using `${VAR_NAME}` syntax.

## Installation

`my-config` is not yet published to PyPI. You can install it directly from the GitHub repository:

```bash
pip install git+https://github.com/yanrucheng/my-config.git
```

Alternatively, for local development:

```bash
git clone https://github.com/yanrucheng/my-config.git
cd my-config
pip install -e .
```

## Usage Examples

This section demonstrates how to use `my-config` classes with practical examples. For a complete runnable example, refer to the <mcfile name="example.py" path="example/example.py"></mcfile> file in the `example/` directory.

### 1. BaseConfig: Loading General Configurations

<mcsymbol name="BaseConfig" filename="base.py" path="src/my_config/base.py" startline="14" type="class"></mcsymbol> is the foundational class for loading configurations from a specified YAML file. It supports resolving environment variables within the configuration.

**Configuration File (`conf/base.yml`):

```yaml
database:
  host: localhost
  port: 5432
  username: admin
  password: ${DB_PASSWORD}

app:
  name: MyApplication
  version: 1.0.0
```

**Python Usage (`example/example.py` excerpt):

```python
import os
from my_config.base import BaseConfig
from jinnang.verbosity import Verbosity

# Set an environment variable that will be resolved in the config
os.environ['DB_PASSWORD'] = 'supersecretpassword'

base_config = BaseConfig(
    filename='conf/base.yml',
    verbosity=Verbosity.FULL, # Or Verbosity.ONCE for less verbose output
    caller_module_path=__file__,
)

print("\n--- BaseConfig ---")
print(f"Loaded from: {base_config.loaded_filepath}")
print(f"Database Host: {base_config.get('database.host')}")
print(f"Database Password: {base_config.get('database.password')}") # Resolved from env var
print(f"Application Name: {base_config.get('app.name')}")
```

### 2. EnvAwareConfig: Environment-Specific Configurations

<mcsymbol name="EnvAwareConfig" filename="env_aware.py" path="src/my_config/env_aware.py" startline="4" type="class"></mcsymbol> extends <mcsymbol name="BaseConfig" filename="base.py" path="src/my_config/base.py" startline="14" type="class"></mcsymbol> to load configurations based on the `APP_ENV` environment variable. It searches for files in a predefined order (production, boe, development).

**Configuration Files (e.g., `conf/my_app.dev.yml`):

```yaml
app_env: development
debug_mode: true
api_url: http://dev.api.example.com
```

**Python Usage (`example/example.py` excerpt):

```python
import os
from my_config.env_aware import EnvAwareConfig
from jinnang.verbosity import Verbosity

# Set APP_ENV to 'development' to load the dev config
os.environ['APP_ENV'] = 'development'

env_aware_config = EnvAwareConfig(
    base_filename='conf/my_app.yml', # Base name for env-aware config
    dev_filename='conf/my_app.dev.yml', # Explicitly specify dev filename
    verbosity=Verbosity.FULL,
    caller_module_path=__file__,
)

print("\n--- EnvAwareConfig ---")
print(f"Loaded from: {env_aware_config.loaded_filepath}")
print(f"Application Environment: {env_aware_config.get('app_env')}")
print(f"Debug Mode: {env_aware_config.get('debug_mode')}")
```

### 3. LLMConfig: Managing Language Model Configurations

<mcsymbol name="LLMConfig" filename="llm.py" path="src/my_config/llm.py" startline="99" type="class"></mcsymbol> is a specialized configuration class for managing Language Model settings, including API keys and base URLs. It processes a `providers` section in the YAML file to create <mcsymbol name="ModelConfig" filename="llm.py" path="src/my_config/llm.py" startline="15" type="class"></mcsymbol> objects.

**Configuration File (`conf/llm.yml`):

```yaml
providers:
  openai:
    api_key: ${OPENAI_API_KEY}
    base_url: https://api.openai.com/v1
    models:
      - name: openai/gpt-4
        model: gpt-4
        tags: ["chat", "large"]
        description: OpenAI's most advanced GPT-4 model.
      - name: openai/gpt-3.5-turbo
        model: gpt-3.5-turbo
        tags: ["chat", "fast"]

  anthropic:
    api_key: ${ANTHROPIC_API_KEY}
    base_url: https://api.anthropic.com/v1
    models:
      - name: anthropic/claude-3-opus
        model: claude-3-opus-20240229
        tags: ["chat", "large"]
```

**Python Usage (`example/example.py` excerpt):

```python
import os
from my_config.llm import LLMConfig
from jinnang.verbosity import Verbosity

# Set the environment variable for the API key
os.environ["OPENAI_API_KEY"] = "sk-YOUR_ACTUAL_OPENAI_API_KEY_HERE"

llm_config = LLMConfig(
    filename='conf/llm.yml',
    verbosity=Verbosity.FULL,
    caller_module_path=__file__,
)

print("\n--- LLMConfig ---")
# Access a specific model configuration
openai_gpt4_config = llm_config.get("openai/gpt-4")

if openai_gpt4_config:
    print(f"OpenAI GPT-4 API Key: {openai_gpt4_config.api_key}")
    print(f"OpenAI GPT-4 Base URL: {openai_gpt4_config.base_url}")
    print(f"OpenAI GPT-4 Model Name: {openai_gpt4_config.model}")
    print(f"OpenAI GPT-4 Tags: {openai_gpt4_config.tags}")
else:
    print("OpenAI GPT-4 configuration not found.")

# Clean up the environment variable (optional, for script execution)
del os.environ["OPENAI_API_KEY"]
```

## Development

To contribute or run tests, clone the repository and install dependencies:

```bash
git clone https://github.com/yanrucheng/my-config.git
cd my-config
pip install -e .[dev]
pytest
```

## License

This project is licensed under the MIT License - see the <mcfile name="LICENSE" path="LICENSE"></mcfile> file for details.