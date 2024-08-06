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
from keri.help import helping

logger = help.ogler.getLogger()


def test_reload_kever(mockHelpingNowUTC):
    """
    Test reload Kever from keystate state message
    """

    with habbing.openHby(name="nat", base="test", salt=coring.Salter(raw=b'0123456789abcdef').qb64) as natHby:
        # setup Nat's habitat using default salt multisig already incepts
        natHab = natHby.makeHab(name="nat", isith='2', icount=3)
        assert natHab.name == 'nat'
        assert natHab.ks == natHby.ks
        assert natHab.db == natHby.db
        assert natHab.kever.prefixer.transferable
        assert natHab.db.opened
        assert natHab.pre in natHab.kevers
        assert natHab.pre in natHab.prefixes
        assert natHab.db.path.endswith("/keri/db/test/nat")
        path = natHab.db.path  # save for later

        # Create series of events for Nat
        natHab.interact()
        natHab.rotate()
        natHab.interact()
        natHab.interact()
        natHab.interact()
        natHab.interact()

        assert natHab.kever.sn == 6
        assert natHab.kever.fn == 6
        assert natHab.kever.serder.said == 'EA3QbTpV15MvLSXHSedm4lRYdQhmYXqXafsD4i75B_yo'
        ldig = bytes(natHab.db.getKeLast(dbing.snKey(natHab.pre, natHab.kever.sn)))
        assert ldig == natHab.kever.serder.saidb
        serder = serdering.SerderKERI(raw=bytes(natHab.db.getEvt(dbing.dgKey(natHab.pre, ldig))))
        assert serder.said == natHab.kever.serder.said
        nstate = natHab.kever.state()

        state =natHab.db.states.get(keys=natHab.pre)  # key state record
        assert state._asjson() == (b'{"vn":[1,0],"i":"EBm9JqQKS4a3EYv5I7BmAPiwhdSQvFAOpqe0dgk3kgH_","s":"6","p":"'
                            b'ED_HpKSCQJoeGxHYjPRD2tgUhbIrLf6fH3e3xJFSq2dL","d":"EA3QbTpV15MvLSXHSedm4lRYd'
                            b'QhmYXqXafsD4i75B_yo","f":"6","dt":"2021-01-01T00:00:00.000000+00:00","et":"i'
                            b'xn","kt":"2","k":["DCORPGaoMtI_RyJFUTIzk0xdza_z6sBQ2e2wzYtEAs3s","DNjSHBbYJa'
                            b'aUKJuPd34n7SRYiZHirwvW-QiHRtfRvBh4","DN-hL9CKn6WdsINEG207T4pSdjaMIxU9SKhfeeH'
                            b'CwfvT"],"nt":"2","n":["EGZ9WHJPgrvDpe08gJpEZ8Gz-rcy72ZG7Tey0PS2CrXY","EO_z0O'
                            b'FTUZ1pmfxj-VnQJcsYFdIVq2tWkN9nUWRxQab_","EMeWMAZpVy7IX6yl4F2t-WoUCaRFZ-0g5dx'
                            b'_LLoEywhx"],"bt":"0","b":[],"c":[],"ee":{"s":"2","d":"EJ7s1vk30hWK_l-exQtzj4'
                            b'P5u_wIzki1drVR4FAKDbEW","br":[],"ba":[]},"di":""}')
        assert state.f == '6'
        assert state == nstate

        # now create new Kever with state
        kever = eventing.Kever(state=state, db=natHby.db)
        assert kever.sn == 6
        assert kever.fn == 6
        assert kever.serder.ked == natHab.kever.serder.ked
        assert kever.serder.said == natHab.kever.serder.said

        kstate = kever.state()
        assert kstate == state
        assert state._asjson() == (b'{"vn":[1,0],"i":"EBm9JqQKS4a3EYv5I7BmAPiwhdSQvFAOpqe0dgk3kgH_","s":"6","p":"'
                            b'ED_HpKSCQJoeGxHYjPRD2tgUhbIrLf6fH3e3xJFSq2dL","d":"EA3QbTpV15MvLSXHSedm4lRYd'
                            b'QhmYXqXafsD4i75B_yo","f":"6","dt":"2021-01-01T00:00:00.000000+00:00","et":"i'
                            b'xn","kt":"2","k":["DCORPGaoMtI_RyJFUTIzk0xdza_z6sBQ2e2wzYtEAs3s","DNjSHBbYJa'
                            b'aUKJuPd34n7SRYiZHirwvW-QiHRtfRvBh4","DN-hL9CKn6WdsINEG207T4pSdjaMIxU9SKhfeeH'
                            b'CwfvT"],"nt":"2","n":["EGZ9WHJPgrvDpe08gJpEZ8Gz-rcy72ZG7Tey0PS2CrXY","EO_z0O'
                            b'FTUZ1pmfxj-VnQJcsYFdIVq2tWkN9nUWRxQab_","EMeWMAZpVy7IX6yl4F2t-WoUCaRFZ-0g5dx'
                            b'_LLoEywhx"],"bt":"0","b":[],"c":[],"ee":{"s":"2","d":"EJ7s1vk30hWK_l-exQtzj4'
                            b'P5u_wIzki1drVR4FAKDbEW","br":[],"ba":[]},"di":""}')

    assert not os.path.exists(natHby.ks.path)
    assert not os.path.exists(natHby.db.path)

    """End Test"""


