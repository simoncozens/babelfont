---
title: Names
---
Names(_formatspecific: dict = <factory>, _: dict = None, familyName: nfsf.BaseObject.I18NDictionary = None, designer: nfsf.BaseObject.I18NDictionary = None, designerURL: nfsf.BaseObject.I18NDictionary = None, manufacturer: nfsf.BaseObject.I18NDictionary = None, manufacturerURL: nfsf.BaseObject.I18NDictionary = None, license: nfsf.BaseObject.I18NDictionary = None, licenseURL: nfsf.BaseObject.I18NDictionary = None, version: nfsf.BaseObject.I18NDictionary = None, uniqueID: nfsf.BaseObject.I18NDictionary = None, description: nfsf.BaseObject.I18NDictionary = None, preferredFamilyName: nfsf.BaseObject.I18NDictionary = None, preferredSubfamilyName: nfsf.BaseObject.I18NDictionary = None, compatibleFullName: nfsf.BaseObject.I18NDictionary = None, sampleText: nfsf.BaseObject.I18NDictionary = None, WWSFamilyName: nfsf.BaseObject.I18NDictionary = None, WWSSubfamilyName: nfsf.BaseObject.I18NDictionary = None, copyright: nfsf.BaseObject.I18NDictionary = None, styleMapFamilyName: nfsf.BaseObject.I18NDictionary = None, trademark: nfsf.BaseObject.I18NDictionary = None)
## Names._formatspecific

* Python type: `dict`


Each object in NFSF has an optional attached dictionary to allow the storage
of format-specific information. Font creation software may store any additional
information that they wish to have preserved on import and export under a
namespaced (reverse-domain) key in this dictionary. For example, information
specific to the Glyphs software should be stored under the key `com.glyphsapp`.
The value stored under this key may be any data serializable in JSON; typically
it will be a `dict`.

Note that there is an important distinction between the Python object format
of this field and the NFSF-JSON representation. When stored to JSON, this key
is exported not as `_formatspecific` but as a simple underscore (`_`).



## Names.familyName

* Python type: `I18NDictionary`

*If not provided, defaults to* `None`.


## Names.designer

* Python type: `I18NDictionary`

*If not provided, defaults to* `None`.


## Names.designerURL

* Python type: `I18NDictionary`

*If not provided, defaults to* `None`.


## Names.manufacturer

* Python type: `I18NDictionary`

*If not provided, defaults to* `None`.


## Names.manufacturerURL

* Python type: `I18NDictionary`

*If not provided, defaults to* `None`.


## Names.license

* Python type: `I18NDictionary`

*If not provided, defaults to* `None`.


## Names.licenseURL

* Python type: `I18NDictionary`

*If not provided, defaults to* `None`.


## Names.version

* Python type: `I18NDictionary`

*If not provided, defaults to* `None`.


## Names.uniqueID

* Python type: `I18NDictionary`

*If not provided, defaults to* `None`.


## Names.description

* Python type: `I18NDictionary`

*If not provided, defaults to* `None`.


## Names.preferredFamilyName

* Python type: `I18NDictionary`

*If not provided, defaults to* `None`.


## Names.preferredSubfamilyName

* Python type: `I18NDictionary`

*If not provided, defaults to* `None`.


## Names.compatibleFullName

* Python type: `I18NDictionary`

*If not provided, defaults to* `None`.


## Names.sampleText

* Python type: `I18NDictionary`

*If not provided, defaults to* `None`.


## Names.WWSFamilyName

* Python type: `I18NDictionary`

*If not provided, defaults to* `None`.


## Names.WWSSubfamilyName

* Python type: `I18NDictionary`

*If not provided, defaults to* `None`.


## Names.copyright

* Python type: `I18NDictionary`

*If not provided, defaults to* `None`.


## Names.styleMapFamilyName

* Python type: `I18NDictionary`

*If not provided, defaults to* `None`.


## Names.trademark

* Python type: `I18NDictionary`

*If not provided, defaults to* `None`.


