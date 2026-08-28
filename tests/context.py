"""Put scripts/ on the import path so the checks can be imported as modules.

The scripts are command-line tools rather than an installed package, so there
is no package to import from. This adds the directory to sys.path once, and
every test module imports through here rather than repeating the boilerplate.
"""
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS_DIR = os.path.join(REPO_ROOT, "scripts")

if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)
