import threading
from keri import help
from keri.app import directing
from hio.base import doing


class SecondaryThreadMonitorer(doing.Doer):
    """
    Doer that monitors the shared exception variable and restarts the secondary thread if needed.
    """
    def __init__(self, crl, queuer, secondaryControllerStop, logger):
        self.crl = crl
        self.queuer = queuer
        self.secondaryControllerStop = secondaryControllerStop
        self.exceptionContainer = []
        self.logger = logger
        self.doer_thread = None
        self.tock = 1.0
        super().__init__(tock=self.tock)

    def start_secondary(self):
        restart = True if self.exceptionContainer else False
        self.secondaryControllerStop.clear()
        self.exceptionContainer.clear()
        self.doer_thread = self.runSecondaryController(
            [self.crl, self.queuer],
            self.secondaryControllerStop,
            self.logger,
            restart=restart
        )

    def recur(self, tyme=None):
        # Start the secondary thread on first run
        if self.doer_thread is None:
            self.start_secondary()

        while True:
            if self.exceptionContainer:
                self.logger.critical(f"Restarting secondary controller due to exception: {self.exceptionContainer[-1]}")
                self.doer_thread.join()
                self.start_secondary()
            yield self.tock

    def close(self):
        if self.doer_thread:
            self.secondaryControllerStop.set()
            self.doer_thread.join()

    def runSecondaryController(self, doers, secondaryControllerStop, logger=help.ogler.getLogger(), restart=False):
        """
        Run all doers (e.g., from Crawler and Queueing) in a dedicated thread using a separate directing.runController.
        All ogmios requests and queueing will happen in this thread.
        """
        def doerController():
            try:
                if restart:
                    self.crl.reconnectOgmios()

                directing.runController(doers=doers, expire=0.0)
            except Exception as ex:
                logger.critical(f"Secondary controller encountered an error: {ex}")
                self.exceptionContainer.append(ex)
            finally:
                secondaryControllerStop.set()

        thread = threading.Thread(target=doerController, daemon=True)
        thread.start()
        return thread
