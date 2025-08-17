"""
KLMD module entry point.

Allows running KLMD as a module: python -m klmd
"""

import sys

from .cli import main

if __name__ == "__main__":
    sys.exit(main())