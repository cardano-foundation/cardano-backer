from hio import doing
from keri.db import subing
from keri.core import serdering, eventing
from ... import cardaning


class Queueing(doing.Doer):

    def __init__(self, name='backer', hab=None):
        self.name = name
        self.hab = hab
        # TODO: pending_kel should change to array
        self.ledger = cardaning.Cardano(name=name, hab=hab)
        # sub-dbs
        self.keldb_queued = subing.SerderSuber(db=hab.db, subkey="kel_queued")
        self.keldb_published = subing.SerderSuber(db=hab.db, subkey="kel_published")
        self.tock = 10  # the job should run daily.

    def publish(self):
        """
        doer call run
            get from queued
                do publishEvent
            deleted from queued
            create in published
        """
        for (pre, said), serder in self.keldb_queued.getItemIter():
            event = eventing.loadEvent(self.hab.db, pre, serder.saidb)
            self.ledger.publishEvent(event=event)
            self.keldb_published.pin(keys=pre, val=serder)
            self.keldb_queued.rem(keys=pre)

    def recur(self, tyme=None):
        while True:
            self.publish()
            yield self.tock

    def push_to_queued(self, pre, msg):
        """
        push even to queued
        """
        serder = serdering.SerderKERI(raw=msg)
        self.keldb_queued.pin(keys=pre, val=serder)
