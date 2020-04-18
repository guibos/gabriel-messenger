"""Configuration Module. This module is a helper to parse config.yaml."""
from pathlib import Path
from typing import Dict, Union

import yaml

from src.ser.common.enums.environment import Environment


class ConfigurationError(Exception):
    """A specific configuration error."""


class Configuration:
    """Read configuration from file."""

    _CONFIG_PATH = "config.yaml"

    def __init__(self,
                 *,
                 config_path: Path = None,
                 environment: Environment = None,
                 app_logging_level: str = None,
                 global_logging_level: str = None) -> None:
        """Get a configuration object with a configuration file read."""
        self._config_path = config_path or self._CONFIG_PATH
        with open(self._config_path, 'r', encoding='utf-8') as file:
            self._config = yaml.load(file, Loader=yaml.SafeLoader)

        if environment:
            self._config['configuration']['environment'] = environment
        else:
            self._config['configuration']['environment'] = Environment(self._config['configuration']['environment'])

        if app_logging_level:
            self._config['configuration']['app_logging_level'] = app_logging_level
        else:
            self._config['configuration']['app_logging_level'] = self._config['configuration']['app_logging_level']

        if global_logging_level:
            self._config['configuration']['global_logging_level'] = global_logging_level
        else:
            self._config['configuration']['global_logging_level'] = self._config['configuration'][
                'global_logging_level']

    def get_global_configuration(self) -> Dict[str, Union[str, Environment, dict]]:
        """Get a configuration section.
        :return: (dict) dictionary of values).
        """
        try:
            return self._config['configuration']
        except KeyError:
            raise ConfigurationError(f"Missing section configuration")

    def get_modules(self) -> Dict[str, dict]:
        """Get all modules that matches with the current environment."""
        try:
            return self._config['environment'][self._config['configuration']['environment'].value]
        except KeyError:
            raise ConfigurationError(f"Missing environment '{self._config['configuration']['environment'].value}'")
