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
from hio.base import doing
from keri import help
from websockets import ConnectionClosedError
import threading
import queue

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
        self._block_queue = queue.Queue(maxsize=1)
        self._fetch_thread = None
        self._stop_fetch = threading.Event()
        doers = [doing.doify(self.crawlBlockDo), doing.doify(self.confirmTrans)]
        super(Crawler, self).__init__(doers=doers, always=True, **kwa)

    def _fetch_next_block(self):
        while not self._stop_fetch.is_set():
            try:
                result = self.client.next_block.execute()
                self._block_queue.put(result)
            except Exception as e:
                logger.error(f"Error fetching next block: {e}")
                self._block_queue.put(None)
            break  # fetch one block per thread run

    def crawlBlockDo(self, tymth=None, tock=0.0):
        self.wind(tymth)
        self.tock = tock
        _ = (yield self.tock)

        startPoint = ogmios.Point(START_SLOT_NUMBER, START_BLOCK_HEADER_HASH) if START_SLOT_NUMBER > 0 else ogmios.Origin()
        lastBlock = self.ledger.states.get(CURRENT_SYNC_POINT)

        if lastBlock:
            startPoint = ogmios.Point(lastBlock.slot, lastBlock.id)

        _, _, _ = self.client.find_intersection.execute([startPoint])

        self._stop_fetch.clear()
        self._fetch_thread = None

        while True:
            try:
                # Start fetch thread if not running and queue is empty
                if self._fetch_thread is None or not self._fetch_thread.is_alive():
                    if self._block_queue.empty():
                        self._fetch_thread = threading.Thread(target=self._fetch_next_block)
                        self._fetch_thread.daemon = True
                        self._fetch_thread.start()

                # Try to get block result without blocking
                try:
                    result = self._block_queue.get_nowait()
                except queue.Empty:
                    yield self.tock
                    continue

                if result is None:
                    yield self.tock
                    continue

                direction, tip, block, _ = result

                if block in [ogmios.Origin()] or isinstance(block, ogmios.Point) or block.blocktype == ogmm.Types.ebb.value or (lastBlock and block == lastBlock):
                    yield self.tock
                    continue

                if not self.ledger.onTip:
                    logger.debug(f"Not reached tip yet. Current Point({block}) with {tip}")

                if direction == ogmios.Direction.forward:
                    if tip.height:
                        self.ledger.updateTip(tip.height)

                    if not self.ledger.onTip and block.height == tip.height:
                        logger.info(f"Reached tip at slot {block.slot}")
                        self.ledger.onTip = True
                        tock = 1.0

                    # Find transactions involving cardano backer
                    if isinstance(block, ogmios.Block) and hasattr(block, "transactions"):
                        logger.debug(f"{direction}:\nblock: {block}\ntip:{tip}\n")

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
                        logger.debug(f"{direction}:\nblock: {block}\ntip:{tip}\n")
                        self.ledger.updateTip(tip.height)
                        self.ledger.rollbackBlock(block.slot, type=CardanoType.KEL)
                        self.ledger.rollbackBlock(block.slot, type=CardanoType.SCHEMA)

                self.ledger.states.pin(CURRENT_SYNC_POINT, PointRecord(id=block.id, slot=block.slot))
            except (ConnectionClosedError, EOFError) as ex:
                logger.critical("Reconnect to ogmios ...")
                try:
                    self.client = ogmios.Client(host=OGMIOS_HOST, port=OGMIOS_PORT)
                    _, _, _ = self.client.find_intersection.execute([tip.to_point()])
                    tock = 0.0
                except Exception as ex:
                    logger.critical(f"Failed to reconnect to ogmios: {ex}")

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

    def close(self):
        self._stop_fetch.set()
        if self._fetch_thread and self._fetch_thread.is_alive():
            self._fetch_thread.join()

