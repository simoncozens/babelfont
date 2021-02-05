from datetime import datetime
from nfsf import *
import openstep_plist
from nfsf.util.affine import Affine
from nfsf.convertors import BaseConvertor
import re
import uuid


class GlyphsTwo(BaseConvertor):
    suffix = ".glyphs"

    @classmethod
    def is_suitable_plist(cls, convertor):
        return (
            ".formatVersion" not in convertor.scratch["plist"]
            or convertor.scratch["plist"][".formatVersion"] < 3
        )

    @classmethod
    def can_load(cls, convertor):
        if not super().can_load(convertor):
            return False
        if not "plist" in convertor.scratch:
            convertor.scratch["plist"] = openstep_plist.load(
                open(convertor.filename, "r"), use_numbers=True
            )
        return cls.is_suitable_plist(convertor)

    @classmethod
    def load(cls, convertor):
        self = cls()
        self.glyphs = convertor.scratch["plist"]
        self.font = Font()
        return self._load()

    def _load(self):
        self._load_axes()

        for gmaster in self.glyphs["fontMaster"]:
            self.font.masters.append(self._load_master(gmaster))

        for gglyph in self.glyphs["glyphs"]:
            g = self._load_glyph(gglyph)
            self.font.glyphs.append(g)

        for ginstance in self.glyphs.get("instances", []):
            self.font.instances.append(self._load_instance(ginstance))

        self._load_metadata()
        return self.font

    def _load_axes(self):
        # XXX Synthesize axes
        pass

    def _load_master(self, gmaster):
        # location = gmaster.get("axesValues", [])
        master = Master(
            name=gmaster.get("name", ""),
            id=gmaster.get("id"),
            xHeight=gmaster.get("xHeight"),
            capHeight=gmaster.get("capHeight"),
            ascender=gmaster.get("ascender"),
            descender=gmaster.get("descender"),
        )
        # XXX Synthesize location

        master.guides = [self._load_guide(x) for x in gmaster.get("guides", [])]

        _maybesetformatspecific(master, gmaster, "customParameters")
        _maybesetformatspecific(master, gmaster, "iconName")
        _maybesetformatspecific(master, gmaster, "id")
        _maybesetformatspecific(master, gmaster, "numberValues")
        _maybesetformatspecific(master, gmaster, "stemValues")
        _maybesetformatspecific(master, gmaster, "properties")
        _maybesetformatspecific(master, gmaster, "userData")
        _maybesetformatspecific(master, gmaster, "visible")
        return master

    def _load_glyph(self, gglyph):
        name = gglyph["glyphname"]
        c = gglyph.get("category")
        sc = gglyph.get("subCategory")
        if sc == "Ligature":
            category = "ligature"
        if c == "Mark":
            category = "mark"
        else:
            category = "base"
        cp = gglyph.get("unicode")
        if isinstance(cp, str) and re.match(r"^[0-9A-F]{4}$", cp):
            cp = int(cp, 16)

        g = Glyph(name=name, codepoint=cp, category=category)
        for entry in [
            "case",
            "category",
            "subCategory",
            "color",
            "direction",
            "export",
            "locked",
            "partsSettings",
            "tags",
        ]:
            _maybesetformatspecific(g, gglyph, entry)

        for layer in gglyph.get("layers"):
            g.layers.extend(self._load_layer(layer))

        return g

    def _load_layer(self, layer, width=None):
        if width is None:
            width = layer["width"]
        l = Layer(width=width, id=layer.get("layerId"))
        l.name = layer.get("name")
        l._master = layer.get("associatedMasterId")
        l.guides = [
            self._load_guide(x)
            for x in layer.get("guideLines", layer.get("guides", []))
        ]
        l.shapes = []
        for shape in layer.get("shapes", []):
            l.shapes.append(self._load_shape(shape))
        for shape in layer.get("paths", []):
            l.shapes.append(self._load_path(shape))
        for shape in layer.get("components", []):
            l.shapes.append(self._load_component(shape))

        _maybesetformatspecific(l, layer, "hints")
        _maybesetformatspecific(l, layer, "partSelection")
        _maybesetformatspecific(l, layer, "visible")
        returns = [l]
        if "background" in layer:
            (background,) = self._load_layer(layer["background"], width=l.width)
            # If it doesn't have an ID, we need to generate one
            background.id = background.id or str(uuid.uuid1())
            background.isBackground = True

            l._background = background.id
            returns.append(background)
        # TODO backgroundImage, metricTop/Bottom/etc, vertOrigin, vertWidth.
        return returns

    def _load_guide(self, gguide):
        pos = gguide.get("position", "{0, 0}")
        m = re.match(r"^\{(\S+), (\S+)\}", pos)
        return Guide(pos=[int(m[1]), int(m[2]), int(gguide.get("angle", 0))])

    def _load_instance(self, ginstance):
        instance = Instance(name=ginstance["name"])
        if "axesValues" in ginstance:
            location = ginstance["axesValues"]
            instance.location = {k.name: v for k, v in zip(self.font.axes, location)}
        else:
            # XXX synthesize
            pass
        return instance

    def _load_path(self, path):
        shape = Shape()
        shape.nodes = []
        for n in path["nodes"]:
            m = re.match(r"(\S+) (\S+) (\S+)( SMOOTH)?(.*)", n)
            ntype = m[3][0].lower()
            if m[4]:
                ntype = ntype + "s"
            n = Node(x=float(m[1]), y=float(m[2]), type=ntype)
            shape.nodes.append(n)
        shape.closed = path["closed"]
        return shape

    def _load_component(self, shape):
        glyphname = shape.get("ref", shape.get("name"))
        transform = shape.get("transform")
        c = Shape(ref=glyphname)

        if not transform:
            translate = Affine.translation(*shape.get("pos", (0, 0)))
            scale = Affine.scale(*shape.get("scale", (1, 1)))
            rotation = Affine.rotation(shape.get("angle", 0))
            # Compute transform...
            t = translate * scale * rotation
            transform = tuple([t.a, t.b, t.c, t.d, t.e, t.f])

        c.transform = transform
        for entry in [
            "alignment",
            "anchorTo",
            "attr",
            "locked",
            "orientation",
            "piece",
            "userData",
        ]:
            _maybesetformatspecific(c, shape, entry)
        return c

    def _load_metadata(self):
        self.font.upm = self.glyphs["unitsPerEm"]
        self.font.version = (self.glyphs["versionMajor"], self.glyphs["versionMinor"])
        self.font.names.familyName.set_default(self.glyphs["familyName"])

        # This is very glyphs 3
        props = {}
        for prop in self.glyphs.get("properties", []):
            if "value" in prop:
                props[prop["key"]] = prop["value"]
            else:
                props[prop["key"]] = { p["language"]: p["value"] for p in prop["values"] }

        if props:
            interestingProps = {
                "copyrights": "copyright",
                "designer": "designer",
                "designerURL": "designerURL",
            }  # Etc
            for glyphsname, attrname in interestingProps.items():
                thing = props.get(glyphsname, "")
                if isinstance(thing, dict):
                    getattr(self.font.names, attrname).copy_in(thing)
                else:
                    getattr(self.font.names, attrname).set_default(thing)
            # Do other properties here

        self.font.note = self.glyphs.get("note")
        self.font.date = datetime.strptime(
            self.glyphs.get("date"), "%Y-%m-%d %H:%M:%S +0000"
        )
        _maybesetformatspecific(self.font, self.glyphs, ".appVersion")
        _maybesetformatspecific(self.font, self.glyphs, ".formatVersion")
        _maybesetformatspecific(self.font, self.glyphs, "DisplayStrings")
        _maybesetformatspecific(self.font, self.glyphs, "customParameters")
        _maybesetformatspecific(self.font, self.glyphs, "settings")
        _maybesetformatspecific(self.font, self.glyphs, "numbers")
        _maybesetformatspecific(self.font, self.glyphs, "stems")
        _maybesetformatspecific(self.font, self.glyphs, "userData")


