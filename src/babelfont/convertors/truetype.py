from typing import Dict
import uuid
from datetime import datetime
from itertools import chain

from fontFeatures import Attachment
from fontFeatures.ttLib import unparse
from fontTools.fontBuilder import FontBuilder
from fontTools.misc.fixedTools import otRound
from fontTools.misc.timeTools import epoch_diff, timestampSinceEpoch
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables._g_l_y_f import GlyphCoordinates
from fontTools.ttLib.ttGlyphSet import _TTGlyph
from fontTools.ttLib.tables.TupleVariation import TupleVariation
from fontTools.varLib.iup import iup_delta_optimize

from babelfont.convertors import BaseConvertor
from babelfont.fontFilters.featureWriters import build_all_features
from babelfont import (
    Master,
    Glyph,
    Layer,
    Anchor,
    Shape,
    Node,
    Axis,
    Instance,
    Features,
)


def _categorize_glyph(font, glyphname):
    if "GDEF" not in font:
        return None
    if not font["GDEF"].table.GlyphClassDef:
        return None
    classdefs = font["GDEF"].table.GlyphClassDef.classDefs
    if glyphname not in classdefs:
        return None
    if classdefs[glyphname] == 1:
        return "base"
    if classdefs[glyphname] == 2:
        return "ligature"
    if classdefs[glyphname] == 3:
        return "mark"
    if classdefs[glyphname] == 4:
        return "component"


