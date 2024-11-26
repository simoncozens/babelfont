import logging
from typing import TYPE_CHECKING, Dict, List

from fontTools.misc.transform import Transform

from babelfont.Anchor import Anchor

if TYPE_CHECKING:
    from babelfont import Glyph, Shape, Transform
    from babelfont.Font import Font
    from babelfont.Layer import Layer

logger = logging.getLogger(__name__)


def propagate_anchors(font: "Font", args=None):
    logger.info("Propagating anchors")
    processed = set()

    for glyph in font.glyphs:
        for layer in glyph.layers:
            _propagate_anchors(layer, glyph.name, processed)


def _propagate_anchors(layer: "Layer", glyphname: str, processed: set):
    if layer.isBackground or (glyphname, layer.id) in processed:
        return
    processed.add((glyphname, layer.id))

    base_components = []
    mark_components = []
    anchor_names = set()
    to_add = {}
    for component in layer.components:
        component_layer = component.component_layer
        if not component_layer:
            continue
        _propagate_anchors(component_layer, component.ref, processed)
        if any(a.name.startswith("_") for a in component_layer.anchors):
            mark_components.append(component)
        else:
            base_components.append(component)
            anchor_names |= {a.name for a in component_layer.anchors}

    if mark_components and not base_components and _is_ligature_mark(layer):
        try:
            component = _component_closest_to_origin(mark_components)
        except Exception as e:
            raise ValueError(
                "Error while determining which component of composite "
                "'{}' is the lowest: {}".format(glyphname, str(e))
            ) from e
        mark_components.remove(component)
        base_components.append(component)
        component_layer = component.component_layer
        anchor_names |= {a.name for a in component_layer.anchors}

    for anchor_name in anchor_names:
        # don't add if parent already contains this anchor OR any associated
        # ligature anchors (e.g. "top_1, top_2" for "top")
        if not any(a.name.startswith(anchor_name) for a in layer.anchors):
            _get_anchor_data(to_add, base_components, anchor_name)

    for component in mark_components:
        _adjust_anchors(to_add, component)

    # we sort propagated anchors to append in a deterministic order
    for name, (x, y) in sorted(to_add.items()):
        layer.anchors.append(Anchor(name=name, x=x, y=y))


def _is_ligature_mark(glyph: "Glyph"):
    return not glyph.name.startswith("_") and "_" in glyph.name


def _get_anchor_data(
    anchor_data: Dict[str, tuple], components: List["Shape"], anchor_name: str
):
    """Get data for an anchor from a list of components."""

    anchors = []
    for component in components:
        for anchor in component.component_layer.anchors:
            if anchor.name == anchor_name:
                anchors.append((anchor, component))
                break
    if len(anchors) > 1:
        for i, (anchor, component) in enumerate(anchors):
            t = component.transform
            name = "%s_%d" % (anchor.name, i + 1)
            anchor_data[name] = t.transformPoint((anchor.x, anchor.y))
    elif anchors:
        anchor, component = anchors[0]
        t = component.transform
        anchor_data[anchor.name] = t.transformPoint((anchor.x, anchor.y))


def _adjust_anchors(anchor_data: Dict[str, tuple], component: "Shape"):
    """
    Adjust base anchors to which a mark component may have been attached, by
    moving the base anchor attached to a mark anchor to the position of
    the mark component's base anchor.
    """

    glyph = component.component_layer
    t = component.transform
    for anchor in glyph.anchors:
        # only adjust if this anchor has data and the component also contains
        # the associated mark anchor (e.g. "_top" for "top")
        if anchor.name in anchor_data and any(
            a.name == "_" + anchor.name for a in glyph.anchors
        ):
            anchor_data[anchor.name] = t.transformPoint((anchor.x, anchor.y))


def _component_closest_to_origin(components):
    """Return the component whose (xmin, ymin) bounds are closest to origin.

    This ensures that a component that is moved below another is
    actually recognized as such. Looking only at the transformation
    offset can be misleading.
    """
    return min(
        components, key=lambda comp: _distance((0, 0), comp.component_layer.bounds()[0])
    )


def _distance(pos1, pos2):
    x1, y1 = pos1
    x2, y2 = pos2
    return (x1 - x2) ** 2 + (y1 - y2) ** 2
