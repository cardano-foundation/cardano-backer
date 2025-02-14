# -*- encoding: utf-8 -*-
"""
KERI
keri.app.backering module

class to support registrar backers
"""

import falcon
import time
import keri.app.oobiing

from hio.base import doing
from hio.core import http
from hio.core.tcp import serving
from hio.help import decking
from keri.app import directing, storing, httping, forwarding, oobiing
from keri import help, kering
from keri.core import serdering, eventing, parsing, routing, Counter, Codens, scheming
from keri.core.coring import Ilks
from keri.db import basing, dbing
from keri.end import ending
from keri.peer import exchanging
from keri.vdr import verifying, viring
from keri.vdr.eventing import Tevery

from backer.cardaning import CardanoType

logger = help.ogler.getLogger()


def setupBacker(hby, queue, alias="backer", mbx=None, tcpPort=5631, httpPort=5632):
    """
    Setup Registrar Backer controller and doers

    """
    cues = decking.Deck()
    doers = []

    # make hab
    hab = hby.habByName(name=alias)
    if hab is None:
        hab = hby.makeHab(name=alias, transferable=False)

    reger = viring.Reger(name=hab.name, db=hab.db, temp=False)
    verfer = verifying.Verifier(hby=hby, reger=reger)

    mbx = mbx if mbx is not None else storing.Mailboxer(name=alias, temp=hby.temp)
    forwarder = forwarding.ForwardHandler(hby=hby, mbx=mbx)
    exchanger = exchanging.Exchanger(hby=hby, handlers=[forwarder])
    clienter = httping.Clienter()
    oobiery = keri.app.oobiing.Oobiery(hby=hby, clienter=clienter)

    app = falcon.App(cors_enable=True)
    ending.loadEnds(app=app, hby=hby, default=hab.pre)
    oobiRes = oobiing.loadEnds(app=app, hby=hby, prefix="/ext")
    rep = storing.Respondant(hby=hby, mbx=mbx)

    rvy = routing.Revery(db=hby.db, cues=cues)
    kvy = eventing.Kevery(db=hby.db,
                          lax=True,
                          local=False,
                          rvy=rvy,
                          cues=cues)
    kvy.registerReplyRoutes(router=rvy.rtr)

    tvy = Tevery(reger=verfer.reger,
                 db=hby.db,
                 local=False,
                 cues=cues)

    tvy.registerReplyRoutes(router=rvy.rtr)
    parser = parsing.Parser(framed=True,
                            kvy=kvy,
                            tvy=tvy,
                            exc=exchanger,
                            rvy=rvy)

    httpEnd = HttpEnd(rxbs=parser.ims, mbx=mbx, hab=hab, queue=queue)
    app.add_route("/", httpEnd)

    receiptEnd = ReceiptEnd(hab=hab, queue=queue, inbound=cues)
    app.add_route("/receipts", receiptEnd)

    schemaEnd = SchemaEnd(hab=hab, queue=queue)
    app.add_route("/schemas", schemaEnd)

    server = http.Server(port=httpPort, app=app)
    httpServerDoer = http.ServerDoer(server=server)

    # setup doers
    regDoer = basing.BaserDoer(baser=verfer.reger)

    server = serving.Server(host="", port=tcpPort)
    serverDoer = serving.ServerDoer(server=server)

    directant = directing.Directant(hab=hab, server=server, verifier=verfer)

    witStart = BackerStart(
        hab=hab,
        parser=parser,
        cues=cues,
        kvy=kvy,
        tvy=tvy,
        rvy=rvy,
        exc=exchanger,
        replies=rep.reps,
        responses=rep.cues,
        queries=httpEnd.qrycues)

    doers.extend(oobiRes)
    doers.extend([regDoer, directant, serverDoer, httpServerDoer, rep, witStart, receiptEnd, queue, *oobiery.doers])

    return doers

