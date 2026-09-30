import os
import pytest
from pathlib import Path

# Ensure backend root is on sys.path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

@pytest.fixture(scope="session", autouse=True)
def setup_test_env():
    # Set testing environment variables
    os.environ["DEBUG"] = "True"
    os.environ["SIMILARITY_THRESHOLD"] = "0.15"
