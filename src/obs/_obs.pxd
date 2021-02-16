
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

    void* obs_source_get_ref(void* source)
    void obs_source_release(void* source)
    const char* obs_source_get_name(void* source)
    const char* obs_source_get_unversioned_id(void* source)
    ctypedef void (*obs_source_enum_proc_t)(void*, void*, void*)
    void obs_source_enum_filters(void* source, obs_source_enum_proc_t callback, void* data)

    void obs_enum_scenes(bool (*callback)(void* data, void* scene), void* data)
    void* obs_scene_from_source(void* source)
    void* obs_sceneitem_get_scene(void* sceneitem)
    void* obs_sceneitem_get_source(void* sceneitem)
    void obs_scene_enum_items(void* scene, bool (*callback)(void* scene, void* sceneitem, void* data), void* data)

    uint32_t OBS_PROPERTY_GROUP

    void* obs_properties_first(void* props)
    bool obs_property_next(void** p)
    const char *obs_property_name(void* p)
    bool obs_property_enabled(void* p)
    bool obs_property_visible(void* p)
    uint32_t obs_property_get_type(void* p)
    bool obs_property_modified(void* p, void* data)
    void* obs_property_group_content(void* p)

    uint32_t OBS_DATA_NULL, OBS_DATA_STRING, OBS_DATA_NUMBER, OBS_DATA_BOOLEAN
    uint32_t OBS_DATA_OBJECT, OBS_DATA_ARRAY
    uint32_t OBS_DATA_NUM_INVALID, OBS_DATA_NUM_INT, OBS_DATA_NUM_DOUBLE

    void* obs_data_first(void* data)
    void obs_data_release(void* data)

    bool obs_data_item_next(void** d)
    const char *obs_data_item_get_name(void* d)
    uint32_t obs_data_item_gettype(void* d)
    uint32_t obs_data_item_numtype(void* d)
    const char *obs_data_item_get_string(void* d)
    uint64_t obs_data_item_get_int(void* d)
    double obs_data_item_get_double(void* d)
    bint obs_data_item_get_bool(void* d)
    void* obs_data_item_get_obj(void* d)
    void* obs_data_item_get_array(void* d)

    size_t obs_data_array_count(void* array)
    void* obs_data_array_item(void* array, size_t i)
    void obs_data_array_release(void* array)
