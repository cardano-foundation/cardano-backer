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
START_SERVICE_TIMEOUT = 30
YACI_CLI_SCRIPT = "yaci-cli"
START_DEVNET_SCRIPT = "start-devnet.sh"
YACI_DOWNLOAD_SCRIPT = "download.sh"
STOP_DEVNET_SCRIPT = "stop-devnet.sh"
START_BACKER_SCRIPT = "start_backer.sh"

def is_process_running(proc_name):
    """Check if a process with the given name is running using `pgrep` (Linux/macOS)."""
    try:
        result = subprocess.run(["pgrep", "-x", proc_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return result.returncode == 0  # `pgrep` returns 0 if process is found
    except FileNotFoundError:
        return False

def wait_for_port(port, host="0.0.0.0", timeout=START_SERVICE_TIMEOUT, check_interval=2):
    start_time = time.time()

    while time.time() - start_time < timeout:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            result = s.connect_ex((host, port))
            if result == 0:
                print(f"Port {port} is now LISTENING.")
                return True
        print(f"Waiting for port {port} to be available...")
        time.sleep(check_interval)

    print(f"Timeout: Port {port} is still not available after {timeout} seconds.")
    return False

class YaciDevnet:
    def __init__(self, dir_path=None):
        if dir_path:
            self.dir_path = dir_path
        else:
            self.dir_path = os.path.abspath(os.path.join(__file__, os.pardir, os.pardir, os.pardir, YACI_CLI_SCRIPT))

        self.download_components_path = os.path.abspath(os.path.join(self.dir_path, YACI_DOWNLOAD_SCRIPT))
        self.start_devnet_path = os.path.abspath(os.path.join(self.dir_path, START_DEVNET_SCRIPT))
        self.stop_devnet_path = os.path.abspath(os.path.join(self.dir_path, STOP_DEVNET_SCRIPT))

    def download_components(self):
        try:
            subprocess.run(["bash", self.download_components_path], check=True)
        except subprocess.CalledProcessError as e:
            logger.critical("Download components failed:\n", e)

    def start_devnet(self):
        """Start the script in the background"""

        process_check = "start-devnet"

        if is_process_running(process_check):
            self.stop_devnet()  # Stop the devnet if it's already running
            time.sleep(2)  # Wait for the devnet to stop

        try:
            self.download_components()
            self.process = subprocess.Popen(["bash", self.start_devnet_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            wait_for_port(DEVNET_OGMIOS_PORT)  # Wait for the devnet to start listening
            logger.info(f"Yaci cli started in background with PID: {self.process.pid}")
        except Exception as e:
            logger.critical("Start devnet failed:\n%s", e)

    def stop_devnet(self):
        """Stop the devnet"""
        try:
            self.process = subprocess.Popen(["bash", self.stop_devnet_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            logger.info(f"Script started in background with PID: {self.process.pid}")
            time.sleep(1)
            logger.info("Devnet stopped")
        except Exception as e:
            logger.critical("Stop devnet failed:\n%s", e)

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

        if is_process_running("bin/backer"):
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

class DevnetBase:
    @classmethod
    def setup_class(cls):
        cls.yaci_devnet = YaciDevnet()
        cls.mock_backer = MockBacker()

        cls.yaci_devnet.start_devnet()
        time.sleep(1)
        cls.mock_backer.start_backer()

    @classmethod
    def teardown_class(cls):
        cls.mock_backer.stop_backer()

        # Remove test data
        if os.path.exists(BACKER_TEST_STORE_DIR):
            shutil.rmtree(BACKER_TEST_STORE_DIR)

        cls.yaci_devnet.stop_devnet()

