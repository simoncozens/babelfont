from babelfont.Font import Font
from fontTools.misc.timeTools import timestampSinceEpoch


def _default(font, table, key, value):
    if (table, key) not in font.custom_opentype_values:
        font.custom_opentype_values[(table, key)] = value


def fill_opentype_values(font: Font, args=None):
    """Prepare a font for final compilation by moving values from
    font attributes to the customOpenTypeValues field."""

    def _fallback_metric(*metrics):
        for metric in metrics:
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
    _default(font, "hhea", "ascent", _fallback_metric("hheaAscender", "ascender"))
    _default(font, "hhea", "descent", _fallback_metric("hheaDescender", "descender"))
    _default(font, "hhea", "lineGap", _fallback_metric("hheaLineGap"))
    _default(font, "OS/2", "usWinAscent", _fallback_metric("winAscent", "ascender"))
    _default(font, "OS/2", "usWinDescent", _fallback_metric("winDescent", "descender"))
    # WinDescent should be positive
    if ("OS/2", "usWinDescent") in font.custom_opentype_values:
        font.custom_opentype_values[("OS/2", "usWinDescent")] = abs(
            font.custom_opentype_values[("OS/2", "usWinDescent")]
        )
    _default(
        font, "OS/2", "sTypoAscender", _fallback_metric("typoAscender", "ascender")
    )
    _default(
        font, "OS/2", "sTypoDescender", _fallback_metric("typoDescender", "descender")
    )
    _default(font, "OS/2", "sTypoLineGap", _fallback_metric("typoLineGap"))
    _default(font, "OS/2", "sxHeight", _fallback_metric("xHeight"))
    _default(font, "OS/2", "sCapHeight", _fallback_metric("capHeight"))
