from .BaseObject import BaseObject, I18NDictionary


class Names(BaseObject):
    familyName: I18NDictionary = None
    designer: I18NDictionary = None
    designerURL: I18NDictionary = None
    manufacturer: I18NDictionary = None
    manufacturerURL: I18NDictionary = None
    license: I18NDictionary = None
    licenseURL: I18NDictionary = None
    version: I18NDictionary = None
    uniqueID: I18NDictionary = None
    description: I18NDictionary = None
    preferredFamilyName: I18NDictionary = None
    preferredSubfamilyName: I18NDictionary = None
    compatibleFullName: I18NDictionary = None
    sampleText: I18NDictionary = None
    WWSFamilyName: I18NDictionary = None
    WWSSubfamilyName: I18NDictionary = None
    copyright: I18NDictionary = None
    styleMapFamilyName: I18NDictionary = None
    trademark: I18NDictionary = None

    _serialize_slots = __annotations__.keys()

    def __post_init__(self):
        for k in self._serialize_slots:
            if not getattr(self, k):
                setattr(self, k, I18NDictionary())
