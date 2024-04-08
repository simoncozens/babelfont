import datetime
import re
import math

import orjson
from fontTools.misc.transform import Transform

from babelfont import Axis, Glyph, Layer, Master, Node, Shape, Guide
from babelfont.BaseObject import Color, I18NDictionary, OTValue
from babelfont.convertors import BaseConvertor


class FontlabVFJ(BaseConvertor):
    suffix = ".vfj"

    def _load(self):
        self.fontlab = orjson.loads(open(self.filename).read())["font"]
        self.known_transforms = {}
        self._load_axes()
        self._load_masters()
        if "defaultMaster" in self.fontlab:
            default = self.font.master(self.fontlab["defaultMaster"])
            if self.font.axes:
                def_loc = default.location
                for axis in self.font.axes:
                    if axis.tag in default.location:
                        axis.default = axis.designspace_to_userspace(def_loc[axis.tag])
            assert self.font.default_master
        for g in self.fontlab.get("glyphs", []):
            glyph = self._load_thing(g, self.glyph_loader)
            # Fontlab allows glyphs to elide layers with no shapes
            # so we need to ensure there is a layer for each master
            layer_ids = [l.id for l in glyph.layers]
            for master in self.font.masters:
                if master.id not in layer_ids:
                    layer = Layer(
                        name=master.id,
                        _master=master.id,
                    )
                    layer._font = self.font
                    glyph.layers.append(layer)

            self.font.glyphs.append(glyph)
        for cls in self.fontlab.get("classes", []):
            self._load_class(cls)
        for feature in self.fontlab.get("openTypeFeatures", []):
            self._load_feature(feature)
        self.font.upm = self.fontlab.get("upm", 1000)
        self._load_metadata()
        return self.font

    def _load_feature(self, feature):
        count = 0
        if "name" in feature:
            # Remove the "feature ... {" first line and "} tag;" last line
            feature["feature"] = re.sub(
                r"^\s*feature\s+(\w+)\s*{(.*)\s*}\s*\1\s*;",
                r"\2",
                feature["feature"],
                flags=re.DOTALL,
            )
            self.font.features.features.append((feature["name"], feature["feature"]))
        else:
            self.font.features.prefixes["Anonymous prefix " + str(count)] = feature[
                "feature"
            ]
            count += 1

    def _load_class(self, cls):
        self.font.features.classes[cls["name"]] = cls["names"]

    axis_loader = (
        Axis,
        {
            "name": "name",
            "tag": "tag",
            "minimum": "min",
            "maximum": "max",
            "default": "default",
            "axisGraph": ("map", lambda _, x: [(v, int(k)) for k, v in x.items()]),
        },
    )

    def _load_kerning(self, flkerning):
        for kclass in flkerning.get("kerningClasses", []):
            if kclass.get("1st"):
                self.font.first_kern_groups[kclass["name"]] = kclass["names"]
            if kclass.get("2nd"):
                self.font.second_kern_groups[kclass["name"]] = kclass["names"]
        kerning = {}
        for left, rvalue in flkerning.get("pairs", {}).items():
            if left.startswith("@"):
                left = "@first_group_" + left[1:]
            for right, value in rvalue.items():
                if right.startswith("@"):
                    right = "@second_group_" + right[1:]
                kerning[(left, right)] = int(value)
        return kerning

    def _convert_color(_, col):
        r, g, b = int(col[1:3], 16), int(col[3:5], 16), int(col[5:7], 16)
        return Color(r, g, b, 0)

    def _convert_shapes(self, flshapes):
        shapes = []
        for shape in flshapes:
            transform_j = shape.get("transform", {})
            if "id" in transform_j:
                self.known_transforms[transform_j["id"]] = transform_j
            if isinstance(transform_j, str):
                transform_j = self.known_transforms[transform_j]
            transform = Transform().translate(
                transform_j.get("xOffset", 0),
                transform_j.get("yOffset", 0),
            )
            if "component" in shape:
                shapes.append(
                    Shape(
                        ref=shape["component"]["glyphName"],
                        transform=transform,
                        _=shape["component"],
                    )
                )
            else:
                for flcontour in shape["elementData"].get("contours", []):
                    contour = Shape(nodes=[])
                    for n in flcontour["nodes"]:
                        contour.nodes.extend(self._load_node(n))
                    if (
                        contour.nodes[0].type[0] == "l"
                        and contour.nodes[-1].type[0] == "q"
                    ):
                        contour.nodes[0].type = "cs"
                        contour.nodes[-1].type = "o"
                    shapes.append(contour)
        return shapes

    def _convert_guides(self, flguides):
        guides = []
        for guide in flguides:
            if "horizontal" in guide:
                y = guide["position"]
                x = 0
                angle = 0
            elif "vertical" in guide:
                x = guide.get("position", 0)
                y = 0
                angle = 90
            else:
                x, y = [float(v) for v in guide["center"].split(" ")]
                vector_x, vector_y = [float(v) for v in guide["vector"].split(" ")]
                angle = math.degrees(math.atan2(vector_y - y, vector_x - x))
            guides.append(Guide(pos=(x, y, angle)))
        return guides

    def _load_node(self, input_):
        stuff = input_.split("  ")
        rv = []
        for ix, node in enumerate(stuff):
            m = re.match(r"(-?[\d\.]+) (-?[\d\.]+)( s)?", node)
            if not m:
                raise ValueError("Can't understand nodestring %s" % node)
            if len(stuff) == 1:
                ntyp = "l"
            elif len(stuff) == 3 and ix == 2:
                ntyp = "c"
            elif len(stuff) == 2 and ix == 1:
                ntyp = "q"
            else:
                ntyp = "o"
            if m[3]:
                ntyp = ntyp + "s"
            rv.append(Node(x=float(m[1]), y=float(m[2]), type=ntyp))
        return rv

    # The way these loaders work is they define a class to load into and a schema.
    # The schema is a mapping between *Fontlab* field names, and what we do with
    # it: if it's a plain string, this is our field name; if it's a tuple, it's
    # our field name and a method to transform the value; if it's a list, it's
    # a combination of field/tuples.
    master_loader = (
        Master,
        {
            "name": ["id", "name"],
            "kerning": ("kerning", _load_kerning),
            "location": (
                "location",
                lambda s, x: {s.axis_name_map[k].tag: v for k, v in x.items()},
            ),
        },
    )

    _layer_loader = (
        Layer,
        {
            "advanceWidth": "width",
            "name": ["name", "_master", "id"],
            "color": ("color", _convert_color),
            "elements": ("shapes", _convert_shapes),
            "guidelines": ("guides", _convert_guides),
        },
    )

    glyph_loader = (
        Glyph,
        {
            "name": "name",
            "unicode": (
                "codepoints",
                lambda _, x: [int(cp, 16) for cp in x.split(",")],
            ),
            "layers": ("layers", _layer_loader),
            "elements": None,
            "openTypeGlyphClass": (
                "category",
                lambda _, x: [None, "base", "ligature", "mark", "component"][x],
            ),
        },
    )

    def _load_thing(self, thing, handler):
        kwargs = {}
        kwargs["_"] = {}
        cls, mapping = handler
        for k, v in thing.items():
            if k not in mapping:
                kwargs["_"][k] = v
            elif mapping[k] is None:
                continue
            elif isinstance(mapping[k], list):
                for newname in mapping[k]:
                    kwargs[newname] = v
            elif isinstance(mapping[k], str):
                kwargs[mapping[k]] = v
            elif isinstance(mapping[k], tuple) and callable(mapping[k][1]):
                newName, convertor = mapping[k]
                kwargs[newName] = convertor(self, v)
            else:
                newName, convertor = mapping[k]
                if isinstance(v, list):
                    kwargs[newName] = [self._load_thing(v1, convertor) for v1 in v]
                else:
                    kwargs[newName] = self._load_thing(v, convertor)
        obj = cls(**kwargs)
        obj._font = self.font
        return obj

    def _load_axes(self):
        self.axis_name_map = {}
        for ax in self.fontlab.get("axes", []):
            axis = self._load_thing(ax, self.axis_loader)
            self.axis_name_map[ax["shortName"]] = axis
            self.font.axes.append(axis)

    def _load_masters(self):
        for m in self.fontlab.get("masters", []):
            fl_master = m["fontMaster"]
            metric_dict = {}
            for metric in [
                "ascender",
                "descender",
                "xHeight",
                "capsHeight",
                "measurement",
                "linegap",
                "underlineThickness",
                "underlinePosition",
            ]:
                if metric not in fl_master:
                    continue
                value = fl_master[metric]
                del fl_master[metric]
                if metric == "capsHeight":
                    metric = "capHeight"
                if metric == "linegap":
                    metric = "hheaLineGap"
                metric_dict[metric] = value
            master = self._load_thing(fl_master, self.master_loader)
            master.metrics = metric_dict
            master.font = self.font
            master.guides = self._convert_guides(fl_master.get("guidelines", []))
            self.font.masters.append(master)

    def _load_metadata(self):
        info = self.fontlab.get("info", {})
        self.font.names.familyName = I18NDictionary.with_default(info.get("tfn"))
        # sgn?
        for tag in [
            "copyright",
            "designer",
            "designerURL",
            "license",
            "licenseURL",
            "manufacturer",
            "manufacturerURL",
            "version",
        ]:
            setattr(self.font.names, tag, I18NDictionary.with_default(info.get(tag)))
        self.font.version = (info.get("versionMajor"), info.get("versionMinor"))
        if "vendor" in info:
            self.font.customOpenTypeValues.append(
                OTValue("OS/2", "achVendID", info["vendor"])
            )
        # Fontlab date format = "2020/08/28 15:33:36"
        if "date" in info:
            self.font.date = datetime.datetime.strptime(
                info["creationDate"],
                "%Y/%m/%d %H:%M:%S",
            )
        if "useTypoMetrics" in info:
            self.font.customOpenTypeValues.append(OTValue("OS/2", "fsSelection", 0x7))
        if "embedding" in info:
            self.font.customOpenTypeValues.append(
                OTValue("OS/2", "fsType", int(info["embedding"], 16))
            )
        # codepageRange
        # unicodeRange