class BackerStart(doing.DoDoer):
    """ Doer to print backer prefix after initialization

    """

    def __init__(self, hab, parser, kvy, tvy, rvy, exc, cues=None, replies=None, responses=None, queries=None, **opts):
        self.hab = hab
        self.parser = parser
        self.kvy = kvy
        self.tvy = tvy
        self.rvy = rvy
        self.exc = exc
        self.queries = queries if queries is not None else decking.Deck()
        self.replies = replies if replies is not None else decking.Deck()
        self.responses = responses if responses is not None else decking.Deck()
        self.cues = cues if cues is not None else decking.Deck()

        doers = [doing.doify(self.start), doing.doify(self.msgDo),
                 doing.doify(self.escrowDo), doing.doify(self.cueDo)]
        super().__init__(doers=doers, **opts)

    def start(self, tymth=None, tock=0.0):
        """ Prints backer name and prefix

        Parameters:
            tymth (function): injected function wrapper closure returned by .tymen() of
                Tymist instance. Calling tymth() returns associated Tymist .tyme.
            tock (float): injected initial tock value

        """
        self.wind(tymth)
        self.tock = tock
        _ = (yield self.tock)

        while not self.hab.inited:
            yield self.tock

        print("Backer", self.hab.name, "ready", self.hab.pre)

    def msgDo(self, tymth=None, tock=0.0):
        """
        Returns doifiable Doist compatibile generator method (doer dog) to process
            incoming message stream of .kevery

        Parameters:
            tymth (function): injected function wrapper closure returned by .tymen() of
                Tymist instance. Calling tymth() returns associated Tymist .tyme.
            tock (float): injected initial tock value

        Usage:
            add result of doify on this method to doers list
        """
        self.wind(tymth)
        self.tock = tock
        _ = (yield self.tock)

        if self.parser.ims:
            logger.info("Client %s received:\n%s\n...\n", self.kvy, self.parser.ims[:1024])
        done = yield from self.parser.parsator()  # process messages continuously
        return done  # should nover get here except forced close

    def escrowDo(self, tymth=None, tock=0.0):
        """
         Returns doifiable Doist compatibile generator method (doer dog) to process
            .kevery and .tevery escrows.

        Parameters:
            tymth (function): injected function wrapper closure returned by .tymen() of
                Tymist instance. Calling tymth() returns associated Tymist .tyme.
            tock (float): injected initial tock value

        Usage:
            add result of doify on this method to doers list
        """
        self.wind(tymth)
        self.tock = tock
        _ = (yield self.tock)

        while True:
            self.kvy.processEscrows()
            self.rvy.processEscrowReply()
            if self.tvy is not None:
                self.tvy.processEscrows()
            self.exc.processEscrow()

            yield

    def cueDo(self, tymth=None, tock=0.0):
        """
         Returns doifiable Doist compatibile generator method (doer dog) to process
            .kevery.cues deque

        Doist Injected Attributes:
            g.tock = tock  # default tock attributes
            g.done = None  # default done state
            g.opts

        Parameters:
            tymth is injected function wrapper closure returned by .tymen() of
                Tymist instance. Calling tymth() returns associated Tymist .tyme.
            tock is injected initial tock value

        Usage:
            add result of doify on this method to doers list
        """
        self.wind(tymth)
        self.tock = tock
        _ = (yield self.tock)

        while True:
            while self.cues:
                cue = self.cues.popleft()
                cueKin = cue["kin"]
                if cueKin == "stream":
                    self.queries.append(cue)
                else:
                    self.responses.append(cue)
                yield self.tock
            yield self.tock