class TrueType(BaseConvertor):
    suffix = ".ttf"

    def _decompose_mixed_layer(self, layer, exportable):
        if (layer.paths and layer.components) or any(
            c.ref not in exportable for c in layer.components
        ):
            layer.decompose()

    def _load(self):
        self.tt = TTFont(self.filename)
        self._load_fvar()
        self._load_head()
        self._load_masters()
        self._load_names()
        self._load_glyphs()
        self._load_features()
        return self.font

    def _load_fvar(self):
        avar = self.tt.get("avar")
        if "fvar" in self.tt:
            for axis in self.tt["fvar"].axes:
                name = self.tt["name"].getDebugName(axis.axisNameID)  # XXX multilingual
                bb_axis = Axis(
                    tag=axis.axisTag,
                    min=axis.minValue,
                    max=axis.maxValue,
                    default=axis.defaultValue,
                    name=name,
                )
                self.font.axes.append(bb_axis)
                if avar:
                    segs = avar.segments[axis.axisTag]
                    mapping = {
                        bb_axis.denormalize_value(k): bb_axis.denormalize_value(v)
                        for k, v in segs.items()
                    }
                    bb_axis.map = mapping
            for instance in self.tt["fvar"].instances:
                self.font.instances.append(
                    Instance(
                        name=self.tt["name"].getDebugName(instance.subfamilyNameID),
                        location=instance.coordinates,
                    )
                )

    def _load_masters(self):
        m = Master(location={}, name="Default", id=str(uuid.uuid1()))
        # Metrics
        m.metrics = {
            "xHeight": (
                self.tt["OS/2"].sxHeight
                if hasattr(self.tt["OS/2"], "sxHeight")
                else None
            ),
            "capHeight": (
                self.tt["OS/2"].sCapHeight
                if hasattr(self.tt["OS/2"], "capHeight")
                else None
            ),
            "ascender": self.tt["hhea"].ascender,
            "descender": self.tt["hhea"].descender,
        }
        m.font = self.font
        self.font.masters = [m]
        if "fvar" in self.tt:
            m.location = {axis.tag: axis.default for axis in self.font.axes}
            all_masters = [
                frozenset(x.axes.items())
                for x in chain(*self.tt["gvar"].variations.values())
            ]
            all_masters = [{k: v[1] for k, v in dict(m1).items()} for m1 in all_masters]
            # Now denormalize.
            # XXX
            pass

    def _load_head(self):
        head = self.tt["head"]
        self.font.upm = head.unitsPerEm
        minor = head.fontRevision % 1
        while minor - int(minor) > 1e-4:
            minor *= 10
        self.font.version = (int(head.fontRevision), int(minor))
        self.font.date = datetime.fromtimestamp(self.tt["head"].created + epoch_diff)

    def _load_names(self):
        names = self.tt["name"]
        # XXX

    def _load_glyphs(self):
        mapping = self.tt["cmap"].buildReversed()
        glyphs_dict = {}
        for glyph in self.tt.getGlyphOrder():
            category = _categorize_glyph(self.tt, glyph) or "base"
            glyphs_dict[glyph] = Glyph(
                name=glyph, codepoints=list(mapping.get(glyph, [])), category=category
            )
            self.font.glyphs.append(glyphs_dict[glyph])
            glyphs_dict[glyph].layers = self._load_layers(glyph, glyphs_dict[glyph])
        return glyphs_dict

    def _load_layers(self, glyphname, glyph):
        ttglyph = self.tt.getGlyphSet()[glyphname]  # _TTGlyphGlyf object
        width = self.tt["hmtx"][glyphname][0]
        # leftMargin = self.tt["hmtx"][g][1]
        layer = Layer(width=width, id=str(uuid.uuid1()))
        layer._master = self.font.masters[0].id
        layer._font = self.font
        layer._glyph = glyph
        ttglyph.draw(layer.getPen())
        return [layer]

    SAVE_FILTERS = [
        "renameGlyphs:production=True",
        "decomposeMixedGlyphs",
        "dropUnexportedGlyphs",
        "zeroMarkWidths",
        "cubicToQuadratic",
        "fillOpentypeValues",
    ]

    def _save(self):
        f = self.font
        fb = FontBuilder(f.upm, isTTF=True)
        fb.setupGlyphOrder(list(f.glyphs.keys()))
        fb.setupCharacterMap(f.unicode_map)

        metrics = {}
        for g in f.glyphs.keys():
            layer = f.default_master.get_glyph_layer(g)
            metrics[g] = (layer.width or 0, layer.lsb or 0)

        fb.setupHorizontalMetrics(metrics)

        ttglyphsets: Dict[str, Dict[str, _TTGlyph]] = {m.id: {} for m in f.masters}
        # We need to do this in order of single components first
        done = set()

        def convert_glyph(g):
            if g in done:
                return
            for m in f.masters:
                layer = m.get_glyph_layer(g)
                if layer:
                    for c in layer.components:
                        convert_glyph(c.ref)
                    pen = TTGlyphPen(ttglyphsets[m.id])
                    layer.draw(pen)

                    ttglyphsets[m.id][g] = pen.glyph()
            done.add(g)

        for g in f.glyphs.keys():
            convert_glyph(g)

        try:
            fb.setupGlyf(ttglyphsets[f.default_master.id])
        except ValueError:
            fb.font["head"].glyphDataFormat = 1
            self.logger.warning(
                "Using Boring Expansion, eh? Setting glyf data format to 1"
            )
            fb.setupGlyf(ttglyphsets[f.default_master.id])
        fb.setupHorizontalHeader()
        f.names.typographicSubfamily = f.default_master.name
        f.names.typographicFamily = f.names.familyName
        fb.setupNameTable(f.names.as_nametable_dict())
        fb.setupOS2()

        if f.axes:
            model = f.variation_model()
            axis_map = {}
            variations = {}
            for g in f.glyphs.keys():
                variations[g] = self.calculate_a_gvar(f, model, g, ttglyphsets)

            for ax in f.axes:
                ax.name = ax.name.as_fonttools_dict
                axis_map[ax.tag] = ax
            for instance in f.instances:
                instance.location = {
                    k: axis_map[k].map_backward(v) for k, v in instance.location.items()
                }
            fb.setupFvar(f.axes, f.instances)

            fb.setupGvar(variations)
            fb.setupAvar(f.axes)
        build_all_features(f, fb.font)
        fb.setupPost()

        for (table, field), value in f.custom_opentype_values.items():
            setattr(fb.font[table], field, value)
        fb.font.save(self.filename)

    def calculate_a_gvar(
        self, f, model, g, ttglyphsets: Dict[str, Dict[str, _TTGlyph]]
    ):
        if g not in ttglyphsets[f.default_master.id]:
            return None
        default_g = ttglyphsets[f.default_master.id][g]
        all_coords = []
        for m in f.masters:
            layer = m.get_glyph_layer(g)
            masterglyph = ttglyphsets[m.id][g]
            basecoords = GlyphCoordinates(masterglyph.coordinates)
            if masterglyph.isComposite():
                component_point = GlyphCoordinates(
                    [
                        (otRound(layer_comp.pos[0]), otRound(layer_comp.pos[1]))
                        for layer_comp in layer.components
                    ]
                )
                basecoords.extend(component_point)
            phantomcoords = GlyphCoordinates(
                [(0, 0), (otRound(layer.width), 0), (0, 0), (0, 0)]
            )
            basecoords.extend(phantomcoords)
            all_coords.append(basecoords)
        for ix, c in enumerate(all_coords):
            all_ok = True
            if len(c) != len(all_coords[0]):
                print("Incompatible master %i in glyph %s" % (ix, g))
                all_ok = False
            if not all_ok:
                return []
        deltas = model.getDeltas(all_coords)
        gvar_entry = []
        if default_g.isComposite():
            endPts = list(range(len(default_g.components)))
        else:
            endPts = default_g.endPtsOfContours

        for delta, sup in zip(deltas, model.supports):
            if not sup:
                continue
            var = TupleVariation(sup, round(delta))
            # This assumes we do the default master first, which may not be true
            delta_opt = iup_delta_optimize(
                round(delta), round(deltas[0]), endPts, tolerance=0.5
            )
            if None in delta_opt:
                var = TupleVariation(sup, delta_opt)
            gvar_entry.append(var)
        return gvar_entry

    def _load_features(self):
        features = unparse(self.tt)
        # Load anchors
        for routine in features.routines:
            for rule in routine.rules:
                if isinstance(rule, Attachment):
                    for glyphname, pos in rule.bases.items():
                        self._add_anchor(glyphname, pos, rule.base_name)
                    for glyphname, pos in rule.marks.items():
                        self._add_anchor(glyphname, pos, rule.mark_name)

        self.font.features = Features()
        for feature, routines in features.features.items():
            self.font.features.features.append(
                (str(feature), "\n".join(x.asFea() for x in routines))
            )
        for routine in features.routines:
            self.font.features.prefixes[routine.name] = routine.asFea()
        self.font.features.classes = features.namedClasses

    def _add_anchor(self, glyphname, pos, name):
        # Would be nice if this was variable.
        layer = self.font.default_master.get_glyph_layer(glyphname)
        layer.anchors.append(Anchor(name=name, x=pos[0], y=pos[1]))

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


