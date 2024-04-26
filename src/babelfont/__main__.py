import argparse
import logging
import sys

from babelfont.convertors import Convert
from babelfont.fontFilters import FILTERS, parse_filter

LOG_FORMAT = "%(message)s"


def main():
    parser = argparse.ArgumentParser(
        prog="babelfont", description="Convert between font formats"
    )
    parser.add_argument(
        "--log-level",
        "-l",
        help="Log level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
    )
    parser.add_argument(
        "--filter",
        "-f",
        help="Filter to apply",
        action="append",
        choices=FILTERS.keys(),
    )
    parser.add_argument("input", metavar="IN", help="Input file")
    parser.add_argument("output", metavar="OUT", help="Output file")
    args = parser.parse_args()

    try:
        from rich.logging import RichHandler

        handlers = [RichHandler()]
    except ImportError:
        handlers = [logging.StreamHandler()]

    logging.basicConfig(
        level=args.log_level, format=LOG_FORMAT, datefmt="[%X]", handlers=handlers
    )

    try:
        font = Convert(args.input).load()
    except Exception as e:
        print("Couldn't read %s: %s" % (args.input, e))
        raise e
        sys.exit(1)

    for filter in args.filter or []:
        fltr, filterargs = parse_filter(filter)
        fltr(font, filterargs)

    try:
        Convert(args.output).save(font)
    except Exception as e:
        print("Couldn't write %s: %s" % (args.output, e))
        raise e
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    sys.exit(main())
