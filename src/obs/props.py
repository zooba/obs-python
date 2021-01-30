import obspython as _obs
import pathlib

from . import data as _data
from .source import Source as _Source

def render(elements):
    p = _obs.obs_properties_create()
    for e in elements:
        e._add(p)
    return p


def _apply_flags(p, source):
    if source.doc:
        _obs.obs_property_set_long_description(p, source.doc)
    _obs.obs_property_set_visible(p, source.visible)
    _obs.obs_property_set_enabled(p, source.enabled)


class Group:
    """Defines a group box that contains other properties.

    The entire group may be checked/unchecked, which appears in the current values
    under the name of the group.

    Be aware that all members of the group appear at the top level of the set
    values. The nesting is for UI only.
    """
    def __init__(self, name, text, checkable=False, elements=None, default=True,
                 doc=None, visible=True, enabled=True):
        self.name = name
        self.text = text
        if elements is None:
            raise ValueError("A list of elements must be provided")
        self.elements = list(elements)
        self.checkable = checkable
        self.default = default
        self.doc = doc
        self.visible = visible
        self.enabled = enabled

    def _add(self, props):
        flags = _obs.OBS_GROUP_NORMAL
        if self.checkable:
            flags = _obs.OBS_GROUP_CHECKABLE
        p = _obs.obs_properties_create()
        for e in self.elements:
            e._add(p)
        g = _obs.obs_properties_add_group(props, self.name, self.text, flags, p)
        _apply_flags(g, self)

    def _default(self):
        d = {self.name: self.default}
        for e in self.elements:
            d.update(e._default())
        return d

    def _get(self, data):
        d = {self.name: _obs.obs_data_get_bool(data, self.name)}
        for e in self.elements:
            d.update(e._get(data))
        return d


class Text:
    """Defines a text field."""
    def __init__(self, name, text, password=False, multiline=False, default="",
                 doc=None, visible=True, enabled=True):
        self.name = name
        self.text = text
        self.password = password
        self.multiline = multiline
        self.default = default
        self.doc = doc
        self.visible = visible
        self.enabled = enabled

    def _add(self, props):
        flags = _obs.OBS_TEXT_DEFAULT
        if self.multiline:
            flags = _obs.OBS_TEXT_MULTILINE
        if self.password:
            flags = _obs.OBS_TEXT_PASSWORD
        p = _obs.obs_properties_add_text(props, self.name, self.text, flags)
        _apply_flags(p, self)

    def _default(self):
        return {self.name: self.default}

    def _get(self, data):
        return {self.name: _obs.obs_data_get_string(data, self.name)}


class Checkbox:
    """Defines a boolean field, which appears as a checkbox."""
    def __init__(self, name, text, default=False,
                 doc=None, visible=True, enabled=True):
        self.name = name
        self.text = text
        self.default = default
        self.doc = doc
        self.visible = visible
        self.enabled = enabled

    def _add(self, props):
        p = _obs.obs_properties_add_bool(props, self.name, self.text)
        _apply_flags(p, self)

    def _default(self):
        return {self.name: self.default}

    def _get(self, data):
        return {self.name: _obs.obs_data_get_bool(data, self.name)}


class Number:
    """Defines a number field or slider.

    The type of number is inferred from the provided min/max/step/defaults, and
    can be forced to float by passing 'float=True'.

    The UI element is a scroller by default. Pass 'slider=True' to create a
    slider.
    """
    _float = float

    def __init__(self, name, text, minimum, maximum, step=1, float=False, scroller=False, slider=False, default=None,
                 doc=None, visible=True, enabled=True):
        self.name = name
        self.text = text
        t = int
        if float or isinstance(default, self._float) or isinstance(maximum - minimum + step, self._float):
            t = self._float
        self.type = t
        self.min = t(minimum)
        self.max = t(maximum)
        self.step = t(step)
        self.scroller = (scroller or not slider)
        self.slider = not self.scroller
        self.default = self.min
        self.doc = doc
        self.visible = visible
        self.enabled = enabled

    def _add(self, props):
        if self.type is float:
            F = _obs.obs_properties_add_float_slider if self.slider else _obs.obs_properties_add_float
        else:
            F = _obs.obs_properties_add_int_slider if self.slider else _obs.obs_properties_add_int
        p = F(props, self.name, self.text, self.min, self.max, self.step)
        _apply_flags(p, self)

    def _default(self):
        return {self.name: self.default}

    def _get(self, data):
        if self.type is float:
            v = _obs.obs_data_get_double(data, self.name)
        else:
            v = _obs.obs_data_get_int(data, self.name)
        return {self.name: v}


