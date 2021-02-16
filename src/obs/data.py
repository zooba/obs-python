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


def _unset_default(data, key, obj):
    _obs.obs_data_unset_default_value(data, key)


def _make_list(arr, obj):
    d = _obs.obs_data_array_create()
    try:
        for o in obj:
            d2 = _obs.obs_data_create()
            try:
                set_data(d2, o.items())
                _obs.obs_data_array_push_back(arr, d2)
            finally:
                _obs.obs_data_release(d2)
        d_, d = d, None
        return d_
    finally:
        if d:
            _obs.obs_data_release(d)


def _set_list(data, key, obj):
    o = _make_list(obj)
    try:
        _obs.obs_data_set_array(data, key, o)
    finally:
        _obs.obs_data_release(o)


def _set_default_list(data, key, obj):
    pass


def _set_obj(data, key, obj):
    d = _obs.obs_data_create()
    set_data(d, obj.items())
    _obs.obs_data_set_obj(data, key, d)


def _set_default_string(data, key, string):
    _obs.obs_data_set_default_string(data, key, sys.intern(string))


def _set_default_obj(data, key, obj):
    d = _obs.obs_data_create()
    set_data(d, obj.items())
    _obs.obs_data_set_default_obj(data, key, d)


_SET_FUNC = {
    bool: _obs.obs_data_set_bool,
    int: _obs.obs_data_set_int,
    float: _obs.obs_data_set_double,
    str: _obs.obs_data_set_string,
    tuple: _set_list,
    list: _set_list,
    dict: _set_obj,
    type(None): _erase,
}


_SET_DEFAULT_FUNC = {
    bool: _obs.obs_data_set_default_bool,
    int: _obs.obs_data_set_default_int,
    float: _obs.obs_data_set_default_double,
    str: _set_default_string,
    tuple: _set_default_list,
    list: _set_default_list,
    dict: _set_default_obj,
    type(None): _unset_default,
}


def set_data(data, key_value_pairs, defaults=False):
    """Sets the values in an OBS data object.
    
    'key_value_pairs' is an iterable of key-value pairs, like dict.items()
    
    If 'defaults' is True, the default values for the data object are set.
    Otherwise, the current values are set.
    """
    funcs = _SET_DEFAULT_FUNC if defaults else _SET_FUNC
    if isinstance(key_value_pairs, dict):
        key_value_pairs = key_value_pairs.items()
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

