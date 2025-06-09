# -*- encoding: utf-8 -*-
"""
Cardano Backer
backer.queueing module

Routinely publishes batches of each transaction type on-chain
"""
import os
from hio.base import doing
from keri import help
from backer.cardaning import Cardano, TransactionType

logger = help.ogler.getLogger()


class Queuer(doing.Doer):

    def __init__(self, ledger: Cardano):
        self.ledger = ledger
        self.tock = int(os.environ.get('QUEUE_DURATION', 10))
        super(Queuer, self).__init__(tock=self.tock)

    # @TODO - foconnor: If more than a tx-worth of events need to be written on-chain,
    #   those events will not appear until the next flush. This could be improved.
    #   Same goes if there is a failure - it won't auto-retry.
    def recur(self, tyme=None):
        while True:
            self.ledger.publishEvents(txType=TransactionType.KEL)
            self.ledger.publishEvents(txType=TransactionType.SCHEMA)

            yield self.tock
