import logging
import uuid
from collections import defaultdict
from typing import Dict, Optional

from babelfont import Font, Layer, Master

logger = logging.getLogger(__name__)


def promote_intermediate_layers(font: Font, _args: dict):
    # Intermediate layers are sparse masters. To handle intermediate
    # layers, we're going to find all the intermediate layers situated
    # at the same point in the designspace, and create a sparse master
    # at that point.
    additional_masters = defaultdict(list)

    for glyph in font.glyphs:
        newlayers = []
        for layer in glyph.layers:
            if loc := intermediate_location(layer, font):
                additional_masters[tuple(loc.items())].append(layer)
            else:
                newlayers.append(layer)
        glyph.layers = newlayers

    if not additional_masters:
        return
    logger.info("Promoting intermediate layers to sparse masters")

    # Create the masters and associate the layers with them
    for loc_tuple, layers in additional_masters.items():
        loc = dict(loc_tuple)
        if any(master.location == loc for master in font.masters):
            _master_exists_error(loc, layers)
            continue
        master = Master(
            name=str(loc), id=str(uuid.uuid1()), location=loc, sparse=True, font=font
        )
        font.masters.append(master)
        for layer in layers:
            layer._master = master.id
            layer.id = master.id
            # Remove the intermediate coordinate, making it a regular layer
            del layer._formatspecific["com.glyphsapp"]["attr"]["coordinates"]


# We know a layer is "intermediate" if it has a Glyphs-specific attribute
# ["attr"]["coordinates"]. The coordinates are the location of the sparse master;
# just the raw values, so we zip them with the axis tags in order.
def intermediate_location(l: Layer, f: Font) -> Optional[Dict[str, float]]:
    if not l._formatspecific or not l._formatspecific["com.glyphsapp"]:
        return
    attr = l._formatspecific["com.glyphsapp"].get("attr")
    if attr and "coordinates" in attr:
        return {axis.tag: coord for axis, coord in zip(f.axes, attr["coordinates"])}


def _master_exists_error(loc, layers):
    glyphs = ", ".join(sorted(layer.glyph.name for layer in layers))
    pl = "s" if len(layers) > 1 else ""
    logger.error(
        f"Glyph{pl} {glyphs} had an 'intermediate' layer at {loc}, but a master already exists"
    )
