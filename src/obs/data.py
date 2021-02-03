import obspython as _obs
import sys

from . import _helper


def get_value(data, key):
    """Gets the value of item 'key' from OBS data object 'data'"""
    return get_values(data, [key])[key]


def get_values(data, keys=None):
    """Gets a dict containing all keys and values from OBS data object 'data'"""
    return _helper.read_data(data, keys)


def _erase(data, key, obj):
    _obs.obs_data_erase(data, key)


def _set_obj(data, key, obj):
    d = _obs.obs_data_create()
    _set_data(d, obj.items())
    _obs.obs_data_set_obj(data, key, d)


def _set_default_string(data, key, string):
    _obs.obs_data_set_default_string(data, key, sys.intern(string))


def _set_default_obj(data, key, obj):
    d = _obs.obs_data_create()
    _set_data(d, obj.items())
    _obs.obs_data_set_default_obj(data, key, d)


_SET_FUNC = {
    bool: _obs.obs_data_set_bool,
    int: _obs.obs_data_set_int,
    float: _obs.obs_data_set_double,
    str: _obs.obs_data_set_string,
    dict: _set_obj,
    type(None): _erase,
}


_SET_DEFAULT_FUNC = {
    bool: _obs.obs_data_set_default_bool,
    int: _obs.obs_data_set_default_int,
    float: _obs.obs_data_set_default_double,
    str: _set_default_string,
    dict: _set_default_obj,
    type(None): lambda *_: None,
}


def set_data(data, key_value_pairs, defaults=False):
    """Sets the values in an OBS data object.
    
    'key_value_pairs' is an iterable of key-value pairs, like dict.items()
    
    If 'defaults' is True, the default values for the data object are set.
    Otherwise, the current values are set.
    """
    funcs = _SET_DEFAULT_FUNC if defaults else _SET_FUNC
    for k, v in key_value_pairs:
        if not k:
            continue
        try:
            funcs[type(v)](data, k, v)
        except LookupError:
            for t, fn in funcs.items():
                if isinstance(v, t):
                    fn(data, k, v)
                    break
            else:
                raise TypeError("unsupported type '{}'".format(type(v)))

