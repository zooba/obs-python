from .loop import Future, LOOP

__all__ = ["SceneItem"]


class SceneItem:
    def __init__(self, scene_name, source, type_=None, owner=None):
        self.scene_name = scene_name
        self.source = source
        self._steps = []
        self._type = type_
        self.owner = owner

    def _do(self, cmd, *args, future=None):
        LOOP.schedule(cmd, self.scene_name, self.source.name, *args, future=future)

    def _call(self, cmd, *args):
        f = Future()
        self._do(cmd, *args, future=f)
        return f.result()

    def __repr__(self):
        return f'<"{self.source.name}" in "{self.scene_name}">'

    def __hash__(self):
        return hash(SceneItem) ^ hash(self.scene_name) ^ hash(self.source)

    def __eq__(self, other):
        return (isinstance(other, SceneItem)
                and self.scene_name == other.scene_name
                and self.source == other.source)

    def __ne__(self, other):
        return not self.__eq__(other)

    def get_pos(self):
        return self._call("obs_sceneitem_get_pos")

    def set_pos(self, x, y):
        self._do("obs_sceneitem_set_pos", (x, y))

    def get_crop(self):
        return self._call("obs_sceneitem_get_crop")

    def set_crop(self, left, right, top, bottom):
        self._do("obs_sceneitem_set_crop", (left, right, top, bottom))
