
# cython: language_level=3

cdef extern from "Windows.h" nogil:
    ctypedef void *HMODULE
    cdef HMODULE GetModuleHandleA(const char*)
    cdef void *GetProcAddress(HMODULE, const char*)

cdef extern from "stdint.h" nogil:
    ctypedef int uint32_t
    ctypedef int uint8_t

cdef extern from "stdbool.h" nogil:
    ctypedef bint bool

cdef extern from "graphics/vec4.h" nogil:
    cdef struct vec4:
        pass
    void vec4_zero(vec4* v)

cdef extern from "obs.h" nogil:
    uint32_t GS_A8, GS_R8
    uint32_t GS_ZS_NONE
    uint32_t GS_CLEAR_COLOR, GS_CLEAR_DEPTH
    uint32_t GS_BLEND_ZERO, GS_BLEND_ONE

    void* gs_texrender_create(uint32_t color_format, uint32_t z_stencil_format)
    int gs_texrender_begin(void *texrender, uint32_t width, uint32_t height)
    void gs_texrender_end(void *texrender)
    void gs_texrender_destroy(void *texrender)
    void gs_texrender_reset(void *texrender)
    void* gs_texrender_get_texture(void *texrender)

    void gs_stage_texture(void* surface, void* texture)
    void* gs_stagesurface_create(uint32_t width, uint32_t height, uint32_t color_format)
    uint32_t gs_stagesurface_get_width(void* surface)
    uint32_t gs_stagesurface_get_height(void* surface)
    uint32_t gs_stagesurface_get_color_format(void* surface)
    void gs_stagesurface_map(void* surface, void* out_data, void* out_stride)
    void gs_stagesurface_unmap(void* surface)
    void gs_stagesurface_destroy(void* surface)

    void gs_clear(uint32_t flags, vec4* color, float depth, uint8_t stencil)
    void gs_ortho(float left, float right, float top, float bottom, float znear, float zfar)

    void gs_blend_state_push()
    void gs_blend_state_pop()
    void gs_blend_function(uint32_t src, uint32_t dest)

    void obs_enter_graphics()
    void obs_leave_graphics()

    void* obs_get_source_by_name(const char* name)
    uint32_t obs_source_get_width(void* source)
    uint32_t obs_source_get_height(void* source)
    void obs_source_inc_showing(void* source)
    void obs_source_video_render(void* source)
    void obs_source_dec_showing(void* source)


    uint32_t OBS_PROPERTY_GROUP

    void* obs_properties_first(void* props);
    bool obs_property_next(void** p)
    const char *obs_property_name(void* p)
    bool obs_property_enabled(void* p)
    bool obs_property_visible(void* p)
    uint32_t obs_property_get_type(void* p)
    bool obs_property_modified(void* p, void* data)
    void* obs_property_group_content(void* p)


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


def get_property_names(size_t properties, size_t if_set_in_data=0):
    cdef void *ps = <void *>properties
    cdef void *data = <void *>if_set_in_data

    cdef void *p = obs_properties_first(ps)
    cdef bytes n
    r = []
    while p:
        if data:
            pass # TODO
        n = obs_property_name(p)
        if n:
            r.append(n.decode("utf-8"))
            if OBS_PROPERTY_GROUP == obs_property_get_type(p):
                ps2 = obs_property_group_content(p)
                if ps2:
                    r.extend(get_property_names(<size_t>ps2, if_set_in_data))
        if not obs_property_next(&p):
            p = NULL
    return r
