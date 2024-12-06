# -*- encoding: utf-8 -*-
"""
KERI
keri.ledger.cardaning module

Registrar Backer operations on Cardano Ledger

"""

import json
import pycardano
import os
import time
import ogmios
from keri import help
from keri.db import subing
from keri.core import serdering

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
        self.keldb_queued = subing.SerderSuber(db=hab.db, subkey="kel_queued")
        self.keldb_published = subing.SerderSuber(db=hab.db, subkey="kel_published")
        self.keldbConfirming = subing.Suber(db=hab.db, subkey="kel_confirming")
        self.context = pycardano.OgmiosV6ChainContext()
        self.client = ogmios.Client()
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

    def updateTip(self, tipHeight):
        self.tipHeight = tipHeight

    def addToQueue(self, event):
        serder = serdering.SerderKERI(raw=event)
        self.keldb_queued.pin(keys=(serder.pre, serder.said), val=serder)

    def removeFromQueue(self, event):
        serder = serdering.SerderKERI(raw=event)
        keys=(serder.pre, serder.said)
        self.keldb_queued.rem(keys=keys)

    def addToPublished(self, event):
        serder = serdering.SerderKERI(raw=event)
        self.keldb_published.pin(keys=(serder.pre, serder.said), val=serder)

    def publishEvents(self):
        kel_data = bytearray()
        submitting_kel = []
        submitting_tx_cbor = None
        temp_tx_cbor = None

        for (_, _), serder in reversed(list(self.keldb_queued.getItemIter())):
            event = serder.raw
            # Build transaction
            builder = pycardano.TransactionBuilder(self.context)
            builder.add_input_address(self.spending_addr)
            builder.add_output(pycardano.TransactionOutput(self.spending_addr, pycardano.Value.from_primitive([TRANSACTION_AMOUNT])))
            kel_data = kel_data + event
            kel_data_bytes = bytes(kel_data)

            # Chunk size
            # bytearrays is not accept
            value = [kel_data_bytes[i:i + 64] for i in range(0, len(kel_data_bytes), 64)]

            # Metadata. accept int key type
            builder.auxiliary_data = pycardano.AuxiliaryData(pycardano.Metadata({1: value}))
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
            submitting_kel.append(event.decode('utf-8'))

        # Submit transaction
        try:
            self.context.submit_tx_cbor(submitting_tx_cbor)
            transId = str(signed_tx.transaction_body.inputs[0].transaction_id)
            trans = {
                "id": transId,
                "kel": submitting_kel,
                "tip": self.tipHeight
            }
            self.keldbConfirming.pin(keys=transId, val=json.dumps(trans).encode('utf-8'))

            for event in submitting_kel:
                event = event.encode('utf-8')
                self.addToPublished(event)
                self.removeFromQueue(event)

        except Exception as e:
            logger.critical(f"ERROR: Submit tx: {e}")


    def getConfirmingTrans(self, transId):
        return self.keldbConfirming.get(transId)

    def rollbackBlock(self, rollBackSlot):
        try:
            for keys, item in self.keldbConfirming.getItemIter():
                if item is None:
                    continue

                item = json.loads(item)
                blockSlot = item["block_slot"]

                if blockSlot > rollBackSlot:
                    # Push back to pending KEL to resubmit
                    for kel_item in item['kel']:
                        self.addToQueue(kel_item.encode('utf-8'))

                    self.keldbConfirming.rem(keys)
        except Exception as e:
            logger.critical(f"Cannot rollback transaction: {e}")

    def confirmTrans(self):
        try:
            for keys, item in self.keldbConfirming.getItemIter():
                if item is None:
                    continue

                item = json.loads(item)
                transTip = int(item["tip"])
                blockHeight = int(item["block_height"]) if 'block_height' in item.keys() else 0

                # Check for confirmation
                if self.tipHeight > 0 and blockHeight > 0 and self.tipHeight - blockHeight >= TRANSACTION_SECURITY_DEPTH:
                    self.keldbConfirming.rem(keys)
                    continue

                if self.tipHeight - transTip > TRANSACTION_TIMEOUT_DEPTH:
                    for kel_item in item['kel']:
                        self.addToQueue(kel_item.encode('utf-8'))

                    self.keldbConfirming.rem(keys)
        except Exception as e:
            logger.critical(f"Cannot confirm transaction: {e}")

    def updateTrans(self, trans):
        transId = trans['id']
        self.keldbConfirming.pin(keys=transId, val=json.dumps(trans).encode('utf-8'))

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
