# -*- encoding: utf-8 -*-
"""
Cardano Backer
backer.crawling module

Cardano crawler to ensure any on-chain transactions reliably appear over time
"""
import os
import ogmios
import ogmios.model.model_map as ogmm
import json
import datetime
from hio.base import doing
from keri import help
from backer.cardaning import TransactionType, PointRecord, CardanoKomerKey

logger = help.ogler.getLogger()

OGMIOS_HOST = os.environ.get('OGMIOS_HOST', 'localhost')
OGMIOS_PORT = int(os.environ.get('OGMIOS_PORT', 1337))
START_SLOT_NUMBER = int(os.environ.get('START_SLOT_NUMBER') or 0)
START_BLOCK_HEADER_HASH = os.environ.get('START_BLOCK_HEADER_HASH', "")


class Crawler(doing.Doer):

    def __init__(self, ledger, tock=0.0):
        self.ledger = ledger
        self.tock = tock
        super().__init__(tock=self.tock)

    def recur(self, tymth=None):
        startPoint = ogmios.Point(START_SLOT_NUMBER, START_BLOCK_HEADER_HASH) if START_SLOT_NUMBER > 0 else ogmios.Origin()
        lastBlock = self.ledger.states.get(CardanoKomerKey.CURRENT_SYNC_POINT.value)

        if lastBlock:
            startPoint = ogmios.Point(lastBlock.slot, lastBlock.id)

        _, _, _ = self.ledger.client.find_intersection.execute([startPoint])

        while True:
            nodeBlockHeight, _ = self.ledger.client.query_block_height.execute()
            if self.ledger.onTip and nodeBlockHeight == self.ledger.tipHeight:
                yield self.tock
                continue

            direction, tip, block, _ = self.ledger.client.next_block.execute()

            if block in [ogmios.Origin()] or isinstance(block, ogmios.Point) or block.blocktype == ogmm.Types.ebb.value:
                yield self.tock
                continue

            if direction == ogmios.Direction.forward:
                if tip.height:
                    self.ledger.updateTip(tip.height)

                if not self.ledger.onTip and block.height == tip.height:
                    logger.info(f"[{datetime.datetime.now()}] Reached tip at slot {block.slot}")
                    self.ledger.onTip = True
                    self.tock = 1.0

                # Find transactions involving cardano backer
                if isinstance(block, ogmios.Block) and hasattr(block, "transactions"):
                    logger.debug(f"[{datetime.datetime.now()}] {direction}:\nblock: {block}\ntip:{tip}\n")

                    for tx in block.transactions:
                        confirmingTx = self.ledger.getConfirmingTx(tx["id"])
                        if confirmingTx is not None:
                            tx = json.loads(confirmingTx)
                            tx["block_slot"] = block.slot
                            tx["block_height"] = block.height
                            self.ledger.updateConfirmingTxMetadata(tx, TransactionType(tx["type"]))
            else:
                # Rollback transactions, we receipt a Point instead of a Block in backward direction
                if isinstance(block, ogmios.Point):
                    logger.debug(f"[{datetime.datetime.now()}] {direction}:\nblock: {block}\ntip:{tip}\n")
                    self.ledger.updateTip(tip.height)
                    self.ledger.rollbackToSlot(block.slot, txType=TransactionType.KEL)
                    self.ledger.rollbackToSlot(block.slot, txType=TransactionType.SCHEMA)

            self.ledger.confirmOrTimeoutDeepTxs(TransactionType.KEL)
            self.ledger.confirmOrTimeoutDeepTxs(TransactionType.SCHEMA)

            self.ledger.states.pin(CardanoKomerKey.CURRENT_SYNC_POINT.value, PointRecord(id=block.id, slot=block.slot))

            yield self.tock
