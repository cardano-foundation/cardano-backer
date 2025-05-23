# -*- encoding: utf-8 -*-
"""
KERI
keri.ledger.cardaning module

Registrar Backer operations on Cardano Ledger

"""
from enum import Enum
import json
import pycardano
import os
import ogmios
from dataclasses import dataclass
from keri import help
from keri.db import subing, koming
from keri.core import serdering, scheming
from backer.constants import METADATUM_LABEL_KEL, METADATUM_LABEL_SCHEMA

logger = help.ogler.getLogger()

QUEUE_DURATION = os.environ.get('QUEUE_DURATION', 60)
NETWORK_NAME = os.environ.get('NETWORK') if os.environ.get('NETWORK') else 'preview'
NETWORK = pycardano.Network.MAINNET if os.environ.get('NETWORK') == 'mainnet' else pycardano.Network.TESTNET
MINIMUN_BALANCE = os.environ.get('MINIMUN_BALANCE', 5000000)
TRANSACTION_AMOUNT = os.environ.get('TRANSACTION_AMOUNT', 1000000)
MIN_BLOCK_CONFIRMATIONS = os.environ.get('MIN_BLOCK_CONFIRMATIONS', 3)
TRANSACTION_SECURITY_DEPTH = os.environ.get('TRANSACTION_SECURITY_DEPTH', 16)
TRANSACTION_TIMEOUT_DEPTH = os.environ.get('TRANSACTION_TIMEOUT_DEPTH', 32)
MAX_TRANSACTION_SIZE = 16384
MAX_TRANSACTION_SIZE_MARGIN = 3 # PyCardano and Ogmios serialize the transaction could result in small variations
OGMIOS_HOST = os.environ.get('OGMIOS_HOST', 'localhost')
OGMIOS_PORT = os.environ.get('OGMIOS_PORT', 1337)
BACKER_STATE_DB = 'bstt.'
BACKER_TIP_KEY = 'b_tip'


class CardanoType(Enum):
    SCHEMA = "CARDANO_SCHEMA"
    KEL = "CARDANO_KEL"


class CardanoDBType(Enum):
    QUEUED = "QUEUED"
    PUBLISHED = "PUBLISHED"
    CONFIRMING = "CONFIRMING"

class CardanoDBName(Enum):
    KEL_QUEUED = "kel_queued"
    KEL_PUBLISHED = "kel_published"
    KEL_CONFIRMING = "kel_confirming"
    SCHEMA_QUEUED = "schemadb_queued"
    SCHEMA_PUBLISHED = "schemadb_published"
    SCHEMA_CONFIRMING = "schemadb_confirming"
    CONFIRMING_UTXOS = "confirming_utxo"


@dataclass
class PointRecord:
    id: str 
    slot: int

