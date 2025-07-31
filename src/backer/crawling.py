# -*- encoding: utf-8 -*-
"""
Cardano Backer
backer.crawling module

Cardano crawler to ensure any on-chain transactions reliably appear over time
"""
import os
import re
import ogmios
import ogmios.model.model_map as ogmm
import json
import datetime
from hio.base import doing
from keri import help
from backer.cardaning import TransactionType, PointRecord, CardanoKomerKey, Cardano

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

        if (remainingPoints := self.ledger.states.cnt(CardanoKomerKey.CURRENT_SYNC_POINTS.value)) > 0:
            while remainingPoints > 0:
                remainingPoints -= 1
                lastItem = self.ledger.states.getLast(CardanoKomerKey.CURRENT_SYNC_POINTS.value)
                checkPoint = ogmios.Point(lastItem.slot, lastItem.id)

                try:
                    block, tip, _ = self.ledger.client.find_intersection.execute([checkPoint])
                    break
                except ogmios.errors.ResponseError as ex:
                    logger.critical(f"[{datetime.datetime.now()}] Error finding intersection from point: {checkPoint}, error: {ex}")
                    if re.search(r'["\']code["\']\s*:\s*1000', str(ex)):
                        # Remove the last item to continue from the last known point
                        self.ledger.states.rem(CardanoKomerKey.CURRENT_SYNC_POINTS.value, lastItem)
                    else:
                        raise ex
        else:
            _, _, _ = self.ledger.client.find_intersection.execute([startPoint])

        while True:
            nodeBlockHeight, _ = self.ledger.client.query_block_height.execute()
            if self.ledger.onTip and nodeBlockHeight == self.ledger.tipHeight:
                yield self.tock
                continue

            direction, tip, block, _ = self.ledger.client.next_block.execute()

            if block in [ogmios.Origin()] or (isinstance(block, ogmios.Block) and block.blocktype == ogmm.Types.ebb.value):
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
                    logger.debug(f"[{datetime.datetime.now()}] \n#####{direction}:#####\nblock: {block}\ntip:{tip}\n")
                    self.tock = 0.0
                    self.ledger.onTip = False
                    self.ledger.updateTip(tip.height)
                    self.ledger.rollbackToSlot(block.slot, txType=TransactionType.KEL)
                    self.ledger.rollbackToSlot(block.slot, txType=TransactionType.SCHEMA)

            self.ledger.confirmOrTimeoutDeepTxs(TransactionType.KEL)
            self.ledger.confirmOrTimeoutDeepTxs(TransactionType.SCHEMA)
            self.ledger.states.add(CardanoKomerKey.CURRENT_SYNC_POINTS.value, PointRecord(id=block.id, slot=block.slot))

            yield self.tock

POINT_RECORD_LIMIT = int(os.environ.get('POINT_RECORD_LIMIT', 2160))
class Pruner(doing.Doer):

    def __init__(self, ledger: Cardano, tock=10.0):
        self.ledger = ledger
        self.tock = tock
        super(Pruner, self).__init__(tock=self.tock)

    def recur(self, tyme=None):
        while True:
            while self.ledger.states.cnt(CardanoKomerKey.CURRENT_SYNC_POINTS.value) > POINT_RECORD_LIMIT:
                iter = self.ledger.states.getIter(CardanoKomerKey.CURRENT_SYNC_POINTS.value)
                removingItem = next(iter)
                self.ledger.states.rem(CardanoKomerKey.CURRENT_SYNC_POINTS.value, removingItem)

            yield self.tock