class HttpEnd:
    """
    HTTP handler that accepts and KERI events POSTed as the body of a request with all attachments to
    the message as a CESR attachment HTTP header.  KEL Messages are processed and added to the database
    of the provided Habitat.

    This also handles `req`, `exn` and `tel` messages that respond with a KEL replay.
    """

    TimeoutQNF = 30
    TimeoutMBX = 5

    def __init__(self, queue, rxbs=None, mbx=None, qrycues=None, hab=None):
        """
        Create the KEL HTTP server from the Habitat with an optional Falcon App to
        register the routes with.

        Parameters
             rxbs (bytearray): output queue of bytes for message processing
             mbx (Mailboxer): Mailbox storage
             qrycues (Deck): inbound qry response queues

        """
        self.rxbs = rxbs if rxbs is not None else bytearray()

        self.mbx = mbx
        self.qrycues = qrycues if qrycues is not None else decking.Deck()
        self.hab = hab
        self.queue = queue

    def on_post(self, req, rep):
        """
        Handles POST for KERI event messages.

        Parameters:
              req (Request) Falcon HTTP request
              rep (Response) Falcon HTTP response

        ---
        summary:  Accept KERI events with attachment headers and parse
        description:  Accept KERI events with attachment headers and parse.
        tags:
           - Events
        requestBody:
           required: true
           content:
             application/json:
               schema:
                 type: object
                 description: KERI event message
        responses:
           200:
              description: Mailbox query response for server sent events
           204:
              description: KEL or EXN event accepted.
        """
        if req.method == "OPTIONS":
            rep.status = falcon.HTTP_200
            return

        rep.set_header('Cache-Control', "no-cache")
        rep.set_header('connection', "close")

        cr = httping.parseCesrHttpRequest(req=req)
        serder = serdering.SerderKERI(sad=cr.payload, kind=eventing.Kinds.json)
        ilk = serder.ked["t"]
        msg = bytearray(serder.raw)
        msg.extend(cr.attachments.encode("utf-8"))
        self.rxbs.extend(msg)

        if ilk in (Ilks.icp, Ilks.rot, Ilks.ixn, Ilks.dip, Ilks.drt, Ilks.exn, Ilks.rpy):
            rep.set_header('Content-Type', "application/json")
            rep.status = falcon.HTTP_204
        elif ilk in (Ilks.vcp, Ilks.vrt, Ilks.iss, Ilks.rev, Ilks.bis, Ilks.brv):
            rep.set_header('Content-Type', "application/json")
            rep.status = falcon.HTTP_204
        elif ilk in (Ilks.qry,):
            if serder.ked["r"] in ("mbx",):
                rep.set_header('Content-Type', "text/event-stream")
                rep.status = falcon.HTTP_200
                rep.stream = QryRpyMailboxIterable(mbx=self.mbx, cues=self.qrycues, said=serder.said, hab=self.hab, queue=self.queue)
            else:
                rep.set_header('Content-Type', "application/json")
                rep.status = falcon.HTTP_204
        print("Post msg received of type", ilk)

