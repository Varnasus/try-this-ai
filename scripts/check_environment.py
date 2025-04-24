import os
import sys
from pathlib import Path

from config import Config, Environment


def check_environment():
    """Check if the current Python environment matches the configuration."""
    # Load configuration
    Config.load_config(Environment.PRODUCTION)

    # Check Python version
    required_version = Config.get("environment.python.version")
    current_version = (
        f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    )

    if current_version != required_version:
        print(f"⚠️ Warning: Python version mismatch")
        print(f"Required: {required_version}")
        print(f"Current:  {current_version}")
        return False

    # Check virtual environment
    venv_path = Config.get("environment.paths.virtualenv")
    if not os.environ.get("VIRTUAL_ENV"):
        print("⚠️ Warning: Not running in a virtual environment")
        print(f"Please activate the virtual environment at: {venv_path}")
        return False

    if not os.environ["VIRTUAL_ENV"].endswith(venv_path):
        print("⚠️ Warning: Wrong virtual environment active")
        print(f"Required: {venv_path}")
        print(f"Current:  {os.environ['VIRTUAL_ENV']}")
        return False

    # Check required packages
    try:
        import pkg_resources

        requirements_files = Config.get("environment.python.virtualenv.requirements")
        missing_packages = []

        for req_file in requirements_files:
            if not Path(req_file).exists():
                continue

            with open(req_file) as f:
                requirements = pkg_resources.parse_requirements(f)
                for requirement in requirements:
                    try:
                        pkg_resources.require(str(requirement))
                    except (
                        pkg_resources.DistributionNotFound,
                        pkg_resources.VersionConflict,
                    ):
                        missing_packages.append(str(requirement))

        if missing_packages:
            print("⚠️ Warning: Missing required packages:")
            for package in missing_packages:
                print(f"  - {package}")
            return False

    except ImportError:
        print("⚠️ Warning: Could not check package requirements")
        return False

    print("✅ Environment check passed!")
    return True


if __name__ == "__main__":
    sys.exit(0 if check_environment() else 1)