class Cardano:
    """
    Environment variables required:
        - WALLET_ADDRESS_CBORHEX = Private Key of funding address as CBOR Hex. Must be an Enterprice address (no Staking part) as PaymentSigningKeyShelley_ed25519

    Additional libraries required:
        pip install pycardano ogmios
    See Backer designation event: https://github.com/WebOfTrust/keripy/issues/90

    Features:
        - Cardano Address is derived from the same Ed25519 seed (private key) used to derive the prefix of the backer
        - Anchoring KELs from multiple prefixes
        - Queue events during a period of time to allow several block confirmations as a safety meassure
        - Optional funding address to fund the backer address
    """

    def __init__(self, hab, ks=None):
        self.pending_kel = []
        self.keldb_queued = subing.Suber(db=hab.db, subkey=CardanoDBName.KEL_QUEUED.value)
        self.keldb_published = subing.Suber(db=hab.db, subkey=CardanoDBName.KEL_PUBLISHED.value)
        self.keldbConfirming = subing.Suber(db=hab.db, subkey=CardanoDBName.KEL_CONFIRMING.value)

        self.schemadb_queued = subing.Suber(db=hab.db, subkey=CardanoDBName.SCHEMA_QUEUED.value)
        self.schemadb_published = subing.Suber(db=hab.db, subkey=CardanoDBName.SCHEMA_PUBLISHED.value)
        self.schemadbConfirming = subing.Suber(db=hab.db, subkey=CardanoDBName.SCHEMA_CONFIRMING.value)

        self.dbConfirmingUtxos = subing.DupSuber(db=hab.db, subkey=CardanoDBName.CONFIRMING_UTXOS.value)

        self.states = koming.Komer(db=hab.db,
                                   schema=PointRecord,
                                   subkey=BACKER_STATE_DB)

        self.context = pycardano.OgmiosV6ChainContext(
            host=OGMIOS_HOST,
            port=OGMIOS_PORT,
            network=NETWORK
        )
        self.client = ogmios.Client(host=OGMIOS_HOST, port=OGMIOS_PORT)
        self.tipHeight = 0

        self.payment_signing_key = pycardano.PaymentSigningKey.from_cbor(os.environ.get('WALLET_ADDRESS_CBORHEX'))
        payment_verification_key = pycardano.PaymentVerificationKey.from_signing_key(self.payment_signing_key)
        self.spending_addr = pycardano.Address(payment_verification_key.hash(), None, network=NETWORK)
        print("Cardano Backer Spending Address:", self.spending_addr.encode())

        balance = self.getaddressBalance(self.spending_addr.encode())
        if balance and balance > MINIMUN_BALANCE:
            print("Address balance:", balance/1000000, "ADA")
        else:
            print("The wallet is empty or insufficient balance detected")
            exit(1)

    def getCardanoDB(self, type, name):
            if type == CardanoType.SCHEMA:
                if name == CardanoDBType.QUEUED:
                    return self.schemadb_queued
                elif name == CardanoDBType.PUBLISHED:
                    return self.schemadb_published
                elif name == CardanoDBType.CONFIRMING:
                    return self.schemadbConfirming
            else:
                if name == CardanoDBType.QUEUED:
                    return self.keldb_queued
                elif name == CardanoDBType.PUBLISHED:
                    return self.keldb_published
                elif name == CardanoDBType.CONFIRMING:
                    return self.keldbConfirming

    def updateTip(self, tipHeight):
        self.tipHeight = tipHeight

    def addToQueue(self, event, type:CardanoType):
        if type == CardanoType.SCHEMA:
            schemer = scheming.Schemer(raw=event)
            self.schemadb_queued.pin(keys=(schemer.said, ), val=event)
        else:
            serder = serdering.SerderKERI(raw=event)
            self.keldb_queued.pin(keys=(serder.pre, serder.said), val=event)

    def removeFromQueue(self, event, type:CardanoType):
        if type == CardanoType.SCHEMA:
            schemer = scheming.Schemer(raw=event)
            self.schemadb_queued.rem(keys=(schemer.said, ))
        else:
            serder = serdering.SerderKERI(raw=event)
            keys=(serder.pre, serder.said)
            self.keldb_queued.rem(keys=keys)

    def addToPublished(self, event, type:CardanoType):
        if type == CardanoType.SCHEMA:
            schemer = scheming.Schemer(raw=event)
            self.schemadb_published.pin(keys=(schemer.said, ), val=event)
        else:
            serder = serdering.SerderKERI(raw=event)
            self.keldb_published.pin(keys=(serder.pre, serder.said), val=event)

    def selectUTXO(self):
        # TODO: We need more advanced UTXO selection in the future.
        # For now, it just selects one and assumes it'll have enough.
        # Deployments should fund the address with 1 or X UTXOs of sufficient size.

        # Select the first utxo from spending address
        utxos = self.context.utxos(self.spending_addr)

        for utxo in utxos:
            if not self.isInConfirmingUTxO(utxo):
                return [utxo]

        return []

    def publishEvents(self, type:CardanoType):
        keri_data = bytearray()
        submitting_items = []
        submitting_tx_cbor = None
        temp_tx_cbor = None

        utxos = self.selectUTXO()

        if len(utxos) < 1:
            logger.critical("ERROR: No UTXO available")
            return

        db_queued = self.getCardanoDB(type, CardanoDBType.QUEUED)
        dbConfirming = self.getCardanoDB(type, CardanoDBType.CONFIRMING)

        for _, event in reversed(list(db_queued.getItemIter())):
            # Build transaction
            builder = pycardano.TransactionBuilder(self.context)

            for utxo in utxos:
                builder.add_input(utxo)

            builder.add_output(pycardano.TransactionOutput(self.spending_addr, pycardano.Value.from_primitive([TRANSACTION_AMOUNT])))
            keri_data = keri_data + event.encode('utf-8')
            keri_data_bytes = bytes(keri_data)

            # Chunk size
            # bytearrays is not accept
            value = [keri_data_bytes[i:i + 64] for i in range(0, len(keri_data_bytes), 64)]

            # Metadata. accept int key type
            metadatumLabel = METADATUM_LABEL_KEL if type == CardanoType.KEL else METADATUM_LABEL_SCHEMA
            builder.auxiliary_data = pycardano.AuxiliaryData(pycardano.Metadata({metadatumLabel: value}))
            try:
                signed_tx = builder.build_and_sign([self.payment_signing_key],
                                                change_address=self.spending_addr,
                                                merge_change=True)

                if len(signed_tx.to_cbor()) > MAX_TRANSACTION_SIZE - MAX_TRANSACTION_SIZE_MARGIN:
                    break

                temp_tx_cbor = signed_tx.to_cbor()
            except pycardano.exception.InvalidTransactionException as e:
                if "exceeds the max limit" in str(e):
                    break

            submitting_tx_cbor = bytes(temp_tx_cbor)
            submitting_items.append(event)

        if not submitting_tx_cbor:
            return

        transId = str(signed_tx.id)
        submitting_trans = {
            "id": transId,
            "type": type.value,
            "keri_raw": submitting_items,
            "tip": self.tipHeight,
        }
        utxoIds = [f"{str(utxo.input.transaction_id)}#{utxo.input.index}" for utxo in utxos]

        dbConfirming.pin(keys=submitting_trans["id"], val=json.dumps(submitting_trans).encode('utf-8'))
        self.dbConfirmingUtxos.pin(keys=submitting_trans["id"], vals=utxoIds)

        # Submit transaction
        try:
            self.context.submit_tx_cbor(submitting_tx_cbor)

            # Remove submitted events from queue and add them into published
            for event in submitting_items:
                event = event.encode('utf-8')
                self.addToPublished(event, type)
                self.removeFromQueue(event, type)

            logger.debug(f"Submitted tx: {submitting_trans}")
        except Exception as e:
            logger.critical(f"ERROR: Submit tx: {e}")
            # Add back to queue
            for keri_item in submitting_trans['keri_raw']:
                self.addToQueue(keri_item.encode('utf-8'), type)

            # Remove from confirming
            self.dbConfirmingUtxos.rem(keys=submitting_trans["id"])
            dbConfirming.rem(submitting_trans["id"])

    def getConfirmingTrans(self, transId):
        tx = self.schemadbConfirming.get(transId)

        if not tx:
            tx = self.keldbConfirming.get(transId)

        return tx

    def rollbackBlock(self, rollBackSlot, type:CardanoType):
        try:
            dbConfirming = self.getCardanoDB(type, CardanoDBType.CONFIRMING)
            for keys, item in dbConfirming.getItemIter():
                if item is None:
                    continue

                item = json.loads(item)
                blockSlot = item["block_slot"]

                if blockSlot > rollBackSlot:
                    # Push back to pending KEL to resubmit
                    for keri_item in item['keri_raw']:
                        self.addToQueue(keri_item.encode('utf-8'), type=type)

                    dbConfirming.rem(keys)
        except Exception as e:
            logger.critical(f"Cannot rollback transaction: {e}")

    def isInConfirmingUTxO(self, utxo):
        utxoId = f"{utxo.input.transaction_id}#{utxo.input.index}"

        for _, confirmingUtxoId  in self.dbConfirmingUtxos.getItemIter():
            if confirmingUtxoId  == utxoId:
                return True

        return False

    def confirmTrans(self, type: CardanoType):
        dbConfirming = self.getCardanoDB(type, CardanoDBType.CONFIRMING)
        try:
            for keys, item in dbConfirming.getItemIter():
                if item is None:
                    continue

                item = json.loads(item)
                transTip = int(item["tip"])
                blockHeight = int(item["block_height"]) if 'block_height' in item.keys() else 0

                # Check for confirmation
                if self.tipHeight > 0 and blockHeight > 0 and self.tipHeight - blockHeight >= TRANSACTION_SECURITY_DEPTH:
                    dbConfirming.rem(keys)
                    self.dbConfirmingUtxos.rem(keys)
                    continue

                if self.tipHeight - transTip > TRANSACTION_TIMEOUT_DEPTH:
                    for keri_item in item['keri_raw']:
                        self.addToQueue(keri_item.encode('utf-8'), type)

                    dbConfirming.rem(keys)
                    self.dbConfirmingUtxos.rem(keys)

        except Exception as e:
            logger.critical(f"Cannot confirm transaction: {e}")

    def updateTrans(self, trans, type:CardanoType):
        transId = trans['id']
        dbConfirming = self.getCardanoDB(type, CardanoDBType.CONFIRMING)
        dbConfirming.pin(keys=transId, val=json.dumps(trans).encode('utf-8'))

    def getaddressBalance(self, addr):
        try:
            utxo_list = self.client.query_utxo.execute([ogmios.Address(addr)])

            if utxo_list and len(utxo_list[0]) > 0:
                utxo = utxo_list[0][0]
                return int(utxo.value['ada']['lovelace'])
        except Exception as e:
            logger.critical(f"Cannot get address's balance: {e}")

        return 0

