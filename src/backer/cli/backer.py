# -*- encoding: utf-8 -*-
"""
CARDANO BACKER
backer.cli.commands module
"""
import multicommand
import traceback
from keri import help
from backer.cli import commands

logger = help.ogler.getLogger()


def main():
    parser = multicommand.create_parser(commands)
    args = parser.parse_args()

    if not hasattr(args, 'handler'):
        parser.print_help()
        return

    try:
        args.handler(args)
    except Exception as ex:
        logger.error(f"ERR: {ex}")
        traceback.print_exc()
        return -1


if __name__ == "__main__":
    main()
