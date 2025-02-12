# -*- encoding: utf-8 -*-
"""
src.tests.test_queueing module

"""
import json
from keri.app import habbing
from keri.core import coring, eventing, serdering, Salter, scheming
from backer import queueing, cardaning


def test_push_kel_to_queued():
    salt = b"0123456789abcdef"
    salter = Salter(raw=salt)

    with habbing.openHby(name="keria", salt=salter.qb64, temp=True) as hby:
        hab = hby.makeHab("test01", transferable=False)

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
        queue = queueing.Queueing(hab=hab, ledger=ledger)
        queue.pushToQueued(serder.pre, msg)

        # Verify push to queue then get serder from keys
        assert ledger.keldb_queued.get((serder.pre, serder.said)) == serder.raw.decode('utf-8')
        # Clean up test DB
        ledger.keldb_queued.trim()


def test_publish_kel():
    salt = b"0123456789abcdef"
    salter = Salter(raw=salt)

    with habbing.openHby(name="keria", salt=salter.qb64, temp=True) as hby:
        hab = hby.makeHab("test02", transferable=False)

        icp = {
            "v": "KERI10JSON00012b_",
            "t": "icp",
            "d": "EMUZhB8shDE0I4kSa6Z688320bQwqWP3eZjnRoRJz7vn",
            "i": "EMUZhB8shDE0I4kSa6Z688320bQwqWP3eZjnRoRJz7vn",
            "s": "0",
            "kt": "1",
            "k": [
                "DOVGajHFpHgoXB55a9Yn4fpTOTHGZEEjsxXX034OUmhh"
            ],
            "nt": "1",
            "n": [
                "EOy1p9bw99tDqwLP6pnThrZ2zwKTxZCOqWgwtT6NQ9WY"
            ],
            "bt": "0",
            "b": [],
            "c": [],
            "a": []
        }

        rot = {
            "v": "KERI10JSON000160_",
            "t": "rot",
            "d": "ELC6knkUz5zhhFgXLBaQ9qW0jvJtD1d911f55_nffl2R",
            "i": "EMUZhB8shDE0I4kSa6Z688320bQwqWP3eZjnRoRJz7vn",
            "s": "1",
            "p": "EMUZhB8shDE0I4kSa6Z688320bQwqWP3eZjnRoRJz7vn",
            "kt": "1",
            "k": [
                "DFq9W4cH7BD77m8NJM2XN4iGz6uoGGQb7KklJNM-AQbG"
            ],
            "nt": "1",
            "n": [
                "ELwL_SJ_p4WQGDAqYBjEGYjZvJIdHSXOVULaA7N6lZzZ"
            ],
            "bt": "0",
            "br": [],
            "ba": [],
            "a": []
        }

        serder_1 = serdering.SerderKERI(sad=icp, kind=eventing.Kinds.json)
        msg_1 = serder_1.raw
        serder_2 = serdering.SerderKERI(sad=rot, kind=eventing.Kinds.json)
        msg_2 = serder_2.raw

        ledger = cardaning.Cardano(hab=hab, ks=hab.ks)
        queue = queueing.Queueing(hab=hab, ledger=ledger)
        queue.pushToQueued(serder_1.pre, msg_1)
        queue.pushToQueued(serder_2.pre, msg_2)

        # Verify keldb_queued had events
        keldb_queued_items = [(pre, serder) for (pre, _), serder in ledger.keldb_queued.getItemIter()]
        assert keldb_queued_items != []

        ledger.publishEvents()

        # Verify keldb_queued published and remove from keldb_queued
        keldb_queued_items = [(pre, serder) for (pre, _), serder in ledger.keldb_queued.getItemIter()]
        assert keldb_queued_items == []

        # Verify event published and keldb_published had events from keldb_queued
        keldb_published = [(pre, serder) for (pre, _), serder in ledger.keldb_published.getItemIter()]
        assert keldb_published != []
        serder_1 = serdering.SerderKERI(raw=keldb_published[0][1].encode('utf-8'))
        serder_2 = serdering.SerderKERI(raw=keldb_published[1][1].encode('utf-8'))
        assert serder_1.said == rot['d']
        assert serder_2.said == icp['d']
        # Clean up test DB
        ledger.keldb_queued.trim()
        ledger.keldb_published.trim()

def test_push_schema_to_queued():
    salt = b"0123456789abcdef"
    salter = Salter(raw=salt)

    with habbing.openHby(name="keria", salt=salter.qb64, temp=True) as hby:
        hab = hby.makeHab("test01", transferable=False)

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

        ledger = cardaning.Cardano(hab=hab, ks=hab.ks)
        queue = queueing.Queueing(hab=hab, ledger=ledger)
        queue.pushToQueued("", schemer.raw, cardaning.CardanoType.SCHEMA)

        # Verify push to queue then get schema from keys
        assert ledger.schemadb_queued.get((schemer.said, )) == schemer.raw.decode('utf-8')
        # Clean up test DB
        ledger.schemadb_queued.trim()


def test_publish_schema():
    salt = b"0123456789abcdef"
    salter = Salter(raw=salt)

    with habbing.openHby(name="keria", salt=salter.qb64, temp=True) as hby:
        hab = hby.makeHab("test02", transferable=False)
        schema_1 = {
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
        schema_2 = {
            "$id": "ENQKl3r1Z6HiLXOD-050aVvKziCWJtXWg3vY2FWUGSxG",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "properties": {
                "a": {
                    "type": "object",
                    "properties": {
                        "b": {
                            "type": "number"
                        },
                        "c": {
                            "type": "string",
                            "format": "date-time"
                        }
                    }
                }
            }
        }

        schemer_1 = scheming.Schemer(raw=json.dumps(schema_1).encode('utf-8'))
        schemer_2 = scheming.Schemer(raw=json.dumps(schema_2).encode('utf-8'))
        msg_1 = schemer_1.raw
        msg_2 = schemer_2.raw

        ledger = cardaning.Cardano(hab=hab, ks=hab.ks)
        queue = queueing.Queueing(hab=hab, ledger=ledger)
        queue.pushToQueued("", msg_1, cardaning.CardanoType.SCHEMA)
        queue.pushToQueued("", msg_2, cardaning.CardanoType.SCHEMA)

        # Verify schemadb_queued had events
        schemadb_queued_items = [(said, schemer) for (said, ), schemer in ledger.schemadb_queued.getItemIter()]
        assert schemadb_queued_items != []

        ledger.publishEvents(type=cardaning.CardanoType.SCHEMA)

        # Verify schemadb_queued published and remove from schemadb_queued
        schemadb_queued_items = [(said, schemer) for (said, ), schemer in ledger.schemadb_queued.getItemIter()]
        assert schemadb_queued_items == []

        # Verify event published and schemadb_published had events from schemadb_queued
        schemadb_published = [(said, schemer) for (said, ), schemer in ledger.schemadb_published.getItemIter()]
        assert schemadb_published != []
        print(f"schemadb_published: {schemadb_published}")
        schemer_1 = scheming.Schemer(raw=schemadb_published[0][1].encode('utf-8'))
        schemer_2 = scheming.Schemer(raw=schemadb_published[1][1].encode('utf-8'))
        assert schemer_1.said == schema_1['$id']
        assert schemer_2.said == schema_2['$id']
        # Clean up test DB
        ledger.schemadb_queued.trim()
        ledger.schemadb_published.trim()
