import obspython as _obs
import threading
import traceback

from . import data as _data


class Future:
    _NOTSET = object()
    _EXCEPTION = object()
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
        return r

    def set_result(self, value):
        self._result = value
        l = self._lock.pop("o", None)
        if l is not None:
            l.release()

    def set_exception(self, message):
        self._exception = message
        self.set_result(self._EXCEPTION)


class _SourceReleaser:
    def __init__(self, source):
        self._source = source

    def __enter__(self):
        return self._source

    def __exit__(self, exc_type, exc_value, exc_tb):
        _obs.obs_source_release(self._source)


class Loop:
    def __init__(self):
        self.steps = []
        self.interval = 10
        self.steps_per_interval = 10
        self._tls = threading.local()
        self._tls.abort = Future()
        self._threads = []

    def _process(self):
        if not self.steps:
            return
        _obs.remove_current_callback()
        todo = self.steps_per_interval
        steps = self.steps
        while steps and todo > 0:
            fn, args, future = steps.pop(0)
            try:
                r = fn(*args)
                if future:
                    future.set_result(r)
            except Exception as ex:
                if future:
                    future.set_exception(ex)
                traceback.print_exc()
                return
            steps = self.steps
            todo -= 1
        _obs.timer_add(self._process, self.interval)

    def reset(self):
        threads, self._threads = self._threads, []
        self.steps = []
        for t in threads:
            t.set_exception("Resetting")
        for f in Future._WAITING:
            f.set_exception("Resetting")
        _obs.timer_add(self._process, self.interval)

    def schedule(self, cmd, *args, future=None):
        try:
            abort = self._tls.abort
        except AttributeError:
            pass
        else:
            if abort.has_result():
                raise KeyboardInterrupt
        self.steps.append((getattr(self, "_" + cmd), args, future))

    def _source_by_name(self, name):
        s = _obs.obs_get_source_by_name(name)
        if not s:
            raise LookupError("no source named {}".format(name))
        return _SourceReleaser(s)

    def _updated(self, props, data, values, on_update):
        for p in props:
            values.update(p._get(data))
        if on_update:
            on_update()

    def _defaults(self, data, defaults):
        return _data.set_data(data, defaults.items(), defaults=True)

    def _new_thread(self, callable):
        def _starter():
            self._tls.abort = a = Future()
            self._threads.append(a)
            try:
                callable()
            except KeyboardInterrupt:
                pass
        t = threading.Thread(target=_starter)
        t.start()

    def _obs_source_inc_showing(self, source_name):
        with self._source_by_name(source_name) as s:
            _obs.obs_source_inc_showing(s)

    def _obs_source_dec_showing(self, source_name):
        with self._source_by_name(source_name) as s:
            _obs.obs_source_dec_showing(s)

    def _obs_source_inc_active(self, source_name):
        with self._source_by_name(source_name) as s:
            _obs.obs_source_inc_active(s)

    def _obs_source_dec_active(self, source_name):
        with self._source_by_name(source_name) as s:
            _obs.obs_source_dec_active(s)

    def _obs_source_get_type(self, source_name):
        with self._source_by_name(source_name) as s:
            return _obs.obs_source_get_unversioned_id(s)

    def _obs_source_get_property_values(self, source_name, property_name):
        pass

    def _obs_source_set_property_values(self, source_name, values):
        with self._source_by_name(source_name) as s:
            d = _obs.obs_data_create()
            try:
                for k, v in values.items():
                    if isinstance(v, str):
                        _obs.obs_data_set_string(d, k, v)
                _obs.obs_source_update(s, d)
            finally:
                _obs.obs_data_release(d)


LOOP = Loop()
