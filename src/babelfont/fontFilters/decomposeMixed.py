from babelfont.Font import Font


def decompose_mixed_glyphs(font: Font):
    exportable = set(glyph.name for glyph in font.glyphs if glyph.exported)
    for glyph in font.glyphs:
        for layer in glyph.layers:
            if (layer.paths and layer.components) or any(
                c.ref not in exportable for c in layer.components
            ):
                layer.decompose()