class OpenType(TrueType):
    suffix = ".otf"

    def _load_layers(self, g, _glyph):
        ttglyph = self.tt.getGlyphSet()[g]
        width = self.tt["hmtx"][g][0]
        layer = Layer(width=width, id=self.font.masters[0].id)
        layer._master = self.font.masters[0].id
        layer._font = self.font
        pen = RecordingPen()
        ttglyph.draw(pen)
        contours = pen.value
        lastcontour = []
        startPt = (0, 0)
        lastPt = (0, 0)
        index = 0
        for operation, segment in contours:
            if operation == "moveTo":
                startPt = segment[0]
            elif operation == "closePath":
                if startPt != lastPt:
                    lastcontour.append(Node(x=startPt[0], y=startPt[1], type="l"))
                contour = Shape()
                contour.nodes = lastcontour
                layer.shapes.append(contour)
                lastcontour = []
            elif operation == "curveTo":
                lastcontour.append(Node(x=segment[0][0], y=segment[0][1], type="o"))
                lastcontour.append(Node(x=segment[1][0], y=segment[1][1], type="o"))
                lastcontour.append(Node(x=segment[2][0], y=segment[2][1], type="c"))
                lastPt = segment[2]
            elif operation == "lineTo":
                lastcontour.append(Node(x=segment[0][0], y=segment[0][1], type="l"))
                lastPt = segment[0]
            elif operation == "qCurveTo":
                lastcontour.append(Node(x=segment[0][0], y=segment[0][1], type="o"))
                lastcontour.append(Node(x=segment[1][0], y=segment[1][1], type="q"))

        return [layer]
