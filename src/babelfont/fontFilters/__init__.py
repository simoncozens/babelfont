from typing import Tuple

from .background import decompose_backgrounds, zero_background_width
from .cu2qu import cubic_to_quadratic
from .customParameters import apply_custom_parameters
from .decomposeMixed import decompose_mixed_glyphs
from .dropUnexported import drop_unexported_glyphs
from .fillOpentype import fill_opentype_values
from .glyphDataXML import bake_in_glyphdata
from .glyphs3fea import translate_glyphs3_fea
from .intermediateLayer import promote_intermediate_layers
from .marks import zero_mark_widths
from .rename import rename_glyphs

FILTERS = {
    "zeroBackgroundWidths": zero_background_width,
    "decomposeBackgrounds": decompose_backgrounds,
    "zeroMarkWidths": zero_mark_widths,
    "renameGlyphs": rename_glyphs,
    "decomposeMixedGlyphs": decompose_mixed_glyphs,
    "dropUnexportedGlyphs": drop_unexported_glyphs,
    "cubicToQuadratic": cubic_to_quadratic,
    "glyphData": bake_in_glyphdata,
    "fillOpentypeValues": fill_opentype_values,
    "intermediateLayers": promote_intermediate_layers,
    "glyphsVariableFeatures": translate_glyphs3_fea,
    "applyCustomParameters": apply_custom_parameters,
}


def parse_filter(input: str) -> Tuple[str, dict]:
    if ":" in input:
        filtername, args = input.split(":", 1)
        args = dict([arg.split("=") for arg in args.split(",")])
    else:
        filtername = input
        args = {}
    if filtername not in FILTERS:
        raise ValueError(f"Unknown filter {filtername}")
    return FILTERS[filtername], args
