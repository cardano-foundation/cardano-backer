# -*- encoding: utf-8 -*-
"""
CARDANO-BACKER
backer.ogmiosing module

class to support subcribe tip from ogmios and cardano node
"""
import ogmios
from hio.base import doing
from keri import help
from ogmios.statequery import QueryNetworkTip

logger = help.ogler.getLogger()


class Ogmioser(doing.DoDoer):

    def __init__(self, on_tip=False, tip_slot=0, **kwa):
        self.on_tip = on_tip
        self.tip_slot = tip_slot
        doers = [doing.doify(self.queryTipDo), doing.doify(self.crawlBlockDo)]
        super(Ogmioser, self).__init__(doers=doers, **kwa)

    def crawlBlockDo(self, tymth=None, tock=0.0):
        self.wind(tymth)
        self.tock = tock
        _ = (yield self.tock)

        try:
            with ogmios.Client() as client:
                _, tip, _ = client.find_intersection.execute([ogmios.Origin()])
                _, _, _ = client.find_intersection.execute([tip.to_point()])

                while True:
                    direction, tip, point, _ = client.next_block.execute()
                    if direction and direction == ogmios.Direction.forward:
                        slot = point.slot

                        if self.tip_slot > 0 and self.tip_slot <= slot:
                            self.on_tip = True
                            logger.debug(
                                f"Reached tip {self.tip_slot} at slot {slot}")
                            return self.tock
                        else:
                            yield self.tock

                    yield self.tock
        except Exception as ex:
            logger.error(f"ERROR: {ex}")
            yield self.tock

        return self.tock

    def queryTipDo(self, tymth=None, tock=0.0):
        self.wind(tymth)
        self.tock = tock
        _ = (yield self.tock)

        try:
            with ogmios.Client() as client:
                query_network_tip = QueryNetworkTip(client)

                while not self.on_tip:
                    network_tip = query_network_tip.execute()
                    point = network_tip[0]
                    self.tip_slot = point.slot
                    yield self.tock
        except Exception as ex:
            yield self.tock
            logger.error(f"ERROR: {ex}")

        return self.tock
