import os
from typing import Optional, List, Dict, Any
from jinnang.common import SingletonFileLoader

class EnvAwareConfig(SingletonFileLoader):
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
        config = EnvAwareConfig(base_filename='config.json', caller_module_path=__file__)
        print(config.filepath)

        # Custom filenames
        custom_config = EnvAwareConfig(
            prod_filename='my_app.prod.yaml',
            boe_filename='my_app.boe.yaml',
            dev_filename='my_app.dev.yaml',
            caller_module_path=__file__
        )
        print(custom_config.filepath)
    """

    def __init__(
        self,
        base_filename: Optional[str] = None,
        prod_filename: Optional[str] = None,
        boe_filename: Optional[str] = None,
        dev_filename: Optional[str] = None,
        caller_module_path: Optional[str] = None,
        search_locations: Optional[List[str]] = None,
        **kwargs: Any
    ):
        if not hasattr(self, '_env_aware_initialized'):
            self._env_aware_initialized = True

            self.base_filename = base_filename
            self.prod_filename = prod_filename
            self.boe_filename = boe_filename
            self.dev_filename = dev_filename
            self.caller_module_path = caller_module_path
            self.search_locations = search_locations

            # Determine the effective filenames with fallback to base_filename
            effective_prod_filename = self.prod_filename or (f"{base_filename.rsplit('.', 1)[0]}.prod.{base_filename.rsplit('.', 1)[1]}" if base_filename else None)
            effective_boe_filename = self.boe_filename or (f"{base_filename.rsplit('.', 1)[0]}.boe.{base_filename.rsplit('.', 1)[1]}" if base_filename else None)
            effective_dev_filename = self.dev_filename or (f"{base_filename.rsplit('.', 1)[0]}.dev.{base_filename.rsplit('.', 1)[1]}" if base_filename else None)

            # Define the search order for environment-specific files
            self.env_search_order = []
            if effective_prod_filename: self.env_search_order.append(effective_prod_filename)
            if effective_boe_filename: self.env_search_order.append(effective_boe_filename)
            if effective_dev_filename: self.env_search_order.append(effective_dev_filename)

            found_file = False
            for filename_to_try in self.env_search_order:
                try:
                    # Attempt to resolve the file path using the parent's method
                    resolved_path = self.resolve_file_path(
                        filename=filename_to_try,
                        caller_module_path=self.caller_module_path,
                        search_locations=self.search_locations
                    )
                    self.loaded_filepath = resolved_path
                    print(f"Found config file: {self.loaded_filepath} (for {filename_to_try})")
                    found_file = True
                    break
                except FileNotFoundError:
                    print(f"Config file not found: {filename_to_try}. Trying next environment...")

            if not found_file:
                raise FileNotFoundError(
                    f"Could not find any environment-specific config file "
                    f"(tried: {', '.join(self.env_search_order)}) "
                    f"in specified locations: {self.search_locations or 'default'}."
                )

        # Call parent init but preserve our loaded_filepath
        temp_filepath = getattr(self, 'loaded_filepath', None)
        super().__init__(**kwargs)
        if temp_filepath is not None:
            self.loaded_filepath = temp_filepath

    @property
    def filepath(self) -> Optional[str]:
        """Returns the path to the loaded configuration file."""
        return self.loaded_filepath

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