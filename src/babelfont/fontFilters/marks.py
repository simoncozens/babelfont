from babelfont.Font import Font
from glyphsLib import glyphdata

def zero_mark_widths(font: Font):
    for glyph in font.glyphs:
        glyphinfo = glyphdata.get_glyph(glyph.name)
        if glyphinfo and not (glyphinfo.category == "Mark" and glyphinfo.subCategory == "Nonspacing"):
            continue
        for layer in glyph.layers:
            layer.width = 0
