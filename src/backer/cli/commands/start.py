# -*- encoding: utf-8 -*-
"""
KERI
keri.kli.backer module

Backer command line interface
"""
import argparse
import os
import logging
import threading
import time

from keri import __version__
from keri import help
from keri.app import directing, habbing, keeping
from keri.db import subing
from backer import backering, queueing
from backer import cardaning
from backer import crawling
from keri.app.cli.common import existing

d = "Runs KERI backer controller"
parser = argparse.ArgumentParser(description=d)
parser.set_defaults(handler=lambda args: launch(args))
parser.add_argument('-V', '--version',
                    action='version',
                    version=__version__,
                    help="Prints out version of script runner.")
parser.add_argument('-H', '--http',
                    action='store',
                    default=5631,
                    help="Local port number the HTTP server listens on. Default is 5666.")
parser.add_argument('-T', '--tcp',
                    action='store',
                    default=5632,
                    help="Local port number the TCP server listens on. Default is 5665.")
parser.add_argument('-n', '--name',
                    action='store',
                    default="backer",
                    help="Name of controller. Default is backer.")
parser.add_argument('--base', '-b', help='additional optional prefix to file location of KERI keystore',
                    required=False, default="")
parser.add_argument('--alias', '-a', help='human readable alias for the new identifier prefix', required=True)
parser.add_argument('--passcode', '-p', help='22 character encryption passcode for keystore (is not saved)',
                    dest="bran", default=None)  # passcode => bran
parser.add_argument("--loglevel", action="store", required=False, default=os.getenv("BACKER_LOG_LEVEL", "CRITICAL"),
                    help="Set log level to DEBUG | INFO | WARNING | ERROR | CRITICAL. Default is CRITICAL")

def launch(args):
    help.ogler.level = logging.getLevelName(args.loglevel)
    help.ogler.reopen(name=args.name, temp=True, clear=True)

    logger = help.ogler.getLogger()


    logger.info("\n******* Starting Backer for %s listening: http/%s, tcp/%s "
                ".******\n\n", args.name, args.http, args.tcp)

    runBacker(name=args.name,
               base=args.base,
               alias=args.alias,
               bran=args.bran,
               tcp=int(args.tcp),
               http=int(args.http),
               logger=logger)

    logger.info("\n******* Ended Backer for %s listening: http/%s, tcp/%s"
                ".******\n\n", args.name, args.http, args.tcp)


def runBacker(name="backer", base="", alias="backer", bran="", tcp=5665, http=5666, expire=0.0, logger=help.ogler.getLogger()):
    """
    Setup and run one backer
    """

    ks = keeping.Keeper(name=name,
                        base=base,
                        temp=False,
                        reopen=True)

    aeid = ks.gbls.get('aeid')

    if aeid is None:
        hby = habbing.Habery(name=name, base=base, bran=bran)
    else:
        hby = existing.setupHby(name=name, base=base, bran=bran)

    hbyDoer = habbing.HaberyDoer(habery=hby)  # setup doer

    hab = hby.habByName(name=alias)
    if hab is None:
        hab = hby.makeHab(name=alias, transferable=False)

    keldb_queued = subing.Suber(db=hab.db, subkey=cardaning.CardanoDBName.KEL_QUEUED.value)    
    schemadb_queued = subing.Suber(db=hab.db, subkey=cardaning.CardanoDBName.SCHEMA_QUEUED.value)

    ledger = cardaning.Cardano(hab=hab, ks=hab.ks, keldb_queued=keldb_queued, schemadb_queued=schemadb_queued)

    queuer = queueing.Queueing(hab=hab, ledger=ledger)

    backer = backering.setupBacker(alias=alias,
                                   hby=hby,
                                   tcpPort=tcp,
                                   httpPort=http,
                                   keldb_queued=keldb_queued,
                                   schemadb_queued=schemadb_queued)
    crl = crawling.Crawler(ledger=ledger)

    secondaryControllerStop = threading.Event()
    doer_thread = runSecondaryController([crl, queuer], secondaryControllerStop, expire, logger)

    # Run the rest of the doers (e.g., KERI doers) in the main thread as before
    doers = [hbyDoer, *backer]
    directing.runController(doers=doers, expire=expire)

    # When main controller exits, stop the doer thread
    secondaryControllerStop.set()
    doer_thread.join()

def runSecondaryController(doers, secondaryControllerStop=None, expire=0.0, logger=help.ogler.getLogger()):
    """
    Run all doers (e.g., from Crawler and Queueing) in a dedicated thread using a separate directing.runController.
    All ogmios requests and queueing will happen in this thread.
    """
    def doerController():
        try:
            directing.runController(doers=doers, expire=expire)
        except Exception as ex:
            logger.critical(f"Secondary controller encountered an error: {ex}")
        finally:
            if secondaryControllerStop:
                secondaryControllerStop.set()

    thread = threading.Thread(target=doerController, daemon=True)
    thread.start()
    return thread
