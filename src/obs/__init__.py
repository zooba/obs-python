import obspython as _obs
from . import props as _props

def ready(globals):
    try:
        desc = globals["__doc__"]
    except LookupError:
        pass
    else:
        def script_description():
            return desc
        globals["script_description"] = script_description

    try:
        props = globals["PROPERTIES"]
    except LookupError:
        pass
    else:
        def script_properties():
            return _props.render(*props)

        values = globals.setdefault("VALUES", {})
        values.update({p.name: p._default() for p in props})

        try:
            on_update = globals["on_update"]
        except LookupError:
            on_update = None

        def script_update(data):
            for p in props:
                values[p.name] = p._get(data)
            if on_update:
                on_update()

        globals["script_properties"] = script_properties
        globals["script_update"] = script_update
