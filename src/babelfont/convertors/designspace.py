import logging
from typing import Dict, List
import time
import uuid

import ufoLib2
from fontTools import designspaceLib
from fontTools.designspaceLib import DesignSpaceDocument
from fontTools.misc import timeTools

from babelfont import (
    Features,
    Font,
    Master,
    Instance,
    Glyph,
    Layer,
    Shape,
    Node,
    Anchor,
    Guide,
    Axis,
    I18NDictionary,
)
from babelfont.convertors import BaseConvertor

log = logging.getLogger(__name__)

UFO_KEY = "org.unifiedfontobject"

metrics = {
    "xHeight": "xHeight",
    "capHeight": "capHeight",
    "ascender": "ascender",
    "descender": "descender",
    "italicAngle": "italicAngle",
    "hheaAscender": "openTypeHheaAscender",
    "hheaDescender": "openTypeHheaDescender",
    "hheaLineGap": "openTypeHheaLineGap",
    "winAscent": "openTypeOS2WinAscent",
    "winDescent": "openTypeOS2WinDescent",
    "typoAscender": "openTypeOS2TypoAscender",
    "typoDescender": "openTypeOS2TypoDescender",
    "typoLineGap": "openTypeOS2TypoLineGap",
    "subscriptXSize": "openTypeOS2SubscriptXSize",
    "subscriptYSize": "openTypeOS2SubscriptYSize",
    "subscriptXOffset": "openTypeOS2SubscriptXOffset",
    "subscriptYOffset": "openTypeOS2SubscriptYOffset",
    "superscriptXSize": "openTypeOS2SuperscriptXSize",
    "superscriptYSize": "openTypeOS2SuperscriptYSize",
    "superscriptXOffset": "openTypeOS2SuperscriptXOffset",
    "superscriptYOffset": "openTypeOS2SuperscriptYOffset",
    "strikeoutSize": "openTypeOS2StrikeoutSize",
    "strikeoutPosition": "openTypeOS2StrikeoutPosition",
    "underlinePosition": "postscriptUnderlinePosition",
    "underlineThickness": "postscriptUnderlineThickness",
    "hheaCaretSlopeRise": "openTypeHheaCaretSlopeRise",
    "hheaCaretSlopeRun": "openTypeHheaCaretSlopeRun",
    "hheaCaretOffset": "openTypeHheaCaretOffset",
}

# Unicode ranges / code page ranges are special

ufo_custom_opentype_values = {
    "openTypeGaspRangeRecords": ("GASP", "gaspRange"),
    # XX more gasp here
    "openTypeHeadCreated": ("head", "created"),
    "openTypeHeadLowestRecPPEM": ("head", "lowestRecPPEM"),
    "openTypeHeadFlags": ("head", "flags"),
    "openTypeOS2WidthClass": ("OS/2", "usWidthClass"),
    "openTypeOS2WeightClass": ("OS/2", "usWeightClass"),
    "openTypeOS2Selection": ("OS/2", "fsSelection"),
    "openTypeOS2VendorID": ("OS/2", "achVendID"),
    "openTypeOS2Panose": ("OS/2", "bPanose"),
    "openTypeOS2FamilyClass": ("OS/2", "sFamilyClass"),
    "openTypeOS2Type": ("OS/2", "fsType"),
}

BITARRAY = [
    ("head", "flags"),
    ("GASP", "gaspRange"),
    ("OS/2", "fsType"),
    ("OS/2", "fsSelection"),
]


def bitarray_to_int(value):
    return sum(2**i for i in value)


def int_to_bitarray(value):
    return [i for i in range(32) if value & 2**i]


def ribbi(style: str) -> bool:
    return style.lower() in ["regular", "italic", "bold", "bold italic"]


