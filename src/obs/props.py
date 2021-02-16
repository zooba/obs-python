import obspython as _obs
import pathlib

from . import data as _data
from . import _helper
from .loop import LOOP
from .sceneitem import SceneItem as _SceneItem
from .source import Source as _Source

def render(elements, on_changed):
    p = _obs.obs_properties_create()
    for e in elements:
        e._add(p, on_changed)
    return p


class _Property:
    def __init__(self, name, text, doc=None, visible=True, enabled=True):
        self.__property = []
        self.name = name
        self.text = text
        self.doc = doc
        self.visible = visible
        self.enabled = enabled

    def _add(self, p, on_changed, clear=True):
        if clear:
            self.__property = [p]
        else:
            self.__property.append(p)
        if self.doc:
            _obs.obs_property_set_long_description(p, self.doc)
        _obs.obs_property_set_visible(p, self.visible)
        _obs.obs_property_set_enabled(p, self.enabled)
        if on_changed:
            _obs.obs_property_set_modified_callback(p, on_changed)

    def show(self):
        if not self.visible:
            self.visible = True
            for p in self.__property:
                _obs.obs_property_set_visible(p, True)

    def hide(self):
        if self.visible:
            self.visible = False
            for p in self.__property:
                _obs.obs_property_set_visible(p, False)

    def enable(self):
        if not self.enabled:
            self.enabled = True
            for p in self.__property:
                _obs.obs_property_set_enabled(p, True)

    def disable(self):
        if self.enabled:
            self.enabled = False
            for p in self.__property:
                _obs.obs_property_set_enabled(p, False)

    def get(self, data):
        v = self._get(data)
        return v.get(self.name, None)


class Group(_Property):
    """Defines a group box that contains other properties.

    The entire group may be checked/unchecked, which appears in the current values
    under the name of the group.

    Be aware that all members of the group appear at the top level of the set
    values. The nesting is for UI only.
    """
    def __init__(self, name, text, elements=None, checkable=False, default=True, *,
                 doc=None, visible=True, enabled=True):
        super().__init__(name, text, doc, visible, enabled)
        if elements is None:
            raise ValueError("A list of elements must be provided")
        self.elements = list(elements)
        self.checkable = checkable
        self.default = default

    def _add(self, props, on_changed):
        flags = _obs.OBS_GROUP_NORMAL
        if self.checkable:
            flags = _obs.OBS_GROUP_CHECKABLE
        p = _obs.obs_properties_create()
        for e in self.elements:
            e._add(p, on_changed)
        g = _obs.obs_properties_add_group(props, self.name, self.text, flags, p)
        super()._add(g, on_changed)

    def _defaults(self, data):
        _data.set_data(data, {self.name: self.default}, defaults=True)
        for e in self.elements:
            e._defaults(data)

    def _get(self, data):
        d = {self.name: _obs.obs_data_get_bool(data, self.name)}
        for e in self.elements:
            d.update(e._get(data))
        return d


class Text(_Property):
    """Defines a text field.

    Specify 'password' to display dots instead of typed characters. Note that
    this only affects the UI and not the saved value on disk.

    Specify 'multiline' for multiple lines, and 'monospace' to use a monospaced
    font. Monospace is not available for single line text fields.
    """
    def __init__(self, name, text, default="", *,
                 password=False, multiline=False, monospace=False,
                 doc=None, visible=True, enabled=True):
        super().__init__(name, text, doc, visible, enabled)
        self.default = default
        self.password = password
        self.multiline = multiline
        self.monospace = monospace

    def _add(self, props, on_changed):
        flags = _obs.OBS_TEXT_DEFAULT
        if self.multiline:
            flags = _obs.OBS_TEXT_MULTILINE
        if self.password:
            flags = _obs.OBS_TEXT_PASSWORD
        self._property = p = _obs.obs_properties_add_text(props, self.name, self.text, flags)
        if self.monospace:
            _obs.obs_property_text_set_monospace(p, True)
        super()._add(p, on_changed)

    def _defaults(self, data):
        _data.set_data(data, {self.name: self.default}, defaults=True)

    def _get(self, data):
        return {self.name: _obs.obs_data_get_string(data, self.name)}


