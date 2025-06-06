import threading
import os
from keri import help
from keri.app import directing
from hio.base import doing
from ogmios.client import Client
from backer import cardaning, queueing, crawling

logger = help.ogler.getLogger()

OGMIOS_HOST = os.environ.get('OGMIOS_HOST', 'localhost')
OGMIOS_PORT = int(os.environ.get('OGMIOS_PORT', 1337))


class CardanoThreadMonitor(doing.Doer):
    """
    Doer that monitors the shared exception variable and restarts the secondary thread if needed.
    """
    def __init__(self, hab):
        self.hab = hab
        self.thread = None
        self.tock = 5.0
        super().__init__(tock=self.tock)

    def enter(self):
        self._startThread()

    def recur(self, tyme=None):
        while True:
            if not self.thread.is_alive():
                logger.critical(f"Restarting Cardano thread after error.")
                self._startThread()
            yield self.tock

    def exit(self):
        if self.thread:
            self.thread.join()

    def _startThread(self):
        def doCardano():
            try:
                with Client(OGMIOS_HOST, OGMIOS_PORT) as client:
                    ledger = cardaning.Cardano(hab=self.hab, client=client)
                    queuer = queueing.Queuer(ledger=ledger)
                    crawler = crawling.Crawler(ledger=ledger)

                    directing.runController(doers=[crawler, queuer], expire=0.0)
            except Exception as ex:
                logger.critical(f"Secondary controller encountered an error: {ex}")

        self.thread = threading.Thread(target=doCardano, daemon=True)
        self.thread.start()
