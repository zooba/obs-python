import obspython as _obs
import pathlib

from .source import Source as _Source

def render(*elements):
    p = _obs.obs_properties_create()
    for e in elements:
        e._add(p)
    return p


class Text:
    def __init__(self, name, text, password=False, multiline=False):
        self.name = name
        self.text = text or name
        self.password = password
        self.multiline = multiline

    def _add(self, props):
        flags = _obs.OBS_TEXT_DEFAULT
        if self.multiline:
            flags = _obs.OBS_TEXT_MULTILINE
        if self.password:
            flags = _obs.OBS_TEXT_PASSWORD
        _obs.obs_properties_add_text(props, self.name, self.text, flags)

    def _default(self):
        return ""

    def _get(self, data):
        return _obs.obs_data_get_string(data, self.name)


class Number:
    _float = float

    def __init__(self, name, text, minimum, maximum, step=1, float=False, scroller=False, slider=False):
        self.name = name
        self.text = text
        t = int
        if float or isinstance(maximum - minimum + step, self._float):
            t = self._float
        self.type = t
        self.min = t(minimum)
        self.max = t(maximum)
        self.step = t(step)
        self.scroller = (scroller or not slider)
        self.slider = not self.scroller

    def _add(self, props):
        if self.type is float:
            F = _obs.obs_properties_add_float_slider if self.slider else _obs.obs_properties_add_float
        else:
            F = _obs.obs_properties_add_int_slider if self.slider else _obs.obs_properties_add_int
        F(props, self.name, self.text, self.min, self.max, self.step)

    def _default(self):
        return self.min

    def _get(self, data):
        if self.type is float:
            return _obs.obs_data_get_double(data, self.name)
        return _obs.obs_data_get_int(data, self.name)


class Path:
    def __init__(self, name, text, open_file=False, save_file=False, open_directory=False, filter="*.*", default=None):
        self.name = name
        self.text = text
        self.open_file = open_file or not (save_file or open_directory)
        self.save_file = save_file and not self.open_file
        self.open_directory = open_directory and not self.open_file
        self.filter = filter
        self.default = str(default or "")

    def _add(self, props):
        t = _obs.OBS_PATH_FILE
        if self.save_file:
            t = _obs.OBS_PATH_FILE_SAVE
        elif self.open_directory:
            t = _obs.OBS_PATH_DIRECTORY
        _obs.obs_properties_add_path(props, self.name, self.text, t, self.filter, self.default)

    def _default(self):
        return pathlib.Path(self.default) if self.default else None

    def _get(self, data):
        p = _obs.obs_data_get_string(data, self.name)
        return pathlib.Path(p) if p else None


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
    def __init__(self, name, text, editable=False, type=str, items=None):
        self.name = name
        self.text = text
        self.editable = editable
        self.type = {str: str, int: int, float: float}.get(type, str)
        self.items = items

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
        
        for k, v in _pairs(self.items):
            add(p, str(k), self.type(v))

    def _default(self):
        if self.items:
            return next(_pairs(self.items))[1]

    def _get(self, data):
        if self.type is float:
            return _obs.obs_data_get_double(data, self.name)
        if self.type is int:
            return _obs.obs_data_get_int(data, self.name)
        return _obs.obs_data_get_string(data, self.name)


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
    def __init__(self, name, text, *kinds, editable=False):
        self.name = name
        self.text = text
        self.kinds = kinds
        self.editable = editable

    def _add(self, props):
        flag = _obs.OBS_COMBO_TYPE_EDITABLE if self.editable else _obs.OBS_COMBO_TYPE_LIST
        fmt = _obs.OBS_COMBO_FORMAT_STRING
        p = _obs.obs_properties_add_list(props, self.name, self.text, flag, fmt)

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
        return None

    def _get(self, data):
        n = _obs.obs_data_get_string(data, self.name)
        if n:
            return _Source(n)


class TextSources(SourceList):
    def __init__(self, name, text):
        super().__init__(name, text, "text_*")


class AudioSources(SourceList):
    def __init__(self, name, text):
        super().__init__(name, text, "wasapi_*")


class MediaSources(SourceList):
    def __init__(self, name, text):
        super().__init__(name, text, "ffmpeg_*")


class ImageSources(SourceList):
    def __init__(self, name, text):
        super().__init__(name, text, "image_source")


class ColorSources(SourceList):
    def __init__(self, name, text):
        super().__init__(name, text, "color_source")


class SourceGroups(SourceList):
    def __init__(self, name, text):
        super().__init__(name, text, "group")

