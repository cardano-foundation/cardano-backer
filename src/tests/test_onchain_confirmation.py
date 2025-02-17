# -*- encoding: utf-8 -*-
"""
src.tests.test_onchain_confirmation module

"""
import logging
import time
import json
from keri import help
from keri.app import habbing
from keri.core import eventing, serdering, Salter, scheming
from backer import cardaning, queueing

UTXO_DELAY = 1
TRANSACTION_SECURITY_DEPTH = 16
TRANSACTION_TIMEOUT_DEPTH = 32
logger = help.ogler.getLogger()

def wait_for_updating_utxo():
    time.sleep(UTXO_DELAY)

def test_kel_confirmation():
    help.ogler.resetLevel(level=logging.DEBUG, globally=True)
    salt = b"0123456789abcdef"
    salter = Salter(raw=salt)

    with habbing.openHby(name="keria", salt=salter.qb64, temp=True) as hby:
        hab = hby.makeHab("test03", transferable=False)
        icp = {
            "v": "KERI10JSON00012b_",
            "t": "icp",
            "d": "EIvqOceOSGCMW4Ls-Wdi6t4K3RjKZU_DcHC_Q2w2jNs9",
            "i": "EIvqOceOSGCMW4Ls-Wdi6t4K3RjKZU_DcHC_Q2w2jNs9",
            "s": "0",
            "kt": "1",
            "k": ["DCwn62HEdsIbb0Tf-xTTR3fxZMQspc4iNbghK93Tfv1m"],
            "nt": "1",
            "n": ["EDzxxCBaWkzJ2Azn5HS50DZjslp-HMPeG6vGEm4AW168"],
            "bt": "0",
            "b": [],
            "c": [],
            "a": [],
        }

        serder = serdering.SerderKERI(sad=icp, kind=eventing.Kinds.json)
        msg = serder.raw
        ledger = cardaning.Cardano(hab=hab, ks=hab.ks)
        ledger.keldb_queued.trim()
        queue = queueing.Queueing(hab=hab, ledger=ledger)
        queue.pushToQueued(serder.pre, msg)
        cardaning.TRANSACTION_SECURITY_DEPTH = TRANSACTION_SECURITY_DEPTH
        cardaning.TRANSACTION_TIMEOUT_DEPTH = TRANSACTION_TIMEOUT_DEPTH

        # Case: Not enough {TRANSACTION_SECURITY_DEPTH} transactions deep into the blockchain
        blockHeight = 26503120
        tipHeight = blockHeight + TRANSACTION_SECURITY_DEPTH - 1

        # Submit event
        ledger.updateTip(tipHeight - 1)
        ledger.publishEvents(type=cardaning.CardanoType.KEL)
        trans = None

        for keys, item in ledger.keldbConfirming.getItemIter():
            if item is None:
                continue

            trans = json.loads(item)

        assert trans['keri_raw'] == [msg.decode('utf-8')]

        transId = trans['id']
        ledger.updateTip(tipHeight)
        trans['block_height'] = blockHeight
        ledger.updateTrans(trans, type=cardaning.CardanoType.KEL)
        ledger.confirmTrans(type=cardaning.CardanoType.KEL)
        confirmingTrans = ledger.getConfirmingTrans(transId)
        assert confirmingTrans != None


        # Case: Transaction does not appear after {TRANSACTION_TIMEOUT_DEPTH} blocks
        tipHeight = blockHeight + TRANSACTION_SECURITY_DEPTH - 1
        ledger.updateTip(tipHeight)
        trans['tip'] = tipHeight - TRANSACTION_TIMEOUT_DEPTH - 1
        trans['block_height'] = blockHeight
        ledger.updateTrans(trans, type=cardaning.CardanoType.KEL)
        ledger.confirmTrans(type=cardaning.CardanoType.KEL)
        wait_for_updating_utxo()
        ledger.publishEvents(type=cardaning.CardanoType.KEL)

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


        # Case: Rollback transaction
        tipHeight = blockHeight + TRANSACTION_SECURITY_DEPTH - 1
        ledger.updateTip(tipHeight)
        newTrans['block_height'] = blockHeight
        newTrans['block_slot'] = tipHeight - 1
        ledger.updateTrans(newTrans, type=cardaning.CardanoType.KEL)
        ledger.updateTip(tipHeight - 1)
        ledger.rollbackBlock((tipHeight - 2), type=cardaning.CardanoType.KEL)
        oldTrans = ledger.getConfirmingTrans(newTransId)
        wait_for_updating_utxo()
        ledger.publishEvents(type=cardaning.CardanoType.KEL)
        ledger.confirmTrans(type=cardaning.CardanoType.KEL)

        # Load new trans
        for keys, item in ledger.keldbConfirming.getItemIter():
            if item is None:
                continue

            latestTrans = json.loads(item)

        assert oldTrans == None
        assert latestTrans != None
        assert latestTrans['id'] != newTransId


        # Case: {TRANSACTION_DEEP} transactions deep into the blockchain
        tipHeight = blockHeight + TRANSACTION_SECURITY_DEPTH
        ledger.updateTip(tipHeight)
        latestTrans['block_height'] = blockHeight
        ledger.updateTrans(latestTrans, type=cardaning.CardanoType.KEL)
        ledger.confirmTrans(type=cardaning.CardanoType.KEL)
        confirmingTrans = ledger.getConfirmingTrans(latestTrans['id'])
        assert confirmingTrans == None

