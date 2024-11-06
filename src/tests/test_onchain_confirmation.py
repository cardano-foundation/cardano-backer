# -*- encoding: utf-8 -*-
"""
src.tests.test_onchain_confirmation module

"""
import os
import json
import time
from datetime import datetime
from keri.app import habbing
from keri.core import coring
from backer import cardaning


SHELLY_UNIX = os.environ.get('SHELLY_UNIX', 1666656000)
TRANSACTION_DEEP = os.environ.get('TRANSACTION_DEEP', 16)
TRANSACTION_CONFIRMATION_TIMEOUT = os.environ.get('TRANSACTION_CONFIRMATION_TIMEOUT', 30)

def test_confirmation():
    salt = b"0123456789abcdef"
    salter = coring.Salter(raw=salt)

    with habbing.openHby(name="keria", salt=salter.qb64, temp=True) as hby:
        hab = hby.makeHab("test03", transferable=False) 
        kel = b'{"v":"KERI10JSON00012b_","t":"icp","d":"ELz6bb998nI6AAeUqrz5VH3KExAHxBWJxEvZFYeT3Gfb","i":"ELz6bb998nI6AAeUqrz5VH3KExAHxBWJxEvZFYeT3Gfb","s":"0","kt":"1","k":["DONml9O3wBfTtqJ2VObpdtFI4O4-uV3vTRxClLUPfAYN"],"nt":"1","n":["EGudxbhGctmGOQS05DJ-M-LryvPYW0RejlJeFsABDaUr"],"bt":"0","b":[],"c":[],"a":[]}-AABAABKtwOi9WupJO2sBNUdulIMW_TNAI-kJHf9lF24SxjavtmiocjjWcAwh405mK5774-wyYI4zqPu2Ylk1FtsRS8O'
        ledger = cardaning.Cardano(hab=hab, ks=hab.ks)
        
        # Publish event
        ledger.publishEvent(kel)
        assert ledger.pending_kel == bytearray(kel)

        # Submit event
        ledger.submitKelTx(kel)
        trans = None

        for keys, item in ledger.keldbConfirming.getItemIter():
            if item is None:
                continue
            
            trans = json.loads(item)

        assert trans['kel'] == kel.decode('utf-8')


        # Case: Not enough {TRANSACTION_DEEP} transactions deep into the blockchain
        transId = trans['id']   
        blockHeight = 26503120
        tipHeight = blockHeight + TRANSACTION_DEEP - 1
        blockSlot = int(datetime.utcnow().timestamp()) - SHELLY_UNIX + TRANSACTION_CONFIRMATION_TIMEOUT - 1

        ledger.updateTip(tipHeight)
        ledger.updateTrans(transId, blockHeight, blockSlot)        
        ledger.confirmTrans()
        confirmingTrans = ledger.getConfirmingTrans(transId)
        assert confirmingTrans != None


        # Case: Transaction does not appear after {TRANSACTION_CONFIRMATION_TIMEOUT} mins
        tipHeight = blockHeight + TRANSACTION_DEEP
        blockSlot = int(datetime.utcnow().timestamp()) - SHELLY_UNIX + TRANSACTION_CONFIRMATION_TIMEOUT + 1
        ledger.updateTip(tipHeight)
        ledger.updateTrans(transId, blockHeight, blockSlot)
        time.sleep(TRANSACTION_CONFIRMATION_TIMEOUT + 1)
        ledger.confirmTrans()
        confirmingTrans = ledger.getConfirmingTrans(transId)        
        newTrans = None
        # Load new trans
        for keys, item in ledger.keldbConfirming.getItemIter():
            if item is None:
                continue
            
            newTrans = json.loads(item)
        
        newTransId = newTrans['id']
        assert newTransId != transId
        assert confirmingTrans == None


        # Case: {TRANSACTION_DEEP} transactions deep into the blockchain + {TRANSACTION_CONFIRMATION_TIMEOUT - 1} senconds after publishing
        tipHeight = blockHeight + TRANSACTION_DEEP
        blockSlot = int(datetime.utcnow().timestamp()) - SHELLY_UNIX + TRANSACTION_CONFIRMATION_TIMEOUT - 1
        ledger.updateTip(tipHeight)
        ledger.updateTrans(newTransId, blockHeight, blockSlot)
        # Confirm transaction: Transaction does not appear after 30mins
        ledger.confirmTrans()
        confirmingTrans = ledger.getConfirmingTrans(newTransId)
        assert confirmingTrans == None