class Checkbox(_Property):
    """Defines a boolean field, which appears as a checkbox."""
    def __init__(self, name, text, default=False, *,
                 doc=None, visible=True, enabled=True):
        super().__init__(name, text, doc, visible, enabled)
        self.default = default

    def _add(self, props, on_changed):
        self._property = p = _obs.obs_properties_add_bool(props, self.name, self.text)
        super()._add(p, on_changed)

    def _defaults(self, data):
        _data.set_data(data, {self.name: self.default}, defaults=True)

    def _get(self, data):
        return {self.name: _obs.obs_data_get_bool(data, self.name)}


class Number(_Property):
    """Defines a number field or slider.

    The type of number is inferred from the provided min/max/step/defaults, and
    can be forced to float by passing 'float=True'.

    The UI element is a scroller by default. Pass 'slider=True' to create a
    slider.
    """
    _float = float

    def __init__(self, name, text, minimum, maximum, step=1, *,
                 float=False, scroller=False, slider=False, default=None, suffix=None,
                 doc=None, visible=True, enabled=True):
        super().__init__(name, text, doc, visible, enabled)
        t = int
        if float or isinstance(default, self._float) or isinstance(maximum - minimum + step, self._float):
            t = self._float
        self.type = t
        self.min = t(minimum)
        self.max = t(maximum)
        self.step = t(step)
        self.scroller = (scroller or not slider)
        self.slider = not self.scroller
        self.default = default if default is not None else self.min
        self.suffix = suffix

    def _add(self, props, on_changed):
        if self.type is float:
            F = _obs.obs_properties_add_float_slider if self.slider else _obs.obs_properties_add_float
        else:
            F = _obs.obs_properties_add_int_slider if self.slider else _obs.obs_properties_add_int
        self._property = p = F(props, self.name, self.text, self.min, self.max, self.step)
        super()._add(p, on_changed)
        if self.type is float:
            if self.suffix:
                _obs.obs_property_float_set_suffix(p, self.suffix)
        else:
            if self.suffix:
                _obs.obs_property_int_set_suffix(p, self.suffix)

    def _defaults(self, data):
        _data.set_data(data, {self.name: self.default}, defaults=True)

    def _get(self, data):
        if self.type is float:
            v = _obs.obs_data_get_double(data, self.name)
        else:
            v = _obs.obs_data_get_int(data, self.name)
        return {self.name: v}


class Path(_Property):
    """Create a path element, which requires users to browse to get the value.

    By default, the Browse button will only open existing files. Pass 'save_file=True'
    to allow specifying non-existent files, or 'open_directory=True' to select a folder.

    'filter' is a string containing 'Text (*.ext;*.ex2)' style filters to be used when
    opening or saving files. Each filter must be separated by two semicolons ';;'.

    The value from this element will be a 'pathlib.Path' object or None.
    """
    def __init__(self, name, text, open_file=False, save_file=False, open_directory=False,
                 filter="All Files (*.*)", default=None, *,
                 doc=None, visible=True, enabled=True):
        super().__init__(name, text, doc, visible, enabled)
        self.open_file = open_file or not (save_file or open_directory)
        self.save_file = save_file and not self.open_file
        self.open_directory = open_directory and not self.open_file
        self.filter = filter
        self.default = str(default or "")

    def _add(self, props, on_changed):
        t = _obs.OBS_PATH_FILE
        if self.save_file:
            t = _obs.OBS_PATH_FILE_SAVE
        elif self.open_directory:
            t = _obs.OBS_PATH_DIRECTORY
        p = _obs.obs_properties_add_path(props, self.name, self.text, t, self.filter, self.default)
        super()._add(p, on_changed)

    def _defaults(self, data):
        v = pathlib.Path(self.default) if self.default else None
        _data.set_data(data, {self.name: v}, defaults=True)

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


