typedef void (*OBS_V)();
typedef void* (*OBS_S_TO_P)(const char*);
typedef void (*OBS_P_TO_V)(void*);
typedef void* (*OBS_P_TO_P)(void*);
typedef int (*OBS_P_TO_I)(void*);
typedef void* (*OBS_II_TO_P)(int, int);
typedef void (*OBS_PII_TO_V)(void*, int, int);
typedef int (*OBS_PII_TO_I)(void*, int, int);
typedef void* (*OBS_III_TO_P)(int, int, int);
typedef void (*OBS_PP_TO_V)(void*, void*);
typedef void (*OBS_PPP_TO_V)(void*, void*, void*);
