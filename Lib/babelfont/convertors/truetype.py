from datetime import datetime
from babelfont import *
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.cu2qu.ufo import glyphs_to_quadratic
from fontTools.misc.timeTools import epoch_diff, timestampSinceEpoch
from fontTools.ttLib.ttFont import _TTGlyphGlyf, _TTGlyphSet
from fontTools.ttLib.tables.TupleVariation import TupleVariation
from babelfont.fontFilters.featureWriters import build_cursive, build_mark_mkmk

class TrueType(BaseConvertor):
    suffix = ".ttf"

    @classmethod
    def can_load(cls, convertor):
        return False  # Not *yet*

    def _save(self):
        f = self.font
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
            save_components = []
            for m in f.masters:
                layer = m.get_glyph_layer(g)
                all_outlines[g].append(layer)
                save_components.append(layer.components)
            try:
                glyphs_to_quadratic(all_outlines[g])
                for ix,m in enumerate(f.masters):
                    layer = m.get_glyph_layer(g)
                    if save_components[ix]:
                        layer.shapes.extend(save_components[ix])
                    pen = TTGlyphPen(m.ttglyphset)
                    layer.draw(pen)
                    m.ttglyphset._glyphs[g] = pen.glyph()

            except Exception as e:
                print("Problem converting glyph %s to quadratic. (Probably incompatible) " % g)
                for m in f.masters:
                    m.ttglyphset._glyphs[g] = TTGlyphPen(m.ttglyphset).glyph()
            done[g] = True

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

        f.names.typographicSubfamily = f.default_master.name
        f.names.typographicFamily = f.names.familyName
        fb.setupNameTable(f.names.as_nametable_dict())

        fb.setupOS2(
            sTypoAscender=f.default_master.ascender,
            sTypoDescender=f.default_master.descender,
            sCapHeight=f.default_master.capHeight,
            sxHeight=f.default_master.xHeight,
        )

        for ax in f.axes:
            ax.name = ax.name.as_fonttools_dict

        if f.axes:
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
                    if m.ttglyphset._glyphs[g].isComposite():
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
        for table, field, value in f.customOpenTypeValues:
            setattr(fb.font[table], field, value)

        # Move glyph categories to fontfeatures
        for g in f.glyphs.values():
            f.features.glyphclasses[g.name] = g.category
        build_cursive(f)
        build_mark_mkmk(f)
        build_mark_mkmk(f, "mkmk")

        f.features.buildBinaryFeatures(fb.font, f.axes)
        fb.font.save(self.filename)

