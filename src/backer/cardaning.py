# -*- encoding: utf-8 -*-
"""
KERI
keri.ledger.cardaning module

Registrar Backer operations on Cardano Ledger

"""

import pycardano
import os
import time
import ogmios
from threading import Timer
from  pprint import pp
from keri import help

logger = help.ogler.getLogger()

QUEUE_DURATION = os.environ.get('QUEUE_DURATION', 60)
NETWORK_NAME = os.environ.get('NETWORK') if os.environ.get('NETWORK') else 'preview'
NETWORK = pycardano.Network.MAINNET if os.environ.get('NETWORK') == 'mainnet' else pycardano.Network.TESTNET
MINIMUN_BALANCE = os.environ.get('MINIMUN_BALANCE', 5000000)
FUNDING_AMOUNT = os.environ.get('FUNDING_AMOUNT', 30000000)
TRANSACTION_AMOUNT = os.environ.get('TRANSACTION_AMOUNT', 1000000)
MIN_BLOCK_CONFIRMATIONS = os.environ.get('MIN_BLOCK_CONFIRMATIONS', 3)


class Cardano:
    """
    Environment variables required:
        - FUNDING_ADDRESS_CBORHEX = Optional, for testing purposes. Private Key of funding address as CBOR Hex. Must be an Enterprice address (no Staking part) as PaymentSigningKeyShelley_ed25519
    
    Additional libraries required:
        pip install pycardano ogmios 
    See Backer designation event: https://github.com/WebOfTrust/keripy/issues/90

    Features:
        - Cardano Address is derived from the same Ed25519 seed (private key) used to derive the prefix of the backer
        - Anchoring KELs from multiple prefixes
        - Queue events during a period of time to allow several block confirmations as a safety meassure
        - Optional funding address to fund the backer address
    """

    def __init__(self, name='backer', hab=None, ks=None):
        self.name = name
        self.pending_kel = bytearray()
        self.timer = Timer(QUEUE_DURATION, self.flushQueue)
        self.context = pycardano.OgmiosV6ChainContext()
        self.client = ogmios.Client()

        # retrieve backer private key and derive cardano address
        backer_private_key = ks.pris.get(hab.kever.prefixer.qb64).raw
        self.payment_signing_key = pycardano.PaymentSigningKey(backer_private_key, "PaymentSigningKeyShelley_ed25519", "PaymentSigningKeyShelley_ed25519")
        payment_verification_key = pycardano.PaymentVerificationKey.from_signing_key(self.payment_signing_key)
        self.spending_addr = pycardano.Address(payment_part=payment_verification_key.hash(),staking_part=None, network=NETWORK)
        print("Cardano Backer Address:", self.spending_addr.encode())
        
        # check address balance and try to fund if necesary
        balance = self.getaddressBalance(self.spending_addr.encode())
        if balance and balance > MINIMUN_BALANCE:
            print("Address balance:", balance/1000000, "ADA")
        else:
            self.fundAddress(self.spending_addr)

    def publishEvent(self, event: bytearray):
        self.pending_kel = event
        self.flushQueue()

    def flushQueue(self):
        try:
            # Build transaction
            builder = pycardano.TransactionBuilder(self.context)
            builder.add_input_address(self.spending_addr)
            builder.add_output(pycardano.TransactionOutput(self.spending_addr, pycardano.Value.from_primitive([TRANSACTION_AMOUNT])))

            # Chunk size
            # bytearrays is not accept
            value = [self.pending_kel[i:i + 64] for i in range(0, len(self.pending_kel), 64)]

            # Metadata. accept int key type
            builder.auxiliary_data = pycardano.AuxiliaryData(pycardano.Metadata({1: value}))

            signed_tx = builder.build_and_sign([self.payment_signing_key],
                                               change_address=self.spending_addr,
                                               merge_change=True)
            # Submit transaction
            self.context.submit_tx(signed_tx.to_cbor())            
        except Exception as e:
            self.timer = Timer(90, self.flushQueue)
            self.timer.start()

    def getaddressBalance(self, addr):
        try:            
            utxo_list = self.client.query_utxo.execute([ogmios.Address(addr)])       

            if utxo_list and len(utxo_list[0]) > 0:          
                utxo = utxo_list[0][0]                
                return int(utxo.value['ada']['lovelace'])
            
        except Exception as e:
            logger.critical(f"Cannot get address's balance: {e}")
        
        return 0

    def fundAddress(self, addr):
        try:
            funding_payment_signing_key = pycardano.PaymentSigningKey.from_cbor(os.environ.get('FUNDING_ADDRESS_CBORHEX'))
            funding_payment_verification_key = pycardano.PaymentVerificationKey.from_signing_key(funding_payment_signing_key)
            funding_addr = pycardano.Address(funding_payment_verification_key.hash(), None, network=NETWORK)
        except KeyError:
            print("Backer address could not be funded. Environment variable FUNDING_ADDRESS_CBORHEX is not set")
            return
        
        fund_addr = funding_addr.encode()
        funding_balance = self.getaddressBalance(fund_addr)
            
        print("Funding address:", funding_addr)
        print("Funding balance:", int(funding_balance)/1000000,"ADA")

        if int(funding_balance) > (FUNDING_AMOUNT + 1000000):
            try:                                
                builder = pycardano.TransactionBuilder(self.context)
                builder.add_input_address(funding_addr)
                builder.add_output(pycardano.TransactionOutput(addr, pycardano.Value.from_primitive([int(FUNDING_AMOUNT/3)])))
                signed_tx = builder.build_and_sign([funding_payment_signing_key], change_address=funding_addr)                
                self.context.submit_tx(signed_tx)
                print("Funds submitted. Wait...")
                time.sleep(50)                
                balance = self.getaddressBalance(self.spending_addr.encode())
                
                if balance:
                    print("Backer balance:",balance/1000000, "ADA")
            except Exception as e:
                logger.critical(f"Cannot fund backer: {e}")
        else:
            print("Insuficient balance to fund backer")


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
    #     funding_payment_signing_key = PaymentSigningKey.from_cbor(os.environ.get('FUNDING_ADDRESS_CBORHEX'))
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
