
# cython: language_level=3

cdef extern from "Windows.h" nogil:
    ctypedef void *HMODULE
    cdef HMODULE GetModuleHandleA(const char*)
    cdef void *GetProcAddress(HMODULE, const char*)

cdef extern from "stdint.h" nogil:
    ctypedef unsigned int uint64_t
    ctypedef unsigned int uint32_t
    ctypedef unsigned int uint8_t

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

