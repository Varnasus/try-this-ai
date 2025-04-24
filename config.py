import logging
import os
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


class Environment(str, Enum):
    DEVELOPMENT = "development"
    PRODUCTION = "production"
    TESTING = "testing"


@dataclass
class ConfigValidation:
    required: bool = True
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    allowed_values: Optional[list] = None
    type: Optional[type] = None


class Config:
    _instance = None
    _config: Dict[str, Any] = {}
    _validations: Dict[str, ConfigValidation] = {}
    _environment: Environment = Environment.DEVELOPMENT
    _version: str = "1.0.0"

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._config:
            self._setup_validations()
            self.load_config()

    @classmethod
    def _setup_validations(cls) -> None:
        """Setup validation rules for configuration values."""
        cls._validations = {
            "app.debug": ConfigValidation(type=bool),
            "app.log_level": ConfigValidation(
                allowed_values=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
            ),
            "api.openai.max_tokens": ConfigValidation(
                type=int, min_value=1, max_value=4000
            ),
            "api.openai.temperature": ConfigValidation(
                type=float, min_value=0.0, max_value=1.0
            ),
            "video.resolution.width": ConfigValidation(
                type=int, min_value=640, max_value=7680
            ),
            "video.resolution.height": ConfigValidation(
                type=int, min_value=480, max_value=4320
            ),
            "video.fps": ConfigValidation(type=int, min_value=1, max_value=120),
            "files.max_size.script": ConfigValidation(
                type=int, min_value=1024, max_value=10485760
            ),
        }

    @classmethod
    def _validate_value(cls, key: str, value: Any) -> bool:
        """Validate a configuration value against its rules."""
        if key not in cls._validations:
            return True

        validation = cls._validations[key]

        if validation.required and value is None:
            logging.error(f"Required configuration value missing: {key}")
            return False

        if validation.type and not isinstance(value, validation.type):
            logging.error(
                f"Invalid type for {key}: expected {validation.type}, got {type(value)}"
            )
            return False

        if validation.min_value is not None and value < validation.min_value:
            logging.error(
                f"Value too small for {key}: {value} < {validation.min_value}"
            )
            return False

        if validation.max_value is not None and value > validation.max_value:
            logging.error(
                f"Value too large for {key}: {value} > {validation.max_value}"
            )
            return False

        if validation.allowed_values and value not in validation.allowed_values:
            logging.error(
                f"Invalid value for {key}: {value} not in {validation.allowed_values}"
            )
            return False

        return True

    @classmethod
    def load_config(cls, env: Optional[Environment] = None) -> None:
        """Load configuration from YAML file with environment support."""
        if env:
            cls._environment = env

        base_path = Path(__file__).parent
        config_path = base_path / f"config.{cls._environment.value}.yaml"

        if not config_path.exists():
            config_path = base_path / "config.yaml"

        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found at {config_path}")

        with open(config_path, "r") as f:
            cls._config = yaml.safe_load(f)

        # Validate all configuration values
        for key in cls._validations:
            value = cls.get(key)
            if not cls._validate_value(key, value):
                raise ValueError(f"Invalid configuration value for {key}")

    @classmethod
    def get(cls, key: str, default: Any = None) -> Any:
        """Get configuration value by key."""
        keys = key.split(".")
        value = cls._config

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k, default)
            else:
                return default
        return value

    @classmethod
    def set(cls, key: str, value: Any) -> None:
        """Set configuration value with validation."""
        if not cls._validate_value(key, value):
            raise ValueError(f"Invalid value for {key}: {value}")

        keys = key.split(".")
        current = cls._config

        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]

        current[keys[-1]] = value

    @classmethod
    def migrate_config(cls, target_version: str) -> None:
        """Migrate configuration to a new version."""
        current_version = cls._version
        if current_version == target_version:
            return

        migrations = {
            "1.0.0": {
                "1.1.0": cls._migrate_1_0_0_to_1_1_0,
            },
            "1.1.0": {
                "1.2.0": cls._migrate_1_1_0_to_1_2_0,
            },
        }

        while current_version != target_version:
            if current_version not in migrations:
                raise ValueError(
                    f"No migration path from {current_version} to {target_version}"
                )

            next_version = next(iter(migrations[current_version].keys()))
            migrations[current_version][next_version]()
            current_version = next_version

    @classmethod
    def _migrate_1_0_0_to_1_1_0(cls) -> None:
        """Migration from version 1.0.0 to 1.1.0."""
        # Example migration: Add new configuration values
        if "new_feature" not in cls._config:
            cls._config["new_feature"] = {"enabled": False, "threshold": 0.5}
        cls._version = "1.1.0"

    @classmethod
    def _migrate_1_1_0_to_1_2_0(cls) -> None:
        """Migration from version 1.1.0 to 1.2.0."""
        # Example migration: Rename or restructure configuration
        if "old_feature" in cls._config:
            cls._config["new_feature_name"] = cls._config.pop("old_feature")
        cls._version = "1.2.0"


# Example usage:
# from config import Config, Environment
#
# # Load production configuration
# Config.load_config(Environment.PRODUCTION)
#
# # Get configuration values with validation
# model = Config.get('api.openai.model')
#
# # Set configuration values with validation
# Config.set('video.fps', 60)
#
# # Migrate configuration to new version
# Config.migrate_config("1.2.0")
