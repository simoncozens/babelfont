import logging

from babelfont.Font import Font
from fontTools.misc.timeTools import timestampSinceEpoch
from fontTools.misc.fixedTools import otRound

logger = logging.getLogger(__name__)


def _default(font, table, key, value, round=otRound):
    if (table, key) not in font.custom_opentype_values:
        font.custom_opentype_values[(table, key)] = round(value)
    return font.custom_opentype_values[(table, key)]


def fill_opentype_values(font: Font, args=None):
    """Prepare a font for final compilation by moving values from
    font attributes to the customOpenTypeValues field."""
    logger.info("Filling in OpenType values")

    def _fallback_metric(*metrics):
        for metric in metrics:
            if callable(metric):
                return metric(font)
            if isinstance(metric, (int, float)):
                return metric
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
    ascender = _default(
        font,
        "hhea",
        "ascent",
        _fallback_metric("hheaAscender", "ascender", font.upm * 0.8),
    )
    descender = _default(
        font,
        "hhea",
        "descent",
        _fallback_metric("hheaDescender", "descender", font.upm * -0.2),
    )
    _default(font, "hhea", "lineGap", _fallback_metric("hheaLineGap"))
    _default(font, "OS/2", "usWinAscent", _fallback_metric("winAscent", ascender))
    _default(font, "OS/2", "usWinDescent", _fallback_metric("winDescent", descender))
    # WinDescent should be positive
    if ("OS/2", "usWinDescent") in font.custom_opentype_values:
        font.custom_opentype_values[("OS/2", "usWinDescent")] = abs(
            font.custom_opentype_values[("OS/2", "usWinDescent")]
        )
    _default(font, "OS/2", "sTypoAscender", _fallback_metric("typoAscender", ascender))
    _default(
        font, "OS/2", "sTypoDescender", _fallback_metric("typoDescender", descender)
    )
    _default(
        font,
        "OS/2",
        "sTypoLineGap",
        _fallback_metric("typoLineGap", "lineGap", font.upm * 0.2),
    )
    x_height = _default(
        font, "OS/2", "sxHeight", _fallback_metric("xHeight", font.upm * 0.5)
    )
    _default(font, "OS/2", "sCapHeight", _fallback_metric("capHeight", font.upm * 0.7))
    _default(
        font,
        "OS/2",
        "yStrikeoutPosition",
        _fallback_metric("strikeoutPosition", x_height * 0.6),
    )
    _default(
        font,
        "post",
        "underlinePosition",
        _fallback_metric("underlinePosition", font.upm * -0.075),
    )
    _default(
        font,
        "post",
        "underlineThickness",
        _fallback_metric("underlineThickness", font.upm * 0.05),
    )
    _default(
        font,
        "OS/2",
        "yStrikeoutSize",
        _fallback_metric("underlineThickness", font.upm * 0.05),
    )
