import logging

from babelfont import Glyph
from babelfont.Font import Font

logger = logging.getLogger(__name__)


def decompose_mixed_glyphs(font: Font, _args=None):
    logger.info("Decomposing mixed glyphs")

    exportable = set(glyph.name for glyph in font.glyphs if glyph.exported)
    done = set()
    for glyph in font.glyphs:
        decompose_a_glyph(font, glyph, exportable, done)


def decompose_a_glyph(font: Font, glyph: Glyph, exportable, done):
    if glyph.name in done:
        return
    for layer in glyph.layers:
        for c in layer.components:
            decompose_a_glyph(font, font.glyphs[c.ref], exportable, done)
        if (layer.paths and layer.components) or any(
            c.ref not in exportable for c in layer.components
        ):
            layer.decompose()
    done.add(glyph.name)
