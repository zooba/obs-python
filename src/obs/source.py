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

    def __hash__(self):
        return hash(Source) ^ hash(self.name)

    def __eq__(self, other):
        return isinstance(other, Source) and self.name == other.name

    def __ne__(self, other):
        return not self.__eq__(other)

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

    def get_sync_offset(self):
        return self._call("obs_source_get_sync_offset")

    def set_sync_offset(self, offset):
        self._do("obs_source_set_sync_offset", offset)
