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
