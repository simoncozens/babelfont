from babelfont.Font import Font

def zero_background_width(font: Font):
    for glyph in font.glyphs:
        for layer in glyph.layers:
            if layer.isBackground:
                layer.width = 0

def decompose_backgrounds(font: Font):
    for glyph in font.glyphs:
        for layer in glyph.layers:
            if layer.isBackground:
                layer.decompose()