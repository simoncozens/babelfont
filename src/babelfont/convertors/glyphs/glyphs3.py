import datetime
import math
import re
import uuid
from collections import OrderedDict, defaultdict
from itertools import tee

import openstep_plist
from fontFeatures.feaLib import ast

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
from babelfont.BaseObject import OTValue
from babelfont.convertors import BaseConvertor
from babelfont.convertors.glyphs.utils import (
    _copyattrs,
    _custom_parameter,
    _g,
    _glyphs_metrics_to_ours,
    _metrics_dict_to_name,
    _metrics_name_to_dict,
    _moveformatspecific,
    _our_metrics_to_glyphs,
    _reverse_rename_metrics,
    _stash,
    _stashed_cp,
    glyphs_i18ndict,
    opentype_custom_parameters,
    to_bitfield,
)


class GlyphsThree(BaseConvertor):
    suffix = ".glyphs"

    @classmethod
    def is_suitable_plist(cls, convertor):
        return (
            ".formatVersion" in convertor.scratch["plist"]
            and convertor.scratch["plist"][".formatVersion"] >= 3
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
    def can_save(cls, convertor, **kwargs):
        if not convertor.filename.endswith(".glyphs"):
            return False
        if "format" in kwargs:
            return kwargs["format"] == 3
        return True

    def _load(self):
        font = self.font
        glyphs = self.scratch["plist"]

        for axis in glyphs.pop("axes", []):
            font.axes.append(self.load_axis(axis))

        for master in glyphs.pop("fontMaster"):
            font.masters.append(self.load_master(master))

        for glyph in glyphs.pop("glyphs"):
            font.glyphs.append(self.load_glyph(glyph))

        for instance in glyphs.pop("instances", []):
            instance = self.load_instance(instance)
            if instance:
                font.instances.append(instance)

        self.load_metadata()

        _stash(font, glyphs)

        # Things that start with "interpret" should pop their
        # format-specific values, and will generally need
        # another method to de-interpret them on save

        self.interpret_metrics()
        self.interpret_axes()
        self.interpret_axis_mappings()
        self.interpret_linked_kerning()
        assert self.font.default_master
        self.interpret_kern_groups()
        self.interpret_opentype_custom_parameters()
        self.interpret_features()

        return font

    def load_metadata(self):
        glyphs = self.scratch["plist"]
        self.font.upm = glyphs.pop("unitsPerEm")
        self.font.version = (glyphs.pop("versionMajor"), glyphs.pop("versionMinor"))
        self.font.names.familyName.set_default(glyphs.pop("familyName"))

        # This is very glyphs 3
        props = {}
        for prop in glyphs.get("properties", []):
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

        self.font.note = glyphs.pop("note", "")
        self.font.date = datetime.datetime.strptime(
            glyphs.pop("date"), "%Y-%m-%d %H:%M:%S +0000"
        )

    def load_axis(self, gaxis):
        axis = Axis(name=gaxis["name"], tag=gaxis["tag"])
        _stash(axis, gaxis, include=["hidden"])
        return axis

    def load_master(self, gmaster):
        glyphs = self.scratch["plist"]
        master = Master(
            name=gmaster["name"],
            id=gmaster["id"],
            font=self.font,
            guides=[self.load_guide(x) for x in gmaster.pop("guides", [])],
        )
        location = gmaster.pop("axesValues", [])
        master.location = {k.tag: v for k, v in zip(self.font.axes, location)}

        kernmaster = master.id
        kerntable = glyphs.get("kerningLTR", {}).get(kernmaster, {})

        master.kerning = self.load_kerning(kerntable)
        # XXX support RTL kerning etc.

        _stash(master, gmaster)
        assert master.valid
        return master

    def load_glyph(self, gglyph):
        name = gglyph["glyphname"]
        c = gglyph.get("category")
        sc = gglyph.get("subCategory")
        if sc == "Ligature":
            category = "ligature"
        if c == "Mark":
            category = "mark"
        else:
            category = "base"
        cp = self.get_codepoint(gglyph)
        exported = True
        if "export" in gglyph and gglyph.pop("export") == 0:
            exported = False
        g = Glyph(name=name, codepoints=cp or [], category=category, exported=exported)
        g.production_name = gglyph.pop("production", None)

        for layer in gglyph.pop("layers", []):
            g.layers.extend(self.load_layer(layer))

        _stash(g, gglyph)

        return g

    def load_layer(self, layer, width=None):
        if width is None:
            width = layer["width"]
        l = Layer(width=width, id=layer.pop("layerId", ""), _font=self.font)
        l.name = layer.pop("name", "")
        if [x for x in self.font.masters if x.id == l.id]:
            l._master = l.id
        else:
            l._master = layer.pop("associatedMasterId", None)
        l.guides = [
            self.load_guide(x) for x in layer.pop("guideLines", layer.pop("guides", []))
        ]
        l.shapes = []
        for shape in layer.pop("shapes", []):
            l.shapes.append(self.load_shape(shape))
        for shape in layer.pop("paths", []):
            l.shapes.append(self.load_path(shape))
        for shape in layer.pop("components", []):
            l.shapes.append(self.load_component(shape))
        for anchor in layer.pop("anchors", []):
            l.anchors.append(self.load_anchor(anchor))

        returns = [l]
        if "background" in layer:
            (background,) = self.load_layer(layer["background"], width=l.width)
            # If it doesn't have an ID, we need to generate one
            background.id = background.id or str(uuid.uuid1())
            background.isBackground = True

            l._background = background.id
            returns.append(background)
        for r in returns:
            assert r.valid

        _stash(l, layer)
        return returns

    def load_guide(self, gguide):
        g = Guide(pos=[*gguide.get("pos", (0, 0)), gguide.get("angle", 0)])
        _stash(g, gguide)
        return g

    def load_anchor(self, ganchor):
        x, y = ganchor.get("pos", (0, 0))
        return Anchor(name=ganchor["name"], x=x, y=y)

    def load_component(self, shape):
        glyphname = shape.pop("ref")
        transform = shape.pop("transform", None)
        if isinstance(transform, str):
            m = re.match(r"^\{(\S+), (\S+), (\S+), (\S+), (\S+), (\S+)\}", transform)
            transform = Transform(*[float(g) for g in m.groups()])
        c = Shape(ref=glyphname)

        if not transform:
            translate = Transform().translate(*shape.pop("pos", (0, 0)))
            scale = Transform().scale(*shape.pop("scale", (1, 1)))
            rotation = Transform().rotate(math.radians(shape.pop("angle", 0)))
            # Compute transform...
            transform = translate.transform(scale).transform(rotation)

        c.transform = transform
        _stash(c, shape)
        return c

    def load_shape(self, shape):
        if "nodes" in shape:  # It's a path
            return self.load_path(shape)
        else:
            return self.load_component(shape)

    def load_instance(self, ginstance):
        if ginstance.get("type") == "variable":
            return
        if "axesValues" in ginstance:
            location = ginstance.pop("axesValues")
            instance_location = {k.tag: v for k, v in zip(self.font.axes, location)}
        elif "instanceInterpolations" in ginstance:
            # All right then.
            instance_location = {k.tag: 0 for k in self.font.axes}
            for mId, factor in ginstance.get("instanceInterpolations").items():
                master_loc = self.font.master(mId).location
                for k in self.font.axes:
                    instance_location[k.tag] += master_loc[k.tag] * factor
        else:
            raise ValueError("Need to Synthesize location")
        name = ginstance.pop("name")
        i = Instance(
            name=name,
            styleName=name,
            location=instance_location,
        )
        _stash(i, ginstance)
        return i

    def load_path(self, path):
        shape = Shape()
        shape.nodes = [Node(*n) for n in path["nodes"]]
        shape.closed = path["closed"]
        _stash(shape, path)
        return shape

    def get_codepoint(self, gglyph):
        cp = gglyph.get("unicode")
        if cp and not isinstance(cp, list):
            cp = [cp]
        if cp:
            return [int(x) for x in cp]

    def interpret_kern_groups(self):
        kerngroups = defaultdict(list)
        for g in self.font.glyphs:
            left_group = _g(g, "kernLeft", pop=True)
            right_group = _g(g, "kernRight", pop=True)

            if left_group:
                kerngroups[f"MMK_L_{left_group}"].append(g.name)
            if right_group:
                kerngroups[f"MMK_R_{right_group}"].append(g.name)

        for k, v in kerngroups.items():
            self.font.features.namedClasses[k] = tuple(v)

    def interpret_linked_kerning(self):
        name_to_master = {m.name.get_default(): m for m in self.font.masters}
        for master in self.font.masters:
            kernmaster = None
            if _stashed_cp(master, "Link Metrics With First Master"):
                master.kerning = self.font.masters[0].kerning
            elif _stashed_cp(master, "Link Metrics With Master"):
                kernmaster_name = _stashed_cp(master, "Link Metrics With Master")
                kernmaster = name_to_master.get(kernmaster_name)
                if kernmaster:
                    master.kerning = kernmaster.kerning

    def load_kerning(self, kerndict):
        return {
            (l, r): value
            for l, level2 in kerndict.items()
            for r, value in level2.items()
        }

    def interpret_metrics(self):
        metrics = _g(self.font, "metrics", [])  # Keep stashed
        metric_types = [_metrics_dict_to_name(k) for k in metrics]
        for master in self.font.masters:
            metric_values = _g(master, "metricValues", [], pop=True)
            for k, v in zip(metric_types, metric_values):
                pos = v.get("pos", 0)
                master.metrics[k] = pos
                if v.get("over"):
                    master.metrics["%s overshoot" % _glyphs_metrics_to_ours(k)] = v[
                        "over"
                    ]

    def interpret_axes(self):
        # The default master in glyphs is either the first master or the
        # one selected by the Variable Font Origin custom parameter
        vfo = _stashed_cp(self.font, "Variable Font Origin")
        if not vfo:
            vfo = self.font.masters[0].id

        for master in self.font.masters:
            for axis in self.font.axes:
                thisLoc = master.location[axis.tag]
                if axis.min is None or thisLoc < axis.min:
                    axis.min = thisLoc
                if master.id == vfo:
                    axis.default = master.location[axis.tag]
                if axis.max is None or thisLoc > axis.max:
                    axis.max = thisLoc

    def interpret_axis_mappings(self):
        axes_by_name = {a.name.get_default(): a for a in self.font.axes}
        for instance in self.font.instances:
            c = (
                _custom_parameter(
                    instance._formatspecific.get("com.glyphsapp", {}), "Axis Location"
                )
                or []
            )
            for loc in c:
                ax = axes_by_name[loc["Axis"]]
                if not ax.map:
                    ax.map = []
                ax.map.append(
                    (
                        instance.location[ax.tag],
                        int(loc["Location"]),
                    )
                )

    def interpret_opentype_custom_parameters(self):
        # Any customparameters in the default master which look like
        # custom OT values need to move there.
        cp = _g(self.font.default_master, "customParameters", [])
        new_cps = []
        for param in cp:
            ot_param = opentype_custom_parameters.get(param["name"])
            if not ot_param:
                new_cps.append(param)
                continue
            self.font.customOpenTypeValues.append(
                OTValue(ot_param[0], ot_param[1], param["value"])
            )
        if new_cps:
            _stash(self.font.default_master, {"customParameters": new_cps})

    def interpret_features(self):
        ff = "# Classes\n"
        for glyphclass in _g(self.font, "classes", [], pop=True):
            ff += f"@{glyphclass['name']} = [{glyphclass['code']}]"

        self.font.features = ff

    def _save(self):
        font = self.font
        out = _moveformatspecific(font)
        self.glyphs = out
        out["versionMajor"], out["versionMinor"] = font.version
        out[".formatVersion"] = 3
        out["unitsPerEm"] = font.upm
        if font.note:
            out["note"] = font.note
        if font.date:
            out["date"] = font.date.strftime("%Y-%m-%d %H:%M:%S +0000")
        out["familyName"] = font.names.familyName.default_or_dict()
        out["axes"] = [self.save_axis(ax) for ax in self.font.axes]

        # Sort out the metrics order, using "my" names
        metrics_order = _g(font, "metrics", [])
        # Ensure we have all the metrics
        for m in font.masters:
            for k in m.metrics.keys():
                if k.endswith(" overshoot"):
                    continue  # We'll write it into the other metric
                k = _metrics_name_to_dict(k)
                if k not in metrics_order:
                    metrics_order.append(k)

        out["metrics"] = metrics_order

        out["fontMaster"] = [self.save_master(m) for m in self.font.masters]
        out["glyphs"] = [self.save_glyph(g) for g in self.font.glyphs]
        instances = [self.save_instance(i) for i in self.font.instances]
        if instances:
            out["instances"] = instances

        kerntables = OrderedDict()
        for master in self.font.masters:
            table = self.save_kerning(master.kerning)
            if table:
                kerntables[master.id] = table
        if kerntables:
            out["kerningLTR"] = kerntables

        self.save_metadata(out)
        self.save_custom_parameters(out)

        with open(self.filename, "wb") as file:
            openstep_plist.dump(out, file, indent=0, single_line_tuples=True)
            file.write(b"\n")

    def save_axis(self, axis):
        gaxis = _moveformatspecific(axis)
        _copyattrs(axis, gaxis, ["name", "tag"])
        return gaxis

    def save_kerning(self, kerntable):
        newtable = {}
        for (l, r), val in kerntable.items():
            newtable.setdefault(l, {})[r] = val
        return newtable

    def save_master(self, master):
        gmaster = _moveformatspecific(master)
        if master.location:
            gmaster["axesValues"] = list(master.location.values())
        gmaster["metricValues"] = []
        for k in self.glyphs["metrics"]:
            metric = {}
            pos = master.metrics.get(_metrics_dict_to_name(k))
            over = master.metrics.get(_metrics_dict_to_name(k) + " overshoot")
            if pos:
                metric["pos"] = pos
            if over:
                metric["over"] = over
            gmaster["metricValues"].append(metric)
        if master.guides:
            gmaster["guides"] = [self.save_guide(g) for g in master.guides]
        _copyattrs(master, gmaster, ["name", "id"], convertor=str)
        return gmaster

    def save_guide(self, guide):
        gguide = _moveformatspecific(guide)
        gguide["pos"] = tuple(guide.pos[0:2])
        if guide.pos[2]:
            gguide["angle"] = guide.pos[2]
        return gguide

    def save_glyph(self, glyph):
        gglyph = _moveformatspecific(glyph)
        gglyph["glyphname"] = glyph.name
        if len(glyph.codepoints) == 1:
            # if glyph.codepoints[0] < 256:
            gglyph["unicode"] = glyph.codepoints[0]
            # else:
            # gglyph["unicode"] = "%04x" % glyph.codepoints[0]
        elif len(glyph.codepoints) > 1:
            gglyph["unicode"] = glyph.codepoints
        gglyph["layers"] = [self.save_layer(l) for l in glyph.layers]
        if glyph.production_name is not None and glyph.production_name != glyph.name:
            gglyph["production"] = glyph.production_name
        if not glyph.exported:
            gglyph["export"] = 0
        # Check for kern groups
        # XXX
        return gglyph

    def save_layer(self, layer):
        glayer = _moveformatspecific(layer)
        _copyattrs(layer, glayer, ["width", "name"])
        glayer["layerId"] = str(layer.id)
        if layer.guides:
            glayer["guides"] = [self.save_guide(g) for g in layer.guides]
        if layer.shapes:
            glayer["shapes"] = [self.save_shape(s) for s in layer.shapes]
        if layer._master and layer._master != layer.id:
            glayer["associatedMasterId"] = layer._master
        return glayer

    def save_shape(self, shape):
        gshape = _moveformatspecific(shape)
        if shape.is_path:
            gshape["closed"] = shape.closed
            gshape["nodes"] = [self.save_node(n) for n in shape.nodes]
        else:
            _copyattrs(shape, gshape, ["ref", "angle"])
            if shape.pos != (0, 0):
                _copyattrs(shape, gshape, ["pos"])
            if shape.scale != (1, 1):
                _copyattrs(shape, gshape, ["scale"])
        return gshape

    def save_node(self, node):
        if node.userdata:
            return (node.x, node.y, node.type, node.userdata)
        else:
            return (node.x, node.y, node.type)

    def save_instance(self, instance):
        ginstance = _moveformatspecific(instance)
        ginstance["name"] = instance.name.get_default()
        ginstance["axesValues"] = [instance.location[ax.tag] for ax in self.font.axes]

        return ginstance

    def save_metadata(self, out):
        if self.font.note:
            out["note"] = self.font.note
        if self.font.version:
            out["versionMajor"], out["versionMinor"] = self.font.version
        if not "properties" in out:
            out["properties"] = []
        props = out["properties"]
        alreadydone = {p["key"] for p in props}
        if self.font.names.copyright and "copyrights" not in alreadydone:
            props.append(
                {
                    "key": "copyrights",
                    "values": glyphs_i18ndict(self.font.names.copyright),
                }
            )
        if self.font.names.designer and "designer" not in alreadydone:
            props.append(
                {"key": "designer", "values": glyphs_i18ndict(self.font.names.designer)}
            )
        if self.font.names.designerURL and "designerURL" not in alreadydone:
            props.append(
                {
                    "key": "designerURL",
                    "values": glyphs_i18ndict(self.font.names.designerURL),
                }
            )
        if not props:
            del out["properties"]

    def save_custom_parameters(self, out):
        if not "customParameters" in out:
            out["customParameters"] = []
        for otvalue in self.font.customOpenTypeValues:
            table, field, value = otvalue.table, otvalue.field, otvalue.value
            if table == "OS/2" and field == "fsType":
                out["customParameters"].append(
                    {"name": "fsType", "value": to_bitfield(int(value))}
                )
            if table == "OS/2" and field == "fsSelection":
                if value & 0x7:
                    out["customParameters"].append(
                        {"name": "Use Typo Metrics", "value": 1}
                    )
                if value & 0x8:
                    out["customParameters"].append(
                        {"name": "Has WWS Names", "value": 1}
                    )
        if not out["customParameters"]:
            del out["customParameters"]