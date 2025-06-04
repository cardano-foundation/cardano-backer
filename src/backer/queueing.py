import os
from hio.base import doing
from keri import help
from keri.core import serdering, scheming
from backer.cardaning import Cardano, CardanoType

logger = help.ogler.getLogger()


class Queueing(doing.Doer):

    def __init__(self, hab, ledger: Cardano):
        self.hab = hab
        self.ledger = ledger
        self.tock = int(os.environ.get('QUEUE_DURATION', 30))  # the job should run daily.

    def recur(self, tyme=None):
        while True:
            if self.ledger.onTip:
                self.ledger.publishEvents(type=CardanoType.KEL)
                self.ledger.publishEvents(type=CardanoType.SCHEMA)

            yield self.tock

