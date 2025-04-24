from pathlib import Path
from typing import Any, Dict

import yaml

from config import Config, Environment


def backup_config(config_path: Path) -> None:
    """Create a backup of the current configuration file."""
    backup_path = config_path.with_suffix(".yaml.bak")
    if config_path.exists():
        with open(config_path, "r") as src, open(backup_path, "w") as dst:
            dst.write(src.read())


def migrate_config_files() -> None:
    """Migrate all configuration files to the latest version."""
    base_path = Path(__file__).parent

    # Migrate each environment's config file
    for env in Environment:
        config_path = base_path / f"config.{env.value}.yaml"
        if config_path.exists():
            backup_config(config_path)

            # Load and migrate the configuration
            Config.load_config(env)
            Config.migrate_config("1.2.0")

            # Save the migrated configuration
            with open(config_path, "w") as f:
                yaml.dump(Config._config, f, default_flow_style=False)


if __name__ == "__main__":
    migrate_config_files()
