import os
from hio.base import doing
from keri import help
from keri.db import subing
from keri.core import serdering, scheming
from backer.cardaning import Cardano, CardanoType

logger = help.ogler.getLogger()


class Queueing(doing.Doer):

    def __init__(self, hab, ledger: Cardano):
        self.hab = hab
        self.ledger = ledger
        self.tock = os.environ.get('QUEUE_DURATION', 30)  # the job should run daily.

    def recur(self, tyme=None):
        while True:
            self.ledger.publishEvents()
            yield self.tock

    def pushToQueued(self, pre, msg, type=CardanoType.KEL):
        """
        push even to queued
        """
        if type is CardanoType.SCHEMA:
            schemer = scheming.Schemer(raw=msg)
            self.ledger.schemadb_queued.pin(keys=(schemer.said, ), val=msg)
        else:
            serder = serdering.SerderKERI(raw=msg)
            self.ledger.keldb_queued.pin(keys=(pre, serder.said), val=msg)

