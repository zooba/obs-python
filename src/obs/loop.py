import obspython as _obs
import threading
import traceback

from . import data as _data
from . import _helper

class Future:
    _NOTSET = object()
    _EXCEPTION = object()
    _INTERRUPT = object()
    _WAITING = []

    def __init__(self):
        self._result = self._NOTSET
        self._exception = None
        self._lock = {}

    def has_result(self):
        return self._result is not self._NOTSET

    def result(self, timeout=-1):
        r = self._result
        if r is not self._NOTSET:
            if r is self._EXCEPTION:
                raise RuntimeError(self._exception)
            elif r is self._INTERRUPT:
                raise KeyboardInterrupt(self._exception)
            return r
        l = self._lock.get("o")
        if l is None:
            l = threading.Lock()
            l.acquire()
            l = self._lock.setdefault("o", l)
        r = self._result
        if r is self._NOTSET:
            self._WAITING.append(self)
            try:
                if not l.acquire(timeout=timeout):
                    raise TimeoutError()
            finally:
                self._WAITING.remove(self)
            r = self._result
            if r is self._NOTSET:
                raise TimeoutError()
        if r is self._EXCEPTION:
            raise RuntimeError(self._exception)
        elif r is self._INTERRUPT:
            raise KeyboardInterrupt(self._exception)
        return r

    def set_result(self, value):
        self._result = value
        l = self._lock.pop("o", None)
        if l is not None:
            l.release()

    def set_exception(self, message):
        self._exception = message
        self.set_result(self._EXCEPTION)

    def interrupt(self, message):
        self._exception = message
        self.set_result(self._INTERRUPT)


class _SourceReleaser:
    def __init__(self, source, returns=None, is_sceneitem=False):
        self._source = source
        self._returns = returns
        self._is_sceneitem = is_sceneitem

    def __enter__(self):
        return self._returns or self._source

    def __exit__(self, exc_type, exc_value, exc_tb):
        if self._is_sceneitem:
            _obs.obs_sceneitem_release(self._source)
        else:
            _obs.obs_source_release(self._source)


