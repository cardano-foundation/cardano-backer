from keri.app import habbing
from keri.core import coring, serdering, eventing
from hio.help import Hict
import requests


def test_missing_registra_backer():
    salt = b"0123456789abcdef"
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
            "k": ["DCwn62HEdsIbb0Tf-xTTR3fxZMQspc4iNbghK93Tfv1m"],
            "nt": "1",
            "n": ["EDzxxCBaWkzJ2Azn5HS50DZjslp-HMPeG6vGEm4AW168"],
            "bt": "0",
            "b": [],
            "c": [],
            "a": [],
        }

        serder = serdering.SerderKERI(sad=icp, kind=eventing.Serials.json)

        body = serder.raw

        CESR_CONTENT_TYPE = "application/cesr+json"
        CESR_ATTACHMENT_HEADER = "CESR-ATTACHMENT"
        CESR_DESTINATION_HEADER = "CESR-DESTINATION"

        attachment = bytes()

        headers = Hict(
            [
                ("Content-Type", CESR_CONTENT_TYPE),
                ("Content-Length", str(len(body))),
                (CESR_ATTACHMENT_HEADER, attachment),
                (
                    CESR_DESTINATION_HEADER,
                    "BD27gP7-sD8XSr7_tTo54aNIRzPBJGX7GvRUVojfYL2H",
                ),
            ]
        )

        res = requests.request(
            "POST", "http://localhost:5666/", headers=headers, data=body
        )
        assert res.status_code == 400


def test_registra_backer_missing_seal():
    salt = b"0123456789abcdef"
    salter = coring.Salter(raw=salt)

    with habbing.openHby(name="keria", salt=salter.qb64, temp=True) as hby:
        hab = hby.makeHab("test02")
        icp = hab.makeOwnInception()

        icp = {
            "v": "KERI10JSON00012b_",
            "t": "icp",
            "d": "EMgk6GJ8LEIW3VwnUlXNWWz-sGqY-fhQxw6owGLv5bWP",
            "i": "EMgk6GJ8LEIW3VwnUlXNWWz-sGqY-fhQxw6owGLv5bWP",
            "s": "0",
            "kt": "1",
            "k": ["DCwn62HEdsIbb0Tf-xTTR3fxZMQspc4iNbghK93Tfv1m"],
            "nt": "1",
            "n": ["EDzxxCBaWkzJ2Azn5HS50DZjslp-HMPeG6vGEm4AW168"],
            "bt": "0",
            "b": ["REGISTRAR_SEAL_SAID"],
            "c": ["RB"],
            "a": [],
        }

        serder = serdering.SerderKERI(sad=icp, kind=eventing.Serials.json)

        body = serder.raw

        CESR_CONTENT_TYPE = "application/cesr+json"
        CESR_ATTACHMENT_HEADER = "CESR-ATTACHMENT"
        CESR_DESTINATION_HEADER = "CESR-DESTINATION"

        attachment = bytes()

        headers = Hict(
            [
                ("Content-Type", CESR_CONTENT_TYPE),
                ("Content-Length", str(len(body))),
                (CESR_ATTACHMENT_HEADER, attachment),
                (
                    CESR_DESTINATION_HEADER,
                    "BD27gP7-sD8XSr7_tTo54aNIRzPBJGX7GvRUVojfYL2H",
                ),
            ]
        )

        res = requests.request(
            "POST", "http://localhost:5666/", headers=headers, data=body
        )
        assert res.status_code == 400


def test_registra_backer_no_matching_backer_identifier():
    salt = b"0123456789abcdef"
    salter = coring.Salter(raw=salt)

    with habbing.openHby(name="keria", salt=salter.qb64, temp=True) as hby:
        hab = hby.makeHab("test02")
        icp = hab.makeOwnInception()

        icp = {
            "v": "KERI10JSON00012b_",
            "t": "icp",
            "d": "EOWWNh7IT3TzmTiKWs3JQ9YqruZQEEH93M2kN_7LzRUd",
            "i": "EOWWNh7IT3TzmTiKWs3JQ9YqruZQEEH93M2kN_7LzRUd",
            "s": "0",
            "kt": "1",
            "k": ["DCwn62HEdsIbb0Tf-xTTR3fxZMQspc4iNbghK93Tfv1m"],
            "nt": "1",
            "n": ["EDzxxCBaWkzJ2Azn5HS50DZjslp-HMPeG6vGEm4AW168"],
            "bt": "0",
            "b": ["bi"],
            "c": ["RB"],
            "a": [{"bi": "xxbi", "d": "REGISTRAR_SEAL_SAID"}],
        }

        serder = serdering.SerderKERI(sad=icp, kind=eventing.Serials.json)

        body = serder.raw

        CESR_CONTENT_TYPE = "application/cesr+json"
        CESR_ATTACHMENT_HEADER = "CESR-ATTACHMENT"
        CESR_DESTINATION_HEADER = "CESR-DESTINATION"

        attachment = bytes()

        headers = Hict(
            [
                ("Content-Type", CESR_CONTENT_TYPE),
                ("Content-Length", str(len(body))),
                (CESR_ATTACHMENT_HEADER, attachment),
                (
                    CESR_DESTINATION_HEADER,
                    "BD27gP7-sD8XSr7_tTo54aNIRzPBJGX7GvRUVojfYL2H",
                ),
            ]
        )

        res = requests.request(
            "POST", "http://localhost:5666/", headers=headers, data=body
        )
        assert res.status_code == 400


