# -*- encoding: utf-8 -*-
"""
src.tests.test_queueing module

"""
import requests

from hio.help import Hict
from keri.app import habbing
from keri.app.keeping import openKS, Manager
from keri.core import coring, eventing, serdering
from keri.core.coring import (Salter, Siger)
from keri.core.eventing import query
from keri.core import serdering
from keri.db.basing import openDB
from keri import help
from backer import queueing


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

        queue = queueing.Queueing(hab=hab)
        queue.push_to_queued(hab.pre, msg)

        # Verify push to queue then get serder from keys
        assert queue.keldb_queued.get(hab.pre).raw == serder.raw


def test_fetch_push_t():
    salt = b"0123456789abcdef"
    salter = coring.Salter(raw=salt)

    with habbing.openHby(name="keria", salt=salter.qb64, temp=True) as hby:     
        hab = hby.makeHab("test01", transferable=False)
        
        icp_1 = {
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

        icp_2 = {
            "v": "KERI10JSON0000fd_",
            "t": "icp",
            "d": "EP-4PeQ-5j1CG4MW2OrPQWbRcQ53IxEeiwqWP6IfXoom",
            "i": "BCwn62HEdsIbb0Tf-xTTR3fxZMQspc4iNbghK93Tfv1m",
            "s": "0",
            "kt": "1",
            "k": [
                "BCwn62HEdsIbb0Tf-xTTR3fxZMQspc4iNbghK93Tfv1m"
            ],
            "nt": "0",
            "n": [],
            "bt": "0",
            "b": [],
            "c": [],
            "a": []
            }

        serder_1 = serdering.SerderKERI(sad=icp_1, kind=eventing.Serials.json)
        msg_1 = serder_1.raw
        serder_2 = serdering.SerderKERI(sad=icp_2, kind=eventing.Serials.json)
        msg_2 = serder_2.raw

        queue = queueing.Queueing(hab=hab)
        queue.push_to_queued(f"{hab.pre}_1", msg_1)
        queue.push_to_queued(f"{hab.pre}_2", msg_2)

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

    with openDB(name="edy") as db, openKS(name="edy") as ks, habbing.openHby(name="keria", salt=salter.qb64, temp=True) as hby:
        # Init key pair manager
        hab = hby.makeHab("test02")
        mgr = Manager(ks=ks, salt=salter.qb64)
        verfers, _ = mgr.incept(icount=1, ncount=0, transferable=True, stem="C")
        qry = hab.query(pre=hab.pre, src=hab.pre, route="/log")
        serder = serdering.SerderKERI(raw=qry)
        sigers = mgr.sign(ser=serder.raw, verfers=verfers)  # default indexed True
        assert isinstance(sigers[0], Siger)

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