class ReceiptEnd(doing.DoDoer):
    """ Endpoint class for Witnessing receipting functionality

     Most times a witness will be able to return its receipt for an event inband.  This API
     will provide that functionality.  When an event needs to be escrowed, this POST API
     will return a 202 and also provides a generic GET API for retrieving a receipt for any
     event.

     """

    def __init__(self, hab, queue, inbound=None, outbound=None, aids=None):
        self.hab = hab
        self.queue = queue
        self.inbound = inbound if inbound is not None else decking.Deck()
        self.outbound = outbound if outbound is not None else decking.Deck()
        self.aids = aids
        self.receipts = set()
        self.psr = parsing.Parser(framed=True,
                                  kvy=self.hab.kvy)

        super(ReceiptEnd, self).__init__(doers=[doing.doify(self.interceptDo)])

    def on_post(self, req, rep):
        """  Receipt POST endpoint handler

        Parameters:
            req (Request): Falcon HTTP request object
            rep (Response): Falcon HTTP response object

        """

        if req.method == "OPTIONS":
            rep.status = falcon.HTTP_200
            return

        rep.set_header('Cache-Control', "no-cache")
        rep.set_header('connection', "close")

        cr = httping.parseCesrHttpRequest(req=req)
        serder = serdering.SerderKERI(sad=cr.payload, kind=eventing.Kinds.json)

        pre = serder.ked["i"]
        if self.aids is not None and pre not in self.aids:
            raise falcon.HTTPBadRequest(description=f"invalid AID={pre} for witnessing receipting")

        ilk = serder.ked["t"]
        if ilk not in (Ilks.icp, Ilks.rot, Ilks.ixn, Ilks.dip, Ilks.drt):
            raise falcon.HTTPBadRequest(description=f"invalid event type ({ilk})for receipting")

        msg = bytearray(serder.raw)
        msg.extend(cr.attachments.encode("utf-8"))

        # Check duplicated event
        existing_said = self.hab.db.getKeLast(key=dbing.snKey(pre=pre,
                                                        sn=serder.sn))

        self.psr.parseOne(ims=bytearray(msg), local=True)

        if pre in self.hab.kevers:
            kever = self.hab.kevers[pre]
            wits = kever.wits

            if self.hab.pre not in wits:
                raise falcon.HTTPBadRequest(description=f"{self.hab.pre} is not a valid witness for {pre} event at "
                                                        f"{serder.sn}: wits={wits}")

            rct = self.hab.receipt(serder)
            self.psr.parseOne(bytes(rct))

            if not existing_said:
                evt = self.hab.db.cloneEvtMsg(pre=serder.pre, fn=0, dig=serder.said)
                self.queue.pushToQueued(serder.pre, bytearray(evt))

            rep.set_header('Content-Type', "application/json+cesr")
            rep.status = falcon.HTTP_200
            rep.data = rct
        else:
            rep.status = falcon.HTTP_202

    def on_get(self, req, rep):
        """  Receipt GET endpoint handler

        Parameters:
            req (Request): Falcon HTTP request object
            rep (Response): Falcon HTTP response object

        """
        pre = req.get_param("pre")
        sn = req.get_param_as_int("sn")
        said = req.get_param("said")

        if pre is None:
            raise falcon.HTTPBadRequest(description="query param 'pre' is required")

        preb = pre.encode("utf-8")

        if sn is None and said is None:
            raise falcon.HTTPBadRequest(description="either 'sn' or 'said' query param is required")

        if sn is not None:
            said = self.hab.db.getKeLast(key=dbing.snKey(pre=preb,
                                                         sn=sn))

        if said is None:
            raise falcon.HTTPNotFound(description=f"event for {pre} at {sn} ({said}) not found")

        said = bytes(said)
        dgkey = dbing.dgKey(preb, said)  # get message
        if not (raw := self.hab.db.getEvt(key=dgkey)):
            raise falcon.HTTPNotFound(description="Missing event for dig={}.".format(said))

        serder = serdering.SerderKERI(raw=bytes(raw))
        if serder.sn > 0:
            wits = [wit.qb64 for wit in self.hab.kvy.fetchWitnessState(pre, serder.sn)]
        else:
            wits = serder.ked["b"]

        if self.hab.pre not in wits:
            raise falcon.HTTPBadRequest(description=f"{self.hab.pre} is not a valid witness for {pre} event at "
                                                    f"{serder.sn}, {wits}")
        rserder = eventing.receipt(pre=pre,
                                   sn=sn,
                                   said=said.decode("utf-8"))
        rct = bytearray(rserder.raw)
        if wigs := self.hab.db.getWigs(key=dgkey):
            rct.extend(Counter(Codens.WitnessIdxSigs, count=len(wigs),
                               gvrsn=kering.Vrsn_1_0).qb64b)
            for wig in wigs:
                rct.extend(wig)

        rep.set_header('Content-Type', "application/json+cesr")
        rep.status = falcon.HTTP_200
        rep.data = rct

    def interceptDo(self, tymth=None, tock=0.0):
        """
         Returns doifiable Doist compatibile generator method (doer dog) to process
            Kevery and Tevery cues deque

        Usage:
            add result of doify on this method to doers list
        """
        # enter context
        self.wind(tymth)
        self.tock = tock
        _ = (yield self.tock)

        while True:
            while self.inbound:  # iteratively process each cue in cues
                cue = self.inbound.popleft()
                cueKin = cue["kin"]  # type or kind of cue

                if cueKin in ("receipt",):  # cue to receipt a received event from other pre
                    serder = cue["serder"]  # Serder of received event for other pre
                    if serder.saidb in self.receipts:
                        self.receipts.remove(serder.saidb)
                    else:
                        self.outbound.append(cue)

                else:
                    self.outbound.append(cue)

                yield self.tock

            yield self.tock

