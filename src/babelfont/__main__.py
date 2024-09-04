import argparse
import logging
import sys

from babelfont.convertors import Convert
from babelfont.convertors.truetype import TrueType
from babelfont.fontFilters import FILTERS, parse_filter

LOG_FORMAT = "%(message)s"

logger = logging.getLogger(__name__)


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
    parser.add_argument(
        "--disable-filter",
        help="Filter to disable",
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

    input_job = Convert(args.input)
    convertor_in = input_job.load_convertor()
    if not convertor_in:
        sys.exit(1)

    try:
        logger.info("Reading %s", args.input)
        font = convertor_in.load(input_job, filters=False)
    except Exception as e:
        if args.log_level == "DEBUG":
            raise e
        logger.error("Couldn't read %s: %s", args.input, e)
        sys.exit(1)

    output_job = Convert(args.output)
    convertor_out = output_job.save_convertor()
    if not convertor_out:
        sys.exit(1)

    filters = convertor_in.LOAD_FILTERS
    filters += args.filter or []
    if isinstance(convertor_out, TrueType):
        filters += convertor_in.COMPILE_FILTERS
    filters += convertor_out.SAVE_FILTERS
    if args.disable_filter:
        filters = [f for f in filters if f not in args.disable_filter]

    for filter in filters:
        fltr, filterargs = parse_filter(filter)
        fltr(font, filterargs)

    try:
        logger.info("Saving %s", args.output)
        convertor_out.save(font, output_job)
    except Exception as e:
        logger.error("Couldn't write %s: %s", args.output, e)
        if args.log_level == "DEBUG":
            raise e

        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    sys.exit(main())
