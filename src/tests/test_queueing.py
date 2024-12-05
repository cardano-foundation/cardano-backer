# -*- encoding: utf-8 -*-
"""
src.tests.test_queueing module

"""
from keri.app import habbing
from keri.core import coring, eventing, serdering
from keri.core import serdering
from backer import queueing, cardaning


def test_push_to_queued():
    salt = b"0123456789abcdef"
    salter = coring.Salter(raw=salt)

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

        serder = serdering.SerderKERI(sad=icp, kind=eventing.Serials.json)
        msg = serder.raw

        ledger = cardaning.Cardano(hab=hab, ks=hab.ks)
        queue = queueing.Queueing(hab=hab, ledger=ledger)
        queue.pushToQueued(serder.pre, msg)

        # Verify push to queue then get serder from keys
        assert ledger.keldb_queued.get((serder.pre, serder.said)).raw == serder.raw
        # Clean up test DB
        ledger.keldb_queued.trim()


def test_publish():
    salt = b"0123456789abcdef"
    salter = coring.Salter(raw=salt)

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

        serder_1 = serdering.SerderKERI(sad=icp, kind=eventing.Serials.json)
        msg_1 = serder_1.raw
        serder_2 = serdering.SerderKERI(sad=rot, kind=eventing.Serials.json)
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
        assert keldb_published[0][1].said == rot['d']
        assert keldb_published[1][1].said == icp['d']
        # Clean up test DB
        ledger.keldb_queued.trim()
        ledger.keldb_published.trim()
