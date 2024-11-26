from .BaseObject import BaseObject, I18NDictionary
from dataclasses import dataclass, asdict, fields

OPENTYPE_NAMES = [
    "copyright",
    "familyName",
    "preferredSubfamilyName",
    "uniqueID",
    "fullName",  # XXX?
    "version",
    "postscriptName",
    "trademark",
    "manufacturer",
    "designer",
    "description",
    "manufacturerURL",
    "designerURL",
    "license",
    "licenseURL",
    "reserved",
    "typographicFamily",
    "typographicSubfamily",
    "compatibleFullName",
    "sampleText",
    "postscriptCIDname",  # XXX?
    "WWSFamilyName",
    "WWSSubfamilyName",
]


@dataclass
class Names(BaseObject):
    """A table of global, localizable names for the font."""

    familyName: I18NDictionary = None  # Name ID 1 if styleMapFamilyName is not present
    styleName: I18NDictionary = None  # Name ID 17 if no typographicSubfamily

    copyright: I18NDictionary = None  # Name ID 0
    styleMapFamilyName: I18NDictionary = None  # Name ID 1
    styleMapStyleName: I18NDictionary = None  # Name ID 2
    uniqueID: I18NDictionary = None  # Name ID 3
    fullName: I18NDictionary = None  # Name ID 4
    version: I18NDictionary = None  # Name ID 5
    postscriptName: I18NDictionary = None  # Name ID 6
    trademark: I18NDictionary = None  # Name ID 7
    manufacturer: I18NDictionary = None  # Name ID 8
    designer: I18NDictionary = None  # Name ID 9
    description: I18NDictionary = None  # Name ID 10
    manufacturerURL: I18NDictionary = None  # Name ID 11
    designerURL: I18NDictionary = None  # Name ID 12
    license: I18NDictionary = None  # Name ID 13
    licenseURL: I18NDictionary = None  # Name ID 14
    typographicFamily: I18NDictionary = None  # Name ID 16
    typographicSubfamily: I18NDictionary = None  # Name ID 17
    compatibleFullName: I18NDictionary = None  # Name ID 18
    sampleText: I18NDictionary = None  # Name ID 19
    WWSFamilyName: I18NDictionary = None  # Name ID 21
    WWSSubfamilyName: I18NDictionary = None  # Name ID 22

    def __post_init__(self):
        for k in fields(self):
            if not getattr(self, k.name):
                setattr(self, k.name, I18NDictionary())

    def as_nametable_dict(self):
        rv = {}
        ft_names = {
            "manufacturerURL": "vendorURL",
            "license": "licenseDescription",
            "licenseURL": "licenseInfoURL",
        }
        for k, v in asdict(self).items():
            if not v:
                continue
            rv[ft_names.get(k, k)] = v.default_or_dict()
        return rv

    def __getitem__(self, key):
        try:
            key = int(key)
        except ValueError as exc:
            raise ValueError("Name ID must be an integer") from exc
        if key == 0:
            return self.copyright
        if key == 1:
            return self.styleMapFamilyName or self.familyName
        if key == 2:
            return self.styleMapStyleName
        if key == 3:
            return self.uniqueID
        if key == 4:
            return self.fullName
        if key == 5:
            return self.version
        if key == 6:
            return self.postscriptName
        if key == 7:
            return self.trademark
        if key == 8:
            return self.manufacturer
        if key == 9:
            return self.designer
        if key == 10:
            return self.description
        if key == 11:
            return self.manufacturerURL
        if key == 12:
            return self.designerURL
        if key == 13:
            return self.license
        if key == 14:
            return self.licenseURL
        if key == 16:
            return self.typographicFamily
        if key == 17:
            return self.typographicSubfamily or self.styleName
        if key == 18:
            return self.compatibleFullName
        if key == 19:
            return self.sampleText
        if key == 21:
            return self.WWSFamilyName
        if key == 22:
            return self.WWSSubfamilyName
        return None
