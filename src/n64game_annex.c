#include "n64game_annex.h"

#include <stddef.h>

#define Q8(world_units) ((int32_t)((world_units) * 256))

enum {
    INTERACTION_RADIUS_Q8 = 10 * 256,
};

typedef struct {
    int32_t min_x_q8;
    int32_t max_x_q8;
    int32_t min_z_q8;
    int32_t max_z_q8;
    N64GameAnnexSector sector;
    bool primary_room;
} AnnexRegion;

typedef struct {
    int32_t x_q8;
    int32_t z_q8;
} AnnexPoint;

typedef struct {
    N64GameAnnexInteraction interaction;
    AnnexPoint point;
    const char *label;
} AnnexInteractionDef;

/*
 * Each connector overlaps both rooms that it joins. The deliberate narrow
 * overlaps are the only paths between the four large room rectangles.
 */
static const AnnexRegion ANNEX_REGIONS[] = {
    { Q8(-44), Q8(20), Q8(-40), Q8(24), N64GAME_ANNEX_ATRIUM, true },
    { Q8(-116), Q8(-52), Q8(-40), Q8(24), N64GAME_ANNEX_SIMULATION, true },
    { Q8(-54), Q8(-42), Q8(-20), Q8(20), N64GAME_ANNEX_SIMULATION, false },
    { Q8(28), Q8(92), Q8(-20), Q8(44), N64GAME_ANNEX_WORKSHOP, true },
    { Q8(18), Q8(30), Q8(0), Q8(24), N64GAME_ANNEX_WORKSHOP, false },
    { Q8(84), Q8(148), Q8(36), Q8(100), N64GAME_ANNEX_OVERLOOK, true },
    { Q8(82), Q8(94), Q8(34), Q8(56), N64GAME_ANNEX_OVERLOOK, false },
};

static const AnnexPoint SAFE_ANCHORS[N64GAME_ANNEX_SECTOR_COUNT] = {
    [N64GAME_ANNEX_ATRIUM] = { Q8(-12), Q8(-8) },
    [N64GAME_ANNEX_SIMULATION] = { Q8(-84), Q8(-8) },
    [N64GAME_ANNEX_WORKSHOP] = { Q8(60), Q8(12) },
    [N64GAME_ANNEX_OVERLOOK] = { Q8(116), Q8(68) },
};

static const AnnexInteractionDef INTERACTIONS[] = {
    {
        N64GAME_ANNEX_INTERACTION_SERA,
        { Q8(-32), Q8(4) },
        "TALK TO SERA",
    },
    {
        N64GAME_ANNEX_INTERACTION_FIELD_RELAY,
        { Q8(52), Q8(18) },
        "FIELD RELAY",
    },
    {
        N64GAME_ANNEX_INTERACTION_TAVI,
        { Q8(4), Q8(-22) },
        "TALK TO TAVI",
    },
    {
        N64GAME_ANNEX_INTERACTION_BEACON,
        { Q8(100), Q8(50) },
        "OVERLOOK BEACON",
    },
    {
        N64GAME_ANNEX_INTERACTION_EXAMINE_SIM_RING,
        { Q8(-66), Q8(10) },
        "EXAMINE SIMULATION RING",
    },
    {
        N64GAME_ANNEX_INTERACTION_EXAMINE_ATRIUM_MAP,
        { Q8(0), Q8(24) },
        "EXAMINE ATRIUM MAP",
    },
    {
        N64GAME_ANNEX_INTERACTION_EXAMINE_WORKSHOP_LOG,
        { Q8(58), Q8(-6) },
        "EXAMINE WORKSHOP LOG",
    },
    {
        N64GAME_ANNEX_INTERACTION_EXAMINE_OVERLOOK_SCOPE,
        { Q8(86), Q8(56) },
        "EXAMINE OVERLOOK SCOPE",
    },
};

static size_t region_count(void)
{
    return sizeof(ANNEX_REGIONS) / sizeof(ANNEX_REGIONS[0]);
}

static size_t interaction_count(void)
{
    return sizeof(INTERACTIONS) / sizeof(INTERACTIONS[0]);
}

