
# cython: language_level=3

cdef extern from "Windows.h" nogil:
    ctypedef void *HMODULE
    cdef HMODULE GetModuleHandleA(const char*)
    cdef void *GetProcAddress(HMODULE, const char*)

cdef extern from "obsdecls.h" nogil:
    ctypedef void (*OBS_V)()
    ctypedef void* (*OBS_S_TO_P)(const char*)
    ctypedef void (*OBS_P_TO_V)(void*)
    ctypedef void* (*OBS_P_TO_P)(void*)
    ctypedef int (*OBS_P_TO_I)(void*)
    ctypedef void* (*OBS_II_TO_P)(int, int)
    ctypedef void (*OBS_PII_TO_V)(void*, int, int)
    ctypedef int (*OBS_PII_TO_I)(void*, int, int)
    ctypedef void* (*OBS_III_TO_P)(int, int, int)
    ctypedef void (*OBS_PP_TO_V)(void*, void*)
    ctypedef void (*OBS_PPP_TO_V)(void*, void*, void*)

cdef HMODULE _mod = GetModuleHandleA("obs")
import obspython as _obs


cdef void* gs_texrender_create(int c, int z) nogil:
    return (<OBS_II_TO_P>GetProcAddress(_mod, "gs_texrender_create"))(c, z)

cdef int gs_texrender_begin(void *tr, int cx, int cy) nogil:
    return (<OBS_PII_TO_I>GetProcAddress(_mod, "gs_texrender_begin"))(tr, cx ,cy)

cdef void gs_texrender_end(void *tr) nogil:
    (<OBS_P_TO_V>GetProcAddress(_mod, "gs_texrender_end"))(tr)

cdef void gs_texrender_destroy(void *tr) nogil:
    (<OBS_P_TO_V>GetProcAddress(_mod, "gs_texrender_destroy"))(tr)

cdef void gs_texrender_reset(void *tr) nogil:
    (<OBS_P_TO_V>GetProcAddress(_mod, "gs_texrender_reset"))(tr)

cdef void* gs_texrender_get_texture(void *tr) nogil:
    return (<OBS_P_TO_P>GetProcAddress(_mod, "gs_texrender_get_texture"))(tr)

cdef void* gs_stagesurface_create(int cx, int cy, int c) nogil:
    return (<OBS_III_TO_P>GetProcAddress(_mod, "gs_stagesurface_create"))(cx, cy, c)

cdef void gs_stage_texture(void* ss, void* tex) nogil:
    (<OBS_PP_TO_V>GetProcAddress(_mod, "gs_stage_texture"))(ss, tex)

cdef void gs_stagesurface_map(void* ss, void* out_data, void* out_stride) nogil:
    (<OBS_PPP_TO_V>GetProcAddress(_mod, "gs_stagesurface_map"))(ss, out_data, out_stride)

cdef void gs_stagesurface_unmap(void* ss) nogil:
    (<OBS_P_TO_V>GetProcAddress(_mod, "gs_stagesurface_unmap"))(ss)

cdef void gs_stagesurface_destroy(void* ss) nogil:
    (<OBS_P_TO_V>GetProcAddress(_mod, "gs_stagesurface_destroy"))(ss)


cdef class RenderedData:
    cdef void *stagesurf
    cdef public unsigned int cx, cy, depth
    cdef unsigned char *texdata
    cdef unsigned int linesize

    def __cinit__(self):
        self.stagesurf = NULL

    def __iter__(self):
        i = 0
        cx = self.cx * self.depth
        stride = self.linesize
        for _ in range(self.cy):
            yield self.texdata[i:i + cx]
            i += stride

    def __getitem__(self, int y):
        y *= self.linesize
        return self.texdata[y:y + self.cx * self.depth]

    def close(self):
        if self.stagesurf:
            _obs.obs_enter_graphics()
            gs_stagesurface_unmap(self.stagesurf)
            gs_stagesurface_destroy(self.stagesurf)
            self.stagesurf = NULL
            _obs.obs_leave_graphics()

    def __dealloc__(self):
        self.close()


def render_source_to_data(source):
    cdef void *texrender = NULL
    cdef void *stagesurf = NULL
    cdef RenderedData r = RenderedData()

    # TODO: support greater depth
    cdef int depth = _obs.GS_R8
    r.depth = 1

    try:
        cx = <unsigned int>_obs.obs_source_get_width(source)
        cy = <unsigned int>_obs.obs_source_get_height(source)
        r.cx = cx
        r.cy = cy
        _obs.obs_enter_graphics()

        texrender = gs_texrender_create(depth, _obs.GS_ZS_NONE)
        gs_texrender_reset(texrender)
        
        if not gs_texrender_begin(texrender, cx, cy):
            raise RuntimeError("failed to render")
        try:
            zero = _obs.vec4()
            _obs.vec4_zero(zero)
            _obs.gs_clear(_obs.GS_CLEAR_COLOR, zero, 0.0, 0)
            _obs.gs_ortho(0.0, cx, 0.0, cy, -100.0, 100.0)
            _obs.gs_blend_state_push()
            _obs.gs_blend_function(_obs.GS_BLEND_ONE, _obs.GS_BLEND_ZERO)
            _obs.obs_source_inc_showing(source)
            _obs.obs_source_video_render(source)
            _obs.obs_source_dec_showing(source)
            _obs.gs_blend_state_pop()
        finally:
            gs_texrender_end(texrender)

        with nogil:
            texture = gs_texrender_get_texture(texrender)
            stagesurf = gs_stagesurface_create(cx, cy, depth)
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
        _obs.obs_leave_graphics()
