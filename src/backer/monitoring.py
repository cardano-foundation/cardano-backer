# -*- encoding: utf-8 -*-
"""
Cardano Backer
backer.monitoring module

Monitor off-loads Cardano activity (which is blocking) to a separate thread and reliably handles failures
"""
import threading
import os
from keri import help
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
        self.doist = doing.Doist(limit=0.0, tock=0.03125, real=True)
        self.cleanupSignal = threading.Event()
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
        self.doist.exit()
        self.cleanupSignal.wait(timeout=5.0)  # Give Ogmios client a moment to gracefully cleanup

    def _startThread(self):
        def doCardano():
            try:
                with Client(OGMIOS_HOST, OGMIOS_PORT) as client:
                    ledger = cardaning.Cardano(hab=self.hab, client=client)
                    queuer = queueing.Queuer(ledger=ledger)
                    crawler = crawling.Crawler(ledger=ledger)
                    pruner = crawling.Pruner(ledger=ledger)

                    self.doist.do(doers=[crawler, queuer, pruner])
            except Exception as ex:
                logger.critical(f"Secondary controller encountered an error: {ex}", exc_info=True)
            finally:
                self.cleanupSignal.set()

        self.thread = threading.Thread(target=doCardano, daemon=True)
        self.thread.start()
