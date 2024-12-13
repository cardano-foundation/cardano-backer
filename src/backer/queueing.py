import os
from hio.base import doing
from keri import help
from keri.db import subing
from keri.core import serdering
from backer import cardaning

logger = help.ogler.getLogger()


class Queueing(doing.Doer):

    def __init__(self, hab, ledger):
        self.hab = hab
        self.ledger = ledger
        self.tock = os.environ.get('QUEUE_DURATION', 30)  # the job should run daily.

    def recur(self, tyme=None):
        while True:
            self.ledger.publishEvents()
            yield self.tock

    def pushToQueued(self, pre, msg):
        """
        push even to queued
        """
        serder = serdering.SerderKERI(raw=msg)
        self.ledger.keldb_queued.pin(keys=(pre, serder.said), val=serder)