class Loop:
    def __init__(self):
        self.steps = []
        self.interval = 10
        self.steps_per_interval = 10
        self._tls = threading.local()
        self._tls.abort = Future()
        self._tls.is_main = True
        self._threads = []
        self._started = False

    def _process(self):
        if not self.steps:
            return
        todo = self.steps_per_interval
        steps = self.steps
        while steps and todo > 0:
            fn, args, future = steps.pop(0)
            try:
                r = fn(*args)
                if future:
                    future.set_result(r)
            except Exception as ex:
                _obs.remove_current_callback()
                self._started = False
                if future:
                    future.set_exception(ex)
                traceback.print_exc()
                return
            steps = self.steps
            todo -= 1

    def start(self):
        if not self._started:
            self._started = True
            _obs.timer_add(self._process, self.interval)

    def reset(self):
        threads, self._threads = self._threads, []
        self.steps = []
        for t in threads:
            t.interrupt("Resetting")
        for f in Future._WAITING:
            f.interrupt("Resetting")
        self.start()

    def schedule(self, cmd, *args, future=None, always=False):
        self.schedule_call(getattr(self, "_" + cmd), *args, future=future, always=always)

    def schedule_call(self, callable, *args, future=None, always=False):
        if not always:
            try:
                abort = self._tls.abort
            except AttributeError:
                pass
            else:
                if abort.has_result():
                    raise KeyboardInterrupt
            if self._tls.is_main:
                try:
                    r = callable(*args)
                except Exception as ex:
                    if future:
                        future.set_exception(ex)
                else:
                    if future:
                        future.set_result(r)
                return
        self.steps.append((callable, args, future))

    def _source_by_name(self, name):
        s = _obs.obs_get_source_by_name(name)
        if not s:
            raise LookupError("no source named {}".format(name))
        return _SourceReleaser(s)

    def _filter_by_name(self, source_name, filter_name):
        s = _obs.obs_get_source_by_name(source_name)
        if not s:
            raise LookupError("no source named {}".format(source_name))
        try:
            f = _obs.obs_source_get_filter_by_name(s, filter_name)
            if not f:
                raise LookupError("no filter named {} on source {}".format(filter_name, source_name))
            return _SourceReleaser(f)
        finally:
            _obs.obs_source_release(s)

    def _sceneitem_by_name(self, scene_name, name):
        with self._source_by_name(scene_name) as source:
            scene = _obs.obs_scene_from_source(source)
            if not scene:
                raise LookupError("no scene named {}".format(scene_name))
            i = _obs.obs_scene_find_source_recursive(scene, name)
            if i is None:
                raise LookupError("no sceneitem named {}".format(name))
            _obs.obs_sceneitem_addref(i)
            return _SourceReleaser(i, is_sceneitem=True)

    def _updated(self, props, data, values, on_update):
        for p in props:
            values.update(p._get(data))
        if on_update:
            on_update()

    def _new_thread(self, callable):
        def _starter():
            self._tls.abort = a = Future()
            self._tls.is_main = False
            self._threads.append(a)
            try:
                callable()
            except KeyboardInterrupt:
                pass
        t = threading.Thread(target=_starter)
        t.start()

    def _obs_source_get_type(self, source_name):
        with self._source_by_name(source_name) as s:
            return _obs.obs_source_get_unversioned_id(s)

    def _obs_source_get_property_values(self, source_name):
        with self._source_by_name(source_name) as s:
            d = _obs.obs_source_get_settings(s)
            try:
                return _data.get_values(d)
            finally:
                _obs.obs_data_release(d)

    def _obs_source_set_property_values(self, source_name, values):
        with self._source_by_name(source_name) as s:
            d = _obs.obs_data_create()
            try:
                _data.set_data(d, values.items())
                _obs.obs_source_update(s, d)
            finally:
                _obs.obs_data_release(d)

    def _obs_filter_get_property_values(self, filter_name, owner_name):
        with self._filter_by_name(owner_name, filter_name) as s:
            d = _obs.obs_source_get_settings(s)
            try:
                return _data.get_values(d)
            finally:
                _obs.obs_data_release(d)

    def _obs_filter_set_property_values(self, filter_name, owner_name, values):
        with self._filter_by_name(owner_name, filter_name) as s:
            d = _obs.obs_data_create()
            try:
                _data.set_data(d, values.items())
                _obs.obs_source_update(s, d)
            finally:
                _obs.obs_data_release(d)



    def _obs_source_get_frame_data(self, source_name):
        with self._source_by_name(source_name) as s:
            return _helper.render_source_to_data(s)

    def _close_object(self, obj):
        obj.close()


    def _obs_sceneitem_get_pos(self, scene_name, source_name):
        with self._sceneitem_by_name(scene_name, source_name) as si:
            p = _obs.vec2()
            _obs.obs_sceneitem_get_pos(si, p)
            return p.x, p.y

    def _obs_sceneitem_set_pos(self, scene_name, source_name, pos):
        with self._sceneitem_by_name(scene_name, source_name) as si:
            p = _obs.vec2()
            p.x, p.y = pos
            _obs.obs_sceneitem_set_pos(si, p)

    def _obs_sceneitem_get_crop(self, scene_name, source_name):
        with self._sceneitem_by_name(scene_name, source_name) as si:
            crop = _obs.obs_sceneitem_crop()
            _obs.obs_sceneitem_get_crop(si, crop)
            return crop.left, crop.right, crop.top, crop.bottom

    def _obs_sceneitem_set_crop(self, scene_name, source_name, crop_sizes):
        with self._sceneitem_by_name(scene_name, source_name) as si:
            crop = _obs.obs_sceneitem_crop()
            crop.left, crop.right, crop.top, crop.bottom = crop_sizes
            _obs.obs_sceneitem_set_crop(si, crop)


    def _obs_source_get_sync_offset(self, source_name):
        with self._source_by_name(source_name) as s:
            return _obs.obs_source_get_sync_offset(s)

    def _obs_source_set_sync_offset(self, source_name, offset):
        with self._source_by_name(source_name) as s:
            _obs.obs_source_set_sync_offset(s, offset)


    def _obs_source_get_filters(self, source_name, filter_cls):
        with self._source_by_name(source_name) as s:
            return [filter_cls(n, k)
                    for n, k in _helper.get_filter_names(s)]


LOOP = Loop()
