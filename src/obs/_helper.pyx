
# cython: language_level=3

from _obs cimport *
from cpython.ref cimport PyObject

cdef extern from "Python.h":
    void PyErr_WriteUnraisable(void *)


import sys

cdef class RenderedData:
    cdef void *stagesurf
    cdef public unsigned int width, height, depth
    cdef unsigned char *texdata
    cdef unsigned int linesize

    def __cinit__(self):
        self.stagesurf = NULL

    def __iter__(self):
        i = 0
        cx = self.width * self.depth
        stride = self.linesize
        for _ in range(self.height):
            yield self.texdata[i:i + cx]
            i += stride

    def __getitem__(self, pts):
        cdef bytearray r
        cdef unsigned int p, cx, cy, depth, stride, i
        if isinstance(pts, int):
            y = pts * self.linesize
            return self.texdata[y:y + self.width * self.depth]
        if isinstance(pts, list):
            i = 0
            cx = self.width
            cy = self.height
            stride = self.linesize
            depth = self.depth
            r = bytearray([0x80]) * (len(pts) * depth)
            for x, y in <list>pts:
                if 0 <= x < cx and 0 <= y < cy:
                    p = y * stride + x * depth
                    r[i:i + depth] = self.texdata[p:p + depth]
                i += depth
            return r
        raise TypeError("argument must be a row index or list of (x, y) pairs")

    def close(self):
        s = self.stagesurf
        self.stagesurf = NULL
        if s:
            with nogil:
                obs_enter_graphics()
                gs_stagesurface_unmap(s)
                gs_stagesurface_destroy(s)
                obs_leave_graphics()

    def __dealloc__(self):
        self.close()


def render_source_to_data(size_t source, uint32_t color_depth=GS_R8):
    cdef void *texrender = NULL
    cdef void *stagesurf = NULL
    cdef RenderedData r = RenderedData()
    cdef vec4 zero

    # TODO: support greater depth
    if color_depth == GS_R8 or color_depth == GS_A8:
        r.depth = 1
    else:
        raise ValueError("unsupported color depth")

    cdef void *s = <void*>source

    try:
        with nogil:
            obs_enter_graphics()

            r.width = cx = obs_source_get_width(s)
            r.height = cy = obs_source_get_height(s)

            texrender = gs_texrender_create(color_depth, GS_ZS_NONE)
            gs_texrender_reset(texrender)

            if not gs_texrender_begin(texrender, cx, cy):
                raise RuntimeError("failed to render")
            try:
                vec4_zero(&zero)
                gs_clear(GS_CLEAR_COLOR, &zero, 0.0, 0)
                gs_ortho(0.0, cx, 0.0, cy, -100.0, 100.0)
                gs_blend_state_push()
                gs_blend_function(GS_BLEND_ONE, GS_BLEND_ZERO)
                obs_source_inc_showing(s)
                obs_source_video_render(s)
                obs_source_dec_showing(s)
                gs_blend_state_pop()
            finally:
                gs_texrender_end(texrender)

            texture = gs_texrender_get_texture(texrender)
            stagesurf = gs_stagesurface_create(cx, cy, color_depth)
            gs_stage_texture(stagesurf, texture)
            gs_stagesurface_map(stagesurf, &r.texdata, &r.linesize)
            r.stagesurf = stagesurf
            stagesurf = NULL
        return r
    finally:
        if stagesurf:
            gs_stagesurface_destroy(stagesurf)
        if texrender:
            gs_texrender_destroy(texrender)
        obs_leave_graphics()


def get_property_names(size_t properties):
    cdef void *ps = <void *>properties

    cdef void *p = obs_properties_first(ps)
    cdef bytes n
    r = []
    while p:
        n = obs_property_name(p)
        if n:
            r.append(n.decode("utf-8"))
            if OBS_PROPERTY_GROUP == obs_property_get_type(p):
                ps2 = obs_property_group_content(p)
                if ps2:
                    r.extend(get_property_names(<size_t>ps2))
        if not obs_property_next(&p):
            break
    return r


def read_data(size_t data, names):
    if not data:
        return {}
    return _read_data(<void*>data, names)


