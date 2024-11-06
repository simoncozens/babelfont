import logging
from typing import List

from babelfont.Font import Font
from babelfont.Glyph import GlyphList

logger = logging.getLogger(__name__)


def _replaceFeature(font: Font, value: str):
    tag, code = value.split(";", 1)
    logger.info(f"Replacing feature '{tag}'")
    font.features.features = [
        (key, code if key == tag else value) for key, value in font.features.features
    ]


def _removeFeatures(font: Font, value: List[str]):
    logger.info(f"Removing features '{', '.join(value)}'")
    font.features.features = [
        (key, value) for key, value in font.features.features if key not in value
    ]


def _removeGlyphs(font: Font, value: List[str]):
    logger.info(f"Removing glyphs")
    # for glyph in value:
    #     font.glyphs.pop(glyph)


def _decomposeGlyphs(font: Font, value: List[str]):
    logger.info(f"Decomposing glyphs")
    for glyph in font.glyphs:
        if glyph.name in value:
            # logger.info(f"Decomposing " + glyph.name)
            for layer in glyph.layers:
                layer.decompose()


def _renameGlyphs(font: Font, value: List[str]):
    logger.info(f"Renaming glyphs")
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
                instance.familyName.get_default() + " " + short_instance_name
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
