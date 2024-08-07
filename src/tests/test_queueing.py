# -*- encoding: utf-8 -*-
"""
tests.core.test_eventing module

"""
import os

import blake3
import pysodium
import pytest

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

logger = help.ogler.getLogger()



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