class Designspace(BaseConvertor):
    suffix = ".designspace"

    @classmethod
    def load(cls, convertor, compile_only=False):
        self = cls()
        self.ds = DesignSpaceDocument.fromfile(convertor.filename)
        self.ds.loadSourceFonts(ufoLib2.Font.open)
        self.font = Font()
        return self._load()

    def _load(self):
        self._load_axes()

        for source in self.ds.sources:
            source._babelfont_master = self._load_master(source)
            self.font.masters.append(source._babelfont_master)

        for instance in self.ds.instances:
            self.font.instances.append(self._load_instance(instance))

        firstmaster = self.ds.sources[0].font
        self._load_metadata(firstmaster)
        glyphs_dict = self._load_glyphs(firstmaster)

        # Right, let's find all the layers. This will be messy.
        for source in self.ds.sources:
            for ufo_layer in source.font.layers:
                for g in source.font.keys():
                    if g not in glyphs_dict:
                        log.warning(
                            "Incompatible glyph set: %s appears in %s but is not in default",
                            g,
                            source.filename,
                        )
                        continue
                    if g not in ufo_layer:
                        continue
                    glyphs_dict[g].layers.append(self._load_layer(source, ufo_layer, g))
        self._fixup_glyph_exported(self.ds.sources[0].font)
        return self.font

    def _fixup_glyph_exported(self, ufo: ufoLib2.Font):
        for glyph in ufo.lib.get("public.skipExportGlyphs", []):
            self.font.glyphs[glyph].exported = False

    def _load_glyphs(self, master: ufoLib2.Font):
        glyphs_dict = {}
        # Start with glyph order if there is one
        order = master.lib.get("public.glyphOrder", [])
        # Then add any remaining glyphs
        order += [g for g in master.keys() if g not in order]
        for g in order:
            glyphs_dict[g] = self._load_glyph(master[g])
            self.font.glyphs.append(glyphs_dict[g])
        return glyphs_dict

    def _load_axes(self):
        for a in self.ds.axes:
            self.font.axes.append(
                Axis(
                    name=a.name,
                    tag=a.tag,
                    min=a.minimum,
                    max=a.maximum,
                    default=a.default,
                    map=a.map,
                )
            )

    def _load_master(self, source: designspaceLib.SourceDescriptor):
        font: ufoLib2.Font = source.font
        i = font.info
        master = Master(
            name=source.name,
            id=(source.name or uuid.uuid1()),
        )
        for our_metric, their_metric in metrics.items():
            master.metrics[our_metric] = getattr(i, their_metric)
        _axis_name_to_id = {a.name.get_default(): a.tag for a in self.font.axes}
        # names XXX
        # guidelines
        master.guides = [self._load_guide(g) for g in (i.guidelines or [])]
        master.location = {_axis_name_to_id[k]: v for k, v in source.location.items()}
        master.font = self.font
        master.kerning = self._load_kerning(source)
        for key, value in font.lib.items():
            if not key.startswith("public."):
                if UFO_KEY not in master._formatspecific:
                    master._formatspecific[UFO_KEY] = {}
                master._formatspecific[UFO_KEY][key] = value
        assert master.valid
        return master

    def _load_groups(self, groups: Dict[str, List[str]]):
        for name, value in groups.items():
            self.font.features.classes[name] = value

    def _load_guide(self, ufo_guide: ufoLib2.objects.Guideline):
        return Guide(
            pos=[ufo_guide.x, ufo_guide.y, ufo_guide.angle],
            name=ufo_guide.name,
            color=ufo_guide.color,
        )

    def _load_kerning(self, source: designspaceLib.SourceDescriptor):
        font: ufoLib2.Font = source.font
        kerning = {}
        for (left, right), value in font.kerning.items():
            if left.startswith("public.kern"):
                left = "@" + left
            if right.startswith("public.kern"):
                right = "@" + right
            kerning[(left, right)] = value
        return kerning

    def _load_glyph(self, ufo_glyph: ufoLib2.objects.Glyph):
        cp = []
        if ufo_glyph.unicodes or ufo_glyph.unicode:
            cp = ufo_glyph.unicodes or [ufo_glyph.unicode]
        lib = self.ds.sources[0].font.lib
        category = lib.get("public.openTypeCategories", {}).get(ufo_glyph.name, "base")
        g = Glyph(name=ufo_glyph.name, codepoints=cp, category=category)

        if "public.postscriptNames" in lib and g.name in lib["public.postscriptNames"]:
            g.production_name = lib["public.postscriptNames"][g.name]
        return g

    def _load_layer(
        self, source: designspaceLib.SourceDescriptor, ufo_layer, glyphname: str
    ):
        if ufo_layer.name == "public.default":
            layer_id = source._babelfont_master.id
        else:
            layer_id = ufo_layer.name
        ufo_glyph = ufo_layer[glyphname]
        width = ufo_glyph.width
        layer = Layer(width=width, id=layer_id)
        layer._master = source._babelfont_master.id
        layer._font = self.font
        layer._glyph = self.font.glyphs[glyphname]
        for contour in ufo_glyph:
            layer.shapes.append(self._load_contour(contour))
        for component in ufo_glyph.components:
            layer.shapes.append(self._load_component(component))
        for anchor in ufo_glyph.anchors:
            layer.anchors.append(self._load_anchor(anchor))
        assert layer.valid
        return layer

    def _load_component(self, shape: ufoLib2.objects.Component):
        c = Shape(ref=shape.baseGlyph, transform=shape.transformation)
        return c

    def _load_anchor(self, anchor: ufoLib2.objects.Anchor):
        return Anchor(name=anchor.name, x=int(anchor.x), y=int(anchor.y))

    def _load_contour(self, contour):
        shape = Shape()
        shape.nodes = []
        for p in contour:
            segtype = p.segmentType
            if p.segmentType == "move":
                segtype = "line"
            ourtype = Node._from_pen_type[segtype]
            if p.smooth:
                ourtype = ourtype + "s"
            shape.nodes.append(Node(p.x, p.y, ourtype))
        return shape

    def _load_instance(self, ufo_instance):
        _axis_tag = {axis.name.get_default(): axis.tag for axis in self.font.axes}
        location = {_axis_tag[k]: v for k, v in ufo_instance.location.items()}
        instance = Instance(name=ufo_instance.name, location=location)
        return instance

    names_dict = {
        "designer": "openTypeNameDesigner",
        "designerURL": "openTypeNameDesignerURL",
        "manufacturer": "openTypeNameManufacturer",
        "manufacturerURL": "openTypeNameManufacturerURL",
        "license": "openTypeNameLicense",
        "licenseURL": "openTypeNameLicenseURL",
        "version": "openTypeNameVersion",
        "uniqueID": "openTypeNameUniqueID",
        "description": "openTypeNameDescription",
        "compatibleFullName": "openTypeNameCompatibleFullName",
        "sampleText": "openTypeNameSampleText",
        "WWSFamilyName": "openTypeNameWWSFamilyName",
        "WWSSubfamilyName": "openTypeNameWWSSubfamilyName",
        "copyright": "copyright",
        "styleMapFamilyName": "styleMapFamilyName",
        "familyName": "familyName",
        "trademark": "trademark",
        "styleName": "styleName",
        "styleMapStyleName": "styleMapStyleName",
        "preferredSubfamilyName": "openTypeNamePreferredSubfamilyName",
    }

    def _load_metadata(self, ufo):
        firstfontinfo = ufo.info
        self.font.upm = firstfontinfo.unitsPerEm
        self.font.version = (firstfontinfo.versionMajor, firstfontinfo.versionMinor)
        self.font.note = firstfontinfo.note
        for ours, theirs in self.names_dict.items():
            their_value = getattr(firstfontinfo, theirs)
            if their_value:
                getattr(self.font.names, ours).set_default(their_value)
        for ufofield, (table, field) in ufo_custom_opentype_values.items():
            if getattr(firstfontinfo, ufofield) is not None:
                value = getattr(firstfontinfo, ufofield)
                if (table, field) in BITARRAY:
                    value = bitarray_to_int(value)
                self.font.custom_opentype_values[(table, field)] = value

        self.font.features = Features.from_fea(ufo.features.text)
        self._load_groups(ufo.groups)

    def _save(self):
        self.ds = DesignSpaceDocument()
        self.save_axes()
        self.save_sources()
        self.save_instances()
        # Lib
        unexported = [g.name for g in self.font.glyphs if not g.exported]
        if unexported:
            self.ds.lib["public.skipExportGlyphs"] = sorted(unexported)
        self.ds.write(self.filename)

    def save_axes(self):
        axes = self.font.axes
        if not axes:
            axes = [
                Axis(
                    name=I18NDictionary.with_default("Weight"),
                    tag="wght",
                    min=100,
                    max=100,
                    default=100,
                )
            ]
        for axis in axes:
            axisDescriptor = designspaceLib.AxisDescriptor()
            axisDescriptor.name = axis.name.get_default()
            other_names = axis.name.as_fonttools_dict
            if other_names:
                axis.labelNames = other_names
            axisDescriptor.tag = axis.tag
            axisDescriptor.minimum = axis.min
            axisDescriptor.maximum = axis.max
            axisDescriptor.default = axis.default
            axisDescriptor.map = axis.map
            self.ds.addAxis(axisDescriptor)

    def _master_filename(self, master):
        return (
            self.font.names.familyName.get_default().replace(" ", "")
            + "-"
            + master.name.get_default().replace(" ", "")
            + ".ufo"
        )

    def save_sources(self):
        font = self.font
        for master in font.masters:
            sourceDescriptor = designspaceLib.SourceDescriptor()
            sourceDescriptor.name = (
                font.names.familyName.get_default() + " " + master.name.get_default()
            )
            sourceDescriptor.filename = self._master_filename(master)
            sourceDescriptor.styleName = master.name.get_default()
            sourceDescriptor.familyName = font.names.familyName.get_default()
            if master == self.font.default_master:
                sourceDescriptor.copyLib = True
                sourceDescriptor.copyGroups = True
                sourceDescriptor.copyFeatures = True
                sourceDescriptor.copyInfo = True
            # sourceDescriptor.filename = master.filename
            # sourceDescriptor.path = master.filename
            axis_tags_to_names = {
                axis.tag: axis.name.get_default() for axis in self.font.axes
            }
            if master.location:
                sourceDescriptor.location = {
                    axis_tags_to_names[ax]: value
                    for ax, value in master.location.items()
                }
            else:
                sourceDescriptor.location = {"Weight": 100}
            self.ds.addSource(sourceDescriptor)
            self.save_master_to_ufo(
                master,
                self._master_filename(master),
                is_default=(master == self.font.default_master),
            )

    def save_instances(self):
        for instance in self.font.instances:
            instanceDescriptor = designspaceLib.InstanceDescriptor()
            instanceDescriptor.name = (
                self.font.names.familyName.get_default()
                + " "
                + instance.name.get_default()
            )
            names = self.font.names
            instanceDescriptor.familyName = names.familyName.get_default()
            instanceDescriptor.styleName = instance.name.get_default()
            instanceDescriptor.styleMapFamilyName = (
                names.styleMapFamilyName.get_default() or names.familyName.get_default()
            )
            if not ribbi(instance.name.get_default()):
                instanceDescriptor.styleMapFamilyName += (
                    " " + instance.name.get_default()
                )
                instanceDescriptor.styleMapStyleName = "regular"
            axis_tags_to_names = {
                axis.tag: axis.name.get_default() for axis in self.font.axes
            }
            if instance.location:
                instanceDescriptor.location = {
                    axis_tags_to_names[ax]: value
                    for ax, value in instance.location.items()
                }
            else:
                instanceDescriptor.location = {"Weight": 400}
            self.ds.addInstance(instanceDescriptor)

    def save_master_to_ufo(self, master: Master, filename, is_default=False):
        ufo = ufoLib2.Font()
        ufo.info.unitsPerEm = self.font.upm
        ufo.info.versionMajor, ufo.info.versionMinor = self.font.version
        if self.font.note and is_default:
            ufo.info.note = self.font.note
        for ours, theirs in self.names_dict.items():
            our_value = getattr(self.font.names, ours).get_default()
            if our_value is not None:
                setattr(ufo.info, theirs, getattr(self.font.names, ours).get_default())
        if not ufo.info.styleName:
            ufo.info.styleName = master.name.get_default()
        for glyph in self.font.glyphs:
            ufo.newGlyph(glyph.name)
        for glyph in self.font.glyphs:
            ufo_glyph = ufo[glyph.name]
            layer = master.get_glyph_layer(glyph.name)
            assert layer
            self.save_layer_to_ufo(ufo_glyph, layer)
            ufo_glyph.unicodes = [int(cp) for cp in glyph.codepoints]
            if layer.background is not None:
                if "public.background" not in ufo.layers:
                    ufo.layers.newLayer("public.background")
                background_layer = None
                for possible_background_layer in glyph.layers:
                    if possible_background_layer.id == layer.background:
                        background_layer = possible_background_layer
                if background_layer:
                    background_glyph = ufo.layers["public.background"].newGlyph(
                        glyph.name
                    )
                    self.save_layer_to_ufo(background_glyph, background_layer)
        # Metrics
        for our_metric, their_metric in metrics.items():
            if our_metric in master.metrics:
                metric_value = master.metrics[our_metric]
                if their_metric in ["openTypeOS2WinDescent"] and metric_value < 0:
                    metric_value = -metric_value
                setattr(ufo.info, their_metric, metric_value)
        if is_default:
            for info_tag, (table, field) in ufo_custom_opentype_values.items():
                if (table, field) in self.font.custom_opentype_values:
                    value = self.font.custom_opentype_values[(table, field)]
                    if (table, field) in BITARRAY:
                        if info_tag == "openTypeOS2Selection":
                            # "Bits 0 (italic), 5 (bold) and 6 (regular) must not be set here"
                            value = value & 0b11111100
                        value = int_to_bitarray(value)
                    if info_tag == "openTypeHeadCreated":
                        value = time.strftime(
                            "%Y/%m/%d %H:%M:%S",
                            time.gmtime(timeTools.epoch_diff + value),
                        )

                    setattr(ufo.info, info_tag, value)
        # Guides
        if master.guides:
            ufo.info.guidelines = []
        for guide in master.guides:
            ufo.info.guidelines.append(
                ufoLib2.objects.Guideline(
                    x=guide.pos[0],
                    y=guide.pos[1],
                    angle=guide.pos[2] % 360,
                    name=guide.name,
                    color=guide.color,
                )
            )
        # Kerning
        for group, members in self.font.first_kern_groups.items():
            ufo.groups["public.kern1." + group] = members
        for group, members in self.font.second_kern_groups.items():
            ufo.groups["public.kern2." + group] = members
        for (left, right), value in master.kerning.items():
            if left.startswith("@first_group_"):
                left = "public.kern1." + left[13:]
            if right.startswith("@second_group_"):
                right = "public.kern2." + right[14:]
            ufo.kerning[left, right] = value

        # Features and groups
        ufo.features.text = self.font.features.to_fea()
        # Lib
        ufo.lib["public.glyphOrder"] = [g.name for g in self.font.glyphs]
        psnames = {
            g.name: g.production_name for g in self.font.glyphs if g.production_name
        }
        if psnames:
            ufo.lib["public.postscriptNames"] = psnames
        for key, value in master._formatspecific.get(UFO_KEY, {}).items():
            ufo.lib[key] = value
        self.logger.info("Saving %s", filename)
        ufo.save(filename, overwrite=True)

    def save_layer_to_ufo(self, ufo_glyph: ufoLib2.objects.Glyph, layer: Layer):
        for shape in layer.shapes:
            if shape.is_component:
                self.save_component_to_ufo(ufo_glyph, shape)
            else:
                self.save_contour_to_ufo(ufo_glyph, shape)
        for anchor in layer.anchors:
            self.save_anchor_to_ufo(ufo_glyph, anchor)
        ufo_glyph.width = layer.width
        if layer.height:
            ufo_glyph.height = layer.height

    def save_anchor_to_ufo(self, ufo_glyph: ufoLib2.objects.Glyph, anchor: Anchor):
        ufo_glyph.appendAnchor(
            ufoLib2.objects.Anchor(name=anchor.name, x=anchor.x, y=anchor.y)
        )

    def save_component_to_ufo(self, ufo_glyph: ufoLib2.objects.Glyph, shape: Shape):
        ufo_glyph.components.append(
            ufoLib2.objects.Component(
                baseGlyph=shape.ref,
                transformation=shape.transform,
            )
        )

    def save_contour_to_ufo(self, ufo_glyph: ufoLib2.objects.Glyph, shape: Shape):
        pen = ufo_glyph.getPointPen()
        pen.beginPath()
        for node in shape.nodes:
            pen.addPoint(
                (node.x, node.y),
                segmentType=Node._to_pen_type[node.type[0]],
                smooth=node.is_smooth,
            )
        pen.endPath()