class DropDown(_Property):
    """Create a dropdown list element.

    'type' may be str, int or float, and all items will be converted to that type.
    """
    def __init__(self, name, text, editable=False, type=str, items=None, default=None, *,
                 doc=None, visible=True, enabled=True):
        super().__init__(name, text, doc, visible, enabled)
        self.editable = editable
        self.type = {str: str, int: int, float: float}.get(type, str)
        self.items = items
        self.default = default

    def _add(self, props, on_changed):
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
        super()._add(p, on_changed)

        for k, v in _pairs(self.items):
            add(p, str(k), self.type(v))

    def _defaults(self, data):
        _data.set_data(data, {self.name: self.default}, defaults=True)

    def _get(self, data):
        if self.type is float:
            v = _obs.obs_data_get_double(data, self.name)
        elif self.type is int:
            v = _obs.obs_data_get_int(data, self.name)
        else:
            v = _obs.obs_data_get_string(data, self.name)
        return {self.name: v}


class List(_Property):
    """Create an editable list of items."""

    def __init__(self, name, text, default=None, *,
                 files=False, urls=False, filter=None, default_path=None,
                 doc=None, visible=True, enabled=True):
        super().__init__(name, text, doc, visible, enabled)
        self.default = [
            d if isinstance(d, dict) else {"value": d, "selected": False, "hidden": False}
            for d in (default or ())
        ]
        self.files = files
        self.urls = urls
        self.filter = filter
        self.default_path = default_path

    def _add(self, props, on_changed):
        fmt = _obs.OBS_EDITABLE_LIST_TYPE_STRINGS
        if self.files:
            fmt = _obs.OBS_EDITABLE_LIST_TYPE_FILES
        if self.urls:
            fmt = _obs.OBS_EDITABLE_LIST_TYPE_FILES_AND_URLS
        p = _obs.obs_properties_add_editable_list(props, self.name, self.text, fmt, self.filter, self.default_path)
        super()._add(p, on_changed)
        for d in self.default:
            _obs.obs_property_list_add_string(p, d, d)

    def _defaults(self, data):
        _data.set_data(data, {self.name: self.default}, defaults=True)

    def _get(self, data):
        o = _obs.obs_data_get_array(data, self.name)
        try:
            values = [v.get("value") for v in _helper.read_data_array(o)]
        finally:
            _obs.obs_data_array_release(o)
        return {self.name: values}


class Color(_Property):
    """Create a color picker element.

    Colors are represented as 24-bit integer values 0xBBGGRR.
    """
    def __init__(self, name, text, default=0xFFFFFF, *,
                 doc=None, visible=True, enabled=True):
        super().__init__(name, text, doc, visible, enabled)
        self.default = default

    def _add(self, props, on_changed):
        p = _obs.obs_properties_add_color(props, self.name, self.text)
        super()._add(p, on_changed)

    def _defaults(self, data):
        _data.set_data(data, {self.name: self.default}, defaults=True)

    def _get(self, data):
        return {self.name: _obs.obs_data_get_int(data, self.name)}


class Font(_Property):
    """Create a font picker element."""
    def __init__(self, name, text, default_face=None, default_size=None, default_bold=False,
                 default_italic=False, default_underline=False, default_strikeout=False, *,
                 doc=None, visible=True, enabled=True):
        super().__init__(name, text, doc, visible, enabled)
        self.default = {
            "face": default_face,
            "size": int(default_size) if default_size else None,
            "flags":
                (_obs.OBS_FONT_BOLD if default_bold else 0) |
                (_obs.OBS_FONT_ITALIC if default_italic else 0) |
                (_obs.OBS_FONT_UNDERLINE if default_underline else 0) |
                (_obs.OBS_FONT_STRIKEOUT if default_strikeout else 0)
        }

    def _add(self, props, on_changed):
        p = _obs.obs_properties_add_font(props, self.name, self.text)
        super()._add(p, on_changed)

    def _defaults(self, data):
        _data.set_data(data, {self.name: self.default}, defaults=True)

    def _get(self, data):
        o = _obs.obs_data_get_obj(data, self.name)
        try:
            d = _helper.read_data(o, None)
        finally:
            _obs.obs_data_release(o)
        f = d.get("flags", 0)
        d.update({
            "bold": bool(f & _obs.OBS_FONT_BOLD),
            "italic": bool(f & _obs.OBS_FONT_ITALIC),
            "underline": bool(f & _obs.OBS_FONT_UNDERLINE),
            "strikeout": bool(f & _obs.OBS_FONT_STRIKEOUT),
        })
        return {self.name: d}


