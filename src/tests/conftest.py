import pytest
from tests.helper import DEVNET_PROCESS_PATH, DEVNET_OGMIOS_PORT, is_process_running


def pytest_sessionstart(session):
    """Skip all tests if Ogmios is not running"""
    if not is_process_running(DEVNET_PROCESS_PATH, DEVNET_OGMIOS_PORT):
        pytest.fail("❌ The devnet could not be reached. Have you started it?", pytrace=False)
