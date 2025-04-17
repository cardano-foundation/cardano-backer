import os
import time
import subprocess
import shutil
import socket
import falcon

from pathlib import Path
from falcon.testing import TestClient
from keri import help
from keri.app import habbing, keeping
from backer import cardaning, queueing
from keri.app.cli.common import existing

logger = help.ogler.getLogger()

BACKER_SALT = "0ACDEyMzQ1Njc4OWxtbm9aBc"
BACKER_TEST_STORE_DIR = "tests/store"
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

def set_test_env():
    os.environ["BACKER_SALT"] = BACKER_SALT
    os.environ["BACKER_PORT"] = str(BACKER_TEST_PORT)
    os.environ["BACKER_TPORT"] = str(BACKER_TEST_TPORT)
    os.environ["BACKER_STORE_DIR"] = BACKER_TEST_STORE_DIR
    os.environ["WALLET_ADDRESS_CBORHEX"] = WALLET_ADDRESS_CBORHEX

class TestEnd:
    def make_test_end(self, route, endclass, cues=None):
        set_test_env()
        name = "testbacker"
        bran = ""
        alias = "testbacker"
        ks = keeping.Keeper(name=name,
                        base=BACKER_TEST_STORE_DIR,
                        temp=True,
                        reopen=True)
        aeid = ks.gbls.get('aeid')

        if aeid is None:
            hby = habbing.Habery(name=name, base=BACKER_TEST_STORE_DIR, bran=bran)
        else:
            hby = existing.setupHby(name=name, base=BACKER_TEST_STORE_DIR, bran=bran)

        hab = hby.habByName(name=alias)
        if hab is None:
            hab = hby.makeHab(name=alias, transferable=False)

        ledger = cardaning.Cardano(hab=hab, ks=hab.ks)
        queue = queueing.Queueing(hab=hab, ledger=ledger)

        app = falcon.App()
        client = TestClient(app)

        if cues:
            endResource = endclass(hab=hab, queue=queue, cues=cues)
        else:
            endResource = endclass(hab=hab, queue=queue)

        app.add_route(route, endResource)

        return hby, hab, client, ledger

class TestBase:
    @classmethod
    def setup_class(cls):
        set_test_env()

    @classmethod
    def teardown_class(cls):
        # Remove test data
        if os.path.exists(BACKER_TEST_STORE_DIR):
            shutil.rmtree(BACKER_TEST_STORE_DIR)

        # Expand user home and define paths
        paths = [
            Path("~/.keri/db/tests").expanduser(),
            Path("~/.keri/cf/tests").expanduser(),
            Path("~/.keri/ks/tests").expanduser()
        ]

        # Remove each directory if it exists
        for path in paths:
            if path.exists() and path.is_dir():
                shutil.rmtree(path)