def test_registra_backer_not_matching_seal():
    salt = b"0123456789abcdef"
    salter = coring.Salter(raw=salt)

    with habbing.openHby(name="keria", salt=salter.qb64, temp=True) as hby:
        hab = hby.makeHab("test02")
        icp = hab.makeOwnInception()

        icp = {
            "v": "KERI10JSON00012b_",
            "t": "icp",
            "d": "ELoi_DFk4utHmhGag-K4moVQ3zyXAsjLPCtj7qzAKmpk",
            "i": "ELoi_DFk4utHmhGag-K4moVQ3zyXAsjLPCtj7qzAKmpk",
            "s": "0",
            "kt": "1",
            "k": ["DCwn62HEdsIbb0Tf-xTTR3fxZMQspc4iNbghK93Tfv1m"],
            "nt": "1",
            "n": ["EDzxxCBaWkzJ2Azn5HS50DZjslp-HMPeG6vGEm4AW168"],
            "bt": "0",
            "b": ["bi"],
            "c": ["RB"],
            "a": [{"bi": "bi", "d": "xxREGISTRAR_SEAL_SAID"}],
        }

        serder = serdering.SerderKERI(sad=icp, kind=eventing.Serials.json)

        body = serder.raw

        CESR_CONTENT_TYPE = "application/cesr+json"
        CESR_ATTACHMENT_HEADER = "CESR-ATTACHMENT"
        CESR_DESTINATION_HEADER = "CESR-DESTINATION"

        attachment = bytes()

        headers = Hict(
            [
                ("Content-Type", CESR_CONTENT_TYPE),
                ("Content-Length", str(len(body))),
                (CESR_ATTACHMENT_HEADER, attachment),
                (
                    CESR_DESTINATION_HEADER,
                    "BD27gP7-sD8XSr7_tTo54aNIRzPBJGX7GvRUVojfYL2H",
                ),
            ]
        )

        res = requests.request(
            "POST", "http://localhost:5666/", headers=headers, data=body
        )
        assert res.status_code == 400


def test_registra_backer():
    salt = b"0123456789abcdef"
    salter = coring.Salter(raw=salt)

    with habbing.openHby(name="keria", salt=salter.qb64, temp=True) as hby:
        hab = hby.makeHab("test02")
        icp = hab.makeOwnInception()

        icp = {
            "v": "KERI10JSON00012b_",
            "t": "icp",
            "d": "EO_bl6JM8Y_iBvA2LNBZtECAGkFxCg6w7ksBTBTzuGFJ",
            "i": "EO_bl6JM8Y_iBvA2LNBZtECAGkFxCg6w7ksBTBTzuGFJ",
            "s": "0",
            "kt": "1",
            "k": ["DCwn62HEdsIbb0Tf-xTTR3fxZMQspc4iNbghK93Tfv1m"],
            "nt": "1",
            "n": ["EDzxxCBaWkzJ2Azn5HS50DZjslp-HMPeG6vGEm4AW168"],
            "bt": "0",
            "b": [
                "biAA",
                "biBB"
            ],
            "c": ["RB"],
            "a": [
                {"bi": "biAA", "d": "REGISTRAR_SEAL_SAID"},
                {"bi": "biBB", "d": "REGISTRAR_SEAL_SAID"}
            ],
        }

        serder = serdering.SerderKERI(sad=icp, kind=eventing.Serials.json)

        body = serder.raw

        CESR_CONTENT_TYPE = "application/cesr+json"
        CESR_ATTACHMENT_HEADER = "CESR-ATTACHMENT"
        CESR_DESTINATION_HEADER = "CESR-DESTINATION"

        attachment = bytes()

        headers = Hict(
            [
                ("Content-Type", CESR_CONTENT_TYPE),
                ("Content-Length", str(len(body))),
                (CESR_ATTACHMENT_HEADER, attachment),
                (
                    CESR_DESTINATION_HEADER,
                    "BD27gP7-sD8XSr7_tTo54aNIRzPBJGX7GvRUVojfYL2H",
                ),
            ]
        )

        res = requests.request(
            "POST", "http://localhost:5666/", headers=headers, data=body
        )
        assert res.status_code == 204
