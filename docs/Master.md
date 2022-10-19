---
title: Master
---
A font master.
## Master.name

* Python type: `I18NDictionary`

* **Required field**

 *Localizable.*


## Master.id

* Python type: `str`

* **Required field**

An ID used to refer to this master in the
`Layer._master` field. (This is allows the user to change the master name
without the layers becoming lost.)


## Master.location

* Python type: `dict`

A dictionary mapping axis tags to coordinates
in order to locate this instance in the design space.
*If not provided, defaults to* `None`.


## Master.guides

* Python type: [[`Guide`](Guide.html)]

* When writing to Babelfont-JSON, each item in the list must be placed on a separate line.

A list of guides.


## Master.metrics

* Python type: `dict`

A dictionary mapping metric names (string) to metric value (integer). The following
metric names are reserved: `xHeight,capHeight,ascender,descender`. Other metrics may be added to this dictionary
as needed by font clients, but their interpretation is not guaranteed to be
compatible between clients.


## Master.kerning

* Python type: `dict`

* When writing to Babelfont-JSON, each item in the list must be placed on a separate line.

I'll be honest, I haven't worked out how this is meant to work.


## Master.font

* Python type: `object`

* This field only exists as an attribute of the the Python object and should not be written to Babelfont-JSON.

Within the Python object, provides a reference to the font object containing this master.
*If not provided, defaults to* `None`.


## Master._formatspecific

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



