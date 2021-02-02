import obspython as _obs
import sys


def _item_get_number(item):
    ntype = _obs.obs_data_item_numtype(item)
    if ntype == _obs.OBS_DATA_NUM_INT:
        return _obs.obs_data_item_get_int(item)
    elif ntype == _obs.OBS_DATA_NUM_DOUBLE:
        return _obs.obs_data_item_get_double(item)
    raise TypeError("unsupported numeric type")


_ITEM_GET_FUNC = {
    _obs.OBS_DATA_NUMBER: _item_get_number,
    _obs.OBS_DATA_STRING: _obs.obs_data_item_get_string,
    _obs.OBS_DATA_BOOLEAN: _obs.obs_data_item_get_bool,
    _obs.OBS_DATA_NULL: (lambda *_: None),
}


def get_value(data, key):
    """Gets the value of item 'key' from OBS data object 'data'"""
    item = _obs.obs_data_item_byname(data, key)
    if item is None:
        raise LookupError(key)
    kind = _obs.obs_data_item_gettype(item)
    try:
        return _ITEM_GET_FUNC[kind](item)
    except LookupError:
        raise TypeError("unsupported data type")


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

