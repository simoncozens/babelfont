import logging

from babelfont.Font import Font
from fontTools.misc.timeTools import timestampSinceEpoch
from fontTools.misc.fixedTools import otRound

logger = logging.getLogger(__name__)


def _default(font, table, key, value, round=otRound):
    if (table, key) not in font.custom_opentype_values:
        font.custom_opentype_values[(table, key)] = round(value)


def fallback_ascender(font):
    return font.upm * 0.8


def fallback_descender(font):
    return font.upm * -0.2


def fallback_cap_height(font):
    return font.upm * 0.7


def fallback_x_height(font):
    return font.upm * 0.5


def fallback_linegap(font):
    return font.upm * 0.2


def fallback_underline_position(font):
    return font.upm * -0.075


def fallback_underline_thickness(font):
    return font.upm * 0.05


def fill_opentype_values(font: Font, args=None):
    """Prepare a font for final compilation by moving values from
    font attributes to the customOpenTypeValues field."""
    logger.info("Filling in OpenType values")

    def _fallback_metric(*metrics):
        for metric in metrics:
            if callable(metric):
                return metric(font)
            if (
                metric in font.default_master.metrics
                and font.default_master.metrics[metric] is not None
            ):
                return int(font.default_master.metrics[metric])
        return 0

    version_decimal = font.version[0] + font.version[1] / 10 ** len(
        str(font.version[1])
    )
    _default(font, "head", "fontRevision", version_decimal)
    _default(font, "head", "created", timestampSinceEpoch(font.date.timestamp()))
    _default(font, "head", "lowestRecPPEM", 10)
    _default(
        font,
        "hhea",
        "ascent",
        _fallback_metric("hheaAscender", "ascender", fallback_ascender),
    )
    _default(
        font,
        "hhea",
        "descent",
        _fallback_metric("hheaDescender", "descender", fallback_descender),
    )
    _default(font, "hhea", "lineGap", _fallback_metric("hheaLineGap"))
    _default(font, "OS/2", "usWinAscent", _fallback_metric("winAscent", "ascender"))
    _default(font, "OS/2", "usWinDescent", _fallback_metric("winDescent", "descender"))
    # WinDescent should be positive
    if ("OS/2", "usWinDescent") in font.custom_opentype_values:
        font.custom_opentype_values[("OS/2", "usWinDescent")] = abs(
            font.custom_opentype_values[("OS/2", "usWinDescent")]
        )
    _default(
        font,
        "OS/2",
        "sTypoAscender",
        _fallback_metric("typoAscender", "ascender", fallback_ascender),
    )
    _default(
        font,
        "OS/2",
        "sTypoDescender",
        _fallback_metric("typoDescender", "descender", fallback_descender),
    )
    _default(
        font,
        "OS/2",
        "sTypoLineGap",
        _fallback_metric("typoLineGap", "lineGap", fallback_linegap),
    )
    _default(font, "OS/2", "sxHeight", _fallback_metric("xHeight", fallback_x_height))
    _default(
        font, "OS/2", "sCapHeight", _fallback_metric("capHeight", fallback_cap_height)
    )
    _default(
        font,
        "post",
        "underlinePosition",
        _fallback_metric("postUnderlinePosition", fallback_underline_position),
    )
    _default(
        font,
        "post",
        "underlineThickness",
        _fallback_metric("postUnderlineThickness", fallback_underline_thickness),
    )
