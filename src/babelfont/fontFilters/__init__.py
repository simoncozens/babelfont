from .background import zero_background_width, decompose_backgrounds
from .marks import zero_mark_widths

FILTERS = {
    "zeroBackgroundWidths": zero_background_width,
    "decomposeBackgrounds": decompose_backgrounds,
    "zeroMarkWidths": zero_mark_widths,
}