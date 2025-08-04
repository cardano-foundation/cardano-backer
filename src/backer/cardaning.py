# -*- encoding: utf-8 -*-
"""
Cardano Backer
backer.cardaning module

Cardano specific helper class for writing KELs or schemas on-chain reliably using Ogmios
"""
from enum import Enum
import json
import pycardano
import os
from dataclasses import dataclass
from keri import help
from keri.db import subing, koming
from keri.core import serdering, scheming
from backer.constants import METADATUM_LABEL_KEL, METADATUM_LABEL_SCHEMA
from backer.persistentogmiosing import PersistentOgmiosV6ChainContext

logger = help.ogler.getLogger()

NETWORK = pycardano.Network.MAINNET if os.environ.get('NETWORK') == 'mainnet' else pycardano.Network.TESTNET
TRANSACTION_SECURITY_DEPTH = int(os.environ.get('TRANSACTION_SECURITY_DEPTH', 16))
TRANSACTION_TIMEOUT_DEPTH = int(os.environ.get('TRANSACTION_TIMEOUT_DEPTH', 32))
MAX_TRANSACTION_SIZE = 16384
MAX_TRANSACTION_SIZE_MARGIN = 3  # Can be small variations in tx size between PyCardano and Ogmios serialization


class TransactionType(Enum):
    SCHEMA = "CARDANO_SCHEMA"
    KEL = "CARDANO_KEL"


class CardanoSuberKey(Enum):
    KELS_QUEUED = "kels_queued"
    KELS_PUBLISHED = "kels_published"
    KELS_CONFIRMING = "kels_confirming"
    SCHEMAS_QUEUED = "schemas_queued"
    SCHEMAS_PUBLISHED = "schemas_published"
    SCHEMAS_CONFIRMING = "schemas_confirming"
    CONFIRMING_UTXOS = "confirming_utxo"


class CardanoKomerKey(Enum):
    BACKER_STATE_DB = 'bstt.'
    CURRENT_SYNC_POINTS = 'bsc.'


@dataclass
class PointRecord:
    id: str 
    slot: int


