# Babelfont: Load, examine and save fonts in a variety of formats

*This describes Babelfont >3.0, which is a complete rewrite from the previous version.*

Babelfont is a utility for loading fonts and examining fonts in a variety
of formats. It can also be used to *write* fonts in some of these formats,
making it possible to convert between font formats.

Here are the formats which are currently supported:

| Format         | Read    | Write |
|----------------|---------|-------|
| Glyphs 2       | *       | *     |
| Glyphs 3       | *       | *     |
| .glyphspackage | *       |       |
| UFO            | *       |       |
| Designspace    | *       |       |
| Fontlab VFJ    | partial |       |
| TTF            | partial | *     |
| OTF            | partial |       |
| Babelfont      | *       | *     |

Babelfont converts all of the above font formats into a intermediary
set of objects, whose object hierarchy can be seen [here](https://simoncozens.github.io/babelfont). The allows
the developer to examine any font (single master or variable), without
needing to worry about the details of each font format.

For example:

```python
from babelfont import load

font = load("Myfont.glyphs") # Or .designspace, or whatever
default_a = font.default_master.get_glyph_layer("A")
top_anchor = default_a.anchors_dict["top"].x
print("Top anchor = (%i,%i)" % (top_anchor.x, top_anchor.y))
print("LSB, RSB = (%i,%i)" % (default_a.lsb, default_a.rsb))
font.save("Myfont.ttf")
```
