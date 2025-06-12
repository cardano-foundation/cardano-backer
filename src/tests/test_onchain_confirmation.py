# -*- encoding: utf-8 -*-
"""
src.tests.test_onchain_confirmation module

"""
import logging
import json
from keri import help
from keri.app import habbing
from keri.core import eventing, serdering, Salter, scheming
from backer import cardaning
from tests.helper import TestBase
from ogmios.client import Client
from tests.helper import DEVNET_OGMIOS_HOST, DEVNET_OGMIOS_PORT

TRANSACTION_SECURITY_DEPTH = 16
TRANSACTION_TIMEOUT_DEPTH = 32
logger = help.ogler.getLogger()


class TestOnchainConfirmation(TestBase):
    def test_kel_confirmation(cls):
        help.ogler.resetLevel(level=logging.DEBUG, globally=True)
        salt = b"0123456789abcdef"
        salter = Salter(raw=salt)

        with habbing.openHby(name="test", salt=salter.qb64, temp=True) as hby, Client(DEVNET_OGMIOS_HOST, DEVNET_OGMIOS_PORT) as client:
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
            ledger = cardaning.Cardano(hab=hab, client=client)
            ledger.kelsQueued.trim()
            ledger.kelsQueued.pin(keys=(serder.pre, serder.said), val=msg)
            cardaning.TRANSACTION_SECURITY_DEPTH = TRANSACTION_SECURITY_DEPTH
            cardaning.TRANSACTION_TIMEOUT_DEPTH = TRANSACTION_TIMEOUT_DEPTH

            # 1. Not enough {TRANSACTION_SECURITY_DEPTH} transactions deep into the blockchain
            blockHeight = 26503120

            # 1.1 Condition: blockHeight > 0 and tipHeight - blockHeight < TRANSACTION_SECURITY_DEPTH => not confirmed
            tipHeight = blockHeight + TRANSACTION_SECURITY_DEPTH - 1

            # Submit event
            ledger.onTip = True
            ledger.updateTip(tipHeight - 1)
            selected_utxo = ledger.selectAvailableUTXOs()
            ledger.publishEvents(txType=cardaning.TransactionType.KEL)
            trans = None

            for keys, item in ledger.kelsConfirming.getItemIter():
                if item is None:
                    continue

                trans = json.loads(item)

            assert trans["batch"] == [msg.decode('utf-8')]

            transId = trans['id']

            # Check that utxo is stored
            for (key, ), utxo_index in ledger.dbConfirmingUtxos.getItemIter():
                assert key == transId
                assert utxo_index == f"{selected_utxo[0].input.transaction_id}#{selected_utxo[0].input.index}"
                break

            ledger.updateTip(tipHeight)
            trans['block_height'] = blockHeight
            ledger.updateConfirmingTxMetadata(trans, txType=cardaning.TransactionType.KEL)
            ledger.confirmOrTimeoutDeepTxs(txType=cardaning.TransactionType.KEL)
            cls.wait_for_updating_utxo()
            confirmingTrans = ledger.getConfirmingTx(transId)
            # Not confirmed so confirmingTrans still exists
            assert confirmingTrans != None

            # 1.2 Condition: blockHeight > 0 and tipHeight - blockHeight = TRANSACTION_SECURITY_DEPTH => confirmed
            tipHeight = blockHeight + TRANSACTION_SECURITY_DEPTH
            ledger.updateTip(tipHeight)
            ledger.confirmOrTimeoutDeepTxs(txType=cardaning.TransactionType.KEL)
            cls.wait_for_updating_utxo()
            confirmingTrans = ledger.getConfirmingTx(transId)
            # Confirmed so confirmingTrans must be None
            assert confirmingTrans == None

            # 1.3 Condition: blockHeight > 0 and tipHeight - blockHeight > TRANSACTION_SECURITY_DEPTH => confirmed
            # Add data again for new test
            ledger.kelsQueued.pin(keys=(serder.pre, serder.said), val=msg)
            tipHeight = blockHeight + TRANSACTION_SECURITY_DEPTH + 1
            ledger.updateTip(tipHeight)
            ledger.publishEvents(txType=cardaning.TransactionType.KEL)
            trans = None

            for keys, item in ledger.kelsConfirming.getItemIter():
                if item is None:
                    continue

                trans = json.loads(item)

            assert trans["batch"] == [msg.decode('utf-8')]

            transId = trans['id']
            trans['block_height'] = blockHeight
            ledger.updateConfirmingTxMetadata(trans, txType=cardaning.TransactionType.KEL)
            ledger.confirmOrTimeoutDeepTxs(txType=cardaning.TransactionType.KEL)
            cls.wait_for_updating_utxo()
            confirmingTrans = ledger.getConfirmingTx(transId)
            # Confirmed so confirmingTrans must be None
            assert confirmingTrans == None

            # 2. Transaction does not appear after {TRANSACTION_TIMEOUT_DEPTH} blocks
            print(f"Case: Transaction does not appear after {TRANSACTION_TIMEOUT_DEPTH} blocks")
            # Add data again for new test
            ledger.kelsQueued.pin(keys=(serder.pre, serder.said), val=msg)
            ledger.publishEvents(txType=cardaning.TransactionType.KEL)

            for keys, item in ledger.kelsConfirming.getItemIter():
                if item is None:
                    continue

                trans = json.loads(item)

            # 2.1 tipHeight - int(tx["tip"]) < TRANSACTION_TIMEOUT_DEPTH => still confirming
            tipHeight = blockHeight + TRANSACTION_TIMEOUT_DEPTH
            ledger.updateTip(tipHeight)
            trans['tip'] = blockHeight + 1 
            trans['block_height'] = tipHeight - TRANSACTION_SECURITY_DEPTH + 1
            ledger.updateConfirmingTxMetadata(trans, txType=cardaning.TransactionType.KEL)
            ledger.confirmOrTimeoutDeepTxs(txType=cardaning.TransactionType.KEL)
            cls.wait_for_updating_utxo()

            # Load new trans
            for keys, item in ledger.kelsConfirming.getItemIter():
                if item is None:
                    continue

                confirmingTrans = json.loads(item)

            assert confirmingTrans == trans

            # 2.2 tipHeight - int(tx["tip"]) = TRANSACTION_TIMEOUT_DEPTH => confirm then remove from confirming db
            # Add data again for new test
            ledger.kelsQueued.pin(keys=(serder.pre, serder.said), val=msg)
            ledger.publishEvents(txType=cardaning.TransactionType.KEL)

            for keys, item in ledger.kelsConfirming.getItemIter():
                if item is None:
                    continue

                trans = json.loads(item)

            tipHeight = blockHeight + TRANSACTION_TIMEOUT_DEPTH
            ledger.updateTip(tipHeight)
            trans['tip'] = blockHeight
            trans['block_height'] = tipHeight - TRANSACTION_SECURITY_DEPTH + 1
            ledger.updateConfirmingTxMetadata(trans, txType=cardaning.TransactionType.KEL)
            ledger.confirmOrTimeoutDeepTxs(txType=cardaning.TransactionType.KEL)
            cls.wait_for_updating_utxo()
            confirmingTrans = ledger.getConfirmingTx(transId)

            newTrans = None

            # Load new trans
            for keys, item in ledger.kelsConfirming.getItemIter():
                if item is None:
                    continue

                newTrans = json.loads(item)

            assert newTrans != trans
            assert confirmingTrans == None

            # 2.3 tipHeight - int(tx["tip"]) > TRANSACTION_TIMEOUT_DEPTH => confirm then remove from confirming db
            # Add data again for new test
            ledger.kelsQueued.pin(keys=(serder.pre, serder.said), val=msg)
            ledger.publishEvents(txType=cardaning.TransactionType.KEL)

            for keys, item in ledger.kelsConfirming.getItemIter():
                if item is None:
                    continue

                trans = json.loads(item)

            tipHeight = blockHeight + TRANSACTION_TIMEOUT_DEPTH + 1
            ledger.updateTip(tipHeight)
            trans['tip'] = blockHeight
            trans['block_height'] = tipHeight - TRANSACTION_SECURITY_DEPTH + 1
            ledger.updateConfirmingTxMetadata(trans, txType=cardaning.TransactionType.KEL)
            ledger.confirmOrTimeoutDeepTxs(txType=cardaning.TransactionType.KEL)
            cls.wait_for_updating_utxo()

            ledger.publishEvents(txType=cardaning.TransactionType.KEL)

            confirmingTrans = ledger.getConfirmingTx(transId)
            newTrans = None

            # Load new trans
            for keys, item in ledger.kelsConfirming.getItemIter():
                if item is None:
                    continue

                newTrans = json.loads(item)

            newTransId = newTrans['id']
            assert newTransId != transId
            assert confirmingTrans == None

            # 3. Rollback transaction
            # 3.1 tx["block_slot"] < slot => not rollback: still confirming
            # Add data again for new test
            ledger.kelsQueued.trim()
            ledger.kelsConfirming.trim()
            ledger.kelsQueued.pin(keys=(serder.pre, serder.said), val=msg)
            cls.wait_for_updating_utxo()
            ledger.publishEvents(txType=cardaning.TransactionType.KEL)

            trans = None
            for keys, item in ledger.kelsConfirming.getItemIter():
                if item is None:
                    continue

                trans = json.loads(item)

            tipHeight = blockHeight + TRANSACTION_SECURITY_DEPTH - 1
            ledger.updateTip(tipHeight)
            trans['block_height'] = blockHeight

            submited_slot = tipHeight - 1
            current_slot = submited_slot + 1
            trans['block_slot'] = submited_slot
            ledger.updateConfirmingTxMetadata(trans, txType=cardaning.TransactionType.KEL)
            ledger.updateTip(tipHeight - 1)
            ledger.rollbackToSlot(current_slot, txType=cardaning.TransactionType.KEL)

            # Load new trans
            confirmingTransTrans = None
            for keys, item in ledger.kelsConfirming.getItemIter():
                if item is None:
                    continue

                confirmingTransTrans = json.loads(item)

            assert trans == confirmingTransTrans

            # 3.2 tx["block_slot"] = slot => not rollback: still confirming
            submited_slot = tipHeight - 1
            current_slot = submited_slot
            trans['block_slot'] = submited_slot
            ledger.updateConfirmingTxMetadata(trans, txType=cardaning.TransactionType.KEL)
            ledger.updateTip(tipHeight - 1)

            ledger.rollbackToSlot(current_slot, txType=cardaning.TransactionType.KEL)

            # Load new trans
            confirmingTransTrans = None
            for keys, item in ledger.kelsConfirming.getItemIter():
                if item is None:
                    continue

                confirmingTransTrans = json.loads(item)

            assert trans == confirmingTransTrans


            # 3.3 tx["block_slot"] > slot => rollback: re-add to queue and remove from confirming db
            submited_slot = tipHeight - 1
            current_slot = submited_slot - 1
            trans['block_slot'] = submited_slot
            ledger.updateConfirmingTxMetadata(trans, txType=cardaning.TransactionType.KEL)
            ledger.updateTip(tipHeight - 1)

            ledger.rollbackToSlot(current_slot, txType=cardaning.TransactionType.KEL)

            # Load new trans
            confirmingTransTrans = None
            for keys, item in ledger.kelsConfirming.getItemIter():
                if item is None:
                    continue

                confirmingTransTrans = json.loads(item)

            assert confirmingTransTrans == None

            queued_event = ledger.kelsQueued.get((serder.pre, serder.said))
            queued_serder = serdering.SerderKERI(raw=queued_event.encode('utf-8'))
            assert queued_serder.said == serder.said


    def test_schema_confirmation(cls):
        help.ogler.resetLevel(level=logging.DEBUG, globally=True)
        salt = b"0123456789abcdef"
        salter = Salter(raw=salt)

        with habbing.openHby(name="test", salt=salter.qb64, temp=True) as hby, Client(DEVNET_OGMIOS_HOST, DEVNET_OGMIOS_PORT) as client:
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
            
            ledger = cardaning.Cardano(hab=hab, client=client)
            ledger.kelsQueued.trim()
            ledger.schemasQueued.trim()
            ledger.schemasQueued.pin(keys=(schemer.said,), val=msg)

            cardaning.TRANSACTION_SECURITY_DEPTH = TRANSACTION_SECURITY_DEPTH
            cardaning.TRANSACTION_TIMEOUT_DEPTH = TRANSACTION_TIMEOUT_DEPTH

            # Case: Not enough {TRANSACTION_SECURITY_DEPTH} transactions deep into the blockchain
            blockHeight = 26503120
            tipHeight = blockHeight + TRANSACTION_SECURITY_DEPTH - 1

            # Submit event
            ledger.onTip = True
            ledger.updateTip(tipHeight - 1)
            cls.wait_for_updating_utxo()
            ledger.publishEvents(txType=cardaning.TransactionType.SCHEMA)
            trans = None

            for keys, item in ledger.schemasConfirming.getItemIter():
                if item is None:
                    continue

                trans = json.loads(item)

            assert trans["batch"] == [msg.decode('utf-8')]

            transId = trans['id']
            ledger.updateTip(tipHeight)
            trans['block_height'] = blockHeight
            ledger.updateConfirmingTxMetadata(trans, cardaning.TransactionType.SCHEMA)
            ledger.confirmOrTimeoutDeepTxs(txType=cardaning.TransactionType.SCHEMA)
            confirmingTrans = ledger.getConfirmingTx(transId)
            assert confirmingTrans != None


            # Case: Transaction does not appear after {TRANSACTION_TIMEOUT_DEPTH} blocks
            tipHeight = blockHeight + TRANSACTION_SECURITY_DEPTH - 1
            ledger.updateTip(tipHeight)
            trans['tip'] = tipHeight - TRANSACTION_TIMEOUT_DEPTH - 1
            trans['block_height'] = blockHeight
            ledger.updateConfirmingTxMetadata(trans, txType=cardaning.TransactionType.SCHEMA)
            ledger.confirmOrTimeoutDeepTxs(txType=cardaning.TransactionType.SCHEMA)
            cls.wait_for_updating_utxo()
            ledger.publishEvents(txType=cardaning.TransactionType.SCHEMA)

            confirmingTrans = ledger.getConfirmingTx(transId)
            newTrans = None

            # Load new trans
            for keys, item in ledger.schemasConfirming.getItemIter():
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
            ledger.updateConfirmingTxMetadata(newTrans, txType=cardaning.TransactionType.SCHEMA)
            ledger.updateTip(tipHeight - 1)
            ledger.rollbackToSlot((tipHeight - 2), txType=cardaning.TransactionType.SCHEMA)
            oldTrans = ledger.getConfirmingTx(newTransId)
            cls.wait_for_updating_utxo()
            ledger.publishEvents(txType=cardaning.TransactionType.SCHEMA)
            ledger.confirmOrTimeoutDeepTxs(txType=cardaning.TransactionType.SCHEMA)

            # Load new trans
            for keys, item in ledger.schemasConfirming.getItemIter():
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
            ledger.updateConfirmingTxMetadata(latestTrans, txType=cardaning.TransactionType.SCHEMA)
            ledger.confirmOrTimeoutDeepTxs(txType=cardaning.TransactionType.SCHEMA)
            confirmingTrans = ledger.getConfirmingTx(latestTrans['id'])
            assert confirmingTrans == None