import os
from hio.base import doing
from keri import help
from backer.cardaning import Cardano, CardanoType

logger = help.ogler.getLogger()


class Queuer(doing.Doer):

    def __init__(self, ledger: Cardano):
        self.ledger = ledger
        self.tock = int(os.environ.get('QUEUE_DURATION', 30))
        super(Queuer, self).__init__(tock=self.tock)

    def recur(self, tyme=None):
        while True:
            if self.ledger.onTip:
                self.ledger.publishEvents(type=CardanoType.KEL)
                self.ledger.publishEvents(type=CardanoType.SCHEMA)

            yield self.tock