def getInfo(alias, hab, ks):
    # # TODO: Implement this later
    # try:
    #     blockfrostProjectId=os.environ['BLOCKFROST_API_KEY']
    # except KeyError:
    #     print("Environment variable BLOCKFROST_API_KEY not set")
    #     exit(1)
    # api = BlockFrostApi(
    #     project_id=blockfrostProjectId,
    #     base_url=BLOCKFROST_API_URL
    #     )
    # backerPrivateKey = ks.pris.get(hab.kever.prefixer.qb64).raw
    # payment_signing_key = PaymentSigningKey(backerPrivateKey,"PaymentSigningKeyShelley_ed25519","PaymentSigningKeyShelley_ed25519")
    # payment_verification_key = PaymentVerificationKey.from_signing_key(payment_signing_key)
    # spending_addr = Address(payment_part=payment_verification_key.hash(),staking_part=None, network=NETWORK)
    # try:
    #     address = api.address(address=spending_addr.encode())
    #     balance = int(address.amount[0].quantity)
    # except ApiError as e:
    #     print("error", e)


    # try:
    #     funding_payment_signing_key = PaymentSigningKey.from_cbor(os.environ.get('WALLET_ADDRESS_CBORHEX'))
    #     funding_payment_verification_key = PaymentVerificationKey.from_signing_key(funding_payment_signing_key)
    #     funding_addr = Address(funding_payment_verification_key.hash(), None, network=NETWORK).encode()
    #     f_address = api.address(address=funding_addr)
    #     funding_balace = int(f_address.amount[0].quantity)
    # except:
    #     funding_addr = "NA"
    #     funding_balace = "NA"

    # print("Name:", alias)
    # print("Prefix:", hab.kever.prefixer.qb64)
    # print("Network:", "Cardano", NETWORK.name)
    # print("Cardano address:", spending_addr.encode())
    # print("Balance:", balance/1000000, "ADA")
    # print("Funding address:", funding_addr)
    # print("Funding balance:", funding_balace/1000000, "ADA")
    return

