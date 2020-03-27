babelfont
~~~~~~~~~

Babelfont allows you to interact with a variety of font formats - UFO,
TTF/OTF with PostScript outlines, and TTF/OTF with TrueType outlines -
without needing to worry about what's going on underneath. It is an
extension to `fontParts <https://fontparts.robotools.dev>`_, on which
it relies for OTF support.

The usual way to interact with TrueType/OpenType fonts is through the
`fonttools <https://github.com/fonttools/fonttools>`_ library; this
provides access to every part of a font, but it does so in a low-level
way which requires the user to not only be familiar with the internal
structure of the font, but to care about the different representations
of information possible within the font.

Babelfont is a bridge between the friendly, high-level interface of
``fontParts`` and the TTF/OTF support of ``fonttools``. It allows you to
do things like this::

    from babelfont import OpenFont
    font = OpenFont("Myfont.otf") # Or TTF. Or UFO...

    glyph = font.layers[0]["space"]
    glyph.width = glyph.width / 2
    font.save("Myfont-halfspace.otf")

Currently you need to save the font in the same format in which you
loaded it - babelfont cannot yet be used for conversion between UFO
and TTF.

For full details of the interface, see
https://fontparts.robotools.dev/en/stable/objectref/objects/font.html