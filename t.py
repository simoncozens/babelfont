from nfsf.convertors import Convert
from dataclasses import asdict
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.cu2qu.ufo import glyphs_to_quadratic
from fontTools.misc.timeTools import epoch_diff, timestampSinceEpoch
from fontTools.ttLib.ttFont import _TTGlyphGlyf, _TTGlyphSet
from fontTools.ttLib.tables.TupleVariation import TupleVariation
import warnings


def warning_on_one_line(message, category, filename, lineno, file=None, line=None):
    return "# [warning] %s\n" % (message)


warnings.formatwarning = warning_on_one_line

# f = Convert("Truculenta[opsz,wdth,wght].glyphs").load()
# f = Convert("tests/data/GlyphsFileFormatv3.glyphs").load()
f = Convert("/Users/simon/others-repos/Amstelvar/sources/Roman/AmstelvarDB.designspace").load()
# f = Convert("/Users/simon/others-repos/glyphsLib/tests/data/master_ufo/GlyphsUnitTestSans.designspace").load()
# f = Convert("Nunito3.glyphs").load()
f.save("output/test.nfsf")

fb = FontBuilder(f.upm, isTTF=True)
fb.setupGlyphOrder(list(f.glyphs.keys()))
fb.setupCharacterMap(f.unicode_map)

metrics = {}
all_outlines = {}

for g in f.glyphs.keys():
    all_outlines[g] = []
    layer = f.default_master.get_glyph_layer(g)
    metrics[g] = (layer.width, layer.lsb)
fb.setupHorizontalMetrics(metrics)

for m in f.masters:
    glyf = {}
    m.ttglyphset = _TTGlyphSet(fb.font, glyf, _TTGlyphGlyf)


done = {}
def do_a_glyph(g):
    if g in done:
        return
    layer = f.default_master.get_glyph_layer(g)
    for c in layer.components:
        do_a_glyph(c.ref)
    for m in f.masters:
        all_outlines[g].append(m.get_glyph_layer(g))
    glyphs_to_quadratic(all_outlines[g])
    for m in f.masters:
        layer = m.get_glyph_layer(g)
        pen = TTGlyphPen(m.ttglyphset)
        layer.draw(pen)
        m.ttglyphset._glyphs[g] = pen.glyph()

for g in f.glyphs.keys():
    do_a_glyph(g)

fb.updateHead(
    fontRevision=f.version[0]
    + f.version[1] / 10 ** len(str(f.version[1])),
    created=timestampSinceEpoch(f.date.timestamp()),
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
    master_layer = f.default_master.get_glyph_layer(g)
    default_g = f.default_master.ttglyphset._glyphs[g]
    default_width = metrics[g][0]
    all_coords = []
    for ix, m in enumerate(f.masters):
        layer = m.get_glyph_layer(g)
        basedelta = m.ttglyphset._glyphs[g].coordinates - default_g.coordinates
        deltawidth = layer.width - default_width
        for layer_comp, master_comp in zip(layer.components, master_layer.components):
            basedelta.append( (layer_comp.pos[0] - master_comp.pos[0], layer_comp.pos[1] - master_comp.pos[1]))

        phantomdelta = [ (0,0), (deltawidth,0), (0,0), (0,0),  ]
        all_coords.append(list(basedelta) + phantomdelta)
    deltas = []
    for coord in zip(*all_coords):
        x_deltas = model.getDeltas([c[0] for c in coord])
        y_deltas = model.getDeltas([c[1] for c in coord])
        deltas.append(zip(x_deltas, y_deltas))
    variations[g] = []
    for deltaset, sup in zip(zip(*deltas), model.supports):
        variations[g].append(TupleVariation(sup, deltaset))
fb.setupGvar(variations)
fb.setupAvar(f.axes)

fb.setupPost()

fb.font.save("foo.ttf")