def queryBlockchain(prefix, hab,ks):
    # #TODO: Implement this later
    # try:
    #     blockfrostProjectId=os.environ['BLOCKFROST_API_KEY']
    # except KeyError:
    #     print("Environment variable BLOCKFROST_API_KEY not set")
    #     exit(1)
    # api = BlockFrostApi(
    #     project_id=blockfrostProjectId,
    #     base_url=BLOCKFROST_API_URL
    #     )
    # backerPrivateKey = ks.pris.get(hab.kever.prefixer.qb64).raw
    # payment_signing_key = PaymentSigningKey(backerPrivateKey,"PaymentSigningKeyShelley_ed25519","PaymentSigningKeyShelley_ed25519")
    # payment_verification_key = PaymentVerificationKey.from_signing_key(payment_signing_key)
    # spending_addr = Address(payment_part=payment_verification_key.hash(),staking_part=None, network=NETWORK)

    # txs = api.address_transactions(spending_addr.encode())
    # for tx in txs:
    #     block_height = tx["block_height"]
    #     latest_block = api.block_latest()
    #     if latest_block.height - block_height < MIN_BLOCK_CONFIRMATIONS: continue
    #     tx_detail = api.transaction(tx.tx_hash)
    #     meta = api.transaction_metadata(tx.tx_hash, return_type='json')
    #     if meta:
    #         # print("Fees: ",str(int(tx_detail.fees)/1000000), "ADA")
    #         for n in meta:
    #             ke = json.loads(''.join(n['json_metadata']))
    #             if prefix == ke['ked']['i']:
    #                 print("SeqNo: ",n['label'])
    #                 pp(ke)
    #                 print("\n")

    return
