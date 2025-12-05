import pytest
import sys
import os

# Add src to python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

def test_imports():
    """
    Simple smoke test to verify that key modules can be imported.
    This ensures that there are no syntax errors or missing dependencies 
    that would prevent the application from starting.
    """
    try:
        from utils import file_utils
        from utils import translations
    except ImportError as e:
        pytest.fail(f"Failed to import modules: {e}")
