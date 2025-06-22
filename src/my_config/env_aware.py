import os
from typing import Optional, List, Dict, Any
from jinnang.common.patterns import SingletonFileLoader
from jinnang.verbosity import Verbosity
from my_config.base import BaseConfig

class EnvAwareConfig(BaseConfig):
    """
    Environment-aware configuration loader with fallback logic.

    This class extends SingletonFileLoader to provide a configuration system
    that prioritizes environment-specific configuration files (prod, boe, dev)
    with a defined fallback order.

    Configuration files are searched in the following order:
    1. Production (prod)
    2. Business Operations Environment (boe)
    3. Development (dev)

    The first found configuration file is loaded. If no file is found, an
    error is raised.

    Usage:
        # Default filenames (config.prod.json, config.boe.json, config.dev.json)
        config = EnvAwareConfig(
            base_filename='config.json', 
            caller_module_path=__file__,
            verbosity=Verbosity.FULL
        )
        print(config.loaded_filepath)

        # Custom filenames with search locations
        custom_config = EnvAwareConfig(
            prod_filename='my_app.prod.yaml',
            boe_filename='my_app.boe.yaml',
            dev_filename='my_app.dev.yaml',
            caller_module_path=__file__,
            search_locations=['./config', '/etc/myapp'],
            verbosity=Verbosity.DETAIL
        )
        print(custom_config.loaded_filepath)

        # Minimal verbosity for production use
        prod_config = EnvAwareConfig(
            base_filename='app.yml',
            caller_module_path=__file__,
            verbosity=Verbosity.ONCE
        )
    """

    def __init__(
        self,
        base_filename: Optional[str] = None,
        prod_filename: Optional[str] = None,
        boe_filename: Optional[str] = None,
        dev_filename: Optional[str] = None,
        caller_module_path: Optional[str] = None,
        verbosity: Verbosity = Verbosity.FULL,
        **kwargs: Any
    ):
        # Store environment-specific parameters for singleton initialization
        if not hasattr(self, '_env_aware_initialized'):
            self._env_aware_initialized = True
            
            self.base_filename = base_filename
            self.prod_filename = prod_filename
            self.boe_filename = boe_filename
            self.dev_filename = dev_filename
            
            # Determine the effective filenames with fallback to base_filename
            effective_prod_filename = self.prod_filename or (f"{base_filename.rsplit('.', 1)[0]}.prod.{base_filename.rsplit('.', 1)[1]}" if base_filename else None)
            effective_boe_filename = self.boe_filename or (f"{base_filename.rsplit('.', 1)[0]}.boe.{base_filename.rsplit('.', 1)[1]}" if base_filename else None)
            effective_dev_filename = self.dev_filename or (f"{base_filename.rsplit('.', 1)[0]}.dev.{base_filename.rsplit('.', 1)[1]}" if base_filename else None)
            
            # Define the search order for environment-specific files based on APP_ENV
            app_env = os.environ.get('APP_ENV')
            self.env_search_order = []

            if app_env == 'production' and effective_prod_filename:
                self.env_search_order.append(effective_prod_filename)
            elif app_env == 'boe' and effective_boe_filename:
                self.env_search_order.append(effective_boe_filename)
            elif app_env == 'development' and effective_dev_filename:
                self.env_search_order.append(effective_dev_filename)
            else:
                # Fallback to default search order if APP_ENV is not set or recognized
                if effective_prod_filename: self.env_search_order.append(effective_prod_filename)
                if effective_boe_filename: self.env_search_order.append(effective_boe_filename)
                if effective_dev_filename: self.env_search_order.append(effective_dev_filename)
            
            # Try to find the first available environment-specific config file
            found_filename = None
            for filename_to_try in self.env_search_order:
                try:
                    # Use parent's resolve_file_path to check if file exists
                    resolved_path = self.resolve_file_path(
                        filename=filename_to_try,
                        caller_module_path=caller_module_path
                    )
                    found_filename = filename_to_try
                    break
                except FileNotFoundError:
                    continue
            
            # If no environment-specific file found, raise error
            if not found_filename:
                raise FileNotFoundError(
                    f"Could not find any environment-specific config file "
                    f"(tried: {', '.join(self.env_search_order)}) "
                    f"relative to caller module path."
                )
            
            # Store the found filename for parent initialization
            self._resolved_filename = found_filename
        
        # Initialize BaseConfig with proper parameters
        super().__init__(
            filename=getattr(self, '_resolved_filename', None),
            caller_module_path=caller_module_path,
            verbosity=verbosity,
            **kwargs
        )

    # You can add methods here to load and parse the config content
    # For example, if it's a JSON or YAML file.
    # def load_config_content(self) -> Dict[str, Any]:
    #     if not self.filepath:
    #         return {}
    #     with open(self.filepath, 'r') as f:
    #         # Add logic to parse JSON, YAML, etc.
    #         if self.filepath.endswith('.json'):
    #             import json
    #             return json.load(f)
    #         elif self.filepath.endswith(('.yaml', '.yml')):
    #             import yaml
    #             return yaml.safe_load(f)
    #         else:
    #             raise ValueError(f"Unsupported config file type: {self.filepath}")