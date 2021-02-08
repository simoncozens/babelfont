from nfsf.convertors import Convert
from dataclasses import asdict
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.pens.cu2quPen import Cu2QuPen
from fontTools.misc.timeTools import epoch_diff, timestampSinceEpoch
from fontTools.ttLib.ttFont import _TTGlyphGlyf, _TTGlyphSet
from fontTools.ttLib.tables.TupleVariation import TupleVariation
import warnings

# f = Convert("Truculenta[opsz,wdth,wght].glyphs").load()
f = Convert("Nunito3.glyphs").load()
#f = Convert("/Users/simon/others-repos/Amstelvar/sources/Roman/AmstelvarDB.designspace").load()
#f = Convert("/Users/simon/others-repos/glyphsLib/master_ufo/GlyphsUnitTestSans.designspace").load()
# f.save("output/test.nfsf")

fb = FontBuilder(f.upm, isTTF=True)
fb.setupGlyphOrder(list(f.glyphs.keys()))
fb.setupCharacterMap(f.unicode_map)

metrics = {}

for g in f.glyphs.keys():
    layer = f.default_master.get_glyph_layer(g)
    metrics[g] = (layer.width, layer.lsb)
fb.setupHorizontalMetrics(metrics)

def do_a_glyph(g, master, ttglyphset):
    if g in ttglyphset._glyphs:
        return
    layer = master.get_glyph_layer(g)
    for c in layer.components:
        do_a_glyph(c.ref, master, ttglyphset)

    pen = Cu2QuPen(TTGlyphPen(ttglyphset), 50)
    layer.draw(pen)
    ttglyphset._glyphs[g] = pen.pen.glyph()

for m in f.masters:
    glyf = {}
    m.ttglyphset = _TTGlyphSet(fb.font, glyf, _TTGlyphGlyf)
    for g in f.glyphs.keys():
        do_a_glyph(g, m, m.ttglyphset)

versionMajor =  1
versionMinor =  0
fb.updateHead(
    fontRevision=versionMajor
    + versionMinor / 10 ** len(str(versionMinor)),
    created=timestampSinceEpoch(1234567890),
    lowestRecPPEM=10
)
fb.setupGlyf(f.default_master.ttglyphset._glyphs)
fb.setupHorizontalHeader(
    ascent=int(f.default_master.ascender or 0),
    descent=int(f.default_master.descender or 0),
)

fb.setupNameTable(f.names.as_nametable_dict())

fb.setupFvar(
    [(ax.tag, ax.min, ax.default, ax.max, ax.name) for ax in f.axes],
    []
)

# Calculate variations
variations = {}
for g in f.glyphs.keys():
    default_g = f.default_master.ttglyphset._glyphs[g]
    default_width = metrics[g][0]
    for m in f.masters:
        if m == f.default_master:
            continue
        thislayer = m.get_glyph_layer(g)
        loc = {k:(0,v,1) for k,v in m.normalized_location.items() }

        this_g = m.ttglyphset._glyphs[g]
        if len(this_g.coordinates) != len(default_g.coordinates):
            warnings.warn("Could not interpolate glyph %s in master %s: %i != %i" % (g, m.name, len(this_g.coordinates), len(default_g.coordinates)))
            continue
        coords = this_g.coordinates - default_g.coordinates
        coords.extend([ (0,0), (thislayer.width-default_width,0), (0,0), (0,0) ])
        if g not in variations:
            variations[g] = []
        variations[g].append(TupleVariation(loc, coords))
fb.setupGvar(variations)

fb.setupPost()

fb.font.save("foo.ttf")
