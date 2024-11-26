import datetime
import math
import re
import uuid
from collections import OrderedDict
from typing import List

import openstep_plist

from babelfont import (
    Anchor,
    Axis,
    Features,
    Glyph,
    Guide,
    Instance,
    Layer,
    Master,
    Node,
    Shape,
    Transform,
)
from babelfont.convertors import BaseConvertor
from babelfont.convertors.glyphs.utils import (
    _copyattrs,
    _custom_parameter,
    _g,
    _glyphs_metrics_to_ours,
    _glyphs_instance_names_to_ours,
    _metrics_dict_to_name,
    _metrics_name_to_dict,
    _moveformatspecific,
    _stash,
    _stashed_cp,
    glyphs_i18ndict,
    labels_to_feature,
    to_bitfield,
    custom_parameter_metrics,
)
from babelfont.Master import CORE_METRICS
from babelfont.BaseObject import I18NDictionary


class GlyphsThree(BaseConvertor):
    suffix = ".glyphs"
    LOAD_FILTERS = ["glyphData", "intermediateLayers"]

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
        if "plist" not in convertor.scratch:
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
        # Oops, we put the axes in designspace coordinates
        for axis in self.font.axes:
            axis.default = axis.designspace_to_userspace(axis.default)
            axis.min = axis.designspace_to_userspace(axis.min)
            axis.max = axis.designspace_to_userspace(axis.max)

        self.interpret_linked_kerning()
        assert self.font.default_master
        self.interpret_kern_groups()
        self.interpret_master_custom_parameters()
        self.interpret_font_custom_parameters()
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
                "designers": "designer",
                "designerURL": "designerURL",
                "trademarks": "trademark",
                "descriptions": "description",
                "licenses": "license",
                "licenseURL": "licenseURL",
                "manufacturers": "manufacturer",
                "manufacturerURL": "manufacturerURL",
            }  # Etc
            for glyphsname, attrname in interestingProps.items():
                thing = props.get(glyphsname, "")
                if isinstance(thing, dict):
                    getattr(self.font.names, attrname).copy_in(thing)
                else:
                    getattr(self.font.names, attrname).set_default(thing)
            # Do other properties here
            if "vendorID" in props:
                self.font.custom_opentype_values[("OS/2", "achVendID")] = props[
                    "vendorID"
                ]

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

    def load_glyph(self, gglyph: dict):
        name = gglyph["glyphname"]
        c = gglyph.get("category")
        sc = gglyph.get("subCategory")
        category = None
        if sc == "Ligature":
            category = "ligature"
        if c == "Mark" and sc == "Nonspacing":
            category = "mark"
        cp = self.get_codepoint(gglyph)
        exported = True
        if "export" in gglyph and gglyph.pop("export") == 0:
            exported = False
        g = Glyph(name=name, codepoints=cp or [], category=category, exported=exported)
        g.production_name = gglyph.pop("production", None)

        for layer in gglyph.pop("layers", []):
            g.layers.extend(self.load_layer(layer, g))

        _stash(g, gglyph)

        return g

    def load_layer(self, gslayer: dict, glyph: Glyph, width=None) -> List[Layer]:
        if width is None and "width" in gslayer:
            width = gslayer.pop("width")
        layer = Layer(
            width=width, id=gslayer.pop("layerId", ""), _font=self.font, _glyph=glyph
        )
        layer.vertWidth = gslayer.pop("vertWidth", None)
        layer.name = gslayer.pop("name", "")
        if [x for x in self.font.masters if x.id == layer.id]:
            layer._master = layer.id
        else:
            layer._master = gslayer.pop("associatedMasterId", None)
        layer.guides = [
            self.load_guide(x)
            for x in gslayer.pop("guideLines", gslayer.pop("guides", []))
        ]
        layer.shapes = []
        for shape in gslayer.pop("shapes", []):
            babelfont_shape = self.load_shape(shape)
            if babelfont_shape.is_component:
                babelfont_shape._layer = layer
            layer.shapes.append(babelfont_shape)
        for shape in gslayer.pop("paths", []):
            layer.shapes.append(self.load_path(shape))
        for shape in gslayer.pop("components", []):
            comp = self.load_component(shape)
            comp._layer = layer
            layer.shapes.append(comp)
        for anchor in gslayer.pop("anchors", []):
            layer.anchors.append(self.load_anchor(anchor))

        returns = [layer]
        layer.glyph = glyph
        if "background" in gslayer:
            (background,) = self.load_layer(
                gslayer["background"], glyph, width=layer.width
            )
            # If it doesn't have an ID, we need to generate one
            background.id = background.id or str(uuid.uuid1())
            background.isBackground = True

            layer.background = background.id
            returns.append(background)
        for r in returns:
            assert r.valid

        _stash(layer, gslayer)
        return returns

    def load_guide(self, gguide):
        g = Guide(
            pos=[*gguide.get("pos", (0, 0)), gguide.get("angle", 0)],
            name=gguide.get("name", None),
        )
        if gguide.get("locked"):
            if g.name is None:
                g.name = ""
            g.name += " [locked]"
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
        variable = ginstance.get("type") == "variable"
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
        elif variable:
            instance_location = None
        else:
            raise ValueError("Need to Synthesize location")
        name = ginstance.pop("name")
        i = Instance(
            name=name,
            variable=variable,
            location=instance_location,
        )
        # The instance name is also the style name, unless a custom prop is set
        i.customNames.styleName.set_default(name)
        props = ginstance.pop("properties", [])
        props_dict = {p["key"]: p["values"] for p in props}
        for glyphs_prop, our_name in _glyphs_instance_names_to_ours.items():
            if glyphs_prop in props_dict:
                for value in props_dict[glyphs_prop]:
                    name_entry: I18NDictionary = getattr(i.customNames, our_name)
                    name_entry[value["language"]] = value["value"]
        _stash(i, ginstance)
        return i

    def load_path(self, path):
        shape = Shape()
        shape.nodes = [Node(*n) for n in path["nodes"]]
        shape.closed = path["closed"]
        _stash(shape, path)
        if len(shape.nodes):
            # Bring it to front
            shape.nodes = shape.nodes[-1:] + shape.nodes[:-1]
        return shape

    def get_codepoint(self, gglyph):
        cp = gglyph.pop("unicode", None)
        if cp is not None and not isinstance(cp, list):
            cp = [cp]
        if cp:
            return [int(x) for x in cp]

    def interpret_kern_groups(self):
        for g in self.font.glyphs:
            left_group = _g(g, "kernLeft", pop=True)
            if left_group:
                self.font.second_kern_groups.setdefault(left_group, []).append(g.name)

            right_group = _g(g, "kernRight", pop=True)
            if right_group:
                self.font.first_kern_groups.setdefault(right_group, []).append(g.name)

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
        def ungroup(groupname):
            if groupname[0] != "@":
                return groupname
            return groupname.replace("@MMK_L", "@first_group").replace(
                "@MMK_R", "@second_group"
            )

        return {
            (ungroup(left), ungroup(right)): value
            for left, level2 in kerndict.items()
            for right, value in level2.items()
        }

    def interpret_metrics(self):
        metrics = _g(self.font, "metrics", [])  # Keep stashed
        metric_types = [_metrics_dict_to_name(k) for k in metrics]
        for master in self.font.masters:
            # Glyphs has these values as defaults:
            master.metrics["underlinePosition"] = -100
            master.metrics["underlineThickness"] = 50

            metric_values = _g(master, "metricValues", [], pop=True)
            master.metrics["italicAngle"] = 0
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
        # There may be a "Axis Mappings" custom parameter, if so use that
        axes_by_name = {a.name.get_default(): a for a in self.font.axes}

        if mapping := _stashed_cp(self.font, "Axis Mappings"):
            axes_by_tag = {a.tag: a for a in self.font.axes}
            for axistag, axismap in mapping.items():
                ax = axes_by_tag[axistag]
                ax.map = []
                for designspace, userspace in axismap.items():
                    ax.map.append((userspace, float(designspace)))
            return

        for instance in self.font.instances:
            # instance.location is in designspace
            # The Axis Location custom parameter is in userspace, use
            # this to make the map
            c = (
                _custom_parameter(
                    instance._formatspecific.get("com.glyphsapp", {}), "Axis Location"
                )
                or []
            )
            # If there isn't an Axis Location, use the weightclass and widthclass
            if not c:
                weightclass = instance._formatspecific.get("com.glyphsapp", {}).get(
                    "weightClass", 400
                )
                if weightclass is not None:
                    c.append({"Axis": "Weight", "Location": weightclass})
                widthclass = instance._formatspecific.get("com.glyphsapp", {}).get(
                    "widthClass", 5
                )
                if widthclass is not None:
                    c.append({"Axis": "Width", "Location": widthclass})
            for loc in c:
                ax = axes_by_name.get(loc["Axis"])
                if not ax:
                    # Maybe we don't have a weight or width but we don't have
                    # an axis location either so we synthesised those locations
                    continue
                if not ax.map:
                    ax.map = []
                ax.map.append(
                    (
                        int(loc["Location"]),  # The instances location in user space
                        instance.location[ax.tag],
                    )
                )

    def interpret_master_custom_parameters(self):
        for master in self.font.masters:
            cps = _g(master, "customParameters", [])
            new_cps = []
            for param in cps:
                if param["name"] in CORE_METRICS:
                    master.metrics[param["name"]] = param["value"]
                else:
                    new_cps.append(param)
            _stash(master, {"customParameters": new_cps})

    def interpret_font_custom_parameters(self):
        cps = _g(self.font, "customParameters", [])
        new_cps = []
        for param in cps:
            if param["name"] == "panose":
                self.font.custom_opentype_values[("OS/2", "panose")] = param["value"]
            # elif param["name"] == "fsType":
            #     self.font.custom_opentype_values[("OS/2", "fsType")] = int(
            #         param["value"]
            #     )
            elif param["name"] == "fsSelection":
                self.font.custom_opentype_values[("OS/2", "fsSelection")] = int(
                    param["value"]
                )
            else:
                new_cps.append(param)
        _stash(self.font, {"customParameters": new_cps})

    def interpret_features(self):
        self.font.features = Features()

        def code_with_notes(feature):
            code = feature["code"]
            if "disabled" in feature:
                code = "# Disabled\n# " + code.replace("\n", "\n# ")
            if "automatic" in feature:
                code = "# Automatic\n" + code
            if "labels" in feature:
                code += "\n".join(labels_to_feature(feature["labels"]))

            return code

        for glyphclass in _g(self.font, "classes", [], pop=True):
            # Beware of tokens XXX
            self.font.features.classes[glyphclass["name"]] = glyphclass["code"].split()
        for prefix in _g(self.font, "featurePrefixes", [], pop=True):
            self.font.features.prefixes[prefix["name"]] = code_with_notes(prefix)
        for feature in _g(self.font, "features", [], pop=True):
            tag = feature.get("tag", feature.get("name"))
            self.font.features.features.append((tag, code_with_notes(feature)))

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
                if k in custom_parameter_metrics:
                    continue
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
        self.save_features(out)

        with open(self.filename, "wb") as file:
            openstep_plist.dump(out, file, indent=0, single_line_tuples=True)
            file.write(b"\n")

    def save_axis(self, axis):
        gaxis = _moveformatspecific(axis)
        _copyattrs(axis, gaxis, ["name", "tag"])
        return gaxis

    def save_kerning(self, kerntable):
        newtable = {}
        for (left, right), val in kerntable.items():
            left = left.replace("@first_group", "@MMK_L").replace(
                "@second_group", "@MMK_R"
            )
            right = right.replace("@first_group", "@MMK_L").replace(
                "@second_group", "@MMK_R"
            )
            newtable.setdefault(left, {})[right] = val
        return newtable

    def save_master(self, master):
        gmaster = _moveformatspecific(master)
        if master.location:
            gmaster["axesValues"] = list(master.location.values())
        gmaster["metricValues"] = []
        if "customParameters" not in gmaster:
            gmaster["customParameters"] = []
        for metric in custom_parameter_metrics:
            if metric in self.font.default_master.metrics:
                gmaster["customParameters"].append(
                    {
                        "name": metric,
                        "value": self.font.default_master.metrics[metric],
                    }
                )
        if not gmaster["customParameters"]:
            del gmaster["customParameters"]

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
        gglyph["layers"] = [
            self.save_layer(layer) for layer in glyph.layers if not layer.isBackground
        ]
        if glyph.production_name is not None and glyph.production_name != glyph.name:
            gglyph["production"] = glyph.production_name
        if not glyph.exported:
            gglyph["export"] = 0
        # Check for kern groups
        for group, members in self.font.second_kern_groups.items():
            if glyph.name in members:
                gglyph["kernLeft"] = group
        for group, members in self.font.first_kern_groups.items():
            if glyph.name in members:
                gglyph["kernRight"] = group
        # XXX
        return gglyph

    def save_layer(self, layer):
        glayer = _moveformatspecific(layer)
        _copyattrs(layer, glayer, ["width", "name"])
        if layer.vertWidth is not None:
            glayer["vertWidth"] = layer.vertWidth
        glayer["layerId"] = str(layer.id)
        if layer.guides:
            glayer["guides"] = [self.save_guide(g) for g in layer.guides]
        if layer.shapes:
            glayer["shapes"] = [self.save_shape(s) for s in layer.shapes]
        if layer._master and layer._master != layer.id:
            glayer["associatedMasterId"] = layer._master
        if layer.anchors:
            glayer["anchors"] = [self.save_anchor(a) for a in layer.anchors]
        if layer.background:
            glayer["background"] = self.save_layer(layer._background_layer())
            if "width" in glayer["background"]:
                del glayer["background"]["width"]
            if "layerId" in glayer["background"]:
                del glayer["background"]["layerId"]
        return glayer

    def save_shape(self, shape):
        gshape = _moveformatspecific(shape)
        if shape.is_path:
            gshape["closed"] = shape.closed
            outputnodes = []
            if len(shape.nodes):
                # Put front back at end
                outputnodes = shape.nodes[1:] + [shape.nodes[0]]

            gshape["nodes"] = [self.save_node(n) for n in outputnodes]
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
        if instance.variable:
            ginstance["type"] = "variable"
        else:
            ginstance["axesValues"] = [
                instance.location[ax.tag] for ax in self.font.axes
            ]
        for glyphs, ours in _glyphs_instance_names_to_ours.items():
            if getattr(instance.customNames, ours).get_default():
                if "properties" not in ginstance:
                    ginstance["properties"] = []
                ginstance["properties"].append(
                    {
                        "key": glyphs,
                        "values": glyphs_i18ndict(getattr(instance.customNames, ours)),
                    }
                )

        return ginstance

    def save_anchor(self, anchor):
        ganchor = _moveformatspecific(anchor)
        ganchor["name"] = anchor.name
        ganchor["pos"] = (anchor.x, anchor.y)
        return ganchor

    def save_metadata(self, out):
        if self.font.note:
            out["note"] = self.font.note
        if self.font.version:
            out["versionMajor"], out["versionMinor"] = self.font.version
        if "properties" not in out:
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
        if self.font.custom_opentype_values.get(("OS/2", "achVendID")):
            props.append(
                {
                    "key": "vendorID",
                    "value": self.font.custom_opentype_values[("OS/2", "achVendID")],
                }
            )
        if not props:
            del out["properties"]

    def save_custom_parameters(self, out):
        if "customParameters" not in out:
            out["customParameters"] = []
        for (table, field), value in self.font.custom_opentype_values.items():
            if table == "OS/2" and field == "fsType":
                out["customParameters"].append(
                    {"name": "fsType", "value": to_bitfield(int(value))}
                )
            if table == "OS/2" and field == "fsSelection":
                if value & (1 << 7):
                    out["customParameters"].append(
                        {"name": "Use Typo Metrics", "value": 1}
                    )
                if value & (1 << 8):
                    out["customParameters"].append(
                        {"name": "Has WWS Names", "value": 1}
                    )
        if not out["customParameters"]:
            del out["customParameters"]

    def save_features(self, out):
        # In truth we should probably steal glyphsLib.builder.features._process_feature_block
        def _save_item(key, value, name):
            item = {}
            item[name] = key
            if value.startswith("# Automatic\n"):
                item["automatic"] = True
                value = re.sub("^# Automatic\n", "", value, flags=re.MULTILINE)
            if value.startswith("# Disabled\n"):
                item["disabled"] = True
                value = re.sub("^#", "", value[10:], flags=re.MULTILINE)
            item["code"] = value
            return item

        if self.font.features:
            out["classes"] = [
                {"name": k, "code": " ".join(v)}
                for k, v in self.font.features.classes.items()
            ]
            out["featurePrefixes"] = [
                _save_item(k, v, "name") for k, v in self.font.features.prefixes.items()
            ]
            out["features"] = [
                _save_item(k, v, "tag") for k, v in self.font.features.features
            ]
        else:
            out["classes"] = []
            out["featurePrefixes"] = []
            out["features"] = []
        if not out["classes"]:
            del out["classes"]
        if not out["featurePrefixes"]:
            del out["featurePrefixes"]
        if not out["features"]:
            del out["features"]
