import logging

from fontTools.cu2qu.ufo import glyphs_to_quadratic

from babelfont.Font import Font


logger = logging.getLogger(__name__)


def cubic_to_quadratic(font: Font, args: dict = {}):
    logger.info("Converting cubic curves to quadratic")
    reverse_direction = args.get("reverseDirection", True)
    for glyph in font.glyphs:
        master_layers = [l for l in glyph.layers if l._master]
        if not master_layers:
            continue
        try:
            glyphs_to_quadratic(master_layers, reverse_direction=reverse_direction)
        except Exception:
            logger.warning(
                "Problem converting glyph %s to quadratic (probably incompatible) ",
                glyph.name,
                # e,
            )
