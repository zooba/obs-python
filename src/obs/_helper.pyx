
# cython: language_level=3

from _obs cimport *

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
