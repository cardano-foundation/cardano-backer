import os
from hio.base import doing
from keri import help
from keri.db import subing
from keri.core import serdering
from backer import cardaning

logger = help.ogler.getLogger()


class Queueing(doing.Doer):

    def __init__(self, name='backer', hab=None):
        self.name = name
        self.hab = hab
        # TODO: pending_kel should change to array
        self.ledger = cardaning.Cardano(name=name, hab=hab, ks=hab.ks)
        # sub-dbs
        self.keldb_queued = subing.SerderSuber(db=hab.db, subkey="kel_queued")
        self.keldb_published = subing.SerderSuber(db=hab.db, subkey="kel_published")
        self.tock = os.environ.get('QUEUE_DURATION', 30)  # the job should run daily.

    def publish(self):
        """
        doer call run
            get from queued
                do publishEvent
            create in published
            deleted from queued
        """        
        for (pre, _), serder in self.keldb_queued.getItemIter():
            try:
                self.ledger.publishEvent(event=serder.raw)
                keys = (pre, serder.said)
                self.keldb_published.pin(keys=keys, val=serder)
                self.keldb_queued.rem(keys=keys)
            except Exception as e:
                logger.error(str(e))
                continue

        self.ledger.flushQueue()


    def recur(self, tyme=None):
        while True:
            self.publish()
            yield self.tock

    def pushToQueued(self, pre, msg):
        """
        push even to queued
        """
        serder = serdering.SerderKERI(raw=msg)
        self.keldb_queued.pin(keys=(pre, serder.said), val=serder)
