import logging

from babelfont.Font import Font
from babelfont.Layer import Layer
from babelfont.Anchor import Anchor

logger = logging.getLogger(__name__)


def propagate_anchors(font: Font):
    logger.info("Propagating anchors")
    processed = set()

    for glyph in font.glyphs:
        for layer in glyph.layers:
            _propagate_anchors(layer, glyph.name, processed)


def _propagate_anchors(layer: Layer, glyphname: str, processed: set):
    if layer.id in processed:
        return
    processed.add(layer.id)

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
        _adjust_anchors(to_add, layer, component)

    # we sort propagated anchors to append in a deterministic order
    for name, (x, y) in sorted(to_add.items()):
        layer.anchors.append(Anchor(name=name, x=x, y=y))


def _is_ligature_mark(glyph):
    return not glyph.name.startswith("_") and "_" in glyph.name
