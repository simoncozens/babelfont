import datetime
import math
import re
import uuid

import openstep_plist

from babelfont import (
    Anchor,
    Axis,
    Glyph,
    Guide,
    Instance,
    Layer,
    Master,
    Node,
    Shape,
    Transform,
)
from babelfont.convertors.glyphs.glyphs3 import GlyphsThree
from babelfont.convertors.glyphs.utils import (
    _glyphs_metrics_to_ours,
    _stash,
)


class Glyphs2(GlyphsThree):
    suffix = ".glyphs"

    @classmethod
    def is_suitable_plist(cls, convertor):
        return (
            ".formatVersion" not in convertor.scratch["plist"]
            or convertor.scratch["plist"][".formatVersion"] < 3
        )

    @classmethod
    def can_save(cls, convertor, **kwargs):
        if not super().can_save(convertor, **kwargs):
            return False
        if "format" not in kwargs or kwargs["format"] != 2:
            return False
        return True

    @classmethod
    def can_load(cls, convertor):
        if not super().can_load(convertor):
            return False
        if "plist" not in convertor.scratch:
            convertor.scratch["plist"] = openstep_plist.load(
                open(convertor.filename, "r"), use_numbers=True
            )
        return cls.is_suitable_plist(convertor)

    def _load(self):
        self.glyphs = self.scratch["plist"]

        self.customParameters = {}
        for param in self.glyphs.get("customParameters", []):
            self.customParameters[param["name"]] = param["value"]

        self._load_axes()

        self._load_kern_groups(self.glyphs["glyphs"])

        for gmaster in self.glyphs["fontMaster"]:
            self.font.masters.append(self._load_master(gmaster))
        self._fixup_axes()
        if not self.font.default_master:
            raise ValueError("Cannot identify default master")

        for gglyph in self.glyphs["glyphs"]:
            g = self._load_glyph(gglyph)
            self.font.glyphs.append(g)

        for ginstance in self.glyphs.get("instances", []):
            self.font.instances.append(self._load_instance(ginstance))

        self._fixup_axis_mappings()

        self._load_metadata()
        _stash(self.font, self.glyphs)

        self.interpret_features()
        return self.font

    def _load_axes(self):
        self.axis_name_map = {}
        if "Axes" in self.customParameters:
            for ax in self.customParameters["Axes"]:
                self.font.axes.append(Axis(name=ax["Name"], tag=ax["Tag"]))
                self.axis_name_map[ax["Name"]] = self.font.axes[-1]
        else:
            self.font.axes.append(Axis(name="Weight", tag="wght"))
            self.font.axes.append(Axis(name="Width", tag="wdth"))
            self.axis_name_map = {
                "Weight": self.font.axes[-1],
                "Width": self.font.axes[-1],
            }

    def _fixup_axes(self):
        for master in self.font.masters:
            for axis in self.font.axes:
                thisLoc = master.location[axis.tag]
                if axis.min is None or thisLoc < axis.min:
                    axis.min = thisLoc
                if master.id == self._default_master_id():
                    axis.default = master.location[axis.tag]
                if axis.max is None or thisLoc > axis.max:
                    axis.max = thisLoc

    def _fixup_axis_mappings(self):
        for axis in self.font.axes:
            if not axis.map:
                continue
            axis.map = list(sorted(set(axis.map)))
            axis.min, axis.max, axis.default = (
                axis.map_backward(axis.min),
                axis.map_backward(axis.max),
                axis.map_backward(axis.default),
            )

    def _custom_parameter(self, thing, name):
        for param in thing.get("customParameters", []):
            if param["name"] == name:
                return param["value"]
        return None

    def _default_master_id(self):
        # The default master in glyphs is either the first master or the
        # one selected by the Variable Font Origin custom parameter
        vfo = self._custom_parameter(self.glyphs, "Variable Font Origin")
        if vfo and vfo in self.font._master_map:
            return vfo
        return self.glyphs["fontMaster"][0]["id"]

    def _get_master_name(self, gmaster):
        if gmaster.get("name"):
            return gmaster["name"]
        cname = self._custom_parameter(gmaster, "Master Name")
        if cname:
            return cname
        # Remove None and empty string
        names = list(
            filter(
                None,
                [
                    gmaster.get("width", "Regular"),
                    gmaster.get("weight", "Regular"),
                    gmaster.get("custom", ""),
                ],
            )
        )

        # Remove redundant occurences of 'Regular'
        while len(names) > 1 and "Regular" in names:
            names.remove("Regular")
        if gmaster.get("italicAngle"):
            if names == ["Regular"]:
                return "Italic"
            if "Italic" not in gmaster.get("custom", ""):
                names.append("Italic")
        return " ".join(names)

    def _load_master(self, gmaster):
        # location = gmaster.get("axesValues", [])
        master = Master(
            name=self._get_master_name(gmaster),
            id=gmaster.get("id"),
        )
        for metric in Master.CORE_METRICS:
            master.metrics[metric] = gmaster.get(_glyphs_metrics_to_ours(metric))
        # Check for metrics in custom parameters

        master.font = self.font

        axisloc = self._custom_parameter(gmaster, "Axis Location")
        if axisloc:
            # I dunno, use that? Needs mapping? Check we are using tags/IDs
            location = axisloc
        else:
            potential_locations = [
                gmaster.get("weightValue", 100),
                gmaster.get("widthValue", 100),
                gmaster.get("customValue", 0),
                gmaster.get("customValue1", 0),
                gmaster.get("customValue2", 0),
                gmaster.get("customValue3", 0),
            ]
            location = {}
            for k, loc in zip(self.font.axes, potential_locations):
                location[k.tag] = loc
        master.location = location

        master.guides = [self._load_guide(x) for x in gmaster.get("guides", [])]

        kernmaster = None
        if self._custom_parameter(gmaster, "Link Metrics With First Master"):
            kernmaster = self.glyphs["fontMaster"][0]["id"]
        elif self._custom_parameter(gmaster, "Link Metrics With Master"):
            kernmaster_name = self._custom_parameter(
                gmaster, "Link Metrics With Master"
            )
            for m in self.glyphs["fontMaster"]:
                name = self._get_master_name(m)
                if name == kernmaster_name:
                    kernmaster = m["id"]
        else:
            kernmaster = master.id
        kerntable = self.glyphs.get("kerning", {}).get(kernmaster, {})
        master.kerning = self._load_kerning(kerntable)

        _stash(master, gmaster)
        return master

    def _get_codepoint(self, gglyph):
        cp = gglyph.get("unicode")
        if not cp:
            return []
        if isinstance(cp, int):
            return [int("%04i" % cp, 16)]
        return [int(x, 16) for x in cp.split(",")]

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
        cp = self._get_codepoint(gglyph)
        exported = True
        if "export" in gglyph and gglyph["export"] == 0:
            exported = False
        g = Glyph(name=name, codepoints=cp or [], category=category, exported=exported)
        g.production_name = gglyph.pop("production", None)

        for layer in gglyph.pop("layers"):
            g.layers.extend(self._load_layer(layer, g))

        _stash(g, gglyph)
        return g

    def _load_layer(self, layer, glyph, width=None):
        if width is None:
            width = layer["width"]
        l = Layer(width=width, id=layer.get("layerId"), _font=self.font, _glyph=glyph)
        l.name = layer.get("name")
        if [x for x in self.font.masters if x.id == l.id]:
            l._master = l.id
        else:
            l._master = layer.get("associatedMasterId")
        l.guides = [
            self._load_guide(x)
            for x in layer.get("guideLines", layer.get("guides", []))
        ]
        l.shapes = []
        for shape in layer.get("shapes", []):
            babelfont_shape = self.load_shape(shape)
            if babelfont_shape.is_component:
                babelfont_shape._layer = layer
            layer.shapes.append(babelfont_shape)
        for shape in layer.get("paths", []):
            l.shapes.append(self._load_path(shape))
        for shape in layer.get("components", []):
            comp = self.load_component(shape)
            comp._layer = l
            l.shapes.append(comp)
        for anchor in layer.get("anchors", []):
            l.anchors.append(self._load_anchor(anchor))

        returns = [l]
        if "background" in layer:
            (background,) = self._load_layer(layer["background"], glyph, width=l.width)
            # If it doesn't have an ID, we need to generate one
            background.id = background.id or str(uuid.uuid1())
            background.isBackground = True

            l.background = background.id
            returns.append(background)
        # TODO backgroundImage, metricTop/Bottom/etc, vertOrigin, vertWidth.
        for r in returns:
            assert r.valid
        _stash(l, layer)

        return returns

    def _load_guide(self, gguide):
        pos = gguide.get("position", "{0, 0}")
        m = re.match(r"^\{(\S+), (\S+)\}", pos)
        return Guide(pos=[int(m[1]), int(m[2]), int(gguide.get("angle", 0))])

    def _load_anchor(self, ganchor):
        pos = ganchor.get("position", "{0, 0}")
        m = re.match(r"^\{(\S+), (\S+)\}", pos)
        return Anchor(name=ganchor["name"], x=float(m[1]), y=float(m[2]))

    def _load_instance(self, ginstance):
        if ginstance.get("type") == "variable":
            return
        if "axesValues" in ginstance:
            location = ginstance["axesValues"]
            instance_location = {k.tag: v for k, v in zip(self.font.axes, location)}
        elif "instanceInterpolations" in ginstance:
            # All right then.
            instance_location = {k.tag: 0 for k in self.font.axes}
            for mId, factor in ginstance["instanceInterpolations"].items():
                master_loc = self.font.master(mId).location
                for k in self.font.axes:
                    instance_location[k.tag] += master_loc[k.tag] * factor
        else:
            raise ValueError("Need to Synthesize location")
        i = Instance(
            name=ginstance["name"],
            styleName=ginstance["name"],
            location=instance_location,
        )
        c = self._custom_parameter(ginstance, "Axis Location") or []
        for loc in c:
            ax = self.axis_name_map[loc["Axis"]]
            if not ax.map:
                ax.map = []
            ax.map.append(
                (
                    int(loc["Location"]),
                    instance_location[ax.tag],
                )
            )

        _stash(i, ginstance, ["customParameters"])
        return i

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
        shape.closed = bool(path["closed"])
        _stash(shape, path, ["attr"])
        return shape

    def _load_component(self, shape):
        glyphname = shape.get("ref", shape.get("name"))
        transform = shape.get("transform")
        if isinstance(transform, str):
            m = re.match(r"^\{(\S+), (\S+), (\S+), (\S+), (\S+), (\S+)\}", transform)
            transform = Transform(*[float(g) for g in m.groups()])
        c = Shape(ref=glyphname)

        if not transform:
            translate = Transform().translate(*shape.get("pos", (0, 0)))
            scale = Transform().scale(*shape.get("scale", (1, 1)))
            rotation = Transform().rotate(math.radians(shape.get("angle", 0)))
            # Compute transform...
            transform = translate.transform(scale).transform(rotation)

        c.transform = transform
        _stash(
            c,
            shape,
            [
                "alignment",
                "anchorTo",
                "attr",
                "locked",
                "orientation",
                "piece",
                "userData",
            ],
        )
        return c

    def _load_kern_groups(self, glyphs):
        kerngroups = {}
        for g in glyphs:
            l_class = g.get("leftKerningGroup", g["glyphname"])
            r_class = g.get("rightKerningGroup", g["glyphname"])
            # DAMMIT GLYPHS
            kerngroups.setdefault("MMK_R_" + l_class, []).append(g["glyphname"])
            kerngroups.setdefault("MMK_L_" + r_class, []).append(g["glyphname"])
        for k, v in kerngroups.items():
            self.font.features.classes[k] = tuple(v)

    def _load_kerning(self, kerndict):
        return {
            (l, r): value
            for l, level2 in kerndict.items()
            for r, value in level2.items()
        }

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
                props[prop["key"]] = {p["language"]: p["value"] for p in prop["values"]}

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

        # Any customparameters in the default master which look like
        # custom OT values need to move there.
        # cp = self.font.default_master._formatspecific.get("com.glyphsapp", {}).get(
        #     "customParameters", {}
        # )
        # for param in cp:
        #     ot_param = opentype_custom_parameters.get(param["name"])
        #     if not ot_param:
        #         continue
        #     self.font.customOpenTypeValues.append(
        #         OTValue(ot_param[0], ot_param[1], param["value"])
        #     )

        self.font.note = self.glyphs.get("note")
        self.font.date = datetime.datetime.strptime(
            self.glyphs.get("date"), "%Y-%m-%d %H:%M:%S +0000"
        )
        _stash(self.font, self.glyphs)

    def _load_features(self):
        for c in self.glyphs.get("classes", []):
            self.font.features.classes[c["name"]] = tuple(c["code"].split())

        # featurefile = ""
        # for f in self.glyphs.get("featurePrefixes", []):
        #     featurefile = featurefile + f.get("code")
        # for f in self.glyphs.get("features", []):
        #     tag = f.get("tag", f.get("name", ""))
        #     feacode = "feature %s { %s\n} %s;" % (tag, f["code"], tag)
        #     featurefile = featurefile + feacode

        # glyphNames = {g.name for g in self.font.glyphs}
        # feaparser = FeaParser(featurefile, glyphNames=glyphNames)
        # ast = feaparser.parser.ast
        # for name, members in self.font.features.classes.items():
        #     glyphclass = ast.GlyphClassDefinition(
        #         name, ast.GlyphClass([m for m in members])
        #     )
        #     feaparser.parser.glyphclasses_.define(name, glyphclass)
        # feaparser.parse()
        # self.font.features += feaparser.ff