def _button_call(properties, btn):
    cb = Button.CALLBACKS[_obs.obs_property_name(btn)]
    return bool(cb())


class Button(_Property):
    """Create a button element with a callback."""
    CALLBACKS = {}

    def __init__(self, name, text, callback, *,
                 doc=None, visible=True, enabled=True):
        super().__init__(name, text, doc, visible, enabled)
        self.callback = callback

    def _add(self, props, on_changed):
        self.CALLBACKS[self.name] = self.callback
        p = _obs.obs_properties_add_button(props, self.name, self.text, _button_call)
        super()._add(p, None)

    def _defaults(self, data):
        pass

    def _get(self, data):
        return {}



class Migrate(_Property):
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
        super().__init__(name, "", None, False, True)
        self.old_type = old_type
        self.new_name = new_name
        self.convert = convert

    def _add(self, props, on_changed):
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
        super()._add(p, on_changed)

    def _defaults(self, data):
        pass

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


class SceneList(_Property):
    """Create a list of scenes"""
    def __init__(self, name, text, *,
                 doc=None, visible=True, enabled=True):
        super().__init__(name, text,
                         doc=doc, visible=visible, enabled=enabled)

    def _add(self, props, on_changed):
        p = _obs.obs_properties_add_list(props, self.name, self.text,
            _obs.OBS_COMBO_TYPE_LIST, _obs.OBS_COMBO_FORMAT_STRING)
        super()._add(p, on_changed)

        _obs.obs_property_list_add_string(p, "(None)", None)
        for n in _helper.get_scene_names():
            _obs.obs_property_list_add_string(p, n, n)

    def _defaults(self, data):
        _data.set_data(data, {self.name: None}, defaults=True)

    def _get(self, data):
        n = _obs.obs_data_get_string(data, self.name)
        return {self.name: n if n else None}


class SourceList(_Property):
    """Create a list of sources matching certain kinds.

    Each kind is either a 'perfect match', 'prefix*', '*suffix', or '*substring*' of
    the source kind (unversioned ID).

    Consider using one of the predefined source lists for common types.
    """
    def __init__(self, name, text, *kinds, editable=False,
                 doc=None, visible=True, enabled=True):
        super().__init__(name, text, doc, visible, enabled)
        self.kinds = kinds
        self.editable = editable

    def _add(self, props, on_changed):
        flag = _obs.OBS_COMBO_TYPE_EDITABLE if self.editable else _obs.OBS_COMBO_TYPE_LIST
        fmt = _obs.OBS_COMBO_FORMAT_STRING
        p = _obs.obs_properties_add_list(props, self.name, self.text, flag, fmt)
        super()._add(p, on_changed)

        _obs.obs_property_list_add_string(p, "(None)", None)
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

    def _defaults(self, data):
        _data.set_data(data, {self.name: None}, defaults=True)

    def _get(self, data):
        n = _obs.obs_data_get_string(data, self.name)
        return {self.name: _Source(n) if n else None}


class TextSources(SourceList):
    "A list of text sources."
    def __init__(self, name, text, *,
                 doc=None, visible=True, enabled=True):
        super().__init__(name, text, "text_*",
                         doc=doc, visible=visible, enabled=enabled)


class AudioSources(SourceList):
    "A list of audio sources."
    def __init__(self, name, text, *,
                 doc=None, visible=True, enabled=True):
        super().__init__(name, text, "wasapi_*",
                         doc=doc, visible=visible, enabled=enabled)


