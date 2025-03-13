import os
import time
import requests
from keri.core import eventing, serdering, eventing
from hio.help import Hict
from keri.app.cli.common import existing
from backer import cardaning
from tests.helper import DevnetBase, BACKER_TEST_STORE_DIR, BACKER_TEST_PORT


RECEIPT_ENDPOINT = f"http://localhost:{BACKER_TEST_PORT}/receipts"


class TestReceipt(DevnetBase):
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
                (CESR_ATTACHMENT_HEADER, bytes(attachment)),
                (
                    CESR_DESTINATION_HEADER,
                    "BGKVzj4ve0VSd8z_AmvhLg4lqcC_9WYX90k03q-R_Ydo",
                ),
            ]
        )

        res = requests.request(
                "POST", RECEIPT_ENDPOINT, headers=headers, data=body_data
            )
        assert res.status_code == 500

    def test_event_receipt_200(cls):
            icp = {
                'v': 'KERI10JSON000159_',
                't': 'icp',
                'd': 'EKqG8yMOH-EqppLpsN3RJ_9j5AEJcFt3sEueuain5PR7',
                'i': 'EKqG8yMOH-EqppLpsN3RJ_9j5AEJcFt3sEueuain5PR7',
                's': '0',
                'kt': '1',
                'k': ['DLRMWlQhxgTKppL8KNOEJdQCOByHOh345mnnjtyLUZOF'],
                'nt': '1',
                'n': ['EBYsgaXEITTxpVWneYccdAuOyqTEgmRkB9XRIAcfbaWi'],
                'bt': '1',
                'b': ['BCMSnYpxb4mLrQsSIyi6tNOUplbqiKpwFijU7M9RTU1V'],
                'c': [],
                'a': []
            }
            attachment= bytearray(
                b'-AABAACAM8fcOHux2rpIr-QRZgVhgM4vviiWTcrOlqAcE_Q9PAKv2o7NcHlJwM4XIz0swetgWXOKzQTewKssAZEQMTcL'
            )
            serder = serdering.SerderKERI(sad=icp, kind=eventing.Kinds.json)
            body = serder.raw

            CESR_CONTENT_TYPE = "application/cesr+json"
            CESR_ATTACHMENT_HEADER = "CESR-ATTACHMENT"
            CESR_DESTINATION_HEADER = "CESR-DESTINATION"

            headers = Hict(
                [
                    ("Content-Type", CESR_CONTENT_TYPE),
                    ("Content-Length", str(len(body))),
                    (CESR_ATTACHMENT_HEADER, bytes(attachment)),
                    (
                        CESR_DESTINATION_HEADER,
                        "EKqG8yMOH-EqppLpsN3RJ_9j5AEJcFt3sEueuain5PR7",
                    ),
                ]
            )

            res = requests.request(
                "POST", RECEIPT_ENDPOINT, headers=headers, data=body
            )

            assert res.status_code == 200

            if res.status_code == 200:
                name = "backer"
                bran = ""
                alias = "backer"

                hby = existing.setupHby(name=name, base=BACKER_TEST_STORE_DIR, bran=bran)
                hab = hby.habByName(name=alias)
                ledger = cardaning.Cardano(hab=hab, ks=hab.ks)

                queued_event = ledger.keldb_queued.get((serder.pre, serder.said))
                queued_serder = serdering.SerderKERI(raw=queued_event.encode('utf-8'))

                assert queued_serder.said == serder.said
                assert queued_serder.sn == serder.sn

                # Wait for event to be published
                timeout = 30
                start_time = time.time()
                while True:
                    published_event = ledger.keldb_published.get((serder.pre, serder.said))

                    if published_event:
                        print("Event published")
                        break
                    else:
                        print("Waiting for event to be published...")

                    if time.time() - start_time > timeout:
                        print("Timeout")
                        break

                    time.sleep(1)

                res = requests.request(
                    "POST", RECEIPT_ENDPOINT, headers=headers, data=body
                )

                assert res.status_code == 200
                # Event is not queued again so It is not published again
                queued_event = ledger.keldb_queued.get((serder.pre, serder.said))
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
                (CESR_ATTACHMENT_HEADER, bytes(attachment)),
                (
                    CESR_DESTINATION_HEADER,
                    "BGKVzj4ve0VSd8z_AmvhLg4lqcC_9WYX90k03q-R_Ydo",
                ),
            ]
        )

        res = requests.request(
            "POST", RECEIPT_ENDPOINT, headers=headers, data=body
        )

        assert res.status_code == 202

    def test_missing_params(cls):
        pre = "pre"
        sn = 1
        said = "test"
        res = requests.request(
            "GET", RECEIPT_ENDPOINT, params={"sn": sn, "said": said}
        )
        assert res.status_code == 400 and "query param 'pre' is required" in str(res.json())

        res = requests.request(
            "GET", RECEIPT_ENDPOINT, params={"pre": pre}
        )
        assert res.status_code == 400 and "either 'sn' or 'said' query param is required" in str(res.json())

        res = requests.request(
            "GET", RECEIPT_ENDPOINT, params={"pre": pre, "sn": sn, "said": said}
        )
        assert res.status_code == 404 and "event for pre at 1 (None) not found" in str(res.json())