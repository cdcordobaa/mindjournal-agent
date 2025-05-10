#!/usr/bin/env python3

import sys
print(f"Python executable: {sys.executable}")

try:
    import pydub
    print(f"pydub imported successfully, version: {pydub.__version__}")
except ImportError as e:
    print(f"Error importing pydub: {e}") 