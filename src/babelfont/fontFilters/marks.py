import logging
from babelfont.Font import Font

logger = logging.getLogger(__name__)


def zero_mark_widths(font: Font, args=None):
    logger.info("Zeroing mark widths")
    for glyph in font.glyphs:
        if glyph.category != "mark":
            continue
        for layer in glyph.layers:
            layer.width = 0
