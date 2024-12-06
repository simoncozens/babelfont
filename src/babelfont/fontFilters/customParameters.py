import logging
from typing import List

from babelfont.Font import Font
from babelfont.Glyph import GlyphList
from .anchorPropagation import _propagate_anchors

logger = logging.getLogger(__name__)


def _replaceFeature(font: Font, value: str):
    tag, code = value.split(";", 1)
    logger.info(f"Replacing feature '{tag}'")
    font.features.features = [
        (key, code if key == tag else value) for key, value in font.features.features
    ]


def _removeFeatures(font: Font, to_remove: List[str]):
    logger.info(f"Removing features '{', '.join(to_remove)}'")
    font.features.features = [
        (key, value) for key, value in font.features.features if key not in to_remove
    ]


def _removeGlyphs(font: Font, value: List[str]):
    logger.info("Removing glyphs")
    for glyph in value:
        font.glyphs[glyph].exported = False


def _decomposeGlyphs(font: Font, value: List[str]):
    logger.info("Decomposing glyphs")
    processed = set()
    for glyph in font.glyphs:
        if glyph.name in value:
            # logger.info(f"Decomposing " + glyph.name)
            for layer in glyph.layers:
                _propagate_anchors(layer, glyph.name, processed)
                layer.decompose()


def _renameGlyphs(font: Font, value: List[str]):
    logger.info("Renaming glyphs")
    for mapping in value:
        oldname, newname = mapping.split("=", 1)
        if newname in font.glyphs and oldname in font.glyphs:
            # Swap any unicode mappings
            (font.glyphs[oldname].codepoints, font.glyphs[newname].codepoints) = (
                font.glyphs[newname].codepoints,
                font.glyphs[oldname].codepoints,
            )
            font.glyphs[newname].name = oldname
            font.glyphs[oldname].name = newname
            font.glyphs = GlyphList({glyph.name: glyph for glyph in font.glyphs})
        swap = {
            newname: oldname,
            oldname: newname,
        }
        for master in font.masters:
            master.kerning = {
                (swap.get(left, left), swap.get(right, right)): kern
                for (left, right), kern in master.kerning.items()
            }
        for group, members in font.first_kern_groups.items():
            font.first_kern_groups[group] = [
                swap.get(member, member) for member in members
            ]
        for group, members in font.second_kern_groups.items():
            font.second_kern_groups[group] = [
                swap.get(member, member) for member in members
            ]


CUSTOM_PARAMETER_APPLIER = {
    "Replace Feature": _replaceFeature,
    "Remove Features": _removeFeatures,
    "Remove Glyphs": _removeGlyphs,
    "Decompose Glyphs": _decomposeGlyphs,
    "Rename Glyphs": _renameGlyphs,
}


def apply_custom_parameters(font: Font, args=None):
    if "instance" in args:
        root = None
        for instance in font.instances:
            short_instance_name = instance.name.get_default()
            long_instance_name = (
                instance.customNames.familyName.get_default()
                + " "
                + short_instance_name
            )
            if args["instance"] in (short_instance_name, long_instance_name):
                root = instance._formatspecific.get("com.glyphsapp", {})
                break
        if not root:
            raise ValueError(f"Instance '{args['instance']}' not found")
    else:
        root = font._formatspecific.get("com.glyphsapp", {})

    for cp in root.get("customParameters", []):
        name = cp.get("name")
        value = cp.get("value")
        if name in CUSTOM_PARAMETER_APPLIER:
            CUSTOM_PARAMETER_APPLIER[name](font, value)
