from nfsf.convertors import Convert
from dataclasses import asdict
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.cu2qu.ufo import glyphs_to_quadratic
from fontTools.misc.timeTools import epoch_diff, timestampSinceEpoch
from fontTools.ttLib.ttFont import _TTGlyphGlyf, _TTGlyphSet
from fontTools.ttLib.tables.TupleVariation import TupleVariation
import warnings

# f = Convert("Truculenta[opsz,wdth,wght].glyphs").load()
# f = Convert("tests/data/GlyphsFileFormatv3.glyphs").load()
#f = Convert("/Users/simon/others-repos/Amstelvar/sources/Roman/AmstelvarDB.designspace").load()
#f = Convert("/Users/simon/others-repos/glyphsLib/master_ufo/GlyphsUnitTestSans.designspace").load()
f = Convert("Nunito3.glyphs").load()
f.save("output/test.nfsf")

fb = FontBuilder(f.upm, isTTF=True)
fb.setupGlyphOrder(list(f.glyphs.keys()))
fb.setupCharacterMap(f.unicode_map)

metrics = {}
all_outlines = {}
for g in f.glyphs.keys():
    layer = f.default_master.get_glyph_layer(g)
    metrics[g] = (layer.width, layer.lsb)
    all_outlines[g] = []
    for m in f.masters:
        all_outlines[g].append(m.get_glyph_layer(g))

# Now convert to quadratic, all outlines of each glyph at once
for g in f.glyphs.keys():
    glyphs_to_quadratic(all_outlines[g])

fb.setupHorizontalMetrics(metrics)

for m in f.masters:
    glyf = {}
    m.ttglyphset = _TTGlyphSet(fb.font, glyf, _TTGlyphGlyf)

def do_a_glyph(g, master, ttglyphset):
    if g in ttglyphset._glyphs:
        return
    layer = master.get_glyph_layer(g)
    for c in layer.components:
        do_a_glyph(c.ref, master, ttglyphset)
    pen = TTGlyphPen(ttglyphset)
    layer.draw(pen)
    ttglyphset._glyphs[g] = pen.glyph()
    all_outlines[g].append(pen.glyph())

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
    ascent=int(f.default_master.ascender),
    descent=int(f.default_master.descender),
)

fb.setupNameTable(f.names.as_nametable_dict())

for ax in f.axes:
    ax.name = ax.name.as_fonttools_dict

fb.setupFvar(f.axes, f.instances)

# Calculate variations
variations = {}
model = f.variation_model()
for g in f.glyphs.keys():
    default_g = f.default_master.ttglyphset._glyphs[g]
    default_width = metrics[g][0]
    all_coords = []
    for ix, m in enumerate(f.masters):
        basedelta  = m.ttglyphset._glyphs[g].coordinates - default_g.coordinates
        deltawidth = m.get_glyph_layer(g).width - default_width
        phantomdelta = [ (0,0), (deltawidth,0), (0,0), (0,0),  ]
        all_coords.append(list(basedelta) + phantomdelta)
    deltas = []
    for coord in zip(*all_coords):
        x_deltas = model.getDeltas([c[0] for c in coord])
        y_deltas = model.getDeltas([c[1] for c in coord])
        deltas.append(zip(x_deltas, y_deltas))
    variations[g] = []
    for deltaset,sup in zip(zip(*deltas), model.supports):
        variations[g].append(TupleVariation(sup,deltaset))
fb.setupGvar(variations)
fb.setupAvar(f.axes)

fb.setupPost()

fb.font.save("foo.ttf")
