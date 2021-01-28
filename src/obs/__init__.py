import obspython as _obs
from . import loop as _loop
from . import props as _props

def run(callable):
    _loop.LOOP.schedule("new_thread", callable)

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
        def script_properties():
            return _props.render(PROPS)

        VALUES = globals.setdefault("VALUES", {})
        for p in PROPS:
            VALUES.update(p._default())

        def script_defaults(data):
            defaults = {}
            for p in PROPS:
                defaults.update(p._default())
            f = _loop.Future()
            _loop.LOOP.schedule("defaults", data, defaults, future=f)
            return f.result()

        try:
            ON_UPDATE = globals["on_update"]
        except LookupError:
            ON_UPDATE = None

        def script_update(data):
            _loop.LOOP.reset()
            _loop.LOOP.schedule("updated", PROPS, data, VALUES, ON_UPDATE)

        globals["script_properties"] = script_properties
        globals["script_update"] = script_update
        globals["script_defaults"] = script_defaults
