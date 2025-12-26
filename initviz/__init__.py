import subprocess
import logging
import os

def _read_version_file():
    """Read version from VERSION file."""
    version_file = os.path.join(os.path.dirname(__file__), '..', 'VERSION')
    try:
        with open(version_file, 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        return None

__version__ = _read_version_file() or "unknown"


def get_git_version():
    try:
        output = subprocess.check_output(["git", "describe", "--tags", "--always"])
        return output.strip().decode('utf-8')
    except Exception as err:
        logging.debug("Git describe failed: %s", err)
        return __version__


def get_version():
    try:
        import importlib.metadata
        return importlib.metadata.version("initviz")
    except Exception as err:
        logging.debug("Not installed, using git version: %s", err)
        return get_git_version()
