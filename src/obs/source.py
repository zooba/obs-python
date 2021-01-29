from .loop import Future, LOOP
from ._helper import rendered_data_to_bytes

class Source:
    def __init__(self, name, loop=None):
        self.name = name
        self._steps = []

    def _do(self, cmd, *args, future=None):
        LOOP.schedule(cmd, self.name, *args, future=future)

    def show(self):
        self._do("obs_source_inc_showing")

    def hide(self):
        self._do("obs_source_dec_showing")

    def activate(self):
        self._do("obs_source_inc_active")

    def deactivate(self):
        self._do("obs_source_dec_active")

    def get_type(self):
        f = Future()
        self._do("obs_source_get_type", future=f)
        return f.result()

    def __getitem__(self, key):
        f = Future()
        self._do("obs_source_get_property_value", key, future=f)
        return f.result()

    def __setitem__(self, key, value):
        self._do("obs_source_set_property_values", {key: value})

    def update(self, key_values):
        self._do("obs_source_set_property_values", dict(key_values))

    def get_frame(self):
        f = Future()
        self._do("obs_source_get_frame_data", future=f)
        data = f.result()
        r = rendered_data_to_bytes(data)
        self._do("obs_source_destroy_frame_data", data)
        return r
