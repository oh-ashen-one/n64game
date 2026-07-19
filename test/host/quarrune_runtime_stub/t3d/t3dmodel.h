#ifndef N64GAME_HOST_STUB_T3DMODEL_H
#define N64GAME_HOST_STUB_T3DMODEL_H

#include <stdint.h>

typedef struct {
    uint32_t texReference;
    const char *texPath;
    uint16_t texWidth;
    uint16_t texHeight;
} T3DMaterialTexture;

typedef struct {
    T3DMaterialTexture textureA;
    T3DMaterialTexture textureB;
} T3DMaterial;

#endif
