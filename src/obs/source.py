from .loop import Future, LOOP

__all__ = ["Source"]


class FrameData:
    def __init__(self, _future):
        self._future = _future

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    def __iter__(self):
        return iter(self._future.result())

    def close(self):
        try:
            d = self._future.result()
        except RuntimeError:
            pass
        else:
            LOOP.schedule("close_object", d, always=True)


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
        return FrameData(f)

    def get_pos(self):
        f = Future()
        self._do("obs_source_get_pos", future=f)
        return f.result()

    def set_pos(self, x, y):
        self._do("obs_source_set_pos", (x, y))

    def get_crop(self):
        f = Future()
        self._do("obs_source_get_crop", future=f)
        return f.result()

    def set_crop(self, left, right, top, bottom):
        self._do("obs_source_set_crop", (left, right, top, bottom))

    def adjust_crop(self, d_left, d_right, d_top, d_bottom):
        self._do("obs_source_adjust_crop", (d_left, d_right, d_top, d_bottom))