static bool sector_valid(N64GameAnnexSector sector)
{
    return sector >= N64GAME_ANNEX_ATRIUM &&
        sector < N64GAME_ANNEX_SECTOR_COUNT;
}

static bool point_in_region(const AnnexRegion *region, int32_t x_q8, int32_t z_q8)
{
    return x_q8 >= region->min_x_q8 && x_q8 <= region->max_x_q8 &&
        z_q8 >= region->min_z_q8 && z_q8 <= region->max_z_q8;
}

static bool point_in_sector(
    N64GameAnnexSector sector,
    int32_t x_q8,
    int32_t z_q8
)
{
    for (size_t i = 0U; i < region_count(); ++i) {
        if (ANNEX_REGIONS[i].sector == sector &&
            point_in_region(&ANNEX_REGIONS[i], x_q8, z_q8)) {
            return true;
        }
    }
    return false;
}

bool n64game_annex_position_valid(int32_t x_q8, int32_t z_q8)
{
    for (size_t i = 0U; i < region_count(); ++i) {
        if (point_in_region(&ANNEX_REGIONS[i], x_q8, z_q8)) {
            return true;
        }
    }
    return false;
}

N64GameAnnexSector n64game_annex_sector_for_position(
    int32_t x_q8,
    int32_t z_q8,
    N64GameAnnexSector fallback
)
{
    if (!n64game_annex_position_valid(x_q8, z_q8)) {
        return sector_valid(fallback) ? fallback : N64GAME_ANNEX_ATRIUM;
    }

    /* Keep the previous sector while crossing an intentional overlap. */
    if (sector_valid(fallback) && point_in_sector(fallback, x_q8, z_q8)) {
        return fallback;
    }

    /* A room wins over a connector when no useful previous sector was supplied. */
    for (size_t i = 0U; i < region_count(); ++i) {
        if (ANNEX_REGIONS[i].primary_room &&
            point_in_region(&ANNEX_REGIONS[i], x_q8, z_q8)) {
            return ANNEX_REGIONS[i].sector;
        }
    }
    for (size_t i = 0U; i < region_count(); ++i) {
        if (point_in_region(&ANNEX_REGIONS[i], x_q8, z_q8)) {
            return ANNEX_REGIONS[i].sector;
        }
    }
    return N64GAME_ANNEX_ATRIUM;
}

static void horizontal_component(
    int32_t x_q8,
    int32_t z_q8,
    int32_t *minimum_q8,
    int32_t *maximum_q8
)
{
    int32_t minimum = x_q8;
    int32_t maximum = x_q8;

    /* At most region_count() passes are needed to close a chain of overlaps. */
    for (size_t pass = 0U; pass < region_count(); ++pass) {
        bool expanded = false;
        for (size_t i = 0U; i < region_count(); ++i) {
            const AnnexRegion *const region = &ANNEX_REGIONS[i];
            if (z_q8 < region->min_z_q8 || z_q8 > region->max_z_q8 ||
                region->max_x_q8 < minimum || region->min_x_q8 > maximum) {
                continue;
            }
            if (region->min_x_q8 < minimum) {
                minimum = region->min_x_q8;
                expanded = true;
            }
            if (region->max_x_q8 > maximum) {
                maximum = region->max_x_q8;
                expanded = true;
            }
        }
        if (!expanded) {
            break;
        }
    }

    *minimum_q8 = minimum;
    *maximum_q8 = maximum;
}

static void vertical_component(
    int32_t x_q8,
    int32_t z_q8,
    int32_t *minimum_q8,
    int32_t *maximum_q8
)
{
    int32_t minimum = z_q8;
    int32_t maximum = z_q8;

    for (size_t pass = 0U; pass < region_count(); ++pass) {
        bool expanded = false;
        for (size_t i = 0U; i < region_count(); ++i) {
            const AnnexRegion *const region = &ANNEX_REGIONS[i];
            if (x_q8 < region->min_x_q8 || x_q8 > region->max_x_q8 ||
                region->max_z_q8 < minimum || region->min_z_q8 > maximum) {
                continue;
            }
            if (region->min_z_q8 < minimum) {
                minimum = region->min_z_q8;
                expanded = true;
            }
            if (region->max_z_q8 > maximum) {
                maximum = region->max_z_q8;
                expanded = true;
            }
        }
        if (!expanded) {
            break;
        }
    }

    *minimum_q8 = minimum;
    *maximum_q8 = maximum;
}

