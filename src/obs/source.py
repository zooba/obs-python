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

    def __getitem__(self, key):
        return self._future.result()[key]

    @property
    def width(self):
        return self._future.result().width

    @property
    def height(self):
        return self._future.result().height

    @property
    def depth(self):
        return self._future.result().depth

    def close(self):
        try:
            d = self._future.result()
        except RuntimeError:
            pass
        else:
            LOOP.schedule("close_object", d, always=True)


class Source:
    def __init__(self, name, type_=None, owner=None):
        self.name = name
        self._steps = []
        self._type = type_
        self.owner = owner

    def _do(self, cmd, *args, future=None):
        LOOP.schedule(cmd, self.name, *args, future=future)

    def _call(self, cmd, *args):
        f = Future()
        self._do(cmd, *args, future=f)
        return f.result()

    def __repr__(self):
        return f"<{self._type or 'Source'} \"{self.name}\">"

    def get_type(self):
        if self._type:
            return self._type
        f = Future()
        self._do("obs_source_get_type", future=f)
        return f.result()

    def __getitem__(self, key):
        if self.owner:
            values = self._call("obs_filter_get_property_values", self.owner.name)
        else:
            values = self._call("obs_source_get_property_values")
        if isinstance(key, slice):
            if key.start or key.stop or key.step:
                raise KeyError("sources only support [:] slices")
            return values
        elif isinstance(key, tuple):
            return {k: values[k] for k in key}
        else:
            return values[key]

    def __setitem__(self, key, value):
        if self.owner:
            self._do("obs_filter_set_property_values", self.owner.name, {key: value})
        else:
            self._do("obs_source_set_property_values", {key: value})

    def update(self, key_values):
        self._do("obs_source_set_property_values", dict(key_values))

    def get_filters(self):
        return self._call("obs_source_get_filters", lambda n, k: Source(n, k, owner=self))

    def get_frame(self):
        f = Future()
        self._do("obs_source_get_frame_data", future=f)
        return FrameData(f)

    def get_pos(self):
        return self._call("obs_source_get_pos")

    def set_pos(self, x, y):
        self._do("obs_source_set_pos", (x, y))

    def get_crop(self):
        return self._call("obs_source_get_crop")

    def set_crop(self, left, right, top, bottom):
        self._do("obs_source_set_crop", (left, right, top, bottom))

    def adjust_crop(self, d_left, d_right, d_top, d_bottom):
        self._do("obs_source_adjust_crop", (d_left, d_right, d_top, d_bottom))

    def get_sync_offset(self):
        return self._call("obs_source_get_sync_offset")

    def set_sync_offset(self, offset):
        self._do("obs_source_set_sync_offset", offset)
