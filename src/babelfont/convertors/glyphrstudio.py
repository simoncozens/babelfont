import datetime
import re
import math
import uuid

import orjson
from fontTools.misc.transform import Transform

from babelfont import Axis, Glyph, Instance, Layer, Master, Node, Shape, Guide
from babelfont.BaseObject import Color, I18NDictionary
from babelfont.convertors import BaseConvertor

names_map = {
    "familyName": "family",
    "styleName": "style",
    "description": "description",
    "designer": "designer",
    "designerURL": "designerURL",
    "manufacturer": "manufacturer",
    "manufacturerURL": "manufacturerURL",
    "license": "license",
    "licenseURL": "licenseURL",
    "copyright": "copyright",
    "trademark": "trademark",
}


class GlyphrStudio2(BaseConvertor):
    suffix = ".gs2"

    def _load(self):
        self.gs2 = orjson.loads(open(self.filename).read())
        weight = int(self.gs2.get("settings", {}).get("font", {}).get("weight", 400))

        # Set up single master font
        self.font.masters = [
            Master(
                name=I18NDictionary.with_default("Regular"),
                id=str(uuid.uuid4()),
                font=self.font,
                location={"wght": weight},
            )
        ]
        self.font.axes = [
            Axis(
                name=I18NDictionary.with_default("Weight"),
                tag="wght",
                min=weight,
                max=weight,
                default=weight,
            )
        ]
        self.font.instances = [
            Instance(
                name=I18NDictionary.with_default("Regular"), location={"wght": weight}
            )
        ]

        self._load_metadata()
        for glyph in sorted(self.gs2.get("glyphs", {}).keys()):
            self._load_glyph(self.gs2["glyphs"][glyph])
        if self.gs2.get("ligatures", {}):
            raise NotImplementedError(
                "Glyphr Studio ligatures are not supported in Babelfont."
            )
        if self.gs2.get("components", {}):
            raise NotImplementedError(
                "Glyphr Studio components are not yet supported in Babelfont."
            )
        if self.gs2.get("kerning", {}):
            raise NotImplementedError(
                "Glyphr Studio kerning is not yet supported in Babelfont."
            )
        return self.font

    def _load_metadata(self):
        font_info = self.gs2.get("settings", {}).get("font", {})
        self.font.upm = font_info.pop("upm", 1000)
        self.font.names.familyName.set_default(font_info.pop("family"))
        self.font.names.styleName.set_default(font_info.pop("style"))
        self.font.version = tuple(
            int(x) for x in font_info.get("version", "1.0").split(".")
        )
        for ours, theirs in names_map.items():
            if theirs in font_info:
                getattr(self.font.names, ours).set_default(font_info.pop(theirs))

        # Vertical metrics
        self.font.masters[0].metrics["ascender"] = font_info.get("ascent", 800)
        self.font.masters[0].metrics["descender"] = font_info.get("descent", -200)
        for metric in Master.CORE_METRICS:
            if metric in font_info:
                self.font.masters[0].metrics[metric] = font_info.pop(metric)
        # Stash everything else we don't know about
        self.font._formatspecific["gs2"] = font_info

    def _load_glyph(self, glyph):
        glyphname = glyph.get("id", "")
        if glyphname.startswith("glyph-0x"):
            unicode = int(glyphname[8:], 16)
        else:
            unicode = None
        our_glyph = Glyph(
            name=glyphname,
            codepoints=[unicode] if unicode is not None else [],
        )
        layer = Layer(
            width=glyph.get("advanceWidth", 1000),
            id=self.font.masters[0].id,
            _master=self.font.masters[0].id,
            shapes=self._load_shapes(glyph.get("shapes", [])),
        )
        our_glyph.layers.append(layer)
        self.font.glyphs[glyphname] = our_glyph

    def _load_shapes(self, shapes):
        result = []
        for shape in shapes:
            if "link" in shape:
                result.append(self._load_component(shape))
            else:
                result.append(self._load_path(shape))
        return result

    def _load_component(self, shape):
        transform = Transform(1)
        # Glyphr Studio does this *weirdly*
        if shape.get("rotateFirst", False):
            # XXX Glyphr rotates around the center of the linked glyph!
            transform = transform.rotate(math.radians(shape.get("rotation", 0) * -1))
        if shape.get("isFlippedEW", False):
            transform = transform.scale(-1, 1)
        if shape.get("isFlippedNS", False):
            transform = transform.scale(1, -1)
        transform = transform.translate(
            shape.get("translateX", 0),
            shape.get("translateY", 0),
        ).scale(shape.get("resizeWidth", 1), shape.get("resizeHeight", 1))

        if not shape.get("rotateFirst", False):
            transform = transform.rotate(math.radians(shape.get("rotation", 0) * -1))
        return Shape(ref=shape["link"], transform=transform)

    def _load_path(self, shape):
        return Shape(
            nodes=self._load_nodes(shape.get("pathPoints", [])),
        )

    def _load_nodes(self, points):
        nodes = []

        for point in points:
            on_curve = point["p"]
            if point.get("h1", {}).get("use", True) is False:
                del point["h1"]
            if point.get("h2", {}).get("use", True) is False:
                del point["h2"]
            if point.get("h1") or point.get("h2"):
                # A cubic!
                handle_before = point.get("h1", {})
                handle_after = point.get("h2", {})
                if handle_before:
                    nodes.append(
                        Node(
                            x=handle_before["coord"]["x"],
                            y=handle_before["coord"]["y"],
                            type="o",
                        )
                    )
                node_type = "c" if (len(nodes) and nodes[-1].type == "o") else "l"
                nodes.append(
                    Node(
                        x=on_curve["coord"]["x"],
                        y=on_curve["coord"]["y"],
                        type=node_type,
                    )
                )
                if handle_after:
                    nodes.append(
                        Node(
                            x=handle_after["coord"]["x"],
                            y=handle_after["coord"]["y"],
                            type="o",
                        )
                    )
            else:
                node_type = "c" if (len(nodes) and nodes[-1].type == "o") else "l"
                nodes.append(
                    Node(
                        x=on_curve["coord"]["x"],
                        y=on_curve["coord"]["y"],
                        type=node_type,
                    )
                )
        return nodes