def test_load_event(mockHelpingNowUTC):
    with habbing.openHby(name="tor", base="test", salt=coring.Salter(raw=b'0123456789abcdef').qb64) as torHby, \
         habbing.openHby(name="wil", base="test", salt=coring.Salter(raw=b'0123456789abcdef').qb64) as wilHby, \
         habbing.openHby(name="wan", base="test", salt=coring.Salter(raw=b'0123456789abcdef').qb64) as wanHby, \
         habbing.openHby(name="tee", base="test", salt=coring.Salter(raw=b'0123456789abcdef').qb64) as teeHby:

        wanKvy = Kevery(db=wanHby.db, lax=False, local=False)
        torKvy = Kevery(db=torHby.db, lax=False, local=False)

        # Create Wan the witness
        wanHab = wanHby.makeHab(name="wan", transferable=False)
        assert wanHab.pre == "BAbSj3jfaeJbpuqg0WtvHw31UoRZOnN_RZQYBwbAqteP"
        msg = wanHab.makeOwnEvent(sn=0)
        parsing.Parser().parse(ims=msg, kvy=torKvy)
        assert wanHab.pre in torKvy.kevers

        # Create Wil the witness, we'll use him later
        wilHab = wilHby.makeHab(name="wil", transferable=False)

        # Create Tor the delegaTOR and pass to witness Wan
        torHab = torHby.makeHab(name="tor", icount=1, isith='1', ncount=1, nsith='1', wits=[wanHab.pre], toad=1)
        assert torHab.pre == "EBOVJXs0trI76PRfvJB2fsZ56PrtyR6HrUT9LOBra8VP"
        torIcp = torHab.makeOwnEvent(sn=0)
        assert torHab.pre in torHab.kvy.kevers

        # Try to load event before Wan has seen it
        with pytest.raises(ValueError):
            _ = eventing.loadEvent(wanHab.db, torHab.pre, torHab.pre)

        # tor events are locallyWitnessed by wan so must process as local
        parsing.Parser().parse(ims=bytearray(torIcp), kvy=wanHab.kvy, local=True) # process as local

        wanHab.processCues(wanHab.kvy.cues)  # process cue returns rct msg
        evt = eventing.loadEvent(wanHab.db, torHab.pre, torHab.pre)
        assert evt == {'ked': {'a': [],
                               'b': ['BAbSj3jfaeJbpuqg0WtvHw31UoRZOnN_RZQYBwbAqteP'],
                               'bt': '1',
                               'c': [],
                               'd': 'EBOVJXs0trI76PRfvJB2fsZ56PrtyR6HrUT9LOBra8VP',
                               'i': 'EBOVJXs0trI76PRfvJB2fsZ56PrtyR6HrUT9LOBra8VP',
                               'k': ['DDgZRj4y6XmkeCsjxLQ-WeAU_U0D3ttTBHW-yicX9hjT'],
                               'kt': '1',
                               'n': ['ED9aiBH7JDgWIgPU1bEXDx8XDFPCWKQilDNyw9W1sCl_'],
                               'nt': '1',
                               's': '0',
                               't': 'icp',
                               'v': 'KERI10JSON000159_'},
                       'receipts': {},
                       'signatures': [{'index': 0,
                                       'signature': 'AAAa36fZASpQeSPn6cEcDMuXRCpDqjXbQ0Q6PqOXB_uktcuANR8rsRdpgB3A87XWeU'
                                                    'QMB0MrWxUE-2bcjq5JJtMP'}],
                       'stored': True,
                       'timestamp': '2021-01-01T00:00:00.000000+00:00',
                       'witness_signatures': [{'index': 0,
                                               'signature': 'AAAU3Kk_Sgd_r4NX4MyE33-eAxM5fUS0WxIyId8YJ-wphNxMT5wI1Mz540'
                                                            'EjYZRkrnty3VfkYhMv-XkGJuY-JWQI'}],
                       'witnesses': ['BAbSj3jfaeJbpuqg0WtvHw31UoRZOnN_RZQYBwbAqteP']}

        # Create Tee the delegaTEE and pass to witness Wan
        teeHab = teeHby.makeHab(name="tee", delpre=torHab.pre, icount=1, isith='1', ncount=1, nsith='1',
                                wits=[wanHab.pre], toad=1)
        assert teeHab.pre == "EDnrWpxagMvr5BBCwCOh3q5M9lvurboZ66vxR-GnIgQo"
        teeIcp = teeHab.makeOwnEvent(sn=0)

        # Anchor Tee's inception event in Tor's KEL
        ixn = torHab.interact(data=[dict(i=teeHab.pre, s='0', d=teeHab.kever.serder.said)])
        parsing.Parser().parse(ims=bytearray(ixn), kvy=wanHab.kvy, local=True)  # give to wan must be local
        wanHab.processCues(wanHab.kvy.cues)  # process cue returns rct msg

        evt = eventing.loadEvent(wanHab.db, torHab.pre, torHab.kever.serder.said)
        assert evt == {'ked': {'a': [{'d': 'EDnrWpxagMvr5BBCwCOh3q5M9lvurboZ66vxR-GnIgQo',
                                      'i': 'EDnrWpxagMvr5BBCwCOh3q5M9lvurboZ66vxR-GnIgQo',
                                      's': '0'}],
                               'd': 'EF7pHYN6XABC9znRdzprt5frW-MMry9rfrCI-_t5Y8VD',
                               'i': 'EBOVJXs0trI76PRfvJB2fsZ56PrtyR6HrUT9LOBra8VP',
                               'p': 'EBOVJXs0trI76PRfvJB2fsZ56PrtyR6HrUT9LOBra8VP',
                               's': '1',
                               't': 'ixn',
                               'v': 'KERI10JSON00013a_'},
                       'receipts': {},
                       'signatures': [{'index': 0,
                                       'signature': 'AABw4jnfadT8aCwyGX2rDtOV8ojW4w4kVehFoJu_p6TzRpsayZ-cibTM_2iZfHVjWx'
                                                    'zcIUbP2ibq6cVbVcOcNHsF'}],
                       'stored': True,
                       'timestamp': '2021-01-01T00:00:00.000000+00:00',
                       'witness_signatures': [{'index': 0,
                                               'signature': 'AABBQIanzXTUfATO36Q_ZzXSE4x2OlxC0MnOuyaUBE4bJhdHhV0f7qPIu5'
                                                            'xClEH2C5AgWgLRPlQ-qo98qJHhIr0B'}],
                       'witnesses': []}

        # Add seal source couple to Tee's inception before sending to Wan
        counter = coring.Counter(code=coring.CtrDex.SealSourceCouples,
                                 count=1)
        teeIcp.extend(counter.qb64b)
        seqner = coring.Seqner(sn=torHab.kever.sn)
        teeIcp.extend(seqner.qb64b)
        teeIcp.extend(torHab.kever.serder.saidb)

        # Endorse Tee's inception event with Tor's Hab just so we have trans receipts
        rct = torHab.receipt(serder=teeHab.kever.serder)
        nrct = wilHab.receipt(serder=teeHab.kever.serder)

        # Now Wan should be ready for Tee's inception
        parsing.Parser().parse(ims=bytearray(teeIcp), kvy=wanKvy, local=True)  # local
        parsing.Parser().parse(ims=bytearray(rct), kvy=wanHab.kvy, local=True) # local
        parsing.Parser().parse(ims=bytearray(nrct), kvy=wanHab.kvy, local=True)  # local
        # ToDo XXXX fix it so cues are durable in db so can process cues from
        # both and remote sources
        wanHab.processCues(wanHab.kvy.cues)  # process cue returns rct msg
        wanHab.processCues(wanKvy.cues)  # process cue returns rct msg

        # Endorse Tee's inception event with Wan's Hab just so we have non-trans receipts

        evt = eventing.loadEvent(wanHab.db, teeHab.pre, teeHab.pre)
        assert evt == {'ked': {'a': [],
                               'b': ['BAbSj3jfaeJbpuqg0WtvHw31UoRZOnN_RZQYBwbAqteP'],
                               'bt': '1',
                               'c': [],
                               'd': 'EDnrWpxagMvr5BBCwCOh3q5M9lvurboZ66vxR-GnIgQo',
                               'di': 'EBOVJXs0trI76PRfvJB2fsZ56PrtyR6HrUT9LOBra8VP',
                               'i': 'EDnrWpxagMvr5BBCwCOh3q5M9lvurboZ66vxR-GnIgQo',
                               'k': ['DLDlVl1H2Q138A5tftVRpyy834ejsY33BB71kXLRNP2h'],
                               'kt': '1',
                               'n': ['EBTtZqMkJOO4nf3cCt6SdezwkoCKtx2fGUKHeFApj_Yx'],
                               'nt': '1',
                               's': '0',
                               't': 'dip',
                               'v': 'KERI10JSON00018d_'},
                       'receipts': {'nontransferable': [{'prefix': 'BEXrSXVksXpnfno_Di6RBX2Lsr9VWRAihjLhowfjNOQQ',
                                                         'signature': '0BCQOeNT3mwAHxh6mYU9K_B2VmbtjJh7_8115k4JrBPR3c4'
                                                                      '3jUSO197H2J73vWMi61qzOovNkSWQbnRx3NFnrk8I'}],
                                    'transferable': [{'prefix': 'EBOVJXs0trI76PRfvJB2fsZ56PrtyR6HrUT9LOBra8VP',
                                                      'said': 'EBOVJXs0trI76PRfvJB2fsZ56PrtyR6HrUT9LOBra8VP',
                                                      'sequence': '0AAAAAAAAAAAAAAAAAAAAAAA',
                                                      'signature': 'AADGbcmUNw_SX7OVNX-PQYl41UZx_pgJXHOoMWrcfmCDGgkc1-'
                                                                   'MqXJjMD9S9moJ-lpPL9-AiXgITemMZL_QYGzIA'}]},
                       'signatures': [{'index': 0,
                                       'signature': 'AAC1-NTntZ0xkgHwooNcKxe9G4XC-rgkSryVz0B_QrZR2kkv4IKi7DMkfMBd4Eck-'
                                                    '2NAi0DMuZeXnlvch6ZP0coO'}],
                       'source_seal': {'said': 'EF7pHYN6XABC9znRdzprt5frW-MMry9rfrCI-_t5Y8VD',
                                       'sequence': 1},
                       'stored': True,
                       'timestamp': '2021-01-01T00:00:00.000000+00:00',
                       'witness_signatures': [{'index': 0,
                                               'signature': 'AABPMW3J1iZyMC-elPOkdIhddhZB_BJYHTdYv5SxcrOfJL_5igDVB6zKD'
                                                            'AQiTj_cNa7oP-l6xSRRxwlHDwqgSwcB'}],
                       'witnesses': ['BAbSj3jfaeJbpuqg0WtvHw31UoRZOnN_RZQYBwbAqteP']}

    """End Test"""


if __name__ == "__main__":
    # pytest.main(['-vv', 'test_eventing.py::test_keyeventfuncs'])
    #test_process_manual()
    #test_keyeventsequence_0()
    #test_process_transferable()
    #test_messagize()
    test_direct_mode()