class VideoSources(SourceList):
    "A list of video sources."
    def __init__(self, name, text, include_media=True, *,
                 doc=None, visible=True, enabled=True):
        kinds = ("dshow_input", "streamfx-source-mirror")
        if include_media:
            kinds += ("ffmpeg_*",)
        super().__init__(name, text, *kinds,
                         doc=doc, visible=visible, enabled=enabled)


class MediaSources(SourceList):
    "A list of media sources."
    def __init__(self, name, text, *,
                 doc=None, visible=True, enabled=True):
        super().__init__(name, text, "ffmpeg_*",
                         doc=doc, visible=visible, enabled=enabled)


class ImageSources(SourceList):
    "A list of image sources."
    def __init__(self, name, text, *,
                 doc=None, visible=True, enabled=True):
        super().__init__(name, text, "image_source",
                         doc=doc, visible=visible, enabled=enabled)


class ColorSources(SourceList):
    "A list of color sources."
    def __init__(self, name, text, *,
                 doc=None, visible=True, enabled=True):
        super().__init__(name, text, "color_source",
                         doc=doc, visible=visible, enabled=enabled)


class SourceGroups(SourceList):
    "A list of groups."
    def __init__(self, name, text, *,
                 doc=None, visible=True, enabled=True):
        super().__init__(name, text, "group",
                         doc=doc, visible=visible, enabled=enabled)


class SceneItemList(_Property):
    """A list of scenes and items within those scenes"""
    def __init__(self, name, text, item_text=None, *,
                 doc=None, visible=True, enabled=True):
        super().__init__(name, text,
                         doc=doc, visible=visible, enabled=enabled)
        self.item_name = f"_{name}_item"
        self.item_text = item_text or f"{text} item"
        self._scenes = None
        self._items = None

    def _add(self, props, on_changed):
        self._scenes = p1 = _obs.obs_properties_add_list(
            props, self.name, self.text,
            _obs.OBS_COMBO_TYPE_LIST, _obs.OBS_COMBO_FORMAT_STRING
        )
        super()._add(p1, self._update)
        self._items = p2 = _obs.obs_properties_add_list(
            props, self.item_name, self.item_text,
            _obs.OBS_COMBO_TYPE_EDITABLE, _obs.OBS_COMBO_FORMAT_STRING
        )
        super()._add(p2, on_changed, clear=False)

        _obs.obs_property_list_add_string(p1, "(None)", None)
        for n in sorted(_helper.get_scene_names()):
            _obs.obs_property_list_add_string(p1, n, n)
        _obs.obs_property_list_add_string(p2, "(None)", None)

    @staticmethod
    def _update(properties, prop, data=None):
        if not data:
            return
        n1 = _obs.obs_property_name(prop)
        n2 = f"_{n1}_item"
        p = _obs.obs_properties_get(properties, n2)
        return SceneItemList._do_update(data, p, n1, n2)

    @classmethod
    def _do_update(cls, data, item_prop, name, item_name):
        s1 = _obs.obs_data_get_string(data, name)
        s2 = _obs.obs_data_get_string(data, item_name)
        _obs.obs_property_list_clear(item_prop)
        _obs.obs_property_list_add_string(item_prop, "(None)", None)
        if not s1:
            return True # still need to update
        try:
            items = _helper.get_scene_item_names(s1)
        except LookupError as ex:
            _obs.obs_property_list_add_string(item_prop, s2, s2)
            return True
        for n, k in items:
            _obs.obs_property_list_add_string(item_prop, n, n)
        return True

    def _defaults(self, data):
        self._do_update(data, self._items, self.name, self.item_name)
        _data.set_data(data, {self.name: None, self.item_name: None}, defaults=True)

    def _get(self, data):
        s1 = _obs.obs_data_get_string(data, self.name)
        s2 = _obs.obs_data_get_string(data, self.item_name)
        if s1 and s2:
            return {self.name: _SceneItem(s1, _Source(s2))}
        return {self.name: None}