class QryRpyMailboxIterable:

    def __init__(self, cues, mbx, said, queue, retry=5000, hab=None):
        self.mbx = mbx
        self.retry = retry
        self.cues = cues
        self.said = said
        self.iter = None
        self.hab = hab
        self.queue = queue

    def __iter__(self):
        return self

    def __next__(self):
        if self.iter is None:
            if self.cues:
                cue = self.cues.popleft()
                serder = cue["serder"]
                if serder.said == self.said:
                    kin = cue["kin"]
                    if kin == "stream":
                        self.iter = iter(MailboxIterable(mbx=self.mbx, pre=cue["pre"], topics=cue["topics"],
                                                         retry=self.retry, hab=self.hab, queue=self.queue))
                else:
                    self.cues.append(cue)
            return b''

        return next(self.iter)

class MailboxIterable:
    TimeoutMBX = 30000000

    def __init__(self, mbx, pre, topics, queue, retry=5000, hab=None):
        self.mbx = mbx
        self.pre = pre
        self.topics = topics
        self.retry = retry
        self.hab = hab
        self.queue = queue

    def __iter__(self):
        self.start = self.end = time.perf_counter()
        return self

    def __next__(self):
        if self.end - self.start < self.TimeoutMBX:
            if self.start == self.end:
                self.end = time.perf_counter()
                return bytearray(f"retry: {self.retry}\n\n".encode("utf-8"))

            data = bytearray()
            for topic, idx in self.topics.items():
                key = self.pre + topic
                for fn, _, msg in self.mbx.cloneTopicIter(key, idx):
                    data.extend(bytearray("id: {}\nevent: {}\nretry: {}\ndata: ".format(fn, topic, self.retry)
                                          .encode("utf-8")))
                    data.extend(msg)
                    data.extend(b'\n\n')
                    idx = idx + 1
                    self.start = time.perf_counter()

                    if topic == "/receipt":
                        try:
                            self.queue.pushToQueued(self.pre, msg)
                        except Exception as e:
                            logger.error(f"ledger error: {e}")
                self.topics[topic] = idx
            self.end = time.perf_counter()
            return data

        raise StopIteration


class SchemaEnd():
    def __init__(self, hab, queue):
        self.hab = hab
        self.queue = queue

    def on_post(self, req: falcon.Request, rep: falcon.Response):
        if req.method == "OPTIONS":
            rep.status = falcon.HTTP_200
            return

        rep.set_header('Cache-Control', "no-cache")
        rep.set_header('connection', "close")
        data = bytes(req.bounded_stream.read())

        try:
            schemer = scheming.Schemer(raw=data)
            existing_schemer = self.hab.db.schema.get(keys=(schemer.said,))

            if not existing_schemer:
                self.hab.db.schema.pin(keys=(schemer.said,), val=schemer)
                self.queue.pushToQueued("", schemer.raw, CardanoType.SCHEMA)
        except kering.ValidationError as e:
            logger.debug(f"Error parsing schema: {e}")
            raise falcon.HTTPBadRequest(description="Invalid schema")

        rep.status = falcon.HTTP_204
