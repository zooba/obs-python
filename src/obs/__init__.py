import obspython as _obs
from . import data as _data
from . import loop as _loop
from . import props as _props

def run(callable):
    _loop.LOOP.schedule("new_thread", callable)


def get_source(source):
    from .source import Source
    return Source(source)


def get_sceneitem(scene, source):
    from .sceneitem import SceneItem
    from .source import Source
    return SceneItem(scene, Source(source))


def ready(globals):
    try:
        desc = globals["__doc__"]
    except LookupError:
        pass
    else:
        def script_description():
            return desc
        globals["script_description"] = script_description

    _loop.LOOP.reset()

    try:
        PROPS = globals["PROPERTIES"]
    except LookupError:
        pass
    else:
        VALUES = globals.setdefault("VALUES", {})
        FUNCS = {k: v for k, v in globals.items()
                 if k.startswith("on_") and k.endswith("_changed")
                 and callable(v)}

        def on_prop_changed(properties, prop, data=None):
            n = _obs.obs_property_name(prop)
            k = "on_{}_changed".format(n)
            v = None
            if data:
                try:
                    VALUES[n] = v = _data.get_value(data, n)
                except LookupError:
                    pass
            try:
                fn = FUNCS[k]
            except KeyError:
                pass
            else:
                return fn(v)

        def script_properties():
            return _props.render(PROPS, on_prop_changed)

        def script_defaults(data):
            for p in PROPS:
                p._defaults(data)

        try:
            ON_UPDATE = globals["on_update"]
        except LookupError:
            ON_UPDATE = None

        def script_update(data):
            _loop.LOOP.start()
            _loop.LOOP.schedule("updated", PROPS, data, VALUES, ON_UPDATE)

        globals["script_properties"] = script_properties
        globals["script_update"] = script_update
        globals["script_defaults"] = script_defaults