class Path:
    """Create a path element, which requires users to browse to get the value.

    By default, the Browse button will only open existing files. Pass 'save_file=True'
    to allow specifying non-existent files, or 'open_directory=True' to select a folder.

    'filter' is a single 'Text (*.ext;*.ex2)' style string to be used when opening or
    saving files.

    The value from this element will be a 'pathlib.Path' object or None.
    """
    def __init__(self, name, text, open_file=False, save_file=False, open_directory=False,
                 filter="All Files (*.*)", default=None,
                 doc=None, visible=True, enabled=True):
        self.name = name
        self.text = text
        self.open_file = open_file or not (save_file or open_directory)
        self.save_file = save_file and not self.open_file
        self.open_directory = open_directory and not self.open_file
        self.filter = filter
        self.default = str(default or "")
        self.doc = doc
        self.visible = visible
        self.enabled = enabled

    def _add(self, props):
        t = _obs.OBS_PATH_FILE
        if self.save_file:
            t = _obs.OBS_PATH_FILE_SAVE
        elif self.open_directory:
            t = _obs.OBS_PATH_DIRECTORY
        p = _obs.obs_properties_add_path(props, self.name, self.text, t, self.filter, self.default)
        _apply_flags(p, self)

    def _default(self):
        return {self.name: pathlib.Path(self.default) if self.default else None}

    def _get(self, data):
        p = _obs.obs_data_get_string(data, self.name)
        return {self.name: pathlib.Path(p) if p else None}


def _pairs(items):
    if isinstance(items, dict):
        for k in sorted(items):
            yield k, items[k]
        return
    for i in items:
        if isinstance(i, (tuple, list)) and len(i) == 2:
            yield i[0], i[1]
        else:
            yield i, i


class DropDown:
    """Create a dropdown list element.

    'type' may be str, int or float, and all items will be converted to that type.
    """
    def __init__(self, name, text, editable=False, type=str, items=None, default=None,
                 doc=None, visible=True, enabled=True):
        self.name = name
        self.text = text
        self.editable = editable
        self.type = {str: str, int: int, float: float}.get(type, str)
        self.items = items
        self.default = default
        self.doc = doc
        self.visible = visible
        self.enabled = enabled

    def _add(self, props):
        flag = _obs.OBS_COMBO_TYPE_EDITABLE if self.editable else _obs.OBS_COMBO_TYPE_LIST
        fmt = _obs.OBS_COMBO_FORMAT_STRING
        add = _obs.obs_property_list_add_string
        if self.type is int:
            flag = 0
            fmt = _obs.OBS_COMBO_FORMAT_INT
            add = _obs.obs_property_list_add_int
        elif self.type is float:
            flag = 0
            fmt = _obs.OBS_COMBO_FORMAT_FLOAT
            add = _obs.obs_property_list_add_float
        p = _obs.obs_properties_add_list(props, self.name, self.text, flag, fmt)
        _apply_flags(p, self)

        for k, v in _pairs(self.items):
            add(p, str(k), self.type(v))

    def _default(self):
        return {self.name: self.default}

    def _get(self, data):
        if self.type is float:
            v = _obs.obs_data_get_double(data, self.name)
        elif self.type is int:
            v = _obs.obs_data_get_int(data, self.name)
        else:
            v = _obs.obs_data_get_string(data, self.name)
        return {self.name: v}


class ColorPicker:
    """Create a color picker element.

    Colors are represented as 24-bit integer values 0xBBGGRR.
    """
    def __init__(self, name, text, default=0xFFFFFF,
                 doc=None, visible=True, enabled=True):
        self.name = name
        self.text = text
        self.default = default
        self.doc = doc
        self.visible = visible
        self.enabled = enabled

    def _add(self, props):
        p = _obs.obs_properties_add_color(props, self.name, self.text)
        _apply_flags(p, self)

    def _default(self):
        return {self.name: self.default}

    def _get(self, data):
        return {self.name: _obs.obs_data_get_int(data, self.name)}


def _button_call(properties, btn):
    cb = Button.CALLBACKS[_obs.obs_property_name(btn)]
    return bool(cb())


class Button:
    """Create a button element with a callback."""
    CALLBACKS = {}

    def __init__(self, name, text, callback,
                 doc=None, visible=True, enabled=True):
        self.name = name
        self.text = text
        self.callback = callback
        self.doc = doc
        self.visible = visible
        self.enabled = enabled

    def _add(self, props):
        self.CALLBACKS[self.name] = self.callback
        p = _obs.obs_properties_add_button(props, self.name, self.text, _button_call)
        _apply_flags(p, self)

    def _default(self):
        return {}

    def _get(self, data):
        return {}



