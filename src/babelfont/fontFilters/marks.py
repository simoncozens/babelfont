import logging
from babelfont.Font import Font
from glyphsLib import glyphdata

logger = logging.getLogger(__name__)


def zero_mark_widths(font: Font, args=None):
    logger.info("Zeroing mark widths")
    for glyph in font.glyphs:
        glyphinfo = glyphdata.get_glyph(glyph.name)
        if glyphinfo and not (
            glyphinfo.category == "Mark" and glyphinfo.subCategory == "Nonspacing"
        ):
            continue
        for layer in glyph.layers:
            layer.width = 0
