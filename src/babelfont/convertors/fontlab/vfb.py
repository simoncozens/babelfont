from collections import defaultdict
import re
import json
import uuid

from vfbLib.vfb.vfb import Vfb
from fontTools.misc.transform import Transform

from babelfont import Anchor, Axis, Glyph, Layer, Master, Node, Shape, Guide
from babelfont.Glyph import GlyphList
from babelfont.BaseObject import Color, I18NDictionary
from babelfont.convertors import BaseConvertor

tags = {
    "Weight": "wght",
    "Width": "wdth",
    "Optical Size": "opsz",
    "Serif": "SERF",
}

ignore = [
    "Encoding Mac",
    "Encoding",
    "Master Count",
    "Default Weight Vector",
    "Type 1 Unique ID",
    "Menu Name",
    "FOND Name",
    "weight_name",  # Do something with this?
    "width_name",  # Do something with this?
    "weight",  # Do something if single master
    "trademark",
    "Monospaced",
    "Slant Angle",
    "Background Bitmap",
    "Glyph Origin",
    "Glyph Anchors Supplemental",
    "Links",
    "PostScript Info",  # for now; one per master
]
store_in_scratch = [
    "Axis Mappings Count",
]
names = {
    "description": "description",
    "License": "license",
    "License URL": "licenseURL",
    "designer": "designer",
    "designerURL": "designerURL",
    "manufacturer": "manufacturer",
    "manufacturerURL": "manufacturerURL",
    "copyright": "copyright",
    "sgn": "familyName",
    "tfn": "familyName",
    "versionFull": "version",
}

# hhea_line_gap
# hhea_ascender
# hhea_descender
# openTypeFeatures
# OpenType Class (names -> glyphs)


# Axis count
# Axis Name
# Axis Mappings Count (items per axis?)


class FontlabVFB(BaseConvertor):
    suffix = ".vfb"

    def _load(self):
        self.vfb = Vfb(self.filename)
        self.vfb.decompile()
        self.current_glyph = None
        self.current_master = None
        scratch = defaultdict(list)
        self.glyph_names = []
        self.metrics = {}
        # Quickly set up GID->name mapping
        for e in self.vfb.entries:
            if e.key == "Glyph":
                self.glyph_names.append(e.decompiled["name"])

        # Now parse the whole thing
        for e in self.vfb.entries:
            name = e.key
            if name is None:
                raise TypeError
            data = e.decompiled
            if data is None:
                continue

            if name in ignore or re.match("^\d+$", name):
                continue
            if name in store_in_scratch:
                scratch[name].append(data)
                continue

            if name == "psn":
                # Postscript name, hey we don't have that.
                pass
            elif name in names:
                if data:
                    setattr(
                        self.font.names, names[name], I18NDictionary.with_default(data)
                    )
            # Axes
            elif name == "Axis Name":
                axis = Axis(name, tags.get(name, name.upper()[:4]))  # Fix up tag!
                self.font.axes.append(axis)
            elif name == "Axis Mappings":
                counts = scratch["Axis Mappings Count"][0]
                for axis, count in zip(self.font.axes, counts):
                    if count > 0:
                        mappings = data[:count]
                        axis.map = [(u, round(d * 1000)) for u, d in mappings]
                        user_coords = [c[0] for c in mappings]
                        axis.min = min(user_coords, default=0)
                        axis.default = axis.minimum
                        axis.max = max(user_coords, default=1000)
                    data = data[10:]
            elif name == "Master Name":
                self.current_master = Master(name=data, id=uuid.uuid1())
                if self.metrics:
                    self.current_master.metrics = self.metrics
                self.font.masters.append(self.current_master)
            elif name == "Master Location":
                _, location = data
                master = self.current_master
                master.location = {}
                for axis, value in zip(self.font.axes, location):
                    master.location[axis.tag] = value
            elif name == "ffn":  # Full family name?
                pass
            elif name == "upm":
                self.font.upm = int(data)
            elif name == "versionMajor":
                self.font.version = (int(data), self.font.version[1])
            elif name == "versionMinor":
                self.font.version = (self.font.version[0], int(data))
            elif name == "vendorID":
                self.font.custom_opentype_values[("OS/2", "achVendID")] = data
            elif name == "hhea_line_gap":
                self.metrics["hheaLineGap"] = int(data)
            elif name == "hhea_ascender":
                self.metrics["hheaAscender"] = int(data)
            elif name == "hhea_descender":
                self.metrics["hheaDescender"] = int(data)
            elif name == "Glyph":
                self.current_glyph = Glyph(name=data["name"])
                self.font.glyphs.append(self.current_glyph)
                self._load_glyph(data)
            elif name == "Glyph GDEF Data":
                for anchor in data.get("anchors", []):
                    self._load_anchor(anchor)
            elif name == "Glyph Guide Properties":
                pass
            elif name == "TrueType Info":
                self._handle_truetype_info(data)
            elif name == "Glyph Unicode":
                self.current_glyph.codepoints = data
            elif name == "Italic Angle":
                # Put in master
                pass
            else:
                print(name, data)

        # Sort the glyphs by Unicode ID and name, because there's no
        # other order in there.
        glyphorder = list(self.font.glyphs.items())
        glyphorder.sort(key=lambda k: (k[1].codepoints, k[0]))
        newlist = GlyphList()
        for g in glyphorder:
            newlist.append(g[1])
        self.font.glyphs = newlist

        # Try and fill in metrics we don't have
        for master in self.font.masters:
            if "ascender" not in master.metrics and "hheaAscender" in master.metrics:
                master.metrics["ascender"] = master.metrics["hheaAscender"]
            if "descender" not in master.metrics and "hheaDescender" in master.metrics:
                master.metrics["descender"] = master.metrics["hheaDescender"]
        return self.font

    def _load_glyph(self, data):
        metrics = data["metrics"]
        masters = self.font.masters
        layers = [
            Layer(width=metric[0], height=metric[1], id=master.id)
            for master, metric in zip(masters, metrics)
        ]
        pens = [layer.getPen() for layer in layers]
        for node in data["nodes"]:
            for pen, point in zip(pens, node["points"]):
                cmd = getattr(pen, node["type"] + "To")
                if node["type"] == "move" and pen.contour:
                    pen.closePath()
                if node["type"] == "curve":
                    pen.curveTo(point[1], point[2], point[0])
                else:
                    cmd(*point)
        for pen in pens:
            if pen.contour:
                pen.closePath()
        for component in data.get("components", []):
            for ix, pen in enumerate(pens):
                pen.addComponent(
                    self.glyph_names[component["gid"]],
                    Transform(
                        dx=component["offsetX"][ix],
                        dy=component["offsetY"][ix],
                        xx=component["scaleX"][ix],
                        yy=component["scaleY"][ix],
                    ),
                )
        for layer in layers:
            self.current_glyph.layers.append(layer)

    def _load_anchor(self, data):
        layer = self.current_glyph.layers[-1]
        layer.anchors.append(
            Anchor(
                name=data["name"],
                x=data["x"],
                y=data["y"],
            )
        )

    def _handle_truetype_info(self, data):
        for element in data:
            pass
