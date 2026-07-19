#ifndef N64GAME_ANNEX_H
#define N64GAME_ANNEX_H

#include <stdbool.h>
#include <stdint.h>

/*
 * Meridian Annex world positions use signed Q8 coordinates: one world unit is
 * 256 coordinate units. The module is deterministic and owns no heap memory.
 */
typedef enum {
    N64GAME_ANNEX_ATRIUM = 0,
    N64GAME_ANNEX_SIMULATION,
    N64GAME_ANNEX_WORKSHOP,
    N64GAME_ANNEX_OVERLOOK,
    N64GAME_ANNEX_SECTOR_COUNT,
} N64GameAnnexSector;

typedef enum {
    N64GAME_ANNEX_INTERACTION_NONE = 0,
    N64GAME_ANNEX_INTERACTION_SERA,
    N64GAME_ANNEX_INTERACTION_FIELD_RELAY,
    N64GAME_ANNEX_INTERACTION_TAVI,
    N64GAME_ANNEX_INTERACTION_BEACON,
    N64GAME_ANNEX_INTERACTION_EXAMINE_SIM_RING,
    N64GAME_ANNEX_INTERACTION_EXAMINE_ATRIUM_MAP,
    N64GAME_ANNEX_INTERACTION_EXAMINE_WORKSHOP_LOG,
    N64GAME_ANNEX_INTERACTION_EXAMINE_OVERLOOK_SCOPE,
    N64GAME_ANNEX_INTERACTION_COUNT,
} N64GameAnnexInteraction;

bool n64game_annex_position_valid(int32_t x_q8, int32_t z_q8);

N64GameAnnexSector n64game_annex_sector_for_position(
    int32_t x_q8,
    int32_t z_q8,
    N64GameAnnexSector fallback
);

void n64game_annex_move_swept(
    int32_t *x_q8,
    int32_t *z_q8,
    int32_t dx_q8,
    int32_t dz_q8
);

void n64game_annex_safe_anchor(
    N64GameAnnexSector sector,
    int32_t *x_q8,
    int32_t *z_q8
);

N64GameAnnexInteraction n64game_annex_interaction_at(int32_t x_q8, int32_t z_q8);

const char *n64game_annex_interaction_label(N64GameAnnexInteraction interaction);

/* Returns false for NONE or an out-of-range interaction. Output pointers may be NULL. */
bool n64game_annex_interaction_point(
    N64GameAnnexInteraction interaction,
    int32_t *x_q8,
    int32_t *z_q8
);

#endif
