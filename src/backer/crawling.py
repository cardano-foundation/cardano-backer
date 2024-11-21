# -*- encoding: utf-8 -*-
"""
CARDANO-BACKER
backer.crawling module

class to support subcribe tip from ogmios and cardano node
"""
import ogmios
import json
from hio.base import doing
from keri import help

logger = help.ogler.getLogger()


class Crawler(doing.DoDoer):

    def __init__(self, backer, ledger, **kwa):
        self.client = ogmios.Client()
        self.backer = backer
        self.on_tip = False
        self.ledger = ledger
        doers = [doing.doify(self.crawlBlockDo), doing.doify(self.confirmTrans)]
        super(Crawler, self).__init__(doers=doers, **kwa)

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
                    if tip.height:
                        self.ledger.updateTip(tip.height)

                    if not self.on_tip and block.height == tip.height:
                        logger.info(f"Reached tip at slot {block.slot}")
                        self.on_tip = True
                        self.extend(self.backer)
                        self.tock = 1.0

                    # Find transactions involving cardano backer
                    if self.on_tip and isinstance(block, ogmios.Block) and hasattr(block, "transactions"):
                        for tx in block.transactions:
                            txId = tx['inputs'][0]['transaction']['id']
                            confirmingTrans = self.ledger.getConfirmingTrans(txId)
                            if confirmingTrans is not None:
                                trans = json.loads(trans)
                                trans["block_slot"] = block.slot
                                trans["block_height"] = block.height
                                self.ledger.updateTrans(trans)
                else:
                    # Rollback transactions, we receipt a Point instead of a Block in backward direction
                    if isinstance(block, ogmios.Point):
                        self.ledger.updateTip(tip.height)
                        self.ledger.rollbackBlock(block.slot)

                yield self.tock
        except Exception as ex:
            logger.error(f"ERROR: {ex}")

        yield self.tock

    def confirmTrans(self, tymth=None, tock=0.0):
        self.wind(tymth)
        self.tock = tock
        _ = (yield self.tock)

        while True:
            if self.on_tip and self.ledger:
                self.ledger.confirmTrans()

            yield self.tock
