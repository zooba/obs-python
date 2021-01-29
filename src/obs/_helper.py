import ctypes
import obspython as _obs

_obs_dll = ctypes.CDLL("obs")

PUBYTE = ctypes.POINTER(ctypes.c_ubyte)
PPUBYTE = ctypes.POINTER(PUBYTE)

gs_texrender_create = _obs_dll.gs_texrender_create
gs_texrender_create.argtypes = [ctypes.c_uint, ctypes.c_uint]
gs_texrender_create.restype = ctypes.c_void_p

gs_texrender_reset = _obs_dll.gs_texrender_reset
gs_texrender_reset.argtypes = [ctypes.c_void_p]

gs_texrender_begin = _obs_dll.gs_texrender_begin
gs_texrender_begin.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int]

gs_texrender_end = _obs_dll.gs_texrender_end
gs_texrender_end.argtypes = [ctypes.c_void_p]

gs_texrender_destroy = _obs_dll.gs_texrender_destroy
gs_texrender_destroy.argtypes = [ctypes.c_void_p]

gs_stagesurface_create = _obs_dll.gs_stagesurface_create
gs_stagesurface_create.argtypes = [ctypes.c_uint, ctypes.c_uint, ctypes.c_uint]
gs_stagesurface_create.restype = ctypes.c_void_p

gs_stagesurface_destroy = _obs_dll.gs_stagesurface_destroy
gs_stagesurface_destroy.argtypes = [ctypes.c_void_p]

gs_texrender_get_texture = _obs_dll.gs_texrender_get_texture
gs_texrender_get_texture.argtypes = [ctypes.c_void_p]
gs_texrender_get_texture.restype = ctypes.c_void_p

gs_stage_texture = _obs_dll.gs_stage_texture
gs_stage_texture.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

gs_stagesurface_map = _obs_dll.gs_stagesurface_map
gs_stagesurface_map.argtypes = [ctypes.c_void_p, PPUBYTE, ctypes.c_void_p]
                
gs_stagesurface_unmap = _obs_dll.gs_stagesurface_unmap
gs_stagesurface_unmap.argtypes = [ctypes.c_void_p]


def render_source_to_data(source):
    cx = _obs.obs_source_get_width(source)
    cy = _obs.obs_source_get_height(source)

    texrender = stagesurf = None
    _obs.obs_enter_graphics()
    try:
        texrender = gs_texrender_create(_obs.GS_R8, _obs.GS_ZS_NONE)
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

        texture = gs_texrender_get_texture(texrender)
        stagesurf = gs_stagesurface_create(cx, cy, _obs.GS_R8)
        gs_stage_texture(stagesurf, texture)

        texdata = PUBYTE()
        linesize = ctypes.c_ulong()
        gs_stagesurface_map(stagesurf, ctypes.byref(texdata), ctypes.byref(linesize))

        result = (stagesurf, cx, cy, texdata, linesize.value)
        stagesurf = None
        return result
    finally:
        if stagesurf:
            gs_stagesurface_destroy(stagesurf)
        if texrender:
            gs_texrender_destroy(texrender)
        _obs.obs_leave_graphics()

def rendered_data_to_bytes(data):
    stagesurf, cx, cy, texdata, linesize = data
    img = []
    off = 0
    for _ in range(cy):
        img.append(bytes(i for i in texdata[off:off + cx]))
        off += linesize
    return img

def destroy_rendered_data(data):
    stagesurf, cx, cy, texdata, linesize = data
    _obs.obs_enter_graphics()
    gs_stagesurface_unmap(stagesurf)
    gs_stagesurface_destroy(stagesurf)
    _obs.obs_leave_graphics()