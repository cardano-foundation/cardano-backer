# -*- encoding: utf-8 -*-
"""
CARDANO-BACKER
backer.crawling module

class to support subcribe tip from ogmios and cardano node
"""
import os
import ogmios
import ogmios.model.model_map as ogmm
import json
import datetime
from hio.base import doing
from keri import help
from websockets import ConnectionClosedError

from backer.cardaning import CardanoType, PointRecord, CURRENT_SYNC_POINT


logger = help.ogler.getLogger()
OGMIOS_HOST = os.environ.get('OGMIOS_HOST', 'localhost')
OGMIOS_PORT = os.environ.get('OGMIOS_PORT', 1337)
START_SLOT_NUMBER = int(os.environ.get('START_SLOT_NUMBER') or 0)
START_BLOCK_HEADER_HASH = os.environ.get('START_BLOCK_HEADER_HASH', "")

class Crawler(doing.DoDoer):

    def __init__(self, ledger, **kwa):
        self.client = ogmios.Client(host=OGMIOS_HOST, port=OGMIOS_PORT)
        self.ledger = ledger
        doers = [doing.doify(self.crawlBlockDo), doing.doify(self.confirmTrans)]
        super(Crawler, self).__init__(doers=doers, **kwa)

    def crawlBlockDo(self, tymth=None, tock=0.0):
        self.wind(tymth)
        self.tock = tock
        _ = (yield self.tock)

        startPoint = ogmios.Point(START_SLOT_NUMBER, START_BLOCK_HEADER_HASH) if START_SLOT_NUMBER > 0 else ogmios.Origin()
        lastBlock = self.ledger.states.get(CURRENT_SYNC_POINT)

        if lastBlock:
            startPoint = ogmios.Point(lastBlock.slot, lastBlock.id)

        _, _, _ = self.client.find_intersection.execute([startPoint])

        while True:
            try:
                # @TODO - focnnor: datetime can be globally set for as a logger prefix
                logger.debug(f"[{datetime.datetime.now()}] Requesting nodeBlockHeight from ogmios...")
                nodeBlockHeight, _ = self.client.query_block_height.execute()
                logger.debug(f"[{datetime.datetime.now()}] Retrieved nodeBlockHeight: {nodeBlockHeight} [current tipHeight: {self.ledger.tipHeight}] [onTip: {self.ledger.onTip}]")

                if self.ledger.onTip and nodeBlockHeight == self.ledger.tipHeight:
                    yield tock
                    continue

                direction, tip, block, _ = self.client.next_block.execute()

                if block in [ogmios.Origin()] or isinstance(block, ogmios.Point) or block.blocktype == ogmm.Types.ebb.value:
                    yield tock
                    continue

                if direction == ogmios.Direction.forward:
                    if tip.height:
                        self.ledger.updateTip(tip.height)

                    if not self.ledger.onTip and block.height == tip.height:
                        logger.info(f"[{datetime.datetime.now()}] Reached tip at slot {block.slot}")
                        self.ledger.onTip = True
                        tock = 1.0

                    # Find transactions involving cardano backer
                    if isinstance(block, ogmios.Block) and hasattr(block, "transactions"):
                        logger.debug(f"[{datetime.datetime.now()}] {direction}:\nblock: {block}\ntip:{tip}\n")

                        for tx in block.transactions:
                            txId = tx['id']
                            confirmingTrans = self.ledger.getConfirmingTrans(txId)
                            if confirmingTrans is not None:
                                trans = json.loads(confirmingTrans)
                                trans["block_slot"] = block.slot
                                trans["block_height"] = block.height
                                item_type = CardanoType(trans["type"])
                                self.ledger.updateTrans(trans, item_type)
                else:
                    # Rollback transactions, we receipt a Point instead of a Block in backward direction
                    if isinstance(block, ogmios.Point):
                        logger.debug(f"[{datetime.datetime.now()}] {direction}:\nblock: {block}\ntip:{tip}\n")
                        self.ledger.updateTip(tip.height)
                        self.ledger.rollbackBlock(block.slot, type=CardanoType.KEL)
                        self.ledger.rollbackBlock(block.slot, type=CardanoType.SCHEMA)

                self.ledger.states.pin(CURRENT_SYNC_POINT, PointRecord(id=block.id, slot=block.slot))
            except (ConnectionClosedError, EOFError) as ex:
                logger.critical(f"[{datetime.datetime.now()}] Reconnect to ogmios ...")
                try:
                    self.client = ogmios.Client(host=OGMIOS_HOST, port=OGMIOS_PORT)
                    _, _, _ = self.client.find_intersection.execute([tip.to_point()])
                    tock = 0.0
                except Exception as ex:
                    logger.critical(f"[{datetime.datetime.now()}] Failed to reconnect to ogmios: {ex}")

            yield tock

    def confirmTrans(self, tymth=None, tock=0.0):
        self.wind(tymth)
        self.tock = tock
        _ = (yield self.tock)

        while True:
            if self.ledger:
                self.ledger.confirmTrans(CardanoType.KEL)
                self.ledger.confirmTrans(CardanoType.SCHEMA)

            yield self.tock