class Cardano:

    def __init__(self, hab, client):
        self.hab = hab
        self.client = client

        self.onTip = False
        self.tipHeight = 0

        # @TODO - foconnor: Most of this class should be subclassed into KELs and schemas
        #   to avoid the if else statements everywhere.
        self.kelsQueued = subing.Suber(db=hab.db, subkey=CardanoSuberKey.KELS_QUEUED.value)
        self.kelsPublished = subing.Suber(db=hab.db, subkey=CardanoSuberKey.KELS_PUBLISHED.value)
        self.kelsConfirming = subing.Suber(db=hab.db, subkey=CardanoSuberKey.KELS_CONFIRMING.value)

        self.schemasQueued = subing.Suber(db=hab.db, subkey=CardanoSuberKey.SCHEMAS_QUEUED.value)
        self.schemasPublished = subing.Suber(db=hab.db, subkey=CardanoSuberKey.SCHEMAS_PUBLISHED.value)
        self.schemasConfirming = subing.Suber(db=hab.db, subkey=CardanoSuberKey.SCHEMAS_CONFIRMING.value)

        self.dbConfirmingUtxos = subing.DupSuber(db=hab.db, subkey=CardanoSuberKey.CONFIRMING_UTXOS.value)

        self.states = koming.IoSetKomer(db=hab.db,
                                   schema=PointRecord,
                                   subkey=CardanoKomerKey.BACKER_STATE_DB.value)

        # Host/port both not needed as client is passed through
        # Better to keep as dummy strings to make it obvious when new functions are being used and need to be overridden
        self.context = PersistentOgmiosV6ChainContext(
            client=self.client,
            host="dummyhost",
            port="dummyport",
            network=NETWORK
        )

        self.paymentSigningKey = pycardano.PaymentSigningKey.from_cbor(os.environ.get('WALLET_ADDRESS_CBORHEX'))
        paymentVerificationKey = pycardano.PaymentVerificationKey.from_signing_key(self.paymentSigningKey)
        self.spending_addr = pycardano.Address(paymentVerificationKey.hash(), None, network=NETWORK)
        logger.info(f"Cardano Backer Spending Address: {self.spending_addr.encode()}")

    def updateTip(self, tipHeight):
        self.tipHeight = tipHeight

    def _addToQueue(self, event, txType: TransactionType):
        if txType == TransactionType.SCHEMA:
            schemer = scheming.Schemer(raw=event)
            self.schemasQueued.pin(keys=(schemer.said,), val=event)
        else:
            serder = serdering.SerderKERI(raw=event)
            self.kelsQueued.pin(keys=(serder.pre, serder.said), val=event)

    def _removeFromQueue(self, event, txType: TransactionType):
        if txType == TransactionType.SCHEMA:
            schemer = scheming.Schemer(raw=event)
            self.schemasQueued.rem(keys=(schemer.said,))
        else:
            serder = serdering.SerderKERI(raw=event)
            self.kelsQueued.rem(keys=(serder.pre, serder.said))

    def _addToPublished(self, event, txType: TransactionType):
        if txType == TransactionType.SCHEMA:
            schemer = scheming.Schemer(raw=event)
            self.schemasPublished.pin(keys=(schemer.said,), val=event)
        else:
            serder = serdering.SerderKERI(raw=event)
            self.kelsPublished.pin(keys=(serder.pre, serder.said), val=event)

    def selectAvailableUTXOs(self):
        def txIsConfirming(utxo):
            utxoId = f"{utxo.input.transaction_id}#{utxo.input.index}"
            for _, confirmingUtxoId in self.dbConfirmingUtxos.getItemIter():
                if confirmingUtxoId == utxoId:
                    return True

            return False

        availableUTXOs = []
        utxos = self.context.utxos(self.spending_addr)

        for utxo in utxos:
            if not txIsConfirming(utxo):
                availableUTXOs.append(utxo)

        return availableUTXOs

    def publishEvents(self, txType: TransactionType):
        if not self.onTip:
            return

        queue = self.kelsQueued if txType == TransactionType.KEL else self.schemasQueued
        confirmingTxs = self.kelsConfirming if txType == TransactionType.KEL else self.schemasConfirming

        # Skip setup nothing queued
        if self.hab.db.cnt(queue.sdb) < 1:
            return

        utxos = self.selectAvailableUTXOs()
        if len(utxos) < 1:
            logger.critical("ERROR: No UTXO available")
            return

        metadataLabel = METADATUM_LABEL_KEL if txType == TransactionType.KEL else METADATUM_LABEL_SCHEMA
        metadataBody = bytearray()

        eventsInBatch = []
        signedTx = None

        for _, event in reversed(list(queue.getItemIter())):
            metadataBody += event.encode('utf-8')

            # Chunk size - bytearrays is not accept
            metadataBodyBytes = bytes(metadataBody)
            value = [metadataBodyBytes[i:i + 64] for i in range(0, len(metadataBodyBytes), 64)]

            builder = pycardano.TransactionBuilder(self.context)
            for utxo in utxos:
                builder.add_input(utxo)
            builder.add_output(pycardano.TransactionOutput(self.spending_addr, pycardano.Value.from_primitive([1000000])))

            # Metadata accept int key type
            builder.auxiliary_data = pycardano.AuxiliaryData(pycardano.Metadata({metadataLabel: value}))
            try:
                signedTx = builder.build_and_sign([self.paymentSigningKey],
                                                  change_address=self.spending_addr,
                                                  merge_change=True)

                if len(signedTx.to_cbor()) > MAX_TRANSACTION_SIZE - MAX_TRANSACTION_SIZE_MARGIN:
                    break

                eventsInBatch.append(event)
            except pycardano.exception.InvalidTransactionException as e:
                if "exceeds the max limit" in str(e):
                    break
                else:
                    raise e

        if not signedTx:
            return

        signedTxMetadata = {
            "id": str(signedTx.id),
            "type": txType.value,
            "batch": eventsInBatch,
            "tip": self.tipHeight,
        }
        utxoIds = [f"{str(utxo.input.transaction_id)}#{utxo.input.index}" for utxo in utxos]

        confirmingTxs.pin(keys=signedTxMetadata["id"], val=json.dumps(signedTxMetadata).encode('utf-8'))
        self.dbConfirmingUtxos.pin(keys=signedTxMetadata["id"], vals=utxoIds)

        # Submit transaction
        try:
            self.context.submit_tx_cbor(bytes(signedTx.to_cbor()))
            logger.info(f"Submitted tx: {signedTxMetadata}")
        except Exception as e:
            logger.critical(f"ERROR: Submit tx: {e}")

            # Remove from confirming
            self.dbConfirmingUtxos.rem(keys=signedTxMetadata["id"])
            confirmingTxs.rem(signedTxMetadata["id"])
            return

        # Mark submitted events as published and remove from queue
        for event in eventsInBatch:
            event = event.encode('utf-8')
            self._addToPublished(event, txType)
            self._removeFromQueue(event, txType)

    def getConfirmingTx(self, txId):
        return self.kelsConfirming.get(txId) or self.schemasConfirming.get(txId)

    def rollbackToSlot(self, slot, txType: TransactionType):
        logger.debug(f"Rolling back transactions to slot {slot} for {txType.value}")
        confirmingTxs = self.kelsConfirming if txType == TransactionType.KEL else self.schemasConfirming
        for keys, tx in confirmingTxs.getItemIter():
            tx = json.loads(tx)
            if "block_slot" not in tx:  # Hasn't appeared on-chain yet
                return

            if tx["block_slot"] > slot:
                # Forget we saw it and re-schedule events
                for event in tx["batch"]:
                    self._addToQueue(event.encode('utf-8'), txType)

                self.dbConfirmingUtxos.rem(keys)
                confirmingTxs.rem(keys)

    def confirmOrTimeoutDeepTxs(self, txType: TransactionType):
        if not self.onTip:
            return

        confirmingTxs = self.kelsConfirming if txType == TransactionType.KEL else self.schemasConfirming
        for keys, tx in confirmingTxs.getItemIter():
            tx = json.loads(tx)
            blockHeight = int(tx["block_height"]) if "block_height" in tx.keys() else 0

            # Check for confirmation
            if blockHeight > 0 and self.tipHeight - blockHeight >= TRANSACTION_SECURITY_DEPTH:
                self.dbConfirmingUtxos.rem(keys)
                confirmingTxs.rem(keys)
                continue

            # Check for timeout (not appearing - maybe fork)
            if self.tipHeight - int(tx["tip"]) >= TRANSACTION_TIMEOUT_DEPTH:
                for event in tx["batch"]:
                    self._addToQueue(event.encode('utf-8'), txType)

                self.dbConfirmingUtxos.rem(keys)
                confirmingTxs.rem(keys)

    def updateConfirmingTxMetadata(self, tx, txType: TransactionType):
        confirmingTxs = self.kelsConfirming if txType == TransactionType.KEL else self.schemasConfirming
        confirmingTxs.pin(keys=tx['id'], val=json.dumps(tx).encode('utf-8'))
