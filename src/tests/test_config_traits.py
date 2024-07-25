import falcon
import pytest
from falcon.testing import helpers
from falcon import testing

from keri.app import habbing, httping, indirecting
from keri.core import coring, serdering, eventing
from keri.vdr import credentialing, verifying
from hio.help import Hict
import requests
from unittest import mock
from unittest.mock import patch, MagicMock, PropertyMock


def test_missing_registra_backer():
    salt = b'0123456789abcdef'
    salter = coring.Salter(raw=salt)

    with habbing.openHby(name="keria", salt=salter.qb64, temp=True) as hby:
        hab = hby.makeHab("test01")
        icp = hab.makeOwnInception()

        icp = {
            "v": "KERI10JSON00012b_",
            "t": "icp",
            "d": "EIvqOceOSGCMW4Ls-Wdi6t4K3RjKZU_DcHC_Q2w2jNs9",
            "i": "EIvqOceOSGCMW4Ls-Wdi6t4K3RjKZU_DcHC_Q2w2jNs9",
            "s": "0",
            "kt": "1",
            "k": [
                "DCwn62HEdsIbb0Tf-xTTR3fxZMQspc4iNbghK93Tfv1m"
            ],
            "nt": "1",
            "n": [
                "EDzxxCBaWkzJ2Azn5HS50DZjslp-HMPeG6vGEm4AW168"
            ],
            "bt": "0",
            "b": [],
            "c": [],
            "a": []
        }

        serder = serdering.SerderKERI(sad=icp, kind=eventing.Serials.json)

        body = serder.raw

        CESR_CONTENT_TYPE = "application/cesr+json"
        CESR_ATTACHMENT_HEADER = "CESR-ATTACHMENT"
        CESR_DESTINATION_HEADER = "CESR-DESTINATION"

        attachment = bytes()

        headers = Hict([
            ("Content-Type", CESR_CONTENT_TYPE),
            ("Content-Length", str(len(body))),
            (CESR_ATTACHMENT_HEADER, attachment),
            (CESR_DESTINATION_HEADER, "BD27gP7-sD8XSr7_tTo54aNIRzPBJGX7GvRUVojfYL2H")
        ])

        res = requests.request("POST", "http://localhost:5666/", headers=headers, data=body)
        assert res.status_code == 400
