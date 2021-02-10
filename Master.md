---
title: Master
---
A font master.

    Attributes:
        name (str): The user-facing master name.
        id (str): An internal identifier for the master.
        location (dict): A dictionary locating this master by mapping axis
            name to designspace location.
        guides ([Guide]): A list of master-level guidelines
        metrics (dict): The master's metrics.
        font (Font): The font that this master belongs to.
    
## Master.name

* Python type: `I18NDictionary`


**Required field**


## Master.id

* Python type: `str`


**Required field**


## Master.location

* Python type: `dict`

*If not provided, defaults to* `None`.


## Master.guides

* Python type: [[`Guide`](Guide.html)]

* When writing to NFSF-JSON, each item in the list must be placed on a separate line.



## Master.metrics

* Python type: `dict`



## Master.kerning

* Python type: `dict`

* When writing to NFSF-JSON, each item in the list must be placed on a separate line.

*If not provided, defaults to* `None`.


## Master.font

* Python type: `object`

* This field only exists as an attribute of the the Python object and should not be written to NFSF-JSON.

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