class GlyphsThree(GlyphsTwo):
    @classmethod
    def is_suitable_plist(cls, convertor):
        return (
            ".formatVersion" in convertor.scratch["plist"]
            and convertor.scratch["plist"][".formatVersion"] >= 3
        )

    def _load(self):
        super()._load()
        return self.font

    def _load_axes(self):
        for gaxis in self.glyphs.get("axes", []):
            axis = Axis(name=gaxis["name"], tag=gaxis["tag"])
            _maybesetformatspecific(axis, gaxis, "hidden")
            self.font.axes.append(axis)

    def _load_master(self, gmaster):
        location = gmaster.get("axesValues", [])
        metrics = self.glyphs["metrics"]
        master = Master(name=gmaster["name"])
        metric_types = [m["type"] for m in metrics]
        metric_values = [x.get("pos", 0) for x in gmaster["metricValues"]]
        master.metrics = {k: v for (k, v) in list(zip(metric_types, metric_values))}
        master.location = {k.name: v for k, v in zip(self.font.axes, location)}
        master.guides = [self._load_guide(x) for x in gmaster.get("guides", [])]

        _maybesetformatspecific(master, gmaster, "customParameters")
        _maybesetformatspecific(master, gmaster, "iconName")
        _maybesetformatspecific(master, gmaster, "id")
        _maybesetformatspecific(master, gmaster, "numberValues")
        _maybesetformatspecific(master, gmaster, "stemValues")
        _maybesetformatspecific(master, gmaster, "properties")
        _maybesetformatspecific(master, gmaster, "userData")
        _maybesetformatspecific(master, gmaster, "visible")
        return master

    def _load_guide(self, gguide):
        return Guide(pos=[*gguide.get("pos", (0, 0)), gguide.get("angle", 0)])

    def _load_shape(self, shape):
        if "nodes" in shape:  # It's a path
            return self._load_path(shape)
        else:
            return self._load_component(shape)

    def _load_path(self, path):
        shape = Shape()
        shape.nodes = [Node(*n[0:3]) for n in path["nodes"]]
        shape.closed = path["closed"]
        return shape


def _maybesetformatspecific(item, glyphs, key):
    if glyphs.get(key):
        if "com.glyphsapp" not in item._formatspecific:
            item._formatspecific["com.glyphsapp"] = {}
        item._formatspecific["com.glyphsapp"][key] = glyphs.get(key)
