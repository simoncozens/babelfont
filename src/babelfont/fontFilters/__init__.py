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
