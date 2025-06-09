# -*- encoding: utf-8 -*-
"""
KERI
keri.kli.backer module

Backer command line interface
"""
import argparse
import os
import logging
from keri import __version__
from keri import help
from keri.app import directing, habbing, keeping
from backer import backering
from keri.app.cli.common import existing
from backer.monitoring import CardanoThreadMonitor

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
              http=int(args.http))

    logger.info("\n******* Ended Backer for %s listening: http/%s, tcp/%s"
                ".******\n\n", args.name, args.http, args.tcp)


def runBacker(name="backer", base="", alias="backer", bran="", tcp=5665, http=5666, expire=0.0):
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

    backer = backering.setupBacker(alias=alias,
                                   hby=hby,
                                   tcpPort=tcp,
                                   httpPort=http)

    # Sets up the Cardano thread with doers, and auto-restarts if it exits
    monitor = CardanoThreadMonitor(hab=hab)

    doers = [hbyDoer, *backer, monitor]
    directing.runController(doers=doers, expire=expire)
