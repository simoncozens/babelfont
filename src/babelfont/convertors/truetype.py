from datetime import datetime
from babelfont import *
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from cu2qu.ufo import glyphs_to_quadratic
from fontTools.misc.timeTools import epoch_diff, timestampSinceEpoch
from fontTools.ttLib.ttFont import _TTGlyphGlyf, _TTGlyphSet
from fontTools.ttLib.tables.TupleVariation import TupleVariation
from babelfont.fontFilters.featureWriters import build_all_features
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables._g_l_y_f import GlyphCoordinates
from fontTools.varLib.iup import iup_delta_optimize


class TrueType(BaseConvertor):
    suffix = ".ttf"

    @classmethod
    def can_load(cls, convertor):
        return False  # Not *yet*

    def _decompose_mixed_layer(self, layer, exportable):
        if (layer.paths and layer.components) or any(c.ref not in exportable for c in layer.components):
            layer.decompose()


    def _save(self):
        f = self.font
        fb = FontBuilder(f.upm, isTTF=True)

        metrics = {}
        all_outlines = {}

        # Find all exportable glyphs
        exportable = [ k for k,v in f.glyphs.items() if v.exported ]

        fb.setupGlyphOrder(exportable)
        fb.setupCharacterMap({ k:v for k,v in f.unicode_map.items() if v in exportable})

        for g in exportable:
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
            self._decompose_mixed_layer(layer, exportable)
            for c in layer.components:
                do_a_glyph(c.ref)

            for m in f.masters:
                layer = m.get_glyph_layer(g)
                self._decompose_mixed_layer(layer, exportable)
                all_outlines[g].append(layer)
            try:
                glyphs_to_quadratic(all_outlines[g], reverse_direction=True)
                for ix,m in enumerate(f.masters):
                    layer = m.get_glyph_layer(g)
                    pen = TTGlyphPen(m.ttglyphset)
                    layer.draw(pen)

                    m.ttglyphset._glyphs[g] = pen.glyph()

            except Exception as e:
                print("Problem converting glyph %s to quadratic. (Probably incompatible) " % g)
                for m in f.masters:
                    m.ttglyphset._glyphs[g] = TTGlyphPen(m.ttglyphset).glyph()
            done[g] = True

        for g in exportable:
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
            sTypoAscender=int(f.default_master.ascender),
            sTypoDescender=int(f.default_master.descender),
            sCapHeight=int(f.default_master.capHeight),
            sxHeight=int(f.default_master.xHeight),
        )


        if f.axes:
            model = f.variation_model()
            axis_map = {}
            variations = {}
            for g in exportable:
                variations[g] = self.calculate_a_gvar(f, model, g, metrics[g][0])

            for ax in f.axes:
                ax.name = ax.name.as_fonttools_dict
                axis_map[ax.tag] = ax
            for instance in f.instances:
                instance.location = {k : axis_map[k].map_backward(v) for k,v in instance.location.items() }
            fb.setupFvar(f.axes, f.instances)

            fb.setupGvar(variations)
            fb.setupAvar(f.axes)
        # Move glyph categories to fontfeatures
        for g in f.glyphs.values():
            if g.exported:
                f.features.glyphclasses[g.name] = g.category

        build_all_features(f, fb.font)
        fb.setupPost()

        for table, field, value in f.customOpenTypeValues:
            setattr(fb.font[table], field, value)

        fb.font.save(self.filename)

        # Rename to production
        rename_map = { g.name: g.production_name or g.name for g in f.glyphs }
        if rename_map:
            font = TTFont(self.filename)
            font.setGlyphOrder([rename_map.get(n, n) for n in font.getGlyphOrder()])
            if "post" in font and font["post"].formatType == 2.0:
                font["post"].extraNames = []
                font["post"].compile(font)
            font.save(self.filename)

    def calculate_a_gvar(self, f, model, g, default_width):
        master_layer = f.default_master.get_glyph_layer(g)
        if not g in f.default_master.ttglyphset._glyphs:
            return None
        default_g = f.default_master.ttglyphset._glyphs[g]
        all_coords = []
        for m in f.masters:
            layer = m.get_glyph_layer(g)
            basecoords = GlyphCoordinates(m.ttglyphset._glyphs[g].coordinates)
            if m.ttglyphset._glyphs[g].isComposite():
                component_point = GlyphCoordinates([ (layer_comp.pos[0], layer_comp.pos[1]) for layer_comp in layer.components ])
                basecoords.extend( component_point)
            phantomcoords = GlyphCoordinates([(0,0), (layer.width,0), (0,0), (0,0) ])
            basecoords.extend(phantomcoords)
            all_coords.append(basecoords)
        deltas = model.getDeltas(all_coords)
        gvar_entry = []
        if default_g.isComposite():
            endPts = list(range(len(default_g.components)))
        else:
            endPts = default_g.endPtsOfContours

        for delta, sup in zip(deltas, model.supports):
            if not sup:
                continue
            var = TupleVariation(sup, delta)
            # This assumes we do the default master first, which may not be true
            delta_opt = iup_delta_optimize(delta, deltas[0], endPts, tolerance=0.5)
            if None in delta_opt:
                var = TupleVariation(sup, delta_opt)
            gvar_entry.append(var)
        return gvar_entry

    # import numpy as np
    # def calculate_a_gvar(self, f, model, g, default_width):
    #     if not g in f.default_master.ttglyphset._glyphs:
    #         return None

    #     all_coords = []
    #     master_ix = f.masters.index(f.default_master)

    #     for m in f.masters:
    #         coords = list(m.ttglyphset._glyphs[g].coordinates)
    #         layer = m.get_glyph_layer(g)
    #         if m.ttglyphset._glyphs[g].isComposite():
    #             coords.extend([c.pos for c in layer.components])
    #         coords.extend( [ (0,0), (layer.width,0), (0,0), (0,0) ] )
    #         all_coords.append(np.array(coords))
    #     stacked = np.array(all_coords)
    #     defaults = stacked[np.newaxis,master_ix,:,:].repeat(len(f.masters),axis=0)
    #     base_deltas = stacked-defaults
    #     x_deltas = np.apply_along_axis(model.getDeltas, 1, base_deltas[:,:,0].transpose())
    #     y_deltas = np.apply_along_axis(model.getDeltas, 1, base_deltas[:,:,1].transpose())
    #     alldeltas = np.array([x_deltas, y_deltas]).transpose()
    #     gvar_entry = []
    #     for deltaset, sup in zip(alldeltas, model.supports):
    #         gvar_entry.append(TupleVariation(sup, list(map(tuple, deltaset))))
    #     return gvar_entry
