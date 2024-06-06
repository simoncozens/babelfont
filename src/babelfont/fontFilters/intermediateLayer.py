from collections import defaultdict
import logging
from typing import Optional
import uuid

from babelfont.Master import Master
from babelfont.Font import Font
from babelfont.Layer import Layer

logger = logging.getLogger(__name__)


def intermediate_location(l: Layer, f: Font) -> Optional[list[float]]:
    if not l._formatspecific or not l._formatspecific["com.glyphsapp"]:
        return
    attr = l._formatspecific["com.glyphsapp"].get("attr")
    if attr and "coordinates" in attr:
        return {axis.tag: coord for axis, coord in zip(f.axes, attr["coordinates"])}


def promote_intermediate_layers(font: Font, args: dict):
    # Intermediate layers are sparse masters. Find all the intermediate
    # layers with the same point in the designspace, and create a master
    # at that point.
    newmasters = defaultdict(list)

    for glyph in font.glyphs:
        newlayers = []
        for layer in glyph.layers:
            loc = intermediate_location(layer, font)
            if loc:
                newmasters[tuple(loc.items())].append(layer)
            else:
                newlayers.append(layer)
        glyph.layers = newlayers

    if not newmasters:
        return
    logger.info("Promoting intermediate layers to sparse masters")

    for loc_tuple, layers in newmasters.items():
        loc = dict(loc_tuple)
        if any(master.location == loc for master in font.masters):
            glyphs = ", ".join(sorted(layer.glyph.name for layer in layers))
            pl = "s" if len(layers) > 1 else ""
            logger.error(
                f"Glyph{pl} {glyphs} had an 'intermediate' layer at {loc}, but a master already exists"
            )
            continue
        master = Master(name=str(loc), id=str(uuid.uuid1()), location=loc, sparse=True)
        master.font = font
        font.masters.append(master)
        for layer in layers:
            layer._master = master.id
            layer.id = master.id
            del layer._formatspecific["com.glyphsapp"]["attr"]
