from .background import zero_background_width, decompose_backgrounds
from .marks import zero_mark_widths
from .rename import rename_glyphs
from .dropUnexported import drop_unexported_glyphs
from .decomposeMixed import decompose_mixed_glyphs
from .cu2qu import cubic_to_quadratic

FILTERS = {
    "zeroBackgroundWidths": zero_background_width,
    "decomposeBackgrounds": decompose_backgrounds,
    "zeroMarkWidths": zero_mark_widths,
    "renameGlyphs": rename_glyphs,
    "decomposeMixedGlyphs": decompose_mixed_glyphs,
    "dropUnexportedGlyphs": drop_unexported_glyphs,
    "cubicToQuadratic": cubic_to_quadratic,
}


def parse_filter(input: str) -> [str, dict]:
    if ":" in input:
        filtername, args = input.split(":", 1)
        args = dict([arg.split("=") for arg in args.split(",")])
    else:
        filtername = input
        args = {}
    if filtername not in FILTERS:
        raise ValueError(f"Unknown filter {filtername}")
    return FILTERS[filtername], args
