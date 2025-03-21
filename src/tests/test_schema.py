import time
import requests
from keri.core import scheming
from hio.help import Hict
from keri.app.cli.common import existing
from backer import cardaning
from tests.helper import TestBase, BACKER_TEST_STORE_DIR, BACKER_TEST_PORT

RECEIPT_ENDPOINT = f"http://localhost:{BACKER_TEST_PORT}/schemas"

class TestSchema(TestBase):
    def test_invalid_schema_format(cls):

        schema = (b'{"$id":"EMRvS7lGxc1eDleXBkvSHkFs8vUrslRcla6UXOJdccza","$schema":"http://json'
                    b'-schema.org/draft-07/schema#","type":"object","properties":{"a":{"type":"str'
                    b'ing"},"b":{"type":"number"},"c":{"type":"string","format":"date-time"}}}')

        CESR_CONTENT_TYPE = "application/cesr+json"

        headers = Hict(
            [
                ("Content-Type", CESR_CONTENT_TYPE),
                ("Content-Length", str(len(schema)))
            ]
        )

        # Invalid schema format
        res = requests.request(
                "POST", RECEIPT_ENDPOINT, headers=headers, data=schema
            )
        assert res.status_code == 400 and "Invalid schema" in str(res.json())


    def test_valid_schema_format(cls):
        schema = (b'{"$id":"EMRvS7lGxc1eDleXBkvSHkFs8vUrslRcla6UXOJdcczw","$schema":"http://json'
                    b'-schema.org/draft-07/schema#","type":"object","properties":{"a":{"type":"str'
                    b'ing"},"b":{"type":"number"},"c":{"type":"string","format":"date-time"}}}')

        CESR_CONTENT_TYPE = "application/cesr+json"

        headers = Hict(
            [
                ("Content-Type", CESR_CONTENT_TYPE),
                ("Content-Length", str(len(schema)))
            ]
        )

        res = requests.request(
            "POST", RECEIPT_ENDPOINT, headers=headers, data=schema
        )
        assert res.status_code == 204

        if res.status_code == 204:
                name = "backer"
                bran = ""
                alias = "backer"

                hby = existing.setupHby(name=name, base=BACKER_TEST_STORE_DIR, bran=bran)
                hab = hby.habByName(name=alias)
                ledger = cardaning.Cardano(hab=hab, ks=hab.ks)

                schemer = scheming.Schemer(raw=schema)

                queued_event = ledger.schemadb_queued.get((schemer.said, ))
                queued_schemer = scheming.Schemer(raw=queued_event.encode('utf-8'))

                assert queued_schemer.said == schemer.said

                # Wait for schemer to be published
                timeout = 30
                start_time = time.time()
                while True:
                    published_schemer = ledger.schemadb_published.get((schemer.said, ))

                    if published_schemer:
                        print("Schemer published")
                        break
                    else:
                        print("Waiting for schemer to be published...")

                    if time.time() - start_time > timeout:
                        print("Timeout")
                        break

                    time.sleep(1)

                res = requests.request(
                    "POST", RECEIPT_ENDPOINT, headers=headers, data=schema
                )

                assert res.status_code == 204
                # Schemer is not queued again so It is not published again
                queued_schemer = ledger.keldb_queued.get((schemer.said, ))
                assert queued_schemer == None
