import logging

from babelfont.Font import Font

logger = logging.getLogger(__name__)


def zero_background_width(font: Font, args=None):
    logger.info("Zeroing background width")
    for glyph in font.glyphs:
        for layer in glyph.layers:
            if layer.isBackground:
                layer.width = 0


def decompose_backgrounds(font: Font, args=None):
    logger.info("Decomposing backgroundss")
    for glyph in font.glyphs:
        for layer in glyph.layers:
            if layer.isBackground:
                layer.decompose()
