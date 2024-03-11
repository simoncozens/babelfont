---
title: Names
---
A table of global, localizable names for the font.
## Names._formatspecific

* Python type: `dict`


Each object in Babelfont has an optional attached dictionary to allow the storage
of format-specific information. Font creation software may store any additional
information that they wish to have preserved on import and export under a
namespaced (reverse-domain) key in this dictionary. For example, information
specific to the Glyphs software should be stored under the key `com.glyphsapp`.
The value stored under this key may be any data serializable in JSON; typically
it will be a `dict`.

Note that there is an important distinction between the Python object format
of this field and the Babelfont-JSON representation. When stored to JSON, this key
is exported not as `_formatspecific` but as a simple underscore (`_`).



## Names.familyName

* Python type: `I18NDictionary`

 *Localizable.*
*If not provided, defaults to* `None`.


## Names.designer

* Python type: `I18NDictionary`

 *Localizable.*
*If not provided, defaults to* `None`.


## Names.designerURL

* Python type: `I18NDictionary`

 *Localizable.*
*If not provided, defaults to* `None`.


## Names.manufacturer

* Python type: `I18NDictionary`

 *Localizable.*
*If not provided, defaults to* `None`.


## Names.manufacturerURL

* Python type: `I18NDictionary`

 *Localizable.*
*If not provided, defaults to* `None`.


## Names.license

* Python type: `I18NDictionary`

 *Localizable.*
*If not provided, defaults to* `None`.


## Names.licenseURL

* Python type: `I18NDictionary`

 *Localizable.*
*If not provided, defaults to* `None`.


## Names.version

* Python type: `I18NDictionary`

 *Localizable.*
*If not provided, defaults to* `None`.


## Names.uniqueID

* Python type: `I18NDictionary`

 *Localizable.*
*If not provided, defaults to* `None`.


## Names.description

* Python type: `I18NDictionary`

 *Localizable.*
*If not provided, defaults to* `None`.


## Names.typographicFamily

* Python type: `I18NDictionary`

 *Localizable.*
*If not provided, defaults to* `None`.


## Names.typographicSubfamily

* Python type: `I18NDictionary`

 *Localizable.*
*If not provided, defaults to* `None`.


## Names.compatibleFullName

* Python type: `I18NDictionary`

 *Localizable.*
*If not provided, defaults to* `None`.


## Names.sampleText

* Python type: `I18NDictionary`

 *Localizable.*
*If not provided, defaults to* `None`.


## Names.WWSFamilyName

* Python type: `I18NDictionary`

 *Localizable.*
*If not provided, defaults to* `None`.


## Names.WWSSubfamilyName

* Python type: `I18NDictionary`

 *Localizable.*
*If not provided, defaults to* `None`.


## Names.copyright

* Python type: `I18NDictionary`

 *Localizable.*
*If not provided, defaults to* `None`.


## Names.styleMapFamilyName

* Python type: `I18NDictionary`

 *Localizable.*
*If not provided, defaults to* `None`.


## Names.trademark

* Python type: `I18NDictionary`

 *Localizable.*
*If not provided, defaults to* `None`.


