# -*- encoding: utf-8 -*-
"""
tests.core.test_eventing module

"""
import os

import blake3
import pysodium
import pytest
import requests

from hio.help import Hict
from keri import kering
from keri.app import habbing, keeping
from keri.app.keeping import openKS, Manager
from keri.core import coring, eventing, parsing, serdering
from keri.core.coring import (Diger, MtrDex, Matter, IdrDex, Indexer,
                              CtrDex, Counter, Salter, Siger, Cigar,
                              Seqner, Verfer, Signer, Prefixer,
                              generateSigners, IdxSigDex, DigDex)
from keri.core.eventing import Kever, Kevery
from keri.core.eventing import (SealDigest, SealRoot, SealBacker,
                                SealEvent, SealLast, StateEvent, StateEstEvent)
from keri.core.eventing import (TraitDex, LastEstLoc, Serials, versify,
                                simple, ample)
from keri.core.eventing import (deWitnessCouple, deReceiptCouple, deSourceCouple,
                                deReceiptTriple,
                                deTransReceiptQuadruple, deTransReceiptQuintuple)
from keri.core.eventing import (incept, rotate, interact, receipt, query,
                                delcept, deltate, state, messagize)
from keri.core import serdering

from keri.db import dbing, basing
from keri.db.basing import openDB
from keri.db.dbing import dgKey, snKey
from keri.kering import (ValidationError, DerivationError, Ilks)

from keri import help
from src.backer import queueing


def test_push_to_queued():
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
        msg = serder.raw

        queue = queueing.Queueing(hab=hab)
        queue.push_to_queued(hab.pre, msg)

        # Verify push to queue then get serder from keys
        assert queue.keldb_queued.get(hab.pre).raw == serder.raw


def test_push_to_queued():
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
        msg = serder.raw

        queue = queueing.Queueing(hab=hab)
        queue.push_to_queued(hab.pre, msg)

        # Verify push to queue then get serder from keys
        assert queue.keldb_queued.get(hab.pre).raw == serder.raw


def test_fetch_push_t():
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
        msg = serder.raw

        queue = queueing.Queueing(hab=hab)
        queue.push_to_queued(hab.pre, msg)

        # Verify keldb_queued had events
        keldb_queued_items = [(pre, serder) for (pre,), serder in queue.keldb_queued.getItemIter()]
        assert keldb_queued_items != []

        queue.publish()

        # Verify keldb_queued published and remove from keldb_queued
        keldb_queued_items = [ (pre, serder) for (pre, ), serder in queue.keldb_queued.getItemIter()]
        assert keldb_queued_items == []

        # Verify event published and keldb_published had events from keldb_queued
        keldb_published = [(pre, serder) for (pre,), serder in queue.keldb_published.getItemIter()]
        assert keldb_published != []


def test_http_call():
    salter = Salter(raw=b'0123456789abcdef')
    vsn = vesn = 0  # sn and last establishment sn = esn
    salter = Salter(raw=b'0123456789abcdef')
    with openDB(name="edy") as db, openKS(name="edy") as ks, habbing.openHby(name="keria", salt=salter.qb64, temp=True) as hby:
        # Init key pair manager
        mgr = Manager(ks=ks, salt=salter.qb64)
        hab = hby.makeHab("test02")

        mgr = Manager(ks=ks, salt=salter.qb64)
        verfers, digers = mgr.incept(icount=1, ncount=0, transferable=True, stem="C")
        #
        # # Test with inception message
        # serder = incept(keys=[verfers[0].qb64], code=MtrDex.Blake3_256)

        qry = hab.query(pre=hab.pre, src=hab.pre, route="/log")
        serder = serdering.SerderKERI(raw=qry)
        # Test with query message
        ked = serder.ked

        sigers = mgr.sign(ser=serder.raw, verfers=verfers)  # default indexed True
        assert isinstance(sigers[0], Siger)
        msg = messagize(serder, sigers=sigers)

        srdr = serdering.SerderKERI(raw=qry)

        qserder = query(route="log",
                        query=dict(i='DAvCLRr5luWmp7keDvDuLP0kIqcyBYq79b3Dho1QvrjI'),
                        stamp=help.helping.DTS_BASE_0)

        msg = qserder.raw

        CESR_CONTENT_TYPE = "application/cesr+json"
        CESR_ATTACHMENT_HEADER = "CESR-ATTACHMENT"
        CESR_DESTINATION_HEADER = "CESR-DESTINATION"

        attachment = b'-VAj-HABEIaGMMWJFPmtXznY1IIiKDIrg-vIyge6mBl2QV8dDjI3-AABAAB6P97k'

        headers = Hict(
            [
                ("Content-Type", CESR_CONTENT_TYPE),
                ("Content-Length", str(len(msg))),
                (CESR_ATTACHMENT_HEADER, attachment),
                (
                    CESR_DESTINATION_HEADER,
                    "BD27gP7-sD8XSr7_tTo54aNIRzPBJGX7GvRUVojfYL2H",
                ),
            ]
        )

        res = requests.request(
            "POST", "http://localhost:5666/", headers=headers, data=msg
        )
        assert res.status_code == 204
