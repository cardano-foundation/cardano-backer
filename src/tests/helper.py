import os
import time
import subprocess
import shutil
import socket

from keri import help

logger = help.ogler.getLogger()

BACKER_SALT = "0ACDEyMzQ1Njc4OWxtbm9aBc"
BACKER_TEST_STORE_DIR = os.path.abspath(os.path.join(__file__, os.pardir, os.pardir, os.pardir, "tests", "store"))
BACKER_TEST_PORT = 5668
BACKER_TEST_TPORT = 5667
WALLET_ADDRESS_CBORHEX = "5820339f8d1757c2c19ba62146d98400be157cdbbe149a4200bd9cc68ef457c201f8"

DEVNET_OGMIOS_PORT = 1337
DEVNET_PROCESS_PATH = ".yaci-cli/components/ogmios/bin/ogmios"
START_SERVICE_TIMEOUT = 30
START_BACKER_SCRIPT = "start_backer.sh"


def is_process_running(proc_path, proc_port):
    """Check if the process is running and includes the expected port argument"""
    try:
        # Get process details (works on Linux & macOS)
        cmd = ["ps", "-eo", "pid,comm,args"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        output = result.stdout.strip()

        proc_port_arg = f"--port {proc_port}"

        for line in output.split("\n"):
            if proc_path in line and proc_port_arg in line:
                return True  # Process is running and has the correct port argument

        return False  # Process is not running or wrong port

    except Exception as e:
        logger.critical(f"Error: {e}")
        return False


def wait_for_port(port, host="0.0.0.0", timeout=START_SERVICE_TIMEOUT, check_interval=2):
    start_time = time.time()

    while time.time() - start_time < timeout:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            result = s.connect_ex((host, port))
            if result == 0:
                logger.info(f"Port {port} is now LISTENING.")
                return True
        logger.info(f"Waiting for port {port} to be available...")
        time.sleep(check_interval)

    logger.info(f"Timeout: Port {port} is still not available after {timeout} seconds.")
    return False


class MockBacker:
    def __init__(self, dir_path=None):
        self.set_test_env()

        if dir_path:
            self.dir_path = dir_path
        else:
            self.dir_path = os.path.abspath(os.path.join(__file__, os.pardir, os.pardir, os.pardir, "scripts"))

        self.start_backer_path = os.path.abspath(os.path.join(self.dir_path, START_BACKER_SCRIPT))

    def set_test_env(self):
        os.environ["BACKER_SALT"] = BACKER_SALT
        os.environ["BACKER_PORT"] = str(BACKER_TEST_PORT)
        os.environ["BACKER_TPORT"] = str(BACKER_TEST_TPORT)
        os.environ["BACKER_STORE_DIR"] = BACKER_TEST_STORE_DIR
        os.environ["WALLET_ADDRESS_CBORHEX"] = WALLET_ADDRESS_CBORHEX

    def start_backer(self):
        """Start the script in the background"""

        if is_process_running("bin/backer", BACKER_TEST_PORT):
            self.stop_backer()  # Stop the backer if it's already running
            time.sleep(1)

        try:
            self.process = subprocess.Popen(["bash", self.start_backer_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            wait_for_port(BACKER_TEST_PORT)  # Wait for the backer to start listening
            logger.info(f"Backer started in background with PID: {self.process.pid}")
        except Exception as e:
            logger.critical("Start backer failed:\n%s", e)

    def stop_backer(self):
        """Stop the backer"""
        try:
            subprocess.run("pkill -f 'bin/backer.*start|.*backer.*/bin/sh'", shell=True)
            time.sleep(1)
            logger.info("Backer stopped")
        except Exception as e:
            logger.critical("Stop backer failed:\n%s", e)

class TestBase:
    @classmethod
    def setup_class(cls):
        cls.mock_backer = MockBacker()
        cls.mock_backer.start_backer()

    @classmethod
    def teardown_class(cls):
        cls.mock_backer.stop_backer()

        # Remove test data
        if os.path.exists(BACKER_TEST_STORE_DIR):
            shutil.rmtree(BACKER_TEST_STORE_DIR)