static int32_t clamp_sum(int32_t value, int32_t delta, int32_t minimum, int32_t maximum)
{
    const int64_t target = (int64_t)value + (int64_t)delta;
    if (target < (int64_t)minimum) {
        return minimum;
    }
    if (target > (int64_t)maximum) {
        return maximum;
    }
    return (int32_t)target;
}

void n64game_annex_move_swept(
    int32_t *x_q8,
    int32_t *z_q8,
    int32_t dx_q8,
    int32_t dz_q8
)
{
    if (x_q8 == NULL || z_q8 == NULL ||
        !n64game_annex_position_valid(*x_q8, *z_q8)) {
        return;
    }

    int32_t minimum;
    int32_t maximum;
    horizontal_component(*x_q8, *z_q8, &minimum, &maximum);
    *x_q8 = clamp_sum(*x_q8, dx_q8, minimum, maximum);

    vertical_component(*x_q8, *z_q8, &minimum, &maximum);
    *z_q8 = clamp_sum(*z_q8, dz_q8, minimum, maximum);
}

void n64game_annex_safe_anchor(
    N64GameAnnexSector sector,
    int32_t *x_q8,
    int32_t *z_q8
)
{
    if (!sector_valid(sector)) {
        sector = N64GAME_ANNEX_ATRIUM;
    }
    if (x_q8 != NULL) {
        *x_q8 = SAFE_ANCHORS[sector].x_q8;
    }
    if (z_q8 != NULL) {
        *z_q8 = SAFE_ANCHORS[sector].z_q8;
    }
}

N64GameAnnexInteraction n64game_annex_interaction_at(int32_t x_q8, int32_t z_q8)
{
    if (!n64game_annex_position_valid(x_q8, z_q8)) {
        return N64GAME_ANNEX_INTERACTION_NONE;
    }
    const int64_t radius_squared =
        (int64_t)INTERACTION_RADIUS_Q8 * (int64_t)INTERACTION_RADIUS_Q8;
    int64_t best_distance = radius_squared + 1;
    N64GameAnnexInteraction best = N64GAME_ANNEX_INTERACTION_NONE;

    for (size_t i = 0U; i < interaction_count(); ++i) {
        const int64_t dx = (int64_t)x_q8 - (int64_t)INTERACTIONS[i].point.x_q8;
        const int64_t dz = (int64_t)z_q8 - (int64_t)INTERACTIONS[i].point.z_q8;
        const int64_t distance = dx * dx + dz * dz;
        if (distance <= radius_squared && distance < best_distance) {
            best_distance = distance;
            best = INTERACTIONS[i].interaction;
        }
    }
    return best;
}

static const AnnexInteractionDef *interaction_def(N64GameAnnexInteraction interaction)
{
    for (size_t i = 0U; i < interaction_count(); ++i) {
        if (INTERACTIONS[i].interaction == interaction) {
            return &INTERACTIONS[i];
        }
    }
    return NULL;
}

const char *n64game_annex_interaction_label(N64GameAnnexInteraction interaction)
{
    const AnnexInteractionDef *const definition = interaction_def(interaction);
    return definition != NULL ? definition->label : NULL;
}

bool n64game_annex_interaction_point(
    N64GameAnnexInteraction interaction,
    int32_t *x_q8,
    int32_t *z_q8
)
{
    const AnnexInteractionDef *const definition = interaction_def(interaction);
    if (definition == NULL) {
        return false;
    }
    if (x_q8 != NULL) {
        *x_q8 = definition->point.x_q8;
    }
    if (z_q8 != NULL) {
        *z_q8 = definition->point.z_q8;
    }
    return true;
}

#undef Q8
