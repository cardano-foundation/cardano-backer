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

    def __init__(self, on_tip=False, backer=None, **kwa):
        self.client = ogmios.Client()
        self.backer = backer
        self.on_tip = on_tip
        doers = [doing.doify(self.crawlBlockDo)]
        super(Ogmioser, self).__init__(doers=doers, **kwa)

    def crawlBlockDo(self, tymth=None, tock=0.0):
        self.wind(tymth)
        self.tock = tock
        _ = (yield self.tock)

        try:
            _, tip, _ = self.client.find_intersection.execute(
                [ogmios.Origin()])
            _, _, _ = self.client.find_intersection.execute([tip.to_point()])

            while True:
                direction, tip, block, _ = self.client.next_block.execute()

                if direction == ogmios.Direction.forward:
                    if not self.on_tip and block.height == tip.height:
                        logger.info(f"Reached tip at slot {block.slot}")
                        self.on_tip = True
                        self.extend(self.backer)
                        self.tock = 1.0
                else:
                    # TODO: Handle for backward
                    logger.debug("Backward direction")

                yield self.tock
        except Exception as ex:
            logger.error(f"ERROR: {ex}")

        yield self.tock