cdef object _read_data(void *data, object names):
    cdef str n
    cdef void *d
    cdef uint32_t dtype
    cdef void *o
    cdef bytes s
    d = obs_data_first(data)
    r = {}
    while d:
        n = obs_data_item_get_name(d).decode()
        if n and (not names or n in names):
            dtype = obs_data_item_gettype(d)
            if dtype == OBS_DATA_NULL:
                r[n] = None
            elif dtype == OBS_DATA_STRING:
                s = obs_data_item_get_string(d)
                r[n] = s.decode()
            elif dtype == OBS_DATA_NUMBER:
                dtype = obs_data_item_numtype(d)
                if dtype == OBS_DATA_NUM_INT:
                    r[n] = obs_data_item_get_int(d)
                elif dtype == OBS_DATA_NUM_DOUBLE:
                    r[n] = obs_data_item_get_double(d)
                else:
                    r[n] = f"Unhandled numtype: {dtype}"
            elif dtype == OBS_DATA_BOOLEAN:
                r[n] = obs_data_item_get_bool(d)
            elif dtype == OBS_DATA_OBJECT or dtype == OBS_DATA_ARRAY:
                o = obs_data_item_get_obj(d)
                r[n] = _read_data(o, None)
                obs_data_release(o)
            else:
                r[n] = f"Unhandled type: {dtype}"
        if not obs_data_item_next(&d):
            break
    return r


def read_data_array(size_t data_array):
    if not data_array:
        return []
    return _read_data_array(<void*>data_array)


cdef object _read_data_array(void* data_array):
    cdef void *item
    r = []
    for i in range(obs_data_array_count(data_array)):
        item = obs_data_array_item(data_array, i)
        if item:
            try:
                r.append(read_data(<size_t>item, None))
            finally:
                obs_data_release(item)
        else:
            r.append(None)
    return r


cdef void _append_filter_data(void *source, void *filter, void *list_obj) nogil:
    cdef const char *name = obs_source_get_name(filter)
    cdef const char *kind = obs_source_get_unversioned_id(filter)
    cdef PyObject *list_ = <PyObject*>list_obj
    with gil:
        try:
            (<list>list_).append((name.decode(), kind.decode()))
        except Exception as ex:
            PyErr_WriteUnraisable(NULL)


def get_filter_names(size_t source):
    cdef void *source_ = <void*>source
    cdef list result = list()
    obs_source_enum_filters(source_, <obs_source_enum_proc_t>_append_filter_data, <PyObject*>result)
    return result


cdef bool _append_scene(void *list_obj, void *source) nogil:
    cdef const char *name = obs_source_get_name(source)
    cdef PyObject *list_ = <PyObject*>list_obj
    with gil:
        try:
            (<list>list_).append((name.decode(), <size_t>obs_source_get_ref(source)))
        except Exception as ex:
            PyErr_WriteUnraisable(NULL)
    return True


def get_scene_names():
    cdef list items = list()
    with nogil:
        obs_enum_scenes(_append_scene, <PyObject*>items)
    result = []
    for n, p in items:
        obs_source_release(<void*><size_t>p)
        result.append(n)
    return result


cdef bool _append_sceneitem_data(void *scene, void *sceneitem, void *list_obj) nogil:
    cdef void *source = obs_sceneitem_get_source(sceneitem)
    if not source:
        return True
    cdef const char *name = obs_source_get_name(source)
    cdef const char *kind = obs_source_get_unversioned_id(source)
    cdef PyObject *list_ = <PyObject*>list_obj
    with gil:
        try:
            (<list>list_).append((name.decode(), kind.decode()))
        except Exception as ex:
            PyErr_WriteUnraisable(NULL)
    return True


def get_scene_item_names(str scene_name):
    cdef void *source = NULL
    cdef list result = []
    cdef bytes scene_name_ = scene_name.encode("utf-8")
    cdef const char *pscene_name = scene_name_
    with nogil:
        source = obs_get_source_by_name(pscene_name)
        if not source:
            with gil:
                raise LookupError(f"no scene named {scene_name}")
        obs_scene_enum_items(obs_scene_from_source(source), _append_sceneitem_data, <PyObject*>result)
        obs_source_release(source)
    return result
