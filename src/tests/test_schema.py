import time
import logging
from keri import help
from keri.core import scheming
from hio.help import Hict
from backer import cardaning, backering
from tests.helper import TestEnd, TestBase
from ogmios.client import Client
from tests.helper import DEVNET_OGMIOS_HOST, DEVNET_OGMIOS_PORT

SCHEMA_ROUTE = "/schemas"
class TestSchema(TestBase):
    @classmethod
    def setup_class(cls):
        help.ogler.resetLevel(level=logging.DEBUG, globally=True)
        test_end = TestEnd()
        cls.hby, cls.hab, cls.client, cls.ledger = test_end.make_test_end(SCHEMA_ROUTE, backering.SchemaEnd, type=cardaning.TransactionType.SCHEMA)

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

        res = cls.client.simulate_post(path=SCHEMA_ROUTE, body=schema, headers=headers, content_type=CESR_CONTENT_TYPE)
        assert res.status_code == 400 and "Invalid schema" in str(res.text)


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

        res = cls.client.simulate_post(path=SCHEMA_ROUTE, body=schema, headers=headers, content_type=CESR_CONTENT_TYPE)
        assert res.status_code == 204

        if res.status_code == 204:
                with Client(DEVNET_OGMIOS_HOST, DEVNET_OGMIOS_PORT) as ogmios_client:
                    ledger = cardaning.Cardano(hab=cls.hab, client=ogmios_client)
                    schemer = scheming.Schemer(raw=schema)
                    queued_event = ledger.schemasQueued.get((schemer.said,))
                    queued_schemer = scheming.Schemer(raw=queued_event.encode('utf-8'))

                    assert queued_schemer.said == schemer.said

                    # Wait for schemer to be published
                    timeout = 30
                    start_time = time.time()
                    while True:
                        published_schemer = ledger.schemasPublished.get((schemer.said,))

                        if published_schemer:
                            print("Schemer published")
                            break
                        else:
                            print("Waiting for schemer to be published...")

                        if time.time() - start_time > timeout:
                            print("Timeout")
                            break

                        time.sleep(1)

                    res = cls.client.simulate_post(path=SCHEMA_ROUTE, body=schema, headers=headers, content_type=CESR_CONTENT_TYPE)

                    assert res.status_code == 204
                    # Schemer is not queued again so It is not published again
                    queued_schemer = ledger.kelsQueued.get((schemer.said,))
                    assert queued_schemer == None
