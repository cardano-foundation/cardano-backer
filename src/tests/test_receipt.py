import time
import logging
from keri import help
from keri.core import serdering, eventing
from keri.db import dbing
from hio.help import Hict, decking
from backer import cardaning, backering
from tests.helper import TestBase, TestEnd

logger = help.ogler.getLogger()

class TestReceipt(TestBase):
    @classmethod
    def setup_class(cls):
        help.ogler.resetLevel(level=logging.DEBUG, globally=True)
        test_end = TestEnd()
        cls.hby, cls.hab, cls.client, cls.ledger = test_end.make_test_end("/receipts", backering.ReceiptEnd, cues=decking.Deck())

    def test_invalid_event_format(cls):
        body_data = b'{"v":"KERI10JSON000159_","t":"icp","d":"INVALID","i":"EEqgEGTZpJ0MZ_a97VwepTg4IWR9aGEfwXyV0DfJ8x6s","s":"0","kt":"1","k":["DMK1djRX6XJUr2jsCq9XcjoqwVtQyf4HhnyGf37_NiAs"],"nt":"1","n":["EJtfLdgPkiaNohGO6oRRaKEBq66HPV8KFOldSGJC4UYx"],"bt":"1","b":["BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha"],"c":[],"a":[]}'
        attachment= bytearray(
            b'-VAj-HABEIaGMMWJFPmtXznY1IIiKDIrg-vIyge6mBl2QV8dDjI3-AABAAB6P97k'
            b'Z3al3V3z3VstRtHRPeOrotuqZZUgBl2yHzgpGyOjAXYGinVqWLAMhdmQ089FTSAz'
            b'qSTBmJzI8RvIezsJ')
        CESR_CONTENT_TYPE = "application/cesr+json"
        CESR_ATTACHMENT_HEADER = "CESR-ATTACHMENT"
        CESR_DESTINATION_HEADER = "CESR-DESTINATION"
        headers = Hict(
            [
                ("Content-Type", CESR_CONTENT_TYPE),
                ("Content-Length", str(len(body_data))),
                (CESR_ATTACHMENT_HEADER, attachment.decode('utf-8')),
                (
                    CESR_DESTINATION_HEADER,
                    "BGKVzj4ve0VSd8z_AmvhLg4lqcC_9WYX90k03q-R_Ydo",
                ),
            ]
        )
        res = cls.client.simulate_post(path="/receipts", body=body_data, headers=headers, content_type=CESR_CONTENT_TYPE)

        assert res.status_code == 500

    def test_event_receipt_200(cls):
            icp = cls.hab.pre
            # Making valid event for testing
            test_hab = cls.hby.habByName(name='test1')
            if not test_hab:
                test_hab = cls.hby.makeHab(name='test1', wits=[icp], toad=1, transferable=True)
            test_serder, _, _ = test_hab.getOwnEvent(sn=0)
            evt = test_hab.db.cloneEvtMsg(pre=test_serder.pre, fn=0, dig=test_serder.said)
            sigs = evt[len(test_serder.raw):]

            # Delete the old event if it exists
            test_key = dbing.snKey(pre=test_serder.pre, sn=test_serder.sn)
            if cls.hab.db.getKeLast(key=test_key):
                cls.hab.db.delKes(key=test_key)

            # Making request
            CESR_CONTENT_TYPE = "application/cesr+json"
            CESR_ATTACHMENT_HEADER = "CESR-ATTACHMENT"
            CESR_DESTINATION_HEADER = "CESR-DESTINATION"
            headers = Hict(
                [
                    ("Content-Type", CESR_CONTENT_TYPE),
                    ("Content-Length", str(len(test_serder.raw))),
                    (CESR_ATTACHMENT_HEADER, sigs.decode('utf-8')),
                    (
                        CESR_DESTINATION_HEADER,
                        test_serder.pre,
                    ),
                ]
            )

            res = cls.client.simulate_post(path="/receipts", body=test_serder.raw, headers=headers)
            assert res.status_code == 200

            if res.status_code == 200:
                queued_event = cls.ledger.keldb_queued.get((test_serder.pre, test_serder.said))
                queued_serder = serdering.SerderKERI(raw=queued_event.encode('utf-8'))

                # Make sure the KEL is pushed to queue
                assert queued_serder.said == test_serder.said
                assert queued_serder.sn == test_serder.sn

                # Publish the event
                cls.ledger.publishEvents(type=cardaning.CardanoType.KEL)

                # Wait for event to be published
                timeout = 30
                start_time = time.time()
                while True:
                    published_event = cls.ledger.keldb_published.get((test_serder.pre, test_serder.said))

                    if published_event:
                        print("Event published")
                        break
                    else:
                        print("Waiting for event to be published...")

                    if time.time() - start_time > timeout:
                        print("Timeout")
                        break

                    time.sleep(1)

                # Make sure the KEL is pushed to published
                assert published_event == queued_event


    def test_event_receipt_200_duplicated(cls):
            icp = cls.hab.pre
            # Making valid event for testing
            test_hab = cls.hby.habByName(name='test2')
            if not test_hab:
                test_hab = cls.hby.makeHab(name='test2', wits=[icp], toad=1, transferable=True)
            test_serder, _, _ = test_hab.getOwnEvent(sn=0)
            evt = test_hab.db.cloneEvtMsg(pre=test_serder.pre, fn=0, dig=test_serder.said)
            sigs = evt[len(test_serder.raw):]

            # Making request
            CESR_CONTENT_TYPE = "application/cesr+json"
            CESR_ATTACHMENT_HEADER = "CESR-ATTACHMENT"
            CESR_DESTINATION_HEADER = "CESR-DESTINATION"
            headers = Hict(
                [
                    ("Content-Type", CESR_CONTENT_TYPE),
                    ("Content-Length", str(len(test_serder.raw))),
                    (CESR_ATTACHMENT_HEADER, sigs.decode('utf-8')),
                    (
                        CESR_DESTINATION_HEADER,
                        test_serder.pre,
                    ),
                ]
            )

            res = cls.client.simulate_post(path="/receipts", body=test_serder.raw, headers=headers)
            assert res.status_code == 200

            if res.status_code == 200:
                # Event is duplicated so It is not pushed to queue
                queued_event = cls.ledger.keldb_queued.get((test_serder.pre, test_serder.said))
                assert queued_event == None

    def test_event_receipt_202(cls):
        icp = {
            "v": "KERI10JSON000159_",
            "t": "icp",
            "d": "EEqgEGTZpJ0MZ_a97VwepTg4IWR9aGEfwXyV0DfJ8x6s",
            "i": "EEqgEGTZpJ0MZ_a97VwepTg4IWR9aGEfwXyV0DfJ8x6s",
            "s": "0",
            "kt": "1",
            "k": ["DMK1djRX6XJUr2jsCq9XcjoqwVtQyf4HhnyGf37_NiAs"],
            "nt": "1",
            "n": ["EJtfLdgPkiaNohGO6oRRaKEBq66HPV8KFOldSGJC4UYx"],
            "bt": "1",
            "b": ["BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha"],
            "c": [],
            "a": []
        }
        attachment= bytearray(
            b'-VAj-HABEIaGMMWJFPmtXznY1IIiKDIrg-vIyge6mBl2QV8dDjI3-AABAAB6P97k'
            b'Z3al3V3z3VstRtHRPeOrotuqZZUgBl2yHzgpGyOjAXYGinVqWLAMhdmQ089FTSAz'
            b'qSTBmJzI8RvIezsJ')
        serder = serdering.SerderKERI(sad=icp, kind=eventing.Kinds.json)
        body = serder.raw

        CESR_CONTENT_TYPE = "application/cesr+json"
        CESR_ATTACHMENT_HEADER = "CESR-ATTACHMENT"
        CESR_DESTINATION_HEADER = "CESR-DESTINATION"

        headers = Hict(
            [
                ("Content-Type", CESR_CONTENT_TYPE),
                ("Content-Length", str(len(body))),
                (CESR_ATTACHMENT_HEADER, attachment.decode('utf-8')),
                (
                    CESR_DESTINATION_HEADER,
                    "BGKVzj4ve0VSd8z_AmvhLg4lqcC_9WYX90k03q-R_Ydo",
                ),
            ]
        )
        res = cls.client.simulate_post(path="/receipts", body=bytes(body), headers=headers, content_type=CESR_CONTENT_TYPE)

        assert res.status_code == 202

    def test_missing_params(cls):
        pre = "pre"
        sn = 1
        said = "test"
        res = cls.client.simulate_get(path="/receipts", params={"sn": sn, "said": said})
        assert res.status_code == 400 and "query param 'pre' is required" in str(res.text)

        res = cls.client.simulate_get(path="/receipts", params={"pre": pre})
        assert res.status_code == 400 and "either 'sn' or 'said' query param is required" in str(res.text)

        res = cls.client.simulate_get(path="/receipts", params={"pre": pre, "sn": sn, "said": said})
        assert res.status_code == 404 and "event for pre at 1 (None) not found" in str(res.text)