from keri.core import serdering, eventing
from hio.help import Hict
import requests

RECEIPT_ENDPOINT = "http://localhost:5668/receipts"

def test_invalid_event_format():
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

def test_valid_event_format():
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

def test_missing_params():
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