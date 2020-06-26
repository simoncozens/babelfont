#!/usr/bin/python
import argparse
from babelfont import OpenFont

parser = argparse.ArgumentParser(description="Duplicate a glyph")
parser.add_argument("input", metavar="INPUT", help="font file (OTF/TTF/UFO)")
parser.add_argument("existing", metavar="EXISTING", help="existing glyph name")
parser.add_argument("new", metavar="NEW", help="new glyph name")
parser.add_argument(
    "--output", type=str, help="output file (if not given, overwrites input)"
)

options = parser.parse_args()

if not options.output:
    options.output = options.input

font = OpenFont(options.input)
existingGlyph = font.layers[0][options.existing]
newGlyph = font.layers[0].newGlyph(options.new)

for c in existingGlyph.contours:
    newGlyph.appendContour(c)
for c in existingGlyph.components:
    newGlyph.appendComponent(c)

newGlyph.width = existingGlyph.width

font.save(options.output)