class Migrate:
    """Create a migration element.

    Migration elements do not appear in the UI, but will read previously stored properties
    and convert them to a new property. If the new property also has a UI element, the
    migration element should appear earlier.

    If 'new_name' has already been set, the migration is ignored. If 'name' does not have a
    stored value, a default value for 'new_name' is only set if another element provides it.

    'old_type' must be one of bool, int, float or str.

    If 'new_name' is omitted, the value is made available as its old name.
    """
    def __init__(self, name, old_type, new_name=None, convert=None):
        self.name = name
        self.old_type = old_type
        self.new_name = new_name
        self.convert = convert

    def _add(self, props):
        if self.old_type is bool:
            p = _obs.obs_property_add_bool(props, self.name, self.name)
        elif self.old_type is int:
            p = _obs.obs_property_add_int(props, self.name, self.name, -2**31, 2**31, 1)
        elif self.old_type is float:
            p = _obs.obs_property_add_float(props, self.name, self.name,
                sys.float_info.min, sys.float_info.max, sys.float_info.epsilon)
        elif self.old_type is str:
            p = _obs.obs_property_add_text(props, self.name, self.name, _obs.OBS_TEXT_DEFAULT)
        else:
            raise TypeError("unsupported migration type: {}".format(self.old_type))
        _obs.obs_property_set_visible(p, False)

    def _default(self):
        return {}

    def _get(self, data):
        if self.new_name:
            try:
                return {self.new_name: _data.get_value(data, self.new_name)}
            except LookupError:
                pass
        v1 = _data.get_value(data, self.name)
        if convert:
            v2 = convert(v1)
        else:
            v2 = v1
        return {self.new_name or self.name: v2}


def _contains_pattern(s, patterns):
    if not patterns:
        return True
    for p in patterns:
        if p == "*" or s == p:
            return True
        if p.startswith("*") and p.endswith("*"):
            return s in p[1:-1]
        if p.startswith("*"):
            return s.endswith(p[1:])
        if p.endswith("*"):
            return s.startswith(p[:-1])
    return False


class SourceList:
    """Create a list of sources matching certain kinds.

    Each kind is either a 'perfect match', 'prefix*', '*suffix', or '*substring*' of
    the source kind (unversioned ID).

    Consider using one of the predefined source lists for common types.
    """
    def __init__(self, name, text, *kinds, editable=False,
                 doc=None, visible=True, enabled=True):
        self.name = name
        self.text = text
        self.kinds = kinds
        self.editable = editable
        self.doc = doc
        self.visible = visible
        self.enabled = enabled

    def _add(self, props):
        flag = _obs.OBS_COMBO_TYPE_EDITABLE if self.editable else _obs.OBS_COMBO_TYPE_LIST
        fmt = _obs.OBS_COMBO_FORMAT_STRING
        p = _obs.obs_properties_add_list(props, self.name, self.text, flag, fmt)
        _apply_flags(p, self)

        sources = _obs.obs_enum_sources()
        if sources is not None:
            try:
                for s in sources:
                    s_id = _obs.obs_source_get_unversioned_id(s)
                    if _contains_pattern(s_id, self.kinds):
                        v = _obs.obs_source_get_name(s)
                        _obs.obs_property_list_add_string(p, v, v)
            finally:
                _obs.source_list_release(sources)

    def _default(self):
        return {self.name: None}

    def _get(self, data):
        n = _obs.obs_data_get_string(data, self.name)
        return {self.name: _Source(n) if n else None}


class TextSources(SourceList):
    "A list of text sources."
    def __init__(self, name, text):
        super().__init__(name, text, "text_*")


class AudioSources(SourceList):
    "A list of audio sources."
    def __init__(self, name, text):
        super().__init__(name, text, "wasapi_*")


class VideoSources(SourceList):
    "A list of video sources."
    def __init__(self, name, text, include_media=True):
        kinds = ("dshow_input", "streamfx-source-mirror")
        if include_media:
            kinds += ("ffmpeg_*",)
        super().__init__(name, text, *kinds)


class MediaSources(SourceList):
    "A list of media sources."
    def __init__(self, name, text):
        super().__init__(name, text, "ffmpeg_*")


class ImageSources(SourceList):
    "A list of image sources."
    def __init__(self, name, text):
        super().__init__(name, text, "image_source")


class ColorSources(SourceList):
    "A list of color sources."
    def __init__(self, name, text):
        super().__init__(name, text, "color_source")


class SourceGroups(SourceList):
    "A list of groups."
    def __init__(self, name, text):
        super().__init__(name, text, "group")