def test_schema_confirmation():
    help.ogler.resetLevel(level=logging.DEBUG, globally=True)
    salt = b"0123456789abcdef"
    salter = Salter(raw=salt)

    with habbing.openHby(name="keria", salt=salter.qb64, temp=True) as hby:
        hab = hby.makeHab("test03", transferable=False)
        schema = {
            "$id": "EMRvS7lGxc1eDleXBkvSHkFs8vUrslRcla6UXOJdcczw",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "properties": {
                "a": {
                    "type": "string"
                },
                "b": {
                    "type": "number"
                },
                "c": {
                    "type": "string",
                    "format": "date-time"
                }
            }
        }

        schemer = scheming.Schemer(raw=json.dumps(schema).encode('utf-8'))
        msg = schemer.raw
        ledger = cardaning.Cardano(hab=hab, ks=hab.ks)
        ledger.keldb_queued.trim()
        queue = queueing.Queueing(hab=hab, ledger=ledger)
        queue.pushToQueued("", msg, cardaning.CardanoType.SCHEMA)
        cardaning.TRANSACTION_SECURITY_DEPTH = TRANSACTION_SECURITY_DEPTH
        cardaning.TRANSACTION_TIMEOUT_DEPTH = TRANSACTION_TIMEOUT_DEPTH

        # Case: Not enough {TRANSACTION_SECURITY_DEPTH} transactions deep into the blockchain
        blockHeight = 26503120
        tipHeight = blockHeight + TRANSACTION_SECURITY_DEPTH - 1

        # Submit event
        ledger.updateTip(tipHeight - 1)
        wait_for_updating_utxo()
        ledger.publishEvents(type=cardaning.CardanoType.SCHEMA)
        trans = None

        for keys, item in ledger.schemadbConfirming.getItemIter():
            if item is None:
                continue

            trans = json.loads(item)

        assert trans['keri_raw'] == [msg.decode('utf-8')]

        transId = trans['id']
        ledger.updateTip(tipHeight)
        trans['block_height'] = blockHeight
        ledger.updateTrans(trans, cardaning.CardanoType.SCHEMA)
        ledger.confirmTrans(type=cardaning.CardanoType.SCHEMA)
        confirmingTrans = ledger.getConfirmingTrans(transId)
        assert confirmingTrans != None


        # Case: Transaction does not appear after {TRANSACTION_TIMEOUT_DEPTH} blocks
        tipHeight = blockHeight + TRANSACTION_SECURITY_DEPTH - 1
        ledger.updateTip(tipHeight)
        trans['tip'] = tipHeight - TRANSACTION_TIMEOUT_DEPTH - 1
        trans['block_height'] = blockHeight
        ledger.updateTrans(trans, type=cardaning.CardanoType.SCHEMA)
        ledger.confirmTrans(type=cardaning.CardanoType.SCHEMA)
        wait_for_updating_utxo()
        ledger.publishEvents(type=cardaning.CardanoType.SCHEMA)

        confirmingTrans = ledger.getConfirmingTrans(transId)
        newTrans = None

        # Load new trans
        for keys, item in ledger.schemadbConfirming.getItemIter():
            if item is None:
                continue

            newTrans = json.loads(item)

        newTransId = newTrans['id']
        assert newTransId != transId
        assert confirmingTrans == None


        # Case: Rollback transaction
        tipHeight = blockHeight + TRANSACTION_SECURITY_DEPTH - 1
        ledger.updateTip(tipHeight)
        newTrans['block_height'] = blockHeight
        newTrans['block_slot'] = tipHeight - 1
        ledger.updateTrans(newTrans, type=cardaning.CardanoType.SCHEMA)
        ledger.updateTip(tipHeight - 1)
        ledger.rollbackBlock((tipHeight - 2), type=cardaning.CardanoType.SCHEMA)
        oldTrans = ledger.getConfirmingTrans(newTransId)
        wait_for_updating_utxo()
        ledger.publishEvents(type=cardaning.CardanoType.SCHEMA)
        ledger.confirmTrans(type=cardaning.CardanoType.SCHEMA)

        # Load new trans
        for keys, item in ledger.schemadbConfirming.getItemIter():
            if item is None:
                continue

            latestTrans = json.loads(item)

        assert oldTrans == None
        assert latestTrans != None
        assert latestTrans['id'] != newTransId


        # Case: {TRANSACTION_DEEP} transactions deep into the blockchain
        tipHeight = blockHeight + TRANSACTION_SECURITY_DEPTH
        ledger.updateTip(tipHeight)
        latestTrans['block_height'] = blockHeight
        ledger.updateTrans(latestTrans, type=cardaning.CardanoType.SCHEMA)
        ledger.confirmTrans(type=cardaning.CardanoType.SCHEMA)
        confirmingTrans = ledger.getConfirmingTrans(latestTrans['id'])
        assert confirmingTrans == None