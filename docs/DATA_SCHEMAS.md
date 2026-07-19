# Data Schemas

Status: Gate 2 implementation contract. These schemas are original to `n64game`. Numeric values are stable once a public build consumes them; names may gain display strings, but shipped IDs are not recycled.

## 1. Representation rules

All runtime and serialized data follows these rules:

1. C uses `<stdint.h>` types and compile-time assertions that `CHAR_BIT == 8` and that `uint8_t`, `uint16_t`, and `uint32_t` have 1, 2, and 4 bytes.
2. `bool`, enums without an explicit storage type, pointers, `size_t`, compiler bitfields, padding, and native `struct` images never enter EEPROM or generated binary packs.
3. Every serialized multi-byte integer is big-endian and is read/written through bounds-checked `read_be16`, `read_be32`, `write_be16`, and `write_be32`. This is an explicit format choice, not permission to cast bytes to a native N64 struct.
4. Signed serialized values use two's-complement fixed widths and the same byte order.
5. Every reserved byte is written as zero and ignored on decode unless a later schema version defines it.
6. ROM data packs and EEPROM pages carry lengths plus CRCs. Decoders validate the complete envelope before exposing definitions.
7. World positions use signed Q16.16; normalized directions and quaternion components use signed Q1.14; tuning distances/scales normally use unsigned Q8.8. Time in authored timelines is an integer 30 Hz tick.
8. `0` means no ID unless an enum explicitly assigns zero. `0xFFFF` is reserved for invalid/wildcard in transient tools and is never a valid authored definition.

ID aliases are fixed-width:

```c
typedef uint16_t AssetId;
typedef uint16_t AnimationSetId;
typedef uint16_t AudioCueId;
typedef uint16_t AiProfileId;
typedef uint8_t BattleResult;
typedef uint16_t BattleEventId;
typedef uint16_t BundleId;
typedef uint16_t CameraCueId;
typedef uint16_t CharacterId;
typedef uint16_t CheckpointId;
typedef uint16_t ConditionId;
typedef uint16_t CreatureId;
typedef uint16_t CutsceneId;
typedef uint16_t DialogueId;
typedef uint16_t DestinationNodeId;
typedef uint16_t EncounterId;
typedef uint16_t InteractionId;
typedef uint16_t MoveId;
typedef uint16_t NpcOccurrenceId;
typedef uint16_t ObjectiveId;
typedef uint16_t RewardId;
typedef uint8_t SaveReason;
typedef uint16_t SaveableLocationId;
typedef uint16_t SceneId;
typedef uint16_t SpawnId;
typedef uint16_t StoryActionListId;
typedef uint16_t StringId;
typedef uint16_t TeamId;
typedef uint16_t TransitionId;
typedef uint16_t UIScreenId;
typedef uint16_t ZoneId;
```

Generated headers are the only source of numeric IDs. Source JSON/YAML uses symbolic names and checked lockfiles; the generator fails on duplicates, deleted-but-reused values, unresolved references, or out-of-range table counts. `data/ids/serialized_ids.lock` exhaustively mirrors every numeric assignment in every named `*Id` or `*IdValue` enum plus `StoryFlagIndex`, destination/page/reward/encounter-clear bits, and the dialogue/examine/NPC once-bit registries. Spawn and cutscene rows retain their specialized lockfile state. At Gate 2 approval, `scripts/validate-id-locks` takes the immutable reviewed-content commit named by the approval record as the historical root. Every descendant commit edge, the index, and the working tree must preserve that ordered root and may only append a new `(domain,value)` or change an existing same-index row from `LIVE` to `TOMBSTONE`; a tombstone can never become live or be reused.

## 2. Location and scene definitions

### 2.1 Stable scene IDs

```c
typedef enum SceneIdValue {
    SCENE_NONE             = 0,
    SCENE_BOOT             = 1,
    SCENE_TITLE            = 2,
    SCENE_OPENING_SLOT     = 3,
    SCENE_NAME_ENTRY       = 4,
    SCENE_SIM_ARENA        = 5,
    SCENE_ANNEX_INTERIOR   = 6,
    SCENE_WORLD_MAP        = 7,
    SCENE_ESTATE_COURTYARD = 8,
    SCENE_ESTATE_INTERIOR  = 9,
    SCENE_END_CHAPTER      = 10
} SceneIdValue;
```

Large scenes use stable zone IDs while changing independently owned resource bundles:

```c
typedef enum ZoneIdValue {
    ZONE_NONE                      = 0x0000,
    ZONE_SIM_ARENA                 = 0x0001,
    ZONE_ANNEX_SIMULATION_ROOM     = 0x0101,
    ZONE_ANNEX_ATRIUM              = 0x0102,
    ZONE_ANNEX_DIRECTOR_LAB        = 0x0103,
    ZONE_ANNEX_PLAYER_ROOM         = 0x0104,
    ZONE_ANNEX_CLINIC              = 0x0105,
    ZONE_ANNEX_WORKSHOP            = 0x0106,
    ZONE_ANNEX_THRESHOLD           = 0x0107,
    ZONE_WORLD_MAP_DESERT          = 0x0201,
    ZONE_ESTATE_COURTYARD          = 0x0301,
    ZONE_ESTATE_FOYER              = 0x0401,
    ZONE_ESTATE_INVENTION_HALL     = 0x0402,
    ZONE_ESTATE_OBSERVATORY_STUDY  = 0x0403,
    ZONE_END_CARD_UI               = 0x0501
} ZoneIdValue;
```

Checkpoint-critical spawn IDs are locked; the source lockfile assigns every door, elevator, battle-lane, follower-handoff, and recovery anchor without reuse:

```c
typedef enum SpawnIdValue {
    SPAWN_NONE                          = 0x0000,
    SPAWN_SIM_INTRO                     = 0x0101,
    SPAWN_SIM_REVEAL                    = 0x0102,
    SPAWN_ANNEX_SIM_POST_TUTORIAL       = 0x0201,
    SPAWN_ANNEX_SIM_FROM_ATRIUM         = 0x0202,
    SPAWN_ANNEX_ATRIUM_RETURN           = 0x0301,
    SPAWN_ANNEX_ATRIUM_POST_CHAPTER     = 0x0302,
    SPAWN_ANNEX_ATRIUM_FROM_SIM         = 0x0303,
    SPAWN_ANNEX_ATRIUM_FROM_DIRECTOR    = 0x0304,
    SPAWN_ANNEX_ATRIUM_FROM_PLAYER_ROOM = 0x0305,
    SPAWN_ANNEX_ATRIUM_FROM_CLINIC      = 0x0306,
    SPAWN_ANNEX_ATRIUM_FROM_WORKSHOP    = 0x0307,
    SPAWN_ANNEX_ATRIUM_FROM_THRESHOLD   = 0x0308,
    SPAWN_ANNEX_ATRIUM_ELEVATOR_LOWER   = 0x0309,
    SPAWN_ANNEX_ATRIUM_ELEVATOR_UPPER   = 0x030A,
    SPAWN_ANNEX_ATRIUM_TRACE_COMPLETE   = 0x030B,
    SPAWN_ANNEX_WORKSHOP_RELAY          = 0x0401,
    SPAWN_ANNEX_WORKSHOP_FROM_ATRIUM    = 0x0402,
    SPAWN_ANNEX_THRESHOLD_DEPARTURE     = 0x0501,
    SPAWN_ANNEX_THRESHOLD_FROM_ATRIUM   = 0x0502,
    SPAWN_ESTATE_COURTYARD_ARRIVAL      = 0x0601,
    SPAWN_ESTATE_COURTYARD_POST_RUSK    = 0x0602,
    SPAWN_ESTATE_COURTYARD_FROM_MAP     = 0x0603,
    SPAWN_ESTATE_COURTYARD_FROM_FOYER   = 0x0604,
    SPAWN_ESTATE_COURTYARD_BATTLE       = 0x0605,
    SPAWN_ESTATE_STUDY_TAVI_FOUND       = 0x0701,
    SPAWN_ESTATE_STUDY_FROM_HALL        = 0x0702,
    SPAWN_ANNEX_DIRECTOR_FROM_ATRIUM    = 0x0801,
    SPAWN_ANNEX_PLAYER_ROOM_FROM_ATRIUM = 0x0901,
    SPAWN_ANNEX_CLINIC_FROM_ATRIUM      = 0x0A01,
    SPAWN_WORLD_MAP_ANNEX_NODE          = 0x0B01,
    SPAWN_WORLD_MAP_ESTATE_NODE         = 0x0B02,
    SPAWN_ESTATE_FOYER_FROM_COURTYARD   = 0x0C01,
    SPAWN_ESTATE_FOYER_FROM_HALL        = 0x0C02,
    SPAWN_ESTATE_HALL_FROM_FOYER        = 0x0D01,
    SPAWN_ESTATE_HALL_FROM_STUDY        = 0x0D02
} SpawnIdValue;
```

The generator writes every other assignment to `data/ids/spawn_ids.lock`; deletion tombstones the value permanently. A saved `(scene, zone, spawn)` must resolve by exact equality to one condition-valid `SaveableLocationDef`; transition membership is irrelevant. Otherwise loading tries the separately validated saved last-safe tuple, then the new-game path. `ZONE_END_CARD_UI` is marked `NON_SAVEABLE_UI`, owns no spawn/collision/nav data, and is never legal in `LocationKey` or the saveable-location registry.

Logical in-memory definition (20 bytes, not serialized by casting):

```c
typedef struct SceneDef {
    SceneId scene_id;                 /* 0 */
    ZoneId default_zone_id;           /* 2 */
    BundleId shell_bundle_id;         /* 4 */
    AssetId loading_card_asset_id;    /* 6 */
    AudioCueId music_cue_id;          /* 8 */
    uint16_t flags;                   /* 10 */
    ConditionId entry_condition_id;   /* 12 */
    CutsceneId entry_cutscene_id;     /* 14 */
    uint16_t arena_cap_kib;           /* 16 */
    uint16_t reserved;                /* 18 */
} SceneDef;
_Static_assert(sizeof(SceneDef) == 20, "SceneDef layout");

enum SceneFlags {
    SCENE_ALLOW_SAVE          = 1u << 0,
    SCENE_ALLOW_PAUSE         = 1u << 1,
    SCENE_IS_BATTLE           = 1u << 2,
    SCENE_IS_LOADING_SHELL    = 1u << 3,
    SCENE_PERSIST_FOLLOWER    = 1u << 4,
    SCENE_NO_PLAYER_CONTROL   = 1u << 5,
    SCENE_NON_SAVEABLE_UI     = 1u << 6
};

typedef enum SceneShellBundleIdValue {
    BUNDLE_SCENE_BOOT_SHELL = 0x6801,
    BUNDLE_SCENE_TITLE_SHELL = 0x6802,
    BUNDLE_SCENE_OPENING_SHELL = 0x6803,
    BUNDLE_SCENE_NAME_SHELL = 0x6804,
    BUNDLE_SCENE_SIM_SHELL = 0x6805,
    BUNDLE_SCENE_ANNEX_SHELL = 0x6806,
    BUNDLE_SCENE_MAP_SHELL = 0x6807,
    BUNDLE_SCENE_ESTATE_COURTYARD_SHELL = 0x6808,
    BUNDLE_SCENE_ESTATE_INTERIOR_SHELL = 0x6809,
    BUNDLE_SCENE_END_CHAPTER_SHELL = 0x680A,
    BUNDLE_UI_SHARED = 0x680B,
    BUNDLE_SIM_TUTORIAL_ARENA = 0x6810,
    BUNDLE_RUSK_BATTLE_ACTION = 0x6811
} SceneShellBundleIdValue;

typedef enum SceneMusicCueIdValue {
    MUSIC_CUE_TITLE = 0x6901,
    MUSIC_CUE_SIMULATION = 0x6902,
    MUSIC_CUE_ANNEX = 0x6903,
    MUSIC_CUE_WORLD_MAP = 0x6904,
    MUSIC_CUE_ESTATE_EXPLORATION = 0x6905,
    MUSIC_CUE_ESTATE_BATTLE = 0x6906,
    MUSIC_CUE_VICTORY_RETURN = 0x6907,
    MUSIC_CUE_CHAPTER_END = 0x6908
} SceneMusicCueIdValue;

typedef enum OpeningPresentationAudioCueIdValue {
    AUDIO_CUE_STORY_SLATE_IN = 0x6A01,
    AUDIO_CUE_STORY_SLATE_SKIP = 0x6A02
} OpeningPresentationAudioCueIdValue;
```

The ten logical audio IDs above map one-to-one to production inventory assets;
the asset name is provenance/input identity, while `AudioCueId` is the only
runtime reference:

| AudioCueId | Inventory asset ID | Required owner/use |
|---|---|---|
| `MUSIC_CUE_TITLE` | `mus.title_loading` | Title, loading motif, and Name Entry |
| `MUSIC_CUE_SIMULATION` | `mus.simulation_battle` | Simulation encounter override |
| `MUSIC_CUE_ANNEX` | `mus.annex_exploration` | Annex scene exploration default |
| `MUSIC_CUE_WORLD_MAP` | `mus.world_travel` | Ordinary world-route presentation |
| `MUSIC_CUE_ESTATE_EXPLORATION` | `mus.estate_exploration` | Estate courtyard/interior scene default |
| `MUSIC_CUE_ESTATE_BATTLE` | `mus.estate_battle` | Rusk encounter override only |
| `MUSIC_CUE_VICTORY_RETURN` | `mus.victory_return` | Rusk victory and companion-return variants |
| `MUSIC_CUE_CHAPTER_END` | `mus.closing_fracture` | Hook/Fracture sequence, final save, and end card |
| `AUDIO_CUE_STORY_SLATE_IN` | `sfx.story.slate_in` | Opening timeline natural-entry event |
| `AUDIO_CUE_STORY_SLATE_SKIP` | `sfx.story.slate_skip` | Opening skip finalizer only |

Generation requires this exact bijection: all eight `mus.*` inventory rows and
the two named `sfx.story` children resolve exactly once, no logical cue maps to
two assets, and no listed production cue is orphaned.

The generated scene table contains exactly these ten nonzero rows. A zero bundle/card/music/cutscene is literal `0`; caps are KiB. `CUTSCENE_OPENING_SOLACE=1` is locked in section 4. References to presentation AssetIds resolve through the manifest registry in section 12.

| SceneId | Default ZoneId | Shell BundleId | Loading-card AssetId | Music AudioCueId | Entry condition / cutscene | Exact flags | Cap |
|---|---|---|---|---|---|---|---:|
| `SCENE_BOOT` | `ZONE_NONE` | `BUNDLE_SCENE_BOOT_SHELL` | `ASSET_UI_SCREEN_STUDIO_MARK` | `0` | `0 / 0` | `SCENE_IS_LOADING_SHELL + SCENE_NO_PLAYER_CONTROL` | 48 |
| `SCENE_TITLE` | `ZONE_NONE` | `BUNDLE_SCENE_TITLE_SHELL` | `ASSET_UI_SCREEN_TITLE_MARK` | `MUSIC_CUE_TITLE` | `0 / 0` | `SCENE_NO_PLAYER_CONTROL` | 48 |
| `SCENE_OPENING_SLOT` | `ZONE_NONE` | `BUNDLE_SCENE_OPENING_SHELL` | `ASSET_UI_SCREEN_CUTSCENE_SLATE` | `MUSIC_CUE_TITLE` | `0 / CUTSCENE_OPENING_SOLACE` | `SCENE_NO_PLAYER_CONTROL` | 48 |
| `SCENE_NAME_ENTRY` | `ZONE_NONE` | `BUNDLE_SCENE_NAME_SHELL` | `ASSET_UI_SCREEN_NAME_ENTRY` | `MUSIC_CUE_TITLE` | `0 / 0` | `SCENE_NO_PLAYER_CONTROL` | 48 |
| `SCENE_SIM_ARENA` | `ZONE_SIM_ARENA` | `BUNDLE_SCENE_SIM_SHELL` | `ASSET_UI_SCREEN_LOADING` | `MUSIC_CUE_SIMULATION` | `0 / 0` | `SCENE_ALLOW_PAUSE + SCENE_IS_BATTLE` | 1040 |
| `SCENE_ANNEX_INTERIOR` | `ZONE_ANNEX_SIMULATION_ROOM` | `BUNDLE_SCENE_ANNEX_SHELL` | `ASSET_UI_SCREEN_LOADING` | `MUSIC_CUE_ANNEX` | `0 / 0` | `SCENE_ALLOW_SAVE + SCENE_ALLOW_PAUSE + SCENE_PERSIST_FOLLOWER` | 1100 |
| `SCENE_WORLD_MAP` | `ZONE_WORLD_MAP_DESERT` | `BUNDLE_SCENE_MAP_SHELL` | `ASSET_UI_SCREEN_LOADING` | `MUSIC_CUE_WORLD_MAP` | `0 / 0` | `SCENE_PERSIST_FOLLOWER + SCENE_NO_PLAYER_CONTROL` | 600 |
| `SCENE_ESTATE_COURTYARD` | `ZONE_ESTATE_COURTYARD` | `BUNDLE_SCENE_ESTATE_COURTYARD_SHELL` | `ASSET_UI_SCREEN_LOADING` | `MUSIC_CUE_ESTATE_EXPLORATION` | `0 / 0` | `SCENE_ALLOW_SAVE + SCENE_ALLOW_PAUSE + SCENE_PERSIST_FOLLOWER` | 1040 |
| `SCENE_ESTATE_INTERIOR` | `ZONE_ESTATE_FOYER` | `BUNDLE_SCENE_ESTATE_INTERIOR_SHELL` | `ASSET_UI_SCREEN_LOADING` | `MUSIC_CUE_ESTATE_EXPLORATION` | `0 / 0` | `SCENE_ALLOW_SAVE + SCENE_ALLOW_PAUSE + SCENE_PERSIST_FOLLOWER` | 1000 |
| `SCENE_END_CHAPTER` | `ZONE_END_CARD_UI` | `BUNDLE_SCENE_END_CHAPTER_SHELL` | `ASSET_UI_SCREEN_CHAPTER_END` | `MUSIC_CUE_CHAPTER_END` | `0 / 0` | `SCENE_NO_PLAYER_CONTROL + SCENE_NON_SAVEABLE_UI` | 48 |

`SceneDef.flags` accepts only mask `0x007F`; unknown bits fail generation. `SCENE_NON_SAVEABLE_UI` requires `SCENE_ALLOW_SAVE` clear, `ZONE_END_CARD_UI`, and a zone binding with zero spawn/collision/nav/interaction IDs. Title settings change only the process-resident profile and never enter the settings/save dispatcher or make Title a gameplay-save scene. Simulation likewise clears `SCENE_ALLOW_SAVE`: its After-Name page is created only by the Name-to-Sim transition recipe, and Pause settings may use the separate settings dispatcher, but Relay/manual save and every battle-state save request are rejected while the simulation owner is live. Every nonzero `entry_cutscene_id`, bundle, asset, music cue, condition, and zone must resolve; duplicate/missing SceneIds, any eleventh row, a nonzero reserved field, or a row cap below its legal zone composite fails generation.

Zone binding is explicit and does not rely on a filename alias:

```c
typedef struct ZoneBindingDef {
    ZoneId zone_id;                    /* 0 */
    SceneId scene_id;                  /* 2 */
    BundleId required_bundle_id;       /* 4 */
    BundleId optional_bundle_id;       /* 6 */
    BundleId action_bundle_a_id;       /* 8 */
    BundleId action_bundle_b_id;       /* 10; mutually exclusive */
    AssetId collision_asset_id;        /* 12 */
    AssetId nav_asset_id;              /* 14 */
    AssetId spawn_table_asset_id;      /* 16 */
    AssetId interaction_asset_id;      /* 18 */
    SpawnId default_spawn_id;          /* 20 */
    SpawnId safe_anchor_spawn_id;      /* 22 */
    uint16_t arena_cap_kib;            /* 24 */
    uint16_t flags;                    /* 26 */
    uint16_t reserved;                 /* 28 */
} ZoneBindingDef;
_Static_assert(sizeof(ZoneBindingDef) == 30, "ZoneBindingDef layout");

enum ZoneBindingFlags {
    ZONE_BIND_OPTIONAL_CAPABLE = 1u << 0,
    ZONE_BIND_ACTION_A_CAPABLE = 1u << 1,
    ZONE_BIND_ACTION_B_CAPABLE = 1u << 2,
    ZONE_BIND_FOLLOWER_NAV = 1u << 3,
    ZONE_BIND_NON_SAVEABLE_UI = 1u << 4
};
```

`ZoneBindingDef.flags` accepts only mask `0x001F` and is derived, not hand-authored: each of bits 0-2 equals whether its corresponding optional/action bundle ID is nonzero; bit 3 is set exactly for bindings whose nav pack contains follower nodes; bit 4 is set only for `ZONE_END_CARD_UI`. All other bits and `reserved` must be zero. A mismatch fails generation.

The generated IDs resolve the following locked symbolic map. The `Authored source(s)` column is provenance/report text only; it never occupies an `AssetId` field. The required bundle's flattened AssetId reference list is the authoritative environment content. A dash compiles to zero; `action A/B` are never resident together.

| Zone | Scene | Authored source(s), not runtime IDs | Required / optional | Action A / B | Collision | Nav / spawn / interaction | Safe/default spawn | Cap |
|---|---|---|---|---|---|---|---|---:|
| `ZONE_SIM_ARENA` | `SCENE_SIM_ARENA` | `env.annex.sim_chamber` | `bnd.annex.sim_room.base` / — | `bnd.sim.tutorial_overlay` / — | `COL_ANNEX_SIM_ROOM` | `nav.sim.arena` / `spn.sim.arena` / `int.sim.arena` | `SPAWN_SIM_INTRO` | 1040 KiB |
| `ZONE_ANNEX_SIMULATION_ROOM` | `SCENE_ANNEX_INTERIOR` | same physical chamber | `bnd.annex.sim_room.base` / `bnd.annex.sim_room.optional` | `bnd.annex.sim_room.onboarding` / — | same `COL_ANNEX_SIM_ROOM` | `nav.annex.sim_room` / `spn.annex.sim_room` / `int.annex.sim_room` | `SPAWN_ANNEX_SIM_POST_TUTORIAL` | 900 KiB |
| `ZONE_ANNEX_ATRIUM` | `SCENE_ANNEX_INTERIOR` | `env.annex.atrium_lower`, `env.annex.atrium_upper`, `env.annex.elevator`, `env.annex.circulation` | `bnd.annex.atrium.required` / `bnd.annex.atrium.optional` | `bnd.annex.atrium.story` / `bnd.annex.atrium.hook` | `COL_ANNEX_ATRIUM` | `nav.annex.atrium` / `spn.annex.atrium` / `int.annex.atrium` | `SPAWN_ANNEX_ATRIUM_RETURN` | 1000 KiB |
| `ZONE_ANNEX_DIRECTOR_LAB` | `SCENE_ANNEX_INTERIOR` | `env.annex.director_lab` | `bnd.annex.director.required` / `bnd.annex.director.optional` | `bnd.annex.director.story` / — | `COL_ANNEX_DIRECTOR` | `nav.annex.director_lab` / `spn.annex.director_lab` / `int.annex.director_lab` | generated safe | 800 KiB |
| `ZONE_ANNEX_PLAYER_ROOM` | `SCENE_ANNEX_INTERIOR` | `env.annex.player_room` | `bnd.annex.player_room.required` / `bnd.annex.player_room.optional` | — / — | `COL_ANNEX_PLAYER_ROOM` | `nav.annex.player_room` / `spn.annex.player_room` / `int.annex.player_room` | generated safe | 700 KiB |
| `ZONE_ANNEX_CLINIC` | `SCENE_ANNEX_INTERIOR` | `env.annex.clinic_bay` | `bnd.annex.clinic.required` / `bnd.annex.clinic.optional` | `bnd.annex.clinic.onboarding` / — | `COL_ANNEX_CLINIC` | `nav.annex.clinic` / `spn.annex.clinic` / `int.annex.clinic` | generated safe | 900 KiB |
| `ZONE_ANNEX_WORKSHOP` | `SCENE_ANNEX_INTERIOR` | `env.annex.workshop` | `bnd.annex.workshop.required` / `bnd.annex.workshop.optional` | `bnd.annex.workshop.relay` / — | `COL_ANNEX_WORKSHOP` | `nav.annex.workshop` / `spn.annex.workshop` / `int.annex.workshop` | `SPAWN_ANNEX_WORKSHOP_RELAY` | 900 KiB |
| `ZONE_ANNEX_THRESHOLD` | `SCENE_ANNEX_INTERIOR` | `env.annex.threshold` | `bnd.annex.threshold.required` / `bnd.annex.threshold.optional` | `bnd.annex.threshold.map_exit` / — | `COL_ANNEX_THRESHOLD` | `nav.annex.threshold` / `spn.annex.threshold` / `int.annex.threshold` | `SPAWN_ANNEX_THRESHOLD_DEPARTURE` | 850 KiB |
| `ZONE_WORLD_MAP_DESERT` | `SCENE_WORLD_MAP` | `env.world_map.desert_relief` | `bnd.map.required` / — | `bnd.map.travel` / — | `COL_WORLD_MAP_NODES` | `nav.world_map.desert` / `spn.world_map.desert` / `int.world_map.desert` | generated Annex node | 600 KiB |
| `ZONE_ESTATE_COURTYARD` | `SCENE_ESTATE_COURTYARD` | `env.estate.courtyard` | `bnd.estate.courtyard.required` / `bnd.estate.courtyard.optional` | `bnd.estate.courtyard.battle` / `bnd.estate.courtyard.story` | `COL_ESTATE_COURTYARD` (+ action-only battle collision) | `nav.estate.courtyard` / `spn.estate.courtyard` / `int.estate.courtyard` | `SPAWN_ESTATE_COURTYARD_ARRIVAL` | 1040 KiB |
| `ZONE_ESTATE_FOYER` | `SCENE_ESTATE_INTERIOR` | `env.estate.foyer_gallery`, `env.estate.circulation` | `bnd.estate.foyer.required` / `bnd.estate.foyer.optional` | `bnd.estate.foyer.entry` / — | `COL_ESTATE_FOYER` | `nav.estate.foyer` / `spn.estate.foyer` / `int.estate.foyer` | generated safe | 750 KiB |
| `ZONE_ESTATE_INVENTION_HALL` | `SCENE_ESTATE_INTERIOR` | `env.estate.invention_hall`, `env.estate.circulation` | `bnd.estate.hall.required` / `bnd.estate.hall.optional` | `bnd.estate.hall.examine` / — | `COL_ESTATE_HALL` | `nav.estate.invention_hall` / `spn.estate.invention_hall` / `int.estate.invention_hall` | generated safe | 950 KiB |
| `ZONE_ESTATE_OBSERVATORY_STUDY` | `SCENE_ESTATE_INTERIOR` | `env.estate.observatory_study`, `env.estate.circulation` | `bnd.estate.study.required` / `bnd.estate.study.optional` | `bnd.estate.study.reunion` / — | `COL_ESTATE_STUDY` | `nav.estate.observatory_study` / `spn.estate.observatory_study` / `int.estate.observatory_study` | `SPAWN_ESTATE_STUDY_TAVI_FOUND` | 900 KiB |
| `ZONE_END_CARD_UI` | `SCENE_END_CHAPTER` | — | `bnd.ui.chapter_end` / — | — / — | — | — / — / — | none; non-saveable | 48 KiB |

`ZONE_SIM_ARENA` and `ZONE_ANNEX_SIMULATION_ROOM` may use the retain transition only when their generated required-bundle AssetId/CRC/unpacked-size lists match exactly. After the action fence, the registry atomically retags that scope to the destination generation, invalidates all overlay handles, and asserts no other source-scene resource remains.

### 2.2 Destination, navigation, spawn, and interaction records

```c
typedef enum DestinationNodeIdValue {
    DEST_NODE_NONE = 0,
    DEST_NODE_MERIDIAN_ANNEX = 1,
    DEST_NODE_VEYRA_ESTATE = 2
} DestinationNodeIdValue;

typedef struct DestinationNodeDef {
    DestinationNodeId id;       /* 0 */
    StringId name_string_id;    /* 2 */
    SceneId scene_id;           /* 4 */
    ZoneId zone_id;             /* 6 */
    SpawnId spawn_id;           /* 8 */
    AssetId icon_asset_id;      /* 10 */
    int32_t map_x_q16;          /* 12 */
    int32_t map_y_q16;          /* 16 */
    ConditionId unlock_condition_id; /* 20 */
    uint16_t flags;             /* 22 */
} DestinationNodeDef;
_Static_assert(sizeof(DestinationNodeDef) == 24, "DestinationNodeDef layout");

typedef struct DestinationEdgeDef {
    DestinationNodeId from_id;  /* 0 */
    DestinationNodeId to_id;    /* 2 */
    ConditionId condition_id;   /* 4 */
    AssetId route_asset_id;     /* 6 */
    uint16_t travel_ticks;      /* 8 */
    uint16_t flags;             /* 10 */
} DestinationEdgeDef;
_Static_assert(sizeof(DestinationEdgeDef) == 12, "DestinationEdgeDef layout");

enum DestinationNodeFlags {
    DEST_NODE_DEFAULT_HOME = 1u << 0,
    DEST_NODE_SELECTABLE = 1u << 1
};

enum DestinationEdgeFlags {
    DEST_EDGE_DIRECTED = 1u << 0,
    DEST_EDGE_PLAY_ROUTE = 1u << 1
};

typedef enum DestinationRuntimeStringIdValue {
    STR_DEST_MERIDIAN_ANNEX = 0x6B01,
    STR_DEST_VEYRA_ESTATE = 0x6B02
} DestinationRuntimeStringIdValue;

typedef struct MapNodePresentationDef {
    DestinationNodeId node_id;      /* 0 */
    DialogueId name_dialogue_id;    /* 2: ROOT_UI row */
    DialogueId description_dialogue_id; /* 4: ROOT_UI row */
    uint16_t flags;                 /* 6: reserved, currently zero */
} MapNodePresentationDef;
_Static_assert(sizeof(MapNodePresentationDef) == 8, "MapNodePresentationDef layout");

enum MapConfirmRouteFlags {
    MAP_CONFIRM_DEBOUNCE_ACCEPT = 1u << 0,
    MAP_CONFIRM_RESERVE_TRANSITION_BEFORE_CLOSE = 1u << 1,
    MAP_CONFIRM_BACK_NO_PROGRESS = 1u << 2,
    MAP_CONFIRM_REQUIRE_VISIBLE_SELECTED_NODE = 1u << 3,
    MAP_CONFIRM_REQUIRE_STABLE_MAP_CONTROL = 1u << 4
};

typedef struct MapConfirmRouteDef {
    DestinationNodeId selected_node_id; /* 0 */
    ConditionId condition_id;           /* 2 */
    TransitionId transition_id;         /* 4 */
    DialogueId prompt_dialogue_id;      /* 6: literal CHOICE root */
    DialogueId confirm_dialogue_id;     /* 8: its option A */
    DialogueId back_dialogue_id;        /* 10: its option B */
    uint16_t flags;                     /* 12 */
    uint16_t reserved;                  /* 14 */
} MapConfirmRouteDef;
_Static_assert(sizeof(MapConfirmRouteDef) == 16, "MapConfirmRouteDef layout");

typedef enum MapOriginKindValue {
    MAP_ORIGIN_NONE = 0,
    MAP_ORIGIN_ANNEX_THRESHOLD = 1,
    MAP_ORIGIN_ESTATE_COURTYARD = 2
} MapOriginKindValue;

enum MapOriginSnapshotFlags {
    MAP_ORIGIN_GENERATION_BOUND = 1u << 0,
    MAP_ORIGIN_SOURCE_COMMIT_VERIFIED = 1u << 1,
    MAP_ORIGIN_CANCEL_AVAILABLE = 1u << 2
};

typedef struct MapOriginSnapshot {
    uint32_t runtime_generation;        /* 0 */
    uint32_t map_generation;            /* 4 */
    TransitionId entered_by_transition; /* 8 */
    uint8_t origin_kind;                /* 10: MapOriginKindValue */
    uint8_t follower_state;             /* 11: ReturnFollowerStateValue */
    uint16_t flags;                     /* 12 */
    uint16_t reserved;                  /* 14: zero */
} MapOriginSnapshot;
_Static_assert(sizeof(MapOriginSnapshot) == 16, "MapOriginSnapshot layout");

enum MapCancelRouteFlags {
    MAP_CANCEL_REQUIRE_STABLE_MAP_CONTROL = 1u << 0,
    MAP_CANCEL_REQUIRE_CURRENT_ORIGIN_GENERATION = 1u << 1,
    MAP_CANCEL_PRESERVE_PROGRESS = 1u << 2,
    MAP_CANCEL_REQUIRE_SAVE_NONE = 1u << 3,
    MAP_CANCEL_FOLLOWER_HANDOFF = 1u << 4
};

typedef struct MapCancelRouteDef {
    uint8_t origin_kind;          /* 0: MapOriginKindValue */
    uint8_t follower_state;       /* 1: ReturnFollowerStateValue */
    TransitionId transition_id;   /* 2 */
    SceneId destination_scene_id; /* 4: equality xref */
    ZoneId destination_zone_id;   /* 6: equality xref */
    SpawnId destination_spawn_id; /* 8: equality xref */
    uint16_t flags;               /* 10 */
} MapCancelRouteDef;
_Static_assert(sizeof(MapCancelRouteDef) == 12, "MapCancelRouteDef layout");

typedef enum DestinationRuntimeAssetIdValue {
    ASSET_MAP_ICON_MERIDIAN_ANNEX = 0x6B11,
    ASSET_MAP_ICON_VEYRA_ESTATE = 0x6B12
} DestinationRuntimeAssetIdValue;

typedef enum DestinationConditionIdValue {
    COND_DEST_ANNEX_AVAILABLE = 0x6101,
    COND_DEST_ESTATE_UNLOCKED = 0x6102,
    COND_DEST_ESTATE_ARRIVED = 0x6103
} DestinationConditionIdValue;

typedef enum TransitionInteractionIdValue {
    INT_SIM_EXIT                   = 0x2001,
    INT_ATRIUM_SIM_DOOR            = 0x2002,
    INT_ATRIUM_DIRECTOR_DOOR       = 0x2003,
    INT_DIRECTOR_EXIT              = 0x2004,
    INT_ATRIUM_PLAYER_DOOR         = 0x2005,
    INT_PLAYER_EXIT                = 0x2006,
    INT_ATRIUM_CLINIC_DOOR         = 0x2007,
    INT_CLINIC_EXIT                = 0x2008,
    INT_ATRIUM_WORKSHOP_DOOR       = 0x2009,
    INT_WORKSHOP_EXIT              = 0x200A,
    INT_ATRIUM_THRESHOLD_DOOR      = 0x200B,
    INT_THRESHOLD_INNER_DOOR       = 0x200C,
    INT_ELEVATOR_UP                = 0x200D,
    INT_ELEVATOR_DOWN              = 0x200E,
    INT_SKIMMER_MAP                = 0x200F,
    INT_ESTATE_SKIMMER             = 0x2010,
    INT_ESTATE_MAIN_DOOR           = 0x2011,
    INT_FOYER_EXIT                 = 0x2012,
    INT_FOYER_HALL_DOOR            = 0x2013,
    INT_HALL_FOYER_DOOR            = 0x2014,
    INT_HALL_STUDY_DOOR            = 0x2015,
    INT_STUDY_EXIT                 = 0x2016,
    INT_ORRERY_SWITCH              = 0x2017,
    INT_ORRERY_ARM_EXAMINE         = 0x2018,
    INT_RUSK_CONFRONTATION_VOLUME  = 0x2019,
    INT_NPC_OREN                   = 0x201A,
    INT_NPC_JO                     = 0x201B,
    INT_NPC_PELL                   = 0x201C,
    INT_ANNEX_RETURN_RESOLUTION_VOLUME = 0x201D,
    INT_NPC_TAVI_FOLLOW            = 0x201E,
    INT_NPC_SERA_POST              = 0x201F,
    INT_NPC_TAVI_POST              = 0x2020,
    INT_NPC_RUSK_POST              = 0x2021,
    INT_NPC_IVO_POST               = 0x2022
} TransitionInteractionIdValue;

typedef struct NavGraphDef {
    AssetId asset_id;           /* 0 */
    ZoneId zone_id;             /* 2 */
    uint16_t first_node;        /* 4 */
    uint16_t node_count;        /* 6 */
    uint16_t first_edge;        /* 8 */
    uint16_t edge_count;        /* 10 */
    uint16_t max_path_nodes;    /* 12 */
    uint16_t flags;             /* 14 */
} NavGraphDef;
_Static_assert(sizeof(NavGraphDef) == 16, "NavGraphDef layout");

enum NavGraphFlags {
    NAV_GRAPH_HAS_FOLLOWER = 1u << 0,
    NAV_GRAPH_HAS_HANDOFF = 1u << 1,
    NAV_GRAPH_HAS_RECOVERY = 1u << 2
};

typedef struct NavNodeDef {
    uint16_t id;                /* 0: local, nonzero */
    uint16_t flags;             /* 2: walk, follower, handoff, recovery */
    int32_t x_q16;              /* 4 */
    int32_t y_q16;              /* 8 */
    int32_t z_q16;              /* 12 */
    uint16_t radius_q8;         /* 16 */
    uint16_t clearance_q8;      /* 18 */
} NavNodeDef;
_Static_assert(sizeof(NavNodeDef) == 20, "NavNodeDef layout");

enum NavNodeFlags {
    NAV_NODE_WALKABLE = 1u << 0,
    NAV_NODE_FOLLOWER_ALLOWED = 1u << 1,
    NAV_NODE_FOLLOWER_HANDOFF = 1u << 2,
    NAV_NODE_RECOVERY = 1u << 3
};

typedef struct NavEdgeDef {
    uint16_t from_node;         /* 0 */
    uint16_t to_node;           /* 2 */
    uint16_t cost_q8;           /* 4 */
    ConditionId condition_id;   /* 6 */
    uint16_t flags;             /* 8: directed, door, follower handoff */
    uint16_t reserved;          /* 10 */
} NavEdgeDef;
_Static_assert(sizeof(NavEdgeDef) == 12, "NavEdgeDef layout");

enum NavEdgeFlags {
    NAV_EDGE_DIRECTED = 1u << 0,
    NAV_EDGE_DOOR = 1u << 1,
    NAV_EDGE_FOLLOWER_HANDOFF = 1u << 2
};

typedef struct SpawnDef {
    SpawnId id;                 /* 0 */
    ZoneId zone_id;             /* 2 */
    int32_t x_q16;              /* 4 */
    int32_t y_q16;              /* 8 */
    int32_t z_q16;              /* 12 */
    int16_t yaw_q14;            /* 16 */
    uint16_t clearance_q8;      /* 18 */
    ConditionId condition_id;   /* 20 */
    uint16_t flags;             /* 22: entry, safe, battle, handoff */
} SpawnDef;
_Static_assert(sizeof(SpawnDef) == 24, "SpawnDef layout");

enum SpawnFlags {
    SPAWN_ENTRY = 1u << 0,
    SPAWN_SAFE = 1u << 1,
    SPAWN_BATTLE = 1u << 2,
    SPAWN_FOLLOWER_HANDOFF = 1u << 3
};

enum InteractionFlags {
    INTERACTION_VARIANT_DRIVEN = 1u << 0,
    INTERACTION_MANDATORY = 1u << 1,
    INTERACTION_REPEATABLE = 1u << 2,
    INTERACTION_SAVED_ONCE_EXAMINE = 1u << 3,
    INTERACTION_ACTOR_ATTACHED = 1u << 4
};

typedef struct InteractionDef {
    InteractionId id;               /* 0 */
    ZoneId zone_id;                 /* 2 */
    AssetId anchor_asset_id;        /* 4: marker/socket, not code */
    StringId prompt_string_id;      /* 6 */
    ConditionId condition_id;       /* 8 */
    StoryActionListId action_xref;  /* 10: equality-only owner mirror */
    uint16_t proximity_radius_q8;   /* 12 */
    int16_t min_facing_dot_q14;     /* 14 */
    int16_t selection_priority;     /* 16 */
    uint16_t flags;                 /* 18 */
    uint16_t prompt_offset_q8;      /* 20 */
    uint16_t reserved;              /* 22 */
} InteractionDef;
_Static_assert(sizeof(InteractionDef) == 24, "InteractionDef layout");

enum OrreryHeldInteractionIdValue {
    STR_PROMPT_HOLD_ORRERY_SWITCH = 0x5101,
    STR_PROMPT_EXAMINE_OPEN_SWITCH = 0x5102,
    STR_PROMPT_EXAMINE_ORRERY_ARM = 0x5103,
    ACTION_ORRERY_COHERENT_OPEN_COMMIT = 0x4102,
    ANIM_CUE_ORRERY_SWITCH_PRESS = 0x3101,
    ANIM_CUE_ORRERY_SWITCH_HELD = 0x3102,
    ANIM_CUE_ORRERY_INTERRUPTED_RESET = 0x3103
};

typedef enum HeldInteractionCallbackIdValue {
    HELD_CALLBACK_NONE = 0,
    HELD_CALLBACK_ORRERY_BEGIN = 0x6101,
    HELD_CALLBACK_ORRERY_CANCEL_RESET = 0x6102
} HeldInteractionCallbackIdValue;

typedef enum OrreryInteractionConditionIdValue {
    COND_INTERACT_ORRERY_CLOSED = 0x6501,
    COND_INTERACT_ORRERY_OPEN = 0x6502
} OrreryInteractionConditionIdValue;

typedef enum OrreryDialogueIdValue {
    ESTATE_EX_ORRERY = 0x5201,
    ESTATE_EX_SWITCH_OPEN = 0x5202,
    ESTATE_EX_ORRERY_OPEN = 0x5203
} OrreryDialogueIdValue;

enum HeldInteractionFlags {
    HELD_CANCEL_ON_RELEASE = 1u << 0,
    HELD_CANCEL_ON_DISCONNECT = 1u << 1,
    HELD_CANCEL_ON_RANGE_EXIT = 1u << 2,
    HELD_CANCEL_ON_EXTERNAL_INTERRUPT = 1u << 3,
    HELD_BLOCK_SAVE_WHILE_ACTIVE = 1u << 4,
    HELD_REQUIRE_COHERENT_WORLD_COMMIT = 1u << 5,
    HELD_MONOTONIC_ONCE = 1u << 6
};

typedef struct HeldInteractionDef {
    InteractionId interaction_id;                /* 0 */
    uint16_t required_ticks;                      /* 2: fixed 30 Hz ticks */
    StringId hold_prompt_string_id;               /* 4 */
    uint16_t begin_callback_id;                   /* 6: HeldInteractionCallbackId */
    uint16_t cancel_callback_id;                  /* 8: HeldInteractionCallbackId */
    StoryActionListId coherent_commit_action_xref;/* 10: equality-only */
    uint16_t press_animation_cue_id;              /* 12 */
    uint16_t held_animation_cue_id;               /* 14 */
    uint16_t reset_animation_cue_id;              /* 16 */
    uint16_t flags;                               /* 18 */
    ConditionId start_condition_id;               /* 20 */
} HeldInteractionDef;
_Static_assert(sizeof(HeldInteractionDef) == 22, "HeldInteractionDef layout");

enum HeldInteractionCallbackFlags {
    HELD_CALLBACK_RUNTIME_ONLY = 1u << 0,
    HELD_CALLBACK_GENERATION_BOUND = 1u << 1,
    HELD_CALLBACK_IDEMPOTENT = 1u << 2,
    HELD_CALLBACK_RESTORE_CLOSED_WORLD = 1u << 3
};

typedef struct HeldInteractionCallbackDef {
    uint16_t id;                    /* 0 */
    InteractionId interaction_id;  /* 2 */
    uint16_t animation_cue_id;      /* 4 */
    uint16_t flags;                 /* 6 */
    uint16_t reserved;              /* 8 */
} HeldInteractionCallbackDef;
_Static_assert(sizeof(HeldInteractionCallbackDef) == 10, "HeldInteractionCallbackDef layout");

enum InteractionVariantFlags {
    INTERACTION_VARIANT_START_HELD = 1u << 0,
    INTERACTION_VARIANT_DIALOGUE = 1u << 1,
    INTERACTION_VARIANT_REPEATABLE = 1u << 2
};

typedef struct InteractionVariantDef {
    InteractionId interaction_id;      /* 0: physical interaction owner */
    ConditionId condition_id;          /* 2: variants must be exclusive */
    StringId prompt_string_id;         /* 4 */
    StoryActionListId action_xref;     /* 6: equality-only */
    DialogueId dialogue_id;            /* 8; zero for held start */
    uint16_t flags;                    /* 10 */
} InteractionVariantDef;
_Static_assert(sizeof(InteractionVariantDef) == 12, "InteractionVariantDef layout");

enum OrreryMechanismStateIdValue {
    MECH_POSE_ORRERY_STAIR_OPEN = 0x6601,
    MECH_COLLISION_STUDY_STAIR_OPEN = 0x6602,
    MECH_NAV_STUDY_STAIR_ENABLED = 0x6603
};

enum MechanismWorldTransactionFlags {
    MECH_TXN_STAGE_ALL_BEFORE_COMMIT = 1u << 0,
    MECH_TXN_ATOMIC_PUBLISH = 1u << 1,
    MECH_TXN_ROLLBACK_ON_FAILURE = 1u << 2,
    MECH_TXN_SET_MONOTONIC_FLAG_LAST = 1u << 3
};

typedef struct MechanismWorldTransactionDef {
    StoryActionListId action_list_xref;     /* 0: equality-only */
    InteractionId owner_interaction_id;     /* 2 */
    ConditionId precondition_id;            /* 4 */
    uint16_t pose_state_id;                  /* 6 */
    uint16_t collision_state_id;             /* 8 */
    uint16_t nav_state_id;                   /* 10 */
    uint16_t commit_story_flag_index;        /* 12 */
    uint16_t rollback_callback_id;           /* 14: HeldInteractionCallbackId */
    uint16_t flags;                          /* 16 */
    uint16_t reserved;                       /* 18 */
} MechanismWorldTransactionDef;
_Static_assert(sizeof(MechanismWorldTransactionDef) == 20, "MechanismWorldTransactionDef layout");
```

The opening slice emits exactly one `HeldInteractionDef`: `{ INT_ORRERY_SWITCH, 45, STR_PROMPT_HOLD_ORRERY_SWITCH, HELD_CALLBACK_ORRERY_BEGIN, HELD_CALLBACK_ORRERY_CANCEL_RESET, ACTION_ORRERY_COHERENT_OPEN_COMMIT, ANIM_CUE_ORRERY_SWITCH_PRESS, ANIM_CUE_ORRERY_SWITCH_HELD, ANIM_CUE_ORRERY_INTERRUPTED_RESET, HELD_CANCEL_ON_RELEASE + HELD_CANCEL_ON_DISCONNECT + HELD_CANCEL_ON_RANGE_EXIT + HELD_CANCEL_ON_EXTERNAL_INTERRUPT + HELD_BLOCK_SAVE_WHILE_ACTIVE + HELD_REQUIRE_COHERENT_WORLD_COMMIT + HELD_MONOTONIC_ONCE, COND_INTERACT_ORRERY_CLOSED }`. The 45 ticks are consecutive fixed gameplay ticks while the bound control remains held and the actor remains inside the interaction volume; presentation ticks cannot substitute. Disconnect invokes cancel/reset before exploration freezes. Release, leaving the legal interaction range/volume, scene/transition/dialogue takeover, damage/state takeover, or any other external interruption invokes the same idempotent cancel/reset callback before control ownership changes.

The callback table is exactly `{ HELD_CALLBACK_ORRERY_BEGIN, INT_ORRERY_SWITCH, ANIM_CUE_ORRERY_SWITCH_PRESS, HELD_CALLBACK_RUNTIME_ONLY + HELD_CALLBACK_GENERATION_BOUND, 0 }` and `{ HELD_CALLBACK_ORRERY_CANCEL_RESET, INT_ORRERY_SWITCH, ANIM_CUE_ORRERY_INTERRUPTED_RESET, HELD_CALLBACK_RUNTIME_ONLY + HELD_CALLBACK_GENERATION_BOUND + HELD_CALLBACK_IDEMPOTENT + HELD_CALLBACK_RESTORE_CLOSED_WORLD, 0 }`. Begin captures the current world/runtime generations, acquires the save block, and poses the pressed switch without touching `GameProgress`. Cancel is legal only for that live owner generation, restores the closed switch/orrery/collision/nav staging, releases the save block, and writes no story action. These callbacks are not StoryAction ISA rows and cannot be referenced by dialogue or checkpoint data.

The two physical interactions use state variants, so the invention-hall interaction count remains 14. Exactly one row per physical ID may be legal:

| InteractionId | ConditionId | Prompt / action / dialogue | Flags |
|---|---|---|---|
| `INT_ORRERY_SWITCH` | `COND_INTERACT_ORRERY_CLOSED` | `STR_PROMPT_HOLD_ORRERY_SWITCH / 0 / 0` | `INTERACTION_VARIANT_START_HELD` |
| `INT_ORRERY_SWITCH` | `COND_INTERACT_ORRERY_OPEN` | `STR_PROMPT_EXAMINE_OPEN_SWITCH / 0 / ESTATE_EX_SWITCH_OPEN` | `INTERACTION_VARIANT_DIALOGUE + INTERACTION_VARIANT_REPEATABLE` |
| `INT_ORRERY_ARM_EXAMINE` | `COND_INTERACT_ORRERY_CLOSED` | `STR_PROMPT_EXAMINE_ORRERY_ARM / 0 / ESTATE_EX_ORRERY` | `INTERACTION_VARIANT_DIALOGUE + INTERACTION_VARIANT_REPEATABLE` |
| `INT_ORRERY_ARM_EXAMINE` | `COND_INTERACT_ORRERY_OPEN` | `STR_PROMPT_EXAMINE_ORRERY_ARM / 0 / ESTATE_EX_ORRERY_OPEN` | `INTERACTION_VARIANT_DIALOGUE + INTERACTION_VARIANT_REPEATABLE` |

`COND_INTERACT_ORRERY_CLOSED` is exactly `!FLAG_ORRERY_STAIR_OPEN`; `COND_INTERACT_ORRERY_OPEN` is exactly that flag. Therefore `ESTATE_EX_ORRERY` and the held start are illegal after opening, while `ESTATE_EX_SWITCH_OPEN` and `ESTATE_EX_ORRERY_OPEN` are illegal before it. Post-open variants are repeatable examine actions and cannot restart the hold.

The unique physical `InteractionDef` rows for `INT_ORRERY_SWITCH` and `INT_ORRERY_ARM_EXAMINE` set `prompt_string_id=0`, `condition_id=0`, `action_xref=0`, and `INTERACTION_VARIANT_DRIVEN`; their shared anchor/proximity/facing/priority data remains in the physical row. The selector resolves one legal `InteractionVariantDef` before displaying a prompt. Duplicate physical `InteractionDef` IDs fail generation. Variant rows may share an owner ID only when `(interaction_id, condition_id)` is unique and the generator proves the owner's conditions exhaustive and mutually exclusive; two simultaneously legal or zero legal variants are fatal for these mandatory interactions.

`ACTION_ORRERY_COHERENT_OPEN_COMMIT` owns the sole `MechanismWorldTransactionDef`: `{ ACTION_ORRERY_COHERENT_OPEN_COMMIT, INT_ORRERY_SWITCH, COND_INTERACT_ORRERY_CLOSED, MECH_POSE_ORRERY_STAIR_OPEN, MECH_COLLISION_STUDY_STAIR_OPEN, MECH_NAV_STUDY_STAIR_ENABLED, FLAG_ORRERY_STAIR_OPEN, HELD_CALLBACK_ORRERY_CANCEL_RESET, MECH_TXN_STAGE_ALL_BEFORE_COMMIT + MECH_TXN_ATOMIC_PUBLISH + MECH_TXN_ROLLBACK_ON_FAILURE + MECH_TXN_SET_MONOTONIC_FLAG_LAST, 0 }`. The typed mechanism executor stages pose, collision, and nav replacements against the same world generation; after all validate, one no-fail publish swaps all three and sets the monotonic flag in the scratch story transaction. Any pre-publish failure invokes the literal rollback callback with the flag false. No generic flag opcode may set `FLAG_ORRERY_STAIR_OPEN`. Cancellation never sets a saved flag.

The complete generated destination graph is two nodes and two directed edges. Q16 values below are signed integers (`-262144=-4.0`, `262144=4.0`); `travel_ticks=180` is exactly six seconds on the fixed 30 Hz travel clock.

| DestinationNodeId | Name / icon | Exact Scene / Zone / Spawn | Map x / y Q16 | Unlock ConditionId | Flags |
|---|---|---|---:|---|---|
| `DEST_NODE_MERIDIAN_ANNEX` | `STR_DEST_MERIDIAN_ANNEX / ASSET_MAP_ICON_MERIDIAN_ANNEX` | `SCENE_ANNEX_INTERIOR / ZONE_ANNEX_THRESHOLD / SPAWN_ANNEX_THRESHOLD_DEPARTURE` | `-262144 / 0` | `COND_DEST_ANNEX_AVAILABLE` | `DEST_NODE_DEFAULT_HOME + DEST_NODE_SELECTABLE` |
| `DEST_NODE_VEYRA_ESTATE` | `STR_DEST_VEYRA_ESTATE / ASSET_MAP_ICON_VEYRA_ESTATE` | `SCENE_ESTATE_COURTYARD / ZONE_ESTATE_COURTYARD / SPAWN_ESTATE_COURTYARD_ARRIVAL` | `262144 / 0` | `COND_DEST_ESTATE_UNLOCKED` | `DEST_NODE_SELECTABLE` |

| From -> to | ConditionId | Route AssetId | Travel ticks | Flags |
|---|---|---|---:|---|
| `DEST_NODE_MERIDIAN_ANNEX -> DEST_NODE_VEYRA_ESTATE` | `COND_DEST_ESTATE_UNLOCKED` | `ASSET_VFX_TRANSITION_WORLD_ROUTE` | 180 | `DEST_EDGE_DIRECTED + DEST_EDGE_PLAY_ROUTE` |
| `DEST_NODE_VEYRA_ESTATE -> DEST_NODE_MERIDIAN_ANNEX` | `COND_DEST_ESTATE_ARRIVED` | `ASSET_VFX_TRANSITION_WORLD_ROUTE` | 180 | `DEST_EDGE_DIRECTED + DEST_EDGE_PLAY_ROUTE` |

The complete presentation rows are `{ DEST_NODE_MERIDIAN_ANNEX, MAP_ANNEX_NAME, MAP_ANNEX_DESC, 0 }` and `{ DEST_NODE_VEYRA_ESTATE, MAP_ESTATE_NAME, MAP_ESTATE_DESC, 0 }`. Those four ROOT_UI DialogueIds and their exact StringIds/text come from the singular `DIALOGUE_GRAPH.md` projection below: `MERIDIAN ANNEX`, `Research outpost and Resonance clinic — Eastern Basin`, `VEYRA ESTATE`, and `Observatory and independent workshop — Western Ridge`. The em dash is the text packer's single supported U+2014 glyph and is not substituted at runtime.

The complete MapConfirmRouteDef table is:

| selected node / route condition | TransitionId | prompt / confirm / back | flags |
|---|---|---|---|
| `DEST_NODE_VEYRA_ESTATE / COND_TRANS_ESTATE_FIRST_ARRIVAL_NO_RETURN_FOLLOWER` | `TRANS_DEF_MAP_TO_ESTATE` | `MAP_TRAVEL_CONFIRM / MAP_TRAVEL_ACTION / MAP_TRAVEL_BACK` | all five flags |
| `DEST_NODE_VEYRA_ESTATE / COND_TRANS_ESTATE_RESELECT_NO_RETURN_FOLLOWER` | `TRANS_DEF_MAP_RESELECT_ESTATE` | same | all five flags |
| `DEST_NODE_VEYRA_ESTATE / COND_TRANS_RETURN_FOLLOWER_ACTIVE_ESTATE_SELECTED` | `TRANS_DEF_MAP_RETURN_RESELECT_ESTATE` | same | all five flags |
| `DEST_NODE_MERIDIAN_ANNEX / COND_TRANS_ANNEX_NODE_NO_RETURN_FOLLOWER` | `TRANS_DEF_MAP_TO_THRESHOLD` | `MAP_RETURN_CONFIRM / MAP_RETURN_ACTION / MAP_RETURN_BACK` | all five flags |
| `DEST_NODE_MERIDIAN_ANNEX / COND_TRANS_RETURN_FOLLOWER_ACTIVE_ANNEX_SELECTED` | `TRANS_DEF_MAP_RETURN_TO_ANNEX` | `MAP_RETURN_CONFIRM / MAP_RETURN_ACTION / MAP_RETURN_BACK` | all five flags |

Map-level Cancel/Back while no confirm prompt owns a separate source-origin
route; prompt-level BACK still only closes its prompt. The three
`MapCancelRouteDef` rows are exact:

| Origin / follower | TransitionId | Exact destination | Flags |
|---|---|---|---|
| `MAP_ORIGIN_ANNEX_THRESHOLD / RETURN_FOLLOWER_INACTIVE` | `TRANS_DEF_MAP_CANCEL_TO_ANNEX` | `SCENE_ANNEX_INTERIOR / ZONE_ANNEX_THRESHOLD / SPAWN_ANNEX_THRESHOLD_DEPARTURE` | `REQUIRE_STABLE_MAP_CONTROL + REQUIRE_CURRENT_ORIGIN_GENERATION + PRESERVE_PROGRESS + REQUIRE_SAVE_NONE` |
| `MAP_ORIGIN_ESTATE_COURTYARD / RETURN_FOLLOWER_INACTIVE` | `TRANS_DEF_MAP_CANCEL_TO_ESTATE` | `SCENE_ESTATE_COURTYARD / ZONE_ESTATE_COURTYARD / SPAWN_ESTATE_COURTYARD_FROM_MAP` | `REQUIRE_STABLE_MAP_CONTROL + REQUIRE_CURRENT_ORIGIN_GENERATION + PRESERVE_PROGRESS + REQUIRE_SAVE_NONE` |
| `MAP_ORIGIN_ESTATE_COURTYARD / RETURN_FOLLOWER_ACTIVE` | `TRANS_DEF_MAP_CANCEL_TO_ESTATE_FOLLOWER` | `SCENE_ESTATE_COURTYARD / ZONE_ESTATE_COURTYARD / SPAWN_ESTATE_COURTYARD_FROM_MAP` | `REQUIRE_STABLE_MAP_CONTROL + REQUIRE_CURRENT_ORIGIN_GENERATION + PRESERVE_PROGRESS + REQUIRE_SAVE_NONE + FOLLOWER_HANDOFF` |

"All five" is exact mask `0x001F`; "same" expands to the three DialogueIds in the first Estate row. The graph locks their exact prompt strings to `Travel to Veyra Observatory Estate?`, `Travel to Meridian Research Annex?`, `TRAVEL`, and `BACK`, and byte-validates each root's option targets. The current selected node is mapped to `MAP_SELECTION_ESTATE` or `MAP_SELECTION_ANNEX` by the locked node-to-selection table, never by numeric cast. On A, MapController snapshots the selected node and follower state, resolves exactly one row whose condition is true, reserves that exact TransitionId, closes the confirm no-fail, and submits the request; TransitionController revalidates the referenced TransitionDef and condition under the same runtime/map generations. On B, Back, controller loss, or deselection it closes the prompt, clears the selection edge, and changes no progress, follower, save, route, or transition state. One physical press cannot open and accept the prompt; opening/closing discards one poll frame. A hidden/dark node cannot acquire focus or a confirm row. Duplicate selected-node/condition rows, zero or multiple matches, prompt/graph mismatch, wrong TransitionDef destination, unknown flags, or nonzero reserved fail generation. Thus `MAP_TRAVEL_CONFIRM` and `MAP_RETURN_CONFIRM` are literal data paths, not hard-coded UI branches.

On every successful transition into `SCENE_WORLD_MAP`, MapController captures one
immutable `MapOriginSnapshot` before map control publishes. Threshold-to-map
first/repeat map to Annex+inactive; Estate-to-map maps to Estate+inactive; and
Study-return-to-map maps to Estate+active. Flags are exactly `0x0007` and the
incoming TransitionId must be one of those four rows. With no confirm open, a
debounced B or explicit Back focus resolves exactly one cancel row, reserves its
SAVE_NONE transition, and only then consumes the edge. It never runs a save
recipe or changes progress/selection/follower state. The transition returns to
the physical source threshold/courtyard; the follower row retains the ordinary
handoff. A stale/missing origin snapshot, Annex+active impossible pair,
destination xref mismatch, non-SAVE_NONE transition, wrong follower flag, or a
prompt Back that invokes map-level Cancel fails generation/runtime closed.

`COND_DEST_ANNEX_AVAILABLE` is exactly the initialized Annex destination bit; `COND_DEST_ESTATE_UNLOCKED` is exactly that bit plus `FLAG_ESTATE_DESTINATION_UNLOCKED`; `COND_DEST_ESTATE_ARRIVED` is exactly `FLAG_ESTATE_ARRIVED`. `DEST_NODE_MERIDIAN_ANNEX` maps explicitly to `DESTINATION_ANNEX_BIT` (0), and `DEST_NODE_VEYRA_ESTATE` maps to `DESTINATION_ESTATE_BIT` (1); numeric node IDs never index the bitset. Node flags accept mask `0x0003`; edge flags accept mask `0x0003`; unknown bits fail. IDs, names, icons, route assets, conditions, coordinates, travel ticks, and tuples are literal generated fields. Duplicate nodes/edges, a missing reverse row, a node-to-bitset inference, or any unresolved reference fails generation. `present.world_route` remains only a delivery alias and is not a runtime AssetId.

`NavGraphDef.flags`, `NavNodeDef.flags`, `NavEdgeDef.flags`, and `SpawnDef.flags` accept only masks `0x0007`, `0x000F`, `0x0007`, and `0x000F` respectively. `NavEdgeDef.reserved` is always zero. `InteractionDef.flags` accepts only `0x001F` and its reserved field is zero. `INTERACTION_ACTOR_ATTACHED` requires a character-model anchor with an authored dialogue focus socket, `ZONE_NONE`, router-owned zero condition/action, and current actor-generation validation; every non-attached row requires a nonzero exact ZoneId. SAVED_ONCE_EXAMINE requires exactly one live ExamineOnceRegistryDef row; REPEATABLE and SAVED_ONCE may coexist only when the registry's already-set behavior is typed replay-without-action. Unknown bits in any generated navigation/spawn/interaction row fail generation rather than being masked.

Per-zone generated counts are locked to the inventory: sim `8/12/10/0`, Annex sim `12/18/6/4`, atrium `36/58/18/12`, director `12/20/6/5`, player room `8/12/4/4`, clinic `16/24/8/7`, workshop `18/28/8/9`, threshold `14/22/8/6`, map `2/2/2/2`, courtyard `32/52/16/10`, foyer `14/22/8/6`, invention hall `28/46/14/14`, and study `18/28/10/10`, expressed as nav nodes/edges/spawns/interactions. Hard per-zone caps are 36 nodes, 58 directed edges, 18 spawns, 14 interactions, and 48 nodes in a bounded path worklist.

Validation requires every edge endpoint, spawn condition, prompt string, action, anchor, and ZoneId to resolve; every safe/default/checkpoint spawn must pass capsule and camera clearance; all mandatory interactions must be reachable from the default spawn under a satisfiable story condition; proximity is nonzero; facing dot lies in Q1.14 `[-16384,16384]`; selector tie-break is priority, distance, facing, then InteractionId. Orphan nodes, impossible one-way mandatory routes, non-variant interaction records without prompts/actions, duplicate physical IDs, invalid variant ownership/condition coverage, and a follower handoff without paired safe anchors fail generation.

### 2.3 Input, exploration motion, collision, camera, and follower tuning

All values below are release data, not controller literals. Simulation consumes
one shaped input sample per fixed 30 Hz tick; UI consumes only the hysteretic
digital events produced from that same sample.

```c
typedef enum InputResponseCurveValue {
    INPUT_CURVE_Q15_SMOOTHSTEP = 1
} InputResponseCurveValue;

enum InputTuningFlags {
    INPUT_RADIAL_DEAD_ZONE = 1u << 0,
    INPUT_CLAMP_OUTER_RADIUS = 1u << 1,
    INPUT_UI_HYSTERESIS = 1u << 2,
    INPUT_FLUSH_ON_DISCONNECT = 1u << 3,
    INPUT_DISCARD_RECONNECT_POLL = 1u << 4,
    INPUT_ONE_EDGE_PER_POLL_FRAME = 1u << 5
};

typedef struct InputTuningDef {
    uint16_t profile_id;             /* 0: one */
    uint8_t inner_dead_zone_raw;     /* 2: radial raw-stick units */
    uint8_t outer_radius_raw;        /* 3 */
    uint16_t ui_enter_q15;           /* 4 */
    uint16_t ui_exit_q15;            /* 6 */
    uint8_t ui_initial_repeat_ticks; /* 8: fixed 30 Hz */
    uint8_t ui_repeat_ticks;         /* 9 */
    uint8_t reconnect_discard_polls; /* 10 */
    uint8_t response_curve;          /* 11: InputResponseCurveValue */
    uint16_t normalized_max_q15;     /* 12: 32767 */
    uint16_t flags;                  /* 14: InputTuningFlags */
    uint32_t reserved;               /* 16: zero */
} InputTuningDef;
_Static_assert(sizeof(InputTuningDef) == 20, "InputTuningDef layout");

enum InputContextMaskValue {
    INPUT_CONTEXT_EXPLORATION = 1u << 0,
    INPUT_CONTEXT_DIALOGUE = 1u << 1,
    INPUT_CONTEXT_NAME_GRID = 1u << 2,
    INPUT_CONTEXT_MENU = 1u << 3,
    INPUT_CONTEXT_RELAY = 1u << 4,
    INPUT_CONTEXT_WORLD_MAP = 1u << 5,
    INPUT_CONTEXT_BATTLE_COMMAND = 1u << 6,
    INPUT_CONTEXT_BATTLE_TARGET = 1u << 7,
    INPUT_CONTEXT_OPENING_SLATE = 1u << 8,
    INPUT_CONTEXT_RECONNECT_TRANSFER = 1u << 9
};

typedef enum HardwareInputValue {
    HW_INPUT_NONE = 0,
    HW_INPUT_STICK_VECTOR = 1,
    HW_INPUT_STICK_UP = 2,
    HW_INPUT_STICK_DOWN = 3,
    HW_INPUT_STICK_LEFT = 4,
    HW_INPUT_STICK_RIGHT = 5,
    HW_INPUT_DPAD_UP = 6,
    HW_INPUT_DPAD_DOWN = 7,
    HW_INPUT_DPAD_LEFT = 8,
    HW_INPUT_DPAD_RIGHT = 9,
    HW_INPUT_A = 10,
    HW_INPUT_B = 11,
    HW_INPUT_Z = 12,
    HW_INPUT_START = 13,
    HW_INPUT_L = 14,
    HW_INPUT_R = 15,
    HW_INPUT_C_UP = 16,
    HW_INPUT_C_DOWN = 17,
    HW_INPUT_C_LEFT = 18,
    HW_INPUT_C_RIGHT = 19
} HardwareInputValue;

typedef enum LogicalInputActionValue {
    INPUT_ACTION_MOVE_VECTOR = 1,
    INPUT_ACTION_INTERACT_PRESS = 2,
    INPUT_ACTION_INTERACT_HOLD = 3,
    INPUT_ACTION_RUN = 4,
    INPUT_ACTION_PAUSE = 5,
    INPUT_ACTION_OPEN_RELAY = 6,
    INPUT_ACTION_CAMERA_YAW_LEFT = 7,
    INPUT_ACTION_CAMERA_YAW_RIGHT = 8,
    INPUT_ACTION_CAMERA_PITCH_UP = 9,
    INPUT_ACTION_CAMERA_PITCH_DOWN = 10,
    INPUT_ACTION_DIALOGUE_ADVANCE = 11,
    INPUT_ACTION_UI_UP = 12,
    INPUT_ACTION_UI_DOWN = 13,
    INPUT_ACTION_UI_LEFT = 14,
    INPUT_ACTION_UI_RIGHT = 15,
    INPUT_ACTION_UI_CONFIRM = 16,
    INPUT_ACTION_NAME_DELETE = 17,
    INPUT_ACTION_NAME_CONFIRM = 18,
    INPUT_ACTION_UI_BACK = 19,
    INPUT_ACTION_RELAY_TAB_PREVIOUS = 20,
    INPUT_ACTION_RELAY_TAB_NEXT = 21,
    INPUT_ACTION_BATTLE_MOVE_INFO = 22,
    INPUT_ACTION_OPENING_SKIP = 23,
    INPUT_ACTION_RECONNECT_TRANSFER = 24
} LogicalInputActionValue;

typedef enum InputBindingTriggerValue {
    INPUT_BIND_HELD_FIXED_TICK = 1,
    INPUT_BIND_PRESS_EDGE = 2,
    INPUT_BIND_DIGITAL_REPEAT_EVENT = 3
} InputBindingTriggerValue;

enum InputBindingFlags {
    INPUT_BIND_CONSUME_EDGE = 1u << 0,
    INPUT_BIND_OWNER_GATED = 1u << 1,
    INPUT_BIND_REQUIRE_CHORD_HELD = 1u << 2,
    INPUT_BIND_REQUIRE_CHORD_RELEASED = 1u << 3,
    INPUT_BIND_APPLY_CAMERA_INVERT_X = 1u << 4,
    INPUT_BIND_APPLY_CAMERA_INVERT_Y = 1u << 5,
    INPUT_BIND_ALLOW_PARALLEL_HELD_SAMPLE = 1u << 6,
    INPUT_BIND_CLEAR_ON_CONTEXT_CHANGE = 1u << 7
};

typedef struct HardwareInputBindingDef {
    uint16_t context_mask; /* 0: InputContextMaskValue */
    uint8_t hardware_input;/* 2: HardwareInputValue */
    uint8_t chord_input;   /* 3: HardwareInputValue or NONE */
    uint8_t logical_action;/* 4: LogicalInputActionValue */
    uint8_t trigger;       /* 5: InputBindingTriggerValue */
    uint8_t priority;      /* 6: high row wins one source event */
    uint8_t flags;         /* 7: InputBindingFlags */
} HardwareInputBindingDef;
_Static_assert(sizeof(HardwareInputBindingDef) == 8, "HardwareInputBindingDef layout");

enum CameraInputTuningFlags {
    CAMERA_INPUT_DIGITAL_FIXED_TICK = 1u << 0,
    CAMERA_INPUT_CHORD_BEFORE_BARE_BUTTON = 1u << 1,
    CAMERA_INPUT_SETTINGS_INVERT_X = 1u << 2,
    CAMERA_INPUT_SETTINGS_INVERT_Y = 1u << 3,
    CAMERA_INPUT_CLEAR_ON_OWNER_CHANGE = 1u << 4
};

typedef struct CameraInputTuningDef {
    uint16_t profile_id;             /* 0: one */
    uint16_t yaw_speed_deg_q8;       /* 2: 120 degrees/second */
    uint16_t pitch_speed_deg_q8;     /* 4: 60 degrees/second */
    uint16_t yaw_step_deg_q8;        /* 6: exact per 30 Hz tick */
    uint16_t pitch_step_deg_q8;      /* 8 */
    uint8_t initial_repeat_ticks;    /* 10: zero, immediate */
    uint8_t repeat_ticks;            /* 11: one */
    uint8_t vertical_chord_input;    /* 12: HW_INPUT_L */
    uint8_t relay_input;             /* 13: HW_INPUT_C_DOWN */
    uint16_t flags;                  /* 14: CameraInputTuningFlags */
    uint32_t reserved;               /* 16: zero */
} CameraInputTuningDef;
_Static_assert(sizeof(CameraInputTuningDef) == 20, "CameraInputTuningDef layout");

enum ControllerEnrollmentFlags {
    CONTROLLER_ENROLL_PLATFORM_ONLY = 1u << 0,
    CONTROLLER_ENROLL_CONSUME_CLAIM_EDGE = 1u << 1,
    CONTROLLER_ENROLL_CLEAR_ALL_LATCHES = 1u << 2,
    CONTROLLER_ENROLL_DISCARD_COMPLETE_POLL = 1u << 3,
    CONTROLLER_ENROLL_PUBLISH_CONTEXT_AFTER_DISCARD = 1u << 4,
    CONTROLLER_ENROLL_RECONNECT_TRANSFER_DISTINCT = 1u << 5
};

typedef struct ControllerEnrollmentDef {
    uint8_t primary_claim_input;     /* 0: HW_INPUT_START */
    uint8_t secondary_claim_input;   /* 1: HW_INPUT_A */
    uint8_t reconnect_transfer_input;/* 2: HW_INPUT_START only */
    uint8_t discard_polls;           /* 3: exact one */
    uint16_t eligible_port_mask;     /* 4: ports 0..3, exact 0x000F */
    uint16_t flags;                  /* 6: ControllerEnrollmentFlags */
    uint32_t reserved;               /* 8: zero */
} ControllerEnrollmentDef;
_Static_assert(sizeof(ControllerEnrollmentDef) == 12, "ControllerEnrollmentDef layout");

typedef struct PlayerMotionTuningDef {
    uint16_t profile_id;         /* 0: one */
    uint16_t walk_speed_q8;      /* 2: metres/second */
    uint16_t run_speed_q8;       /* 4 */
    uint16_t acceleration_q8;    /* 6: metres/second squared */
    uint16_t deceleration_q8;    /* 8 */
    uint16_t turn_speed_deg_q8;  /* 10: degrees/second */
    uint16_t move_enter_q15;     /* 12 */
    uint16_t move_exit_q15;      /* 14 */
    uint16_t run_enter_q15;      /* 16 */
    uint16_t run_exit_q15;       /* 18 */
    uint16_t gravity_q8;         /* 20 */
    uint16_t max_fall_speed_q8;  /* 22 */
} PlayerMotionTuningDef;
_Static_assert(sizeof(PlayerMotionTuningDef) == 24, "PlayerMotionTuningDef layout");

enum CollisionTuningFlags {
    COLLISION_CAPSULE_SWEEP = 1u << 0,
    COLLISION_SLIDE_ON_BLOCK = 1u << 1,
    COLLISION_STEP_REQUIRES_TOP_CLEARANCE = 1u << 2,
    COLLISION_DOOR_REQUIRES_FULL_CAPSULE_CLEARANCE = 1u << 3,
    COLLISION_RECOVER_TO_ZONE_SAFE_ANCHOR = 1u << 4,
    COLLISION_GENERATION_BOUND = 1u << 5
};

typedef struct CollisionTuningDef {
    uint16_t profile_id;                /* 0: one */
    uint16_t capsule_radius_q8;         /* 2 */
    uint16_t capsule_height_q8;         /* 4 */
    uint16_t skin_width_q8;             /* 6 */
    uint16_t max_step_height_q8;        /* 8 */
    uint16_t max_slope_cos_q15;         /* 10: cos(45 degrees) */
    uint16_t ground_probe_q8;           /* 12 */
    uint16_t door_clearance_q8;         /* 14 */
    uint16_t fall_recovery_distance_q8; /* 16: below last grounded point */
    uint8_t penetration_iterations;     /* 18: exact bounded cap */
    uint8_t sweep_substeps;             /* 19 */
    uint16_t flags;                     /* 20: CollisionTuningFlags */
    uint16_t reserved0;                 /* 22: zero */
    uint32_t reserved1;                 /* 24: zero */
} CollisionTuningDef;
_Static_assert(sizeof(CollisionTuningDef) == 28, "CollisionTuningDef layout");

enum CameraTuningFlags {
    CAMERA_USE_SPHERE_SWEEP = 1u << 0,
    CAMERA_PULL_IN_BEFORE_OCCLUSION = 1u << 1,
    CAMERA_NEVER_PUSH_THROUGH_BLOCKER = 1u << 2,
    CAMERA_GENERATION_BOUND = 1u << 3
};

typedef struct CameraTuningDef {
    uint16_t profile_id;          /* 0: one */
    uint16_t yaw_speed_deg_q8;    /* 2 */
    int16_t pitch_min_deg_q8;     /* 4 */
    int16_t pitch_max_deg_q8;     /* 6 */
    uint16_t default_distance_q8; /* 8 */
    uint16_t min_distance_q8;     /* 10 */
    uint16_t max_distance_q8;     /* 12 */
    uint16_t target_height_q8;    /* 14 */
    uint16_t collision_radius_q8; /* 16 */
    uint8_t yaw_smooth_ticks;     /* 18 */
    uint8_t pitch_smooth_ticks;   /* 19 */
    uint8_t distance_smooth_ticks;/* 20 */
    uint8_t target_smooth_ticks;  /* 21 */
    uint16_t flags;               /* 22: CameraTuningFlags */
    uint16_t scalar_snap_epsilon_q8;/* 24 */
    uint16_t target_snap_epsilon_q16;/* 26: world target vector */
} CameraTuningDef;
_Static_assert(sizeof(CameraTuningDef) == 28, "CameraTuningDef layout");

enum CameraVolumeFlags {
    CAMERA_VOLUME_ORBIT = 1u << 0,
    CAMERA_VOLUME_USE_AUTHORED_YAW_BIAS = 1u << 1,
    CAMERA_VOLUME_USE_AUTHORED_PITCH_BIAS = 1u << 2,
    CAMERA_VOLUME_BLOCKER_COLLISION = 1u << 3,
    CAMERA_VOLUME_FALLBACK_TO_ZONE_ORBIT = 1u << 4,
    CAMERA_VOLUME_SAFE_GENERATION_OWNER = 1u << 5
};

enum CameraBlockerMaskValue {
    CAMERA_BLOCKER_WORLD = 1u << 0,
    CAMERA_BLOCKER_DOOR = 1u << 1
};

typedef struct CameraVolumeDef {
    uint16_t volume_id;        /* 0: nonzero local ID from col.common.camera_volumes */
    ZoneId zone_id;            /* 2 */
    uint16_t source_volume_id; /* 4: exact authored convex-volume record */
    uint16_t fallback_volume_id;/* 6: same-zone fallback or global zero */
    int16_t yaw_bias_deg_q8;   /* 8 */
    int16_t pitch_bias_deg_q8; /* 10 */
    uint16_t distance_q8;      /* 12 */
    uint16_t priority;         /* 14: higher wins; tie by lower volume_id */
    uint16_t blend_ticks;      /* 16: fixed 30 Hz */
    uint16_t blocker_mask;     /* 18: authored camera-blocker layers */
    uint16_t flags;            /* 20: CameraVolumeFlags */
    uint16_t reserved;         /* 22: zero */
} CameraVolumeDef;
_Static_assert(sizeof(CameraVolumeDef) == 24, "CameraVolumeDef layout");

enum FollowerTuningFlags {
    FOLLOWER_PATHFIND_ON_ZONE_NAV = 1u << 0,
    FOLLOWER_RECOVER_ONLY_OFF_CAMERA = 1u << 1,
    FOLLOWER_REQUIRE_RECOVERY_ANCHOR_CLEARANCE = 1u << 2,
    FOLLOWER_CANCEL_ON_GENERATION_CHANGE = 1u << 3,
    FOLLOWER_CANCEL_ON_TRANSITION_OR_MODAL = 1u << 4,
    FOLLOWER_NEVER_TELEPORT_ACROSS_CLOSED_DOOR = 1u << 5
};

typedef struct FollowerTuningDef {
    ZoneId zone_id;                    /* 0 */
    uint16_t recover_distance_q8;      /* 2: sustained player distance */
    uint16_t stall_progress_epsilon_q8;/* 4 */
    uint16_t stall_ticks;              /* 6: fixed 30 Hz */
    uint16_t recover_distance_ticks;   /* 8: exact 45 */
    uint8_t off_camera_frames;         /* 10: consecutive rendered frames */
    uint8_t off_camera_margin_pixels;  /* 11 */
    uint16_t anchor_search_node_cap;   /* 12 */
    uint16_t flags;                    /* 14: FollowerTuningFlags */
    uint16_t trail_min_q8;             /* 16: 1.2 m rounded to Q8 */
    uint16_t trail_target_q8;          /* 18: 1.6 m rounded to Q8 */
    uint16_t trail_max_q8;             /* 20: 2.0 m */
    uint16_t walk_speed_q8;            /* 22: metres/second */
    uint16_t run_speed_q8;             /* 24 */
    uint16_t acceleration_q8;          /* 26 */
    uint16_t deceleration_q8;          /* 28 */
    uint16_t steering_yield_radius_q8; /* 30: player/interaction clearance */
    uint16_t portal_wait_threshold_q8; /* 32: handoff wait pose */
    uint16_t turn_speed_deg_q8;        /* 34 */
    uint16_t handoff_stable_ticks;     /* 36: paired anchors current */
    uint16_t reserved0;                /* 38: zero */
    uint32_t reserved1;                /* 40: zero */
} FollowerTuningDef;
_Static_assert(sizeof(FollowerTuningDef) == 44, "FollowerTuningDef layout");

static const InputTuningDef INPUT_TUNING[1] = {
    { 1, 12, 76, 18022, 13107, 12, 4, 1, INPUT_CURVE_Q15_SMOOTHSTEP,
      32767, INPUT_RADIAL_DEAD_ZONE + INPUT_CLAMP_OUTER_RADIUS +
      INPUT_UI_HYSTERESIS + INPUT_FLUSH_ON_DISCONNECT +
      INPUT_DISCARD_RECONNECT_POLL + INPUT_ONE_EDGE_PER_POLL_FRAME, 0 }
};

static const CameraInputTuningDef CAMERA_INPUT_TUNING[1] = {
    { 1, 30720, 15360, 1024, 512, 0, 1, HW_INPUT_L, HW_INPUT_C_DOWN,
      CAMERA_INPUT_DIGITAL_FIXED_TICK + CAMERA_INPUT_CHORD_BEFORE_BARE_BUTTON +
      CAMERA_INPUT_SETTINGS_INVERT_X + CAMERA_INPUT_SETTINGS_INVERT_Y +
      CAMERA_INPUT_CLEAR_ON_OWNER_CHANGE, 0 }
};

static const ControllerEnrollmentDef CONTROLLER_ENROLLMENT[1] = {
    { HW_INPUT_START, HW_INPUT_A, HW_INPUT_START, 1, 0x000F,
      CONTROLLER_ENROLL_PLATFORM_ONLY + CONTROLLER_ENROLL_CONSUME_CLAIM_EDGE +
      CONTROLLER_ENROLL_CLEAR_ALL_LATCHES + CONTROLLER_ENROLL_DISCARD_COMPLETE_POLL +
      CONTROLLER_ENROLL_PUBLISH_CONTEXT_AFTER_DISCARD +
      CONTROLLER_ENROLL_RECONNECT_TRANSFER_DISTINCT, 0 }
};

static const HardwareInputBindingDef HARDWARE_INPUT_BINDINGS[29] = {
    { INPUT_CONTEXT_EXPLORATION, HW_INPUT_STICK_VECTOR, HW_INPUT_NONE,
      INPUT_ACTION_MOVE_VECTOR, INPUT_BIND_HELD_FIXED_TICK, 100,
      INPUT_BIND_OWNER_GATED + INPUT_BIND_CLEAR_ON_CONTEXT_CHANGE },
    { INPUT_CONTEXT_EXPLORATION, HW_INPUT_A, HW_INPUT_NONE,
      INPUT_ACTION_INTERACT_PRESS, INPUT_BIND_PRESS_EDGE, 120,
      INPUT_BIND_CONSUME_EDGE + INPUT_BIND_OWNER_GATED + INPUT_BIND_CLEAR_ON_CONTEXT_CHANGE },
    { INPUT_CONTEXT_EXPLORATION, HW_INPUT_A, HW_INPUT_NONE,
      INPUT_ACTION_INTERACT_HOLD, INPUT_BIND_HELD_FIXED_TICK, 110,
      INPUT_BIND_OWNER_GATED + INPUT_BIND_ALLOW_PARALLEL_HELD_SAMPLE + INPUT_BIND_CLEAR_ON_CONTEXT_CHANGE },
    { INPUT_CONTEXT_EXPLORATION, HW_INPUT_B, HW_INPUT_NONE,
      INPUT_ACTION_RUN, INPUT_BIND_HELD_FIXED_TICK, 100,
      INPUT_BIND_OWNER_GATED + INPUT_BIND_CLEAR_ON_CONTEXT_CHANGE },
    { INPUT_CONTEXT_EXPLORATION + INPUT_CONTEXT_BATTLE_COMMAND + INPUT_CONTEXT_BATTLE_TARGET,
      HW_INPUT_START, HW_INPUT_NONE,
      INPUT_ACTION_PAUSE, INPUT_BIND_PRESS_EDGE, 120,
      INPUT_BIND_CONSUME_EDGE + INPUT_BIND_OWNER_GATED + INPUT_BIND_CLEAR_ON_CONTEXT_CHANGE },
    { INPUT_CONTEXT_EXPLORATION, HW_INPUT_C_DOWN, HW_INPUT_L,
      INPUT_ACTION_OPEN_RELAY, INPUT_BIND_PRESS_EDGE, 100,
      INPUT_BIND_CONSUME_EDGE + INPUT_BIND_OWNER_GATED +
      INPUT_BIND_REQUIRE_CHORD_RELEASED + INPUT_BIND_CLEAR_ON_CONTEXT_CHANGE },
    { INPUT_CONTEXT_EXPLORATION, HW_INPUT_C_LEFT, HW_INPUT_NONE,
      INPUT_ACTION_CAMERA_YAW_LEFT, INPUT_BIND_HELD_FIXED_TICK, 150,
      INPUT_BIND_OWNER_GATED + INPUT_BIND_APPLY_CAMERA_INVERT_X + INPUT_BIND_CLEAR_ON_CONTEXT_CHANGE },
    { INPUT_CONTEXT_EXPLORATION, HW_INPUT_C_RIGHT, HW_INPUT_NONE,
      INPUT_ACTION_CAMERA_YAW_RIGHT, INPUT_BIND_HELD_FIXED_TICK, 150,
      INPUT_BIND_OWNER_GATED + INPUT_BIND_APPLY_CAMERA_INVERT_X + INPUT_BIND_CLEAR_ON_CONTEXT_CHANGE },
    { INPUT_CONTEXT_EXPLORATION, HW_INPUT_C_UP, HW_INPUT_L,
      INPUT_ACTION_CAMERA_PITCH_UP, INPUT_BIND_HELD_FIXED_TICK, 200,
      INPUT_BIND_OWNER_GATED + INPUT_BIND_REQUIRE_CHORD_HELD +
      INPUT_BIND_APPLY_CAMERA_INVERT_Y + INPUT_BIND_CLEAR_ON_CONTEXT_CHANGE },
    { INPUT_CONTEXT_EXPLORATION, HW_INPUT_C_DOWN, HW_INPUT_L,
      INPUT_ACTION_CAMERA_PITCH_DOWN, INPUT_BIND_HELD_FIXED_TICK, 200,
      INPUT_BIND_OWNER_GATED + INPUT_BIND_REQUIRE_CHORD_HELD +
      INPUT_BIND_APPLY_CAMERA_INVERT_Y + INPUT_BIND_CLEAR_ON_CONTEXT_CHANGE },

    { INPUT_CONTEXT_DIALOGUE, HW_INPUT_A, HW_INPUT_NONE,
      INPUT_ACTION_DIALOGUE_ADVANCE, INPUT_BIND_PRESS_EDGE, 120,
      INPUT_BIND_CONSUME_EDGE + INPUT_BIND_OWNER_GATED + INPUT_BIND_CLEAR_ON_CONTEXT_CHANGE },

    { INPUT_CONTEXT_NAME_GRID + INPUT_CONTEXT_MENU + INPUT_CONTEXT_RELAY + INPUT_CONTEXT_WORLD_MAP + INPUT_CONTEXT_BATTLE_COMMAND + INPUT_CONTEXT_BATTLE_TARGET,
      HW_INPUT_STICK_UP, HW_INPUT_NONE, INPUT_ACTION_UI_UP, INPUT_BIND_DIGITAL_REPEAT_EVENT, 100,
      INPUT_BIND_CONSUME_EDGE + INPUT_BIND_OWNER_GATED + INPUT_BIND_CLEAR_ON_CONTEXT_CHANGE },
    { INPUT_CONTEXT_NAME_GRID + INPUT_CONTEXT_MENU + INPUT_CONTEXT_RELAY + INPUT_CONTEXT_WORLD_MAP + INPUT_CONTEXT_BATTLE_COMMAND + INPUT_CONTEXT_BATTLE_TARGET,
      HW_INPUT_STICK_DOWN, HW_INPUT_NONE, INPUT_ACTION_UI_DOWN, INPUT_BIND_DIGITAL_REPEAT_EVENT, 100,
      INPUT_BIND_CONSUME_EDGE + INPUT_BIND_OWNER_GATED + INPUT_BIND_CLEAR_ON_CONTEXT_CHANGE },
    { INPUT_CONTEXT_NAME_GRID + INPUT_CONTEXT_MENU + INPUT_CONTEXT_RELAY + INPUT_CONTEXT_WORLD_MAP + INPUT_CONTEXT_BATTLE_COMMAND + INPUT_CONTEXT_BATTLE_TARGET,
      HW_INPUT_STICK_LEFT, HW_INPUT_NONE, INPUT_ACTION_UI_LEFT, INPUT_BIND_DIGITAL_REPEAT_EVENT, 100,
      INPUT_BIND_CONSUME_EDGE + INPUT_BIND_OWNER_GATED + INPUT_BIND_CLEAR_ON_CONTEXT_CHANGE },
    { INPUT_CONTEXT_NAME_GRID + INPUT_CONTEXT_MENU + INPUT_CONTEXT_RELAY + INPUT_CONTEXT_WORLD_MAP + INPUT_CONTEXT_BATTLE_COMMAND + INPUT_CONTEXT_BATTLE_TARGET,
      HW_INPUT_STICK_RIGHT, HW_INPUT_NONE, INPUT_ACTION_UI_RIGHT, INPUT_BIND_DIGITAL_REPEAT_EVENT, 100,
      INPUT_BIND_CONSUME_EDGE + INPUT_BIND_OWNER_GATED + INPUT_BIND_CLEAR_ON_CONTEXT_CHANGE },
    { INPUT_CONTEXT_NAME_GRID + INPUT_CONTEXT_MENU + INPUT_CONTEXT_RELAY + INPUT_CONTEXT_WORLD_MAP + INPUT_CONTEXT_BATTLE_COMMAND + INPUT_CONTEXT_BATTLE_TARGET,
      HW_INPUT_DPAD_UP, HW_INPUT_NONE, INPUT_ACTION_UI_UP, INPUT_BIND_DIGITAL_REPEAT_EVENT, 100,
      INPUT_BIND_CONSUME_EDGE + INPUT_BIND_OWNER_GATED + INPUT_BIND_CLEAR_ON_CONTEXT_CHANGE },
    { INPUT_CONTEXT_NAME_GRID + INPUT_CONTEXT_MENU + INPUT_CONTEXT_RELAY + INPUT_CONTEXT_WORLD_MAP + INPUT_CONTEXT_BATTLE_COMMAND + INPUT_CONTEXT_BATTLE_TARGET,
      HW_INPUT_DPAD_DOWN, HW_INPUT_NONE, INPUT_ACTION_UI_DOWN, INPUT_BIND_DIGITAL_REPEAT_EVENT, 100,
      INPUT_BIND_CONSUME_EDGE + INPUT_BIND_OWNER_GATED + INPUT_BIND_CLEAR_ON_CONTEXT_CHANGE },
    { INPUT_CONTEXT_NAME_GRID + INPUT_CONTEXT_MENU + INPUT_CONTEXT_RELAY + INPUT_CONTEXT_WORLD_MAP + INPUT_CONTEXT_BATTLE_COMMAND + INPUT_CONTEXT_BATTLE_TARGET,
      HW_INPUT_DPAD_LEFT, HW_INPUT_NONE, INPUT_ACTION_UI_LEFT, INPUT_BIND_DIGITAL_REPEAT_EVENT, 100,
      INPUT_BIND_CONSUME_EDGE + INPUT_BIND_OWNER_GATED + INPUT_BIND_CLEAR_ON_CONTEXT_CHANGE },
    { INPUT_CONTEXT_NAME_GRID + INPUT_CONTEXT_MENU + INPUT_CONTEXT_RELAY + INPUT_CONTEXT_WORLD_MAP + INPUT_CONTEXT_BATTLE_COMMAND + INPUT_CONTEXT_BATTLE_TARGET,
      HW_INPUT_DPAD_RIGHT, HW_INPUT_NONE, INPUT_ACTION_UI_RIGHT, INPUT_BIND_DIGITAL_REPEAT_EVENT, 100,
      INPUT_BIND_CONSUME_EDGE + INPUT_BIND_OWNER_GATED + INPUT_BIND_CLEAR_ON_CONTEXT_CHANGE },
    { INPUT_CONTEXT_NAME_GRID + INPUT_CONTEXT_MENU + INPUT_CONTEXT_RELAY + INPUT_CONTEXT_WORLD_MAP + INPUT_CONTEXT_BATTLE_COMMAND + INPUT_CONTEXT_BATTLE_TARGET,
      HW_INPUT_A, HW_INPUT_NONE, INPUT_ACTION_UI_CONFIRM, INPUT_BIND_PRESS_EDGE, 120,
      INPUT_BIND_CONSUME_EDGE + INPUT_BIND_OWNER_GATED + INPUT_BIND_CLEAR_ON_CONTEXT_CHANGE },
    { INPUT_CONTEXT_NAME_GRID, HW_INPUT_B, HW_INPUT_NONE,
      INPUT_ACTION_NAME_DELETE, INPUT_BIND_PRESS_EDGE, 120,
      INPUT_BIND_CONSUME_EDGE + INPUT_BIND_OWNER_GATED + INPUT_BIND_CLEAR_ON_CONTEXT_CHANGE },
    { INPUT_CONTEXT_NAME_GRID, HW_INPUT_START, HW_INPUT_NONE,
      INPUT_ACTION_NAME_CONFIRM, INPUT_BIND_PRESS_EDGE, 120,
      INPUT_BIND_CONSUME_EDGE + INPUT_BIND_OWNER_GATED + INPUT_BIND_CLEAR_ON_CONTEXT_CHANGE },
    { INPUT_CONTEXT_MENU + INPUT_CONTEXT_RELAY + INPUT_CONTEXT_WORLD_MAP + INPUT_CONTEXT_BATTLE_COMMAND + INPUT_CONTEXT_BATTLE_TARGET,
      HW_INPUT_B, HW_INPUT_NONE, INPUT_ACTION_UI_BACK, INPUT_BIND_PRESS_EDGE, 120,
      INPUT_BIND_CONSUME_EDGE + INPUT_BIND_OWNER_GATED + INPUT_BIND_CLEAR_ON_CONTEXT_CHANGE },
    { INPUT_CONTEXT_RELAY, HW_INPUT_L, HW_INPUT_NONE,
      INPUT_ACTION_RELAY_TAB_PREVIOUS, INPUT_BIND_PRESS_EDGE, 130,
      INPUT_BIND_CONSUME_EDGE + INPUT_BIND_OWNER_GATED + INPUT_BIND_CLEAR_ON_CONTEXT_CHANGE },
    { INPUT_CONTEXT_RELAY, HW_INPUT_R, HW_INPUT_NONE,
      INPUT_ACTION_RELAY_TAB_NEXT, INPUT_BIND_PRESS_EDGE, 130,
      INPUT_BIND_CONSUME_EDGE + INPUT_BIND_OWNER_GATED + INPUT_BIND_CLEAR_ON_CONTEXT_CHANGE },
    { INPUT_CONTEXT_BATTLE_COMMAND + INPUT_CONTEXT_BATTLE_TARGET, HW_INPUT_Z, HW_INPUT_NONE,
      INPUT_ACTION_BATTLE_MOVE_INFO, INPUT_BIND_PRESS_EDGE, 120,
      INPUT_BIND_CONSUME_EDGE + INPUT_BIND_OWNER_GATED + INPUT_BIND_CLEAR_ON_CONTEXT_CHANGE },
    { INPUT_CONTEXT_OPENING_SLATE, HW_INPUT_A, HW_INPUT_NONE,
      INPUT_ACTION_OPENING_SKIP, INPUT_BIND_PRESS_EDGE, 120,
      INPUT_BIND_CONSUME_EDGE + INPUT_BIND_OWNER_GATED + INPUT_BIND_CLEAR_ON_CONTEXT_CHANGE },
    { INPUT_CONTEXT_OPENING_SLATE, HW_INPUT_START, HW_INPUT_NONE,
      INPUT_ACTION_OPENING_SKIP, INPUT_BIND_PRESS_EDGE, 120,
      INPUT_BIND_CONSUME_EDGE + INPUT_BIND_OWNER_GATED + INPUT_BIND_CLEAR_ON_CONTEXT_CHANGE },
    { INPUT_CONTEXT_RECONNECT_TRANSFER, HW_INPUT_START, HW_INPUT_NONE,
      INPUT_ACTION_RECONNECT_TRANSFER, INPUT_BIND_PRESS_EDGE, 255,
      INPUT_BIND_CONSUME_EDGE + INPUT_BIND_OWNER_GATED + INPUT_BIND_CLEAR_ON_CONTEXT_CHANGE }
};

static const PlayerMotionTuningDef PLAYER_MOTION_TUNING[1] = {
    { 1, 384, 704, 1536, 2048, 46080, 3277, 2458, 22937, 19660, 2304, 3072 }
};

static const CollisionTuningDef COLLISION_TUNING[1] = {
    { 1, 72, 384, 4, 64, 23170, 12, 152, 768, 4, 4,
      COLLISION_CAPSULE_SWEEP + COLLISION_SLIDE_ON_BLOCK +
      COLLISION_STEP_REQUIRES_TOP_CLEARANCE +
      COLLISION_DOOR_REQUIRES_FULL_CAPSULE_CLEARANCE +
      COLLISION_RECOVER_TO_ZONE_SAFE_ANCHOR + COLLISION_GENERATION_BOUND, 0, 0 }
};

static const CameraTuningDef CAMERA_TUNING[1] = {
    { 1, 30720, -8960, 14080, 896, 384, 1152, 320, 32,
      6, 6, 8, 6, CAMERA_USE_SPHERE_SWEEP +
      CAMERA_PULL_IN_BEFORE_OCCLUSION + CAMERA_NEVER_PUSH_THROUGH_BLOCKER +
      CAMERA_GENERATION_BOUND, 1, 256 }
};

static const CameraVolumeDef CAMERA_VOLUMES[11] = {
    { 1,  ZONE_ANNEX_SIMULATION_ROOM,     1, 0, 0, 0,  768, 0,  8, 0x0003, 0x0029, 0 },
    { 2,  ZONE_ANNEX_ATRIUM,              2, 0, 0, 0, 1024, 0, 12, 0x0003, 0x0029, 0 },
    { 3,  ZONE_ANNEX_DIRECTOR_LAB,        3, 0, 0, 0,  768, 0,  8, 0x0003, 0x0029, 0 },
    { 4,  ZONE_ANNEX_PLAYER_ROOM,         4, 0, 0, 0,  704, 0,  8, 0x0003, 0x0029, 0 },
    { 5,  ZONE_ANNEX_CLINIC,              5, 0, 0, 0,  768, 0,  8, 0x0003, 0x0029, 0 },
    { 6,  ZONE_ANNEX_WORKSHOP,            6, 0, 0, 0,  768, 0,  8, 0x0003, 0x0029, 0 },
    { 7,  ZONE_ANNEX_THRESHOLD,           7, 0, 0, 0,  896, 0,  8, 0x0003, 0x0029, 0 },
    { 8,  ZONE_ESTATE_COURTYARD,          8, 0, 0, 0, 1024, 0, 12, 0x0003, 0x0029, 0 },
    { 9,  ZONE_ESTATE_FOYER,              9, 0, 0, 0,  768, 0,  8, 0x0003, 0x0029, 0 },
    { 10, ZONE_ESTATE_INVENTION_HALL,    10, 0, 0, 0,  896, 0, 10, 0x0003, 0x0029, 0 },
    { 11, ZONE_ESTATE_OBSERVATORY_STUDY, 11, 0, 0, 0,  768, 0,  8, 0x0003, 0x0029, 0 }
};

static const FollowerTuningDef FOLLOWER_TUNING[6] = {
    { ZONE_ESTATE_OBSERVATORY_STUDY, 1536, 8, 30, 45, 2, 16, 48, 0x003F,
      307, 410, 512, 448, 832, 1792, 2304, 192, 128, 55296, 2, 0, 0 },
    { ZONE_ESTATE_INVENTION_HALL,    2048, 8, 30, 45, 2, 16, 48, 0x003F,
      307, 410, 512, 448, 832, 1792, 2304, 192, 128, 55296, 2, 0, 0 },
    { ZONE_ESTATE_FOYER,             1536, 8, 30, 45, 2, 16, 48, 0x003F,
      307, 410, 512, 448, 832, 1792, 2304, 192, 128, 55296, 2, 0, 0 },
    { ZONE_ESTATE_COURTYARD,         2560, 8, 30, 45, 2, 16, 48, 0x003F,
      307, 410, 512, 448, 832, 1792, 2304, 192, 128, 55296, 2, 0, 0 },
    { ZONE_ANNEX_THRESHOLD,           1536, 8, 30, 45, 2, 16, 48, 0x003F,
      307, 410, 512, 448, 832, 1792, 2304, 192, 128, 55296, 2, 0, 0 },
    { ZONE_ANNEX_ATRIUM,              2048, 8, 30, 45, 2, 16, 48, 0x003F,
      307, 410, 512, 448, 832, 1792, 2304, 192, 128, 55296, 2, 0, 0 }
};
```

Raw stick magnitude uses integer square root over signed raw X/Y. Magnitude
`<=12` yields zero; `>=76` yields `32767`; between them, linear Q15
`n=((m-12)*32767+32)/64` is evaluated in unsigned widened arithmetic (round to
nearest, ties upward). With `Q=32767`, smoothstep is exactly
`num=(uint64_t)n*n*(3*Q-2*n)`, `den=(uint64_t)Q*Q`, then
`s=min(Q,(num+den/2)/den)`; rounding occurs once, after the full 64-bit
numerator is formed, and saturation occurs only after that division. The shaped
magnitude `s` is then multiplied by the normalized radial direction with the
ordinary signed Q15 vector multiply. Required goldens are
`m=12 -> n=0 -> s=0`, `m=44 -> n=16384 -> s=16384`, and
`m=76 -> n=32767 -> s=32767`; the endpoint branches run before the interior
formula. UI direction enters at `18022` and does not
release until below `13107`; the first repeat is tick 12 and later repeats every
4 held ticks. Disconnect emits neutral state and clears held/repeat/edge epochs;
reconnect samples one full poll for state but emits no edge until the next poll.

When no active port is bound, platform enrollment runs before every logical
context and is the sole consumer of claim input. Only a new Start or A edge on
connected ports is eligible; candidates sort by lower port then Start before A.
The winner binds that port, consumes the claim edge, clears every port/context/
repeat latch, and discards one complete subsequent hardware poll. No logical
context is published until that discard poll finishes, so a claiming A cannot
also confirm Title/New Game and claiming Start cannot Pause/skip. Reconnect is a
different retained-owner path: the original port may resume under the neutral/
discard policy, while transferring to another port requires the overlay's Start
action; A never transfers. Enrollment and transfer generations cannot consume
one another's edge.

`HARDWARE_INPUT_BINDINGS` is the complete N64 hardware-to-logical-action
contract. Exactly one primary context bit is current; reconnect transfer
temporarily replaces it. Ambiguous/no primary ownership emits no action and is a
debug assertion. Exploration maps stick vector to movement, A press/hold to
interaction ownership, held B to Run, C-Left/Right to yaw, held
L+C-Up/C-Down to pitch, and bare C-Down press to Relay. Start press maps to
Pause from stable exploration or a battle command/target-selection safe boundary;
the owner gate rejects it during battle action/presentation/result phases. Dialogue maps
A press alone to reveal/advance. Name Grid uses repeated stick/D-pad directions,
A selection, B Delete, and Start Confirm. Menu, Relay, Map, and both battle
selection contexts use repeated stick/D-pad directions, A Confirm, and B Back;
Relay additionally consumes L/R for previous/next tabs, and battle command/
target consumes Z for Move Info. Only the slate maps A/Start to Skip; only the
reconnect overlay maps Start to controller transfer.

Rows are filtered by the single context, chord state from the same hardware
poll, and owner capability, then sorted by priority descending. One press-edge
source may produce and consume at most one logical edge. Held samples are
separate and may coexist only on the A interaction press/hold pair explicitly
flagged for it. Context/owner changes clear held-repeat/edge state and discard a
poll. Thus held B can Run in exploration but cannot become Back after Pause
opens, and menu B cannot Run. For C-Down, priority 200 L-chord pitch is resolved
before priority 100 bare Relay; `REQUIRE_CHORD_RELEASED` makes bare Relay
illegal whenever L is held. The chord snapshot is fixed for that poll/press, so
one C-Down press cannot both tilt and open Relay. Camera Invert X swaps the
logical yaw sign only after binding; Invert Y does the same for pitch. No other
context or hard-coded button fallback exists.

Digital camera repeat is immediate and exactly once per fixed tick. C-Left/
C-Right apply `1024` degree-Q8 (4 degrees) per tick, or 120 degrees/second;
held L+C-Up/C-Down apply `512` degree-Q8 (2 degrees) per tick, or 60
degrees/second. Bare C-Up has no action. Pitch is clamped before desired-pose
smoothing; yaw wraps normally. Controller loss, camera-token takeover, scene/
context change, or opening Relay clears the held camera action before another
tick. `CameraInputTuningDef.yaw_speed_deg_q8` must equal
`CameraTuningDef.yaw_speed_deg_q8`; the latter remains the camera authority and
the input field is a generator-checked equality mirror. Each speed must also
equal its per-tick step times 30, so an alternate continuous speed cannot
coexist with the literal digital step.

Motion is camera-relative on the ground plane. It starts above `3277`, stops
below `2458`, enters Run at `22937`, and leaves Run below `19660`; acceleration,
deceleration, yaw, gravity, and fall speed use saturating fixed-point integration
in the literal row. Collision performs one capsule sweep, at most four ordered
penetration solves and four motion substeps, then slides. A step of at most
`64/256 m` succeeds only with full top/landing clearance; floor normals below
Q15 cosine `23170` are too steep. Doors require `152/256 m` clearance. Falling
more than `768/256 m` below the last grounded point or leaving collision bounds
fences movement, validates the same zone generation, and restores the exact
`ZoneBindingDef.safe_anchor_spawn_id`; it never advances story or chooses a
different room.

Exploration camera is a 3.5 m orbit with -35/+55 degree pitch limits, a 1.25 m
target height, and the literal smoothing ticks. It sphere-sweeps radius 0.125 m
from target to desired eye against blocker mask bits before every reveal; hit
distance pulls in to contact minus skin and never pushes through a blocker.
`col.common.camera_volumes` compiles exactly the eleven literal zone-default
orbit rows above (Annex Sim, Atrium, Director Lab, Player Room, Clinic,
Workshop, Threshold, Estate Courtyard, Foyer, Invention Hall, Study). Each
source volume is one authored convex room volume with no rail and no secondary
fallback; the global orbit tuning is its fallback. All rows use blocker mask
`WORLD+DOOR` and flags exactly `ORBIT + BLOCKER_COLLISION +
SAFE_GENERATION_OWNER` (`0x0029`). Overlap is impossible across current zone
ownership; within a malformed asset it would choose higher priority then lower
volume ID, and equal current priorities would expose the duplicate as a build
failure. Asset export must prove exact set equality with these eleven rows,
convex containment data, blocker flags, and generation ownership before a scene
can publish. Additional rails/subvolumes require a reviewed data-table revision;
runtime cannot invent them.

Gameplay camera smoothing is a restartable finite interpolation, not an
implementation-selected low-pass filter. Desired yaw, pitch, and distance are
clamped/wrapped first. For each scalar, a desired-value change captures the
current solved value as `start`, the new value as `target`, sets `elapsed=0`, and
uses its literal duration (`6/6/8` ticks). Target-position X/Y/Z does the same in
Q16.16 for 6 ticks. At tick `k=1..duration`, with widened signed
`delta=target-start`, compute
`step=sign(delta)*((abs(delta)*k + duration/2)/duration)` and
`solved=start+step`; ties round away from zero, addition saturates in the native
signed type, and the final tick assigns the exact target. No intermediate
feedback is fed into the equation. Yaw first chooses the shortest delta in the
half-open degree-Q8 range `[-46080,46080)`; exactly +180 degrees therefore uses
-180. If a scalar delta is at most `1` Q8, or every target-vector component is
at most `256` Q16, it snaps before allocating a smoothing owner. Collision pull-
in is applied after the interpolated desired eye and does not rewrite the
distance smoother.

Required scalar goldens are yaw `0 -> 7680` over 6 ticks:
`k1=1280,k3=3840,k6=7680`; pitch `-2560 -> 5120` over 6:
`k1=-1280,k3=1280,k6=5120`; distance `896 -> 512` over 8:
`k1=848,k4=704,k8=512`. Required Q16 target-component golden is
`0 -> 65536` over 6: `k1=10923,k3=32768,k6=65536`. A new desired value,
camera-token transfer, or generation change restarts/cancels with the current
solved pose; stale interpolation ticks cannot write a newer camera owner.

Follower simulation exists in exactly the six rows above; the World Map carries
only a handoff snapshot and no live follower actor. Every row repeats the same
normal-follow feel values and generation rejects disagreement: min/target/max
trail distance is `307/410/512` Q8 (approximately 1.2/1.6/2.0 m), walk/run cap
is `448/832` Q8 (1.75/3.25 m/s), acceleration/deceleration is `1792/2304`
Q8, turn cap is `55296` degree-Q8 (216 degrees/s), steering/yield radius is
`192` Q8 (0.75 m), and portal wait threshold is `128` Q8 (0.5 m).

Each fixed tick first chooses the reachable offset node/point nearest the exact
1.6 m point behind the player's solved facing, ties by path cost then node ID.
A candidate whose swept follower capsule enters the 0.75 m player/mandatory-
interaction yield disc is rejected; if all candidates reject, target speed is
zero and Tavi turns/yields in place. Player separation below the 1.2 m minimum
also targets zero speed. At or below 2.0 m the legal offset uses the 1.75 m/s
walk cap; above 2.0 m it uses the 3.25 m/s run cap. Velocity approaches that cap
by exactly `round(1792/30)=60` Q8 per tick and returns toward zero by
`round(2304/30)=77` Q8 per tick, saturating without overshoot. Facing approaches
the steering direction by at most `round(55296/30)=1843` degree-Q8 per tick on
the shortest arc. Required goldens from rest are walk velocity
`0,60,120,...,420,448` over eight ticks and run `0,60,...,780,832` over
fourteen; deceleration from walk is `448,371,294,217,140,63,0`.

At a door/portal source handoff, entering 0.5 m of its anchor forces the authored
wait pose and zero target speed. It never opens the door or submits a transition.
Only after the door is open, destination nav generation and paired destination
anchor are current, and those facts remain stable for exactly two fixed ticks
may the transition owner capture the follower handoff token and unload the old
zone. The destination reconstructs Tavi at that paired anchor before follower
simulation resumes. A generation change resets the two-tick proof; there is no
timeout teleport.

Recovery requires both
distance above the row threshold for all 45 fixed ticks and path progress less
than `8/256 m` for at least 30 ticks. It then selects a same-component
`NAV_NODE_RECOVERY` behind the player by lowest path cost then node ID, within a
48-node bounded search, with capsule/camera/door clearance. Both follower and
anchor capsules must remain outside the camera frustum expanded by 16 pixels for
two consecutive rendered frames and have blocker-occluded line of sight before
the next fixed-step recovery. Scene/follower/camera generation change,
transition, Pause/modal, regained path progress, visibility, or threshold drop
cancels the pending recovery and resets both timers. There is no on-camera
teleport or cross-door/zone recovery.

## 3. Cast, story flags, and objectives

### 3.1 Character IDs

```c
typedef enum CharacterIdValue {
    CHAR_NONE          = 0,
    CHAR_PLAYER        = 1,
    CHAR_TAVI          = 2,
    CHAR_DR_SERA_VENN  = 3,
    CHAR_OREN_SAYE     = 4,
    CHAR_IVO_VEYRA     = 5,
    CHAR_RUSK          = 6,
    CHAR_MARA_OVELLE   = 7,
    CHAR_JO_RENN       = 8,
    CHAR_PELL_ANWAR    = 9
} CharacterIdValue;
```

The player's display name is save data, not a separate character ID. `CHAR_PLAYER` resolves to that string; all other names resolve through `StringId`.

```c
typedef struct CharacterDef {
    CharacterId id;                   /* 0 */
    StringId name_string_id;          /* 2 */
    AssetId model_asset_id;           /* 4 */
    AssetId portrait_asset_id;        /* 6 */
    AnimationSetId animation_set_id;  /* 8 */
    AudioCueId voice_bank_id;         /* 10 */
    uint16_t flags;                   /* 12 */
    uint16_t scale_q8;                /* 14 */
    uint16_t capsule_radius_q8;       /* 16 */
    uint16_t capsule_height_q8;       /* 18 */
    uint16_t interact_radius_q8;      /* 20 */
    uint16_t default_emote;           /* 22 */
    uint8_t skeleton_bone_count;      /* 24 */
    uint8_t max_vertex_influences;    /* 25; must equal 1 for Tiny3D export */
    uint8_t material_count;           /* 26 */
    uint8_t lod_count;                /* 27 */
    uint8_t portrait_base_region;     /* 28: human atlas region 0..8 */
    uint8_t expression_first_region;  /* 29: 9..20, or 0xFF when none */
    uint8_t expression_region_count;  /* 30 */
    uint8_t reserved;                 /* 31 */
} CharacterDef;
_Static_assert(sizeof(CharacterDef) == 32, "CharacterDef layout");

enum CharacterFlags {
    CHARACTER_PLAYER = 1u << 0,
    CHARACTER_FOLLOWER = 1u << 1,
    CHARACTER_REQUIRED_STORY = 1u << 2,
    CHARACTER_OPTIONAL_SUPPORT = 1u << 3
};

typedef enum OpeningCharacterModelAssetIdValue {
    ASSET_MODEL_CHR_PLAYER_ARI = 0x7401,
    ASSET_MODEL_CHR_TAVI = 0x7402,
    ASSET_MODEL_CHR_SERA_VENN = 0x7403,
    ASSET_MODEL_CHR_OREN_SAYE = 0x7404,
    ASSET_MODEL_CHR_IVO_VEYRA = 0x7405,
    ASSET_MODEL_CHR_RUSK = 0x7406,
    ASSET_MODEL_CHR_MARA_OVELLE = 0x7407,
    ASSET_MODEL_CHR_JO_RENN = 0x7408,
    ASSET_MODEL_CHR_PELL_ANWAR = 0x7409,
    ASSET_UI_PORTRAITS_HUMANS = 0x740A
} OpeningCharacterModelAssetIdValue;

typedef enum OpeningCharacterAnimationSetIdValue {
    ANIMSET_PLAYER_ARI = 0x7501,
    ANIMSET_TAVI = 0x7502,
    ANIMSET_SERA_VENN = 0x7503,
    ANIMSET_OREN_SAYE = 0x7504,
    ANIMSET_IVO_VEYRA = 0x7505,
    ANIMSET_RUSK = 0x7506,
    ANIMSET_MARA_OVELLE = 0x7507,
    ANIMSET_JO_RENN = 0x7508,
    ANIMSET_PELL_ANWAR = 0x7509
} OpeningCharacterAnimationSetIdValue;

typedef enum OpeningCharacterNameStringIdValue {
    STR_NAME_TAVI = 0x7601,
    STR_NAME_SERA_VENN = 0x7602,
    STR_NAME_OREN_SAYE = 0x7603,
    STR_NAME_IVO_VEYRA = 0x7604,
    STR_NAME_RUSK = 0x7605,
    STR_NAME_MARA_OVELLE = 0x7606,
    STR_NAME_JO_RENN = 0x7607,
    STR_NAME_PELL_ANWAR = 0x7608
} OpeningCharacterNameStringIdValue;
```

The source validator reads exported GLB data and requires exactly one bone influence for every skinned exported vertex. `max_vertex_influences` must be `1`; it is evidence metadata, not a runtime workaround. Vertex duplication/splitting by the approved exporter must preserve the reviewed deformation and budget.

All nine characters are text-only in this slice, so `voice_bank_id=0`. Models map one-to-one to the exact inventory packages `chr.player.ari`, `chr.tavi`, `chr.sera_venn`, `chr.oren_saye`, `chr.ivo_veyra`, `chr.rusk`, `chr.mara_ovelle`, `chr.jo_renn`, and `chr.pell_anwar`; animations map to their matching `anm.*` rows. Every row references the single `ASSET_UI_PORTRAITS_HUMANS` asset sourced from `ui.portraits.humans`. Atlas regions 0-8 are bases in CharacterId order; expression regions 9-20 are assigned contiguously and never inferred at runtime.

| CharacterId | Name StringId | Model / portrait base + expressions / animation / voice | Flags | Scale / capsule radius,height / interact | Bones / influences / materials / LODs |
|---|---|---|---|---|---|
| `CHAR_PLAYER` | `0` (dynamic saved name) | `ASSET_MODEL_CHR_PLAYER_ARI` / atlas `0`, expr `9..10` / `ANIMSET_PLAYER_ARI` / `0` | `CHARACTER_PLAYER + CHARACTER_REQUIRED_STORY` | `256 / 72,384 / 384` | `24 / 1 / 3 / 2` |
| `CHAR_TAVI` | `STR_NAME_TAVI` | `ASSET_MODEL_CHR_TAVI` / atlas `1`, expr `11..12` / `ANIMSET_TAVI` / `0` | `CHARACTER_FOLLOWER + CHARACTER_REQUIRED_STORY` | `256 / 64,320 / 352` | `22 / 1 / 3 / 2` |
| `CHAR_DR_SERA_VENN` | `STR_NAME_SERA_VENN` | `ASSET_MODEL_CHR_SERA_VENN` / atlas `2`, expr `13..14` / `ANIMSET_SERA_VENN` / `0` | `CHARACTER_REQUIRED_STORY` | `256 / 72,416 / 384` | `22 / 1 / 3 / 1` |
| `CHAR_OREN_SAYE` | `STR_NAME_OREN_SAYE` | `ASSET_MODEL_CHR_OREN_SAYE` / atlas `3`, expr `15` / `ANIMSET_OREN_SAYE` / `0` | `CHARACTER_REQUIRED_STORY` | `256 / 80,400 / 384` | `22 / 1 / 3 / 1` |
| `CHAR_IVO_VEYRA` | `STR_NAME_IVO_VEYRA` | `ASSET_MODEL_CHR_IVO_VEYRA` / atlas `4`, expr `16` / `ANIMSET_IVO_VEYRA` / `0` | `CHARACTER_REQUIRED_STORY` | `256 / 72,400 / 384` | `24 / 1 / 3 / 1` |
| `CHAR_RUSK` | `STR_NAME_RUSK` | `ASSET_MODEL_CHR_RUSK` / atlas `5`, expr `17..18` / `ANIMSET_RUSK` / `0` | `CHARACTER_REQUIRED_STORY` | `256 / 80,400 / 384` | `22 / 1 / 3 / 1` |
| `CHAR_MARA_OVELLE` | `STR_NAME_MARA_OVELLE` | `ASSET_MODEL_CHR_MARA_OVELLE` / atlas `6`, no expressions (`0xFF,0`) / `ANIMSET_MARA_OVELLE` / `0` | `CHARACTER_OPTIONAL_SUPPORT` | `256 / 68,360 / 352` | `18 / 1 / 2 / 1` |
| `CHAR_JO_RENN` | `STR_NAME_JO_RENN` | `ASSET_MODEL_CHR_JO_RENN` / atlas `7`, expr `19` / `ANIMSET_JO_RENN` / `0` | `CHARACTER_REQUIRED_STORY` | `256 / 72,376 / 368` | `20 / 1 / 3 / 1` |
| `CHAR_PELL_ANWAR` | `STR_NAME_PELL_ANWAR` | `ASSET_MODEL_CHR_PELL_ANWAR` / atlas `8`, expr `20` / `ANIMSET_PELL_ANWAR` / `0` | `CHARACTER_REQUIRED_STORY` | `256 / 68,368 / 368` | `18 / 1 / 2 / 1` |

`CHAR_PLAYER.name_string_id` must be zero and its display name always comes from the validated save buffer. Every NPC name ID above must resolve to the exact displayed name and may not be zero. The generator checks portrait ranges are nonoverlapping and cover exactly 9 bases plus 12 expressions, and that every count matches the inventory package. In the table, all dimensions are Q8.8 integers and `default_emote=0` for every row.

### 3.2 Saved story flags

The save reserves 128 bits. These first 23 indices are locked:

```c
typedef enum StoryFlagIndex {
    FLAG_OPENING_CINEMATIC_SEEN        = 0,
    FLAG_PLAYER_NAME_CONFIRMED         = 1,
    FLAG_TUTORIAL_COMPLETE             = 2,
    FLAG_ANNEX_INTRO_COMPLETE          = 3,
    FLAG_STARTER_TEAM_RECEIVED         = 4,
    FLAG_FIELD_RELAY_QUEST_STARTED     = 5,
    FLAG_FIELD_RELAY_UNLOCKED          = 6,
    FLAG_TAVI_MISSING_REPORTED         = 7,
    FLAG_ESTATE_DESTINATION_UNLOCKED   = 8,
    FLAG_ANNEX_EXIT_CLEARED            = 9,
    FLAG_ESTATE_ARRIVED                = 10,
    FLAG_RUSK_CONFRONTATION_SEEN       = 11,
    FLAG_RUSK_BATTLE_WON               = 12,
    FLAG_RUSK_BATTLE_REWARD_CLAIMED    = 13,
    FLAG_ESTATE_DOOR_OPEN              = 14,
    FLAG_IVO_MET                       = 15,
    FLAG_TAVI_FOUND                    = 16,
    FLAG_TAVI_RETURNED_TO_ANNEX        = 17,
    FLAG_RETURN_TO_ANNEX_REQUESTED     = 18,
    FLAG_SOLACE_BEACON_RECEIVED        = 19,
    FLAG_FRACTURE_SIGNAL_SEEN          = 20,
    FLAG_SLICE_COMPLETE                = 21,
    FLAG_ORRERY_STAIR_OPEN             = 22,
    STORY_FLAG_LOCKED_COUNT            = 23,
    STORY_FLAG_CAPACITY                = 128
} StoryFlagIndex;

typedef struct StoryFlagSet {
    uint32_t words[4]; /* 0 */
} StoryFlagSet;
_Static_assert(sizeof(StoryFlagSet) == 16, "StoryFlagSet layout");
```

Serialization writes bits in index order: flag `n` is bit `(n & 7)` of payload byte `(n >> 3)`, least-significant bit first within that byte. Runtime word order is irrelevant to the codec. Optional NPC and examine one-shots use separate saved bitsets and cannot gate the mandatory story.

The locked bit golden for `FLAG_ORRERY_STAIR_OPEN` is payload story-flag byte 2 mask `0x40`. A set containing all locked indices `0..22` encodes the first three story-flag bytes as `FF FF 7F` and the remaining thirteen bytes as zero. Host and target codec tests compare this byte sequence exactly.

Required implications checked after decode and after every story transaction include:

- every initialized persistent page implies `opening_cinematic_seen` and `player_name_confirmed`;
- `starter_team_received` implies party count exactly two, slots exactly `ECHO_QUARRUNE` then `ECHO_AYSELOR`, and those two distinct living slots active;
- `field_relay_unlocked` implies `field_relay_quest_started`;
- `estate_destination_unlocked` implies both `field_relay_unlocked` and `tavi_missing_reported`;
- `rusk_battle_reward_claimed` implies `rusk_battle_won`.
- `estate_door_open` implies both `rusk_battle_won` and `rusk_battle_reward_claimed`;
- `orrery_stair_open` implies `estate_door_open`; `tavi_found` implies `orrery_stair_open`;
- `tavi_returned_to_annex` implies `tavi_found`, `ivo_met`, `estate_door_open`, `return_to_annex_requested`, and `OBJ_RETURN_WITH_TAVI == OBJECTIVE_COMPLETE`;
- `solace_beacon_received` implies `tavi_found` and `tavi_returned_to_annex`, proving the completed return transition rather than merely its request;
- `slice_complete` implies `tutorial_complete`, `rusk_battle_won`, `tavi_found`, `solace_beacon_received`, and `fracture_signal_seen`;
- any persisted `tutorial_complete` implies `starter_team_received`; `CHECKPOINT_AFTER_TUTORIAL` writes tutorial completion and starter acquisition as one validated transaction, so no journal page can contain half-applied onboarding.

An invalid implication does not get guessed into validity. The decoder rejects that page and tries the other journal page; debug tooling reports the first violated rule.

`FLAG_ORRERY_STAIR_OPEN` is monotonic and has one legal set point. `INT_ORRERY_SWITCH` begins a hold transaction with the flag still false and the study-stair nav edge/collision portal still blocked. The action may set the flag only after the required hold completes and the switch animation, orrery-arm clearance, open stair pose, replacement collision, and study-stair nav edge are all staged and can publish coherently in one commit. Release, interruption, or controller disconnect before that commit cancels the transaction, restores the released switch and blocked arm pose, leaves the nav/collision portal blocked, and leaves the flag false. Saves are forbidden from press through cancellation/commit cleanup. Stable zone entry and manual-save reconstruction choose the open mechanism pose, open collision, and enabled stair edge iff the flag is true; no transient animation time is serialized. `TRANS_DEF_HALL_TO_STUDY` tests this exact flag, and persistent `tavi_found` without it is invalid.

`tavi_following` is derived runtime state, not a saved monotonic flag: it is true only while the return objective is active, `return_to_annex_requested && tavi_found && !tavi_returned_to_annex`, and the current zone has a valid follower nav/handoff definition. `RETURN_005` sets `FLAG_TAVI_RETURNED_TO_ANNEX` only after the Annex atrium entry is coherent; follower runtime state then becomes false.

Generated condition `COND_TRANS_RETURN_FOLLOWER_ACTIVE` is exactly that derived predicate, including the active Return objective and a valid current-zone handoff definition. The transition table uses explicit `== false` and `== true` tests of this one boolean so overlapping triggers are exhaustive and mutually exclusive.

Saved bit assignments are also stable:

```c
typedef enum DestinationBit {
    DESTINATION_ANNEX_BIT = 0,
    DESTINATION_ESTATE_BIT = 1
} DestinationBit;

typedef enum RelayPageBit {
    RELAY_PARTY_BIT = 0,
    RELAY_MESSAGES_BIT = 1,
    RELAY_RESONANCE_BIT = 2,
    RELAY_MAP_BIT = 3
} RelayPageBit;

typedef enum RewardClaimBit {
    REWARD_RUSK_FIRST_WIN_BIT = 0
} RewardClaimBit;
```

The Annex destination is set for every initialized save. The Estate bit requires `estate_destination_unlocked`; all four Relay page bits require `field_relay_unlocked`. Encounter-clear bit `n` corresponds to `EncounterId n` for IDs 1-63.

### 3.3 Objective IDs and states

```c
typedef enum ObjectiveIdValue {
    OBJ_NONE                 = 0,
    OBJ_RETRIEVE_FIELD_RELAY = 1,
    OBJ_FIND_TAVI            = 2,
    OBJ_RETURN_WITH_TAVI     = 3,
    OBJ_OPENING_COMPLETE     = 4,
    OBJ_CAPACITY             = 8
} ObjectiveIdValue;

typedef enum ObjectiveStateValue {
    OBJECTIVE_LOCKED   = 0,
    OBJECTIVE_ACTIVE   = 1,
    OBJECTIVE_COMPLETE = 2,
    OBJECTIVE_FAILED   = 3
} ObjectiveStateValue;
```

Opening objectives only move `LOCKED -> ACTIVE -> COMPLETE`; `FAILED` is reserved for future optional objectives and never used to block this chapter. The save holds eight one-byte states.

Only one mandatory objective may be active. `OBJ_RETRIEVE_FIELD_RELAY` remains active through Jo's acquisition and its `Ask Pell to trace Tavi's message.` substage. Dismissing `SERA_RELAY_002` atomically sets `FLAG_TAVI_MISSING_REPORTED`, completes that objective, and starts `OBJ_FIND_TAVI`; `PELL_TRACE_004` then sets `FLAG_ESTATE_DESTINATION_UNLOCKED`. No checkpoint may contain both required objectives active or Estate unlocked before the Relay objective handoff.

`quest_counters[0]` is the locked Relay substage: `0` not started, `1` collect from Jo, `2` ask Pell, `3` Sera handoff complete. `FLAG_FIELD_RELAY_QUEST_STARTED` requires `>=1`; `FLAG_FIELD_RELAY_UNLOCKED` requires `>=2`; `FLAG_TAVI_MISSING_REPORTED` requires exactly `3`. Values 4-255 are invalid in this chapter.

`JO_RELAY_003` is presentation-only: it previews the linked Relay UI while the acquisition modal owns input and changes no persistent flag, page bit, objective state, or quest counter. Dismissal of `JO_RELAY_006` is the sole unlock set point. One story transaction sets `FLAG_FIELD_RELAY_UNLOCKED`, sets `quest_counters[0]=2`, sets all four Relay page bits, keeps `OBJ_RETRIEVE_FIELD_RELAY` as the sole active objective, and makes its player-facing step `Ask Pell to trace Tavi's message.` Player-owned Relay surfaces become available only after that transaction commits. The automatic `CHECKPOINT_FIELD_RELAY` write is requested later, after the workshop has returned to stable exploration with no dialogue, animation, or transition action pending.

```c
typedef struct ObjectiveDef {
    ObjectiveId id;                       /* 0 */
    StringId title_string_id;             /* 2 */
    StringId description_string_id;       /* 4 */
    ConditionId activate_condition_id;    /* 6 */
    ConditionId complete_condition_id;    /* 8 */
    StoryActionListId on_start_action_xref; /* 10: equality-only */
    StoryActionListId on_complete_action_xref; /* 12 */
    CharacterId marker_character_id;      /* 14 */
    ZoneId marker_zone_id;                /* 16 */
    uint16_t flags;                       /* 18 */
} ObjectiveDef;
_Static_assert(sizeof(ObjectiveDef) == 20, "ObjectiveDef layout");

enum ObjectiveFlags {
    OBJECTIVE_MANDATORY = 1u << 0,
    OBJECTIVE_VISIBLE_WHEN_ACTIVE = 1u << 1,
    OBJECTIVE_HAS_WORLD_MARKER = 1u << 2
};

typedef enum ObjectiveRuntimeStringIdValue {
    STR_OBJ_RELAY_TITLE = 0x6C01,
    STR_OBJ_RELAY_DESC = 0x6C02,
    STR_OBJ_FIND_TAVI_TITLE = 0x6C03,
    STR_OBJ_FIND_TAVI_DESC = 0x6C04,
    STR_OBJ_RETURN_TITLE = 0x6C05,
    STR_OBJ_RETURN_DESC = 0x6C06,
    STR_OBJ_OPENING_COMPLETE_TITLE = 0x6C07,
    STR_OBJ_OPENING_COMPLETE_DESC = 0x6C08,
    STR_OBJ_RELAY_COLLECT_FROM_JO_DESC = 0x6C09,
    STR_OBJ_RELAY_ASK_PELL_DESC = 0x6C0A
} ObjectiveRuntimeStringIdValue;

typedef enum ObjectiveConditionIdValue {
    COND_OBJ_RELAY_ACTIVE = 0x6110,
    COND_OBJ_RELAY_COMPLETE = 0x6111,
    COND_OBJ_FIND_TAVI_ACTIVE = 0x6112,
    COND_OBJ_FIND_TAVI_COMPLETE = 0x6113,
    COND_OBJ_RETURN_ACTIVE = 0x6114,
    COND_OBJ_RETURN_COMPLETE = 0x6115,
    COND_OBJ_OPENING_ACTIVE = 0x6116,
    COND_OBJ_OPENING_COMPLETE = 0x6117
} ObjectiveConditionIdValue;

typedef struct ObjectiveSubstageDef {
    ObjectiveId objective_id;       /* 0 */
    uint8_t counter_index;          /* 2: quest_counters[] */
    uint8_t minimum_value;          /* 3: inclusive */
    uint8_t maximum_value;          /* 4: inclusive */
    uint8_t reserved0;              /* 5 */
    StringId description_string_id; /* 6 */
    CharacterId marker_character_id;/* 8 */
    ZoneId marker_zone_id;          /* 10 */
    uint16_t flags;                 /* 12 */
} ObjectiveSubstageDef;
_Static_assert(sizeof(ObjectiveSubstageDef) == 14, "ObjectiveSubstageDef layout");

enum ObjectiveSubstageFlags {
    OBJECTIVE_SUBSTAGE_VISIBLE = 1u << 0,
    OBJECTIVE_SUBSTAGE_HAS_WORLD_MARKER = 1u << 1
};
```

The complete four-row ObjectiveDef table is literal; zero action IDs mean the owning dialogue/hook transaction performs the state change and ObjectiveDef must not emit a second action.

| ObjectiveId | Title / description StringId | Activate / complete ConditionId | Start / complete action | Marker CharacterId / ZoneId | Flags |
|---|---|---|---|---|---|
| `OBJ_RETRIEVE_FIELD_RELAY` | `STR_OBJ_RELAY_TITLE / STR_OBJ_RELAY_DESC` | `COND_OBJ_RELAY_ACTIVE / COND_OBJ_RELAY_COMPLETE` | `0 / 0` | `CHAR_JO_RENN / ZONE_ANNEX_WORKSHOP` | `OBJECTIVE_MANDATORY + OBJECTIVE_VISIBLE_WHEN_ACTIVE + OBJECTIVE_HAS_WORLD_MARKER` |
| `OBJ_FIND_TAVI` | `STR_OBJ_FIND_TAVI_TITLE / STR_OBJ_FIND_TAVI_DESC` | `COND_OBJ_FIND_TAVI_ACTIVE / COND_OBJ_FIND_TAVI_COMPLETE` | `0 / 0` | `CHAR_TAVI / ZONE_ESTATE_OBSERVATORY_STUDY` | `OBJECTIVE_MANDATORY + OBJECTIVE_VISIBLE_WHEN_ACTIVE + OBJECTIVE_HAS_WORLD_MARKER` |
| `OBJ_RETURN_WITH_TAVI` | `STR_OBJ_RETURN_TITLE / STR_OBJ_RETURN_DESC` | `COND_OBJ_RETURN_ACTIVE / COND_OBJ_RETURN_COMPLETE` | `0 / 0` | `CHAR_DR_SERA_VENN / ZONE_ANNEX_ATRIUM` | `OBJECTIVE_MANDATORY + OBJECTIVE_VISIBLE_WHEN_ACTIVE + OBJECTIVE_HAS_WORLD_MARKER` |
| `OBJ_OPENING_COMPLETE` | `STR_OBJ_OPENING_COMPLETE_TITLE / STR_OBJ_OPENING_COMPLETE_DESC` | `COND_OBJ_OPENING_ACTIVE / COND_OBJ_OPENING_COMPLETE` | `0 / 0` | `0 / ZONE_NONE` | `OBJECTIVE_MANDATORY` |

Objective flags accept only mask `0x0007`. `OBJECTIVE_HAS_WORLD_MARKER` requires both marker IDs nonzero; its absence requires both zero. Every string/condition/marker resolves, all four nonzero ObjectiveIds appear once, and reserved capacity slots 5-7 have no ObjectiveDef and cannot be condition/action subjects.

The Relay objective's complete substage override table has exactly two rows:

| ObjectiveId | counter index / inclusive range | Description StringId | Marker CharacterId / ZoneId | Flags / reserved |
|---|---|---|---|---|
| `OBJ_RETRIEVE_FIELD_RELAY` | `0 / 1..1` | `STR_OBJ_RELAY_COLLECT_FROM_JO_DESC` | `CHAR_JO_RENN / ZONE_ANNEX_WORKSHOP` | `OBJECTIVE_SUBSTAGE_VISIBLE + OBJECTIVE_SUBSTAGE_HAS_WORLD_MARKER / 0` |
| `OBJ_RETRIEVE_FIELD_RELAY` | `0 / 2..2` | `STR_OBJ_RELAY_ASK_PELL_DESC` | `CHAR_PELL_ANWAR / ZONE_ANNEX_ATRIUM` | `OBJECTIVE_SUBSTAGE_VISIBLE + OBJECTIVE_SUBSTAGE_HAS_WORLD_MARKER / 0` |

When an objective is active, the UI and marker resolver selects exactly one matching `(objective_id,counter_index,value-range)` row when present; otherwise it uses `ObjectiveDef`. Rows are sorted by `(objective_id,counter_index,minimum_value)`, ranges for one key cannot overlap, `minimum_value<=maximum_value`, and every range is reachable. Flags accept only `0x0003`; a world-marker row requires both marker IDs, and reserved is zero. Relay counter 0 therefore resolves Jo only at value 1 and Pell's authored atrium Relay balcony only at value 2. Values 0 and 3 have no active Relay presentation row because the objective is respectively locked or complete.

Persistent validation also enforces the following equivalences, not one-way hints:

- `active_objective_id==OBJ_NONE` iff no objective-state byte is `ACTIVE`; otherwise exactly one entry is `ACTIVE` and its index equals `active_objective_id`.
- `field_relay_quest_started && !tavi_missing_reported` means `OBJ_RETRIEVE_FIELD_RELAY` is the sole active objective (including its post-Jo `Ask Pell...` substage); `tavi_missing_reported` means that objective is complete.
- `tavi_missing_reported && !tavi_found` means `OBJ_FIND_TAVI` is sole active; `tavi_found` means Find is complete.
- `return_to_annex_requested && !tavi_returned_to_annex` means `OBJ_RETURN_WITH_TAVI` is sole active; `tavi_returned_to_annex` means Return is complete.
- Before the hook, `OBJ_OPENING_COMPLETE` is locked; the hook may activate it only in unsaved runtime, and `slice_complete` iff its persisted state is complete.
- Annex destination bit is always set. Estate destination bit is set iff `estate_destination_unlocked`.
- All four Relay page bits are set iff `field_relay_unlocked`; none is set before unlock.
- Rusk encounter-clear bit, `rusk_battle_won`, Rusk reward claim bit, `rusk_battle_reward_claimed`, and `estate_door_open` are equivalent in every stable page; there is no save between result/reward and the completed door animation. Team Link is 1 iff that claim is set in this chapter; otherwise it is 0.
- Because saving is forbidden during the hook, `solace_beacon_received`, `fracture_signal_seen`, and `slice_complete` are either all false (`CHECKPOINT_TAVI_RETURNED` or earlier) or all true (`CHECKPOINT_SLICE_COMPLETE`) in persistent data.

Any mismatch invalidates the page; validation never repairs it by setting a bit, completing an objective, or granting a reward.

## 4. Cutscene timeline data

Cutscene IDs are a tombstoned lock registry, not filenames. The opening slice has one cutscene definition; deleted future IDs remain reserved in `data/ids/cutscene_ids.lock`.

```c
typedef enum CutsceneIdValue {
    CUTSCENE_NONE = 0,
    CUTSCENE_OPENING_SOLACE = 1
} CutsceneIdValue;

enum {
    CUTSCENE_DEF_COUNT_MAX = 64,
    CUTSCENE_EVENTS_PER_TIMELINE_MAX = 96,
    CUTSCENE_EVENT_TABLE_MAX = 1024
};

typedef enum CutsceneSkipPolicyValue {
    CUTSCENE_SKIP_DISABLED = 0,
    CUTSCENE_SKIP_A_OR_START_IMMEDIATE = 1
} CutsceneSkipPolicyValue;

typedef enum CutsceneCallbackIdValue {
    CUTSCENE_CALLBACK_NONE = 0,
    CUTSCENE_CALLBACK_OPENING_FINISH = 1
} CutsceneCallbackIdValue;

enum CutsceneDefFlags {
    CUTSCENE_REALTIME_UI_SHELL = 1u << 0,
    CUTSCENE_MEDIA_FALLBACK_TO_TIMELINE = 1u << 1
};

typedef struct CutsceneDef {
    CutsceneId id;                         /* 0 */
    uint16_t first_event;                  /* 2 */
    uint16_t event_count;                  /* 4 */
    uint16_t duration_ticks;               /* 6: fixed 30 Hz presentation ticks */
    uint16_t skip_target_tick;             /* 8 */
    StoryActionListId finalizer_action_xref; /* 10; equality-only, 0 allowed */
    uint8_t skip_policy;                   /* 12: CutsceneSkipPolicyValue */
    uint8_t callback_id;                   /* 13: CutsceneCallbackIdValue */
    uint16_t flags;                        /* 14 */
} CutsceneDef;
_Static_assert(sizeof(CutsceneDef) == 16, "CutsceneDef layout");

typedef enum CutsceneEventType {
    CUT_EVENT_NONE          = 0,
    CUT_EVENT_CAMERA_CUT    = 1,
    CUT_EVENT_CAMERA_TWEEN  = 2,
    CUT_EVENT_ACTOR_BLOCK   = 3,
    CUT_EVENT_ACTOR_ANIM    = 4,
    CUT_EVENT_DIALOGUE      = 5,
    CUT_EVENT_FADE          = 6,
    CUT_EVENT_AUDIO         = 7,
    CUT_EVENT_VFX           = 8,
    CUT_EVENT_STORY_ACTION  = 9,
    CUT_EVENT_CONTROL       = 10,
    CUT_EVENT_TRANSITION    = 11,
    CUT_EVENT_LETTERBOX     = 12
} CutsceneEventType;

enum CutsceneEventFlags {
    CUT_EVENT_BLOCKING      = 1u << 0,
    CUT_EVENT_APPLY_ON_SKIP = 1u << 1,
    CUT_EVENT_CRITICAL      = 1u << 2,
    CUT_EVENT_RELATIVE      = 1u << 3
};

typedef struct CutsceneEvent {
    uint16_t tick;       /* 0: 30 Hz from timeline start */
    uint8_t type;        /* 2: CutsceneEventType */
    uint8_t flags;       /* 3 */
    uint16_t subject_id; /* 4: actor/camera/layer depending on type */
    uint16_t arg0;       /* 6: cue, duration, emote, or target */
    int16_t arg1;        /* 8: type-specific signed parameter */
    int16_t arg2;        /* 10: type-specific signed parameter */
    uint32_t data_id;    /* 12: StringId, AssetId, action list, or packed value */
} CutsceneEvent;
_Static_assert(sizeof(CutsceneEvent) == 16, "CutsceneEvent layout");
```

The complete `CutsceneDef` table is one row: `{ CUTSCENE_OPENING_SOLACE, 0, 3, 106, 106, 0, CUTSCENE_SKIP_A_OR_START_IMMEDIATE, CUTSCENE_CALLBACK_OPENING_FINISH, CUTSCENE_REALTIME_UI_SHELL + CUTSCENE_MEDIA_FALLBACK_TO_TIMELINE }`. Its complete event range is byte-for-byte equivalent to these three initializers; audio bus 6 is the nonblocking UI/story bus, RGBA8 `0x000000FF` is opaque black, and color index 0 is the black fade channel:

```c
static const CutsceneEvent CUTSCENE_OPENING_EVENTS[3] = {
    {  0, CUT_EVENT_FADE, CUT_EVENT_BLOCKING | CUT_EVENT_CRITICAL,
       UI_SCREEN_CUTSCENE_SLATE, 8, 1, 0, 0x000000FF },
    {  0, CUT_EVENT_AUDIO, CUT_EVENT_CRITICAL,
       6, AUDIO_CUE_STORY_SLATE_IN, 256, 0, 0 },
    { 98, CUT_EVENT_FADE, CUT_EVENT_BLOCKING | CUT_EVENT_CRITICAL,
       UI_SCREEN_CUTSCENE_SLATE, 8, 0, 0, 0x000000FF }
};
```

The loaded scene composition remains fully visible for ticks 8-97 inclusive. The future media path resolves the same ID and callback, falling back to these events.

Payload rules are exact and table-driven. `reserved` means the field must be numeric zero; `id` means the value must resolve in the named generated registry. A duration must be nonzero and `tick + duration <= CutsceneDef.duration_ticks` using widened arithmetic.

| Type | `subject_id` | `arg0` | `arg1` / `arg2` | `data_id` | Legal event flags |
|---|---|---|---|---|---|
| `CUT_EVENT_NONE` | 0 | 0 | 0 / 0 | 0 | 0; runtime queue sentinel only, illegal in authored ranges |
| `CUT_EVENT_CAMERA_CUT` | CameraCueId | blend ticks, including 0 | easing ID / 0 | target CharacterId or marker ID | permitted `CUT_EVENT_BLOCKING + CUT_EVENT_CRITICAL` |
| `CUT_EVENT_CAMERA_TWEEN` | source CameraCueId | nonzero duration ticks | easing ID / look-mode enum | destination CameraCueId | permitted `CUT_EVENT_BLOCKING + CUT_EVENT_CRITICAL + CUT_EVENT_RELATIVE` |
| `CUT_EVENT_ACTOR_BLOCK` | CharacterId | nonzero duration ticks | x / z offset Q8.8 | destination marker AssetId | permitted `CUT_EVENT_BLOCKING + CUT_EVENT_CRITICAL + CUT_EVENT_RELATIVE` |
| `CUT_EVENT_ACTOR_ANIM` | CharacterId | animation cue ID | blend ticks / loop count (`0` means once) | AnimationSetId override or 0 | permitted `CUT_EVENT_BLOCKING + CUT_EVENT_CRITICAL + CUT_EVENT_RELATIVE` |
| `CUT_EVENT_DIALOGUE` | CharacterId speaker | DialogueId | emote ID / hold ticks | StringId override or 0 | permitted `CUT_EVENT_BLOCKING + CUT_EVENT_CRITICAL` |
| `CUT_EVENT_FADE` | UIScreenId layer | nonzero duration ticks | direction `0=out,1=in` / color-index `0..15` | RGBA8 | permitted `CUT_EVENT_BLOCKING + CUT_EVENT_CRITICAL` |
| `CUT_EVENT_AUDIO` | audio bus `1..6` | AudioCueId | gain Q8.8 / pan Q1.14 | optional stop AudioCueId or 0 | permitted `CUT_EVENT_BLOCKING + CUT_EVENT_CRITICAL` |
| `CUT_EVENT_VFX` | CharacterId or marker ID | VFX cue ID | duration ticks / scale Q8.8 | AssetId | permitted `CUT_EVENT_BLOCKING + CUT_EVENT_CRITICAL + CUT_EVENT_RELATIVE` |
| `CUT_EVENT_STORY_ACTION` | StoryActionListId | 0 | 0 / 0 | 0 | permitted `CUT_EVENT_BLOCKING + CUT_EVENT_CRITICAL + CUT_EVENT_APPLY_ON_SKIP` |
| `CUT_EVENT_CONTROL` | generated control-owner ID | acquire `1` or release `2` | input-mask / 0 | 0 | permitted `CUT_EVENT_CRITICAL + CUT_EVENT_APPLY_ON_SKIP` |
| `CUT_EVENT_TRANSITION` | locked TransitionId | 0 | 0 / 0 | 0 | required `CUT_EVENT_BLOCKING`; additionally permitted `CUT_EVENT_CRITICAL`; style/save/destination come only from TransitionDef |
| `CUT_EVENT_LETTERBOX` | UIScreenId layer | nonzero duration ticks | target bar height `0..32` pixels / easing ID | RGBA8 | permitted `CUT_EVENT_BLOCKING + CUT_EVENT_CRITICAL + CUT_EVENT_APPLY_ON_SKIP` |

`CutsceneEvent.flags` accepts only mask `0x0F`, but each row must also satisfy the smaller required/permitted set above; unknown or disallowed bits fail. `CUT_EVENT_BLOCKING` holds timeline completion until that event's bounded presenter handle completes. `CUT_EVENT_CRITICAL` makes a missing/failed reference abort the cutscene through its finalizer/fallback path instead of logging and omitting presentation. `CUT_EVENT_RELATIVE` interprets authored transforms in the current subject/marker frame captured at event dispatch; without it they are absolute scene coordinates. `CUT_EVENT_STORY_ACTION` may use `CUT_EVENT_APPLY_ON_SKIP` only when the referenced list and every included operation satisfy the skip contract in section 8. A control/letterbox apply-on-skip event must be a release/zero-height cleanup, never an acquisition/show operation. A transition event always carries one locked `TransitionId`; a raw destination Scene/Zone/Spawn or duplicated style/save policy is invalid.

Generation requires `1..64` unique nonzero CutsceneIds, all present in the tombstoned lock, and a dense event table of at most 1024 rows. Each definition has `1..96` events; widened `first_event + event_count` must stay inside the table; ranges cannot overlap or leave referenced rows outside a definition. Events sort strictly by `(tick, source_index)`, occur inside duration, resolve every ID, obey payload/flag/zero rules, and cannot contain incompatible blocking overlaps or any transition before the finalizer point. `duration_ticks` and `skip_target_tick` are nonzero and the latter is at most duration. Definition flags accept only mask `0x0003`; unknown values in skip/callback enums or any missing `SceneDef.entry_cutscene_id`, `ACTION_START_CUTSCENE`, or event reference fail generation.

On accepted skip, the player advances only `APPLY_ON_SKIP` events in source order, then emits the typed finalizer trigger if `finalizer_action_xref` is nonzero, then invokes `callback_id` once. Natural completion uses the same order. StoryTriggerBinding is the only action dispatcher; the cutscene field is an equality-only cross-reference. Runtime generation plus `(CutsceneId,event source_index)` deduplicates event application; repeated skip/end callbacks cannot replay mutations or external requests.

### 4.1 Opening cinematic finalizer

```c
typedef enum OpeningCinematicFinishReason {
    OPENING_FINISH_NATURAL = 1,
    OPENING_FINISH_SKIP = 2,
    OPENING_FINISH_PLAYBACK_END = 3
} OpeningCinematicFinishReason;

enum OpeningFinishAudioFlags {
    OPENING_FINISH_AUDIO_NONBLOCKING = 1u << 0,
    OPENING_FINISH_AUDIO_SKIP_ONLY = 1u << 1
};

typedef struct OpeningFinishAudioDef {
    CutsceneId cutscene_id;  /* 0 */
    uint8_t finish_reason;   /* 2: OpeningCinematicFinishReason */
    uint8_t bus;             /* 3: 1..6 */
    AudioCueId cue_id;       /* 4 */
    uint16_t flags;          /* 6 */
} OpeningFinishAudioDef;
_Static_assert(sizeof(OpeningFinishAudioDef) == 8, "OpeningFinishAudioDef layout");

void opening_cinematic_finish(OpeningCinematicFinishReason reason);
```

The complete finish-audio table has one row: `{ CUTSCENE_OPENING_SOLACE,
OPENING_FINISH_SKIP, 6, AUDIO_CUE_STORY_SLATE_SKIP,
OPENING_FINISH_AUDIO_NONBLOCKING + OPENING_FINISH_AUDIO_SKIP_ONLY }`. The
callback owns this row: an accepted A/Start skip schedules the cue once before
timeline teardown/callback handoff, but never waits for it. Natural completion
and future-media playback end do not play the skip cue; the entry event already
played `AUDIO_CUE_STORY_SLATE_IN`. Unknown reasons, another cutscene, another
cue, flags outside `0x0003`, or a duplicate row fail generation.

The callback is idempotent per new-game opening generation. Natural slate timing is exactly 106 presentation ticks: 8 fade-in, 90 fully visible (3.0 seconds), and 8 fade-out. A/Start during any of the 106 ticks, including fade-in, full hold, or fade-out, performs safe immediate shutdown and finalization without waiting out the remainder. The callback records `FLAG_OPENING_CINEMATIC_SEEN` only in the uninitialized runtime draft, clears input edges, and enters name entry; it cannot request a save. After nonempty name confirmation and coherent simulation entry, `CHECKPOINT_AFTER_NAME` is the first persistent flag write. Controller loss may let the 106-tick presentation timeline finish, but name entry stays frozen and edge-cleared until reconnect.

The future replacement contract is exact: video `rom:/cinematic/opening_solace.video`, audio `rom:/audio/cinematic/opening_solace.audio`, timeline `rom:/data/cutscene/opening_solace.cut`, and callback `opening_cinematic_finish`. The `.video`/`.audio` payload formats are declared after measurement during future user-supplied video integration; Gate 9 is a media-free storyboard/handoff gate. The logical contract does not hard-code H.264 or WAV64. Missing/failed future media falls back to the same slate and finalizer contract.

### 4.2 Name-entry data and cancel path

```c
typedef enum NameEntryAction {
    NAME_ACTION_LETTER = 1,
    NAME_ACTION_DELETE = 2,
    NAME_ACTION_DEFAULT = 3,
    NAME_ACTION_CONFIRM = 4,
    NAME_ACTION_BACK = 5
} NameEntryAction;

typedef struct NameEntryDef {
    uint8_t min_length;              /* 0: 1 */
    uint8_t max_length;              /* 1: 8 */
    uint8_t default_length;          /* 2: 3 */
    uint8_t grid_item_count;         /* 3: 30 */
    char default_name[8];            /* 4: ARI + zero padding */
    StringId header_string_id;       /* 12 */
    StringId help_string_id;         /* 14 */
    StringId empty_string_id;        /* 16 */
    StringId confirm_string_id;      /* 18 */
    StringId cancel_string_id;       /* 20 */
    uint16_t flags;                  /* 22 */
} NameEntryDef;
_Static_assert(sizeof(NameEntryDef) == 24, "NameEntryDef layout");

enum NameEntryFlags {
    NAME_ENTRY_START_CONFIRMS_NONEMPTY = 1u << 0,
    NAME_ENTRY_B_DELETES_NONEMPTY_ONLY = 1u << 1,
    NAME_ENTRY_BACK_OPENS_CANCEL = 1u << 2
};

typedef enum NameEntryStringIdValue {
    STR_NAME_ENTRY_HEADER = 0x6D01,
    STR_NAME_ENTRY_HELP = 0x6D02,
    STR_NAME_ENTRY_EMPTY = 0x6D03,
    STR_NAME_ENTRY_CONFIRM = 0x6D04,
    STR_NAME_ENTRY_CANCEL = 0x6D05
} NameEntryStringIdValue;
```

The sole NameEntryDef row is `{ 1, 8, 3, 30, {'A','R','I',0,0,0,0,0}, STR_NAME_ENTRY_HEADER, STR_NAME_ENTRY_HELP, STR_NAME_ENTRY_EMPTY, STR_NAME_ENTRY_CONFIRM, STR_NAME_ENTRY_CANCEL, NAME_ENTRY_START_CONFIRMS_NONEMPTY + NAME_ENTRY_B_DELETES_NONEMPTY_ONLY + NAME_ENTRY_BACK_OPENS_CANCEL }`. Flags accept only mask `0x0007`; all three bits are required in this chapter. The grid is exactly A-Z, DELETE, DEFAULT, CONFIRM, BACK. `{B}` deletes one letter only when the buffer is nonempty and never doubles as cancel. Selecting BACK with `{A}` invokes `NAME_CANCEL` (`KEEP EDITING` / `RETURN`) through one debounced `NAME_ACTION_BACK`; returning to title discards the draft and writes nothing. `{START}` requests confirm only for a nonempty valid buffer. Every action is edge-triggered; opening a prompt clears/consumes the triggering edge, closing it discards one poll frame, and controller loss freezes the buffer/cursor/prompt. Validation proves the 30 unique grid actions, uppercase-only 1-8-byte output, zero default padding, reachable BACK item, safe default choice on cancel, and no physical press can both open and resolve a prompt.

## 5. Echoforms, affinities, moves, and statuses

### 5.1 Echoform and affinity IDs

```c
typedef enum CreatureIdValue {
    ECHO_NONE       = 0,
    ECHO_QUARRUNE   = 1, /* real starter */
    ECHO_AYSELOR    = 2, /* real starter */
    ECHO_KILNBACK   = 3, /* simulation player */
    ECHO_NACREEL    = 4, /* simulation player */
    ECHO_GYRECLAST  = 5, /* simulation opponent */
    ECHO_KIVARRAX   = 6, /* simulation opponent */
    ECHO_KOVRASS    = 7, /* Rusk */
    ECHO_ULVOREL    = 8  /* Rusk */
} CreatureIdValue;

typedef enum AffinityId {
    AFFINITY_NONE    = 0,
    AFFINITY_CURRENT = 1,
    AFFINITY_EMBER   = 2,
    AFFINITY_GALE    = 3,
    AFFINITY_STRATA  = 4
} AffinityId;
```

The advantage cycle is `CURRENT > EMBER > GALE > STRATA > CURRENT`. Advantage is Q8.8 `384` (1.5x), disadvantage `192` (0.75x), and neutral `256`. `AFFINITY_NONE` is valid for non-damaging support/status moves and for duo damage explicitly marked `MOVE_AFFINITY_NEUTRAL_DAMAGE`; it resolves as 256 only in that marked damage case. An ordinary `MOVE_DAMAGE` must name one of the four affinities.

```c
typedef struct CreatureDef {
    CreatureId id;                       /* 0 */
    StringId name_string_id;             /* 2 */
    AssetId model_asset_id;              /* 4 */
    AssetId portrait_atlas_asset_id;     /* 6 */
    AnimationSetId animation_set_id;     /* 8 */
    AudioCueId vocal_bank_id;            /* 10 */
    uint8_t affinity_id;                 /* 12 */
    uint8_t flags;                       /* 13 */
    uint16_t base_hp;                    /* 14 */
    uint16_t base_attack;                /* 16: displayed as Power */
    uint16_t base_defense;               /* 18: displayed as Guard */
    uint16_t base_speed;                 /* 20 */
    uint16_t scale_q8;                   /* 22 */
    MoveId move_ids[4];                  /* 24 */
    uint16_t resonance_tags;             /* 32 */
    uint8_t skeleton_bone_count;         /* 34 */
    uint8_t max_vertex_influences;        /* 35; must equal 1 */
    uint16_t collider_radius_q8;          /* 36 */
    uint8_t portrait_region_index;        /* 38: atlas region 0..7 */
    uint8_t reserved;                     /* 39 */
} CreatureDef;
_Static_assert(sizeof(CreatureDef) == 40, "CreatureDef layout");

enum CreatureFlags {
    CREATURE_PERSISTENT_PARTY = 1u << 0,
    CREATURE_TUTORIAL_LOANER = 1u << 1,
    CREATURE_ENEMY_ROSTER = 1u << 2
};

typedef enum OpeningCreatureModelAssetIdValue {
    ASSET_MODEL_ECHO_QUARRUNE = 0x7101,
    ASSET_MODEL_ECHO_AYSELOR = 0x7102,
    ASSET_MODEL_ECHO_KILNBACK = 0x7103,
    ASSET_MODEL_ECHO_NACREEL = 0x7104,
    ASSET_MODEL_ECHO_GYRECLAST = 0x7105,
    ASSET_MODEL_ECHO_KIVARRAX = 0x7106,
    ASSET_MODEL_ECHO_KOVRASS = 0x7107,
    ASSET_MODEL_ECHO_ULVOREL = 0x7108,
    ASSET_UI_PORTRAITS_ECHOFORMS = 0x7109
} OpeningCreatureModelAssetIdValue;

typedef enum OpeningCreatureAnimationSetIdValue {
    ANIMSET_ECHO_QUARRUNE = 0x7201,
    ANIMSET_ECHO_AYSELOR = 0x7202,
    ANIMSET_ECHO_KILNBACK = 0x7203,
    ANIMSET_ECHO_NACREEL = 0x7204,
    ANIMSET_ECHO_GYRECLAST = 0x7205,
    ANIMSET_ECHO_KIVARRAX = 0x7206,
    ANIMSET_ECHO_KOVRASS = 0x7207,
    ANIMSET_ECHO_ULVOREL = 0x7208
} OpeningCreatureAnimationSetIdValue;

typedef enum OpeningCreatureVocalBankIdValue {
    AUDIO_VOX_QUARRUNE = 0x7301,
    AUDIO_VOX_AYSELOR = 0x7302,
    AUDIO_VOX_KILNBACK = 0x7303,
    AUDIO_VOX_NACREEL = 0x7304,
    AUDIO_VOX_GYRECLAST = 0x7305,
    AUDIO_VOX_KIVARRAX = 0x7306,
    AUDIO_VOX_KOVRASS = 0x7307,
    AUDIO_VOX_ULVOREL = 0x7308
} OpeningCreatureVocalBankIdValue;

typedef enum OpeningCreatureNameStringIdValue {
    STR_NAME_ECHO_QUARRUNE = 0x7701,
    STR_NAME_ECHO_AYSELOR = 0x7702,
    STR_NAME_ECHO_KILNBACK = 0x7703,
    STR_NAME_ECHO_NACREEL = 0x7704,
    STR_NAME_ECHO_GYRECLAST = 0x7705,
    STR_NAME_ECHO_KIVARRAX = 0x7706,
    STR_NAME_ECHO_KOVRASS = 0x7707,
    STR_NAME_ECHO_ULVOREL = 0x7708
} OpeningCreatureNameStringIdValue;
```

`CreatureDef.flags` accepts only mask `0x07` and exactly one bit per row: Quarrune/Ayselor use `CREATURE_PERSISTENT_PARTY`; Kilnback/Nacreel use `CREATURE_TUTORIAL_LOANER`; Gyreclast/Kivarrax/Kovrass/Ulvorel use `CREATURE_ENEMY_ROSTER`. Every opening Echoform has four nonzero, distinct move IDs; at least one is a damage move and at least one is support/status. Every required animation cue in its animation-set mask must resolve before asset conversion passes. Unknown flags or a role/TeamDef/PartySlot disagreement fail generation/decode.

The runtime IDs above map directly to the inventory contract: model IDs are generated child assets from source packages `echo.quarrune` through `echo.ulvorel`; the one portrait asset is the aggregate `ui.portraits.echoforms` atlas with region indices 0-7 in CreatureId order; animation sets map to exact `anm.echo.*` rows; vocal banks map to exact `vox.*` rows. The generator rejects the old undefined pseudo-names `mdl.echo.*`, `ui.portrait.*`, and `aud.vocal.*`. The eight opening definitions are locked at level 10, the level used by both chapter encounters:

| Creature | Affinity | HP | Power (`base_attack`) | Guard (`base_defense`) | Speed | Four `MoveId`s | Model / portrait / animation / vocal logical IDs |
|---|---|---:|---:|---:|---:|---|---|
| `ECHO_QUARRUNE` | Strata | 92 | 40 | 48 | 36 | `RIDGE_RAM`, `BRACE_RELAY`, `GROUNDING_RING`, `STEADY_PULSE` | `ASSET_MODEL_ECHO_QUARRUNE` / atlas region 0 / `ANIMSET_ECHO_QUARRUNE` / `AUDIO_VOX_QUARRUNE` |
| `ECHO_AYSELOR` | Gale | 74 | 43 | 30 | 64 | `SIROCCO_SLICE`, `LIFT_CURRENT`, `DAZZLE_WAKE`, `GUIDING_DRAFT` | `ASSET_MODEL_ECHO_AYSELOR` / atlas region 1 / `ANIMSET_ECHO_AYSELOR` / `AUDIO_VOX_AYSELOR` |
| `ECHO_KILNBACK` | Ember | 112 | 48 | 42 | 34 | `CINDER_CHARGE`, `BELLOWS_GUARD`, `SCORCH_MARK`, `BANKED_FLAME` | `ASSET_MODEL_ECHO_KILNBACK` / atlas region 2 / `ANIMSET_ECHO_KILNBACK` / `AUDIO_VOX_KILNBACK` |
| `ECHO_NACREEL` | Current | 86 | 41 | 32 | 63 | `ARC_JET`, `CONDUCTIVE_VEIL`, `FLOW_SWITCH`, `STATIC_RIPPLE` | `ASSET_MODEL_ECHO_NACREEL` / atlas region 3 / `ANIMSET_ECHO_NACREEL` / `AUDIO_VOX_NACREEL` |
| `ECHO_GYRECLAST` | Strata | 104 | 44 | 46 | 28 | `AUGER_KNUCKLE`, `DUST_SCREEN`, `FAULT_PIN`, `CARAPACE_BRACE` | `ASSET_MODEL_ECHO_GYRECLAST` / atlas region 4 / `ANIMSET_ECHO_GYRECLAST` / `AUDIO_VOX_GYRECLAST` |
| `ECHO_KIVARRAX` | Gale | 78 | 42 | 28 | 70 | `CROSSWIND_CUT`, `SLIPSTREAM`, `PRESSURE_DROP`, `TALON_SWEEP` | `ASSET_MODEL_ECHO_KIVARRAX` / atlas region 5 / `ANIMSET_ECHO_KIVARRAX` / `AUDIO_VOX_KIVARRAX` |
| `ECHO_KOVRASS` | Ember | 82 | 43 | 38 | 58 | `CLINKER_BITE`, `BOILER_CHORUS`, `ASH_MANTLE`, `FURNACE_FEINT` | `ASSET_MODEL_ECHO_KOVRASS` / atlas region 6 / `ANIMSET_ECHO_KOVRASS` / `AUDIO_VOX_KOVRASS` |
| `ECHO_ULVOREL` | Current | 88 | 46 | 40 | 52 | `RILL_LASH`, `PRESSURE_LEAP`, `COOLING_SHROUD`, `UNDERTOW` | `ASSET_MODEL_ECHO_ULVOREL` / atlas region 7 / `ANIMSET_ECHO_ULVOREL` / `AUDIO_VOX_ULVOREL` |

The remaining CreatureDef bytes are fixed by this companion table. Tags are numeric sums of `ResonanceTagBits` across the four listed moves; `max_vertex_influences=1` and `reserved=0` in every row.

| CreatureId | Name StringId | Flags | Scale Q8.8 | Resonance tags | Bones / influences | Collider Q8.8 | Portrait region / reserved |
|---|---|---|---:|---:|---|---:|---|
| `ECHO_QUARRUNE` | `STR_NAME_ECHO_QUARRUNE` | `CREATURE_PERSISTENT_PARTY` | 256 | 175 | `20 / 1` | 96 | `0 / 0` |
| `ECHO_AYSELOR` | `STR_NAME_ECHO_AYSELOR` | `CREATURE_PERSISTENT_PARTY` | 256 | 371 | `18 / 1` | 80 | `1 / 0` |
| `ECHO_KILNBACK` | `STR_NAME_ECHO_KILNBACK` | `CREATURE_TUTORIAL_LOANER` | 256 | 47 | `18 / 1` | 112 | `2 / 0` |
| `ECHO_NACREEL` | `STR_NAME_ECHO_NACREEL` | `CREATURE_TUTORIAL_LOANER` | 256 | 123 | `20 / 1` | 88 | `3 / 0` |
| `ECHO_GYRECLAST` | `STR_NAME_ECHO_GYRECLAST` | `CREATURE_ENEMY_ROSTER` | 256 | 109 | `18 / 1` | 112 | `4 / 0` |
| `ECHO_KIVARRAX` | `STR_NAME_ECHO_KIVARRAX` | `CREATURE_ENEMY_ROSTER` | 256 | 59 | `20 / 1` | 84 | `5 / 0` |
| `ECHO_KOVRASS` | `STR_NAME_ECHO_KOVRASS` | `CREATURE_ENEMY_ROSTER` | 256 | 111 | `18 / 1` | 104 | `6 / 0` |
| `ECHO_ULVOREL` | `STR_NAME_ECHO_ULVOREL` | `CREATURE_ENEMY_ROSTER` | 256 | 175 | `20 / 1` | 96 | `7 / 0` |

Together, the two tables and ID enums instantiate all 40 bytes of each CreatureDef. The generator recomputes the tag union and rejects disagreement, a nonzero reserved byte, a duplicate portrait region/name, or any missing asset/animation/audio reference.

These values are the exact derived values at level 10/rank 0. Outside this chapter, deterministic derivation is `HP = max(1, base_hp + 4*(level-10) + 2*rank)`, `Power = max(1, base_attack + 2*(level-10) + rank)`, `Guard = max(1, base_defense + 2*(level-10) + rank)`, and `Speed = max(1, base_speed + (level-10) + rank/2)`, with signed widened intermediates and floor integer division. Opening teams are fixed at level 10/rank 0, so no hidden encounter scaling changes the table.

### 5.2 Move definitions

```c
typedef enum MoveIdValue {
    MOVE_NONE = 0,
    RIDGE_RAM = 1,
    BRACE_RELAY = 2,
    GROUNDING_RING = 3,
    STEADY_PULSE = 4,
    SIROCCO_SLICE = 5,
    LIFT_CURRENT = 6,
    DAZZLE_WAKE = 7,
    GUIDING_DRAFT = 8,
    CINDER_CHARGE = 9,
    BELLOWS_GUARD = 10,
    SCORCH_MARK = 11,
    BANKED_FLAME = 12,
    ARC_JET = 13,
    CONDUCTIVE_VEIL = 14,
    FLOW_SWITCH = 15,
    STATIC_RIPPLE = 16,
    AUGER_KNUCKLE = 17,
    DUST_SCREEN = 18,
    FAULT_PIN = 19,
    CARAPACE_BRACE = 20,
    CROSSWIND_CUT = 21,
    SLIPSTREAM = 22,
    PRESSURE_DROP = 23,
    TALON_SWEEP = 24,
    CLINKER_BITE = 25,
    BOILER_CHORUS = 26,
    ASH_MANTLE = 27,
    FURNACE_FEINT = 28,
    RILL_LASH = 29,
    PRESSURE_LEAP = 30,
    COOLING_SHROUD = 31,
    UNDERTOW = 32,
    SUNLINE_CASCADE = 33,
    HORIZON_BREAK = 34,
    MOVE_LOCKED_COUNT = 35
} MoveIdValue;

typedef enum MoveCategory {
    MOVE_DAMAGE  = 1,
    MOVE_SUPPORT = 2,
    MOVE_STATUS  = 3,
    MOVE_DUO     = 4
} MoveCategory;

typedef enum TargetRule {
    TARGET_SELF             = 1,
    TARGET_ONE_ALLY         = 2,
    TARGET_ONE_ENEMY        = 3,
    TARGET_ALL_ALLIES       = 4,
    TARGET_ALL_ENEMIES      = 5,
    TARGET_ANY_ACTIVE       = 6,
    TARGET_SELF_OR_ALLY     = 7,
    TARGET_LINKED_DUO_ALL_ENEMIES = 8
} TargetRule;

enum MoveFlags {
    MOVE_REQUIRES_LIVING_TARGET = 1u << 0,
    MOVE_RETARGET_SAME_SIDE     = 1u << 1,
    MOVE_CANNOT_REPEAT          = 1u << 2,
    MOVE_CONSUMES_RESONANCE     = 1u << 3,
    MOVE_LINKS_BOTH_ALLIES      = 1u << 4,
    MOVE_ALWAYS_HITS            = 1u << 5,
    MOVE_ONCE_PER_ENCOUNTER     = 1u << 6,
    MOVE_SCRIPTED_DAMAGE        = 1u << 7,
    MOVE_STATUS_ALWAYS_APPLY    = 1u << 8,
    MOVE_AFFINITY_NEUTRAL_DAMAGE = 1u << 9
};

enum ResonanceTagBits {
    RES_TAG_DAMAGE    = 1u << 0,
    RES_TAG_ALLY      = 1u << 1,
    RES_TAG_POWER     = 1u << 2,
    RES_TAG_GUARD     = 1u << 3,
    RES_TAG_SPEED     = 1u << 4,
    RES_TAG_MULTI     = 1u << 5,
    RES_TAG_STAGGER   = 1u << 6,
    RES_TAG_CLEANSE   = 1u << 7,
    RES_TAG_EMPOWER   = 1u << 8,
    RES_TAG_DUO       = 1u << 9
};

typedef enum ResonanceAwardKindValue {
    RESONANCE_AWARD_DAMAGE = 1,
    RESONANCE_AWARD_AFFINITY_ADVANTAGE = 2,
    RESONANCE_AWARD_PARTNER_SUPPORT_10 = 3,
    RESONANCE_AWARD_PARTNER_SUPPORT_12 = 4,
    RESONANCE_AWARD_PARTNER_SUPPORT_14 = 5,
    RESONANCE_AWARD_PARTNER_CLEANSE = 6,
    RESONANCE_AWARD_COMPLEMENTARY_FOLLOW = 7,
    RESONANCE_AWARD_TUTORIAL_CALIBRATION = 8
} ResonanceAwardKindValue;

typedef struct MoveDef {
    MoveId id;                   /* 0 */
    StringId name_string_id;     /* 2 */
    uint8_t target_rule;         /* 4 */
    uint8_t affinity_id;         /* 5 */
    uint8_t category;            /* 6 */
    int8_t priority;             /* 7 */
    uint16_t power;              /* 8 */
    uint16_t accuracy_q16;       /* 10: 0..65535; ignored when always hits */
    uint8_t status_id;           /* 12 */
    uint8_t status_chance_q8;    /* 13: 0..255 */
    uint8_t status_turns;        /* 14: stage duration or status action count */
    uint8_t cooldown_rounds;     /* 15 */
    uint16_t flags;              /* 16 */
    int16_t resonance_delta;     /* 18: clamped to 0..100 after resolution */
    uint16_t effect_script_id;   /* 20 */
    uint16_t animation_cue_id;   /* 22 */
    AssetId vfx_asset_id;        /* 24 */
    AudioCueId sfx_cue_id;       /* 26 */
    CameraCueId camera_cue_id;   /* 28 */
    uint16_t reserved;           /* 30 */
    uint32_t resonance_tag_mask; /* 32 */
} MoveDef;
_Static_assert(sizeof(MoveDef) == 36, "MoveDef layout");

enum OpeningMoveGeneratedIdBases {
    STR_MOVE_GENERATED_BASE = 0x8000,
    EFFECT_SCRIPT_GENERATED_BASE = 0x8100,
    ANIM_CUE_MOVE_GENERATED_BASE = 0x8200,
    ASSET_VFX_MOVE_GENERATED_BASE = 0x8300,
    AUDIO_SFX_MOVE_GENERATED_BASE = 0x8400,
    CAMERA_CUE_MOVE_GENERATED_BASE = 0x8500
};
```

For every registered MoveId `m` in `1..34`, the emit mapping is normative: `name_string_id=0x8000+m`, `effect_script_id=0x8100+m`, `animation_cue_id=0x8200+m`, `vfx_asset_id=0x8300+m`, `sfx_cue_id=0x8400+m`, and `camera_cue_id=0x8500+m`. Every resulting ID is a real generated registry/manifest row; deletion tombstones it. This formula plus the 34-row gameplay table below fixes all six fields without hand-selected bytes. `reserved=0` in every row.

`MoveDef.flags` accepts only mask `0x03FF` and is generated by these complete rules, with every unlisted bit clear:

- `MOVE_REQUIRES_LIVING_TARGET` is set on all 34 moves.
- `MOVE_RETARGET_SAME_SIDE` is set exactly when target rule is ONE_ALLY, ONE_ENEMY, ANY_ACTIVE, or SELF_OR_ALLY; invalid execution targets choose the lowest-lane/instance legal replacement. It is clear for self/all/linked-duo rules.
- `MOVE_CANNOT_REPEAT` is set exactly when cooldown is nonzero, `MOVE_ONCE_PER_ENCOUNTER` is set, or category is DUO.
- `MOVE_CONSUMES_RESONANCE` and `MOVE_LINKS_BOTH_ALLIES` are set exactly on Sunline Cascade and Horizon Break.
- `MOVE_ALWAYS_HITS` is set exactly on SUPPORT, STATUS, and DUO rows; those rows store `accuracy_q16=0`. Ordinary displayed `100%` damage stores `65535` and does not set this bit.
- `MOVE_ONCE_PER_ENCOUNTER` is set only on Steady Pulse; `MOVE_SCRIPTED_DAMAGE` only on Sunline Cascade; `MOVE_STATUS_ALWAYS_APPLY` only on Fault Pin and Furnace Feint; `MOVE_AFFINITY_NEUTRAL_DAMAGE` only on the two duo moves.

`resonance_tag_mask` is the exact sum of declared `ResonanceTagBits` tokens in the row's Tags column and accepts only mask `0x000003FF`; prose such as `priority+1`, `once`, or `always-status` is a MoveDef field/flag, not a tag. `target_rule`, affinity, category, priority, power, accuracy, status fields, cooldown, resonance delta, and tag tokens are exactly the table columns. `MoveDef.resonance_delta` is validation metadata for only two scalar cases: a flat partner-support award (`+10`, `+12`, or `+14`) or a finisher commit cost (`-100`). Damage, advantage, cleanse, follow-through, and calibration awards are derived by their typed effect predicates and therefore require `resonance_delta=0`; they are not summed into this field. The scalar is never applied independently. The effect interpreter remains the sole meter mutation authority, so no move can award or consume twice. The generator materializes each 36-byte row and byte-compares it with source; no default flag, presentation ID, or reserved byte is inferred by Gate 3.

`effect_script_id` indexes validated, bounded bytecode rather than arbitrary C:

```c
typedef enum MoveEffectOp {
    MOVE_EFFECT_DAMAGE = 1,
    MOVE_EFFECT_HEAL_FLAT,
    MOVE_EFFECT_STAGE_ADD,
    MOVE_EFFECT_CLEAR_STATUS,
    MOVE_EFFECT_REMOVE_POSITIVE_POWER,
    MOVE_EFFECT_SET_GUIDING_DRAFT,
    MOVE_EFFECT_SELECT_POWER_IF_POSITIVE_STAGE,
    MOVE_EFFECT_APPLY_STATUS,
    MOVE_EFFECT_AWARD_RESONANCE,
    MOVE_EFFECT_START_COOLDOWN,
    MOVE_EFFECT_ONCE_PER_ENCOUNTER_GATE,
    MOVE_EFFECT_FINISHER_COMMIT,
    MOVE_EFFECT_TUTORIAL_FINISH_DAMAGE
} MoveEffectOp;

typedef enum MoveEffectTarget {
    EFFECT_TARGET_USER = 1,
    EFFECT_TARGET_RESOLVED = 2,
    EFFECT_TARGET_CONSCIOUS_PARTNER = 3,
    EFFECT_TARGET_ALL_RESOLVED = 4
} MoveEffectTarget;

typedef enum BattleStatIdValue {
    BATTLE_STAT_POWER = 1,
    BATTLE_STAT_GUARD = 2,
    BATTLE_STAT_SPEED = 3
} BattleStatIdValue;

enum MoveEffectInstrFlags {
    EFFECT_REQUIRE_SUCCESSFUL_HIT = 1u << 0,
    EFFECT_ONCE_PER_ACTION = 1u << 1,
    EFFECT_PLAYER_SIDE_ONLY = 1u << 2,
    EFFECT_REQUIRE_POSITIVE_POWER_STAGE = 1u << 3
};

typedef struct MoveEffectInstr {
    uint8_t op;          /* 0 */
    uint8_t target;      /* 1 */
    int16_t value;       /* 2: power/heal/stage/resonance */
    uint8_t duration;    /* 4: rounds/actions */
    uint8_t flags;       /* 5: conditional/once-per-action */
    uint16_t aux_id;     /* 6: stat, status, tag, or paired MoveId */
} MoveEffectInstr;
_Static_assert(sizeof(MoveEffectInstr) == 8, "MoveEffectInstr layout");

typedef struct MoveEffectScriptDef {
    uint16_t id;                 /* 0 */
    uint16_t first_instruction;  /* 2 */
    uint8_t instruction_count;   /* 4: 1..8 */
    uint8_t max_emitted_events;  /* 5 */
    uint16_t flags;              /* 6 */
} MoveEffectScriptDef;
_Static_assert(sizeof(MoveEffectScriptDef) == 8, "MoveEffectScriptDef layout");
```

The instruction encoding is exact. `resolved` means the already validated MoveDef target set; `all resolved` visits its living members in lane then instance order. `owning MoveId` is the one MoveDef/DuoFinisherDef whose `effect_script_id` selected the script. Unlisted target/flag values are illegal, and every operand described as zero must be zero.

| MoveEffectOp | Legal target | `value` | `duration` | Legal/required flags | `aux_id` and exact semantics |
|---|---|---:|---:|---|---|
| `MOVE_EFFECT_DAMAGE` | resolved or all resolved | 0 | 0 | require-hit | 0; use the already selected MoveDef power and ordinary formula |
| `MOVE_EFFECT_HEAL_FLAT` | user, resolved, conscious partner, or all resolved | `1..32767` HP | 0 | once-per-action | 0; clamp each legal target to max HP |
| `MOVE_EFFECT_STAGE_ADD` | user, resolved, conscious partner, or all resolved | signed `-2..2`, nonzero | `1..255` rounds | once-per-action, optionally require-hit | one `BattleStatIdValue`; add/clamp and refresh duration |
| `MOVE_EFFECT_CLEAR_STATUS` | user, resolved, conscious partner, or all resolved | 0 | 0 | once-per-action | `STATUS_STAGGERED`; clear only if present |
| `MOVE_EFFECT_REMOVE_POSITIVE_POWER` | resolved or all resolved | 0 | 0 | require-hit + once-per-action | `BATTLE_STAT_POWER`; set a positive Power stage to 0, leave nonpositive unchanged |
| `MOVE_EFFECT_SET_GUIDING_DRAFT` | user, resolved, or conscious partner | 120 | 0 | once-per-action | 0; set the one-use 120-percent modifier, never stack |
| `MOVE_EFFECT_SELECT_POWER_IF_POSITIVE_STAGE` | user | alternate power `34` | 0 | require-positive-Power-stage | `BATTLE_STAT_POWER`; for owning `PRESSURE_LEAP` select 34 iff user stage >0, otherwise its MoveDef power 26 |
| `MOVE_EFFECT_APPLY_STATUS` | resolved or all resolved | 0 | exact MoveDef `status_turns` | require-hit + once-per-action | registered nonzero StatusId matching MoveDef; chance/always policy comes only from MoveDef |
| `MOVE_EFFECT_AWARD_RESONANCE` | user, resolved, or conscious partner | exact gain for typed kind | 0 | player-side-only + once-per-action | one non-calibration `ResonanceAwardKindValue`; require its exact predicate below |
| `MOVE_EFFECT_START_COOLDOWN` | user | 0 | exact MoveDef cooldown `1..255` | once-per-action | owning MoveId; only after a legal effect commit |
| `MOVE_EFFECT_ONCE_PER_ENCOUNTER_GATE` | user | 0 | 0 | once-per-action | owning MoveId; reject when its stable move-slot once bit is already set |
| `MOVE_EFFECT_FINISHER_COMMIT` | user | exact Resonance cost `100` | 0 | once-per-action | owning registered duo MoveId; atomically mark linked command committed and consume meter after legal damage commit |
| `MOVE_EFFECT_TUTORIAL_FINISH_DAMAGE` | all resolved | 0 | 0 | once-per-action | owning `SUNLINE_CASCADE`; emit one non-random current-HP-equal hit per living target |

In this table `require-hit`, `once-per-action`, `player-side-only`, and `require-positive-Power-stage` mean the corresponding declared `EFFECT_*` bit. `MoveEffectInstr.flags` accepts only mask `0x0F` and must be a subset of the row. For DAMAGE, APPLY_STATUS, and REMOVE_POSITIVE_POWER the require-hit bit is mandatory; for SELECT_POWER the positive-stage bit is mandatory; Resonance requires both player-side and once; all other required bits are shown. `aux_id` may encode only the exact stat, StatusId, ResonanceAwardKind, or owning/paired MoveId stated in its row—never a raw enum of a different domain.

`EFFECT_ONCE_PER_ACTION` deduplicates instruction dispatch by `(battle_generation, action_seq, instruction_index)`. For a target-mutating instruction, that one dispatch still iterates every member of ALL_RESOLVED exactly once and records `(action_seq,instruction_index,target_instance)` to prevent duplicate per-target application. A global award/cooldown/finisher emits once for the action regardless of target cardinality. The Resonance kinds are fixed:

| ResonanceAwardKind | Exact amount and predicate | Target / dedup |
|---|---|---|
| `RESONANCE_AWARD_DAMAGE` | +6 iff a player action committed at least 1 total HP damage | user; once/action |
| `RESONANCE_AWARD_AFFINITY_ADVANTAGE` | +4 iff at least one committed target was advantage-hit | user; once/action even multi-target |
| `RESONANCE_AWARD_PARTNER_SUPPORT_10` | +10 iff the declared support affected the conscious partner, never self | resolved partner; once/action |
| `RESONANCE_AWARD_PARTNER_SUPPORT_12` | +12 under the same partner-only predicate | resolved partner; once/action |
| `RESONANCE_AWARD_PARTNER_SUPPORT_14` | +14 under the same partner-only predicate | resolved partner; once/action |
| `RESONANCE_AWARD_PARTNER_CLEANSE` | +8 iff the conscious partner's Staggered status was actually cleared | partner; once/action |
| `RESONANCE_AWARD_COMPLEMENTARY_FOLLOW` | +12 iff the affected partner consumes one valid same-round setup record with a damaging follow | partner; once/setup record/round |
| `RESONANCE_AWARD_TUTORIAL_CALIBRATION` | `100-current`, only Gate 4 after honest meter >=70 and setup/follow proof | system source; once tutorial generation |

The instruction opcode forbids `RESONANCE_AWARD_TUTORIAL_CALIBRATION`; only TutorialScript owns it. Amount and kind must byte-agree, invalid/miss/no-op/enemy/self-support/replayed action awards zero, and the setup record is marked consumed before adding its typed award.

Scripts contain no jumps, loops, pointers, or arbitrary IDs. `MoveEffectScriptDef.flags` is MUST-BE-ZERO for this chapter. The validator requires `instruction_count=1..8`, checks widened `first_instruction + instruction_count` within a nonoverlapping dense table, resolves every ID, compares every source-derived script byte to the authoritative move table, and simulates every target cardinality. It rejects an invalid target, nonzero unused field, damage without a damage/duo category, `AFFINITY_NONE` damage without the duo neutral flag, a neutral flag on ordinary damage, illegal stat/stage/duration, cleanse other than Staggered, any conditional power other than the exact Pressure Leap rule, cooldown/once/Resonance/tag disagreement, a non-duo finisher opcode, or a declared `max_emitted_events` below the proven bound/above the 64-entry queue. Execution order is fixed: legality/once/cooldown gate; target resolution; accuracy; Power selection; variance and pending damage; status draw; damage/heal/status/stage/cleanse/empower commits; Resonance awards; cooldown start; finisher consumption. Unknown opcode/target/flag bits, duplicate/zero script IDs, reserved values, and table overflow are build failures.

Accuracy `0` always fails, `65535` is exact full accuracy, and intermediate values consume one deterministic 16-bit draw and succeed on `< accuracy_q16`; `MOVE_ALWAYS_HITS` bypasses accuracy entirely. For each living resolved target in lane then instance order, a successful damaging hit consumes its variance draw. A chance-bearing status then consumes exactly one 8-bit draw in `[0,255]` before effect commits and applies on `draw < status_chance_q8`. Dazzle Wake uses `89/256` (displayed as 35%); Static Ripple uses `64/256` (25%). Fault Pin and Furnace Feint use `MOVE_STATUS_ALWAYS_APPLY`, not a fake `255` chance, and consume no status draw. Damage variance uses `240 + floor(high8 * 33 / 256)`, yielding Q8.8 `[240,272]`. No RNG calls are legal outside intermediate accuracy, per-target variance, and chance status. Equal-score AI pairs sort by MoveId then target instance and consume no RNG, so AI decisions cannot shift the battle stream.

For `MOVE_STATUS_ALWAYS_APPLY`, `status_id` is `STATUS_STAGGERED`, `status_chance_q8` is zero, and the effect script must contain one matching apply-status opcode. For Dazzle/Static, the field is 89/64 and the always flag is clear. Every other move has `status_id=STATUS_NONE` and zero status fields.

The xorshift32 golden stream for seed `0x53494D31` begins `27055886, 0EAE0F0C, 26B2FDCB, 587F888E, 84AD9B19`. A full-accuracy two-target Dazzle Wake therefore consumes variance/status pairs in target order: target 0 uses high bytes `39/14`, target 1 uses `38/88`; both status draws apply because `14,88 < 89`. Threshold goldens require Dazzle draw 88 apply/89 fail, Static draw 63 apply/64 fail, and always-apply consume no draw. Retry restores the seed so the stream repeats exactly.

The complete move table is authoritative. `100%` means `accuracy_q16=65535`; chance percentages map to Q0.8 as shown. `+N ally` applies only when a conscious partner, not self, is affected. Every regular move has priority 0 except `BOILER_CHORUS`, whose explicit support priority is +1 and is shown in move info; duo priority is +10.

| ID / display name | Target | Affinity / category | Power / accuracy | Exact effect, duration, status | Cooldown | Resonance | Tags / flags |
|---|---|---|---|---|---:|---:|---|
| `RIDGE_RAM` / Ridge Ram | one enemy | Strata / damage | 28 / 100% | damage | 0 | 0 | damage |
| `BRACE_RELAY` / Brace Relay | self or ally | none / support | 0 / always | Guard +1 for 2 rounds | 0 | +14 ally | ally, guard |
| `GROUNDING_RING` / Grounding Ring | all enemies | Strata / damage | 14 / 100% | damage; remove one positive Power stage from each hit target | 0 | 0 | damage, multi, power |
| `STEADY_PULSE` / Steady Pulse | self or ally | none / support | 12 heal / always | restore 12 HP; clear Staggered; once per encounter | encounter | 0 | ally, cleanse, once |
| `SIROCCO_SLICE` / Sirocco Slice | one enemy | Gale / damage | 26 / 100% | damage | 0 | 0 | damage |
| `LIFT_CURRENT` / Lift Current | self or ally | none / support | 0 / always | Speed +1 for 2 rounds | 0 | +14 ally | ally, speed |
| `DAZZLE_WAKE` / Dazzle Wake | all enemies | Gale / damage | 12 / 100% | damage; independently apply Staggered at `89/256` (UI 35%) | 0 | 0 | damage, multi, stagger |
| `GUIDING_DRAFT` / Guiding Draft | self or ally | none / support | 0 / always | set one-use +20% next committed damaging move flag | 0 | +12 ally | ally, empower |
| `CINDER_CHARGE` / Cinder Charge | one enemy | Ember / damage | 32 / 100% | damage | 0 | 0 | damage |
| `BELLOWS_GUARD` / Bellows Guard | all allies | none / support | 0 / always | Guard +1 for 1 round | 0 | +10 | ally, guard, multi |
| `SCORCH_MARK` / Scorch Mark | one enemy | none / status | 0 / always | Power -1 for 2 rounds | 0 | 0 | power |
| `BANKED_FLAME` / Banked Flame | self | none / support | 0 / always | Power +1 for 2 rounds | 0 | 0 | power |
| `ARC_JET` / Arc Jet | one enemy | Current / damage | 29 / 100% | damage | 0 | 0 | damage |
| `CONDUCTIVE_VEIL` / Conductive Veil | one ally | none / support | 0 / always | Guard +1 for 2 rounds | 0 | +14 | ally, guard |
| `FLOW_SWITCH` / Flow Switch | all allies | none / support | 0 / always | Speed +1 for 1 round | 0 | +10 | ally, speed, multi |
| `STATIC_RIPPLE` / Static Ripple | all enemies | Current / damage | 13 / 100% | damage; independently apply Staggered at `64/256` (25%) | 0 | 0 | damage, multi, stagger |
| `AUGER_KNUCKLE` / Auger Knuckle | one enemy | Strata / damage | 27 / 100% | damage | 0 | 0 | damage |
| `DUST_SCREEN` / Dust Screen | all enemies | none / status | 0 / always | Power -1 for 1 round | 0 | 0 | power, multi |
| `FAULT_PIN` / Fault Pin | one enemy | Strata / damage | 18 / 100% | damage; guaranteed Staggered (`MOVE_STATUS_ALWAYS_APPLY`) | 2 rounds | 0 | damage, stagger, always-status |
| `CARAPACE_BRACE` / Carapace Brace | self | none / support | 0 / always | Guard +1 for 2 rounds | 0 | 0 | guard |
| `CROSSWIND_CUT` / Crosswind Cut | one enemy | Gale / damage | 25 / 100% | damage | 0 | 0 | damage |
| `SLIPSTREAM` / Slipstream | self or ally | none / support | 0 / always | Speed +1 for 2 rounds | 0 | 0 | ally, speed |
| `PRESSURE_DROP` / Pressure Drop | one enemy | none / status | 0 / always | Guard -1 for 2 rounds | 0 | 0 | guard |
| `TALON_SWEEP` / Talon Sweep | all enemies | Gale / damage | 12 / 100% | damage | 0 | 0 | damage, multi |
| `CLINKER_BITE` / Clinker Bite | one enemy | Ember / damage | 27 / 100% | damage | 0 | 0 | damage |
| `BOILER_CHORUS` / Boiler Chorus | one ally | none / support | 0 / always | Power +1 for 2 rounds; priority +1 | 0 | 0 | ally, power, priority+1 |
| `ASH_MANTLE` / Ash Mantle | all allies | none / support | 0 / always | Guard +1 for 1 round | 0 | 0 | ally, guard, multi |
| `FURNACE_FEINT` / Furnace Feint | one enemy | Ember / damage | 17 / 100% | damage; guaranteed Staggered (`MOVE_STATUS_ALWAYS_APPLY`) | 2 rounds | 0 | damage, stagger, always-status |
| `RILL_LASH` / Rill Lash | one enemy | Current / damage | 28 / 100% | damage | 0 | 0 | damage |
| `PRESSURE_LEAP` / Pressure Leap | one enemy | Current / damage | 26 / 100% | damage; substitute power 34 while user has a positive Power stage | 0 | 0 | damage, power |
| `COOLING_SHROUD` / Cooling Shroud | self or ally | none / support | 0 / always | Guard +1 for 2 rounds and clear Staggered | 0 | 0 | ally, guard, cleanse |
| `UNDERTOW` / Undertow | all enemies | Current / damage | 13 / 100% | damage | 0 | 0 | damage, multi |
| `SUNLINE_CASCADE` / Sunline Cascade | linked duo, all enemies | neutral-none / duo | scripted / cannot miss | tutorial-only: emit damage equal to each living target's current HP, in lane order; no variance | 0 | -100 | duo, damage, multi, always-hits, scripted, neutral-damage |
| `HORIZON_BREAK` / Horizon Break | linked duo, all enemies | neutral-none / duo | 44 / cannot miss | normal tuned damage to each living enemy; not a forced kill | 0 | -100 | duo, damage, multi, always-hits, neutral-damage |

`TARGET_SELF_OR_ALLY` admits self or the conscious active partner and rejects both enemies and a KO partner. `TARGET_ONE_ALLY` requires the conscious partner and rejects self. All-enemy effects skip KO lanes. Effect scripts encode the conditional resonance rules and Pressure Leap substitution; source validation compares script parameters against this table.

```c
typedef struct DuoFinisherDef {
    MoveId move_id;                    /* 0 */
    CreatureId required_creature_a;    /* 2 */
    CreatureId required_creature_b;    /* 4 */
    uint8_t target_rule;               /* 6 */
    uint8_t flags;                     /* 7 */
    uint8_t resonance_cost;            /* 8: exactly 100 */
    uint8_t reserved0;                 /* 9 */
    uint16_t effect_script_id;         /* 10 */
    uint16_t animation_cue_id;         /* 12 */
    AssetId vfx_asset_id;              /* 14 */
    AudioCueId sfx_cue_id;             /* 16 */
    CameraCueId camera_cue_id;         /* 18 */
} DuoFinisherDef;
_Static_assert(sizeof(DuoFinisherDef) == 20, "DuoFinisherDef layout");

enum DuoFinisherFlags {
    DUO_LINKS_BOTH_ALLIES = 1u << 0,
    DUO_TARGETS_ALL_ENEMIES = 1u << 1,
    DUO_CONSUMES_RESONANCE = 1u << 2,
    DUO_ALWAYS_HITS = 1u << 3,
    DUO_SCRIPTED_DAMAGE = 1u << 4,
    DUO_TUTORIAL_ONLY = 1u << 5,
    DUO_NEUTRAL_FORMULA = 1u << 6
};
```

The complete DuoFinisherDef table is:

| MoveId | Required creatures | Target | Flags | Cost / reserved | Effect / animation / VFX / SFX / camera IDs |
|---|---|---|---|---|---|
| `SUNLINE_CASCADE` | `ECHO_KILNBACK / ECHO_NACREEL` | `TARGET_LINKED_DUO_ALL_ENEMIES` | `DUO_LINKS_BOTH_ALLIES + DUO_TARGETS_ALL_ENEMIES + DUO_CONSUMES_RESONANCE + DUO_ALWAYS_HITS + DUO_SCRIPTED_DAMAGE + DUO_TUTORIAL_ONLY` | `100 / 0` | `0x8121 / 0x8221 / 0x8321 / 0x8421 / 0x8521` |
| `HORIZON_BREAK` | `ECHO_QUARRUNE / ECHO_AYSELOR` | `TARGET_LINKED_DUO_ALL_ENEMIES` | `DUO_LINKS_BOTH_ALLIES + DUO_TARGETS_ALL_ENEMIES + DUO_CONSUMES_RESONANCE + DUO_ALWAYS_HITS + DUO_NEUTRAL_FORMULA` | `100 / 0` | `0x8122 / 0x8222 / 0x8322 / 0x8422 / 0x8522` |

These IDs are the generated-base formula for MoveIds 33 (`0x21`) and 34 (`0x22`). `DuoFinisherDef.flags` accepts only mask `0x7F`; all other combinations and nonzero `reserved0` fail. `SUNLINE_CASCADE` requires `ECHO_KILNBACK + ECHO_NACREEL`; its tutorial effect emits one non-random HP-equal damage event per living target and is illegal in any other encounter. `HORIZON_BREAK` requires `ECHO_QUARRUNE + ECHO_AYSELOR` and uses `linked_power=floor((effective_power_quarrune + effective_power_ayselor)/2)`, independent of lane order. At baseline this is `floor((40+43)/2)=41`. Its move power 44 then runs through the ordinary neutral-affinity formula with one variance draw per living target, so it is not a forced kill. Order in the two active lanes is irrelevant. Both require both partners conscious/available and Resonance 100, replace both commands, target all living enemies, and consume exactly 100 only on finisher commit.

Guiding Draft is one boolean per actor, not a stack counter. A solo damaging move reads only its user's flag and applies one 120% multiplier. For `HORIZON_BREAK`, both linked actors' flags contribute: `empower_count` is 0, 1, or 2 and final pre-HP-clamp damage is `floor(normal_linked_damage*(100+20*empower_count)/100)`, capped by the normal integer/HP limits. A successful linked damage commit clears every contributing participant flag; an invalid/cancelled finisher clears none. Sunline's scripted HP-equal damage cannot be empowered, and its locked loaners have no Guiding Draft. Baseline Horizon against Guard 40 at variance 256 is 54 damage, then 54/64/75 for zero/one/two flags. Goldens prove lane independence, no flag stacking above two, partner-only flag isolation for solo moves, linked clear timing, and cancellation preservation.

### 5.3 Temporary status family

The chapter has one temporary ailment. Power/Guard/Speed stages and Guiding Draft's one-use modifier are volatile modifiers, not statuses.

```c
typedef enum StatusIdValue {
    STATUS_NONE      = 0,
    STATUS_STAGGERED = 1
} StatusIdValue;

typedef struct StatusDef {
    uint8_t id;                  /* 0 */
    uint8_t flags;               /* 1: clear on KO, cleanseable */
    uint16_t speed_multiplier_q8;/* 2: 192 = -25% */
    uint8_t owner_actions_until_expire; /* 4: exactly 1 */
    uint8_t reserved0;           /* 5 */
    uint16_t apply_string_id;    /* 6 */
    uint16_t expire_string_id;   /* 8 */
    uint16_t reserved1;          /* 10 */
} StatusDef;
_Static_assert(sizeof(StatusDef) == 12, "StatusDef layout");

enum StatusFlags {
    STATUS_CLEAR_ON_KO = 1u << 0,
    STATUS_CLEANSEABLE = 1u << 1
};

typedef enum StatusRuntimeStringIdValue {
    STR_STATUS_STAGGERED_APPLY = 0x6E01,
    STR_STATUS_STAGGERED_EXPIRE = 0x6E02
} StatusRuntimeStringIdValue;

typedef struct BattleStatus {
    uint8_t id;                      /* 0 */
    uint8_t source_instance_id;      /* 1 */
    uint8_t owner_actions_remaining; /* 2: exactly 1 while Staggered */
    uint8_t applied_round;           /* 3 */
} BattleStatus;
_Static_assert(sizeof(BattleStatus) == 4, "BattleStatus layout");
```

The sole nonzero row is the literal initializer `{ STATUS_STAGGERED, STATUS_CLEAR_ON_KO + STATUS_CLEANSEABLE, 192, 1, 0, STR_STATUS_STAGGERED_APPLY, STR_STATUS_STAGGERED_EXPIRE, 0 }`. The two StringIds resolve to the authored apply/expire battle text. Status flags accept only mask `0x03` and all reserved fields are zero. Staggered multiplies effective Speed by `192/256` through the affected actor's next completed action and then expires. Applying it before a pending action recomputes that actor's key and stable-sorts only the unexecuted command suffix; applying it after the actor acted preserves it for the next round. Reapplication refreshes the one-action obligation. A completed no-op still counts as the actor's action; KO, explicit cleanse, retry reconstruction, and battle end clear it immediately. Temporary status and volatile modifiers are never serialized to EEPROM.

## 6. Teams and encounters

```c
typedef enum TeamIdValue {
    TEAM_NONE = 0,
    TEAM_SIM_PLAYER = 1,
    TEAM_SIM_OPPONENT = 2,
    TEAM_RUSK = 3,
    TEAM_REAL_STARTERS = 4
} TeamIdValue;

typedef enum AiProfileIdValue {
    AI_NONE = 0,
    AI_TUTORIAL_GATED = 1,
    AI_RUSK_SUPPORT = 2
} AiProfileIdValue;

enum EncounterFlags {
    ENCOUNTER_USE_SAVED_PLAYER_PARTY = 1u << 0,
    ENCOUNTER_IS_TUTORIAL            = 1u << 1,
    ENCOUNTER_ALLOW_RETRY            = 1u << 2,
    ENCOUNTER_GRANTS_REWARD          = 1u << 3,
    ENCOUNTER_RESTORE_HP_ON_RETRY    = 1u << 4
};

typedef enum EncounterIdValue {
    ENCOUNTER_NONE = 0,
    ENCOUNTER_SIM_TUTORIAL = 1,
    ENCOUNTER_RUSK_COURTYARD = 2
} EncounterIdValue;

typedef enum TutorialScriptIdValue {
    TUTORIAL_SCRIPT_NONE = 0,
    TUTORIAL_SCRIPT_OPENING = 1
} TutorialScriptIdValue;

typedef struct TeamDef {
    TeamId id;                     /* 0 */
    uint8_t roster_count;          /* 2: 1..4 */
    uint8_t initial_active_count;  /* 3: 1..2 */
    CreatureId creature_ids[4];    /* 4 */
    uint8_t levels[4];             /* 12 */
    uint16_t ai_profile_ids[4];    /* 16 */
} TeamDef;
_Static_assert(sizeof(TeamDef) == 24, "TeamDef layout");

typedef enum EncounterKindValue {
    ENCOUNTER_KIND_TUTORIAL = 1,
    ENCOUNTER_KIND_STORY = 2
} EncounterKindValue;

typedef struct EncounterDef {
    EncounterId id;                      /* 0 */
    uint8_t kind;                        /* 2: simulation or story */
    uint8_t flags;                       /* 3 */
    SceneId scene_id;                    /* 4 */
    ZoneId zone_id;                      /* 6 */
    BundleId arena_bundle_id;            /* 8 */
    AudioCueId music_cue_id;             /* 10 */
    CutsceneId intro_cutscene_id;        /* 12 */
    StoryActionListId victory_action_xref; /* 14: equality-only */
    StoryActionListId defeat_action_xref;  /* 16: equality-only */
    uint16_t tutorial_script_id;         /* 18 */
    RewardId reward_id;                  /* 20 */
    TeamId player_team_id;               /* 22; 0 when saved party flag is set */
    TeamId enemy_team_id;                /* 24 */
    uint16_t ai_profile_id;              /* 26 */
    uint32_t base_seed;                  /* 28 */
} EncounterDef;
_Static_assert(sizeof(EncounterDef) == 32, "EncounterDef layout");
```

Locked encounter IDs are `ENCOUNTER_SIM_TUTORIAL = 1` and `ENCOUNTER_RUSK_COURTYARD = 2`. The complete TeamDef table is literal; array braces below are the four emitted slots, including zero tails:

| TeamId | roster / active | creature_ids[4] | levels[4] | ai_profile_ids[4] |
|---|---|---|---|---|
| `TEAM_SIM_PLAYER` | `2 / 2` | `{ ECHO_KILNBACK, ECHO_NACREEL, ECHO_NONE, ECHO_NONE }` | `{ 10, 10, 0, 0 }` | `{ AI_NONE, AI_NONE, AI_NONE, AI_NONE }` |
| `TEAM_SIM_OPPONENT` | `2 / 2` | `{ ECHO_GYRECLAST, ECHO_KIVARRAX, ECHO_NONE, ECHO_NONE }` | `{ 10, 10, 0, 0 }` | `{ AI_TUTORIAL_GATED, AI_TUTORIAL_GATED, AI_NONE, AI_NONE }` |
| `TEAM_RUSK` | `2 / 2` | `{ ECHO_KOVRASS, ECHO_ULVOREL, ECHO_NONE, ECHO_NONE }` | `{ 10, 10, 0, 0 }` | `{ AI_RUSK_SUPPORT, AI_RUSK_SUPPORT, AI_NONE, AI_NONE }` |
| `TEAM_REAL_STARTERS` | `2 / 2` | `{ ECHO_QUARRUNE, ECHO_AYSELOR, ECHO_NONE, ECHO_NONE }` | `{ 10, 10, 0, 0 }` | `{ AI_NONE, AI_NONE, AI_NONE, AI_NONE }` |

The complete EncounterDef rows spell every field:

| id / kind / flags | scene / zone / arena bundle / music | intro / victory list / defeat list | tutorial / reward | player / enemy / AI | seed |
|---|---|---|---|---|---:|
| `ENCOUNTER_SIM_TUTORIAL / ENCOUNTER_KIND_TUTORIAL / (ENCOUNTER_IS_TUTORIAL + ENCOUNTER_ALLOW_RETRY + ENCOUNTER_RESTORE_HP_ON_RETRY)` | `SCENE_SIM_ARENA / ZONE_SIM_ARENA / BUNDLE_SIM_TUTORIAL_ARENA / MUSIC_CUE_SIMULATION` | `CUTSCENE_NONE / ACTION_TUTORIAL_RESULT_ACCEPT / 0` | `TUTORIAL_SCRIPT_OPENING / REWARD_NONE` | `TEAM_SIM_PLAYER / TEAM_SIM_OPPONENT / AI_TUTORIAL_GATED` | `0x53494D31` |
| `ENCOUNTER_RUSK_COURTYARD / ENCOUNTER_KIND_STORY / (ENCOUNTER_USE_SAVED_PLAYER_PARTY + ENCOUNTER_ALLOW_RETRY + ENCOUNTER_GRANTS_REWARD + ENCOUNTER_RESTORE_HP_ON_RETRY)` | `SCENE_ESTATE_COURTYARD / ZONE_ESTATE_COURTYARD / BUNDLE_RUSK_BATTLE_ACTION / MUSIC_CUE_ESTATE_BATTLE` | `CUTSCENE_NONE / ACTION_RUSK_VICTORY_RESULT / ACTION_RUSK_DEFEAT_RESULT` | `TUTORIAL_SCRIPT_NONE / REWARD_RUSK_FIRST_WIN` | `TEAM_NONE / TEAM_RUSK / AI_RUSK_SUPPORT` | `0x5255534B` |

Team rows require count `2`, two distinct registered creatures, two legal nonzero levels, exact zero tails, and per-slot AI agreement; no player slot may name an AI profile. Encounter flags accept only mask `0x1F` and must equal the row. Saved-party requires `player_team_id=TEAM_NONE`; its absence requires a nonzero TeamDef. Tutorial/reward/script/action/bundle/music fields must agree with kind and row, and every StoryActionList admits battle-result context.

Scene music is the exploration default; an encounter or authored story route may
temporarily override it through one typed presentation table:

```c
typedef enum MusicPresentationTriggerKindValue {
    MUSIC_TRIGGER_ENCOUNTER_VICTORY = 1,
    MUSIC_TRIGGER_STORY_ACTION_COMMIT = 2
} MusicPresentationTriggerKindValue;

typedef enum MusicTreatmentVariantValue {
    MUSIC_VARIANT_VICTORY_STING = 1,
    MUSIC_VARIANT_COMPANION_RETURN = 2,
    MUSIC_VARIANT_CLOSING_FRACTURE = 3
} MusicTreatmentVariantValue;

enum MusicPresentationRouteFlags {
    MUSIC_ROUTE_ONE_SHOT = 1u << 0,
    MUSIC_ROUTE_RESUME_CUE_ON_COMPLETE = 1u << 1,
    MUSIC_ROUTE_FADE_CURRENT_BEFORE_OPEN = 1u << 2,
    MUSIC_ROUTE_NONBLOCKING_STORY = 1u << 3,
    MUSIC_ROUTE_CARRY_INTO_MATCHING_DESTINATION = 1u << 4
};

typedef struct MusicPresentationRouteDef {
    uint8_t trigger_kind;       /* 0 */
    uint8_t variant;            /* 1 */
    uint16_t owner_id;          /* 2: EncounterId or StoryActionListId */
    AudioCueId cue_id;          /* 4 */
    AudioCueId resume_cue_id;   /* 6 */
    uint16_t flags;             /* 8 */
    uint16_t reserved;          /* 10 */
} MusicPresentationRouteDef;
_Static_assert(sizeof(MusicPresentationRouteDef) == 12, "MusicPresentationRouteDef layout");
```

The three rows are exact:

| Trigger / typed owner | Variant | Override / resume cue | Exact flags / reserved |
|---|---|---|---|
| `MUSIC_TRIGGER_ENCOUNTER_VICTORY / ENCOUNTER_RUSK_COURTYARD` | `MUSIC_VARIANT_VICTORY_STING` | `MUSIC_CUE_VICTORY_RETURN / MUSIC_CUE_ESTATE_EXPLORATION` | `MUSIC_ROUTE_ONE_SHOT + MUSIC_ROUTE_RESUME_CUE_ON_COMPLETE + MUSIC_ROUTE_FADE_CURRENT_BEFORE_OPEN / 0` |
| `MUSIC_TRIGGER_STORY_ACTION_COMMIT / ACTION_REUNION_RETURN_START_SAVE` | `MUSIC_VARIANT_COMPANION_RETURN` | `MUSIC_CUE_VICTORY_RETURN / MUSIC_CUE_ESTATE_EXPLORATION` | `MUSIC_ROUTE_ONE_SHOT + MUSIC_ROUTE_RESUME_CUE_ON_COMPLETE + MUSIC_ROUTE_FADE_CURRENT_BEFORE_OPEN + MUSIC_ROUTE_NONBLOCKING_STORY / 0` |
| `MUSIC_TRIGGER_STORY_ACTION_COMMIT / ACTION_HOOK_BEGIN_OBJECTIVE` | `MUSIC_VARIANT_CLOSING_FRACTURE` | `MUSIC_CUE_CHAPTER_END / MUSIC_CUE_CHAPTER_END` | `MUSIC_ROUTE_FADE_CURRENT_BEFORE_OPEN + MUSIC_ROUTE_NONBLOCKING_STORY + MUSIC_ROUTE_CARRY_INTO_MATCHING_DESTINATION / 0` |

`ACTION_RUSK_VICTORY_RESULT` commits the encounter-victory trigger exactly once
after reward state is coherent; defeat/Retry never selects it. The reunion row
fires only after `ACTION_REUNION_RETURN_START_SAVE` publishes in the Estate
study, plays its short return variation, then resumes Estate exploration for the
authored Study-to-Courtyard walk; the actual map transition selects the World Map
default at handoff. The audio service fades/releases the
current stream before opening the override, then resumes the listed cue only if
the generation and destination owner still match. `ACTION_HOOK_BEGIN_OBJECTIVE`
starts the separate closing treatment before `HOOK_001` in the loaded Annex
atrium; the matching `SCENE_END_CHAPTER` default adopts the same live cue without
restart, so the Hook/Fracture sequence, final save, and end card share one
authored treatment. The carry flag is legal only when override and destination
default are the same nonzero cue. Flags accept only `0x001F`.
Duplicate trigger/owner keys, a trigger-kind/owner-domain mismatch, any cue other
than the exact row, or an unreferenced music inventory ID fails generation.

The tutorial AI obeys the authored lesson gates without inventing damage or reading unconfirmed commands. Rusk AI subsequently enumerates legal pairs and scores visible HP, affinity, Power/Guard/Speed stages, Staggered, support synergy, expected KO, and repetition, with stable MoveId then target-instance tie-breaks. The locked round-one order is Kovrass first because Boiler Chorus has visible priority +1, then priority-0 Ayselor (64), Ulvorel (52), and Quarrune (36). With Rusk seed `0x5255534B`, Ayselor Dazzle consumes high bytes `FF,2A,3B,B3` as Kovrass variance/status then Ulvorel variance/status: Kovrass's 42 applies after it already acted, while Ulvorel's 179 fails. Boosted Ulvorel therefore remains Speed 52 and resolves Pressure Leap before Quarrune. A separate synthetic forced-status test proves pending Ulvorel would become 39 and still remain ahead. No hidden priority is permitted. Source validation requires two active actors per side, exactly these seeds/AI IDs, legal four-move rosters, no simulation reward, and a one-time Rusk reward ID. Retry recreates the same encounter from its base seed and prebattle snapshot.

```c
typedef struct AiProfileDef {
    AiProfileId id;                 /* 0 */
    uint8_t policy;                 /* 2: scripted/tutorial/scored */
    uint8_t defensive_cap_percent;  /* 3 */
    int16_t affinity_advantage;     /* 4 */
    int16_t affinity_disadvantage;  /* 6 */
    int16_t expected_ko;            /* 8 */
    int16_t low_hp_target;          /* 10 */
    int16_t stage_or_debuff;        /* 12 */
    int16_t stagger_pending;        /* 14 */
    int16_t stagger_already_acted;  /* 16 */
    int16_t clear_partner_stagger;  /* 18 */
    int16_t pair_synergy;           /* 20 */
    int16_t repeat_penalty;         /* 22 */
    int16_t defensive_low_hp;       /* 24 */
    int16_t defensive_healthy;      /* 26 */
    int16_t score_min;              /* 28 */
    int16_t score_max;              /* 30 */
    uint16_t flags;                 /* 32 */
    uint16_t reserved;              /* 34 */
} AiProfileDef;
_Static_assert(sizeof(AiProfileDef) == 36, "AiProfileDef layout");

enum AiProfileFlags {
    AI_PROFILE_TUTORIAL_CONSTRAINTS = 1u << 0,
    AI_PROFILE_SCRIPTED_ROUND_ONE = 1u << 1,
    AI_PROFILE_SCORED_AFTER_SCRIPT = 1u << 2,
    AI_PROFILE_NO_RNG_TIES = 1u << 3,
    AI_PROFILE_DEFENSIVE_CAP = 1u << 4
};

typedef enum AiPolicyValue {
    AI_POLICY_TUTORIAL_CONSTRAINTS = 1,
    AI_POLICY_SCRIPTED_THEN_SCORED = 2
} AiPolicyValue;
```

The complete AiProfileDef rows are emitted field-for-field in struct order after `id`:

| id | policy, defensive cap | advantage, disadvantage, KO, low HP, stage | stagger pending, acted, clear | pair, repeat, defensive low, healthy | score min/max | flags / reserved |
|---|---|---|---|---|---|---|
| `AI_TUTORIAL_GATED` | `AI_POLICY_TUTORIAL_CONSTRAINTS, 0` | `0, 0, 0, 0, 0` | `0, 0, 0` | `0, 0, 0, 0` | `0 / 0` | `AI_PROFILE_TUTORIAL_CONSTRAINTS + AI_PROFILE_NO_RNG_TIES / 0` |
| `AI_RUSK_SUPPORT` | `AI_POLICY_SCRIPTED_THEN_SCORED, 30` | `24, -16, 60, 12, 10` | `18, 8, 22` | `48, -14, 16, -12` | `-128 / 255` | `AI_PROFILE_SCRIPTED_ROUND_ONE + AI_PROFILE_SCORED_AFTER_SCRIPT + AI_PROFILE_NO_RNG_TIES + AI_PROFILE_DEFENSIVE_CAP / 0` |

`AiProfileDef.flags` accepts only mask `0x001F`. The tutorial row's all-zero scoring bounds/weights mean TutorialScript is the sole legal-choice constraint; Rusk's exact nonzero weights are those above. Any policy/flag/weight contradiction, unknown bit, or nonzero reserved fails generation. `expected_damage` is the exact ordinary damage formula with current effective stats, affinity, and fixed variance 256, summed once per living resolved target and capped at 80; it never consumes RNG and ignores future status draws. Each legal damaging action starts with that value; support starts at 0. A defensive action is heal/Guard/cleanse. It is removed from enumeration when choosing it would make `10*(defensive_actions+1) > 3*(total_actions+1)`, unless no nondefensive legal action exists. Legal two-actor pairs score the clamped action sum plus pair synergy, then clamp `[-256,511]`.

Round 1 uses the locked script above. Later rounds enumerate all legal `(move,target)` actions and legal two-actor pairs, never inspect unconfirmed player commands, and sort equal final scores by the tuple `(left MoveId,left target instance,right MoveId,right target instance)`. No RNG is consumed. Goldens prove: equal actions choose lower MoveId/target without advancing xorshift; an otherwise equal advantage attack beats neutral by 24 and disadvantage by 40; expected KO adds 60; Boiler+boosted Pressure Leap adds exactly 48; third defensive choice in ten is allowed but a fourth is rejected when nondefensive legal options exist; repetition subtracts 14 then 28; all intermediate/final clamps hold.

### 6.1 Reward data

```c
typedef enum RewardIdValue {
    REWARD_NONE = 0,
    REWARD_RUSK_FIRST_WIN = 1
} RewardIdValue;

typedef struct RewardDef {
    RewardId id;                      /* 0 */
    CreatureId required_creature_a;  /* 2 */
    CreatureId required_creature_b;  /* 4 */
    uint16_t sync_delta_each;         /* 6 */
    uint8_t team_link_value;          /* 8 */
    uint8_t claim_bit_index;          /* 9 */
    uint16_t encounter_clear_bit;     /* 10 */
    uint16_t flags;                   /* 12: restore HP, saturating sync */
    uint16_t reserved;                /* 14 */
} RewardDef;
_Static_assert(sizeof(RewardDef) == 16, "RewardDef layout");

enum RewardFlags {
    REWARD_RESTORE_HP = 1u << 0,
    REWARD_SATURATING_SYNC = 1u << 1
};
```

`REWARD_RUSK_FIRST_WIN` is exactly Quarrune+Ayselor, `sync_delta_each=25`, `team_link_value=1`, claim bit `REWARD_RUSK_FIRST_WIN_BIT`, encounter-clear bit `ENCOUNTER_RUSK_COURTYARD`, and `flags=REWARD_SATURATING_SYNC`; `REWARD_RESTORE_HP` is deliberately clear. Reward flags accept only `0x0003` and reserved is zero. Starter acquisition initializes both Sync values and Team Link to zero; real-battle history initializes `last_battle_result=BATTLE_RESULT_NONE` and `last_encounter_id=0`. There is no other persistent Sync source before this reward. Victory validates the exact two-slot party and unclaimed bit, saturating-adds 25 to each Sync (cap 1000), sets Team Link to 1, sets encounter-clear, `FLAG_RUSK_BATTLE_WON`, claim bit, `FLAG_RUSK_BATTLE_REWARD_CLAIMED`, `last_battle_result=BATTLE_RESULT_WIN`, and `last_encounter_id=ENCOUNTER_RUSK_COURTYARD` in one scratch-progress transaction, then commits once; it preserves the exact post-battle HP. Re-entry with the claim bit applies no delta. Only `RUSK_POST_005` dismissal below restores both starters, matching the visible promise before door animation begins. `CHECKPOINT_RUSK_VICTORY` remains illegal until all reward facts, full HP, door open, Sync exactly 25/25, Team Link 1, and exact battle-history values hold.

### 6.2 Tutorial gate data

```c
enum TutorialLessonBits {
    TUTORIAL_LESSON_TWO_COMMANDS = 1u << 0,
    TUTORIAL_LESSON_LEGAL_TARGETS = 1u << 1,
    TUTORIAL_LESSON_HP_CALLOUT_ACK = 1u << 2,
    TUTORIAL_LESSON_HP_DELTA_OBSERVED = 1u << 3,
    TUTORIAL_LESSON_INFO_AFFINITY = 1u << 4,
    TUTORIAL_LESSON_SUPPORT = 1u << 5,
    TUTORIAL_LESSON_STAGGER = 1u << 6,
    TUTORIAL_LESSON_PARTNER_SETUP = 1u << 7,
    TUTORIAL_LESSON_RESONANCE_70 = 1u << 8,
    TUTORIAL_LESSON_FINISHER = 1u << 9
};

typedef enum TutorialEnemyPolicyIdValue {
    TUTORIAL_ENEMY_LOW_POWER_NONLETHAL = 1,
    TUTORIAL_ENEMY_NORMAL_NONLETHAL = 2,
    TUTORIAL_ENEMY_STAGGER_WHEN_LEGAL = 3,
    TUTORIAL_ENEMY_RESONANCE_SUPPORT_PRESSURE = 4,
    TUTORIAL_ENEMY_FINISHER_HOLD = 5
} TutorialEnemyPolicyIdValue;

typedef enum TutorialDialogueIdValue {
    TUTORIAL_GATE1_INSTRUCTION = 0x5501,
    TUTORIAL_GATE1_REPEAT = 0x5502,
    TUTORIAL_GATE2_INSTRUCTION = 0x5503,
    TUTORIAL_GATE2_REPEAT = 0x5504,
    TUTORIAL_GATE3_INSTRUCTION = 0x5505,
    TUTORIAL_GATE3_REPEAT = 0x5506,
    TUTORIAL_GATE4_INSTRUCTION = 0x5507,
    TUTORIAL_GATE4_REPEAT = 0x5508,
    TUTORIAL_GATE5_INSTRUCTION = 0x5509,
    TUTORIAL_GATE5_REPEAT = 0x550A
} TutorialDialogueIdValue;

typedef enum TutorialRuntimePhaseValue {
    TUTORIAL_RUNTIME_UNOWNED = 0,
    TUTORIAL_RUNTIME_INTRO_FLYIN = 1,
    TUTORIAL_RUNTIME_INTRO_DIALOGUE = 2,
    TUTORIAL_RUNTIME_GATE_1 = 3,
    TUTORIAL_RUNTIME_GATE_2 = 4,
    TUTORIAL_RUNTIME_GATE_3 = 5,
    TUTORIAL_RUNTIME_GATE_4 = 6,
    TUTORIAL_RUNTIME_GATE_5 = 7,
    TUTORIAL_RUNTIME_RESULT = 8,
    TUTORIAL_RUNTIME_INTERRUPTED = 9,
    TUTORIAL_RUNTIME_RESTARTING = 10
} TutorialRuntimePhaseValue;

typedef enum TutorialOwnerEventValue {
    TUTORIAL_EVENT_GATE1_INSTRUCTION_REQUIRED = 1,
    TUTORIAL_EVENT_GATE1_ACCEPTED = 2,
    TUTORIAL_EVENT_GATE2_INSTRUCTION_REQUIRED = 3,
    TUTORIAL_EVENT_GATE2_UNMET = 4,
    TUTORIAL_EVENT_GATE2_ACCEPTED = 5,
    TUTORIAL_EVENT_GATE3_INSTRUCTION_REQUIRED = 6,
    TUTORIAL_EVENT_GATE3_UNMET = 7,
    TUTORIAL_EVENT_GATE3_ACCEPTED = 8,
    TUTORIAL_EVENT_GATE4_INSTRUCTION_REQUIRED = 9,
    TUTORIAL_EVENT_GATE4_UNMET = 10,
    TUTORIAL_EVENT_GATE4_FULL = 11,
    TUTORIAL_EVENT_GATE5_INSTRUCTION_REQUIRED = 12,
    TUTORIAL_EVENT_GATE5_UNMET = 13,
    TUTORIAL_EVENT_GATE5_FINISHER_RESOLVED = 14,
    TUTORIAL_EVENT_IMPOSSIBLE_STATE = 15,
    TUTORIAL_EVENT_PRE_GATE5_EARLY_KO_CLAMP = 16,
    TUTORIAL_EVENT_GATE1_UNMET = 17
} TutorialOwnerEventValue;

enum TutorialEventRouteFlags {
    TUTORIAL_EVENT_ACQUIRE_ROOT = 1u << 0,
    TUTORIAL_EVENT_ADVANCE_PHASE_ON_CLOSE = 1u << 1,
    TUTORIAL_EVENT_ADVANCE_PHASE_IMMEDIATE = 1u << 2,
    TUTORIAL_EVENT_REPEAT_SAFE = 1u << 3,
    TUTORIAL_EVENT_OVERLAY = 1u << 4,
    TUTORIAL_EVENT_INTERRUPT_BEFORE_ROOT = 1u << 5
};

typedef struct TutorialEventToken {
    uint32_t runtime_generation;  /* 0 */
    uint32_t tutorial_generation; /* 4 */
    uint32_t battle_generation;   /* 8 */
    uint32_t event_epoch;         /* 12: nonzero, monotonic per tutorial owner */
    EncounterId encounter_id;     /* 16 */
    uint8_t phase;                /* 18: TutorialRuntimePhaseValue */
    uint8_t event_id;             /* 19: TutorialOwnerEventValue */
} TutorialEventToken;
_Static_assert(sizeof(TutorialEventToken) == 20, "TutorialEventToken layout");

typedef struct TutorialEventRouteDef {
    uint8_t event_id;          /* 0: TutorialOwnerEventValue */
    uint8_t gate_id;           /* 1: 0 or exact TutorialGateDef id */
    uint16_t legal_phase_mask; /* 2: bit n is TutorialRuntimePhaseValue n */
    DialogueId root_id;        /* 4: zero only for an immediate phase edge */
    uint8_t next_phase;        /* 6: zero means preserve current phase */
    uint8_t priority;          /* 7: larger preempts a lower pending callout */
    uint16_t flags;            /* 8: TutorialEventRouteFlags */
    uint16_t reserved;         /* 10: zero */
} TutorialEventRouteDef;
_Static_assert(sizeof(TutorialEventRouteDef) == 12, "TutorialEventRouteDef layout");

typedef enum TutorialBootstrapSourceKindValue {
    TUTORIAL_BOOTSTRAP_TRANSITION_OUTCOME = 1,
    TUTORIAL_BOOTSTRAP_CONTINUE_STABLE = 2
} TutorialBootstrapSourceKindValue;

enum TutorialBootstrapFlags {
    TUTORIAL_BOOTSTRAP_CONSTRUCT_EXACT_ONCE = 1u << 0,
    TUTORIAL_BOOTSTRAP_STAGE_ALL_ACTORS = 1u << 1,
    TUTORIAL_BOOTSTRAP_REQUIRE_COHERENT_SPAWN = 1u << 2,
    TUTORIAL_BOOTSTRAP_INTRO_BEFORE_DIALOGUE = 1u << 3,
    TUTORIAL_BOOTSTRAP_BIND_GENERATIONS = 1u << 4
};

typedef struct TutorialEncounterBootstrapDef {
    uint8_t source_kind;             /* 0 */
    uint8_t reserved0;               /* 1 */
    uint16_t source_id;              /* 2: TransitionId or CheckpointId */
    EncounterId encounter_id;        /* 4 */
    uint16_t tutorial_script_id;     /* 6 */
    SceneId scene_id;                /* 8 */
    ZoneId zone_id;                  /* 10 */
    SpawnId spawn_id;                /* 12 */
    uint16_t flyin_ticks;            /* 14: fixed 30 Hz */
    uint16_t flags;                  /* 16 */
    uint16_t reserved1;              /* 18 */
} TutorialEncounterBootstrapDef;
_Static_assert(sizeof(TutorialEncounterBootstrapDef) == 20, "TutorialEncounterBootstrapDef layout");

static const TutorialEncounterBootstrapDef TUTORIAL_BOOTSTRAPS[2] = {
    { TUTORIAL_BOOTSTRAP_TRANSITION_OUTCOME, 0, TRANS_DEF_NAME_TO_SIM,
      ENCOUNTER_SIM_TUTORIAL, TUTORIAL_SCRIPT_OPENING,
      SCENE_SIM_ARENA, ZONE_SIM_ARENA, SPAWN_SIM_INTRO, 210,
      TUTORIAL_BOOTSTRAP_CONSTRUCT_EXACT_ONCE + TUTORIAL_BOOTSTRAP_STAGE_ALL_ACTORS +
      TUTORIAL_BOOTSTRAP_REQUIRE_COHERENT_SPAWN + TUTORIAL_BOOTSTRAP_INTRO_BEFORE_DIALOGUE +
      TUTORIAL_BOOTSTRAP_BIND_GENERATIONS, 0 },
    { TUTORIAL_BOOTSTRAP_CONTINUE_STABLE, 0, CHECKPOINT_AFTER_NAME,
      ENCOUNTER_SIM_TUTORIAL, TUTORIAL_SCRIPT_OPENING,
      SCENE_SIM_ARENA, ZONE_SIM_ARENA, SPAWN_SIM_INTRO, 210,
      TUTORIAL_BOOTSTRAP_CONSTRUCT_EXACT_ONCE + TUTORIAL_BOOTSTRAP_STAGE_ALL_ACTORS +
      TUTORIAL_BOOTSTRAP_REQUIRE_COHERENT_SPAWN + TUTORIAL_BOOTSTRAP_INTRO_BEFORE_DIALOGUE +
      TUTORIAL_BOOTSTRAP_BIND_GENERATIONS, 0 }
};

The Name-to-Sim row fires only after its post recipe and save outcome resolve; the Continue row fires only after the After-Name page is fully decoded, validated, and initially stable. Either row reserves one battle owner, constructs `ENCOUNTER_SIM_TUTORIAL` once, binds the live runtime/battle/tutorial generations, installs Kilnback/Nacreel/Gyreclast/Kivarrax from the literal TeamDefs at their coherent sim spawn slots, and enters `TUTORIAL_RUNTIME_INTRO_FLYIN`. It resolves all four models, nameplates, tactical UI, arena, and camera before publishing ownership. The exact `210` presentation ticks are seven seconds and pause on controller loss; the authored fly-in must complete every blocking camera/actor event before the owner advances to `TUTORIAL_RUNTIME_INTRO_DIALOGUE`. Live Name-to-Sim completion then emits `STORY_START_SOURCE_TUTORIAL_INTRO_COMPLETE`; loaded After-Name completion instead releases its delayed `STORY_START_SOURCE_CONTINUE_LOADED_STABLE` edge. It never emits both. Each source acquires `SIM_001` before player input under the same generation/precondition, and neither `SIM_001` nor `SIM_002` constructs actors. Duplicate bootstrap source, a second construction in the same generations, missing intro presentation, nonzero reserved, wrong tuple/team/script, dual-source emission, or dialogue before intro completion fails closed. Restart/Continue gets a fresh generation and exactly one new construction; a stale completion cannot start dialogue.

The tutorial event router is the only owner allowed to turn lesson state into a
Dialogue root or a phase edge. Its seventeen rows are literal and set-equal with
the tutorial-owned event table in `DIALOGUE_GRAPH.md`:

```c
static const TutorialEventRouteDef TUTORIAL_EVENT_ROUTES[17] = {
    { TUTORIAL_EVENT_GATE1_INSTRUCTION_REQUIRED, 1, 0x0008, TUTORIAL_GATE1_INSTRUCTION,
      0, 10, TUTORIAL_EVENT_ACQUIRE_ROOT, 0 },
    { TUTORIAL_EVENT_GATE1_ACCEPTED, 1, 0x0008, SIM_G1_DONE,
      TUTORIAL_RUNTIME_GATE_2, 12,
      TUTORIAL_EVENT_ACQUIRE_ROOT + TUTORIAL_EVENT_ADVANCE_PHASE_ON_CLOSE, 0 },
    { TUTORIAL_EVENT_GATE2_INSTRUCTION_REQUIRED, 2, 0x0010, TUTORIAL_GATE2_INSTRUCTION,
      0, 10, TUTORIAL_EVENT_ACQUIRE_ROOT, 0 },
    { TUTORIAL_EVENT_GATE2_UNMET, 2, 0x0010, TUTORIAL_GATE2_REPEAT,
      0, 8, TUTORIAL_EVENT_ACQUIRE_ROOT + TUTORIAL_EVENT_REPEAT_SAFE, 0 },
    { TUTORIAL_EVENT_GATE2_ACCEPTED, 2, 0x0010, 0,
      TUTORIAL_RUNTIME_GATE_3, 12, TUTORIAL_EVENT_ADVANCE_PHASE_IMMEDIATE, 0 },
    { TUTORIAL_EVENT_GATE3_INSTRUCTION_REQUIRED, 3, 0x0020, TUTORIAL_GATE3_INSTRUCTION,
      0, 10, TUTORIAL_EVENT_ACQUIRE_ROOT, 0 },
    { TUTORIAL_EVENT_GATE3_UNMET, 3, 0x0020, TUTORIAL_GATE3_REPEAT,
      0, 8, TUTORIAL_EVENT_ACQUIRE_ROOT + TUTORIAL_EVENT_REPEAT_SAFE, 0 },
    { TUTORIAL_EVENT_GATE3_ACCEPTED, 3, 0x0020, 0,
      TUTORIAL_RUNTIME_GATE_4, 12, TUTORIAL_EVENT_ADVANCE_PHASE_IMMEDIATE, 0 },
    { TUTORIAL_EVENT_GATE4_INSTRUCTION_REQUIRED, 4, 0x0040, TUTORIAL_GATE4_INSTRUCTION,
      0, 10, TUTORIAL_EVENT_ACQUIRE_ROOT, 0 },
    { TUTORIAL_EVENT_GATE4_UNMET, 4, 0x0040, TUTORIAL_GATE4_REPEAT,
      0, 8, TUTORIAL_EVENT_ACQUIRE_ROOT + TUTORIAL_EVENT_REPEAT_SAFE, 0 },
    { TUTORIAL_EVENT_GATE4_FULL, 4, 0x0040, SIM_G4_FULL,
      TUTORIAL_RUNTIME_GATE_5, 12,
      TUTORIAL_EVENT_ACQUIRE_ROOT + TUTORIAL_EVENT_ADVANCE_PHASE_ON_CLOSE, 0 },
    { TUTORIAL_EVENT_GATE5_INSTRUCTION_REQUIRED, 5, 0x0080, TUTORIAL_GATE5_INSTRUCTION,
      0, 10, TUTORIAL_EVENT_ACQUIRE_ROOT, 0 },
    { TUTORIAL_EVENT_GATE5_UNMET, 5, 0x0080, TUTORIAL_GATE5_REPEAT,
      0, 8, TUTORIAL_EVENT_ACQUIRE_ROOT + TUTORIAL_EVENT_REPEAT_SAFE, 0 },
    { TUTORIAL_EVENT_GATE5_FINISHER_RESOLVED, 5, 0x0080, SIM_G5_DONE,
      TUTORIAL_RUNTIME_RESULT, 20,
      TUTORIAL_EVENT_ACQUIRE_ROOT + TUTORIAL_EVENT_ADVANCE_PHASE_ON_CLOSE, 0 },
    { TUTORIAL_EVENT_IMPOSSIBLE_STATE, 0, 0x00F8, SIM_RESULT_INTERRUPTED,
      TUTORIAL_RUNTIME_INTERRUPTED, 30,
      TUTORIAL_EVENT_ACQUIRE_ROOT + TUTORIAL_EVENT_INTERRUPT_BEFORE_ROOT, 0 },
    { TUTORIAL_EVENT_PRE_GATE5_EARLY_KO_CLAMP, 0, 0x0078,
      SIM_RESULT_CALIBRATION_HOLD, 0, 5,
      TUTORIAL_EVENT_ACQUIRE_ROOT + TUTORIAL_EVENT_REPEAT_SAFE +
      TUTORIAL_EVENT_OVERLAY, 0 },
    { TUTORIAL_EVENT_GATE1_UNMET, 1, 0x0008, TUTORIAL_GATE1_REPEAT,
      0, 8, TUTORIAL_EVENT_ACQUIRE_ROOT + TUTORIAL_EVENT_REPEAT_SAFE, 0 }
};
```

Phase masks accept only bits `0..10`; route flags accept only `0x003F`. Every
nonzero root resolves to one Dialogue Graph node. Root zero is legal only for
the two immediate accepted edges, which must carry
`ADVANCE_PHASE_IMMEDIATE`, a nonzero next phase, and no acquisition flag.
Every other row that changes phase does so atomically either before root
acquisition (`IMPOSSIBLE_STATE`) or on the generation-current terminal close;
no command boundary can observe an intermediate phase. The `GATE2_ACCEPTED`
and `GATE3_ACCEPTED` edges deliberately have no extra line of dialogue, but are
typed events rather than hard-coded controller increments.

Every emitted event is the exact 20-byte token above. The router requires all
three owner generations, encounter, phase, and nonzero epoch to match before it
resolves a row. Accepting a token records that epoch before acquisition or
phase publish; a repeated or stale token is ignored. At most one non-overlay
tutorial root is pending. Story and encounter-result roots preempt tutorial
callouts, while the early-KO overlay may auto-close without consuming a command
edge. An event missing from this exact table, an extra route, duplicate event,
phase-mask/gate disagreement, wrong root, root-zero acquisition, stale terminal
close, or two pending primary roots fails generation/runtime closed.

typedef struct TutorialScriptDef {
    uint16_t id;                         /* 0 */
    EncounterId encounter_id;            /* 2 */
    uint16_t first_gate;                  /* 4 */
    uint8_t gate_count;                   /* 6: exactly 5 */
    uint8_t flags;                        /* 7 */
    uint8_t min_resonance_before_calibration; /* 8: 70 */
    uint8_t calibration_value;            /* 9: 100 */
    uint8_t prefinisher_ko_hold_hp;       /* 10: 1 */
    uint8_t reserved0;                    /* 11 */
    MoveId completion_move_id;            /* 12: SUNLINE_CASCADE */
    uint16_t reserved1;                   /* 14 */
} TutorialScriptDef;
_Static_assert(sizeof(TutorialScriptDef) == 16, "TutorialScriptDef layout");

enum TutorialScriptFlags {
    TUTORIAL_SCRIPT_CALIBRATE_ONCE = 1u << 0,
    TUTORIAL_SCRIPT_PREFINISHER_KO_HOLD = 1u << 1,
    TUTORIAL_SCRIPT_IMMUTABLE_SEED = 1u << 2
};

typedef struct TutorialGateDef {
    uint16_t gate_id;              /* 0 */
    uint16_t required_lesson_bits; /* 2 */
    uint32_t accepted_tag_mask;    /* 4 */
    uint8_t required_actor_count;  /* 8 */
    uint8_t min_resonance;         /* 9 */
    uint16_t enemy_policy_id;      /* 10 */
    DialogueId instruction_id;     /* 12 */
    DialogueId repeat_id;          /* 14 */
    uint16_t flags;                /* 16 */
    uint16_t reserved;             /* 18 */
} TutorialGateDef;
_Static_assert(sizeof(TutorialGateDef) == 20, "TutorialGateDef layout");

enum TutorialRestartFlags {
    TUTORIAL_RESTART_REQUIRE_INTERRUPTED_PHASE = 1u << 0,
    TUTORIAL_RESTART_DESTROY_BATTLE_OWNER = 1u << 1,
    TUTORIAL_RESTART_DESTROY_LOCAL_LESSONS = 1u << 2,
    TUTORIAL_RESTART_PRESERVE_NAME_SETTINGS = 1u << 3,
    TUTORIAL_RESTART_REQUIRE_STORY_UNCHANGED = 1u << 4,
    TUTORIAL_RESTART_REBUILD_IMMUTABLE_DEFS = 1u << 5,
    TUTORIAL_RESTART_ADVANCE_ALL_GENERATIONS = 1u << 6,
    TUTORIAL_RESTART_BLOCK_INPUT_UNTIL_COHERENT = 1u << 7
};

typedef struct TutorialRestartDef {
    StoryActionListId action_list_id; /* 0 */
    EncounterId encounter_id;        /* 2 */
    uint16_t tutorial_script_id;     /* 4 */
    SceneId scene_id;                /* 6 */
    ZoneId zone_id;                  /* 8 */
    SpawnId spawn_id;                /* 10 */
    uint32_t encounter_seed;         /* 12 */
    uint8_t required_phase;          /* 16 */
    uint8_t restart_phase;           /* 17 */
    uint16_t flags;                  /* 18 */
    uint16_t coherent_hold_ticks;    /* 20: fixed 30 Hz */
    uint16_t reserved;               /* 22: zero */
} TutorialRestartDef;
_Static_assert(sizeof(TutorialRestartDef) == 24, "TutorialRestartDef layout");

enum TutorialGateFlags {
    TUTORIAL_GATE_REPEAT_SAFE = 1u << 0,
    TUTORIAL_GATE_REQUIRE_VISIBLE_PRESENTATION = 1u << 1,
    TUTORIAL_GATE_CALIBRATION_OWNER = 1u << 2,
    TUTORIAL_GATE_FINISHER_ONLY = 1u << 3
};
```

The sole restart row is literal:

| Story action | Encounter / script | Scene / zone / spawn | Seed | Required / restart phase | Flags / coherent hold / reserved |
|---|---|---|---:|---|---|
| `ACTION_SIM_TUTORIAL_RESTART` | `ENCOUNTER_SIM_TUTORIAL / TUTORIAL_SCRIPT_OPENING` | `SCENE_SIM_ARENA / ZONE_SIM_ARENA / SPAWN_SIM_INTRO` | `0x53494D31` | `TUTORIAL_RUNTIME_INTERRUPTED / TUTORIAL_RUNTIME_GATE_1` | `REQUIRE_INTERRUPTED_PHASE + DESTROY_BATTLE_OWNER + DESTROY_LOCAL_LESSONS + PRESERVE_NAME_SETTINGS + REQUIRE_STORY_UNCHANGED + REBUILD_IMMUTABLE_DEFS + ADVANCE_ALL_GENERATIONS + BLOCK_INPUT_UNTIL_COHERENT / 60 / 0` |

Restart is selected only by the generation-current dismissal of
`SIM_RESULT_RESTART`. Before destroying anything, it resolves this row, the
exact EncounterDef, both immutable TeamDefs, the five TutorialGateDefs, every
required model/UI resource, and a fresh battle/tutorial/dialogue owner slot.
It snapshots a hash of persistent `GameProgress` and sanitized settings for a
postcondition check, quiesces presentation, fences renderer/audio users, moves
the tutorial owner to `RESTARTING`, and destroys the old battle plus every
tutorial-local lesson, hold, calibration, meter, command, status, event, and
dialogue owner. It then constructs the exact four actors from the immutable
encounter/team definitions and seed `0x53494D31`, advances runtime, battle,
tutorial, dialogue, and event epochs to fresh nonzero values, and publishes
`GATE_1` only after scene/spawn/camera/UI coherence and the 60-tick authored
recalibration dissolve complete. The next legal event is exactly
`GATE1_INSTRUCTION_REQUIRED`.

Name, sanitized settings, campaign seed, opening-seen state, and the coherent
After-Name progress remain byte-identical; `tutorial_complete` remains false.
No reward, HP, status, lesson bit, meter, or partial action is serialized or
carried. Resource reservation failure leaves the interrupted owner and Restart
choice intact; failure after teardown reconstructs the same interrupted page
from the reserved process-safe resources before input returns. A stale dismiss,
wrong phase/tuple/seed, reused generation, persistent-progress hash change,
partial actor set, or input before coherence fails closed. This is the only
runtime tutorial-restart path; neither EncounterDef defeat xrefs nor scene code
may manufacture a restart.

The sole TutorialScriptDef initializer is `{ TUTORIAL_SCRIPT_OPENING, ENCOUNTER_SIM_TUTORIAL, 1, 5, TUTORIAL_SCRIPT_CALIBRATE_ONCE + TUTORIAL_SCRIPT_PREFINISHER_KO_HOLD + TUTORIAL_SCRIPT_IMMUTABLE_SEED, 70, 100, 1, 0, SUNLINE_CASCADE, 0 }` in struct field order.

The five TutorialGateDef rows are literal:

| gate | required lesson bits | accepted tag mask | actors / min meter | enemy policy | instruction / repeat | flags / reserved |
|---:|---|---|---|---|---|---|
| 1 | `TUTORIAL_LESSON_TWO_COMMANDS + TUTORIAL_LESSON_LEGAL_TARGETS + TUTORIAL_LESSON_HP_CALLOUT_ACK + TUTORIAL_LESSON_HP_DELTA_OBSERVED` | `RES_TAG_DAMAGE` | `2 / 0` | `TUTORIAL_ENEMY_LOW_POWER_NONLETHAL` | `TUTORIAL_GATE1_INSTRUCTION / TUTORIAL_GATE1_REPEAT` | `TUTORIAL_GATE_REPEAT_SAFE + TUTORIAL_GATE_REQUIRE_VISIBLE_PRESENTATION / 0` |
| 2 | `TUTORIAL_LESSON_INFO_AFFINITY` | `RES_TAG_DAMAGE` | `2 / 0` | `TUTORIAL_ENEMY_NORMAL_NONLETHAL` | `TUTORIAL_GATE2_INSTRUCTION / TUTORIAL_GATE2_REPEAT` | `TUTORIAL_GATE_REPEAT_SAFE / 0` |
| 3 | `TUTORIAL_LESSON_SUPPORT + TUTORIAL_LESSON_STAGGER` | `RES_TAG_ALLY + RES_TAG_POWER + RES_TAG_GUARD + RES_TAG_SPEED + RES_TAG_STAGGER` | `1 / 0` | `TUTORIAL_ENEMY_STAGGER_WHEN_LEGAL` | `TUTORIAL_GATE3_INSTRUCTION / TUTORIAL_GATE3_REPEAT` | `TUTORIAL_GATE_REPEAT_SAFE / 0` |
| 4 | `TUTORIAL_LESSON_PARTNER_SETUP + TUTORIAL_LESSON_RESONANCE_70` | `RES_TAG_DAMAGE + RES_TAG_ALLY + RES_TAG_POWER + RES_TAG_GUARD + RES_TAG_SPEED + RES_TAG_EMPOWER` | `2 / 70` | `TUTORIAL_ENEMY_RESONANCE_SUPPORT_PRESSURE` | `TUTORIAL_GATE4_INSTRUCTION / TUTORIAL_GATE4_REPEAT` | `TUTORIAL_GATE_REPEAT_SAFE + TUTORIAL_GATE_CALIBRATION_OWNER / 0` |
| 5 | `TUTORIAL_LESSON_FINISHER` | `RES_TAG_DUO` | `2 / 100` | `TUTORIAL_ENEMY_FINISHER_HOLD` | `TUTORIAL_GATE5_INSTRUCTION / TUTORIAL_GATE5_REPEAT` | `TUTORIAL_GATE_REPEAT_SAFE + TUTORIAL_GATE_FINISHER_ONLY / 0` |

Script flags accept only mask `0x07`; gate flags accept only `0x000F`; all reserved fields are zero. IDs are contiguous `1..5`, the Script range is exactly those five rows, every dialogue/policy resolves, `accepted_tag_mask` accepts only the declared Resonance tag mask, and the required bits are the exact predicate latch set. Any flag/predicate/threshold contradiction fails generation.

| Gate | Completion predicate | Enemy/hold policy |
|---|---|---|
| 1 commands/targets/HP | both loaners receive legal commands and legal target masks; HP panel callout is acknowledged and at least one real HP delta is visibly resolved | low-power legal attacks; loaners cannot be KO'd; gate cannot complete before HP observation bits |
| 2 info/order/affinity | info opened then closed; STRONG and RESISTED previews observed; any legal choices accepted | normal deterministic queue, nonlethal loaner pressure |
| 3 support/effects | at least one legal support/debuff action commits | legal Gyreclast Fault Pin demonstrates Staggered when possible; loaners have no cleanse and are never asked to invent a fifth move |
| 4 Resonance | one partner-directed setup→that partner's follow-through has committed and honest meter is `>=70` | legal guard/support pressure; calibration to 100 once only after predicate; cleanse +8 appears only as a forward glossary hint |
| 5 finisher | committed `SUNLINE_CASCADE` with both loaners conscious | non-finisher choices repeat safely; only the finisher may complete both opponent KOs |

Before Gate 5, ordinary damage that would KO a tutorial opponent clamps it to exactly 1 simulated HP and emits `CALIBRATION HOLD`; this is an explicit gate constraint on the same damage events, not alternate hidden HP. Gate 5 removes the hold and Sunline's HP-equal scripted events finish both. Tutorial-local lesson bits, hold mask, calibration-used bit, cooldown/once bits, meter, and battle state are never saved. The typed `ACTION_SIM_TUTORIAL_RESTART` route above destroys them and recreates the encounter from `0x53494D31`, preserving name/settings and `tutorial_complete=false` without mutating persistent story state.

Gate 1 goldens reject completion after two command selections alone, set `HP_CALLOUT_ACK` only when the production HP blocks are focused/dismissed, set `HP_DELTA_OBSERVED` only when a nonzero committed HP event has completed presentation, then accept the four-bit commands/targets/HP predicate. Miss/no-op, a hidden/clipped HP block, and calibration hold without its visible HP event do not satisfy observation.

Gate 4 carries the honest clamped meter `P` produced by Gates 1-3; it never resets it. Primary increments are: Conductive Veil→Kilnback (+14), Kilnback Cinder Charge→Gyreclast (+6 damage,+12 follow), total `P+32`; Flow Switch (+10), Kilnback Cinder Charge→Gyreclast (+6,+12), total `P+60`; if still needed, Nacreel Arc Jet→Kivarrax (+6), Kilnback Cinder Charge→Kivarrax (+6,+4 advantage), total `P+76`, all clamped at 100. Alternate increments are Arc Jet (+6), Bellows Guard (+10)=`P+16`; Conductive Veil→Kilnback (+14), Cinder Charge→Gyreclast (+6,+12)=`P+48`; Flow Switch (+10), Cinder Charge→Kivarrax (+6,+4,+12)=`P+80`. The script stops repeating once both the setup/follow predicate and meter `>=70` hold. If entry `P>=70`, it still requires one partner setup/follow but does not reset; if the resulting meter is 70-99 calibration sets 100 once, while an already-100 meter skips calibration. Parameterized goldens cover `P=0` only as a lower-bound test fixture plus real carried values 69, 70, 99, and 100. Neither path includes a loaner cleanse.

## 7. Battle runtime state

Runtime battle data is never saved as an EEPROM image. A resume always returns to the last committed safe scene; Retry uses an in-memory `GameProgress` snapshot.

```c
enum {
    BATTLE_MAX_ROSTER_PER_SIDE = 4,
    BATTLE_MAX_ACTORS          = 8,
    BATTLE_ACTIVE_PER_SIDE     = 2,
    BATTLE_MAX_COMMANDS        = 8,
    BATTLE_EVENT_QUEUE_CAP     = 64,
    RESONANCE_MAX              = 100
};

enum BattleVolatileFlags {
    BATTLE_VOLATILE_GUIDING_DRAFT = 1u << 0
};

enum BattleActorFlags {
    BATTLE_ACTOR_ACTIVE = 1u << 0,
    BATTLE_ACTOR_KO = 1u << 1,
    BATTLE_ACTOR_COMMAND_LOCKED = 1u << 2
};

enum BattleCommandFlags {
    BATTLE_COMMAND_VALIDATED = 1u << 0,
    BATTLE_COMMAND_LINKED = 1u << 1,
    BATTLE_COMMAND_COMMITTED = 1u << 2
};

enum ResonanceSetupFlags {
    RESONANCE_SETUP_VALID = 1u << 0,
    RESONANCE_SETUP_CONSUMED = 1u << 1
};

enum BattlePendingFlags {
    BATTLE_PENDING_PRESENTATION = 1u << 0,
    BATTLE_PENDING_REPLACEMENT = 1u << 1,
    BATTLE_PENDING_RESULT_ACTION = 1u << 2,
    BATTLE_PENDING_RESELECTION = 1u << 3
};

typedef enum BattlePhase {
    BATTLE_PHASE_INTRO = 0,
    BATTLE_PHASE_COMMAND_SELECT,
    BATTLE_PHASE_TARGET_SELECT,
    BATTLE_PHASE_BUILD_TURN_QUEUE,
    BATTLE_PHASE_ACTION_BEGIN,
    BATTLE_PHASE_ACTION_PRESENT,
    BATTLE_PHASE_DAMAGE_STATUS_RESOLVE,
    BATTLE_PHASE_KNOCKOUT_REPLACE,
    BATTLE_PHASE_ROUND_CLEANUP,
    BATTLE_PHASE_VICTORY,
    BATTLE_PHASE_DEFEAT,
    BATTLE_PHASE_RESULT_PRESENT,
    BATTLE_PHASE_EXIT
} BattlePhase;

typedef enum BattleModeValue {
    BATTLE_MODE_TUTORIAL = 1,
    BATTLE_MODE_STORY = 2
} BattleModeValue;

typedef struct BattleActor {
    CreatureId creature_id;         /* 0 */
    uint8_t instance_id;            /* 2: stable 0..7 */
    uint8_t side;                   /* 3: 0 player, 1 enemy */
    uint8_t roster_index;           /* 4 */
    uint8_t lane;                   /* 5: 0 left, 1 right, 0xFF benched */
    uint8_t level;                  /* 6 */
    uint8_t flags;                  /* 7: active, KO, command locked */
    uint16_t current_hp;            /* 8 */
    uint16_t max_hp;                /* 10 */
    uint16_t effective_attack;      /* 12: displayed as Power */
    uint16_t effective_defense;     /* 14: displayed as Guard */
    uint16_t effective_speed;       /* 16 */
    BattleStatus status;            /* 18 */
    uint8_t move_cooldown[4];       /* 22 */
    int8_t power_stage;             /* 26: -2..+2 */
    int8_t guard_stage;             /* 27: -2..+2 */
    int8_t speed_stage;             /* 28: -2..+2 */
    uint8_t power_rounds;           /* 29 */
    uint8_t guard_rounds;           /* 30 */
    uint8_t speed_rounds;           /* 31 */
    uint8_t volatile_flags;         /* 32: Guiding Draft one-use flag */
    uint8_t once_used_mask;         /* 33: one bit per move slot */
    uint8_t cooldown_started_mask;  /* 34: suppress same-round decrement */
    uint8_t reserved0;              /* 35 */
    uint16_t power_applied_round;   /* 36 */
    uint16_t guard_applied_round;   /* 38 */
    uint16_t speed_applied_round;   /* 40 */
    uint16_t reserved1;             /* 42 */
    uint32_t last_resonance_tags;   /* 44 */
    uint16_t last_action_seq;       /* 48 */
    MoveId last_committed_move_id;  /* 50 */
    uint8_t consecutive_move_uses;  /* 52: capped at 3 */
    uint8_t reserved2[3];           /* 53 */
} BattleActor;
_Static_assert(sizeof(BattleActor) == 56, "BattleActor layout");

typedef enum BattleCommandKind {
    COMMAND_NONE     = 0,
    COMMAND_MOVE     = 1,
    COMMAND_DUO      = 2,
    COMMAND_REPLACE  = 3,
    COMMAND_FORFEIT  = 4
} BattleCommandKind;

typedef struct BattleCommand {
    uint8_t actor_instance_id; /* 0 */
    uint8_t kind;              /* 1 */
    uint8_t move_slot;         /* 2: 0..3 */
    uint8_t flags;             /* 3: validated, linked, committed */
    uint8_t target_mask;       /* 4: bit per actor instance */
    int8_t priority;           /* 5 */
    uint16_t speed_key;        /* 6 */
    uint16_t stable_key;       /* 8 */
    uint16_t action_seq;       /* 10; nonzero, wraps with idle gap */
    MoveId move_id;            /* 12 */
    uint16_t reserved;         /* 14 */
} BattleCommand;
_Static_assert(sizeof(BattleCommand) == 16, "BattleCommand layout");

typedef struct ResonanceSetupRecord {
    uint16_t round;                    /* 0 */
    uint16_t setup_action_seq;         /* 2 */
    uint8_t setup_source_instance_id;  /* 4 */
    uint8_t partner_instance_id;       /* 5: actor that must follow through */
    uint8_t flags;                     /* 6: valid, consumed */
    uint8_t reserved;                  /* 7 */
} ResonanceSetupRecord;
_Static_assert(sizeof(ResonanceSetupRecord) == 8, "ResonanceSetupRecord layout");

typedef struct BattleState {
    uint8_t phase;                  /* 0 */
    uint8_t mode;                   /* 1: tutorial or story */
    uint16_t round;                 /* 2 */
    uint32_t rng_state;             /* 4: xorshift32, never zero */
    EncounterId encounter_id;       /* 8 */
    uint16_t phase_tick;            /* 10 */
    uint8_t actor_count;            /* 12 */
    uint8_t active_mask;            /* 13 */
    uint8_t command_count;          /* 14 */
    uint8_t command_cursor;         /* 15 */
    uint8_t winner;                 /* 16: 0 none, 1 player, 2 enemy */
    uint8_t pending_lesson;         /* 17 */
    uint16_t lesson_bits;           /* 18 */
    uint16_t resonance;             /* 20: 0..100 */
    uint16_t next_action_seq;       /* 22 */
    uint16_t presenting_action_seq; /* 24; zero when not waiting */
    uint16_t pending_flags;         /* 26 */
    StoryActionListId result_action_xref; /* 28: equality-only diagnostic mirror */
    uint16_t reserved;              /* 30 */
    uint16_t ai_total_actions;      /* 32: committed enemy actions */
    uint16_t ai_defensive_actions;  /* 34 */
    ResonanceSetupRecord resonance_setup[2];     /* 36: one per player lane */
    BattleActor actors[BATTLE_MAX_ACTORS];       /* 52 */
    BattleCommand commands[BATTLE_MAX_COMMANDS]; /* 500 */
} BattleState;
_Static_assert(sizeof(BattleState) == 628, "BattleState layout");
```

Battle runtime masks are complete: `BattleActor.flags` accepts `0x07`, `volatile_flags` accepts `0x01`, `BattleCommand.flags` accepts `0x07`, `ResonanceSetupRecord.flags` accepts `0x03`, and `BattleState.pending_flags` accepts `0x000F`. ACTIVE and KO are mutually exclusive; COMMAND_LOCKED requires ACTIVE. LINKED requires a DUO command and paired command, COMMITTED requires VALIDATED, and no committed command may be edited. CONSUMED requires VALID and blocks a second award. Pending PRESENTATION iff `presenting_action_seq!=0`; REPLACEMENT/RESULT_ACTION/RESELECTION are mutually consistent with their exact phases. Reserved fields/bits are zero. Encounter construction and Retry clear command/setup/pending/volatile/once/cooldown state before rebuilding; KO sets KO, clears ACTIVE/volatile/stages/setup records, and cannot retain COMMAND_LOCKED. Unknown bits or illegal combinations assert in host/debug and fail generated fixtures.

`active_mask` contains exactly two living active bits per side until knockout/replacement or battle end. Actor instance IDs never change during an encounter. Commands sort by priority descending, speed descending, then stable key ascending; stable key is `(side << 8) | instance_id`. The seeded RNG uses a tested xorshift32 implementation with golden vectors; it is called only at documented accuracy, variance, and chance-status points. AI scoring ties sort by MoveId then target instance without RNG.

On each legal committed enemy action, `ai_total_actions` increments, `ai_defensive_actions` increments when its opcode class is defensive, and the actor's last MoveId/reuse count updates (same ID increments to a cap of 3, different ID resets to 1). Invalid-target no-ops update none of them. Encounter construction and Retry zero the counters/history; they are not saved. These fields are the only inputs for the defensive-cap/repetition terms in `AI_RUSK_SUPPORT`.

Simulation-to-presentation messages are fixed 16-byte events:

```c
typedef enum BattleEventTypeValue {
    BATTLE_EVENT_ACTION_START = 1,
    BATTLE_EVENT_ANIMATION = 2,
    BATTLE_EVENT_CAMERA = 3,
    BATTLE_EVENT_VFX = 4,
    BATTLE_EVENT_SFX = 5,
    BATTLE_EVENT_HP_DELTA = 6,
    BATTLE_EVENT_STATUS_APPLY = 7,
    BATTLE_EVENT_STATUS_REMOVE = 8,
    BATTLE_EVENT_STAGE_APPLY = 9,
    BATTLE_EVENT_STAGE_REMOVE = 10,
    BATTLE_EVENT_KNOCKOUT = 11,
    BATTLE_EVENT_RESONANCE_DELTA = 12,
    BATTLE_EVENT_TEXT = 13,
    BATTLE_EVENT_FINISHER_COMMIT = 14
} BattleEventTypeValue;

enum BattleEventFlags {
    BATTLE_EVENT_BLOCKING = 1u << 0,
    BATTLE_EVENT_MULTI_TARGET = 1u << 1,
    BATTLE_EVENT_SIMULATION_COMMITTED = 1u << 2,
    BATTLE_EVENT_HIGH_PRIORITY = 1u << 3
};

enum {
    BATTLE_INSTANCE_NONE = 0xFF,
    BATTLE_EVENT_DELAY_TICKS_MAX = 300
};

typedef enum BattleEventReasonValue {
    BATTLE_REASON_NONE = 0,
    BATTLE_REASON_MOVE_EFFECT = 1,
    BATTLE_REASON_EXPIRED = 2,
    BATTLE_REASON_CLEANSED = 3,
    BATTLE_REASON_KNOCKOUT = 4,
    BATTLE_REASON_REWARD = 5,
    BATTLE_REASON_TUTORIAL = 6
} BattleEventReasonValue;

typedef enum BattleTextFormatValue {
    BATTLE_TEXT_PLAIN = 0,
    BATTLE_TEXT_SOURCE_NAME = 1,
    BATTLE_TEXT_TARGET_NAME = 2,
    BATTLE_TEXT_MOVE_NAME = 3
} BattleTextFormatValue;

typedef struct BattleEvent {
    uint16_t action_seq;        /* 0 */
    uint8_t type;               /* 2 */
    uint8_t flags;              /* 3 */
    uint8_t source_instance_id; /* 4 */
    uint8_t target_mask;        /* 5 */
    int16_t amount;             /* 6 */
    uint16_t data0;             /* 8 */
    uint16_t data1;             /* 10 */
    uint16_t delay_ticks;       /* 12 */
    uint16_t reserved;          /* 14 */
} BattleEvent;
_Static_assert(sizeof(BattleEvent) == 16, "BattleEvent layout");

typedef struct BattleRuntimeOwner {
    uint32_t runtime_generation;          /* 0: copied from live GameProgress */
    uint32_t battle_generation;           /* 4: nonzero process counter */
    uint16_t last_accepted_action_seq;     /* 8 */
    uint16_t reserved;                     /* 10: zero */
} BattleRuntimeOwner;
_Static_assert(sizeof(BattleRuntimeOwner) == 12, "BattleRuntimeOwner layout");

typedef struct BattleEventQueueHeader {
    uint32_t runtime_generation_snapshot; /* 0 */
    uint32_t battle_generation_snapshot;  /* 4 */
    uint16_t read_index;                   /* 8: 0..63 */
    uint16_t write_index;                  /* 10: 0..63 */
    uint16_t count;                        /* 12: 0..64 */
    uint16_t reserved;                     /* 14: zero */
} BattleEventQueueHeader;
_Static_assert(sizeof(BattleEventQueueHeader) == 16, "BattleEventQueueHeader layout");

typedef enum BattlePresentationAckTypeValue {
    BATTLE_ACK_PRESENTATION_COMPLETE = 1
} BattlePresentationAckTypeValue;

typedef struct BattlePresentationAck {
    uint32_t runtime_generation; /* 0 */
    uint32_t battle_generation;  /* 4 */
    uint16_t action_seq;         /* 8 */
    uint8_t type;                /* 10: BattlePresentationAckTypeValue */
    uint8_t flags;               /* 11: zero in this chapter */
    uint32_t reserved;           /* 12 */
} BattlePresentationAck;
_Static_assert(sizeof(BattlePresentationAck) == 16, "BattlePresentationAck layout");
```

`EncounterDef.kind` accepts only `ENCOUNTER_KIND_TUTORIAL` or `ENCOUNTER_KIND_STORY`; `BattleState.mode` is the corresponding `BATTLE_MODE_*` value and must agree with the selected encounter. `BattleEvent.type` accepts only the 14 outbound simulation-to-presentation values above. The 64-entry outbound queue cannot overwrite unread events. Before an action enqueues, generation proves the complete worst-case dual-target/dual-KO/status/Resonance/finisher burst fits; overflow is an assertion and certification failure, never permission to drop presentation or simulation events.

Every outbound event obeys this exact payload contract. `source` is a live actor instance `0..7` unless the row permits `BATTLE_INSTANCE_NONE`; `one target` is a one-hot subset of the live actor mask; `resolved targets` is the already validated action mask. `data0`/`data1` IDs resolve in their typed registry. Unused fields and `reserved` are zero.

| Event type | Source / target mask | `amount` | `data0` / `data1` | `delay_ticks` | Exact legal flags and presenter mapping |
|---|---|---:|---|---:|---|
| `BATTLE_EVENT_ACTION_START` | acting instance / resolved targets | 0 | MoveId / command ordinal `0..7` | 0 | `BLOCKING + MULTI_TARGET`; bind action header, actor, move, targets |
| `BATTLE_EVENT_ANIMATION` | instance being animated / its one-hot bit | 0 | animation cue / blend ticks | `0..300` | `BLOCKING`; resolve actor AnimationSetId and play cue |
| `BATTLE_EVENT_CAMERA` | acting instance / resolved targets | 0 | CameraCueId / duration ticks | `0..300` | `BLOCKING + MULTI_TARGET + HIGH_PRIORITY`; resolve authored camera cue |
| `BATTLE_EVENT_VFX` | acting instance or none / resolved targets | scale Q8.8 `1..32767` | AssetId / anchor mode `0=world,1=source,2=each target` | `0..300` | `BLOCKING + MULTI_TARGET`; instantiate validated VFX at exact anchors |
| `BATTLE_EVENT_SFX` | acting instance or none / zero | gain Q8.8 `0..256` | AudioCueId / bus `1..6` | `0..300` | zero or `HIGH_PRIORITY`; schedule logical cue, never a filename |
| `BATTLE_EVENT_HP_DELTA` | effect source or none / one target | nonzero signed HP delta; damage negative | resulting HP / max HP | `0..300` | `SIMULATION_COMMITTED`; animate exact HP endpoints, never recalculate damage |
| `BATTLE_EVENT_STATUS_APPLY` | effect source / one target | remaining owner actions `1..255` | registered StatusId / `BATTLE_REASON_MOVE_EFFECT` | `0..300` | `SIMULATION_COMMITTED`; update icon/text from StatusDef |
| `BATTLE_EVENT_STATUS_REMOVE` | effect source or none / one target | 0 | registered StatusId / expired, cleansed, or knockout reason | `0..300` | `SIMULATION_COMMITTED`; remove exact icon and show reason-specific text |
| `BATTLE_EVENT_STAGE_APPLY` | effect source / one target | resulting signed stage `-2..2` | BattleStatId / remaining rounds `1..255` | `0..300` | `SIMULATION_COMMITTED`; update stat chevron/duration from committed value |
| `BATTLE_EVENT_STAGE_REMOVE` | effect source or none / one target | prior signed stage `-2..2`, nonzero | BattleStatId / expired, cleansed, or knockout reason | `0..300` | `SIMULATION_COMMITTED`; clear exact stat presentation |
| `BATTLE_EVENT_KNOCKOUT` | effect source or none / one target | 0 | target CreatureId / replacement instance `0..7` or `BATTLE_INSTANCE_NONE` | `0..300` | `BLOCKING + SIMULATION_COMMITTED + HIGH_PRIORITY`; play KO then replacement handoff |
| `BATTLE_EVENT_RESONANCE_DELTA` | awarding player instance, or none only for tutorial calibration / zero | nonzero signed delta | resulting meter `0..100` / ResonanceAwardKindValue | `0..300` | `SIMULATION_COMMITTED`; tween meter to exact endpoint once |
| `BATTLE_EVENT_TEXT` | instance or none / zero or one target | 0 | StringId / BattleTextFormatValue | `0..300` | zero or `HIGH_PRIORITY`; substitute exactly none/source/target/move and render in stable queue order |
| `BATTLE_EVENT_FINISHER_COMMIT` | linked leader instance / resolved enemy targets | `-100` | duo MoveId / resulting meter `0` | `0..300` | `BLOCKING + MULTI_TARGET + SIMULATION_COMMITTED + HIGH_PRIORITY`; play linked finisher package |

The table's flag shorthand denotes the declared `BATTLE_EVENT_*` bits. `BattleEvent.flags` accepts only mask `0x0F` and must be a subset of its row; required flags listed for committed mutations and finisher/KO/action ownership may not be omitted. `target_mask` cannot contain an inactive/unknown instance or be multi-bit unless `BATTLE_EVENT_MULTI_TARGET` is set. `action_seq` is nonzero and identical across one action burst. Events for an action are sorted by `(delay_ticks, generation source_index)`, with ACTION_START first at delay 0. Resonance `data1` must match the exact delta/predicate table above; `BATTLE_INSTANCE_NONE` is legal only for `RESONANCE_AWARD_TUTORIAL_CALIBRATION`, which is emitted by Gate 4's current-generation TutorialScript. Unknown event/reason/anchor/bus/text-format/award values, bad signed domains, unresolved references, nonzero unused/reserved fields, delay above 300, or payload/state disagreement fail generation/host tests and are rejected at runtime.

`delay_ticks` is an absolute offset from presentation tick 0 for that action, not a delay from the prior event and not a simulation tick. The fixed 30 Hz presentation clock advances only while battle presentation owns the active scene; Pause, controller-loss modal, transition fence, and retry/teardown stop it. At each tick, equal-delay events dispatch in queue source order. A `BATTLE_EVENT_BLOCKING` event registers a bounded presenter handle that must complete; nonblocking events still must dispatch. The presenter may acknowledge only after every event became eligible, every required mapping dispatched, and every blocking handle completed. `HIGH_PRIORITY` controls presentation layering/ducking only; `MULTI_TARGET` authorizes a multi-bit target mask; `SIMULATION_COMMITTED` means the presenter consumes the exact committed endpoint and can never mutate or recompute simulation.

The presenter resolves AnimationSet/camera/VFX/SFX/Status/stat/String/finisher references exactly as the row specifies. Required missing mappings are generation failures; an optional SFX may resolve to deliberate silence but still consumes its event. Unsupported animation, camera, VFX, UI, or text never falls back to an arbitrary asset. Host goldens compare the complete emitted event bytes and presenter dispatch trace for every move, status/stage path, KO/replacement, text, and both finishers.

One `BattleRuntimeOwner` owns the generation not stored in `BattleState`. Construction copies the current nonzero `GameProgress.runtime_generation` and obtains `battle_generation=next_nonzero(old)` where unsigned increment wraps `0xFFFFFFFF->1`; zero is never published. Each retry first advances the old battle generation before destroying queues, then construction obtains another fresh value. Teardown/scene exit advances the process counter before freeing presenter state. A `BattleEventQueueHeader` snapshots both owner generations when its empty 64-entry queue is created; no event from another generation may enter it. The presenter copies those exact snapshots into its acknowledgement. Thus an outbound burst, its presentation handles, and its inbound ack all share one explicit owner; a late event/ack from pre-retry or pre-teardown state cannot match.

Presenter acknowledgements travel through a separate fixed eight-entry presenter-to-simulation queue. The presenter emits one `BATTLE_ACK_PRESENTATION_COMPLETE` only after consuming every outbound event for that action sequence. Simulation accepts it only while waiting on the exact nonzero `presenting_action_seq` and when both runtime and battle generations match the live owners; acceptance clears the wait and records that sequence as consumed. Duplicate, zero, stale-runtime, stale-battle, future/wrong-sequence, unknown-type, or nonzero-reserved acknowledgements are rejected without advancing phase and increment a diagnostic counter. Queue overflow is a certification assertion. Retry and scene exit increment battle/runtime generations before destroying presenter state, making late acknowledgements harmless.

### 7.1 Damage, target, and finisher invariants

Damage is `base=max(1, move_power + (Power*3)/4 - Guard/2)` then `max(1, floor(base*affinity_q8*variance_q8/65536))`, using widened intermediates. Locked goldens are `(move,Power,Guard,affinity,variance)->damage`: `(28,40,30,256,256)->43`, `(26,43,38,384,256)->58`, `(32,48,28,192,256)->40`, `(29,41,46,256,240)->33`, and `(1,1,200,192,240)->1`.

- `current_hp <= max_hp`, KO iff `current_hp == 0`, and no negative intermediate is narrowed before clamping.
- Target masks contain only living active instances allowed by `TargetRule`.
- Execution revalidation may retarget to the lowest-lane then lowest-instance legal actor only when the move has `MOVE_RETARGET_SAME_SIDE`.
- An action's HP/status commit is accepted once for its nonzero `action_seq`.
- Resonance clamps to `[0,100]`; a duo command requires `100`, two living/available active allies, and a legal target.
- A duo command replaces both ally commands. It consumes Resonance at finisher commit, never during cursor preview. Partner invalidation before commit cancels without charge.
- Battle-end detection runs after each damage/status/KO resolution and before a no-target command.

If a linked finisher becomes invalid before commit while enemies remain, the simulation preserves Resonance 100, deletes the linked command, marks neither linked ally acted, and returns every surviving/available uncommitted ally whose command was replaced to legal command selection. Previously committed actors never receive another action. After replacement selections, it rebuilds only the unexecuted queue suffix; action-sequence/acted masks prevent double actions. If no enemy remains, victory takes precedence and command selection does not reopen.

Power/Guard/Speed stage values clamp independently to `[-2,+2]`. Stage multipliers are exactly `{-2:128, -1:192, 0:256, +1:320, +2:384}` in Q8.8. `effective = max(1, floor(level_derived_stat * multiplier / 256))`; Staggered, when present, then computes `effective_speed=max(1,floor(stage_adjusted_speed*192/256))`. Damage consumes effective Power/Guard and queue construction consumes effective Speed. Pressure Leap checks `power_stage > 0`, not the rounded value.

Applying another modifier adds then clamps the stage, refreshes duration to the greater authored remaining rounds, and records the current round for that stat. Round cleanup does not decrement a stage applied during that same round; on each later cleanup it decrements once and clears the stage at zero. Thus a one-round effect applied by the final actor remains meaningful through the next complete round. A Speed-stage apply/reapply recomputes the affected pending actor's key and stable-sorts only the unexecuted suffix, exactly like Staggered; already executed actions never move. Power/Guard never reorder. Golden tests cover one- and two-round effects applied by the first and last actor, refresh/clamp, pending Speed reorder, and expiry.

Knockout and battle end clear all three stages and Guiding Draft. Guiding Draft computes `empowered_damage=max(1,floor(normal_damage*120/100))` after affinity/variance and before HP clamp, then is consumed only after a damaging action legally commits and produces its damage event; misses/no-ops retain it.

Move availability is exact. `move_cooldown[slot]==0` is available; `1..2` is the number of future command-selection rounds still unavailable; `0xFF` is a validator-only absent-slot sentinel and is illegal for the four filled opening slots. A legal committed Fault Pin/Furnace Feint sets its slot to 2 and sets `cooldown_started_mask`; same-round cleanup clears that started bit without decrementing. The next two command selections reject the move, with intervening cleanups reducing 2→1→0, so it returns on the third. A target-invalid no-op does not start cooldown. Steady Pulse additionally requires its `once_used_mask` slot bit clear; the bit sets when its legal action commits, even if the target was full HP/already clean, and never clears through KO/replacement. Encounter construction and Retry reset all cooldowns, started bits, and once-use bits; battle end discards them. Goldens cover early/late commits, both unavailable selections, no-op, KO, and retry.

Resonance awards are ordered after successful effect resolution, require `source.side==player`, and are deduplicated by `action_seq` plus award source. Enemy-tagged actions always award zero:

| Source | Exact gain |
|---|---:|
| successful damaging action that deals at least 1 HP | +6 once per action |
| at least one affinity-advantage target hit by that action | +4 once per action |
| partner support | move-defined +10, +12, or +14; never also for self |
| clearing the conscious partner's `STATUS_STAGGERED` | +8 once per action |
| complementary setup tag followed by partner follow-through | +12 once per round |

The complementary match is exact: an earlier committed move with `RES_TAG_ALLY` must have successfully applied a stage, cleanse, or Guiding Draft to the conscious partner; that affected partner must then commit a damaging move with `RES_TAG_DAMAGE` in the same round. The actors must differ. A player-side setup writes the slot indexed by the affected partner's player lane; a later valid setup for that same partner deterministically replaces the prior unconsumed record. A matching follow-through marks it consumed before adding +12, so multi-target events cannot duplicate it. Round cleanup, partner/setup-source KO, replacement out of the active lanes, battle end, and Retry clear records; enemy and self-support actions never write them. `last_resonance_tags` is action history only and cannot substitute for this state. Goldens cover two setup records, same-partner overwrite, consumed replay, multi-target follow-through, expiry, KO, enemy attempts, and retry. Invalid targets, misses, no-ops, duplicate resolutions, self-support, and presentation replay award zero. Tutorial Gate 4 cannot calibrate early: its required demonstrated path includes partner support, damaging actions, and one partner follow-through, repeating safe legal actions until the honest meter is at least 70; only then may calibration set it to 100.

## 8. Dialogue, conditions, and story actions

```c
typedef enum OpeningDialogueIdValue {
    ANNEX_INTRO_004 = 0x5301,
    ANNEX_INTRO_005 = 0x5302,
    OREN_003 = 0x5303,
    JO_RELAY_006 = 0x5304,
    SERA_RELAY_002 = 0x5305,
    PELL_TRACE_004 = 0x5306,
    RUSK_PRE_005 = 0x5307,
    RUSK_RETRY_001 = 0x5308,
    RUSK_RETRY_IMMEDIATE_001 = 0x5309,
    SERA_RUSK_RETURN_001 = 0x530A,
    RUSK_POST_005 = 0x530B,
    REUNION_001 = 0x530C,
    REUNION_004 = 0x530D,
    REUNION_011 = 0x530E,
    RETURN_005 = 0x530F,
    RETURN_007 = 0x5310,
    HOOK_005 = 0x5311,
    HOOK_010 = 0x5312,
    HOOK_014 = 0x5313,
    POST_OREN_001 = 0x5314,
    POST_OREN_UNSAVED_001 = 0x5315,
    ANNEX_INTRO_001 = 0x5316,
    RUSK_WIN_UI_001 = 0x5317,
    RUSK_LOSE_001 = 0x5318,
    RUSK_LOSE_CHOICE = 0x5319,
    RETURN_001 = 0x531A,
    HOOK_001 = 0x531B,
    SIM_001 = 0x531C,
    RUSK_PRE_001 = 0x531D,
    OREN_001 = 0x531E,
    JO_RELAY_001 = 0x531F,
    PELL_TRACE_001 = 0x5326,
    SIM_002 = 0x5327,
    EXIT_LOCKED_NO_RELAY = 0x5328,
    EXIT_LOCKED_NO_TRACE = 0x5329,
    EXIT_READY_001 = 0x532A,
    SERA_DEPART_001 = 0x532B,
    RUSK_ENTRY_001 = 0x532C,
    RUSK_ENTRY_002 = 0x532D,
    RUSK_ENTRY_003 = 0x532E,
    RUSK_EXIT_001 = 0x532F,
    EXIT_READY_OPEN = 0x5336,
    EXIT_READY_STAY = 0x5337,
    TAVI_EXIT_001 = 0x5338,
    RETURN_SKIMMER_REPEAT_001 = 0x5339,
    EXIT_READY_REPEAT_001 = 0x533A,
    EXIT_READY_REPEAT_OPEN = 0x533B
} OpeningDialogueIdValue;

typedef enum MandatoryBridgeDialogueStringIdValue {
    STR_DIALOGUE_SIM_001 = 0x6F01,
    STR_DIALOGUE_SIM_002 = 0x6F02,
    STR_DIALOGUE_EXIT_LOCKED_NO_RELAY = 0x6F03,
    STR_DIALOGUE_EXIT_LOCKED_NO_TRACE = 0x6F04,
    STR_DIALOGUE_EXIT_READY = 0x6F05,
    STR_DIALOGUE_EXIT_READY_OPEN = 0x6F06,
    STR_DIALOGUE_EXIT_READY_STAY = 0x6F07,
    STR_DIALOGUE_SERA_DEPART = 0x6F08,
    STR_DIALOGUE_RUSK_ENTRY_001 = 0x6F09,
    STR_DIALOGUE_RUSK_ENTRY_002 = 0x6F0A,
    STR_DIALOGUE_RUSK_ENTRY_003 = 0x6F0B,
    STR_DIALOGUE_RUSK_EXIT_001 = 0x6F0C,
    STR_DIALOGUE_TAVI_EXIT_001 = 0x6F0D,
    STR_DIALOGUE_RETURN_SKIMMER_REPEAT = 0x6F0E,
    STR_DIALOGUE_EXIT_READY_REPEAT = 0x6F0F,
    STR_DIALOGUE_EXIT_READY_REPEAT_OPEN = 0x6F10
} MandatoryBridgeDialogueStringIdValue;

typedef struct DialogueNode {
    DialogueId id;                    /* 0 */
    CharacterId speaker_id;           /* 2 */
    StringId text_string_id;          /* 4 */
    DialogueId next_id;               /* 6 */
    DialogueId alternate_next_id;     /* 8 */
    ConditionId condition_id;         /* 10 */
    StoryActionListId action_list_xref; /* 12: equality-only owner mirror */
    CameraCueId camera_cue_id;        /* 14 */
    uint8_t emote_id;                 /* 16 */
    uint8_t flags;                    /* 17 */
    uint16_t auto_advance_ticks;      /* 18; 0 requires confirm */
} DialogueNode;
_Static_assert(sizeof(DialogueNode) == 20, "DialogueNode layout");

enum DialogueNodeFlags {
    DIALOGUE_SKIPPABLE_TYPING = 1u << 0,
    DIALOGUE_CHOICE = 1u << 1,
    DIALOGUE_ONE_SHOT = 1u << 2,
    DIALOGUE_CLOSE_AFTER = 1u << 3,
    DIALOGUE_KEEP_CAMERA = 1u << 4
};

enum {
    DIALOGUE_NODE_TABLE_MAX = 256,
    DIALOGUE_CHAIN_ADVANCE_MAX = 48,
    DIALOGUE_TEXT_PAGES_PER_NODE_MAX = 4,
    DIALOGUE_LINES_PER_PAGE_MAX = 3
};
```

Dialogue camera IDs and their shot assets are closed registries. A cue never means
"choose a reasonable camera" at runtime:

```c
typedef enum DialogueCameraCueIdValue {
    CAMERA_CUE_UI_NONE = 0x8600,
    CAMERA_CUE_SIM_COMMS = 0x8601,
    CAMERA_CUE_ANNEX_GROUP = 0x8602,
    CAMERA_CUE_OREN = 0x8603,
    CAMERA_CUE_JO_RELAY = 0x8604,
    CAMERA_CUE_PELL_RELAY = 0x8605,
    CAMERA_CUE_RUSK_COURTYARD = 0x8606,
    CAMERA_CUE_RUSK_FOYER = 0x8607,
    CAMERA_CUE_ESTATE_STUDY = 0x8608,
    CAMERA_CUE_ANNEX_RETURN = 0x8609,
    CAMERA_CUE_HOOK_GROUP = 0x860A,
    CAMERA_CUE_OPTIONAL_NPC = 0x860B,
    CAMERA_CUE_EXAMINE_FOCUS = 0x860C,
    CAMERA_CUE_POST_CHAPTER = 0x860D,
    CAMERA_CUE_MAP_UI = 0x860E
} DialogueCameraCueIdValue;

typedef enum DialogueCameraShotAssetIdValue {
    ASSET_CAMERA_SHOT_UI_NONE = 0x7801,
    ASSET_CAMERA_SHOT_SIM_COMMS = 0x7802,
    ASSET_CAMERA_SHOT_ANNEX_GROUP = 0x7803,
    ASSET_CAMERA_SHOT_OREN = 0x7804,
    ASSET_CAMERA_SHOT_JO_RELAY = 0x7805,
    ASSET_CAMERA_SHOT_PELL_RELAY = 0x7806,
    ASSET_CAMERA_SHOT_RUSK_COURTYARD = 0x7807,
    ASSET_CAMERA_SHOT_RUSK_FOYER = 0x7808,
    ASSET_CAMERA_SHOT_ESTATE_STUDY = 0x7809,
    ASSET_CAMERA_SHOT_ANNEX_RETURN = 0x780A,
    ASSET_CAMERA_SHOT_HOOK_GROUP = 0x780B,
    ASSET_CAMERA_SHOT_OPTIONAL_NPC = 0x780C,
    ASSET_CAMERA_SHOT_EXAMINE_FOCUS = 0x780D,
    ASSET_CAMERA_SHOT_POST_CHAPTER = 0x780E,
    ASSET_CAMERA_SHOT_MAP_UI = 0x780F
} DialogueCameraShotAssetIdValue;

typedef enum CameraShotTargetModeValue {
    CAMERA_SHOT_TARGET_NONE = 0,
    CAMERA_SHOT_TARGET_SPEAKER = 1,
    CAMERA_SHOT_TARGET_GROUP_CENTROID = 2,
    CAMERA_SHOT_TARGET_INTERACTION_MARKER = 3,
    CAMERA_SHOT_TARGET_SCENE_MARKER = 4,
    CAMERA_SHOT_TARGET_MAP_UI = 5
} CameraShotTargetModeValue;

typedef enum CameraShotFramingModeValue {
    CAMERA_SHOT_PRESERVE_ACTIVE = 0,
    CAMERA_SHOT_LOCKED = 1,
    CAMERA_SHOT_FOLLOW_TARGET = 2,
    CAMERA_SHOT_SCREEN_SPACE = 3
} CameraShotFramingModeValue;

enum DialogueCameraCueFlags {
    DIALOGUE_CAMERA_NO_WORLD_OVERRIDE = 1u << 0,
    DIALOGUE_CAMERA_REQUIRE_LIVE_TARGET = 1u << 1,
    DIALOGUE_CAMERA_KEEP_UNTIL_CHAIN_CLOSE = 1u << 2,
    DIALOGUE_CAMERA_SCREEN_SPACE = 1u << 3,
    DIALOGUE_CAMERA_ALLOW_SCENE_MARKER = 1u << 4
};

typedef struct CameraShotResourceDef {
    AssetId asset_id;          /* 0: equality mirror of owning manifest entry */
    uint8_t target_mode;       /* 2 */
    uint8_t framing_mode;      /* 3 */
    int32_t eye_x_q16;         /* 4: target-relative metres */
    int32_t eye_y_q16;         /* 8 */
    int32_t eye_z_q16;         /* 12 */
    int32_t look_x_q16;        /* 16 */
    int32_t look_y_q16;        /* 20 */
    int32_t look_z_q16;        /* 24 */
    uint16_t vertical_fov_q8;  /* 28: degrees; zero only for no-world/UI */
    uint16_t default_blend_ticks; /* 30: fixed 30 Hz */
    uint16_t flags;            /* 32: reserved for shot-resource behavior; zero */
    uint16_t reserved;         /* 34 */
} CameraShotResourceDef;
_Static_assert(sizeof(CameraShotResourceDef) == 36, "CameraShotResourceDef layout");

typedef struct DialogueCameraCueDef {
    CameraCueId camera_cue_id; /* 0 */
    AssetId shot_asset_id;     /* 2: one CameraShotResourceDef payload */
    BundleId owning_bundle_id; /* 4 */
    uint16_t flags;            /* 6 */
    uint16_t reserved;         /* 8 */
} DialogueCameraCueDef;
_Static_assert(sizeof(DialogueCameraCueDef) == 10, "DialogueCameraCueDef layout");
```

The cue table is literal; all shot assets are required `ASSET_DATA_TABLE` entries
owned once by `BUNDLE_UI_SHARED` and referenced by every scene load closure that
uses the cue:

| CameraCueId | Shot AssetId | existing inventory production source | exact cue flags |
|---|---|---|---|
| `CAMERA_CUE_UI_NONE` | `ASSET_CAMERA_SHOT_UI_NONE` | `ui.panel.dialogue` | `DIALOGUE_CAMERA_NO_WORLD_OVERRIDE` |
| `CAMERA_CUE_SIM_COMMS` | `ASSET_CAMERA_SHOT_SIM_COMMS` | `env.annex.sim_chamber` | `REQUIRE_LIVE_TARGET + KEEP_UNTIL_CHAIN_CLOSE` |
| `CAMERA_CUE_ANNEX_GROUP` | `ASSET_CAMERA_SHOT_ANNEX_GROUP` | `env.annex.atrium_lower` | `REQUIRE_LIVE_TARGET + KEEP_UNTIL_CHAIN_CLOSE` |
| `CAMERA_CUE_OREN` | `ASSET_CAMERA_SHOT_OREN` | `env.annex.director_lab` | `REQUIRE_LIVE_TARGET + KEEP_UNTIL_CHAIN_CLOSE` |
| `CAMERA_CUE_JO_RELAY` | `ASSET_CAMERA_SHOT_JO_RELAY` | `env.annex.workshop` | `REQUIRE_LIVE_TARGET + KEEP_UNTIL_CHAIN_CLOSE` |
| `CAMERA_CUE_PELL_RELAY` | `ASSET_CAMERA_SHOT_PELL_RELAY` | `env.annex.atrium_upper` | `REQUIRE_LIVE_TARGET + KEEP_UNTIL_CHAIN_CLOSE` |
| `CAMERA_CUE_RUSK_COURTYARD` | `ASSET_CAMERA_SHOT_RUSK_COURTYARD` | `env.estate.courtyard` | `REQUIRE_LIVE_TARGET + KEEP_UNTIL_CHAIN_CLOSE` |
| `CAMERA_CUE_RUSK_FOYER` | `ASSET_CAMERA_SHOT_RUSK_FOYER` | `env.estate.foyer_gallery` | `REQUIRE_LIVE_TARGET + KEEP_UNTIL_CHAIN_CLOSE` |
| `CAMERA_CUE_ESTATE_STUDY` | `ASSET_CAMERA_SHOT_ESTATE_STUDY` | `env.estate.observatory_study` | `REQUIRE_LIVE_TARGET + KEEP_UNTIL_CHAIN_CLOSE` |
| `CAMERA_CUE_ANNEX_RETURN` | `ASSET_CAMERA_SHOT_ANNEX_RETURN` | `env.annex.atrium_lower` | `REQUIRE_LIVE_TARGET + KEEP_UNTIL_CHAIN_CLOSE` |
| `CAMERA_CUE_HOOK_GROUP` | `ASSET_CAMERA_SHOT_HOOK_GROUP` | `lmk.annex.resonance_monitor` | `REQUIRE_LIVE_TARGET + KEEP_UNTIL_CHAIN_CLOSE + ALLOW_SCENE_MARKER` |
| `CAMERA_CUE_OPTIONAL_NPC` | `ASSET_CAMERA_SHOT_OPTIONAL_NPC` | `col.common.camera_volumes` | `REQUIRE_LIVE_TARGET + KEEP_UNTIL_CHAIN_CLOSE` |
| `CAMERA_CUE_EXAMINE_FOCUS` | `ASSET_CAMERA_SHOT_EXAMINE_FOCUS` | `col.common.camera_volumes` | `REQUIRE_LIVE_TARGET + KEEP_UNTIL_CHAIN_CLOSE` |
| `CAMERA_CUE_POST_CHAPTER` | `ASSET_CAMERA_SHOT_POST_CHAPTER` | `col.common.camera_volumes` | `REQUIRE_LIVE_TARGET + KEEP_UNTIL_CHAIN_CLOSE` |
| `CAMERA_CUE_MAP_UI` | `ASSET_CAMERA_SHOT_MAP_UI` | `env.world_map.desert_relief` | `NO_WORLD_OVERRIDE + SCREEN_SPACE` |

Unqualified flag names in the table expand to the exact `DIALOGUE_CAMERA_*`
constants. The 15 resource payloads, in AssetId order, are exact:

| AssetId | target / framing | eye Q16 `(x,y,z)` | look Q16 `(x,y,z)` | FOV Q8 / blend |
|---|---|---:|---:|---:|
| `ASSET_CAMERA_SHOT_UI_NONE` | `NONE / PRESERVE_ACTIVE` | `0,0,0` | `0,0,0` | `0 / 0` |
| `ASSET_CAMERA_SHOT_SIM_COMMS` | `GROUP_CENTROID / FOLLOW_TARGET` | `0,114688,-311296` | `0,78643,0` | `15360 / 12` |
| `ASSET_CAMERA_SHOT_ANNEX_GROUP` | `GROUP_CENTROID / FOLLOW_TARGET` | `-196608,131072,-327680` | `0,81920,0` | `14336 / 15` |
| `ASSET_CAMERA_SHOT_OREN` | `SPEAKER / FOLLOW_TARGET` | `-98304,114688,-196608` | `0,81920,0` | `13312 / 12` |
| `ASSET_CAMERA_SHOT_JO_RELAY` | `SPEAKER / FOLLOW_TARGET` | `98304,106496,-180224` | `0,73728,0` | `12800 / 10` |
| `ASSET_CAMERA_SHOT_PELL_RELAY` | `SPEAKER / FOLLOW_TARGET` | `-81920,114688,-212992` | `0,77824,0` | `13312 / 12` |
| `ASSET_CAMERA_SHOT_RUSK_COURTYARD` | `SPEAKER / FOLLOW_TARGET` | `-229376,147456,-393216` | `0,90112,0` | `14848 / 15` |
| `ASSET_CAMERA_SHOT_RUSK_FOYER` | `SPEAKER / FOLLOW_TARGET` | `163840,122880,-278528` | `0,81920,0` | `13824 / 12` |
| `ASSET_CAMERA_SHOT_ESTATE_STUDY` | `GROUP_CENTROID / FOLLOW_TARGET` | `-196608,139264,-327680` | `0,90112,0` | `14336 / 15` |
| `ASSET_CAMERA_SHOT_ANNEX_RETURN` | `GROUP_CENTROID / FOLLOW_TARGET` | `196608,131072,-344064` | `0,81920,0` | `14336 / 15` |
| `ASSET_CAMERA_SHOT_HOOK_GROUP` | `SCENE_MARKER / LOCKED` | `0,163840,-393216` | `0,98304,0` | `15360 / 18` |
| `ASSET_CAMERA_SHOT_OPTIONAL_NPC` | `SPEAKER / FOLLOW_TARGET` | `-81920,106496,-180224` | `0,73728,0` | `12800 / 10` |
| `ASSET_CAMERA_SHOT_EXAMINE_FOCUS` | `INTERACTION_MARKER / LOCKED` | `0,98304,-163840` | `0,65536,0` | `11520 / 8` |
| `ASSET_CAMERA_SHOT_POST_CHAPTER` | `SPEAKER / FOLLOW_TARGET` | `-114688,122880,-229376` | `0,81920,0` | `13312 / 12` |
| `ASSET_CAMERA_SHOT_MAP_UI` | `MAP_UI / SCREEN_SPACE` | `0,0,0` | `0,0,0` | `0 / 0` |

These 15 AssetIds are generated runtime children of the explicit production
packages in the table, under the approved one-package-to-many-runtime-child rule
in `ASSET_INVENTORY.md` section 8.3. They are not 15 new inventory art assets:
their editable camera marker/volume data, review ownership, and provenance remain
with the named existing package, and the generated asset BOM records that parent
ID for every child. An unresolved parent or a child counted as a new production
package fails the inventory/ledger audit. Every resource row has
`flags=reserved=0`; its manifest entry has unpacked size
exactly `36`, alignment `4`, `ASSET_REQUIRED`, and payload CRC from those bytes.
The generated cue table is sorted `0x8600..0x860E`, has unique cue/asset pairs,
and accepts only cue flag mask `0x001F`. Missing manifest entries or scene refs,
wrong target/framing domains, a world shot with zero FOV, or a UI/no-override
shot with nonzero FOV fails Gate 2. `DialogueNode.camera_cue_id` accepts exactly
`0` or one registered cue in `0x8600..0x860E`: literal `0` means no camera
request/resource at all and is distinct from `CAMERA_CUE_UI_NONE`, whose explicit
resource preserves the active camera for a UI-owned row. Any other graph value
fails Gate 2.

```c
static const DialogueNode MANDATORY_BRIDGE_DIALOGUE_NODES[16] = {
    { SIM_001, CHAR_DR_SERA_VENN, STR_DIALOGUE_SIM_001,
      SIM_002, 0, 0, 0, 0, 0, DIALOGUE_SKIPPABLE_TYPING, 0 },
    { SIM_002, CHAR_DR_SERA_VENN, STR_DIALOGUE_SIM_002,
      0, 0, 0, ACTION_SIM_TUTORIAL_START, 0, 0,
      DIALOGUE_SKIPPABLE_TYPING + DIALOGUE_CLOSE_AFTER, 0 },
    { EXIT_LOCKED_NO_RELAY, CHAR_NONE, STR_DIALOGUE_EXIT_LOCKED_NO_RELAY,
      0, 0, 0, 0, 0, 0,
      DIALOGUE_SKIPPABLE_TYPING + DIALOGUE_CLOSE_AFTER, 0 },
    { EXIT_LOCKED_NO_TRACE, CHAR_DR_SERA_VENN, STR_DIALOGUE_EXIT_LOCKED_NO_TRACE,
      0, 0, 0, 0, 0, 0,
      DIALOGUE_SKIPPABLE_TYPING + DIALOGUE_CLOSE_AFTER, 0 },
    { EXIT_READY_001, CHAR_NONE, STR_DIALOGUE_EXIT_READY,
      EXIT_READY_OPEN, EXIT_READY_STAY, 0, 0, 0, 0,
      DIALOGUE_CHOICE, 0 },
    { EXIT_READY_OPEN, CHAR_NONE, STR_DIALOGUE_EXIT_READY_OPEN,
      0, 0, 0, ACTION_EXIT_OPEN_FIRST_SERA, 0, 0,
      DIALOGUE_CLOSE_AFTER, 0 },
    { EXIT_READY_STAY, CHAR_NONE, STR_DIALOGUE_EXIT_READY_STAY,
      0, 0, 0, 0, 0, 0, DIALOGUE_CLOSE_AFTER, 0 },
    { EXIT_READY_REPEAT_001, CHAR_NONE, STR_DIALOGUE_EXIT_READY_REPEAT,
      EXIT_READY_REPEAT_OPEN, EXIT_READY_STAY, 0, 0, 0, 0,
      DIALOGUE_CHOICE, 0 },
    { EXIT_READY_REPEAT_OPEN, CHAR_NONE, STR_DIALOGUE_EXIT_READY_REPEAT_OPEN,
      0, 0, 0, ACTION_EXIT_OPEN_REPEAT_MAP, 0, 0,
      DIALOGUE_CLOSE_AFTER, 0 },
    { SERA_DEPART_001, CHAR_DR_SERA_VENN, STR_DIALOGUE_SERA_DEPART,
      0, 0, 0, ACTION_SERA_DEPART_CONTINUE_MAP, 0, 0,
      DIALOGUE_SKIPPABLE_TYPING + DIALOGUE_ONE_SHOT + DIALOGUE_CLOSE_AFTER, 0 },
    { RUSK_ENTRY_001, CHAR_RUSK, STR_DIALOGUE_RUSK_ENTRY_001,
      RUSK_ENTRY_002, 0, 0, 0, CAMERA_CUE_RUSK_FOYER, 0,
      DIALOGUE_SKIPPABLE_TYPING + DIALOGUE_KEEP_CAMERA, 0 },
    { RUSK_ENTRY_002, CHAR_RUSK, STR_DIALOGUE_RUSK_ENTRY_002,
      RUSK_ENTRY_003, 0, 0, 0, CAMERA_CUE_RUSK_FOYER, 0,
      DIALOGUE_SKIPPABLE_TYPING + DIALOGUE_KEEP_CAMERA, 0 },
    { RUSK_ENTRY_003, CHAR_RUSK, STR_DIALOGUE_RUSK_ENTRY_003,
      0, 0, 0, 0, CAMERA_CUE_RUSK_FOYER, 0,
      DIALOGUE_SKIPPABLE_TYPING + DIALOGUE_ONE_SHOT + DIALOGUE_CLOSE_AFTER, 0 },
    { RUSK_EXIT_001, CHAR_RUSK, STR_DIALOGUE_RUSK_EXIT_001,
      TAVI_EXIT_001, 0, 0, 0, 0, 0,
      DIALOGUE_SKIPPABLE_TYPING + DIALOGUE_KEEP_CAMERA, 0 },
    { TAVI_EXIT_001, CHAR_TAVI, STR_DIALOGUE_TAVI_EXIT_001,
      0, 0, 0, ACTION_TAVI_EXIT_CONTINUE_RETURN, 0, 0,
      DIALOGUE_SKIPPABLE_TYPING + DIALOGUE_ONE_SHOT + DIALOGUE_CLOSE_AFTER, 0 },
    { RETURN_SKIMMER_REPEAT_001, CHAR_NONE, STR_DIALOGUE_RETURN_SKIMMER_REPEAT,
      0, 0, 0, ACTION_TAVI_EXIT_REPEAT_CONTINUE_RETURN, 0, 0,
      DIALOGUE_SKIPPABLE_TYPING + DIALOGUE_CLOSE_AFTER, 0 }
};
```

The corresponding string rows are literal UTF-8 source strings converted by the text packer: `STR_DIALOGUE_SIM_001="Signal is clean. {PLAYER}, take the near pair."`, `STR_DIALOGUE_SIM_002="Two partners. Two commands. Read the field before you move."`, `STR_DIALOGUE_EXIT_LOCKED_NO_RELAY="A Field Relay is required for desert travel."`, `STR_DIALOGUE_EXIT_LOCKED_NO_TRACE="Trace Tavi's packet with Pell before you leave."`, `STR_DIALOGUE_EXIT_READY="OPEN DESERT MAP?"`, `STR_DIALOGUE_EXIT_READY_OPEN="OPEN MAP"`, `STR_DIALOGUE_EXIT_READY_STAY="STAY"`, `STR_DIALOGUE_EXIT_READY_REPEAT="OPEN DESERT MAP?"`, `STR_DIALOGUE_EXIT_READY_REPEAT_OPEN="OPEN MAP"`, `STR_DIALOGUE_SERA_DEPART="Bring Tavi home. Keep the pair close."`, `STR_DIALOGUE_RUSK_ENTRY_001="Tavi is with Ivo in the upper study."`, `STR_DIALOGUE_RUSK_ENTRY_002="The direct stair is jammed by an orrery arm. The hall route is clear."`, `STR_DIALOGUE_RUSK_ENTRY_003="Touch nothing that hums in three directions."`, `STR_DIALOGUE_RUSK_EXIT_001="I will send Ivo's full chart when the bands clear."`, `STR_DIALOGUE_TAVI_EXIT_001="And I will send Sera a message before I leave anywhere."`, and `STR_DIALOGUE_RETURN_SKIMMER_REPEAT="RETURN TO ANNEX WITH TAVI?"`. The text compiler treats punctuation and `{PLAYER}` exactly as shown; no controller invents substitute copy.

These rows are a required literal subset of the complete dialogue graph. A graph import may supply the surrounding nodes, but a duplicate mandatory ID must be byte-identical to this initializer and string row or generation fails. `SIM_001.next_id` is therefore mechanically proven to resolve to numeric `SIM_002=0x5327`. The first and repeat exit choices use distinct roots and distinct OPEN targets, so every node has at most one action mirror and every StoryTrigger key remains unique. An OPEN target is a semantic choice target: selection emits its ENTER trigger before any second-page presentation, reserves/closes the choice owner, and dispatches its one literal list. `EXIT_READY_STAY` performs the reserved close and returns control with no trigger. `RETURN_SKIMMER_REPEAT_001` is shown only after a typed interaction confirmation accepted A; its dismissal continues travel, while Back at the interaction confirmation closes before this node is acquired. No auto-advance, camera cue, emote, alternate, or hidden action is inferred from prose.

### 8.0.1 Singular complete dialogue projection

[`DIALOGUE_GRAPH.md`](DIALOGUE_GRAPH.md) is the sole editable source for the complete `DialogueNode` and dialogue StringId tables. The frozen Gate 2 input SHA-256 is `5151387d32be8929f9a992f598393a152df3d6983aebc6a8b3cf2c2a35fbe5f6`. Its `DROW` signature is normative and supplies, for every row, literal symbol, DialogueId hex+decimal mirrors, StringId hex+decimal mirrors, speaker, next, alternate, ConditionId, action-list xref, camera, emote, flags, auto ticks, owner class, and exact UTF-8 copy. The data generator parses exactly `223` authored records: `16` byte-locked bridge rows plus `207` nonbridge rows, of which exactly `160` are the first-column Story copy rows. It does not read Markdown row order as a default and may not fill an omitted field. Hex/decimal disagreement, an unparsed DROW-like line, a field outside the fixed arity, or a source hash/count mismatch is fatal.

Projection is deterministic: bridge rows use the explicitly locked `0x6F01..0x6F10` StringIds; every graph-declared nonbridge row uses its literal listed StringId, which the graph also verifies against `StringId = DialogueId + 0x4000`. The generator emits rows sorted by numeric DialogueId and a separate text pack sorted by StringId. It then byte-compares all 16 bridge rows against `MANDATORY_BRIDGE_DIALOGUE_NODES`, every nonzero action xref against exactly one StoryTrigger owner/phase, every camera/emote/flag against the graph's closed numeric domains, and every string against the exact UTF-8 bytes before token substitution. Graph owner classes are build annotations only and emit no hidden runtime field.

The graph is complete, not a patch: every nonzero `next_id`/`alternate_next_id` resolves; every choice has two nonzero targets; every selected zero target has CLOSE_AFTER; all roots are reached by a typed StoryStart, interaction/portal, battle/tutorial/result, help, examine/NPC, map, or process owner; and no chain cycles or exceeds the declared advance/page bounds. Fields listed as zero remain zero—there is no default camera, emote, condition, action, auto-advance, or inferred sequential next. Exactly `26` rows have a nonzero action xref and must byte-compare in both directions with the graph's closed node/action mirror list; the other `197` are literal zero. Generation emits a coverage manifest containing row count, sorted `(DialogueId,StringId)` pairs, root-owner relation, edge list, action-xref relation, and source SHA-256. The emitted sorted array is exactly `223 * sizeof(DialogueNode) = 4,460` bytes before enclosing-asset alignment. Missing/extra/duplicate IDs or StringIds, a size other than `4,460`, orphan roots/nodes/actions, graph/Data bridge drift, and unreachable mandatory story copy fail Gate 2.

`DialogueNode.flags` accepts only mask `0x1F`; unknown bits fail. For an ordinary node, `condition_id=0` selects `next_id`; otherwise true selects `next_id` and false selects `alternate_next_id`. A selected zero target is legal only with `DIALOGUE_CLOSE_AFTER` and closes after any node action succeeds. A nonzero selected target must resolve. For a `DIALOGUE_CHOICE` node, `next_id` is option A and `alternate_next_id` is option B, both nonzero; `condition_id=0` enables both, while a nonzero condition gates only option B (false hides/disables B) and never auto-selects a branch. Choice labels are the target nodes' validated text labels.

Branch selection reads the immutable pre-action condition view. Once the player/auto edge chooses a legal target, DialogueController emits exactly one typed ENTER/DISMISS StoryTrigger event carrying the node's equality-checked `action_list_xref`; StoryTrigger alone validates/commits the list. Only its success consumes the edge and closes/enters the already selected target. The action cannot alter which branch that same advance takes. After its progress transaction, DialogueController performs its reserved no-fail close, then StoryTrigger emits any suffix external request. A failed trigger leaves the current fully revealed node active and emits nothing. `DIALOGUE_ONE_SHOT` requires one explicit `DialogueOnceRegistryDef` row below and normally stages that bit in the same successful trigger transaction. The sole `ONCE_DEFER_TO_EXTERNAL_COMMIT` row instead carries the staged bit in its pre-reserved TransitionRequest and publishes it only inside the exact transition recipe named by `DeferredDialogueOnceCommitDef`; cancellation publishes neither bit nor transition recipe.

The generated graph has at most 256 nodes, no intra-conversation cycle, at most 48 node advances from any root, and no sub-dialogue call stack. Each node wraps to at most four pages of three lines inside the 320x240 safe rectangle after an eight-character player-name substitution. During typewriter reveal, the first A edge on a `DIALOGUE_SKIPPABLE_TYPING` node reveals the remaining glyphs only; it cannot also advance. A later poll-frame A edge advances. Start is not a Dialogue action: it neither reveals, advances, nor skips a story line, and Pause is unavailable while Dialogue owns the input context. Only one edge is accepted per complete poll/render frame; entry, choice opening/closing, controller recovery, and node change clear latches and discard one poll frame. Auto-advance timing starts only after the final page is fully visible and pauses on disconnect. Thus rapid input cannot double-commit, skip a choice, or leak into the destination state.

The three saved 64-bit one-shot sets use explicit tombstoned registries; no DialogueId, InteractionId, CharacterId, or occurrence ID is truncated or used as a bit index.

```c
enum OnceRegistryFlags {
    ONCE_REGISTRY_TOMBSTONE = 1u << 0,
    ONCE_HIDE_WHEN_SET = 1u << 1,
    ONCE_ROUTE_TO_REPEAT = 1u << 2,
    ONCE_REPLAY_WITHOUT_ACTION = 1u << 3,
    ONCE_DEFER_TO_EXTERNAL_COMMIT = 1u << 4
};

typedef struct DialogueOnceRegistryDef {
    DialogueId dialogue_id; /* 0; zero only for tombstone */
    uint8_t bit_index;      /* 2: 0..63 */
    uint8_t flags;          /* 3 */
    DialogueId repeat_dialogue_id; /* 4; required only for ROUTE */
} DialogueOnceRegistryDef;
_Static_assert(sizeof(DialogueOnceRegistryDef) == 6, "DialogueOnceRegistryDef layout");

typedef struct ExamineOnceRegistryDef {
    InteractionId interaction_id; /* 0; zero only for tombstone */
    uint8_t bit_index;            /* 2: 0..63 */
    uint8_t flags;                /* 3 */
    DialogueId repeat_dialogue_id; /* 4 */
} ExamineOnceRegistryDef;
_Static_assert(sizeof(ExamineOnceRegistryDef) == 6, "ExamineOnceRegistryDef layout");

typedef struct NpcOnceRegistryDef {
    NpcOccurrenceId occurrence_id; /* 0; zero only for tombstone */
    CharacterId character_id;      /* 2; zero only for tombstone */
    uint8_t bit_index;             /* 4: 0..63 */
    uint8_t flags;                 /* 5 */
} NpcOnceRegistryDef;
_Static_assert(sizeof(NpcOnceRegistryDef) == 6, "NpcOnceRegistryDef layout");

typedef struct DialogueConversationOnceDef {
    DialogueId root_dialogue_id;     /* 0: start-router lookup */
    DialogueId terminal_dialogue_id; /* 2: owns DIALOGUE_ONE_SHOT */
    uint8_t bit_index;               /* 4: exact DialogueOnceRegistryDef bit */
    uint8_t flags;                   /* 5: reserved, currently zero */
} DialogueConversationOnceDef;
_Static_assert(sizeof(DialogueConversationOnceDef) == 6, "DialogueConversationOnceDef layout");

enum DeferredDialogueOnceCommitFlags {
    DEFERRED_ONCE_RESERVE_TRANSITION_BEFORE_CLOSE = 1u << 0,
    DEFERRED_ONCE_PUBLISH_IN_RECIPE_TRANSACTION = 1u << 1,
    DEFERRED_ONCE_CLEAR_ON_PREPARE_CANCEL = 1u << 2,
    DEFERRED_ONCE_REQUIRE_FIRST_USE_CONDITION = 1u << 3
};

typedef struct DeferredDialogueOnceCommitDef {
    DialogueId terminal_dialogue_id; /* 0 */
    StoryActionListId action_list_id; /* 2 */
    TransitionId transition_id;       /* 4 */
    uint16_t transition_recipe_id;    /* 6 */
    uint8_t bit_index;                /* 8 */
    uint8_t flags;                    /* 9 */
    uint16_t reserved;                /* 10 */
} DeferredDialogueOnceCommitDef;
_Static_assert(sizeof(DeferredDialogueOnceCommitDef) == 12, "DeferredDialogueOnceCommitDef layout");

typedef struct NpcOccurrenceDef {
    NpcOccurrenceId occurrence_id; /* 0 */
    CharacterId character_id;      /* 2 */
    ZoneId zone_id;                /* 4 */
    DialogueId pre_dialogue_xref;  /* 6: variant equality mirror */
    DialogueId post_dialogue_xref; /* 8 */
    uint16_t flags;                /* 10 */
} NpcOccurrenceDef;
_Static_assert(sizeof(NpcOccurrenceDef) == 12, "NpcOccurrenceDef layout");

enum NpcOccurrenceVariantFlags {
    NPC_VARIANT_STORY_STATE = 1u << 0,
    NPC_VARIANT_REPEAT_WITHOUT_ACTION = 1u << 1
};

typedef struct NpcOccurrenceVariantDef {
    NpcOccurrenceId occurrence_id; /* 0 */
    ConditionId condition_id;      /* 2 */
    DialogueId dialogue_id;        /* 4 */
    uint8_t priority;              /* 6 */
    uint8_t flags;                 /* 7 */
} NpcOccurrenceVariantDef;
_Static_assert(sizeof(NpcOccurrenceVariantDef) == 8, "NpcOccurrenceVariantDef layout");

enum NpcOccurrenceFlags {
    NPC_OCCURRENCE_OPTIONAL = 1u << 0,
    NPC_OCCURRENCE_SAVED_ONCE = 1u << 1
};

typedef enum OpeningHelpDialogueIdValue {
    HELP_MOVE = 0x5320,
    HELP_CAMERA = 0x5321,
    HELP_PAUSE = 0x5322,
    HELP_PARTY = 0x5323,
    HELP_SAVE = 0x5324,
    HELP_MAP = 0x5325,
    MARA_PRE_001 = 0x5330,
    MARA_POST_001 = 0x5331,
    JO_PRE_001 = 0x5332,
    JO_POST_001 = 0x5333,
    PELL_PRE_001 = 0x5334,
    PELL_POST_001 = 0x5335
} OpeningHelpDialogueIdValue;

typedef enum OpeningHelpStringIdValue {
    STR_HELP_MOVE = 0x9320,
    STR_HELP_CAMERA = 0x9321,
    STR_HELP_PAUSE = 0x9322,
    STR_HELP_PARTY = 0x9323,
    STR_HELP_SAVE = 0x9324,
    STR_HELP_MAP = 0x9325
} OpeningHelpStringIdValue;

typedef enum HelpPromptTriggerValue {
    HELP_TRIGGER_FIRST_STABLE_ATRIUM_CONTROL = 1,
    HELP_TRIGGER_FIELD_RELAY_UNLOCKED_STABLE = 2,
    HELP_TRIGGER_FIRST_WORLD_MAP_CONTROL = 3
} HelpPromptTriggerValue;

enum HelpPromptCompletionEventBits {
    HELP_COMPLETE_TIMER_90_TICKS = 1u << 0,
    HELP_COMPLETE_MOVE_DEMONSTRATED = 1u << 1,
    HELP_COMPLETE_RUN_DEMONSTRATED = 1u << 2,
    HELP_COMPLETE_INTERACT_DEMONSTRATED = 1u << 3,
    HELP_COMPLETE_CAMERA_ADJUSTED = 1u << 4,
    HELP_COMPLETE_EXPLICIT_DISMISS = 1u << 5,
    HELP_COMPLETE_PAUSE_OPENED = 1u << 6,
    HELP_COMPLETE_PARTY_SCREEN_OPENED = 1u << 7,
    HELP_COMPLETE_MANUAL_SAVE_COMMITTED = 1u << 8,
    HELP_COMPLETE_EXTERIOR_EXIT_PROMPT_OPENED = 1u << 9,
    HELP_COMPLETE_WORLD_MAP_CONTROL_ACQUIRED = 1u << 10
};

enum HelpPromptFlags {
    HELP_PROMPT_NON_STACKING = 1u << 0,
    HELP_PROMPT_REQUIRE_STABLE_CONTROL = 1u << 1,
    HELP_PROMPT_DEFER_DURING_DIALOGUE = 1u << 2,
    HELP_PROMPT_DEFER_DURING_TRANSITION = 1u << 3,
    HELP_PROMPT_PAUSE_ON_CONTROLLER_LOSS = 1u << 4,
    HELP_PROMPT_PERSIST_ON_NEXT_LEGAL_SAVE = 1u << 5,
    HELP_PROMPT_DO_NOT_SEIZE_MOVEMENT = 1u << 6
};

typedef struct HelpPromptDef {
    DialogueId dialogue_id;           /* 0: stable content/once owner */
    StringId string_id;               /* 2: exact rendered copy */
    SceneId scene_id;                  /* 4: zero means any scene */
    ZoneId zone_id;                    /* 6: zero means any zone */
    uint32_t completion_event_mask;    /* 8: OR semantics */
    uint16_t minimum_visible_ticks;    /* 12: fixed 30 Hz; 0 allowed */
    uint8_t trigger;                   /* 14: HelpPromptTriggerValue */
    uint8_t once_bit_index;            /* 15: DialogueOnceRegistryDef */
    uint8_t predecessor_once_bit;      /* 16: 0xFF means none */
    uint8_t priority;                  /* 17: higher first */
    uint8_t flags;                     /* 18 */
    uint8_t reserved;                  /* 19 */
} HelpPromptDef;
_Static_assert(sizeof(HelpPromptDef) == 20, "HelpPromptDef layout");
```

The six HelpPromptDef rows are literal:

| Dialogue / String | exact trigger location | completion event OR-mask / minimum ticks | once / predecessor / priority | flags |
|---|---|---|---|---|
| `HELP_MOVE / STR_HELP_MOVE` | `FIRST_STABLE_ATRIUM_CONTROL / SCENE_ANNEX_INTERIOR / ZONE_ANNEX_ATRIUM` | `TIMER_90_TICKS + MOVE_DEMONSTRATED + RUN_DEMONSTRATED + INTERACT_DEMONSTRATED / 90` | `1 / 0xFF / 60` | all seven `HELP_PROMPT_*` flags |
| `HELP_CAMERA / STR_HELP_CAMERA` | `FIRST_STABLE_ATRIUM_CONTROL / SCENE_ANNEX_INTERIOR / ZONE_ANNEX_ATRIUM` | `CAMERA_ADJUSTED + EXPLICIT_DISMISS / 0` | `2 / 1 / 59` | all seven flags |
| `HELP_PAUSE / STR_HELP_PAUSE` | `FIRST_STABLE_ATRIUM_CONTROL / SCENE_ANNEX_INTERIOR / ZONE_ANNEX_ATRIUM` | `PAUSE_OPENED / 0` | `3 / 2 / 58` | all seven flags |
| `HELP_PARTY / STR_HELP_PARTY` | `FIELD_RELAY_UNLOCKED_STABLE / SCENE_ANNEX_INTERIOR / 0` | `PARTY_SCREEN_OPENED + EXTERIOR_EXIT_PROMPT_OPENED / 0` | `4 / 0xFF / 50` | all seven flags |
| `HELP_SAVE / STR_HELP_SAVE` | `FIELD_RELAY_UNLOCKED_STABLE / SCENE_ANNEX_INTERIOR / 0` | `MANUAL_SAVE_COMMITTED + EXTERIOR_EXIT_PROMPT_OPENED / 0` | `5 / 4 / 49` | all seven flags |
| `HELP_MAP / STR_HELP_MAP` | `FIRST_WORLD_MAP_CONTROL / SCENE_WORLD_MAP / ZONE_WORLD_MAP_DESERT` | `WORLD_MAP_CONTROL_ACQUIRED / 1` | `6 / 0xFF / 70` | all seven flags |

Table aliases expand one-for-one to the `HELP_TRIGGER_*` and `HELP_COMPLETE_*` constants above; "all seven" is exact mask `0x7F`. The string rows are exactly `"{STICK} MOVE   Hold {B} RUN   {A} INTERACT"`, `"{C-LEFT}/{C-RIGHT} TURN   HOLD {L}+{C-UP}/{C-DOWN} TILT"`, `"{START} PAUSE"`, `"View Quarrune and Ayselor under PARTY."`, `"Record progress from the Field Relay when the area is stable."`, and `"Choose a lit destination. Dark horizon marks are not routes."` in row order.

One `HelpPromptOwner` holds a nonzero runtime generation and at most one active prompt; queued eligible rows are ordered by priority then DialogueId. A row cannot acquire while dialogue, cutscene, transition, battle, menu, or another help prompt owns presentation. Stable-control triggers debounce for one complete poll/render frame. Prompts overlay exploration and, because `DO_NOT_SEIZE_MOVEMENT` is set, MOVE/CAMERA demonstrations remain possible. Completion uses OR semantics over exactly the row mask; an event carries runtime generation plus its producing subsystem generation and is accepted once. `HELP_MOVE`'s 90-tick event becomes eligible only after 90 actually visible gameplay ticks, while any demonstrated action may complete it sooner. The one-tick MAP row guarantees at least one rendered prompt frame before its acquisition event completes it.

Controller loss freezes the visible-tick counter, clears input/event latches, retains the active row, and cannot set a bit; reconnect discards one full poll frame before events resume. Deferred prompts retain no input edge and reacquire only at stable control. Completion starts a scratch one-shot transaction, verifies the row's exact live DialogueOnceRegistryDef bit and predecessor, sets only that bit, and publishes once; presentation closes after the no-fail publish. The bit is encoded by the next otherwise-legal checkpoint/manual/transition save—help never forces or coalesces an EEPROM write—and reboot reoffers only unpersisted prompts. `EXTERIOR_EXIT_PROMPT_OPENED` may complete PARTY/SAVE immediately before the first/repeat exit choice, but it cannot satisfy MOVE/CAMERA/PAUSE. Unknown flags/events, a mask mismatch, a non-help registry owner, duplicate bit, unmet predecessor, equal priority, nonzero reserved, or a trigger/location disagreement fails generation.

```c

typedef enum OpeningExamineInteractionIdValue {
    INT_EX_ANNEX_SIM = 0x2101,
    INT_EX_ANNEX_MONITOR = 0x2102,
    INT_EX_ANNEX_SOLACE = 0x2103,
    INT_EX_ANNEX_CLINIC = 0x2104,
    INT_EX_ANNEX_TOOLWALL = 0x2105,
    INT_EX_ANNEX_PLAYER_ROOM = 0x2106,
    INT_EX_ANNEX_WINDOW = 0x2107,
    INT_EX_ANNEX_LIFT = 0x2108,
    INT_EX_ESTATE_FOUNTAIN = 0x2109,
    INT_EX_ESTATE_WEATHERVANE = 0x210A,
    INT_EX_ESTATE_TRACKS = 0x210B,
    INT_EX_ESTATE_GARDEN = 0x210C,
    INT_EX_ESTATE_DOME = 0x210D,
    INT_EX_ESTATE_PORTRAIT = 0x210E,
    INT_EX_ESTATE_COMPASS = 0x210F,
    INT_EX_ESTATE_WALKDESK = 0x2110,
    INT_EX_ESTATE_BOTTLESTAR = 0x2111,
    INT_EX_ESTATE_RAINCLOCK = 0x2112,
    INT_EX_ESTATE_LOGBOOK = 0x2113,
    INT_EX_ESTATE_TELESCOPE = 0x2114
} OpeningExamineInteractionIdValue;

typedef enum OpeningExamineDialogueIdValue {
    ANNEX_EX_SIM = 0x5401,
    ANNEX_EX_MONITOR = 0x5402,
    ANNEX_EX_SOLACE = 0x5403,
    ANNEX_EX_CLINIC = 0x5404,
    ANNEX_EX_TOOLWALL = 0x5405,
    ANNEX_EX_PLAYER_ROOM = 0x5406,
    ANNEX_EX_WINDOW = 0x5407,
    ANNEX_EX_LIFT = 0x5408,
    ESTATE_EX_FOUNTAIN = 0x5409,
    ESTATE_EX_WEATHERVANE = 0x540A,
    ESTATE_EX_TRACKS = 0x540B,
    ESTATE_EX_GARDEN = 0x540C,
    ESTATE_EX_DOME = 0x540D,
    ESTATE_EX_PORTRAIT = 0x540E,
    ESTATE_EX_COMPASS = 0x540F,
    ESTATE_EX_WALKDESK = 0x5410,
    ESTATE_EX_BOTTLESTAR = 0x5411,
    ESTATE_EX_RAINCLOCK = 0x5412,
    ESTATE_EX_LOGBOOK = 0x5413,
    ESTATE_EX_TELESCOPE = 0x5414
} OpeningExamineDialogueIdValue;

typedef enum OpeningNpcOccurrenceIdValue {
    NPC_OCCURRENCE_ANNEX_MARA = 0x5601,
    NPC_OCCURRENCE_ANNEX_JO = 0x5602,
    NPC_OCCURRENCE_ANNEX_PELL = 0x5603
} OpeningNpcOccurrenceIdValue;

typedef enum OpeningNpcVariantConditionIdValue {
    COND_NPC_MARA_POST = 0x6530,
    COND_NPC_MARA_PRE = 0x6531,
    COND_NPC_JO_POST = 0x6532,
    COND_NPC_JO_PRE = 0x6533,
    COND_NPC_PELL_POST = 0x6534,
    COND_NPC_PELL_PRE = 0x6535
} OpeningNpcVariantConditionIdValue;
```

Registry lookup by exact owner ID is the sole bit-index authority; source records do not duplicate or infer the index. A `DialogueNode` with `DIALOGUE_ONE_SHOT` has exactly one live Dialogue row; DialogueController tests it before entry and sets it only in the same successful node-advance transaction. An InteractionDef with `INTERACTION_SAVED_ONCE_EXAMINE` has exactly one Examine row; InteractionController tests before offering it and sets it only after its action/dialogue completes successfully. Each saved-once `NpcOccurrenceDef` has a stable NpcOccurrenceId independent of CharacterId and exactly one NPC row; its typed story-state variant is selected first, then the once bit controls first-presentation behavior and sets only after successful completion. These sets never substitute for mandatory story flags or objective state.

The live dialogue-once lock assignments are exact:

| bit | DialogueId | already-set behavior / repeat |
|---:|---|---|
| 0 | `SERA_RUSK_RETURN_001` | `ONCE_HIDE_WHEN_SET / 0` |
| 1 | `HELP_MOVE` | `ONCE_HIDE_WHEN_SET / 0` |
| 2 | `HELP_CAMERA` | `ONCE_HIDE_WHEN_SET / 0` |
| 3 | `HELP_PAUSE` | `ONCE_HIDE_WHEN_SET / 0` |
| 4 | `HELP_PARTY` | `ONCE_HIDE_WHEN_SET / 0` |
| 5 | `HELP_SAVE` | `ONCE_HIDE_WHEN_SET / 0` |
| 6 | `HELP_MAP` | `ONCE_HIDE_WHEN_SET / 0` |
| 7 | `SERA_DEPART_001` | `ONCE_HIDE_WHEN_SET + ONCE_DEFER_TO_EXTERNAL_COMMIT / 0` |
| 8 | `RUSK_ENTRY_003` | `ONCE_HIDE_WHEN_SET / 0` |
| 9 | `TAVI_EXIT_001` | `ONCE_ROUTE_TO_REPEAT / RETURN_SKIMMER_REPEAT_001` |

The live examine-once assignments are the exact pairs `(bit,interaction,repeat dialogue)`: `(0,INT_EX_ANNEX_SIM,ANNEX_EX_SIM)`, `(1,INT_EX_ANNEX_MONITOR,ANNEX_EX_MONITOR)`, `(2,INT_EX_ANNEX_SOLACE,ANNEX_EX_SOLACE)`, `(3,INT_EX_ANNEX_CLINIC,ANNEX_EX_CLINIC)`, `(4,INT_EX_ANNEX_TOOLWALL,ANNEX_EX_TOOLWALL)`, `(5,INT_EX_ANNEX_PLAYER_ROOM,ANNEX_EX_PLAYER_ROOM)`, `(6,INT_EX_ANNEX_WINDOW,ANNEX_EX_WINDOW)`, `(7,INT_EX_ANNEX_LIFT,ANNEX_EX_LIFT)`, `(8,INT_EX_ESTATE_FOUNTAIN,ESTATE_EX_FOUNTAIN)`, `(9,INT_EX_ESTATE_WEATHERVANE,ESTATE_EX_WEATHERVANE)`, `(10,INT_EX_ESTATE_TRACKS,ESTATE_EX_TRACKS)`, `(11,INT_EX_ESTATE_GARDEN,ESTATE_EX_GARDEN)`, `(12,INT_EX_ESTATE_DOME,ESTATE_EX_DOME)`, `(13,INT_EX_ESTATE_PORTRAIT,ESTATE_EX_PORTRAIT)`, `(14,INT_EX_ESTATE_COMPASS,ESTATE_EX_COMPASS)`, `(15,INT_EX_ESTATE_WALKDESK,ESTATE_EX_WALKDESK)`, `(16,INT_EX_ESTATE_BOTTLESTAR,ESTATE_EX_BOTTLESTAR)`, `(17,INT_EX_ESTATE_RAINCLOCK,ESTATE_EX_RAINCLOCK)`, `(18,INT_EX_ESTATE_LOGBOOK,ESTATE_EX_LOGBOOK)`, and `(19,INT_EX_ESTATE_TELESCOPE,ESTATE_EX_TELESCOPE)`. Every row uses `ONCE_REPLAY_WITHOUT_ACTION`: first completion sets the bit; later interaction shows the named one-page copy without replaying animation/action. Orrery-arm/switch variants remain repeatable state-driven interactions and are intentionally not in this saved-once set.

The NPC occurrence and lock tables are literal:

| occurrence / character / zone | first / repeat | occurrence flags | once bit / behavior |
|---|---|---|---|
| `NPC_OCCURRENCE_ANNEX_MARA / CHAR_MARA_OVELLE / ZONE_ANNEX_CLINIC` | `MARA_PRE_001 / MARA_POST_001` | `NPC_OCCURRENCE_OPTIONAL + NPC_OCCURRENCE_SAVED_ONCE` | `0 / ONCE_REPLAY_WITHOUT_ACTION` |
| `NPC_OCCURRENCE_ANNEX_JO / CHAR_JO_RENN / ZONE_ANNEX_WORKSHOP` | `JO_PRE_001 / JO_POST_001` | `NPC_OCCURRENCE_OPTIONAL + NPC_OCCURRENCE_SAVED_ONCE` | `1 / ONCE_REPLAY_WITHOUT_ACTION` |
| `NPC_OCCURRENCE_ANNEX_PELL / CHAR_PELL_ANWAR / ZONE_ANNEX_ATRIUM` | `PELL_PRE_001 / PELL_POST_001` | `NPC_OCCURRENCE_OPTIONAL + NPC_OCCURRENCE_SAVED_ONCE` | `2 / ONCE_REPLAY_WITHOUT_ACTION` |

The six variant rows are `(MARA,COND_NPC_MARA_POST,MARA_POST_001,2)`, `(MARA,COND_NPC_MARA_PRE,MARA_PRE_001,1)`, `(JO,COND_NPC_JO_POST,JO_POST_001,2)`, `(JO,COND_NPC_JO_PRE,JO_PRE_001,1)`, `(PELL,COND_NPC_PELL_POST,PELL_POST_001,2)`, and `(PELL,COND_NPC_PELL_PRE,PELL_PRE_001,1)`; every row has `NPC_VARIANT_STORY_STATE + NPC_VARIANT_REPEAT_WITHOUT_ACTION`. POST conditions are respectively Tavi objective active-or-later, Relay unlocked, and Estate destination unlocked; each PRE is the exact boolean complement within its occurrence's legal chapter range. Variant selection occurs before testing the once bit, chooses the unique true highest-priority story-era row, and only then uses the once bit to suppress first-talk animation/action. Therefore a first-ever late conversation correctly uses POST copy, while an early repeated conversation remains PRE until the story state changes.

These are the complete live prefixes of `data/ids/dialogue_once_bits.lock`, `examine_once_bits.lock`, and `npc_once_bits.lock`; later lock rows are tombstones or zero capacity, never inferred IDs. The Sera Return start edge consults dialogue bit 0 after stable threshold reveal; on completion the same dialogue advance transaction sets it, so reboot/revisit cannot replay it. First-departure Sera, first foyer-entry Rusk, and the Rusk/Tavi skimmer exchange use bits `7..9` respectively. Sera's row is the sole legal deferred row: dismissal reserves its first-departure transition and carries bit 7 in that request, while `TRANS_RECIPE_ANNEX_DEPARTURE` atomically publishes the bit with `FLAG_ANNEX_EXIT_CLEARED` and the save snapshot. Failure/cancel before recipe publish leaves both clear, so retry replays the still-uncompleted departure line; success persists both, so it can never replay after actual departure. Rusk-entry's bit is committed only by terminal `RUSK_ENTRY_003` close and is captured by the next stable destination/manual save. Tavi's bit is staged in the same node transaction whose suffix requests the stable-source Return save, so successful departure persists it. If that suffix is cancelled after in-memory publish, bit 9 routes the next same-session skimmer acceptance directly to `RETURN_SKIMMER_REPEAT_001`, never replays either required line, and remains eligible to retry the exact travel request.

The complete conversation-level once table is `{ RUSK_ENTRY_001, RUSK_ENTRY_003, 8, 0 }`. Start routing consults this row by root; the registry owner remains the terminal node. Interruption before terminal close leaves bit 8 clear and reacquires the first incomplete node under the same dialogue generation; reboot resumes normal foyer control and can start the full three-line chain again. Only terminal close sets the bit, so page 1 can never hide pages 2–3. One-node Sera and Tavi conversations do not need a conversation row because their root is their terminal.

The sole deferred-once row is `{ SERA_DEPART_001, ACTION_SERA_DEPART_CONTINUE_MAP, TRANS_DEF_THRESHOLD_TO_MAP, TRANS_RECIPE_ANNEX_DEPARTURE, 7, DEFERRED_ONCE_RESERVE_TRANSITION_BEFORE_CLOSE + DEFERRED_ONCE_PUBLISH_IN_RECIPE_TRANSACTION + DEFERRED_ONCE_CLEAR_ON_PREPARE_CANCEL + DEFERRED_ONCE_REQUIRE_FIRST_USE_CONDITION, 0 }`. The generator byte-compares every xref to the one Sera StoryTrigger, first-departure TransitionDef, and its pre recipe. No other dialogue, transition, or bit may use this mechanism.

Each registry has at most 64 rows and unique bit indices. Live owner IDs are unique; zero-owner tombstones are excluded from owner-uniqueness checks. Values come from `data/ids/dialogue_once_bits.lock`, `examine_once_bits.lock`, and `npc_once_bits.lock`; deletion replaces the live owner with a same-index tombstone forever. Registry flags accept only `0x1F`. Exactly one already-set behavior—HIDE, ROUTE_TO_REPEAT, or REPLAY_WITHOUT_ACTION—is set on every live row; ROUTE requires a nonzero registered repeat DialogueId and the other behaviors require repeat zero unless the Examine row names its typed replay text. DEFER is optional only on the literal Sera-depart row and requires the exact transition-recipe commit mapping above; every other use fails generation. Tombstones require zero owner/repeat fields and only TOMBSTONE. NpcOccurrence flags accept only `0x0003`, and every saved-once occurrence requires OPTIONAL as well. On encode, every bit with neither a live row nor tombstone is zero. Decode rejects an unregistered set bit; tombstone bits are preserved but never tested/set. Missing/extra rows, reused indices, inferred modulo mappings, incompatible behaviors, and unknown flags fail generation.

Threshold and courtyard skimmers use one typed route selector rather than controller ID switches:

```c
typedef enum OpeningPortalConditionIdValue {
    COND_PORTAL_EXIT_LOCKED_NO_RELAY = 0x6536,
    COND_PORTAL_EXIT_LOCKED_NO_TRACE = 0x6537
} OpeningPortalConditionIdValue;

typedef enum PortalRouteTargetKindValue {
    PORTAL_ROUTE_DIALOGUE = 1,
    PORTAL_ROUTE_TRANSITION = 2
} PortalRouteTargetKindValue;

typedef enum PortalOnceRequirementValue {
    PORTAL_ONCE_IGNORE = 0,
    PORTAL_ONCE_REQUIRE_CLEAR = 1,
    PORTAL_ONCE_REQUIRE_SET = 2
} PortalOnceRequirementValue;

enum PortalRouteFlags {
    PORTAL_ROUTE_DEBOUNCE_ACCEPT = 1u << 0,
    PORTAL_ROUTE_REQUIRE_STABLE_CONTROL = 1u << 1,
    PORTAL_ROUTE_RESERVE_TARGET_BEFORE_CLOSE = 1u << 2,
    PORTAL_ROUTE_NO_PROGRESS_ON_CANCEL = 1u << 3
};

typedef struct PortalDialogueRouteDef {
    InteractionId interaction_id; /* 0 */
    ConditionId condition_id;     /* 2 */
    uint16_t target_id;           /* 4: DialogueId or TransitionId */
    uint8_t target_kind;          /* 6 */
    uint8_t priority;             /* 7: unique per interaction */
    uint8_t once_bit_index;       /* 8: zero unless once requirement nonignore */
    uint8_t once_requirement;     /* 9 */
    uint16_t flags;               /* 10 */
    uint16_t reserved;            /* 12 */
} PortalDialogueRouteDef;
_Static_assert(sizeof(PortalDialogueRouteDef) == 14, "PortalDialogueRouteDef layout");
```

The complete route table is:

| interaction / condition | target | priority / once | flags |
|---|---|---|---|
| `INT_SKIMMER_MAP / COND_PORTAL_EXIT_LOCKED_NO_RELAY` | `DIALOGUE / EXIT_LOCKED_NO_RELAY` | `40 / IGNORE` | all four flags |
| `INT_SKIMMER_MAP / COND_PORTAL_EXIT_LOCKED_NO_TRACE` | `DIALOGUE / EXIT_LOCKED_NO_TRACE` | `39 / IGNORE` | all four flags |
| `INT_SKIMMER_MAP / COND_TRANS_ANNEX_FIRST_DEPARTURE_NO_RETURN_FOLLOWER` | `DIALOGUE / EXIT_READY_001` | `38 / IGNORE` | all four flags |
| `INT_SKIMMER_MAP / COND_TRANS_ANNEX_REPEAT_TRAVEL_NO_RETURN_FOLLOWER` | `DIALOGUE / EXIT_READY_REPEAT_001` | `37 / IGNORE` | all four flags |
| `INT_ESTATE_SKIMMER / COND_TRANS_ESTATE_EXIT_NO_RETURN_FOLLOWER` | `TRANSITION / TRANS_DEF_ESTATE_TO_MAP` | `30 / IGNORE` | all four flags |
| `INT_ESTATE_SKIMMER / COND_TRANS_RETURN_FOLLOWER_ACTIVE` | `DIALOGUE / RUSK_EXIT_001` | `32 / bit 9 CLEAR` | all four flags |
| `INT_ESTATE_SKIMMER / COND_TRANS_RETURN_FOLLOWER_ACTIVE` | `DIALOGUE / RETURN_SKIMMER_REPEAT_001` | `31 / bit 9 SET` | all four flags |

"All four" is exact mask `0x000F`. The two new portal conditions are exact persisted predicates: NO_RELAY is `!FLAG_FIELD_RELAY_UNLOCKED`; NO_TRACE is `FLAG_FIELD_RELAY_UNLOCKED && !FLAG_ESTATE_DESTINATION_UNLOCKED`. The condition-registry compiler emits them alongside every other ConditionId. The four threshold rows are exhaustive and disjoint through the legal opening story range. The three Estate rows split on derived follower false/true, then bit 9 clear/set; priority cannot mask ambiguity, and generation proves exactly one legal row whenever the interaction is offered. `INT_SKIMMER_MAP` first emits `HELP_COMPLETE_EXTERIOR_EXIT_PROMPT_OPENED`, then debounces A/B and selects a row from the unchanged view. Cancel closes without progress, once-bit, save, dialogue, or transition mutation. A accepted row reserves its target before relinquishing interaction ownership; a transition target is validated under TransitionConditionView. Dialogue targets emit no StoryAction directly—their literal final/choice nodes own the sole StoryTrigger rows above.

The first OPEN target starts `SERA_DEPART_001`, never the map transition. Sera dismissal holds bit 7 as a deferred mutation and solely requests `TRANS_DEF_THRESHOLD_TO_MAP`; its pre-recipe commits that bit, departure flag, checkpoint, and save snapshot together before map staging. Repeat OPEN solely requests `TRANS_DEF_THRESHOLD_TO_MAP_REPEAT`. At the Estate skimmer, first accepted return plays `RUSK_EXIT_001 -> TAVI_EXIT_001`; only Tavi's final dismissal requests `TRANS_DEF_STUDY_RETURN_TO_MAP`. Once bit 9 is set, the repeat row skips both lines and uses its distinct continuation list. This gives cancel/retry and reboot one typed path without replay or direct-controller transition invention.

Shared mandatory/repeat NPCs and the five follower/post-chapter interactions use a
second typed selector. It is deliberately separate from portal routing and from
saved-once optional occurrence animation state:

```c
typedef enum OpeningNpcInteractionConditionIdValue {
    COND_NPC_POST_CHAPTER_SAVED = 0x6538,
    COND_NPC_POST_CHAPTER_DIRTY = 0x6539,
    COND_NPC_OREN_REPEAT = 0x653A
} OpeningNpcInteractionConditionIdValue;

typedef enum NpcInteractionPredicateKindValue {
    NPC_ROUTE_STORY_PRECONDITION = 1,
    NPC_ROUTE_INTERACTION_CONDITION = 2,
    NPC_ROUTE_POST_CHAPTER_CONDITION = 3
} NpcInteractionPredicateKindValue;

typedef enum NpcInteractionDispatchKindValue {
    NPC_ROUTE_DISPATCH_DIALOGUE = 1,
    NPC_ROUTE_DISPATCH_STORY_START = 2
} NpcInteractionDispatchKindValue;

enum NpcInteractionRouteFlags {
    NPC_ROUTE_DEBOUNCE_ACCEPT = 1u << 0,
    NPC_ROUTE_REQUIRE_STABLE_CONTROL = 1u << 1,
    NPC_ROUTE_RESERVE_DIALOGUE_BEFORE_RELEASE = 1u << 2,
    NPC_ROUTE_CLEAR_INPUT_LATCHES = 1u << 3
};

typedef struct NpcInteractionRouteDef {
    InteractionId interaction_id; /* 0 */
    uint16_t predicate_id;        /* 2: ConditionId or StoryStartPreconditionId */
    DialogueId dialogue_id;       /* 4: direct root or StoryStart equality mirror */
    uint8_t predicate_kind;       /* 6 */
    uint8_t dispatch_kind;        /* 7 */
    uint8_t priority;             /* 8: unique per InteractionId */
    uint8_t reserved0;            /* 9 */
    uint16_t flags;               /* 10 */
    uint16_t reserved1;           /* 12 */
} NpcInteractionRouteDef;
_Static_assert(sizeof(NpcInteractionRouteDef) == 14, "NpcInteractionRouteDef layout");

enum NpcInteractionPlacementFlags {
    NPC_PLACEMENT_PHYSICAL_PROMPT = 1u << 0,
    NPC_PLACEMENT_FOLLOWER_ATTACHED = 1u << 1,
    NPC_PLACEMENT_REQUIRE_DERIVED_FOLLOWER = 1u << 2,
    NPC_PLACEMENT_POST_CHAPTER_ONLY = 1u << 3
};

typedef struct NpcInteractionPlacementDef {
    InteractionId interaction_id; /* 0 */
    CharacterId character_id;     /* 2 */
    SceneId scene_id;             /* 4; zero only for follower-attached */
    ZoneId zone_id;               /* 6; zero only for follower-attached */
    uint16_t flags;               /* 8 */
    uint16_t reserved;            /* 10 */
} NpcInteractionPlacementDef;
_Static_assert(sizeof(NpcInteractionPlacementDef) == 12, "NpcInteractionPlacementDef layout");
```

The five new physical placements are exact:

| InteractionId | Character / Scene / Zone | flags |
|---|---|---|
| `INT_NPC_TAVI_FOLLOW` | `CHAR_TAVI / 0 / 0` | `PHYSICAL_PROMPT + FOLLOWER_ATTACHED + REQUIRE_DERIVED_FOLLOWER` |
| `INT_NPC_SERA_POST` | `CHAR_DR_SERA_VENN / SCENE_ANNEX_INTERIOR / ZONE_ANNEX_ATRIUM` | `PHYSICAL_PROMPT + POST_CHAPTER_ONLY` |
| `INT_NPC_TAVI_POST` | `CHAR_TAVI / SCENE_ANNEX_INTERIOR / ZONE_ANNEX_ATRIUM` | `PHYSICAL_PROMPT + POST_CHAPTER_ONLY` |
| `INT_NPC_RUSK_POST` | `CHAR_RUSK / SCENE_ESTATE_COURTYARD / ZONE_ESTATE_COURTYARD` | `PHYSICAL_PROMPT + POST_CHAPTER_ONLY` |
| `INT_NPC_IVO_POST` | `CHAR_IVO_VEYRA / SCENE_ESTATE_INTERIOR / ZONE_ESTATE_OBSERVATORY_STUDY` | `PHYSICAL_PROMPT + POST_CHAPTER_ONLY` |

The placement flag aliases expand exactly to `NPC_PLACEMENT_*`. Each placement
must resolve one real generated `InteractionDef`, not merely a router row. Those
five physical rows are literal:

| InteractionId | Zone / anchor / prompt | condition / action | radius / facing / priority / offset | InteractionDef flags |
|---|---|---|---|---|
| `INT_NPC_TAVI_FOLLOW` | `ZONE_NONE / ASSET_MODEL_CHR_TAVI / STR_UI_INTERACT` | `0 / 0` | `384 / 8192 / 90 / 256` | `VARIANT_DRIVEN + REPEATABLE + ACTOR_ATTACHED` |
| `INT_NPC_SERA_POST` | `ZONE_ANNEX_ATRIUM / ASSET_MODEL_CHR_SERA_VENN / STR_UI_INTERACT` | `0 / 0` | `384 / 8192 / 90 / 256` | `VARIANT_DRIVEN + REPEATABLE` |
| `INT_NPC_TAVI_POST` | `ZONE_ANNEX_ATRIUM / ASSET_MODEL_CHR_TAVI / STR_UI_INTERACT` | `0 / 0` | `384 / 8192 / 89 / 256` | `VARIANT_DRIVEN + REPEATABLE` |
| `INT_NPC_RUSK_POST` | `ZONE_ESTATE_COURTYARD / ASSET_MODEL_CHR_RUSK / STR_UI_INTERACT` | `0 / 0` | `384 / 8192 / 90 / 256` | `VARIANT_DRIVEN + REPEATABLE` |
| `INT_NPC_IVO_POST` | `ZONE_ESTATE_OBSERVATORY_STUDY / ASSET_MODEL_CHR_IVO_VEYRA / STR_UI_INTERACT` | `0 / 0` | `384 / 8192 / 90 / 256` | `VARIANT_DRIVEN + REPEATABLE` |

`STR_UI_INTERACT` is the graph-generated StringId for `UI_INTERACT`; the model
AssetId supplies the inventory-required authored dialogue focus socket. The
InteractionDef flag aliases expand exactly to `INTERACTION_*`. The two fixed
Annex rows consume two of the already-budgeted 12 `int.annex.atrium` records,
Rusk consumes one of the existing 10 `int.estate.courtyard` records, and Ivo
consumes one of the existing 10 `int.estate.observatory_study` records; generation
must still equal those frozen inventory totals. The actor-attached follower row
is a generated child of `chr.tavi`, follows the live actor across legal Estate
zones, and is not counted in a fixed zone interaction index. It is present only
while the derived follower generation is current. Nonzero prompt/radius, focus
socket existence, exact Q8/Q14 bounds, zero router-owned condition/action, and
the per-zone totals are compile-time validations.

The complete mandatory/shared/post selector rows are:

| Interaction / predicate | kind / dispatch | root | priority |
|---|---|---|---:|
| `INT_NPC_OREN / COND_NPC_POST_CHAPTER_DIRTY` | `POST_CHAPTER_CONDITION / DIALOGUE` | `POST_OREN_UNSAVED_001` | 6 |
| `INT_NPC_OREN / COND_NPC_POST_CHAPTER_SAVED` | `POST_CHAPTER_CONDITION / DIALOGUE` | `POST_OREN_001` | 5 |
| `INT_NPC_OREN / STORY_PRECOND_OREN_ASSIGNMENT_READY` | `STORY_PRECONDITION / STORY_START` | `OREN_001` | 3 |
| `INT_NPC_OREN / COND_NPC_OREN_REPEAT` | `INTERACTION_CONDITION / DIALOGUE` | `OREN_004` | 2 |
| `INT_NPC_JO / STORY_PRECOND_JO_RELAY_READY` | `STORY_PRECONDITION / STORY_START` | `JO_RELAY_001` | 3 |
| `INT_NPC_PELL / COND_SAVE_SLICE_COMPLETE` | `INTERACTION_CONDITION / DIALOGUE` | `POST_PELL_001` | 5 |
| `INT_NPC_PELL / STORY_PRECOND_PELL_TRACE_READY` | `STORY_PRECONDITION / STORY_START` | `PELL_TRACE_001` | 3 |
| `INT_NPC_TAVI_FOLLOW / COND_TRANS_RETURN_FOLLOWER_ACTIVE` | `INTERACTION_CONDITION / DIALOGUE` | `TAVI_FOLLOW_001` | 3 |
| `INT_NPC_SERA_POST / COND_SAVE_SLICE_COMPLETE` | `INTERACTION_CONDITION / DIALOGUE` | `POST_SERA_001` | 3 |
| `INT_NPC_TAVI_POST / COND_SAVE_SLICE_COMPLETE` | `INTERACTION_CONDITION / DIALOGUE` | `POST_TAVI_001` | 3 |
| `INT_NPC_RUSK_POST / COND_SAVE_SLICE_COMPLETE` | `INTERACTION_CONDITION / DIALOGUE` | `POST_RUSK_001` | 3 |
| `INT_NPC_IVO_POST / COND_SAVE_SLICE_COMPLETE` | `INTERACTION_CONDITION / DIALOGUE` | `POST_IVO_001` | 3 |

Every row carries exact route flags `0x000F` and zero reserved fields. A
`STORY_START` dispatch emits the typed `INTERACTION_ACCEPT` source; it does not
acquire the mirrored root directly, and the StoryStart table must byte-agree on
interaction, precondition, and root. If no typed row matches, Jo and Pell may
fall through to their existing `NpcOccurrenceVariantDef` optional selector;
Oren has an intentional no-dialogue state before assignment becomes legal.
Follower-attached placement resolves against the current Tavi actor generation
and accepts no fixed zone; all other rows require exact physical placement.

The Oren selector is exhaustively truth-table tested. Slice-complete plus
`CONTINUE_UNSAVED/dirty` selects priority 6; slice-complete plus durable `SAVED`
selects priority 5 for either clean or newer-dirty runtime; pre-slice
assignment-ready selects priority 3; and Relay-quest-started while Relay remains
locked selects priority 2. Semantic validation rejects `CONTINUE_UNSAVED/clean`.
While the final outcome is pending
the end owner prevents post-chapter exploration, so no Oren prompt is offered.
`COND_NPC_OREN_REPEAT` is exactly Relay-quest-started AND NOT Relay-unlocked and
therefore cannot reach action-bearing `OREN_003` or replay stale "retrieve the
Relay" copy after Jo's handoff. Later pre-chapter Oren states intentionally have
no dialogue until the post-chapter rows become legal. `COND_SAVE_SLICE_COMPLETE`
already proves the Rusk win, Orrery, Tavi, and chapter invariants; the Rusk/Ivo
placement supplies the additional Estate/Courtyard/Study accessibility fact.
Equal highest priorities, a direct acquisition for a STORY_START row, optional
once state affecting era selection, missing physical placement, or a condition
view outside the registered context fails generation.

Conditions use bounds-checked reverse-Polish instructions so compound requirements remain data-driven:

```c
typedef enum ConditionOp {
    COND_PUSH_SOURCE = 1,
    COND_NOT,
    COND_AND,
    COND_OR,
    COND_EQ,
    COND_GE
} ConditionOp;

typedef enum ConditionSourceValue {
    CONDITION_SOURCE_CONSTANT = 1,
    CONDITION_SOURCE_PROGRESS_FLAG = 2,
    CONDITION_SOURCE_OBJECTIVE_STATE = 3,
    CONDITION_SOURCE_CURRENT_SCENE = 4,
    CONDITION_SOURCE_PARTY_CREATURE = 5,
    CONDITION_SOURCE_QUEST_COUNTER = 6,
    CONDITION_SOURCE_DESTINATION_BIT = 7,
    CONDITION_SOURCE_RELAY_PAGE_BITS = 8,
    CONDITION_SOURCE_CHECKPOINT_ID = 9,
    CONDITION_SOURCE_BATTLE_RESULT = 10,
    CONDITION_SOURCE_RUNTIME_DRAFT_STATE = 11,
    CONDITION_SOURCE_TUTORIAL_RESULT_STATE = 12,
    CONDITION_SOURCE_PRE_RUSK_SNAPSHOT_STATE = 13,
    CONDITION_SOURCE_SELECTED_MAP_NODE = 14,
    CONDITION_SOURCE_RUNTIME_CHECKPOINT_TOKEN = 15,
    CONDITION_SOURCE_RETURN_FOLLOWER_STATE = 16,
    CONDITION_SOURCE_SELECTED_JOURNAL_SEMANTIC_CLASS = 17,
    CONDITION_SOURCE_RUNTIME_DIRTY_STATE = 18,
    CONDITION_SOURCE_FINAL_SAVE_OUTCOME = 19,
    CONDITION_SOURCE_DIRTY_WARNING_ACK = 20,
    CONDITION_SOURCE_CONTROL_STATE = 21,
    CONDITION_SOURCE_PROCESS_ACCEPT_TOKEN = 22,
    CONDITION_SOURCE_OPENING_FINALIZER_GENERATION = 23,
    CONDITION_SOURCE_RUNTIME_CURRENT_SAVELOC = 24
} ConditionSourceValue;

typedef enum RuntimeDraftStateValue {
    RUNTIME_DRAFT_NONE = 0,
    RUNTIME_DRAFT_NEW_GAME_ACCEPTED = 1,
    RUNTIME_DRAFT_OPENING_FINALIZED = 2,
    RUNTIME_DRAFT_NAME_CONFIRMED = 3
} RuntimeDraftStateValue;

typedef enum TutorialResultStateValue {
    TUTORIAL_RESULT_INCOMPLETE = 0,
    TUTORIAL_RESULT_COMPLETE = 1
} TutorialResultStateValue;

typedef enum PreRuskSnapshotStateValue {
    PRE_RUSK_SNAPSHOT_INVALID = 0,
    PRE_RUSK_SNAPSHOT_VALID = 1
} PreRuskSnapshotStateValue;

typedef enum MapSelectionValue {
    MAP_SELECTION_NONE = 0,
    MAP_SELECTION_ANNEX = 1,
    MAP_SELECTION_ESTATE = 2,
    MAP_SELECTION_BACK = 3
} MapSelectionValue;

typedef enum RuntimeCheckpointTokenValue {
    RUNTIME_CHECKPOINT_NONE = 0,
    RUNTIME_CHECKPOINT_SLICE_COMPLETE_COMMITTED = 1
} RuntimeCheckpointTokenValue;

typedef enum ReturnFollowerStateValue {
    RETURN_FOLLOWER_INACTIVE = 0,
    RETURN_FOLLOWER_ACTIVE = 1
} ReturnFollowerStateValue;

typedef enum JournalSemanticClassValue {
    JOURNAL_SEMANTIC_INVALID = 0,
    JOURNAL_SEMANTIC_VALID_GENERAL = 1,
    JOURNAL_SEMANTIC_VALID_SLICE_FINAL = 2
} JournalSemanticClassValue;

typedef enum RuntimeDirtyStateValue {
    RUNTIME_PROGRESS_CLEAN = 0,
    RUNTIME_PROGRESS_DIRTY = 1
} RuntimeDirtyStateValue;

typedef enum FinalSaveOutcomeValue {
    FINAL_SAVE_OUTCOME_PENDING = 0,
    FINAL_SAVE_OUTCOME_SAVED = 1,
    FINAL_SAVE_OUTCOME_CONTINUE_UNSAVED = 2
} FinalSaveOutcomeValue;

typedef enum DirtyWarningAckValue {
    DIRTY_WARNING_NOT_ACKNOWLEDGED = 0,
    DIRTY_WARNING_END_CARD_RETURN_ACK = 1,
    DIRTY_WARNING_GAMEPLAY_RETURN_ACK = 2,
    DIRTY_WARNING_ROLLBACK_FATAL_RETURN_ACK = 3
} DirtyWarningAckValue;

typedef enum ControlStateValue {
    CONTROL_STATE_UNSTABLE = 0,
    CONTROL_STATE_STABLE = 1
} ControlStateValue;

For `ProcessNavigationConditionView`, source 21 publishes
`CONTROL_STATE_STABLE` only from a retained, generation-current Pause origin.
The origin is legal either when no `BattleRuntimeOwner` exists and the captured
exploration control generation/stable-state token still matches, or when a live
owner matches the current campaign and `GameProgress.runtime_generation`, its
`battle_generation` equals `ProcessUiOriginSnapshot.control_generation`, and
`BattleState.phase` is exactly `BATTLE_PHASE_COMMAND_SELECT` or
`BATTLE_PHASE_TARGET_SELECT` with no pending/committed action, event
presentation, replacement, result, transition, save candidate, or teardown.
The Pause owner remains the sole input owner while this structural check runs;
the same retained snapshot is used beneath a dirty-return warning. Every other
state publishes `CONTROL_STATE_UNSTABLE`. The Condition VM receives only that
typed scalar, never a pointer to `BattleState` or `BattleRuntimeOwner`.

typedef enum ProcessAcceptTokenValue {
    PROCESS_ACCEPT_NONE = 0,
    PROCESS_ACCEPT_NEW_GAME = 1,
    PROCESS_ACCEPT_OPENING_FINISH = 2,
    PROCESS_ACCEPT_NAME_CONFIRM = 3,
    PROCESS_ACCEPT_NAME_CANCEL_RETURN = 4,
    PROCESS_ACCEPT_TITLE_CONTINUE = 5,
    PROCESS_ACCEPT_RETURN_TO_TITLE = 6,
    PROCESS_ACCEPT_NEW_GAME_ABORT_TO_TITLE = 7
} ProcessAcceptTokenValue;

typedef enum OpeningFinalizerGenerationValue {
    OPENING_FINALIZER_GENERATION_INVALID = 0,
    OPENING_FINALIZER_GENERATION_CURRENT = 1
} OpeningFinalizerGenerationValue;

typedef enum ConditionValueType {
    CONDITION_VALUE_BOOL = 1,
    CONDITION_VALUE_U8 = 2,
    CONDITION_VALUE_U16 = 3,
    CONDITION_VALUE_OBJECTIVE_STATE = 4,
    CONDITION_VALUE_SCENE_ID = 5,
    CONDITION_VALUE_CHECKPOINT_ID = 6,
    CONDITION_VALUE_BATTLE_RESULT = 7,
    CONDITION_VALUE_RUNTIME_DRAFT = 8,
    CONDITION_VALUE_TUTORIAL_RESULT = 9,
    CONDITION_VALUE_PRE_RUSK_SNAPSHOT = 10,
    CONDITION_VALUE_MAP_SELECTION = 11,
    CONDITION_VALUE_RUNTIME_CHECKPOINT = 12,
    CONDITION_VALUE_RETURN_FOLLOWER = 13,
    CONDITION_VALUE_JOURNAL_SEMANTIC = 14,
    CONDITION_VALUE_RUNTIME_DIRTY = 15,
    CONDITION_VALUE_FINAL_SAVE_OUTCOME = 16,
    CONDITION_VALUE_DIRTY_WARNING_ACK = 17,
    CONDITION_VALUE_CONTROL_STATE = 18,
    CONDITION_VALUE_PROCESS_ACCEPT = 19,
    CONDITION_VALUE_OPENING_GENERATION = 20,
    CONDITION_VALUE_SAVEABLE_LOCATION_ID = 21
} ConditionValueType;

enum {
    CONDITION_INSTRUCTIONS_PER_DEF_MAX = 32,
    CONDITION_STACK_DEPTH_MAX = 8,
    CONDITION_INSTRUCTION_TABLE_MAX = 2048
};

enum ConditionContextMask {
    CONDITION_CONTEXT_PROGRESS = 1u << 0,
    CONDITION_CONTEXT_TRANSITION = 1u << 1,
    CONDITION_CONTEXT_PROCESS_NAV = 1u << 2,
    CONDITION_CONTEXT_INTERACTION = 1u << 3,
    CONDITION_CONTEXT_SAVE_CODEC = 1u << 4,
    CONDITION_CONTEXT_POST_CHAPTER_INTERACTION = 1u << 5
};

typedef struct ConditionInstr {
    uint8_t op;          /* 0 */
    uint8_t source;      /* 1 */
    uint16_t subject_id; /* 2 */
    int32_t value;       /* 4 */
} ConditionInstr;
_Static_assert(sizeof(ConditionInstr) == 8, "ConditionInstr layout");

typedef struct ConditionDef {
    ConditionId id;                 /* 0 */
    uint16_t first_instruction;     /* 2 */
    uint16_t instruction_count;     /* 4 */
    uint8_t max_stack_depth;        /* 6 */
    uint8_t context_mask;           /* 7 */
    uint32_t allowed_source_mask;   /* 8: bit(source-1), sources 1..24 */
    uint32_t reserved;              /* 12 */
} ConditionDef;
_Static_assert(sizeof(ConditionDef) == 16, "ConditionDef layout");
```

The condition VM uses a tagged stack cell `{ ConditionValueType type; int32_t value; }`; no width-based or signedness coercion exists. `COND_PUSH_SOURCE` has stack arity `0->1`. Every nonconstant source has `value=0` and returns the exact type below; its `subject_id` domain is also exact. `CONDITION_SOURCE_CONSTANT` instead uses `subject_id=ConditionValueType` and `value` as the literal, which must fit and belong to that type's declared enum/ID domain.

| Source | Legal `subject_id` | Result type / producer |
|---|---|---|
| `CONDITION_SOURCE_CONSTANT` | `ConditionValueType` | that exact type; validates literal domain |
| `CONDITION_SOURCE_PROGRESS_FLAG` | locked story-flag index `0..22` | BOOL, candidate progress bit |
| `CONDITION_SOURCE_OBJECTIVE_STATE` | registered ObjectiveId `1..4` | OBJECTIVE_STATE, candidate byte |
| `CONDITION_SOURCE_CURRENT_SCENE` | 0 | SCENE_ID, candidate `current_location.scene_id` |
| `CONDITION_SOURCE_PARTY_CREATURE` | registered nonzero CreatureId resolving to CreatureDef | BOOL, present in candidate party |
| `CONDITION_SOURCE_QUEST_COUNTER` | index `0..7` | U8, candidate counter |
| `CONDITION_SOURCE_DESTINATION_BIT` | registered bit `0..1` | BOOL, candidate bit |
| `CONDITION_SOURCE_RELAY_PAGE_BITS` | registered bit `0..3` | BOOL, candidate bit |
| `CONDITION_SOURCE_CHECKPOINT_ID` | 0 | CHECKPOINT_ID, candidate checkpoint |
| `CONDITION_SOURCE_BATTLE_RESULT` | 0 | BATTLE_RESULT, candidate result |
| `CONDITION_SOURCE_RUNTIME_DRAFT_STATE` | 0 | RUNTIME_DRAFT, draft owner |
| `CONDITION_SOURCE_TUTORIAL_RESULT_STATE` | 0 | TUTORIAL_RESULT, tutorial owner |
| `CONDITION_SOURCE_PRE_RUSK_SNAPSHOT_STATE` | 0 | PRE_RUSK_SNAPSHOT, snapshot owner |
| `CONDITION_SOURCE_SELECTED_MAP_NODE` | 0 | MAP_SELECTION, map controller |
| `CONDITION_SOURCE_RUNTIME_CHECKPOINT_TOKEN` | 0 | RUNTIME_CHECKPOINT, story controller |
| `CONDITION_SOURCE_RETURN_FOLLOWER_STATE` | 0 | RETURN_FOLLOWER, follower derivation |
| `CONDITION_SOURCE_SELECTED_JOURNAL_SEMANTIC_CLASS` | 0 | JOURNAL_SEMANTIC, verified loader |
| `CONDITION_SOURCE_RUNTIME_DIRTY_STATE` | 0 | RUNTIME_DIRTY, save service |
| `CONDITION_SOURCE_FINAL_SAVE_OUTCOME` | 0 | FINAL_SAVE_OUTCOME, save service |
| `CONDITION_SOURCE_DIRTY_WARNING_ACK` | 0 | DIRTY_WARNING_ACK, process UI |
| `CONDITION_SOURCE_CONTROL_STATE` | 0 | CONTROL_STATE, control owner |
| `CONDITION_SOURCE_PROCESS_ACCEPT_TOKEN` | 0 | PROCESS_ACCEPT, process controller |
| `CONDITION_SOURCE_OPENING_FINALIZER_GENERATION` | 0 | OPENING_GENERATION, opening owner |
| `CONDITION_SOURCE_RUNTIME_CURRENT_SAVELOC` | 0 | SAVEABLE_LOCATION_ID, exact registry resolver |

For operator instructions, `source`, `subject_id`, and `value` are all zero. `COND_NOT` pops one BOOL and pushes BOOL. `COND_AND` and `COND_OR` pop two BOOL values and push BOOL. `COND_EQ` pops two cells of the identical `ConditionValueType` and pushes BOOL; all listed types are equality-comparable. `COND_GE` pops identical types and is legal only for U8, U16, OBJECTIVE_STATE, or JOURNAL_SEMANTIC, whose numeric orders are explicitly locked; IDs, booleans, and every other enum are not ordered. Operand order is `lhs` below `rhs`, producing `lhs op rhs`. A type mismatch, illegal literal, unknown op/source, nonzero operator operand, underflow, or overflow is invalid data; runtime evaluation fails closed to false and records a debug fault.

Every condition has `instruction_count` in `1..32`, computed peak stack in `1..8`, and `max_stack_depth` exactly equal to that computed peak. The global instruction table has at most 2048 rows. Generation widens `first_instruction + instruction_count` to 32 bits, requires it within the actual table, rejects overlapping ranges and duplicate/zero ConditionIds, symbolically executes every path, and requires the terminal stack to contain exactly one BOOL. Runtime checks the same range before evaluation, allocates exactly eight fixed cells, and never reads beyond the declared slice.

Condition evaluation is a pure read over one immutable typed view. Progress/dialogue/objective/save-location and save-codec conditions receive only persisted candidate fields through `ProgressConditionView` and may use sources 1-10. `TransitionConditionView` adds sources 11-16 and 21. `ProcessNavigationConditionView` adds sources 17-24. Ordinary interaction conditions receive the transition-grade view, but the Orrery pair reads only its persisted flag. `PostChapterInteractionConditionView` is a distinct read-only caller view: it exposes persisted sources 1-10 plus save-service-owned source 18 `RUNTIME_DIRTY_STATE` and source 19 `FINAL_SAVE_OUTCOME`, and no other runtime source. `ConditionDef.context_mask` accepts only `0x3F`; `allowed_source_mask` must equal the sources actually referenced and be a subset of every declared context whitelist. Context bits name legal callers, not source ancestry, so `COND_NPC_POST_CHAPTER_SAVED` and `COND_NPC_POST_CHAPTER_DIRTY` use only `CONDITION_CONTEXT_POST_CHAPTER_INTERACTION`, while `COND_NPC_OREN_REPEAT` uses only `CONDITION_CONTEXT_INTERACTION`. A save condition containing source 11-24 is a build failure, so saved-row legality cannot depend on control, selection, generation, warning, or UI provenance.

Runtime-only producers are single-owner and generation-bound. The title/menu controller emits an accept token only after a debounced commit; the opening finalizer owns its generation; the map controller owns selection; the verified loader owns journal class; story owns the checkpoint token; and the save service owns outcome/dirty. Each view carries the live runtime generation plus per-owner generation/validity. If any referenced runtime source is absent or stale, the whole condition returns false before executing; a stale value is never silently coerced to a current zero enum. The post-chapter interaction view additionally requires `FLAG_SLICE_COMPLETE`, post-chapter exploration ownership, stable control, and a current save-service outcome/dirty generation before sources 18/19 are exposed. `JOURNAL_SEMANTIC_VALID_SLICE_FINAL` proves a fully valid `CHECKPOINT_SLICE_COMPLETE` page and every final checkpoint equivalence; its `SaveReason` may be Final Hook or any later operation legally permitted for that checkpoint, because reason is provenance rather than resume identity. The process resolver maps the coherent in-memory `LocationKey` by exact tuple equality to one condition-valid `SaveableLocationDef` and publishes its `SaveableLocationId`; no code compares a `LocationKey` struct to an integer ID. Views contain copied scalars, not subsystem objects, and evaluation cannot mutate, allocate, consume RNG, present, or follow pointers.

```c
typedef enum StoryActionOp {
    ACTION_SET_FLAG = 1,
    ACTION_ADVANCE_OBJECTIVE = 2,
    ACTION_UNLOCK_DESTINATION = 3,
    ACTION_GRANT_PARTY = 4,
    ACTION_GRANT_REWARD_ONCE = 5,
    ACTION_REFRESH_DERIVED_FOLLOWER = 6,
    ACTION_REQUEST_SAVE = 7,
    ACTION_REQUEST_TRANSITION = 8,
    ACTION_START_DIALOGUE = 9,
    ACTION_START_CUTSCENE = 10,
    ACTION_START_ENCOUNTER = 11,
    ACTION_SET_RELAY_PAGE = 12,
    ACTION_SET_BOUNDED_QUEST_SUBSTAGE = 13,
    ACTION_COMMIT_MECHANISM_WORLD_TXN = 14,
    ACTION_CAPTURE_PRE_RUSK_SNAPSHOT = 15,
    ACTION_REQUEST_RETENTION_SAVE = 16,
    ACTION_ADVANCE_TUTORIAL_GATE = 17,
    ACTION_RESTORE_PARTY_HP = 18,
    ACTION_START_WORLD_CALLBACK = 19,
    ACTION_RESTART_TUTORIAL = 20
} StoryActionOp;

enum StoryActionFlags {
    STORY_ACTION_IDEMPOTENT = 1u << 0,
    STORY_ACTION_APPLY_ON_SKIP = 1u << 1,
    STORY_ACTION_EXTERNAL_REQUEST = 1u << 2
};

enum StoryActionContextFlags {
    STORY_CONTEXT_DIALOGUE = 1u << 0,
    STORY_CONTEXT_CUTSCENE = 1u << 1,
    STORY_CONTEXT_INTERACTION = 1u << 2,
    STORY_CONTEXT_BATTLE_RESULT = 1u << 3,
    STORY_CONTEXT_CHECKPOINT = 1u << 4,
    STORY_CONTEXT_PROCESS = 1u << 5,
    STORY_CONTEXT_TRANSITION = 1u << 6
};

enum StoryActionListFlags {
    STORY_LIST_ATOMIC_PROGRESS = 1u << 0,
    STORY_LIST_SKIP_FINALIZER = 1u << 1
};

enum {
    STORY_ACTION_LIST_COUNT_MAX = 256,
    STORY_ACTIONS_PER_LIST_MAX = 24,
    STORY_EXTERNAL_REQUESTS_PER_LIST_MAX = 2,
    STORY_ACTION_TABLE_MAX = 2048
};

typedef struct StoryAction {
    uint8_t op;            /* 0 */
    uint8_t flags;         /* 1: idempotent, apply-on-skip */
    uint16_t subject_id;   /* 2 */
    uint32_t value;        /* 4 */
    uint16_t aux_id;       /* 8 */
    uint16_t reserved;     /* 10 */
} StoryAction;
_Static_assert(sizeof(StoryAction) == 12, "StoryAction layout");

typedef struct StoryActionListDef {
    StoryActionListId id;         /* 0 */
    uint16_t first_action;        /* 2 */
    uint8_t action_count;         /* 4 */
    uint8_t external_request_count; /* 5 */
    uint16_t context_flags;       /* 6 */
    uint16_t flags;               /* 8 */
    uint16_t reserved;            /* 10 */
} StoryActionListDef;
_Static_assert(sizeof(StoryActionListDef) == 12, "StoryActionListDef layout");
```

Every opcode has one exact operand and execution contract. `zero` below means every bit is zero; a packed ID occupies only its stated bits and all remaining bits are zero.

| Op | Exact `subject_id` / `value` / `aux_id` | Legal action flags | Typed behavior |
|---|---|---|---|
| `ACTION_SET_FLAG` | registered story-flag index / `1` / zero | `IDEMPOTENT + APPLY_ON_SKIP` | set one monotonic scratch flag; clearing is illegal and Orrery is excluded |
| `ACTION_ADVANCE_OBJECTIVE` | registered ObjectiveId / expected state bits 0-7 plus next state bits 8-15 / resulting active ObjectiveId or 0 | zero | require exact expected state, legal locked transition, and one-active-objective invariant |
| `ACTION_UNLOCK_DESTINATION` | registered DestinationBit / `1` / zero | `IDEMPOTENT + APPLY_ON_SKIP` | set one registered scratch destination bit |
| `ACTION_GRANT_PARTY` | registered TeamId / zero / zero | `IDEMPOTENT + APPLY_ON_SKIP` | install the exact TeamDef once; an exact already-installed team is a no-op, any mismatch fails |
| `ACTION_GRANT_REWARD_ONCE` | RewardId / claim-bit index in low 8 bits / EncounterId | `IDEMPOTENT + APPLY_ON_SKIP` | apply exact RewardDef only when unclaimed; exact claimed state is a no-op |
| `ACTION_REFRESH_DERIVED_FOLLOWER` | zero / zero / zero | `IDEMPOTENT + APPLY_ON_SKIP` | recompute volatile follower after scratch publish; writes no save bit |
| `ACTION_REQUEST_SAVE` | registered nonzero ChapterMilestoneRecipeId / zero / zero | `EXTERNAL_REQUEST`; `APPLY_ON_SKIP` only in a declared `SKIP_FINALIZER` | apply the exact milestone recipe to scratch, validate it, then enqueue its immutable generation-bound snapshot after joint commit |
| `ACTION_REQUEST_TRANSITION` | one locked TransitionId / zero / zero | `EXTERNAL_REQUEST + APPLY_ON_SKIP` | enqueue that exact row; raw Scene/Zone/Spawn/style/save operands are forbidden |
| `ACTION_START_DIALOGUE` | registered DialogueId / zero / zero | `EXTERNAL_REQUEST` | start only after current owner closes and progress commits |
| `ACTION_START_CUTSCENE` | registered CutsceneId / zero / zero | `EXTERNAL_REQUEST` | start the resolved CutsceneDef after commit |
| `ACTION_START_ENCOUNTER` | registered EncounterId / zero / zero | `EXTERNAL_REQUEST` | start after a paired battle TransitionId commits, or immediately when already at its battle spawn |
| `ACTION_SET_RELAY_PAGE` | registered RelayPageBit `0..3` / `1` / zero | `IDEMPOTENT + APPLY_ON_SKIP` | set one player-owned page bit in scratch progress |
| `ACTION_SET_BOUNDED_QUEST_SUBSTAGE` | counter index `0..7` / expected-next-maximum packed below / zero | zero | exact monotonic scratch-counter compare-and-advance |
| `ACTION_COMMIT_MECHANISM_WORLD_TXN` | owner InteractionId / low 16 StoryActionListId with high 16 zero / zero | `IDEMPOTENT + APPLY_ON_SKIP` | resolve and atomically publish one typed MechanismWorldTransactionDef |
| `ACTION_CAPTURE_PRE_RUSK_SNAPSHOT` | `ENCOUNTER_RUSK_COURTYARD` / zero / zero | zero | after scratch invariants, capture a fresh current-generation immutable prebattle snapshot before any battle transition enqueue |
| `ACTION_REQUEST_RETENTION_SAVE` | registered nonzero StoryRetentionSaveRecipeId / zero / zero | `EXTERNAL_REQUEST` | retain checkpoint/chapter/location semantics, encode current scratch one-shot mutation, and enqueue the exact immutable replacement page |
| `ACTION_ADVANCE_TUTORIAL_GATE` | `TUTORIAL_SCRIPT_OPENING` / expected phase in bits 0-7 plus next phase in bits 8-15 / `ENCOUNTER_SIM_TUTORIAL` | zero | generation-bound compare-and-advance of the already-live tutorial owner; never constructs an encounter or actor |
| `ACTION_RESTORE_PARTY_HP` | registered TeamId / zero / zero | `IDEMPOTENT + APPLY_ON_SKIP` | require the exact installed team and set every living filled member to its derived maximum HP in scratch progress |
| `ACTION_START_WORLD_CALLBACK` | registered StoryControllerCallbackId / zero / zero | `EXTERNAL_REQUEST` | reserve and start the exact generation-bound world callback after scratch progress commits and the dialogue owner closes |
| `ACTION_RESTART_TUTORIAL` | `TUTORIAL_SCRIPT_OPENING` / exact seed `0x53494D31` / `ENCOUNTER_SIM_TUTORIAL` | `EXTERNAL_REQUEST` | resolve the sole TutorialRestartDef, reserve all reconstruction resources, then replace only tutorial-local runtime after the Restart dialogue closes |

The table's shorthand names mean the declared `STORY_ACTION_*` bits. `StoryAction.flags` accepts only mask `0x07`; an operation may use only its row's subset. `STORY_ACTION_APPLY_ON_SKIP` always requires `STORY_ACTION_IDEMPOTENT`, except a skip-finalizer external save/transition whose list-level generation key supplies exact-once behavior. Every request/start opcode requires `STORY_ACTION_EXTERNAL_REQUEST`; every mutation/refresh/mechanism opcode forbids it. Unknown opcodes, flags, IDs, nonzero reserved/unused bits, or operand/domain disagreement fail generation.

An action list is validated completely and applied to scratch `GameProgress`. Scratch mutations come first, followed by an optional snapshot capture, at most one mechanism transaction, and at most one derived-follower refresh. Mechanism/follower resources are prevalidated and staged against the prospective scratch state. Every external suffix target/combination/generation is prevalidated and its bounded queue slots are reserved before publish. One no-fail commit publishes scratch progress, a newly captured immutable prebattle snapshot if requested, mechanism world state, and derived follower state together; suffix enqueue into reserved slots is then no-fail. Any validation/staging/reservation failure releases reservations/staging and publishes nothing. There is no post-progress follower validation or queue-full failure that can strand non-idempotent progress.

`StoryActionListDef.action_count` is `1..24`; `external_request_count` is `0..2` and equals the actual suffix count. Context flags accept only `0x007F`, list flags only `0x0003`, and reserved is zero. There are at most 256 unique nonzero list IDs and 2048 actions. Widened `first_action + action_count` must be within the actual dense action table; list ranges cannot overlap; every dialogue/cutscene/interaction/encounter/checkpoint/process/transition reference resolves to a list whose context admits the caller. The generator rejects a duplicate list, orphan action, illegal order, or count/flag mismatch.

An external suffix is one of: one save; one transition; one terminal start; one typed world callback; one tutorial restart; save then transition; or battle transition then matching encounter start. Dialogue/cutscene/encounter starts, world callbacks, and tutorial restart are mutually exclusive. There is at most one of each request kind. A save-then-transition pair is legal only when the referenced TransitionDef has `SAVE_NONE`; the first action's immutable snapshot and SaveReason are the sole persistence authority, the transition cannot issue/coalesce a second write, and a failed save prevents transition enqueue. The battle pair requires `TRANSITION_BATTLE_START` or `TRANSITION_BATTLE_RETRY`, a destination matching the EncounterDef, and exact order transition then encounter; the dispatcher attaches encounter start as a transition-COMMIT continuation. A world callback resolves one typed callback row, reserves its generation-bound owner before scratch publish, and may appear only as the final suffix. A tutorial restart resolves exactly one TutorialRestartDef and is legal only for the interrupted Restart dialogue binding. Any other two-request combination fails. Each emitted request is deduplicated by `(runtime_generation, StoryActionListId, action_index)`; retrying a failed pre-publish list emits nothing, and replaying a completed list cannot duplicate an external request.

All suffix conditions are evaluated during prevalidation against the immutable prospective scratch-progress view, not the pre-action live view. Thus first-confrontation `FLAG_RUSK_CONFRONTATION_SEEN` is visible to `COND_TRANS_RUSK_START` before the action list publishes, while no other subsystem can observe it yet. The transition request stores the validated prospective-view generation/hash and COMMIT rejects any mismatch; it never reevaluates against partially published state. Runtime-only sources still come from their current typed owners. This rule applies uniformly and is not a Rusk special case.

Four dialogue-owned list rows and their eleven actions are locked at the start of the global action table:

```c
enum OpeningStoryActionListIdValue {
    ACTION_OREN_RELAY_QUEST_START = 0x4110,
    ACTION_RUSK_PRE_START_BATTLE = 0x4111,
    ACTION_RUSK_LATER_START_BATTLE = 0x4112,
    ACTION_RUSK_IMMEDIATE_START_ENCOUNTER = 0x4113,
    ACTION_JO_RELAY_UNLOCK = 0x4140,
    ACTION_SERA_RELAY_HANDOFF = 0x4141,
    ACTION_PELL_TRACE_DESTINATION = 0x4142
};

static const StoryAction OPENING_ACTION_PREFIX[11] = {
    { ACTION_SET_FLAG, STORY_ACTION_IDEMPOTENT,
      FLAG_FIELD_RELAY_QUEST_STARTED, 1, 0, 0 },
    { ACTION_ADVANCE_OBJECTIVE, 0,
      OBJ_RETRIEVE_FIELD_RELAY, 0x00000100, OBJ_RETRIEVE_FIELD_RELAY, 0 },
    { ACTION_SET_BOUNDED_QUEST_SUBSTAGE, 0,
      0, 0x00030100, 0, 0 },
    { ACTION_SET_FLAG, STORY_ACTION_IDEMPOTENT,
      FLAG_RUSK_CONFRONTATION_SEEN, 1, 0, 0 },
    { ACTION_CAPTURE_PRE_RUSK_SNAPSHOT, 0,
      ENCOUNTER_RUSK_COURTYARD, 0, 0, 0 },
    { ACTION_REQUEST_TRANSITION, STORY_ACTION_EXTERNAL_REQUEST,
      TRANS_DEF_RUSK_BATTLE_START, 0, 0, 0 },
    { ACTION_START_ENCOUNTER, STORY_ACTION_EXTERNAL_REQUEST,
      ENCOUNTER_RUSK_COURTYARD, 0, 0, 0 },
    { ACTION_CAPTURE_PRE_RUSK_SNAPSHOT, 0,
      ENCOUNTER_RUSK_COURTYARD, 0, 0, 0 },
    { ACTION_REQUEST_TRANSITION, STORY_ACTION_EXTERNAL_REQUEST,
      TRANS_DEF_RUSK_BATTLE_START, 0, 0, 0 },
    { ACTION_START_ENCOUNTER, STORY_ACTION_EXTERNAL_REQUEST,
      ENCOUNTER_RUSK_COURTYARD, 0, 0, 0 },
    { ACTION_START_ENCOUNTER, STORY_ACTION_EXTERNAL_REQUEST,
      ENCOUNTER_RUSK_COURTYARD, 0, 0, 0 }
};

static const StoryActionListDef OPENING_ACTION_LIST_PREFIX[4] = {
    { ACTION_OREN_RELAY_QUEST_START, 0, 3, 0,
      STORY_CONTEXT_DIALOGUE, STORY_LIST_ATOMIC_PROGRESS, 0 },
    { ACTION_RUSK_PRE_START_BATTLE, 3, 4, 2,
      STORY_CONTEXT_DIALOGUE, STORY_LIST_ATOMIC_PROGRESS, 0 },
    { ACTION_RUSK_LATER_START_BATTLE, 7, 3, 2,
      STORY_CONTEXT_DIALOGUE, STORY_LIST_ATOMIC_PROGRESS, 0 },
    { ACTION_RUSK_IMMEDIATE_START_ENCOUNTER, 10, 1, 1,
      STORY_CONTEXT_DIALOGUE, STORY_LIST_ATOMIC_PROGRESS, 0 }
};
```

Dismissal of `OREN_003` owns `ACTION_OREN_RELAY_QUEST_START`; therefore counter 0 changes `0->1`, the Relay-quest flag sets, and Retrieve Relay moves `LOCKED->ACTIVE` with itself as the sole active objective in one scratch transaction.

The three remaining Relay dialogue transactions occupy global action indices `15..26` and are literal:

```c
static const StoryAction RELAY_STORY_ACTIONS[12] = {
    { ACTION_SET_FLAG, STORY_ACTION_IDEMPOTENT + STORY_ACTION_APPLY_ON_SKIP,
      FLAG_FIELD_RELAY_UNLOCKED, 1, 0, 0 },
    { ACTION_SET_BOUNDED_QUEST_SUBSTAGE, 0,
      0, 0x00030201, 0, 0 },
    { ACTION_SET_RELAY_PAGE, STORY_ACTION_IDEMPOTENT + STORY_ACTION_APPLY_ON_SKIP,
      RELAY_PARTY_BIT, 1, 0, 0 },
    { ACTION_SET_RELAY_PAGE, STORY_ACTION_IDEMPOTENT + STORY_ACTION_APPLY_ON_SKIP,
      RELAY_MESSAGES_BIT, 1, 0, 0 },
    { ACTION_SET_RELAY_PAGE, STORY_ACTION_IDEMPOTENT + STORY_ACTION_APPLY_ON_SKIP,
      RELAY_RESONANCE_BIT, 1, 0, 0 },
    { ACTION_SET_RELAY_PAGE, STORY_ACTION_IDEMPOTENT + STORY_ACTION_APPLY_ON_SKIP,
      RELAY_MAP_BIT, 1, 0, 0 },

    { ACTION_SET_BOUNDED_QUEST_SUBSTAGE, 0,
      0, 0x00030302, 0, 0 },
    { ACTION_SET_FLAG, STORY_ACTION_IDEMPOTENT + STORY_ACTION_APPLY_ON_SKIP,
      FLAG_TAVI_MISSING_REPORTED, 1, 0, 0 },
    { ACTION_ADVANCE_OBJECTIVE, 0,
      OBJ_RETRIEVE_FIELD_RELAY, 0x00000201, OBJ_NONE, 0 },
    { ACTION_ADVANCE_OBJECTIVE, 0,
      OBJ_FIND_TAVI, 0x00000100, OBJ_FIND_TAVI, 0 },

    { ACTION_SET_FLAG, STORY_ACTION_IDEMPOTENT + STORY_ACTION_APPLY_ON_SKIP,
      FLAG_ESTATE_DESTINATION_UNLOCKED, 1, 0, 0 },
    { ACTION_UNLOCK_DESTINATION, STORY_ACTION_IDEMPOTENT + STORY_ACTION_APPLY_ON_SKIP,
      DESTINATION_ESTATE_BIT, 1, 0, 0 }
};

static const StoryActionListDef RELAY_STORY_ACTION_LISTS[3] = {
    { ACTION_JO_RELAY_UNLOCK, 15, 6, 0,
      STORY_CONTEXT_DIALOGUE, STORY_LIST_ATOMIC_PROGRESS, 0 },
    { ACTION_SERA_RELAY_HANDOFF, 21, 4, 0,
      STORY_CONTEXT_DIALOGUE, STORY_LIST_ATOMIC_PROGRESS, 0 },
    { ACTION_PELL_TRACE_DESTINATION, 25, 2, 0,
      STORY_CONTEXT_DIALOGUE, STORY_LIST_ATOMIC_PROGRESS, 0 }
};
```

`JO_RELAY_006`, `SERA_RELAY_002`, and `PELL_TRACE_004` bind respectively to those three lists. The Jo list compares counter 1 then publishes counter 2, unlock, and all four pages together. The Sera list compares 2 then publishes 3, the missing report, Retrieve `ACTIVE->COMPLETE`, and Find `LOCKED->ACTIVE` together. The Pell list publishes both the story flag and destination bit together. Intermediate scratch states are not validated or observable; the complete list is validated once against the final one-active-objective and Relay equivalences before publish.

The remaining mandatory opening action lists and their dense global action range `27..57` are fixed:

```c
typedef enum ChapterStoryActionListIdValue {
    ACTION_TUTORIAL_RESULT_ACCEPT = 0x4150,
    ACTION_ANNEX_INTRO_STARTERS = 0x4151,
    ACTION_ANNEX_INTRO_COMPLETE_SAVE = 0x4152,
    ACTION_FIELD_RELAY_CHECKPOINT = 0x4153,
    ACTION_TRACE_COMPLETE_CHECKPOINT = 0x4154,
    ACTION_RUSK_VICTORY_RESULT = 0x4155,
    ACTION_RUSK_DEFEAT_RESULT = 0x4156,
    ACTION_RUSK_DOOR_COMPLETE_SAVE = 0x4157,
    ACTION_REUNION_ENTER_FOUND = 0x4158,
    ACTION_REUNION_IVO_MET = 0x4159,
    ACTION_REUNION_RETURN_START_SAVE = 0x415A,
    ACTION_RETURN_OBJECTIVE_COMPLETE = 0x415B,
    ACTION_RETURN_COMPLETE_SAVE = 0x415C,
    ACTION_HOOK_BEGIN_OBJECTIVE = 0x415D,
    ACTION_HOOK_BEACON = 0x415E,
    ACTION_HOOK_FRACTURE = 0x415F,
    ACTION_HOOK_COMPLETE_SAVE = 0x4160
} ChapterStoryActionListIdValue;

typedef enum ChapterMilestoneRecipeIdValue {
    MILESTONE_AFTER_TUTORIAL = 1,
    MILESTONE_FIELD_RELAY = 2,
    MILESTONE_ANNEX_TRACE_COMPLETE = 3,
    MILESTONE_RUSK_VICTORY = 4,
    MILESTONE_TAVI_FOUND = 5,
    MILESTONE_TAVI_RETURNED = 6,
    MILESTONE_SLICE_COMPLETE = 7
} ChapterMilestoneRecipeIdValue;

typedef enum StoryRetentionSaveRecipeIdValue {
    RETENTION_SAVE_SERA_RUSK_RETURN_ONCE = 1
} StoryRetentionSaveRecipeIdValue;

static const StoryAction CHAPTER_STORY_ACTIONS[31] = {
    { ACTION_SET_FLAG, STORY_ACTION_IDEMPOTENT + STORY_ACTION_APPLY_ON_SKIP,
      FLAG_TUTORIAL_COMPLETE, 1, 0, 0 },
    { ACTION_REQUEST_TRANSITION, STORY_ACTION_EXTERNAL_REQUEST,
      TRANS_DEF_SIM_REVEAL, 0, 0, 0 },

    { ACTION_GRANT_PARTY, STORY_ACTION_IDEMPOTENT + STORY_ACTION_APPLY_ON_SKIP,
      TEAM_REAL_STARTERS, 0, 0, 0 },
    { ACTION_SET_FLAG, STORY_ACTION_IDEMPOTENT + STORY_ACTION_APPLY_ON_SKIP,
      FLAG_STARTER_TEAM_RECEIVED, 1, 0, 0 },

    { ACTION_SET_FLAG, STORY_ACTION_IDEMPOTENT + STORY_ACTION_APPLY_ON_SKIP,
      FLAG_ANNEX_INTRO_COMPLETE, 1, 0, 0 },
    { ACTION_REQUEST_SAVE, STORY_ACTION_EXTERNAL_REQUEST,
      MILESTONE_AFTER_TUTORIAL, 0, 0, 0 },
    { ACTION_REQUEST_SAVE, STORY_ACTION_EXTERNAL_REQUEST,
      MILESTONE_FIELD_RELAY, 0, 0, 0 },
    { ACTION_REQUEST_SAVE, STORY_ACTION_EXTERNAL_REQUEST,
      MILESTONE_ANNEX_TRACE_COMPLETE, 0, 0, 0 },

    { ACTION_SET_FLAG, STORY_ACTION_IDEMPOTENT + STORY_ACTION_APPLY_ON_SKIP,
      FLAG_RUSK_BATTLE_WON, 1, 0, 0 },
    { ACTION_GRANT_REWARD_ONCE, STORY_ACTION_IDEMPOTENT + STORY_ACTION_APPLY_ON_SKIP,
      REWARD_RUSK_FIRST_WIN, REWARD_RUSK_FIRST_WIN_BIT, ENCOUNTER_RUSK_COURTYARD, 0 },
    { ACTION_START_DIALOGUE, STORY_ACTION_EXTERNAL_REQUEST,
      RUSK_WIN_UI_001, 0, 0, 0 },
    { ACTION_START_DIALOGUE, STORY_ACTION_EXTERNAL_REQUEST,
      RUSK_LOSE_001, 0, 0, 0 },

    { ACTION_SET_FLAG, STORY_ACTION_IDEMPOTENT + STORY_ACTION_APPLY_ON_SKIP,
      FLAG_ESTATE_DOOR_OPEN, 1, 0, 0 },
    { ACTION_REQUEST_SAVE, STORY_ACTION_EXTERNAL_REQUEST,
      MILESTONE_RUSK_VICTORY, 0, 0, 0 },

    { ACTION_SET_FLAG, STORY_ACTION_IDEMPOTENT + STORY_ACTION_APPLY_ON_SKIP,
      FLAG_TAVI_FOUND, 1, 0, 0 },
    { ACTION_ADVANCE_OBJECTIVE, 0,
      OBJ_FIND_TAVI, 0x00000201, OBJ_NONE, 0 },
    { ACTION_SET_FLAG, STORY_ACTION_IDEMPOTENT + STORY_ACTION_APPLY_ON_SKIP,
      FLAG_IVO_MET, 1, 0, 0 },

    { ACTION_SET_FLAG, STORY_ACTION_IDEMPOTENT + STORY_ACTION_APPLY_ON_SKIP,
      FLAG_RETURN_TO_ANNEX_REQUESTED, 1, 0, 0 },
    { ACTION_ADVANCE_OBJECTIVE, 0,
      OBJ_RETURN_WITH_TAVI, 0x00000100, OBJ_RETURN_WITH_TAVI, 0 },
    { ACTION_REFRESH_DERIVED_FOLLOWER, STORY_ACTION_IDEMPOTENT + STORY_ACTION_APPLY_ON_SKIP,
      0, 0, 0, 0 },
    { ACTION_REQUEST_SAVE, STORY_ACTION_EXTERNAL_REQUEST,
      MILESTONE_TAVI_FOUND, 0, 0, 0 },

    { ACTION_SET_FLAG, STORY_ACTION_IDEMPOTENT + STORY_ACTION_APPLY_ON_SKIP,
      FLAG_TAVI_RETURNED_TO_ANNEX, 1, 0, 0 },
    { ACTION_ADVANCE_OBJECTIVE, 0,
      OBJ_RETURN_WITH_TAVI, 0x00000201, OBJ_NONE, 0 },
    { ACTION_REFRESH_DERIVED_FOLLOWER, STORY_ACTION_IDEMPOTENT + STORY_ACTION_APPLY_ON_SKIP,
      0, 0, 0, 0 },
    { ACTION_REQUEST_SAVE, STORY_ACTION_EXTERNAL_REQUEST,
      MILESTONE_TAVI_RETURNED, 0, 0, 0 },

    { ACTION_ADVANCE_OBJECTIVE, 0,
      OBJ_OPENING_COMPLETE, 0x00000100, OBJ_OPENING_COMPLETE, 0 },
    { ACTION_SET_FLAG, STORY_ACTION_IDEMPOTENT + STORY_ACTION_APPLY_ON_SKIP,
      FLAG_SOLACE_BEACON_RECEIVED, 1, 0, 0 },
    { ACTION_SET_FLAG, STORY_ACTION_IDEMPOTENT + STORY_ACTION_APPLY_ON_SKIP,
      FLAG_FRACTURE_SIGNAL_SEEN, 1, 0, 0 },

    { ACTION_SET_FLAG, STORY_ACTION_IDEMPOTENT + STORY_ACTION_APPLY_ON_SKIP,
      FLAG_SLICE_COMPLETE, 1, 0, 0 },
    { ACTION_ADVANCE_OBJECTIVE, 0,
      OBJ_OPENING_COMPLETE, 0x00000201, OBJ_NONE, 0 },
    { ACTION_REQUEST_SAVE, STORY_ACTION_EXTERNAL_REQUEST,
      MILESTONE_SLICE_COMPLETE, 0, 0, 0 }
};

static const StoryActionListDef CHAPTER_STORY_ACTION_LISTS[17] = {
    { ACTION_TUTORIAL_RESULT_ACCEPT, 27, 2, 1, STORY_CONTEXT_BATTLE_RESULT, STORY_LIST_ATOMIC_PROGRESS, 0 },
    { ACTION_ANNEX_INTRO_STARTERS, 29, 2, 0, STORY_CONTEXT_DIALOGUE, STORY_LIST_ATOMIC_PROGRESS, 0 },
    { ACTION_ANNEX_INTRO_COMPLETE_SAVE, 31, 2, 1, STORY_CONTEXT_DIALOGUE, STORY_LIST_ATOMIC_PROGRESS, 0 },
    { ACTION_FIELD_RELAY_CHECKPOINT, 33, 1, 1, STORY_CONTEXT_CHECKPOINT, STORY_LIST_ATOMIC_PROGRESS, 0 },
    { ACTION_TRACE_COMPLETE_CHECKPOINT, 34, 1, 1, STORY_CONTEXT_CHECKPOINT, STORY_LIST_ATOMIC_PROGRESS, 0 },
    { ACTION_RUSK_VICTORY_RESULT, 35, 3, 1, STORY_CONTEXT_BATTLE_RESULT, STORY_LIST_ATOMIC_PROGRESS, 0 },
    { ACTION_RUSK_DEFEAT_RESULT, 38, 1, 1, STORY_CONTEXT_BATTLE_RESULT, STORY_LIST_ATOMIC_PROGRESS, 0 },
    { ACTION_RUSK_DOOR_COMPLETE_SAVE, 39, 2, 1, STORY_CONTEXT_CHECKPOINT, STORY_LIST_ATOMIC_PROGRESS, 0 },
    { ACTION_REUNION_ENTER_FOUND, 41, 2, 0, STORY_CONTEXT_DIALOGUE, STORY_LIST_ATOMIC_PROGRESS, 0 },
    { ACTION_REUNION_IVO_MET, 43, 1, 0, STORY_CONTEXT_DIALOGUE, STORY_LIST_ATOMIC_PROGRESS, 0 },
    { ACTION_REUNION_RETURN_START_SAVE, 44, 4, 1, STORY_CONTEXT_DIALOGUE, STORY_LIST_ATOMIC_PROGRESS, 0 },
    { ACTION_RETURN_OBJECTIVE_COMPLETE, 48, 3, 0, STORY_CONTEXT_DIALOGUE, STORY_LIST_ATOMIC_PROGRESS, 0 },
    { ACTION_RETURN_COMPLETE_SAVE, 51, 1, 1, STORY_CONTEXT_DIALOGUE, STORY_LIST_ATOMIC_PROGRESS, 0 },
    { ACTION_HOOK_BEGIN_OBJECTIVE, 52, 1, 0, STORY_CONTEXT_CUTSCENE, STORY_LIST_ATOMIC_PROGRESS, 0 },
    { ACTION_HOOK_BEACON, 53, 1, 0, STORY_CONTEXT_DIALOGUE, STORY_LIST_ATOMIC_PROGRESS, 0 },
    { ACTION_HOOK_FRACTURE, 54, 1, 0, STORY_CONTEXT_DIALOGUE, STORY_LIST_ATOMIC_PROGRESS, 0 },
    { ACTION_HOOK_COMPLETE_SAVE, 55, 3, 1, STORY_CONTEXT_DIALOGUE, STORY_LIST_ATOMIC_PROGRESS, 0 }
};
```

The coherent Orrery commit is the sole mandatory action at global index 58:

```c
static const StoryAction ORRERY_COHERENT_ACTIONS[1] = {
    { ACTION_COMMIT_MECHANISM_WORLD_TXN,
      STORY_ACTION_IDEMPOTENT + STORY_ACTION_APPLY_ON_SKIP,
      INT_ORRERY_SWITCH, ACTION_ORRERY_COHERENT_OPEN_COMMIT, 0, 0 }
};

static const StoryActionListDef ORRERY_COHERENT_ACTION_LISTS[1] = {
    { ACTION_ORRERY_COHERENT_OPEN_COMMIT, 58, 1, 0,
      STORY_CONTEXT_INTERACTION, STORY_LIST_ATOMIC_PROGRESS, 0 }
};
```

Sera's post-Return one-shot retention write and the simulation handoff occupy global indices `59..60`:

```c
typedef enum SupplementalStoryActionListIdValue {
    ACTION_SERA_RUSK_RETURN_ONCE_SAVE = 0x4161,
    ACTION_SIM_TUTORIAL_START = 0x4162,
    ACTION_EXIT_OPEN_FIRST_SERA = 0x4163,
    ACTION_EXIT_OPEN_REPEAT_MAP = 0x4164,
    ACTION_TAVI_EXIT_CONTINUE_RETURN = 0x4165,
    ACTION_TAVI_EXIT_REPEAT_CONTINUE_RETURN = 0x4166,
    ACTION_SERA_DEPART_CONTINUE_MAP = 0x4167,
    ACTION_RUSK_POST_HEAL_AND_DOOR_BEGIN = 0x4168,
    ACTION_SIM_TUTORIAL_RESTART = 0x4169
} SupplementalStoryActionListIdValue;

static const StoryAction SUPPLEMENTAL_STORY_ACTIONS[10] = {
    { ACTION_REQUEST_RETENTION_SAVE, STORY_ACTION_EXTERNAL_REQUEST,
      RETENTION_SAVE_SERA_RUSK_RETURN_ONCE, 0, 0, 0 },
    { ACTION_ADVANCE_TUTORIAL_GATE, 0,
      TUTORIAL_SCRIPT_OPENING, 0x00000302, ENCOUNTER_SIM_TUTORIAL, 0 },
    { ACTION_START_DIALOGUE, STORY_ACTION_EXTERNAL_REQUEST,
      SERA_DEPART_001, 0, 0, 0 },
    { ACTION_REQUEST_TRANSITION, STORY_ACTION_EXTERNAL_REQUEST,
      TRANS_DEF_THRESHOLD_TO_MAP_REPEAT, 0, 0, 0 },
    { ACTION_REQUEST_TRANSITION, STORY_ACTION_EXTERNAL_REQUEST,
      TRANS_DEF_STUDY_RETURN_TO_MAP, 0, 0, 0 },
    { ACTION_REQUEST_TRANSITION, STORY_ACTION_EXTERNAL_REQUEST,
      TRANS_DEF_STUDY_RETURN_TO_MAP, 0, 0, 0 },
    { ACTION_REQUEST_TRANSITION, STORY_ACTION_EXTERNAL_REQUEST,
      TRANS_DEF_THRESHOLD_TO_MAP, 0, 0, 0 },
    { ACTION_RESTORE_PARTY_HP,
      STORY_ACTION_IDEMPOTENT + STORY_ACTION_APPLY_ON_SKIP,
      TEAM_REAL_STARTERS, 0, 0, 0 },
    { ACTION_START_WORLD_CALLBACK, STORY_ACTION_EXTERNAL_REQUEST,
      STORY_CALLBACK_RUSK_DOOR_ANIMATION_BEGIN, 0, 0, 0 },
    { ACTION_RESTART_TUTORIAL, STORY_ACTION_EXTERNAL_REQUEST,
      TUTORIAL_SCRIPT_OPENING, 0x53494D31, ENCOUNTER_SIM_TUTORIAL, 0 }
};

static const StoryActionListDef SUPPLEMENTAL_STORY_ACTION_LISTS[9] = {
    { ACTION_SERA_RUSK_RETURN_ONCE_SAVE, 59, 1, 1,
      STORY_CONTEXT_DIALOGUE, STORY_LIST_ATOMIC_PROGRESS, 0 },
    { ACTION_SIM_TUTORIAL_START, 60, 1, 0,
      STORY_CONTEXT_DIALOGUE, STORY_LIST_ATOMIC_PROGRESS, 0 },
    { ACTION_EXIT_OPEN_FIRST_SERA, 61, 1, 1,
      STORY_CONTEXT_DIALOGUE, STORY_LIST_ATOMIC_PROGRESS, 0 },
    { ACTION_EXIT_OPEN_REPEAT_MAP, 62, 1, 1,
      STORY_CONTEXT_DIALOGUE, STORY_LIST_ATOMIC_PROGRESS, 0 },
    { ACTION_TAVI_EXIT_CONTINUE_RETURN, 63, 1, 1,
      STORY_CONTEXT_DIALOGUE, STORY_LIST_ATOMIC_PROGRESS, 0 },
    { ACTION_TAVI_EXIT_REPEAT_CONTINUE_RETURN, 64, 1, 1,
      STORY_CONTEXT_DIALOGUE, STORY_LIST_ATOMIC_PROGRESS, 0 },
    { ACTION_SERA_DEPART_CONTINUE_MAP, 65, 1, 1,
      STORY_CONTEXT_DIALOGUE, STORY_LIST_ATOMIC_PROGRESS, 0 },
    { ACTION_RUSK_POST_HEAL_AND_DOOR_BEGIN, 66, 2, 1,
      STORY_CONTEXT_DIALOGUE, STORY_LIST_ATOMIC_PROGRESS, 0 },
    { ACTION_SIM_TUTORIAL_RESTART, 68, 1, 1,
      STORY_CONTEXT_DIALOGUE, STORY_LIST_ATOMIC_PROGRESS, 0 }
};
```

`ACTION_SIM_TUTORIAL_START` compares the already-live `TUTORIAL_SCRIPT_OPENING` owner from exact phase `TUTORIAL_RUNTIME_INTRO_DIALOGUE (2)` to `TUTORIAL_RUNTIME_GATE_1 (3)` and checks its encounter xref is exactly `ENCOUNTER_SIM_TUTORIAL`. It contains no external request and constructs nothing. The fly-in/bootstrap has already staged all four actors and nameplates before `SIM_001`; `SIM_002` dismissal merely publishes the gate phase once under the bound generations. Continue at `CHECKPOINT_AFTER_NAME` creates a fresh bootstrap/tutorial/dialogue generation and follows the same chain without double construction; no scene-enter scanner constructs an encounter, and a stale dismissal cannot advance the new owner. `ACTION_SIM_TUTORIAL_RESTART` is different: it is a terminal external request legal only from the exact interrupted Restart dismissal and must resolve the sole TutorialRestartDef before the old runtime is quiesced.

The global table order is therefore opening `0..10`, transition recipes `11..14`, Relay `15..26`, chapter `27..57`, Orrery commit `58`, and supplemental dialogue/tutorial handoffs `59..68`; generation asserts these exact ranges and rejects a textual count/index disagreement. `SupplementalStoryActionListIdValue` is part of the same named `StoryActionListId` collision domain as every other `*StoryActionListIdValue` enum; anonymous action-list enums are forbidden. The held begin/cancel callbacks are deliberately outside this table.

Mandatory owners bind through one typed table; controllers do not switch on dialogue names:

```c
typedef enum StoryTriggerOwnerKindValue {
    STORY_TRIGGER_OWNER_DIALOGUE = 1,
    STORY_TRIGGER_OWNER_ENCOUNTER = 2,
    STORY_TRIGGER_OWNER_WORLD_CALLBACK = 3,
    STORY_TRIGGER_OWNER_HOOK_SEQUENCE = 4,
    STORY_TRIGGER_OWNER_HELD_INTERACTION = 5,
    STORY_TRIGGER_OWNER_TRANSITION_RECIPE = 6
} StoryTriggerOwnerKindValue;

typedef enum StoryTriggerPhaseValue {
    STORY_TRIGGER_ENTER = 1,
    STORY_TRIGGER_DISMISS = 2,
    STORY_TRIGGER_RESULT_ACCEPT = 3,
    STORY_TRIGGER_VICTORY_COMMIT = 4,
    STORY_TRIGGER_DEFEAT_COMMIT = 5,
    STORY_TRIGGER_STABLE_AFTER_DISMISS = 6,
    STORY_TRIGGER_ANIMATION_COMPLETE = 7,
    STORY_TRIGGER_SEQUENCE_BEGIN = 8,
    STORY_TRIGGER_HELD_BEGIN = 9,
    STORY_TRIGGER_HELD_CANCEL = 10,
    STORY_TRIGGER_HELD_COMMIT = 11,
    STORY_TRIGGER_RECIPE_APPLY = 12
} StoryTriggerPhaseValue;

enum StoryTriggerBindingFlags {
    STORY_TRIGGER_EXACT_ONCE_PER_GENERATION = 1u << 0,
    STORY_TRIGGER_OWNER_CLOSE_BEFORE_EXTERNAL = 1u << 1,
    STORY_TRIGGER_REQUIRE_STABLE_AFTER_DISMISS = 1u << 2,
    STORY_TRIGGER_ENTER_BEFORE_FIRST_LINE = 1u << 3,
    STORY_TRIGGER_CONTROLLER_CALLBACK = 1u << 4,
    STORY_TRIGGER_GENERATION_BOUND = 1u << 5
};

typedef enum StoryControllerCallbackIdValue {
    STORY_CALLBACK_NONE = 0,
    STORY_CALLBACK_RUSK_DOOR_ANIMATION_BEGIN = 0x6701
} StoryControllerCallbackIdValue;

typedef enum StorySequenceIdValue {
    STORY_SEQUENCE_OPENING_HOOK = 0x6710
} StorySequenceIdValue;

typedef struct StoryTriggerBindingDef {
    uint8_t owner_kind;                  /* 0 */
    uint8_t phase;                       /* 1 */
    uint16_t owner_id;                   /* 2 */
    StoryActionListId action_list_id;    /* 4; exclusive with callback */
    uint16_t controller_callback_id;     /* 6 */
    ConditionId condition_id;            /* 8; zero means unconditional owner event */
    uint16_t flags;                      /* 10 */
    uint16_t reserved;                   /* 12 */
} StoryTriggerBindingDef;
_Static_assert(sizeof(StoryTriggerBindingDef) == 14, "StoryTriggerBindingDef layout");
```

The complete chapter-critical owner table is literal:

| owner kind / id | phase | action list or callback | condition | flags |
|---|---|---|---|---|
| `ENCOUNTER / ENCOUNTER_SIM_TUTORIAL` | `RESULT_ACCEPT` | `ACTION_TUTORIAL_RESULT_ACCEPT` | `0` | `EXACT_ONCE + OWNER_CLOSE_BEFORE_EXTERNAL + GENERATION_BOUND` |
| `DIALOGUE / ANNEX_INTRO_004` | `DISMISS` | `ACTION_ANNEX_INTRO_STARTERS` | `0` | `EXACT_ONCE + GENERATION_BOUND` |
| `DIALOGUE / ANNEX_INTRO_005` | `DISMISS` | `ACTION_ANNEX_INTRO_COMPLETE_SAVE` | `0` | `EXACT_ONCE + OWNER_CLOSE_BEFORE_EXTERNAL + GENERATION_BOUND` |
| `DIALOGUE / JO_RELAY_006` | `STABLE_AFTER_DISMISS` | `ACTION_FIELD_RELAY_CHECKPOINT` | `0` | `EXACT_ONCE + REQUIRE_STABLE_AFTER_DISMISS + GENERATION_BOUND` |
| `DIALOGUE / PELL_TRACE_004` | `STABLE_AFTER_DISMISS` | `ACTION_TRACE_COMPLETE_CHECKPOINT` | `0` | `EXACT_ONCE + REQUIRE_STABLE_AFTER_DISMISS + GENERATION_BOUND` |
| `ENCOUNTER / ENCOUNTER_RUSK_COURTYARD` | `VICTORY_COMMIT` | `ACTION_RUSK_VICTORY_RESULT` | `0` | `EXACT_ONCE + OWNER_CLOSE_BEFORE_EXTERNAL + GENERATION_BOUND` |
| `ENCOUNTER / ENCOUNTER_RUSK_COURTYARD` | `DEFEAT_COMMIT` | `ACTION_RUSK_DEFEAT_RESULT` | `0` | `EXACT_ONCE + OWNER_CLOSE_BEFORE_EXTERNAL + GENERATION_BOUND` |
| `WORLD_CALLBACK / STORY_CALLBACK_RUSK_DOOR_ANIMATION_BEGIN` | `ANIMATION_COMPLETE` | `ACTION_RUSK_DOOR_COMPLETE_SAVE` | `0` | `EXACT_ONCE + GENERATION_BOUND` |
| `DIALOGUE / REUNION_001` | `ENTER` | `ACTION_REUNION_ENTER_FOUND` | `0` | `EXACT_ONCE + ENTER_BEFORE_FIRST_LINE + GENERATION_BOUND` |
| `DIALOGUE / REUNION_004` | `DISMISS` | `ACTION_REUNION_IVO_MET` | `0` | `EXACT_ONCE + GENERATION_BOUND` |
| `DIALOGUE / REUNION_011` | `DISMISS` | `ACTION_REUNION_RETURN_START_SAVE` | `0` | `EXACT_ONCE + OWNER_CLOSE_BEFORE_EXTERNAL + GENERATION_BOUND` |
| `DIALOGUE / RETURN_005` | `DISMISS` | `ACTION_RETURN_OBJECTIVE_COMPLETE` | `0` | `EXACT_ONCE + GENERATION_BOUND` |
| `DIALOGUE / RETURN_007` | `DISMISS` | `ACTION_RETURN_COMPLETE_SAVE` | `0` | `EXACT_ONCE + OWNER_CLOSE_BEFORE_EXTERNAL + GENERATION_BOUND` |
| `HOOK_SEQUENCE / STORY_SEQUENCE_OPENING_HOOK` | `SEQUENCE_BEGIN` | `ACTION_HOOK_BEGIN_OBJECTIVE` | `0` | `EXACT_ONCE + GENERATION_BOUND` |
| `DIALOGUE / HOOK_005` | `DISMISS` | `ACTION_HOOK_BEACON` | `0` | `EXACT_ONCE + GENERATION_BOUND` |
| `DIALOGUE / HOOK_010` | `DISMISS` | `ACTION_HOOK_FRACTURE` | `0` | `EXACT_ONCE + GENERATION_BOUND` |
| `DIALOGUE / HOOK_014` | `DISMISS` | `ACTION_HOOK_COMPLETE_SAVE` | `0` | `EXACT_ONCE + OWNER_CLOSE_BEFORE_EXTERNAL + GENERATION_BOUND` |
| `DIALOGUE / RUSK_POST_005` | `DISMISS` | `ACTION_RUSK_POST_HEAL_AND_DOOR_BEGIN` | `0` | `EXACT_ONCE + OWNER_CLOSE_BEFORE_EXTERNAL + GENERATION_BOUND` |
| `DIALOGUE / SERA_RUSK_RETURN_001` | `DISMISS` | `ACTION_SERA_RUSK_RETURN_ONCE_SAVE` | `0` | `EXACT_ONCE + OWNER_CLOSE_BEFORE_EXTERNAL + GENERATION_BOUND` |
| `DIALOGUE / SIM_002` | `DISMISS` | `ACTION_SIM_TUTORIAL_START` | `0` | `EXACT_ONCE + GENERATION_BOUND` |
| `DIALOGUE / SIM_RESULT_RESTART` | `DISMISS` | `ACTION_SIM_TUTORIAL_RESTART` | `0` | `EXACT_ONCE + OWNER_CLOSE_BEFORE_EXTERNAL + GENERATION_BOUND` |
| `DIALOGUE / EXIT_READY_OPEN` | `ENTER` | `ACTION_EXIT_OPEN_FIRST_SERA` | `0` | `EXACT_ONCE + OWNER_CLOSE_BEFORE_EXTERNAL + ENTER_BEFORE_FIRST_LINE + GENERATION_BOUND` |
| `DIALOGUE / EXIT_READY_REPEAT_OPEN` | `ENTER` | `ACTION_EXIT_OPEN_REPEAT_MAP` | `0` | `EXACT_ONCE + OWNER_CLOSE_BEFORE_EXTERNAL + ENTER_BEFORE_FIRST_LINE + GENERATION_BOUND` |
| `DIALOGUE / SERA_DEPART_001` | `DISMISS` | `ACTION_SERA_DEPART_CONTINUE_MAP` | `0` | `EXACT_ONCE + OWNER_CLOSE_BEFORE_EXTERNAL + GENERATION_BOUND` |
| `DIALOGUE / TAVI_EXIT_001` | `DISMISS` | `ACTION_TAVI_EXIT_CONTINUE_RETURN` | `0` | `EXACT_ONCE + OWNER_CLOSE_BEFORE_EXTERNAL + GENERATION_BOUND` |
| `DIALOGUE / RETURN_SKIMMER_REPEAT_001` | `DISMISS` | `ACTION_TAVI_EXIT_REPEAT_CONTINUE_RETURN` | `0` | `EXACT_ONCE + OWNER_CLOSE_BEFORE_EXTERNAL + GENERATION_BOUND` |
| `DIALOGUE / OREN_003` | `DISMISS` | `ACTION_OREN_RELAY_QUEST_START` | `0` | `EXACT_ONCE + GENERATION_BOUND` |
| `DIALOGUE / JO_RELAY_006` | `DISMISS` | `ACTION_JO_RELAY_UNLOCK` | `0` | `EXACT_ONCE + GENERATION_BOUND` |
| `DIALOGUE / SERA_RELAY_002` | `DISMISS` | `ACTION_SERA_RELAY_HANDOFF` | `0` | `EXACT_ONCE + GENERATION_BOUND` |
| `DIALOGUE / PELL_TRACE_004` | `DISMISS` | `ACTION_PELL_TRACE_DESTINATION` | `0` | `EXACT_ONCE + GENERATION_BOUND` |
| `DIALOGUE / RUSK_PRE_005` | `DISMISS` | `ACTION_RUSK_PRE_START_BATTLE` | `0` | `EXACT_ONCE + OWNER_CLOSE_BEFORE_EXTERNAL + GENERATION_BOUND` |
| `DIALOGUE / RUSK_RETRY_001` | `DISMISS` | `ACTION_RUSK_LATER_START_BATTLE` | `0` | `EXACT_ONCE + OWNER_CLOSE_BEFORE_EXTERNAL + GENERATION_BOUND` |
| `DIALOGUE / RUSK_RETRY_IMMEDIATE_001` | `DISMISS` | `ACTION_RUSK_IMMEDIATE_START_ENCOUNTER` | `0` | `EXACT_ONCE + OWNER_CLOSE_BEFORE_EXTERNAL + GENERATION_BOUND` |
| `HELD_INTERACTION / INT_ORRERY_SWITCH` | `HELD_BEGIN` | `HELD_CALLBACK_ORRERY_BEGIN` | `COND_INTERACT_ORRERY_CLOSED` | `CONTROLLER_CALLBACK + GENERATION_BOUND` |
| `HELD_INTERACTION / INT_ORRERY_SWITCH` | `HELD_CANCEL` | `HELD_CALLBACK_ORRERY_CANCEL_RESET` | `0` | `CONTROLLER_CALLBACK + GENERATION_BOUND` |
| `HELD_INTERACTION / INT_ORRERY_SWITCH` | `HELD_COMMIT` | `ACTION_ORRERY_COHERENT_OPEN_COMMIT` | `COND_INTERACT_ORRERY_CLOSED` | `EXACT_ONCE + GENERATION_BOUND` |
| `TRANSITION_RECIPE / TRANS_RECIPE_NAME_INITIALIZE` | `RECIPE_APPLY` | `ACTION_TRANS_AFTER_NAME` | `0` | `EXACT_ONCE + GENERATION_BOUND` |
| `TRANSITION_RECIPE / TRANS_RECIPE_ANNEX_DEPARTURE` | `RECIPE_APPLY` | `ACTION_TRANS_ANNEX_DEPARTURE` | `0` | `EXACT_ONCE + GENERATION_BOUND` |
| `TRANSITION_RECIPE / TRANS_RECIPE_ESTATE_ARRIVAL` | `RECIPE_APPLY` | `ACTION_TRANS_ESTATE_ARRIVAL` | `0` | `EXACT_ONCE + GENERATION_BOUND` |
| `TRANSITION_RECIPE / TRANS_RECIPE_RUSK_RETURN_ANNEX` | `RECIPE_APPLY` | `ACTION_TRANS_RUSK_RETURN_ANNEX` | `0` | `EXACT_ONCE + GENERATION_BOUND` |

The authoring-table aliases map exactly as follows and are expanded before the emitted C row is byte-compared. Owner aliases `DIALOGUE`, `ENCOUNTER`, `WORLD_CALLBACK`, `HOOK_SEQUENCE`, `HELD_INTERACTION`, and `TRANSITION_RECIPE` map one-for-one to the same-suffix `STORY_TRIGGER_OWNER_*` values. Phase aliases are explicitly `ENTER=STORY_TRIGGER_ENTER`, `DISMISS=STORY_TRIGGER_DISMISS`, `RESULT_ACCEPT=STORY_TRIGGER_RESULT_ACCEPT`, `VICTORY_COMMIT=STORY_TRIGGER_VICTORY_COMMIT`, `DEFEAT_COMMIT=STORY_TRIGGER_DEFEAT_COMMIT`, `STABLE_AFTER_DISMISS=STORY_TRIGGER_STABLE_AFTER_DISMISS`, `ANIMATION_COMPLETE=STORY_TRIGGER_ANIMATION_COMPLETE`, `SEQUENCE_BEGIN=STORY_TRIGGER_SEQUENCE_BEGIN`, `HELD_BEGIN=STORY_TRIGGER_HELD_BEGIN`, `HELD_CANCEL=STORY_TRIGGER_HELD_CANCEL`, `HELD_COMMIT=STORY_TRIGGER_HELD_COMMIT`, and `RECIPE_APPLY=STORY_TRIGGER_RECIPE_APPLY`. Flag aliases `EXACT_ONCE`, `OWNER_CLOSE_BEFORE_EXTERNAL`, `REQUIRE_STABLE_AFTER_DISMISS`, `ENTER_BEFORE_FIRST_LINE`, `CONTROLLER_CALLBACK`, and `GENERATION_BOUND` map one-for-one to same-suffix `STORY_TRIGGER_*` bits. No other shorthand exists. `(owner_kind,owner_id,phase)` is unique. First and repeat exit routing use distinct literal choice-target owner IDs, so no condition is needed in dialogue context and each fixed transition suffix validates its own TransitionDef under `TransitionConditionView`. Exactly one of action list or callback is nonzero, and each resolves in its typed registry. Every nonzero mandatory action list has exactly one primary owner row; the two post-dismiss stable checkpoint rows are deliberate second phases of their dialogue owners. All rows are generation-bound before dispatch, and any stale/duplicate event is ignored without applying progress. The Rusk-door begin callback stages the authored door animation and a same-generation completion token; failure leaves the door closed and offers Retry, while only its completion row may set the flag and request the milestone save.

`StoryTriggerBindingDef` is the sole StoryAction dispatcher in the executable. Every other owner field renamed `*_xref` is an equality-only generated mirror: `DialogueNode`, `InteractionDef`/`InteractionVariantDef`, `HeldInteractionDef`, `MechanismWorldTransactionDef`, `ObjectiveDef`, `CutsceneDef`/story events, `EncounterDef`, `BattleState`, `BattleDefeatFlowDef`, and `TransitionStoryRecipeDef` may expose the expected list for validation/debugging but never call it. On load/generation, each nonzero xref must equal exactly one compatible trigger row; zero means no action. Encounter resolution emits one VICTORY/DEFEAT trigger; it does not invoke EncounterDef or BattleState xrefs. Dialogue emits one selected ENTER/DISMISS trigger; it does not invoke its node xref. Held/transition owners follow the same rule. A direct invocation outside StoryTrigger is a certification failure, preventing exact-once keys from being bypassed or lists from double-dispatching.

Context admission is generated from owner plus phase, never guessed from an ID: every dialogue ENTER/DISMISS row, including `HOOK_005`, `HOOK_010`, and `HOOK_014`, maps to `STORY_CONTEXT_DIALOGUE`; dialogue STABLE_AFTER_DISMISS and world ANIMATION_COMPLETE map to `STORY_CONTEXT_CHECKPOINT`; encounter phases map to `STORY_CONTEXT_BATTLE_RESULT`; hook-sequence BEGIN maps to `STORY_CONTEXT_CUTSCENE`; held phases map to `STORY_CONTEXT_INTERACTION`; transition-recipe apply maps to `STORY_CONTEXT_TRANSITION`. A list's context must contain that exact bit and no caller may widen it at runtime.

Upstream story starts are themselves typed:

```c
typedef enum StoryStartSourceKindValue {
    STORY_START_SOURCE_TRANSITION_COMMIT = 1,
    STORY_START_SOURCE_MILESTONE_SAVE_RESOLVED = 2,
    STORY_START_SOURCE_SCENE_ENTER = 3,
    STORY_START_SOURCE_WORLD_VOLUME_ENTER = 4,
    STORY_START_SOURCE_STABLE_POST_REVEAL = 5,
    STORY_START_SOURCE_CONTINUE_LOADED_STABLE = 6,
    STORY_START_SOURCE_INTERACTION_ACCEPT = 7,
    STORY_START_SOURCE_TUTORIAL_INTRO_COMPLETE = 8
} StoryStartSourceKindValue;

typedef enum StoryStartTargetKindValue {
    STORY_START_TARGET_DIALOGUE = 1,
    STORY_START_TARGET_HOOK_SEQUENCE = 2
} StoryStartTargetKindValue;

typedef enum StoryStartPreconditionIdValue {
    STORY_PRECOND_SIM_TUTORIAL_READY = 0x6520,
    STORY_PRECOND_ANNEX_INTRO_READY = 0x6521,
    STORY_PRECOND_REUNION_STUDY_READY = 0x6522,
    STORY_PRECOND_RETURN_ATRIUM_READY = 0x6523,
    STORY_PRECOND_HOOK_READY = 0x6524,
    STORY_PRECOND_RUSK_RETURN_LINE_READY = 0x6525,
    STORY_PRECOND_RUSK_FIRST_CONFRONTATION = 0x6526,
    STORY_PRECOND_RUSK_LATER_CONFRONTATION = 0x6527,
    STORY_PRECOND_OREN_ASSIGNMENT_READY = 0x6528,
    STORY_PRECOND_JO_RELAY_READY = 0x6529,
    STORY_PRECOND_PELL_TRACE_READY = 0x652A,
    STORY_PRECOND_RUSK_FOYER_ENTRY_READY = 0x652B
} StoryStartPreconditionIdValue;

enum StoryStartEdgeFlags {
    STORY_START_EXACT_ONCE_PER_GENERATION = 1u << 0,
    STORY_START_REQUIRE_DESTINATION_COHERENT = 1u << 1,
    STORY_START_ENTER_BEFORE_PLAYER_CONTROL = 1u << 2,
    STORY_START_USE_ONCE_REGISTRY = 1u << 3,
    STORY_START_AFTER_STABLE_REVEAL = 1u << 4,
    STORY_START_AFTER_RESERVED_OWNER_CLOSE = 1u << 5,
    STORY_START_AFTER_POST_RECIPE_OUTCOME = 1u << 6
};

enum StoryStartActorBits {
    STORY_ACTOR_PLAYER = 1u << 0,
    STORY_ACTOR_TAVI = 1u << 1,
    STORY_ACTOR_IVO = 1u << 2,
    STORY_ACTOR_SERA = 1u << 3,
    STORY_ACTOR_MARA = 1u << 4,
    STORY_ACTOR_RUSK = 1u << 5,
    STORY_ACTOR_QUARRUNE = 1u << 6,
    STORY_ACTOR_AYSELOR = 1u << 7,
    STORY_ACTOR_OREN = 1u << 8,
    STORY_ACTOR_JO = 1u << 9,
    STORY_ACTOR_PELL = 1u << 10
};

enum StoryStartResourceBits {
    STORY_START_RESOURCE_ACTORS = 1u << 0,
    STORY_START_RESOURCE_SPAWNS = 1u << 1,
    STORY_START_RESOURCE_NAV = 1u << 2,
    STORY_START_RESOURCE_DIALOGUE = 1u << 3,
    STORY_START_RESOURCE_FOLLOWER_HANDOFF = 1u << 4
};

enum StoryStartOnceRegistryKindValue {
    STORY_START_ONCE_NONE = 0,
    STORY_START_ONCE_DIALOGUE = 1
};

enum StoryStartPreconditionFlags {
    STORY_PRECOND_REQUIRE_EXACT_LOCATION = 1u << 0,
    STORY_PRECOND_REQUIRE_CHECKPOINT = 1u << 1,
    STORY_PRECOND_REQUIRE_OBJECTIVE = 1u << 2,
    STORY_PRECOND_REQUIRE_RESOURCES = 1u << 3,
    STORY_PRECOND_REQUIRE_STABLE_CONTROL = 1u << 4
};

typedef struct StoryStartPreconditionDef {
    uint16_t id;                         /* 0 */
    SceneId scene_id;                    /* 2 */
    ZoneId zone_id;                      /* 4 */
    uint16_t reserved0;                  /* 6 */
    uint32_t required_story_flags;       /* 8: locked bits 0..22 */
    uint32_t forbidden_story_flags;      /* 12 */
    CheckpointId checkpoint_id;          /* 16; zero means no checkpoint test */
    ObjectiveId objective_id;            /* 18; zero means no objective test */
    uint16_t required_actor_mask;        /* 20 */
    uint8_t objective_state;             /* 22 */
    uint8_t required_resource_mask;      /* 23 */
    uint8_t once_registry_kind;          /* 24 */
    uint8_t once_bit_index;              /* 25; zero when NONE */
    uint8_t flags;                       /* 26 */
    uint8_t reserved1;                   /* 27 */
    uint32_t reserved2;                  /* 28: explicit tail capacity */
} StoryStartPreconditionDef;
_Static_assert(sizeof(StoryStartPreconditionDef) == 32, "StoryStartPreconditionDef layout");

typedef struct StoryStartEdgeDef {
    uint8_t source_kind;        /* 0 */
    uint8_t target_kind;        /* 1 */
    uint16_t source_id;         /* 2: typed by source_kind */
    uint16_t target_id;         /* 4: DialogueId or StorySequenceId */
    uint16_t precondition_id;   /* 6: StoryStartPreconditionIdValue */
    uint16_t flags;             /* 8 */
    uint16_t reserved;          /* 10 */
} StoryStartEdgeDef;
_Static_assert(sizeof(StoryStartEdgeDef) == 12, "StoryStartEdgeDef layout");

enum StorySequenceFlags {
    STORY_SEQUENCE_OWNS_CONTROL = 1u << 0,
    STORY_SEQUENCE_NO_REPLAY_AFTER_COMPLETE = 1u << 1
};

typedef struct StorySequenceDef {
    uint16_t id;                /* 0 */
    DialogueId root_dialogue_id;/* 2 */
    uint16_t flags;             /* 4 */
    uint16_t reserved;          /* 6 */
} StorySequenceDef;
_Static_assert(sizeof(StorySequenceDef) == 8, "StorySequenceDef layout");

enum StoryResolutionVolumeFlags {
    STORY_VOLUME_REQUIRE_PLAYER_ENTER = 1u << 0,
    STORY_VOLUME_REQUIRE_FOLLOWER_ENTER = 1u << 1,
    STORY_VOLUME_REQUIRE_STABLE_CONTROL = 1u << 2,
    STORY_VOLUME_DEBOUNCE_ONE_FRAME = 1u << 3,
    STORY_VOLUME_NO_TELEPORT_ACQUISITION = 1u << 4
};

typedef struct StoryResolutionVolumeDef {
    InteractionId interaction_id;  /* 0: WORLD_VOLUME_ENTER source */
    SceneId scene_id;              /* 2 */
    ZoneId zone_id;                /* 4 */
    uint16_t entry_dwell_ticks;    /* 6: fixed 30 Hz */
    uint16_t authored_walk_min_ticks; /* 8: evidence bound */
    uint16_t authored_walk_max_ticks; /* 10 */
    uint16_t required_actor_mask;  /* 12 */
    uint16_t flags;                /* 14 */
    uint16_t reserved;             /* 16 */
} StoryResolutionVolumeDef;
_Static_assert(sizeof(StoryResolutionVolumeDef) == 18, "StoryResolutionVolumeDef layout");
```

The sole sequence row is `{ STORY_SEQUENCE_OPENING_HOOK, HOOK_001, STORY_SEQUENCE_OWNS_CONTROL + STORY_SEQUENCE_NO_REPLAY_AFTER_COMPLETE, 0 }`; HookController resolves this row and never hard-codes its root.

The sole resolution-volume row is `{ INT_ANNEX_RETURN_RESOLUTION_VOLUME, SCENE_ANNEX_INTERIOR, ZONE_ANNEX_ATRIUM, 2, 600, 1350, STORY_ACTOR_PLAYER + STORY_ACTOR_TAVI, STORY_VOLUME_REQUIRE_PLAYER_ENTER + STORY_VOLUME_REQUIRE_FOLLOWER_ENTER + STORY_VOLUME_REQUIRE_STABLE_CONTROL + STORY_VOLUME_DEBOUNCE_ONE_FRAME + STORY_VOLUME_NO_TELEPORT_ACQUISITION, 0 }`. Its authored collision/nav path begins at `SPAWN_ANNEX_THRESHOLD_DEPARTURE`, crosses the ordinary player-controlled threshold-to-atrium portal, and ends at the visible atrium resolution marker. Certification playback at normal walk speed must enter in `600..1350` active gameplay ticks (20–45 seconds); run speed may be faster but cannot fire before both player and derived Tavi follower physically overlap the volume for two stable ticks. The transition to Atrium releases player control normally and owns no RETURN dialogue. Reboot at `CHECKPOINT_TAVI_FOUND` or the return route resumes at a legal stable location from which the same walk/volume remains reachable. A teleport, scene-enter scan, portal COMMIT start, missing follower overlap, stale follower generation, or out-of-range measured walk fails the story reachability gate.

The typed precondition rows are exact. `BIT(F)` below means `1u << F` and is legal because every referenced locked flag index is below 32:

| PreconditionId | exact Scene / Zone | required / forbidden story flags | checkpoint | objective/state | actors / resources | once kind/bit | flags |
|---|---|---|---|---|---|---|---|
| `STORY_PRECOND_SIM_TUTORIAL_READY` | `SCENE_SIM_ARENA / ZONE_SIM_ARENA` | `BIT(FLAG_OPENING_CINEMATIC_SEEN)+BIT(FLAG_PLAYER_NAME_CONFIRMED) / BIT(FLAG_TUTORIAL_COMPLETE)` | `CHECKPOINT_AFTER_NAME` | `0 / 0` | `0 / STORY_START_RESOURCE_DIALOGUE` | `NONE / 0` | exact location + checkpoint + resources |
| `STORY_PRECOND_ANNEX_INTRO_READY` | `SCENE_ANNEX_INTERIOR / ZONE_ANNEX_SIMULATION_ROOM` | `BIT(FLAG_TUTORIAL_COMPLETE) / BIT(FLAG_ANNEX_INTRO_COMPLETE)+BIT(FLAG_STARTER_TEAM_RECEIVED)` | `CHECKPOINT_AFTER_NAME` | `0 / 0` | `SERA+MARA+QUARRUNE+AYSELOR / ACTORS+SPAWNS+NAV+DIALOGUE` | `NONE / 0` | exact location + checkpoint + resources |
| `STORY_PRECOND_REUNION_STUDY_READY` | `SCENE_ESTATE_INTERIOR / ZONE_ESTATE_OBSERVATORY_STUDY` | `BIT(FLAG_ORRERY_STAIR_OPEN) / BIT(FLAG_TAVI_FOUND)` | `0` | `OBJ_FIND_TAVI / OBJECTIVE_ACTIVE` | `TAVI+IVO / ACTORS+SPAWNS+NAV+DIALOGUE` | `NONE / 0` | exact location + objective + resources |
| `STORY_PRECOND_RETURN_ATRIUM_READY` | `SCENE_ANNEX_INTERIOR / ZONE_ANNEX_ATRIUM` | `BIT(FLAG_TAVI_FOUND)+BIT(FLAG_IVO_MET)+BIT(FLAG_RETURN_TO_ANNEX_REQUESTED) / BIT(FLAG_TAVI_RETURNED_TO_ANNEX)` | `0` | `OBJ_RETURN_WITH_TAVI / OBJECTIVE_ACTIVE` | `PLAYER+TAVI+SERA / ACTORS+SPAWNS+NAV+DIALOGUE+FOLLOWER_HANDOFF` | `NONE / 0` | exact location + objective + resources + stable control |
| `STORY_PRECOND_HOOK_READY` | `SCENE_ANNEX_INTERIOR / ZONE_ANNEX_ATRIUM` | `BIT(FLAG_TAVI_RETURNED_TO_ANNEX) / BIT(FLAG_SLICE_COMPLETE)` | `CHECKPOINT_TAVI_RETURNED` | `OBJ_OPENING_COMPLETE / OBJECTIVE_LOCKED` | `TAVI+SERA / ACTORS+DIALOGUE` | `NONE / 0` | exact location + checkpoint + objective + resources |
| `STORY_PRECOND_RUSK_RETURN_LINE_READY` | `SCENE_ANNEX_INTERIOR / ZONE_ANNEX_THRESHOLD` | `BIT(FLAG_ESTATE_ARRIVED)+BIT(FLAG_RUSK_CONFRONTATION_SEEN) / BIT(FLAG_RUSK_BATTLE_WON)` | `CHECKPOINT_RUSK_RETURN_TO_ANNEX` | `OBJ_FIND_TAVI / OBJECTIVE_ACTIVE` | `0 / DIALOGUE` | `DIALOGUE / 0` | exact location + checkpoint + objective + resources + stable |
| `STORY_PRECOND_RUSK_FIRST_CONFRONTATION` | `SCENE_ESTATE_COURTYARD / ZONE_ESTATE_COURTYARD` | `BIT(FLAG_ESTATE_ARRIVED) / BIT(FLAG_RUSK_CONFRONTATION_SEEN)+BIT(FLAG_RUSK_BATTLE_WON)` | `CHECKPOINT_ESTATE_ARRIVAL` | `OBJ_FIND_TAVI / OBJECTIVE_ACTIVE` | `RUSK / ACTORS+SPAWNS+NAV+DIALOGUE` | `NONE / 0` | exact location + checkpoint + objective + resources |
| `STORY_PRECOND_RUSK_LATER_CONFRONTATION` | `SCENE_ESTATE_COURTYARD / ZONE_ESTATE_COURTYARD` | `BIT(FLAG_ESTATE_ARRIVED)+BIT(FLAG_RUSK_CONFRONTATION_SEEN) / BIT(FLAG_RUSK_BATTLE_WON)` | `CHECKPOINT_RUSK_RETURN_TO_ANNEX` | `OBJ_FIND_TAVI / OBJECTIVE_ACTIVE` | `RUSK / ACTORS+SPAWNS+NAV+DIALOGUE` | `NONE / 0` | exact location + checkpoint + objective + resources |
| `STORY_PRECOND_OREN_ASSIGNMENT_READY` | `SCENE_ANNEX_INTERIOR / ZONE_ANNEX_DIRECTOR_LAB` | `BIT(FLAG_ANNEX_INTRO_COMPLETE)+BIT(FLAG_STARTER_TEAM_RECEIVED) / BIT(FLAG_FIELD_RELAY_QUEST_STARTED)` | `CHECKPOINT_AFTER_TUTORIAL` | `0 / 0` | `OREN / ACTORS+SPAWNS+NAV+DIALOGUE` | `NONE / 0` | exact location + checkpoint + resources |
| `STORY_PRECOND_JO_RELAY_READY` | `SCENE_ANNEX_INTERIOR / ZONE_ANNEX_WORKSHOP` | `BIT(FLAG_FIELD_RELAY_QUEST_STARTED) / BIT(FLAG_FIELD_RELAY_UNLOCKED)` | `0` | `OBJ_RETRIEVE_FIELD_RELAY / OBJECTIVE_ACTIVE` | `JO / ACTORS+SPAWNS+NAV+DIALOGUE` | `NONE / 0` | exact location + objective + resources |
| `STORY_PRECOND_PELL_TRACE_READY` | `SCENE_ANNEX_INTERIOR / ZONE_ANNEX_ATRIUM` | `BIT(FLAG_FIELD_RELAY_UNLOCKED) / BIT(FLAG_TAVI_MISSING_REPORTED)` | `CHECKPOINT_FIELD_RELAY` | `OBJ_RETRIEVE_FIELD_RELAY / OBJECTIVE_ACTIVE` | `PELL / ACTORS+SPAWNS+NAV+DIALOGUE` | `NONE / 0` | exact location + checkpoint + objective + resources |
| `STORY_PRECOND_RUSK_FOYER_ENTRY_READY` | `SCENE_ESTATE_INTERIOR / ZONE_ESTATE_FOYER` | `BIT(FLAG_RUSK_BATTLE_WON)+BIT(FLAG_ESTATE_DOOR_OPEN) / 0` | `CHECKPOINT_RUSK_VICTORY` | `OBJ_FIND_TAVI / OBJECTIVE_ACTIVE` | `RUSK / ACTORS+SPAWNS+NAV+DIALOGUE` | `DIALOGUE / 8` | exact location + checkpoint + objective + resources |

The display aliases in this table expand exactly to `STORY_ACTOR_*`, `STORY_START_RESOURCE_*`, `STORY_START_ONCE_*`, and `STORY_PRECOND_*` constants; emitted rows contain the full expressions and zero both reserved fields.

| source | target | precondition | flags |
|---|---|---|---|
| `STORY_START_SOURCE_TUTORIAL_INTRO_COMPLETE / TUTORIAL_SCRIPT_OPENING` | `STORY_START_TARGET_DIALOGUE / SIM_001` | `STORY_PRECOND_SIM_TUTORIAL_READY` | `STORY_START_EXACT_ONCE_PER_GENERATION + STORY_START_REQUIRE_DESTINATION_COHERENT + STORY_START_ENTER_BEFORE_PLAYER_CONTROL` |
| `STORY_START_SOURCE_CONTINUE_LOADED_STABLE / CHECKPOINT_AFTER_NAME` | `STORY_START_TARGET_DIALOGUE / SIM_001` | `STORY_PRECOND_SIM_TUTORIAL_READY` | `STORY_START_EXACT_ONCE_PER_GENERATION + STORY_START_REQUIRE_DESTINATION_COHERENT + STORY_START_ENTER_BEFORE_PLAYER_CONTROL + STORY_START_AFTER_STABLE_REVEAL` |
| `STORY_START_SOURCE_TRANSITION_COMMIT / TRANS_DEF_SIM_REVEAL` | `STORY_START_TARGET_DIALOGUE / ANNEX_INTRO_001` | `STORY_PRECOND_ANNEX_INTRO_READY` | `STORY_START_EXACT_ONCE_PER_GENERATION + STORY_START_REQUIRE_DESTINATION_COHERENT + STORY_START_ENTER_BEFORE_PLAYER_CONTROL` |
| `STORY_START_SOURCE_WORLD_VOLUME_ENTER / INT_RUSK_CONFRONTATION_VOLUME` | `STORY_START_TARGET_DIALOGUE / RUSK_PRE_001` | `STORY_PRECOND_RUSK_FIRST_CONFRONTATION` | `STORY_START_EXACT_ONCE_PER_GENERATION + STORY_START_REQUIRE_DESTINATION_COHERENT` |
| `STORY_START_SOURCE_TRANSITION_COMMIT / TRANS_DEF_MAP_RESELECT_ESTATE` | `STORY_START_TARGET_DIALOGUE / RUSK_RETRY_001` | `STORY_PRECOND_RUSK_LATER_CONFRONTATION` | `STORY_START_EXACT_ONCE_PER_GENERATION + STORY_START_REQUIRE_DESTINATION_COHERENT + STORY_START_ENTER_BEFORE_PLAYER_CONTROL` |
| `STORY_START_SOURCE_INTERACTION_ACCEPT / INT_NPC_OREN` | `STORY_START_TARGET_DIALOGUE / OREN_001` | `STORY_PRECOND_OREN_ASSIGNMENT_READY` | `STORY_START_EXACT_ONCE_PER_GENERATION + STORY_START_REQUIRE_DESTINATION_COHERENT` |
| `STORY_START_SOURCE_INTERACTION_ACCEPT / INT_NPC_JO` | `STORY_START_TARGET_DIALOGUE / JO_RELAY_001` | `STORY_PRECOND_JO_RELAY_READY` | `STORY_START_EXACT_ONCE_PER_GENERATION + STORY_START_REQUIRE_DESTINATION_COHERENT` |
| `STORY_START_SOURCE_INTERACTION_ACCEPT / INT_NPC_PELL` | `STORY_START_TARGET_DIALOGUE / PELL_TRACE_001` | `STORY_PRECOND_PELL_TRACE_READY` | `STORY_START_EXACT_ONCE_PER_GENERATION + STORY_START_REQUIRE_DESTINATION_COHERENT` |
| `STORY_START_SOURCE_TRANSITION_COMMIT / TRANS_DEF_COURTYARD_TO_FOYER` | `STORY_START_TARGET_DIALOGUE / RUSK_ENTRY_001` | `STORY_PRECOND_RUSK_FOYER_ENTRY_READY` | `STORY_START_EXACT_ONCE_PER_GENERATION + STORY_START_REQUIRE_DESTINATION_COHERENT + STORY_START_ENTER_BEFORE_PLAYER_CONTROL + STORY_START_USE_ONCE_REGISTRY` |
| `STORY_START_SOURCE_TRANSITION_COMMIT / TRANS_DEF_HALL_TO_STUDY` | `STORY_START_TARGET_DIALOGUE / REUNION_001` | `STORY_PRECOND_REUNION_STUDY_READY` | `STORY_START_EXACT_ONCE_PER_GENERATION + STORY_START_REQUIRE_DESTINATION_COHERENT + STORY_START_ENTER_BEFORE_PLAYER_CONTROL` |
| `STORY_START_SOURCE_WORLD_VOLUME_ENTER / INT_ANNEX_RETURN_RESOLUTION_VOLUME` | `STORY_START_TARGET_DIALOGUE / RETURN_001` | `STORY_PRECOND_RETURN_ATRIUM_READY` | `STORY_START_EXACT_ONCE_PER_GENERATION + STORY_START_REQUIRE_DESTINATION_COHERENT` |
| `STORY_START_SOURCE_MILESTONE_SAVE_RESOLVED / MILESTONE_TAVI_RETURNED` | `STORY_START_TARGET_HOOK_SEQUENCE / STORY_SEQUENCE_OPENING_HOOK` | `STORY_PRECOND_HOOK_READY` | `STORY_START_EXACT_ONCE_PER_GENERATION + STORY_START_REQUIRE_DESTINATION_COHERENT + STORY_START_AFTER_RESERVED_OWNER_CLOSE` |
| `STORY_START_SOURCE_STABLE_POST_REVEAL / TRANS_DEF_RUSK_RETURN_ANNEX` | `STORY_START_TARGET_DIALOGUE / SERA_RUSK_RETURN_001` | `STORY_PRECOND_RUSK_RETURN_LINE_READY` | `STORY_START_EXACT_ONCE_PER_GENERATION + STORY_START_REQUIRE_DESTINATION_COHERENT + STORY_START_USE_ONCE_REGISTRY + STORY_START_AFTER_STABLE_REVEAL` |
| `STORY_START_SOURCE_CONTINUE_LOADED_STABLE / CHECKPOINT_TAVI_RETURNED` | `STORY_START_TARGET_HOOK_SEQUENCE / STORY_SEQUENCE_OPENING_HOOK` | `STORY_PRECOND_HOOK_READY` | `STORY_START_EXACT_ONCE_PER_GENERATION + STORY_START_REQUIRE_DESTINATION_COHERENT + STORY_START_AFTER_STABLE_REVEAL` |
| `STORY_START_SOURCE_CONTINUE_LOADED_STABLE / CHECKPOINT_RUSK_RETURN_TO_ANNEX` | `STORY_START_TARGET_DIALOGUE / SERA_RUSK_RETURN_001` | `STORY_PRECOND_RUSK_RETURN_LINE_READY` | `STORY_START_EXACT_ONCE_PER_GENERATION + STORY_START_REQUIRE_DESTINATION_COHERENT + STORY_START_USE_ONCE_REGISTRY + STORY_START_AFTER_STABLE_REVEAL` |
| `STORY_START_SOURCE_CONTINUE_LOADED_STABLE / CHECKPOINT_RUSK_VICTORY` | `STORY_START_TARGET_DIALOGUE / RUSK_ENTRY_001` | `STORY_PRECOND_RUSK_FOYER_ENTRY_READY` | `STORY_START_EXACT_ONCE_PER_GENERATION + STORY_START_REQUIRE_DESTINATION_COHERENT + STORY_START_USE_ONCE_REGISTRY + STORY_START_AFTER_STABLE_REVEAL` |

Start preconditions use this dedicated typed record, not ConditionVM sources, so actor/resource/once checks are not invented RPN operands. `REUNION_001` ENTER sets Tavi found before its first line only after staged Tavi/Ivo resources validate. `SIM_001` has two literal and mutually exclusive recovery-safe sources: live Name-to-Sim publishes Tutorial-Intro-Complete, while Continue at `CHECKPOINT_AFTER_NAME` delays its loaded-stable edge until the fresh typed bootstrap has constructed the encounter, staged all actors, and finished the same seven-second fly-in. The bootstrap records which source kind owns the generation and rejects dual publication, so neither edge can race initialized facts or double-construct actors. The Tavi-return milestone source is not the progress publish or owner close: it emits one generation-bound resolved token only after the exact request reaches terminal `COMMITTED` or the player explicitly accepts `CONTINUED_DIRTY`, the retained Return/save-failure owner releases, and no SaveService UI remains. Retry stays under that owner and emits nothing. The Hook therefore cannot overlap the Tavi checkpoint writer/failure UI or enqueue its final save behind an unresolved mandatory request. Stable-post-reveal and Continue-loaded sources supply stable-control proof; this makes the tutorial, Sera's Return line, and a rebooted pre-Hook checkpoint reachable without scene flag scans. Oren, Jo, and Pell roots are exact interaction-accept rows; the Pell root owns the chain through `SERA_RELAY_001/002`, so no separate Sera controller branch exists. Duplicate/revisit starts fail closed under the live generation plus once/flag state.

The source registry is exact: TRANSITION_COMMIT/STABLE_POST_REVEAL resolve TransitionId; MILESTONE_SAVE_RESOLVED resolves a ChapterMilestoneRecipeId plus exact terminal request generation/result and accepts only `COMMITTED` or `CONTINUED_DIRTY`; SCENE_ENTER resolves SceneId; WORLD_VOLUME_ENTER and INTERACTION_ACCEPT resolve InteractionId; CONTINUE_LOADED_STABLE resolves CheckpointId; TUTORIAL_INTRO_COMPLETE resolves TutorialScriptId. Target DIALOGUE resolves a registered dialogue root; target HOOK_SEQUENCE resolves StorySequenceDef. Edge keys `(source_kind,source_id,target_kind,target_id)` are unique and reserved is zero. Flags accept only `0x007F`: ENTER_BEFORE_PLAYER_CONTROL is legal only for transition/scene/CONTINUE_LOADED_STABLE/tutorial-intro sources, USE_ONCE only when the precondition names a live matching once row or conversation-terminal mapping, AFTER_STABLE_REVEAL only for stable/loaded sources, AFTER_RESERVED_OWNER_CLOSE only for milestone sources after terminal owner release, and AFTER_POST_RECIPE_OUTCOME only for a SAVE_AFTER_STORY transition. Every edge's precondition resolves exactly once.

Precondition masks accept only locked story bits `0..22` and required/forbidden intersection must be zero. Exact-location/checkpoint/objective/resource/stable flags require their corresponding fields/proof, while absent flags require those fields zero; objective zero requires state zero and nonzero requires a registered ObjectiveId plus legal state. Actor masks accept only `0x07FF`, resource masks only `0x1F`, and a nonzero actor mask requires ACTORS. Once kind NONE requires bit zero; DIALOGUE requires bit `0..63` resolving the exact live dialogue-once lock row selected by the target. All reserved fields are zero. Any field/flag/edge mismatch, missing resource, ambiguous edge, or stale generation fails closed before owner acquisition.

Rusk has three noninterchangeable owners. First confrontation dismissal `RUSK_PRE_005` uses `ACTION_RUSK_PRE_START_BATTLE`: it sets `FLAG_RUSK_CONFRONTATION_SEEN`, captures a fresh current-generation snapshot containing that scratch state/party HP, then requests BATTLE_START and its encounter continuation. A later Estate re-entry after Return-to-Annex or reboot shows `RUSK_RETRY_001` and uses `ACTION_RUSK_LATER_START_BATTLE`: confrontation is already durable, but it captures a new current-generation snapshot and again requests BATTLE_START. Defeat-menu Retry itself restores the existing snapshot, requests `TRANS_DEF_RUSK_BATTLE_RETRY`, and only after that transition commits shows `RUSK_RETRY_IMMEDIATE_001`; dismissal uses `ACTION_RUSK_IMMEDIATE_START_ENCOUNTER`, starting the encounter at the already-restored battle spawn without capturing or transitioning again. Return/teardown invalidates the old snapshot, so the later path cannot use BATTLE_RETRY. The controller never scans zero-trigger rows or starts an encounter merely because a condition is true; only these debounced owners (plus the explicit defeat-menu Retry transition) act.

`ACTION_SET_BOUNDED_QUEST_SUBSTAGE` uses `subject_id` as the `quest_counters[]` index and packs `expected_current`, `next`, and `maximum` in `value` bits `0..7`, `8..15`, and `16..23`; bits `24..31` and `aux_id` must be zero. It succeeds only when the current byte equals `expected_current`, `next == expected_current + 1`, and `next <= maximum`. For counter 0 the only generated steps are `0->1`, `1->2`, and `2->3` with maximum 3; repeat/stale/out-of-order action lists fail atomically. Thus `JO_RELAY_006` can set substage 2 in the same scratch transaction as Relay unlock/page bits, and `SERA_RELAY_002` can set substage 3 with the objective handoff.

Stable progress validates counter 0 by exact equivalence: value 0 iff none of quest-started, Relay-unlocked, Tavi-missing, or the four Relay page bits is set; value 1 iff quest-started is set, Relay-unlocked/Tavi-missing are clear, all pages are clear, and Retrieve is active on the Jo substage; value 2 iff quest-started and Relay-unlocked are set, Tavi-missing is clear, all four pages are set, and Retrieve remains active on the Pell substage; value 3 iff quest-started, Relay-unlocked, and Tavi-missing are set, all four pages are set, Retrieve is complete, and Find is active until its own completion. No other flag/objective/page combination is legal.

`ACTION_COMMIT_MECHANISM_WORLD_TXN` is legal only in an action list that resolves one `MechanismWorldTransactionDef`; `subject_id` equals its owner `InteractionId` and `value` equals its `action_list_xref`. It delegates the typed pose/collision/nav staging and no-fail publish described in section 2.2. The generic `ACTION_SET_FLAG` validator rejects `FLAG_ORRERY_STAIR_OPEN`, so no dialogue or repeated interaction can bypass that world commit.

`ACTION_REFRESH_DERIVED_FOLLOWER` writes no persistent boolean. Its prospective state and active-zone follower assets are validated and staged before the joint progress/world publish described above; the commit merely publishes that staged derived state and cannot fail afterward. `FLAG_TAVI_RETURNED_TO_ANNEX` is set by the ordinary monotonic flag opcode at `RETURN_005`.

## 9. Runtime progress and retry snapshot

The runtime `GameProgress` is field-oriented and pointer-free. `SaveData` is its persistent logical value, but it is still encoded field by field rather than copied to EEPROM:

```c
typedef struct LocationKey {
    SceneId scene_id; /* 0 */
    ZoneId zone_id;   /* 2 */
    SpawnId spawn_id; /* 4 */
} LocationKey;
_Static_assert(sizeof(LocationKey) == 6, "LocationKey layout");

typedef enum SaveReasonValue {
    SAVE_REASON_NONE = 0,
    SAVE_REASON_CHECKPOINT = 1,
    SAVE_REASON_MANUAL_RELAY = 2,
    SAVE_REASON_BATTLE_RESULT = 3,
    SAVE_REASON_FINAL_HOOK = 4,
    SAVE_REASON_TRANSITION = 5,
    SAVE_REASON_SETTINGS = 6
} SaveReasonValue;

typedef enum BattleResultValue {
    BATTLE_RESULT_NONE = 0,
    BATTLE_RESULT_WIN = 1,
    BATTLE_RESULT_DEFEAT = 2,
    BATTLE_RESULT_RETURN_TO_ANNEX = 3
} BattleResultValue;

typedef struct SaveData {
    char player_name[8];               /* 0: uppercase, not NUL-terminated */
    uint8_t player_name_length;        /* 8 */
    uint8_t initialized;               /* 9 */
    uint16_t reserved0;                /* 10 */
    LocationKey current_location;      /* 12 */
    LocationKey last_safe_location;    /* 18 */
    uint32_t playtime_seconds;         /* 24 */
    uint32_t campaign_seed;            /* 28 */
    StoryFlagSet story_flags;          /* 32 */
    uint8_t objective_states[8];       /* 48 */
    uint16_t destination_unlock_bits;  /* 56 */
    uint16_t relay_page_bits;          /* 58 */
    uint16_t reward_claim_bits;        /* 60 */
    uint16_t research_points;          /* 62 */
    uint8_t encounter_clear_bits[8];   /* 64 */
    uint8_t dialogue_once_bits[8];     /* 72 */
    uint8_t examine_bits[8];           /* 80 */
    uint8_t npc_once_bits[8];          /* 88 */
    GameSettings settings;             /* 96 */
    uint8_t party_count;               /* 104 */
    uint8_t active_left_index;         /* 105 */
    uint8_t active_right_index;        /* 106 */
    uint8_t team_link;                 /* 107 */
    PartySlot party[4];                /* 108 */
    uint8_t quest_counters[8];         /* 172 */
    CheckpointId checkpoint_id;        /* 180 */
    SaveReason last_save_reason;       /* 182 */
    BattleResult last_battle_result;   /* 183 */
    ObjectiveId active_objective_id;   /* 184 */
    EncounterId last_encounter_id;     /* 186 */
    uint16_t chapter_progression;      /* 188 */
} SaveData;
_Static_assert(sizeof(SaveData) == 192, "SaveData logical layout");

typedef struct GameProgress {
    SaveData saved;              /* 0 */
    uint32_t runtime_generation; /* 192: never serialized */
} GameProgress;
_Static_assert(sizeof(GameProgress) == 196, "GameProgress layout");

typedef struct GameProgressSnapshot {
    SaveData saved;                      /* 0: field-copied logical value */
    uint32_t captured_runtime_generation;/* 192 */
    uint32_t snapshot_generation;        /* 196: nonzero monotonic owner serial */
} GameProgressSnapshot;
_Static_assert(sizeof(GameProgressSnapshot) == 200, "GameProgressSnapshot layout");

typedef enum SaveRequestPhaseValue {
    SAVE_REQUEST_EMPTY = 0,
    SAVE_REQUEST_RESERVED = 1,
    SAVE_REQUEST_SNAPSHOT_READY = 2,
    SAVE_REQUEST_ADDRESS_READY = 3,
    SAVE_REQUEST_ENQUEUED = 4,
    SAVE_REQUEST_WRITING = 5,
    SAVE_REQUEST_VERIFYING = 6,
    SAVE_REQUEST_COMMITTED = 7,
    SAVE_REQUEST_FAILED = 8,
    SAVE_REQUEST_CANCELED = 9,
    SAVE_REQUEST_CONTINUED_DIRTY = 10,
    SAVE_REQUEST_TRAVELED_UNSAVED = 11,
    SAVE_REQUEST_ABORTED_TO_TITLE = 12
} SaveRequestPhaseValue;

typedef enum SaveJournalPageValue {
    SAVE_JOURNAL_PAGE_UNASSIGNED = 0,
    SAVE_JOURNAL_PAGE_A = 1,
    SAVE_JOURNAL_PAGE_B = 2
} SaveJournalPageValue;

typedef enum SaveRequestResultValue {
    SAVE_REQUEST_RESULT_NONE = 0,
    SAVE_REQUEST_RESULT_SUCCESS = 1,
    SAVE_REQUEST_RESULT_WRITE_FAILURE = 2,
    SAVE_REQUEST_RESULT_VERIFY_FAILURE = 3,
    SAVE_REQUEST_RESULT_CANCELED = 4,
    SAVE_REQUEST_RESULT_ADDRESS_CONFLICT = 5,
    SAVE_REQUEST_RESULT_CONTINUED_DIRTY = 6,
    SAVE_REQUEST_RESULT_TRAVELED_UNSAVED = 7,
    SAVE_REQUEST_RESULT_ABORTED_TO_TITLE = 8
} SaveRequestResultValue;

enum SaveRequestIdentityFlags {
    SAVE_REQUEST_ENCODED_IDENTITY_VERIFIED = 1u << 0,
    SAVE_REQUEST_PRIOR_SETTINGS_CAPTURED = 1u << 1,
    SAVE_REQUEST_RUNTIME_WAS_DIRTY = 1u << 2,
    SAVE_REQUEST_CANDIDATE_SLICE_COMPLETE = 1u << 3,
    SAVE_REQUEST_RETRY_USES_IMMUTABLE_BYTES = 1u << 4,
    SAVE_REQUEST_PRODUCER_ROUTE_RESOLVED = 1u << 5,
    SAVE_REQUEST_OVERWRITE_AUTHORITY_REQUIRED = 1u << 6
};

enum SaveRequestLifecycleFlags {
    SAVE_REQUEST_LIFECYCLE_QUEUE_SLOT_RESERVED = 1u << 0,
    SAVE_REQUEST_LIFECYCLE_ADDRESS_ASSIGNED = 1u << 1,
    SAVE_REQUEST_LIFECYCLE_WRITER_ACTIVE = 1u << 2,
    SAVE_REQUEST_LIFECYCLE_CANDIDATE_PUBLISHED = 1u << 3,
    SAVE_REQUEST_LIFECYCLE_UI_OWNER_PUBLISHED = 1u << 4,
    SAVE_REQUEST_LIFECYCLE_SETTINGS_RESTORED = 1u << 5,
    SAVE_REQUEST_LIFECYCLE_DIRTY_RECONCILED = 1u << 6,
    SAVE_REQUEST_LIFECYCLE_TERMINAL = 1u << 7
};

typedef struct SaveRequest {
    GameProgressSnapshot immutable_progress; /* 0: never changes after SNAPSHOT_READY */
    uint8_t encoded_payload[216];            /* 200: exact immutable EEPROM payload bytes */
    GameSettings prior_runtime_settings;     /* 416: meaningful only with PRIOR_SETTINGS_CAPTURED */
    uint32_t request_generation;             /* 424: nonzero save-service owner */
    uint32_t campaign_owner_generation;      /* 428: exact current runtime/draft campaign owner */
    uint32_t journal_write_plan_generation;  /* 432: NewGame plan for first page, else zero */
    uint32_t ui_owner_generation;            /* 436: zero until failure UI publishes */
    uint32_t candidate_settings_generation;  /* 440: zero for non-settings requests */
    uint32_t prior_settings_generation;      /* 444: zero unless prior settings captured */
    uint32_t attempt_generation;             /* 448: fresh nonzero value per write attempt */
    uint32_t address_assignment_generation;  /* 452: zero until sole-writer promotion */
    uint32_t encoded_payload_crc32;          /* 456: CRC of exact encoded_payload bytes */
    uint32_t anchor_sequence;                /* 460: zero is data when anchor_page is assigned */
    uint32_t target_sequence;                /* 464: assigned only at ADDRESS_READY */
    uint16_t producer_id;                    /* 468: domain selected by producer_kind */
    uint16_t owner_id_xref;                  /* 470: resolved ProcessUiOwnerIdValue */
    uint8_t anchor_page;                     /* 472: SaveJournalPageValue; UNASSIGNED allowed */
    uint8_t target_page;                     /* 473: A or B only after assignment */
    uint8_t producer_kind;                   /* 474: SaveFailureProducerKindValue */
    uint8_t source_kind;                     /* 475: SaveFailureSourceKindValue */
    uint8_t policy_id;                       /* 476: SaveFailureUiPolicyIdValue */
    uint8_t phase;                           /* 477: SaveRequestPhaseValue */
    uint8_t result;                          /* 478: SaveRequestResultValue */
    uint8_t prior_settings_valid;            /* 479: exact 0 or 1 */
    uint8_t prior_save_reason;               /* 480: SaveReasonValue for Settings Cancel */
    uint8_t prior_dirty_state;               /* 481: RuntimeDirtyStateValue */
    uint16_t identity_flags;                 /* 482: SaveRequestIdentityFlags */
    uint16_t lifecycle_flags;                /* 484: SaveRequestLifecycleFlags */
    uint16_t reserved0;                      /* 486: zero */
} SaveRequest;
_Static_assert(sizeof(SaveRequest) == 488, "SaveRequest layout");

typedef enum SaveQueuePriorityValue {
    SAVE_QUEUE_PRIORITY_USER_INITIATED = 1,
    SAVE_QUEUE_PRIORITY_MANDATORY_OWNER_BLOCKING = 2
} SaveQueuePriorityValue;

typedef enum SaveQueueAdmissionResultValue {
    SAVE_QUEUE_ADMISSION_RESERVED_ACTIVE = 1,
    SAVE_QUEUE_ADMISSION_RESERVED_SUCCESSOR = 2,
    SAVE_QUEUE_ADMISSION_BUSY_RETRY = 3
} SaveQueueAdmissionResultValue;

enum SaveQueueAdmissionFlags {
    SAVE_QUEUE_ADMISSION_GENERATION_BOUND = 1u << 0,
    SAVE_QUEUE_ADMISSION_NO_PROGRESS_PUBLISHED = 1u << 1,
    SAVE_QUEUE_ADMISSION_NOTIFY_OWNER = 1u << 2,
    SAVE_QUEUE_ADMISSION_RETRY_ON_SLOT_RELEASE = 1u << 3
};

typedef enum SaveQueueBusyBehaviorValue {
    SAVE_QUEUE_BUSY_RETRY_OWNER_TRANSACTION = 1,
    SAVE_QUEUE_BUSY_KEEP_USER_SCRATCH = 2
} SaveQueueBusyBehaviorValue;

enum SaveQueueAdmissionPolicyFlags {
    SAVE_QUEUE_POLICY_OWNER_BLOCKING = 1u << 0,
    SAVE_QUEUE_POLICY_RESERVE_BEFORE_PUBLISH = 1u << 1,
    SAVE_QUEUE_POLICY_ALLOW_SUCCESSOR = 1u << 2,
    SAVE_QUEUE_POLICY_REQUIRE_ACTIVE_QUIESCENT = 1u << 3,
    SAVE_QUEUE_POLICY_RETAIN_ORIGIN_UNTIL_TERMINAL = 1u << 4,
    SAVE_QUEUE_POLICY_BLOCK_SEMANTIC_TRANSACTIONS = 1u << 5
};

typedef struct SaveQueueAdmissionPolicyDef {
    uint8_t producer_kind;  /* 0: SaveFailureProducerKindValue */
    uint8_t priority;       /* 1: SaveQueuePriorityValue */
    uint16_t producer_id;   /* 2: domain selected by producer_kind */
    uint8_t busy_behavior;  /* 4: SaveQueueBusyBehaviorValue */
    uint8_t flags;          /* 5: SaveQueueAdmissionPolicyFlags */
    uint16_t reserved;      /* 6: zero */
} SaveQueueAdmissionPolicyDef;
_Static_assert(sizeof(SaveQueueAdmissionPolicyDef) == 8, "SaveQueueAdmissionPolicyDef layout");

typedef struct SaveQueueAdmissionToken {
    uint32_t admission_generation;        /* 0 */
    uint32_t runtime_generation;          /* 4 */
    uint32_t campaign_owner_generation;   /* 8: exact current runtime/draft owner */
    uint32_t request_generation;          /* 12: new request, zero when busy */
    uint16_t producer_id;                  /* 16 */
    uint8_t producer_kind;                 /* 18: SaveFailureProducerKindValue */
    uint8_t priority;                      /* 19: SaveQueuePriorityValue */
    uint8_t result;                        /* 20: SaveQueueAdmissionResultValue */
    uint8_t busy_behavior;                 /* 21: SaveQueueBusyBehaviorValue */
    uint16_t flags;                        /* 22 */
} SaveQueueAdmissionToken;
_Static_assert(sizeof(SaveQueueAdmissionToken) == 24, "SaveQueueAdmissionToken layout");

typedef enum RetrySeedPolicyValue {
    RETRY_SEED_POLICY_FIXED_ENCOUNTER_BASE = 1
} RetrySeedPolicyValue;

enum PreRuskSnapshotPayloadFlags {
    PRE_RUSK_PAYLOAD_CONFRONTATION_INCLUDED = 1u << 0,
    PRE_RUSK_PAYLOAD_REWARDS_CLEAR = 1u << 1,
    PRE_RUSK_PAYLOAD_PARTY_HP_EXACT = 1u << 2
};

typedef struct PreRuskBattleSnapshotPayload {
    GameProgressSnapshot progress; /* 0 */
    EncounterId encounter_id;      /* 200 */
    uint8_t retry_seed_policy;     /* 202 */
    uint8_t flags;                 /* 203 */
    uint32_t retry_seed;           /* 204 */
} PreRuskBattleSnapshotPayload;
_Static_assert(sizeof(PreRuskBattleSnapshotPayload) == 208, "PreRuskBattleSnapshotPayload layout");

typedef enum PreRuskSnapshotOwnerStateValue {
    PRE_RUSK_OWNER_EMPTY = 0,
    PRE_RUSK_OWNER_VALID = 1
} PreRuskSnapshotOwnerStateValue;

typedef struct PreRuskSnapshotOwner {
    PreRuskBattleSnapshotPayload payload; /* 0: immutable while valid */
    uint32_t bound_runtime_generation;    /* 208: may rebind after restore */
    uint8_t state;                        /* 212 */
    uint8_t reserved[3];                  /* 213 */
} PreRuskSnapshotOwner;
_Static_assert(sizeof(PreRuskSnapshotOwner) == 216, "PreRuskSnapshotOwner layout");

typedef struct BattleDefeatResultToken {
    uint32_t runtime_generation; /* 0 */
    uint32_t defeat_flow_generation; /* 4: post-battle overlay owner */
    uint32_t menu_generation;    /* 8: overlay instance */
    uint32_t input_event_epoch;  /* 12: accepted-edge epoch */
    EncounterId encounter_id;    /* 16 */
    uint16_t flags;              /* 18 */
} BattleDefeatResultToken;
_Static_assert(sizeof(BattleDefeatResultToken) == 20, "BattleDefeatResultToken layout");

typedef enum DefeatFlowOwnerStateValue {
    DEFEAT_FLOW_OWNER_EMPTY = 0,
    DEFEAT_FLOW_OWNER_CHOICES = 1,
    DEFEAT_FLOW_OWNER_HANDOFF_PENDING = 2
} DefeatFlowOwnerStateValue;

typedef struct DefeatFlowOwner {
    BattleDefeatResultToken token; /* 0: all-zero while empty */
    uint32_t next_defeat_flow_generation; /* 20: nonzero allocator serial */
    uint8_t state;                 /* 24 */
    uint8_t accepted_choice;       /* 25: zero until one epoch accepts */
    uint16_t reserved;             /* 26 */
} DefeatFlowOwner;
_Static_assert(sizeof(DefeatFlowOwner) == 28, "DefeatFlowOwner layout");

enum BattleDefeatResultTokenFlags {
    DEFEAT_TOKEN_SIMULATION_COMMITTED = 1u << 0,
    DEFEAT_TOKEN_PRESENTATION_QUIESCED = 1u << 1,
    DEFEAT_TOKEN_CHOICE_OWNER_ACTIVE = 1u << 2
};

typedef enum BattleDefeatChoiceValue {
    BATTLE_DEFEAT_CHOICE_RETRY = 1,
    BATTLE_DEFEAT_CHOICE_RETURN_TO_ANNEX = 2
} BattleDefeatChoiceValue;

typedef enum BattleDefeatRestorePhaseValue {
    BATTLE_DEFEAT_RESTORE_BEFORE_TRANSITION = 1,
    BATTLE_DEFEAT_RESTORE_IN_POST_RECIPE = 2
} BattleDefeatRestorePhaseValue;

typedef enum PreRuskRestoreMergePolicyValue {
    PRE_RUSK_RESTORE_STORY_PARTY_PRESERVE_RUNTIME = 1
} PreRuskRestoreMergePolicyValue;

enum BattleDefeatFlowFlags {
    DEFEAT_FLOW_REQUIRE_PRE_RUSK_SNAPSHOT = 1u << 0,
    DEFEAT_FLOW_TEARDOWN_BATTLE_BEFORE_REQUEST = 1u << 1,
    DEFEAT_FLOW_SHOW_DIALOGUE_ON_COMMIT = 1u << 2,
    DEFEAT_FLOW_INVALIDATE_SNAPSHOT_ON_COMMIT = 1u << 3,
    DEFEAT_FLOW_REBUILD_MENU_ON_ROLLBACK = 1u << 4,
    DEFEAT_FLOW_DESTROY_OWNER_AFTER_HANDOFF = 1u << 5
};

typedef struct BattleDefeatFlowDef {
    EncounterId encounter_id;               /* 0 */
    uint8_t choice;                          /* 2 */
    uint8_t restore_phase;                   /* 3 */
    uint8_t merge_policy;                    /* 4 */
    uint8_t reserved0;                       /* 5 */
    TransitionId transition_id;              /* 6 */
    DialogueId on_commit_dialogue_id;        /* 8 */
    StoryActionListId dialogue_dismiss_action_xref; /* 10 */
    uint16_t post_recipe_xref;               /* 12 */
    uint16_t rollback_continuation_id;       /* 14 */
    uint16_t flags;                          /* 16 */
} BattleDefeatFlowDef;
_Static_assert(sizeof(BattleDefeatFlowDef) == 18, "BattleDefeatFlowDef layout");

enum BattleDefeatRollbackContinuationIdValue {
    RUSK_DEFEAT_MENU_ROLLBACK = 1
};

enum BattleDefeatRollbackFlags {
    DEFEAT_ROLLBACK_REQUIRE_LIVE_SNAPSHOT = 1u << 0,
    DEFEAT_ROLLBACK_REQUIRE_RESULT_TOKEN = 1u << 1,
    DEFEAT_ROLLBACK_REBUILD_OVERLAY_AND_CHOICES = 1u << 2,
    DEFEAT_ROLLBACK_PRESERVE_RUNTIME_GENERATION = 1u << 3,
    DEFEAT_ROLLBACK_ADVANCE_MENU_AND_INPUT_EPOCH = 1u << 4
};

typedef struct BattleDefeatRollbackContinuationDef {
    uint16_t id;                    /* 0 */
    EncounterId encounter_id;      /* 2 */
    DialogueId choice_dialogue_id; /* 4 */
    uint16_t flags;                /* 6 */
    uint16_t reserved;             /* 8 */
} BattleDefeatRollbackContinuationDef;
_Static_assert(sizeof(BattleDefeatRollbackContinuationDef) == 10, "BattleDefeatRollbackContinuationDef layout");
```

The generated C header declares the `GameSettings` and `PartySlot` types documented below before `SaveData`; section order here follows the gameplay-to-storage explanation rather than C declaration order.

`SaveRequest` is the sole runtime consumer of the producer, source-route, policy,
and Process UI registries in section 13.2. One fixed two-slot queue permits one
active writer and one immutable-payload successor; no slot contains a pointer or
a mutable `GameProgress` view. Before `SNAPSHOT_READY`, the producer resolves
exactly one `SaveFailureProducerRouteDef`, its one source route, its one policy,
and its one DEFAULT Process UI owner, field-copies progress, emits and stores all
216 canonical payload bytes, calculates their CRC-32/ISO-HDLC, and reserves the
queue slot. The successor deliberately leaves attempt/address generations,
anchor/target pages, and both sequences zero/unassigned while another writer is
active. It never projects an uncommitted predecessor into journal ordering.

Queue admission is itself typed and occurs before any producer publishes story,
transition, settings, or owner-close state. There is deliberately no lossy
automatic/coalescible class: every live producer is either a mandatory
owner-blocking transaction or an explicit user request, and no immutable save
candidate is displaced. Every non-service producer must receive ACTIVE or
SUCCESSOR reservation before its no-fail publish. BUSY_RETRY returns with
`NO_PROGRESS_PUBLISHED`, retains the exact origin/control owner, and retries the
whole transaction on slot release. Manual Relay and Settings retain their
scratch surface and use USER_INITIATED; BUSY_RETRY disables Apply/Save and
co-renders the already-live `PROCESS_UI_OWNER_SAVE_SERVICE /
PROCESS_UI_STATE_SAVE_WRITING` binding with `UI_SAVING`. It never routes through
TRANSITION_FAILURE or its transition-busy copy. Slot release closes that status,
clears one poll frame, and reenables the action. No request or producer event is
silently dropped.

The exact admission policy row is captured into each admission token and is
re-resolved by producer kind/ID before `SaveRequest` construction. Name-to-Sim
is the sole ACTIVE_QUIESCENT producer: the Title/opening/name process must prove
the SaveService has no active request, successor, failed retained head, or
backend callback, then reserve the active slot and complete raw-page reread plus
address assignment before publishing initialized Sim progress. It can never
wait as a successor. Every other mandatory producer may reserve the successor.
Manual/Settings may reserve either slot, but after reservation their retained
origin blocks every semantic or save-producing transaction until COMMITTED or a
typed FAILED resolution; therefore no successor can capture candidate settings
that Cancel might later restore. Policy flags accept only `0x003F`, admission
flags only `0x000F`, and every reserved field is zero. Goldens cover empty/one/
two slots, active commit/fail/cancel/retry, mandatory and user BUSY_RETRY,
Name-to-Sim quiescence rejection, settings-candidate failure/Cancel, no
dependent successor, campaign-owner mismatch, and stale admission notices.

When and only when a request reaches the head as sole writer, promotion rereads
and validates both durable page envelopes, applies section 11.3 ordering, and
atomically fills a fresh nonzero address-assignment generation, anchor page/
sequence (or UNASSIGNED/zero when no envelope is valid), opposite target page,
and exact next sequence before entering `ADDRESS_READY`. The selected address
tuple is frozen across every attempt/retry for that request. The snapshot's
captured runtime/snapshot generations, exact 216 payload bytes and CRC, request
generation, campaign-owner and journal-plan generations, producer/source/policy/owner tuple, prior settings/generations,
prior-valid byte, and identity flags are immutable from SNAPSHOT_READY through
terminal release. Attempt generation changes only on a write attempt;
UI-owner generation changes only when failure UI publishes; address fields
change exactly once at promotion; lifecycle flags are monotonic. Identity flags
accept only `0x007F`, lifecycle flags only `0x00FF`, and both reserved fields are
zero.

The only successful phase prefix is `EMPTY -> RESERVED -> SNAPSHOT_READY ->
ADDRESS_READY -> ENQUEUED -> WRITING -> VERIFYING -> COMMITTED`; WRITE_FAILURE
and VERIFY_FAILURE use the same addressed prefix through WRITING/VERIFYING and
end at FAILED. Sole-writer promotion has one pre-address failure edge:
`SNAPSHOT_READY -> FAILED / ADDRESS_CONFLICT` while address generation, pages,
sequences, and attempt generation remain unassigned/zero and no EEPROM byte is
touched. An ordinary ADDRESS_CONFLICT Retry clears the result and returns to
SNAPSHOT_READY for a fresh durable reread. It does not retain or invent an
address, does not increment attempt generation, and cannot enter ENQUEUED until
promotion succeeds. Name-to-Sim detects this edge while its active-only request
and initialized progress are still unpublished; it terminally enters
ABORTED_TO_TITLE, releases the request/draft, reruns the Title loader, and
requires fresh confirmation. No other result is legal before ADDRESS_READY.

WRITE_FAILURE/VERIFY_FAILURE Retry is a separate exact path. It retains the
immutable snapshot, byte array, CRC, assigned address tuple, campaign and
producer/source/policy owners, and request generation, clears the result, and
returns FAILED -> ENQUEUED. The writer allocates the fresh nonzero
`attempt_generation` only on ENQUEUED -> WRITING. Thus a partial target can be
rewritten safely without confusing conflict retry with an addressed retry.
Cancel is legal only from FAILED under ALLOW_CANCEL and ends at CANCELED.
It sets result CANCELED and TERMINAL after its source-specific restoration or
discard succeeds. COMMITTED sets result SUCCESS and TERMINAL only after durable
reread verification and campaign reconciliation complete.
SAVE_CONTINUE_DIRTY consumes the failure UI epoch, applies the policy's exact
dirty/final-outcome mutation, sets result CONTINUED_DIRTY, phase
CONTINUED_DIRTY, and TERMINAL, then releases the head. SAVE_TRAVEL_UNSAVED first
publishes the already-validated transition scratch, marks it dirty, then sets
result/phase TRAVELED_UNSAVED and TERMINAL before releasing the head into the
transition. These are deliberate terminal outcomes, never aliases for CANCELED.

The New Game initialization policy exposes only addressed Retry or
`PROCESS_ACCEPT_NEW_GAME_ABORT_TO_TITLE`. Abort consumes the UI epoch, sets
ABORTED_TO_TITLE, fences every backend callback by phase/request/attempt,
destroys the unpublished-or-new-campaign runtime and draft authority, returns to
Title, and performs a fresh two-page loader pass; the preserved anchor remains
recoverable even if the target write was partial. Retry keeps the same address
and confirmed authority until the first page verifies. The authority moves to
CONSUMED only with that request's COMMITTED result. No Continue Dirty or Travel
Unsaved action is legal before the first campaign page commits.

The second slot waits at SNAPSHOT_READY until the predecessor reaches one of the
terminal phases COMMITTED, CANCELED, CONTINUED_DIRTY, TRAVELED_UNSAVED, or
ABORTED_TO_TITLE. FAILED and retrying heads continue to own the writer/address
and block promotion. Slot release clears the old UI generation/input epoch and
promotes at most one successor through a fresh durable reread; it never inherits
the predecessor's target. A stale button must match request generation,
`ui_owner_generation`, snapshot generation, current owner, phase FAILED, and an
unconsumed input epoch. A completion must additionally match the current attempt
and require phase WRITING or VERIFYING; any callback after a terminal phase is
ignored/asserted and cannot commit, mutate dirty state, close a newer UI, or
promote twice.

The exact Cancel behavior is source-bound:

| Failure source | Prior-settings requirement | Exact `SAVE_CANCEL_TO_OWNER` effect |
|---|---|---|
| `SAVE_FAILURE_SOURCE_MANUAL_RELAY` | `prior_settings_valid=0`; settings generations and prior bytes zero | discard the uncommitted manual candidate and failure owner; return to the retained Relay surface with live progress/settings/dirty state unchanged |
| `SAVE_FAILURE_SOURCE_SETTINGS` | `prior_settings_valid=1`, `PRIOR_SETTINGS_CAPTURED`, exact nonzero prior/candidate settings generations, typed prior SaveReason/dirty state | restore captured sanitized settings, prior SaveReason, and prior dirty state; advance live settings generation once; discard request/failure owner; no journal claim changes |

Settings Apply edits scratch first. Before publishing the sanitized candidate to
runtime, it captures prior settings, SaveReason, dirty state, and settings
generation into the request and proves candidate generation is
`next_nonzero(prior)`. It may publish the candidate settings and temporary
`SAVE_REASON_SETTINGS` only after queue reservation. From that reservation until
COMMITTED/CANCELED, the retained Settings owner blocks gameplay, story,
transition, menu-close, and every other save-producing semantic transaction;
no successor may depend on or later re-encode the candidate. Settings Cancel
after a failed write is legal only while live runtime generation, settings
generation, settings bytes, SaveReason, and dirty state still equal the exact
candidate state owned by the request. Any mismatch makes the old owner stale and
forbids restoration. Manual Relay never publishes a settings
change and therefore has nothing to restore. Pre-transition Cancel follows its
separate scratch-discard contract and never uses this shared Manual/Settings row.
If Settings Apply began CLEAN, its failed candidate made runtime dirty and Cancel
returns it to CLEAN after exact restoration; if it began DIRTY for unrelated
progress, Cancel leaves it DIRTY. Goldens cover both origins and reject a stale
candidate-generation cancel, a synthetic candidate-to-successor attempt, and
any semantic mutation while the retained owner is active.

A verified COMMITTED result reconciles persistence atomically only against its
campaign owner. The request's nonzero `campaign_owner_generation` and immutable
payload `campaign_seed` must both equal the live `FinalSaveOutcomeOwner` mirrors.
A mismatch may leave a newly verified historical journal page on EEPROM, but it
cannot change the current campaign's durable outcome, runtime dirty state,
SaveReason, UI, or owner generation. With an exact campaign match, a semantically
valid `CHECKPOINT_SLICE_COMPLETE` candidate upgrades the outcome to `SAVED`
regardless of whether its operation reason is Final Hook, Manual Relay, Settings,
or a later legal transition; SaveReason remains operation provenance, not
durable-record identity. Runtime dirty then clears only if the committed
request's captured semantic runtime generation equals the current live
generation and a fresh canonical encode of current progress is byte-identical
to all 216 immutable request bytes after the four playtime bytes are normalized
to the request's captured value. Live playtime
must be greater than or equal to that captured value. CRC is checked first only
as an optimization; equality never relies on a hash collision. If any newer
mutation exists, the durable page may advance and a complete opening may become
known-saved, but runtime remains DIRTY. A non-current queued success can
never falsely clean newer play.

After that exact current reconciliation and before publishing Save Done, a
`SAVE_REASON_SETTINGS` request additionally requires its candidate settings
generation and candidate bytes to equal the live settings owner; it then
atomically copies those eight bytes into `SettingsProfileOwner`, advances the
profile generation, records the current campaign/settings generations, and sets
source `SETTINGS_PROFILE_CAMPAIGN_SETTINGS_COMMIT`. No other request may change
the process profile. Any current initialized commit may refresh the independent
`GS` capsule best-effort only after a complete reread proves its page is the
unambiguously newest selected page; profile publication never depends on that
header write succeeding. Campaign mismatch, semantic-generation mismatch,
newer runtime bytes, or a merely historical verified page suppresses both
profile and capsule updates.

Active playtime advances in a separate monotonic accumulator only on
player-controlled fixed gameplay ticks; it does not advance semantic
`runtime_generation` or set dirty by itself. Request capture materializes the
current saturated seconds into the immutable payload. Reconciliation ignores
only later monotonic clock advance through the normalization above; every other
byte and semantic generation must match. A later save captures the newer time.
Tests cover same-second, multi-second, saturation, and regression cases so the
clock neither forces every successful save dirty nor masks another mutation.

The reachable post-chapter state pairs are exhaustive:

| Durable final outcome | Runtime dirty | Meaning / legal transition |
|---|---|---|
| `FINAL_SAVE_OUTCOME_SAVED` | `RUNTIME_PROGRESS_CLEAN` | a verified complete page equals current progress |
| `FINAL_SAVE_OUTCOME_SAVED` | `RUNTIME_PROGRESS_DIRTY` | the opening record is secure, but current location/settings/progress is newer; saved Oren copy remains truthful |
| `FINAL_SAVE_OUTCOME_CONTINUE_UNSAVED` | `RUNTIME_PROGRESS_DIRTY` | Slice Complete exists only in memory; unsaved Oren copy is required |

`CONTINUE_UNSAVED + CLEAN` is illegal. A later exact-current successful save of
coherent Slice Complete atomically upgrades it to `SAVED + CLEAN`; an older
complete success upgrades only the durable axis and leaves dirty true. Pending
is legal only while the initial Final Hook write/failure choice is unresolved
and has no post-chapter interaction route. A later post-chapter save failure
after `SAVED + CLEAN` followed by Continue Dirty produces `SAVED + DIRTY`, never
reverts the durable axis. Decode of any verified Slice Complete page initializes
the durable axis to SAVED from checkpoint semantics even when a later legitimate
SaveReason replaced `FINAL_HOOK`. Goldens cover exact-current, late/queued,
manual recovery, settings recovery, later postchapter failure, reload, and all
illegal cross-products.

The exact 216-byte EEPROM projection is below. Its extra bytes are explicit schema/reserved capacity, not compiler padding.

`GameProgressSnapshot` is a byte-independent field copy produced by a dedicated copier. `PRE_RUSK_BATTLE_SNAPSHOT` is created in memory only by `ACTION_CAPTURE_PRE_RUSK_SNAPSHOT`, after all preceding scratch mutations validate and before the battle transition suffix. Its payload is exactly current prospective `SaveData`, current runtime generation, a new nonzero snapshot generation, `ENCOUNTER_RUSK_COURTYARD`, `RETRY_SEED_POLICY_FIXED_ENCOUNTER_BASE`, flags `PRE_RUSK_PAYLOAD_CONFRONTATION_INCLUDED + PRE_RUSK_PAYLOAD_REWARDS_CLEAR + PRE_RUSK_PAYLOAD_PARTY_HP_EXACT`, and seed `0x5255534B`. The candidate must include confrontation seen, exact party HP/progression, and zero Rusk win/clear/reward/door facts. It stores no renderer handle, `BattleState`, audio, actor transform, or pointer and never triggers EEPROM; reboot resumes `CHECKPOINT_ESTATE_ARRIVAL` and replays the confrontation.

While valid, payload bytes never change. `PRE_RUSK_RESTORE_STORY_PARTY_PRESERVE_RUNTIME` restores every saved story, objective, inventory/party, HP/progression, location/checkpoint, battle-history, and chapter field from the payload, but sets `playtime_seconds=max(live.playtime_seconds,payload.playtime_seconds)` and copies the live independently sanitized `GameSettings`; those are the only merge exceptions. It then assigns `runtime_generation=next_nonzero(live_generation)`, clears volatile battle/presenter state, and updates only `PreRuskSnapshotOwner.bound_runtime_generation` to that new generation. Thus pause/settings changes and elapsed battle time never rewind, while story/party retry state is exact. Host tests mutate every saved field, increase time, change each setting, and prove only those two exceptions survive.

`COND_TRANS_PRE_RUSK_SNAPSHOT_VALID` is exactly owner state valid, payload encounter Rusk, and bound generation equal to live generation. Retry may rebind repeatedly without changing snapshot generation/seed/data. Return-to-Annex invalidates the owner only after the post-enter recipe, save-slot reservation, and coherent destination publish succeed. Reboot or full courtyard/GameState snapshot-owner destruction invalidates it; ordinary battle action/presenter-overlay teardown inside a defeat flow explicitly does not. A later Estate confrontation must capture a new payload and cannot reuse the invalidated one.

The two `BattleDefeatFlowDef` rows are literal:

| Encounter / choice | restore phase / merge policy | TransitionId | on-COMMIT dialogue / dismissal xref | post-recipe xref / rollback | Flags |
|---|---|---|---|---|---|
| `ENCOUNTER_RUSK_COURTYARD / BATTLE_DEFEAT_CHOICE_RETRY` | `BATTLE_DEFEAT_RESTORE_BEFORE_TRANSITION / PRE_RUSK_RESTORE_STORY_PARTY_PRESERVE_RUNTIME` | `TRANS_DEF_RUSK_BATTLE_RETRY` | `RUSK_RETRY_IMMEDIATE_001 / ACTION_RUSK_IMMEDIATE_START_ENCOUNTER` | `0 / RUSK_DEFEAT_MENU_ROLLBACK` | `DEFEAT_FLOW_REQUIRE_PRE_RUSK_SNAPSHOT + DEFEAT_FLOW_TEARDOWN_BATTLE_BEFORE_REQUEST + DEFEAT_FLOW_SHOW_DIALOGUE_ON_COMMIT + DEFEAT_FLOW_REBUILD_MENU_ON_ROLLBACK + DEFEAT_FLOW_DESTROY_OWNER_AFTER_HANDOFF` |
| `ENCOUNTER_RUSK_COURTYARD / BATTLE_DEFEAT_CHOICE_RETURN_TO_ANNEX` | `BATTLE_DEFEAT_RESTORE_IN_POST_RECIPE / PRE_RUSK_RESTORE_STORY_PARTY_PRESERVE_RUNTIME` | `TRANS_DEF_RUSK_RETURN_ANNEX` | `0 / 0` | `TRANS_RECIPE_RUSK_RETURN_ANNEX / RUSK_DEFEAT_MENU_ROLLBACK` | `DEFEAT_FLOW_REQUIRE_PRE_RUSK_SNAPSHOT + DEFEAT_FLOW_TEARDOWN_BATTLE_BEFORE_REQUEST + DEFEAT_FLOW_INVALIDATE_SNAPSHOT_ON_COMMIT + DEFEAT_FLOW_REBUILD_MENU_ON_ROLLBACK + DEFEAT_FLOW_DESTROY_OWNER_AFTER_HANDOFF` |

The sole rollback row is `{ RUSK_DEFEAT_MENU_ROLLBACK, ENCOUNTER_RUSK_COURTYARD, RUSK_LOSE_CHOICE, DEFEAT_ROLLBACK_REQUIRE_LIVE_SNAPSHOT + DEFEAT_ROLLBACK_REQUIRE_RESULT_TOKEN + DEFEAT_ROLLBACK_REBUILD_OVERLAY_AND_CHOICES + DEFEAT_ROLLBACK_PRESERVE_RUNTIME_GENERATION + DEFEAT_ROLLBACK_ADVANCE_MENU_AND_INPUT_EPOCH, 0 }`. After defeat presentation is acknowledged, BattleRuntimeOwner first advances/destroys the battle generation exactly as section 7 requires; only then DefeatFlowOwner obtains a separate new nonzero `defeat_flow_generation`, `menu_generation`, and `input_event_epoch`, constructs the overlay/choices, and emits the exact 20-byte `BattleDefeatResultToken`. No field is compared to a battle generation. Any newly reconstructed encounter later obtains its own fresh battle generation.

Choice acceptance validates the live runtime, defeat-flow, menu, and input-event generations, all three token flags, the still-active CHOICES state, zero prior accepted choice, and the bound snapshot, then atomically records the chosen value and moves the owner to HANDOFF_PENDING. It reserves unbound transition/rollback capacity without stamping a generation. Retry restores/rebinds, advances runtime generation, and only afterward atomically fills both reserved continuations with the new runtime generation, unchanged live defeat-flow/menu/input generations, and copied validated acceptance proof; a prefill failure releases both reservations and publishes nothing. Return fills its request/rollback with the current generation, while its post-recipe continuation is staged against the exact prospective generation produced by restoration. A transition COMMIT runs the exact row continuation: Retry acquires `RUSK_RETRY_IMMEDIATE_001` and its reserved dismissal continuation; Return applies the typed recipe, reserves/enqueues its exact save snapshot, and invalidates the pre-Rusk snapshot only afterward. The `dialogue_dismiss_action_xref` is a required equality cross-check against the one `StoryTriggerBindingDef` for that dialogue dismissal, and `post_recipe_xref` is a required equality cross-check against the one `TransitionStoryBindingDef`; BattleDefeatFlow never dispatches either a second time.

The success handoff has one mandatory finalizer before any continuation owner releases control. Retry finalizes only after the short dialogue owner and its dismissal slot are acquired no-fail; Return finalizes only after destination/progress publish plus immutable save enqueue succeed. It then zeroes the entire public result token, sets state EMPTY and accepted choice zero, advances `next_defeat_flow_generation=next_nonzero(old defeat_flow_generation)`, and only then releases the continuation. Therefore no late menu edge or copied result token can act during the new dialogue/scene. If any staging/load/COMMIT step fails first, rollback does not reuse the accepted epoch: it advances both `menu_generation` and `input_event_epoch` with `next_nonzero`, clears accepted choice and all UI input latches, rebuilds overlay/choices, mints a new matching token under CHOICES, and discards one full poll frame before reacquisition. Defeat-flow generation may remain live for this rollback, but the old menu/event token can no longer match. A generic scene reload or reopening choices with the accepted epoch is forbidden. No core controller hard-codes Rusk dialogue or destination IDs.

Seed initialization uses one locked `mix32` function: `x ^= x>>16; x *= 0x7FEB352D; x ^= x>>15; x *= 0x846CA68B; x ^= x>>16`, with unsigned 32-bit wrap after each operation; a zero result remaps to `0x6D2B79F5`. New Game creates its runtime-draft `campaign_seed = mix32(install_nonce ^ captured_boot_tick ^ 0x4E363447)` once when BEGIN commits. A missing/corrupt header supplies a process-generated nonzero draft install nonce but does not write it before the first checkpoint. Opening restart preserves the draft seed; cancel discards it; coherent `CHECKPOINT_AFTER_NAME` persists it.

Starter acquisition derives `personal_seed = mix32(campaign_seed ^ (CreatureId * 0x9E3779B9) ^ slot_index)` for Quarrune slot 0 and Ayselor slot 1; multiplication wraps uint32 and zero-remap is identical. These seeds commit atomically with `CHECKPOINT_AFTER_TUTORIAL`. Fixed encounter seeds remain independent. Golden input `install_nonce=0x12345678`, `boot_tick=0x00001000` yields campaign `0x757EEA74`, Quarrune `0x31AB6F86`, and Ayselor `0x5E51FE8D`.

Opening persistent progression is closed, not free-form. `research_points` is initialized to 0 and remains exactly 0 for the entire slice. Before starter acquisition all party slots are zero. Quarrune/Ayselor enter at level 10, progression rank 0, experience 0, full derived HP, Sync 0, move-unlock mask `0x0F`, and flags 0; no chapter action changes level/rank/experience/mask. Rusk victory changes only Sync to 25 each and Team Link to 1 while retaining post-battle HP; `RUSK_POST_005` dismissal then restores both HP values in the typed heal/door transaction. Any other research/rank/experience/mask value is invalid for an opening-chapter page.

`chapter_progression` is the exact highest committed story recipe: After Name 0, After Tutorial 1, Field Relay 2, Annex Trace Complete 3, Annex Departure 4, Estate Arrival 5, Rusk Victory 6, Tavi Found 7, Tavi Returned 8, Slice Complete 9. `CHECKPOINT_RUSK_RETURN_TO_ANNEX` retains value 5 because the battle was not won. Manual, transition, and settings saves retain the current value. Transactions set the listed value atomically and never decrement it; decoder validation derives the same value from checkpoint/flags and rejects disagreement.

### 9.1 Saveable location registry

Saved tuples have their own generated registry. They are not inferred from transition destinations: several checkpoint anchors are intentionally never a normal portal destination, while battle, world-map, loading, and end-card destinations are intentionally never saveable.

```c
typedef enum SaveableLocationIdValue {
    SAVELOC_SIM_INTRO = 1,
    SAVELOC_ANNEX_SIM_POST_TUTORIAL = 2,
    SAVELOC_ANNEX_SIM_FROM_ATRIUM = 3,
    SAVELOC_ANNEX_ATRIUM_FROM_SIM = 4,
    SAVELOC_ANNEX_ATRIUM_FROM_DIRECTOR = 5,
    SAVELOC_ANNEX_ATRIUM_FROM_PLAYER_ROOM = 6,
    SAVELOC_ANNEX_ATRIUM_FROM_CLINIC = 7,
    SAVELOC_ANNEX_ATRIUM_FROM_WORKSHOP = 8,
    SAVELOC_ANNEX_ATRIUM_FROM_THRESHOLD = 9,
    SAVELOC_ANNEX_ATRIUM_ELEVATOR_LOWER = 10,
    SAVELOC_ANNEX_ATRIUM_ELEVATOR_UPPER = 11,
    SAVELOC_ANNEX_ATRIUM_TRACE_COMPLETE = 12,
    SAVELOC_ANNEX_ATRIUM_RETURN = 13,
    SAVELOC_ANNEX_ATRIUM_POST_CHAPTER = 14,
    SAVELOC_ANNEX_DIRECTOR_FROM_ATRIUM = 15,
    SAVELOC_ANNEX_PLAYER_ROOM_FROM_ATRIUM = 16,
    SAVELOC_ANNEX_CLINIC_FROM_ATRIUM = 17,
    SAVELOC_ANNEX_WORKSHOP_RELAY = 18,
    SAVELOC_ANNEX_WORKSHOP_FROM_ATRIUM = 19,
    SAVELOC_ANNEX_THRESHOLD_DEPARTURE = 20,
    SAVELOC_ANNEX_THRESHOLD_FROM_ATRIUM = 21,
    SAVELOC_ESTATE_COURTYARD_ARRIVAL = 22,
    SAVELOC_ESTATE_COURTYARD_POST_RUSK = 23,
    SAVELOC_ESTATE_COURTYARD_FROM_MAP = 24,
    SAVELOC_ESTATE_COURTYARD_FROM_FOYER = 25,
    SAVELOC_ESTATE_FOYER_FROM_COURTYARD = 26,
    SAVELOC_ESTATE_FOYER_FROM_HALL = 27,
    SAVELOC_ESTATE_HALL_FROM_FOYER = 28,
    SAVELOC_ESTATE_HALL_FROM_STUDY = 29,
    SAVELOC_ESTATE_STUDY_FROM_HALL = 30,
    SAVELOC_ESTATE_STUDY_TAVI_FOUND = 31
} SaveableLocationIdValue;

typedef enum SaveLocationConditionIdValue {
    COND_SAVE_AFTER_NAME = 0x6301,
    COND_SAVE_ANNEX_STORY_LEGAL = 0x6302,
    COND_SAVE_RELAY_ACQUIRED = 0x6303,
    COND_SAVE_TRACE_OR_LATER = 0x6304,
    COND_SAVE_ANNEX_RETURNED = 0x6305,
    COND_SAVE_SLICE_COMPLETE = 0x6306,
    COND_SAVE_THRESHOLD_DEPARTURE = 0x6307,
    COND_SAVE_ESTATE_ARRIVED = 0x6308,
    COND_SAVE_ESTATE_POST_RUSK = 0x6309,
    COND_SAVE_ESTATE_INTERIOR = 0x630A,
    COND_SAVE_ORRERY_OPEN = 0x630B,
    COND_SAVE_TAVI_FOUND = 0x630C
} SaveLocationConditionIdValue;

enum SaveableLocationFlags {
    SAVELOC_CHECKPOINT_EXACT = 1u << 0,
    SAVELOC_MANUAL_ALLOWED = 1u << 1,
    SAVELOC_LAST_SAFE_ALLOWED = 1u << 2,
    SAVELOC_CONTINUE_ALLOWED = 1u << 3
};

typedef struct SaveableLocationDef {
    SaveableLocationId id;          /* 0 */
    SceneId scene_id;               /* 2 */
    ZoneId zone_id;                 /* 4 */
    SpawnId spawn_id;               /* 6 */
    ConditionId legal_condition_id; /* 8 */
    uint16_t flags;                 /* 10 */
} SaveableLocationDef;
_Static_assert(sizeof(SaveableLocationDef) == 12, "SaveableLocationDef layout");
```

The condition programs are exact: `AFTER_NAME` is confirmed name plus opening seen and tutorial false; `ANNEX_STORY_LEGAL` is tutorial/starter complete with story facts legal for the candidate Annex tuple; `RELAY_ACQUIRED` adds Relay unlock/substage at least 2; `TRACE_OR_LATER` adds Estate unlock; `ANNEX_RETURNED` requires Tavi returned; `SLICE_COMPLETE` requires the locked final-hook equivalences; `THRESHOLD_DEPARTURE` is Annex departure cleared or the exact Rusk Return recipe; `ESTATE_ARRIVED` requires Estate arrived; `ESTATE_POST_RUSK` requires all stable Rusk equivalences; `ESTATE_INTERIOR` requires Estate door open; `ORRERY_OPEN` adds the stair-open flag; and `TAVI_FOUND` adds the reunion/return-objective equivalences. These codec-visible conditions read only persisted `SaveData` plus the candidate tuple. Runtime control/dialogue/animation stability is a separate encode-request gate and is never required during reboot decode.

| SaveableLocationId | Exact Scene / Zone / Spawn | ConditionId | Flags |
|---|---|---|---|
| `SAVELOC_SIM_INTRO` | `SCENE_SIM_ARENA / ZONE_SIM_ARENA / SPAWN_SIM_INTRO` | `COND_SAVE_AFTER_NAME` | `SAVELOC_CHECKPOINT_EXACT + SAVELOC_LAST_SAFE_ALLOWED + SAVELOC_CONTINUE_ALLOWED` |
| `SAVELOC_ANNEX_SIM_POST_TUTORIAL` | `SCENE_ANNEX_INTERIOR / ZONE_ANNEX_SIMULATION_ROOM / SPAWN_ANNEX_SIM_POST_TUTORIAL` | `COND_SAVE_ANNEX_STORY_LEGAL` | `SAVELOC_CHECKPOINT_EXACT + SAVELOC_MANUAL_ALLOWED + SAVELOC_LAST_SAFE_ALLOWED + SAVELOC_CONTINUE_ALLOWED` |
| `SAVELOC_ANNEX_SIM_FROM_ATRIUM` | `SCENE_ANNEX_INTERIOR / ZONE_ANNEX_SIMULATION_ROOM / SPAWN_ANNEX_SIM_FROM_ATRIUM` | `COND_SAVE_ANNEX_STORY_LEGAL` | `SAVELOC_MANUAL_ALLOWED + SAVELOC_LAST_SAFE_ALLOWED + SAVELOC_CONTINUE_ALLOWED` |
| `SAVELOC_ANNEX_ATRIUM_FROM_SIM` | `SCENE_ANNEX_INTERIOR / ZONE_ANNEX_ATRIUM / SPAWN_ANNEX_ATRIUM_FROM_SIM` | `COND_SAVE_ANNEX_STORY_LEGAL` | `SAVELOC_MANUAL_ALLOWED + SAVELOC_LAST_SAFE_ALLOWED + SAVELOC_CONTINUE_ALLOWED` |
| `SAVELOC_ANNEX_ATRIUM_FROM_DIRECTOR` | `SCENE_ANNEX_INTERIOR / ZONE_ANNEX_ATRIUM / SPAWN_ANNEX_ATRIUM_FROM_DIRECTOR` | `COND_SAVE_ANNEX_STORY_LEGAL` | `SAVELOC_MANUAL_ALLOWED + SAVELOC_LAST_SAFE_ALLOWED + SAVELOC_CONTINUE_ALLOWED` |
| `SAVELOC_ANNEX_ATRIUM_FROM_PLAYER_ROOM` | `SCENE_ANNEX_INTERIOR / ZONE_ANNEX_ATRIUM / SPAWN_ANNEX_ATRIUM_FROM_PLAYER_ROOM` | `COND_SAVE_ANNEX_STORY_LEGAL` | `SAVELOC_MANUAL_ALLOWED + SAVELOC_LAST_SAFE_ALLOWED + SAVELOC_CONTINUE_ALLOWED` |
| `SAVELOC_ANNEX_ATRIUM_FROM_CLINIC` | `SCENE_ANNEX_INTERIOR / ZONE_ANNEX_ATRIUM / SPAWN_ANNEX_ATRIUM_FROM_CLINIC` | `COND_SAVE_ANNEX_STORY_LEGAL` | `SAVELOC_MANUAL_ALLOWED + SAVELOC_LAST_SAFE_ALLOWED + SAVELOC_CONTINUE_ALLOWED` |
| `SAVELOC_ANNEX_ATRIUM_FROM_WORKSHOP` | `SCENE_ANNEX_INTERIOR / ZONE_ANNEX_ATRIUM / SPAWN_ANNEX_ATRIUM_FROM_WORKSHOP` | `COND_SAVE_ANNEX_STORY_LEGAL` | `SAVELOC_MANUAL_ALLOWED + SAVELOC_LAST_SAFE_ALLOWED + SAVELOC_CONTINUE_ALLOWED` |
| `SAVELOC_ANNEX_ATRIUM_FROM_THRESHOLD` | `SCENE_ANNEX_INTERIOR / ZONE_ANNEX_ATRIUM / SPAWN_ANNEX_ATRIUM_FROM_THRESHOLD` | `COND_SAVE_ANNEX_STORY_LEGAL` | `SAVELOC_MANUAL_ALLOWED + SAVELOC_LAST_SAFE_ALLOWED + SAVELOC_CONTINUE_ALLOWED` |
| `SAVELOC_ANNEX_ATRIUM_ELEVATOR_LOWER` | `SCENE_ANNEX_INTERIOR / ZONE_ANNEX_ATRIUM / SPAWN_ANNEX_ATRIUM_ELEVATOR_LOWER` | `COND_SAVE_ANNEX_STORY_LEGAL` | `SAVELOC_MANUAL_ALLOWED + SAVELOC_LAST_SAFE_ALLOWED + SAVELOC_CONTINUE_ALLOWED` |
| `SAVELOC_ANNEX_ATRIUM_ELEVATOR_UPPER` | `SCENE_ANNEX_INTERIOR / ZONE_ANNEX_ATRIUM / SPAWN_ANNEX_ATRIUM_ELEVATOR_UPPER` | `COND_SAVE_ANNEX_STORY_LEGAL` | `SAVELOC_MANUAL_ALLOWED + SAVELOC_LAST_SAFE_ALLOWED + SAVELOC_CONTINUE_ALLOWED` |
| `SAVELOC_ANNEX_ATRIUM_TRACE_COMPLETE` | `SCENE_ANNEX_INTERIOR / ZONE_ANNEX_ATRIUM / SPAWN_ANNEX_ATRIUM_TRACE_COMPLETE` | `COND_SAVE_TRACE_OR_LATER` | `SAVELOC_CHECKPOINT_EXACT + SAVELOC_MANUAL_ALLOWED + SAVELOC_LAST_SAFE_ALLOWED + SAVELOC_CONTINUE_ALLOWED` |
| `SAVELOC_ANNEX_ATRIUM_RETURN` | `SCENE_ANNEX_INTERIOR / ZONE_ANNEX_ATRIUM / SPAWN_ANNEX_ATRIUM_RETURN` | `COND_SAVE_ANNEX_RETURNED` | `SAVELOC_CHECKPOINT_EXACT + SAVELOC_MANUAL_ALLOWED + SAVELOC_LAST_SAFE_ALLOWED + SAVELOC_CONTINUE_ALLOWED` |
| `SAVELOC_ANNEX_ATRIUM_POST_CHAPTER` | `SCENE_ANNEX_INTERIOR / ZONE_ANNEX_ATRIUM / SPAWN_ANNEX_ATRIUM_POST_CHAPTER` | `COND_SAVE_SLICE_COMPLETE` | `SAVELOC_CHECKPOINT_EXACT + SAVELOC_MANUAL_ALLOWED + SAVELOC_LAST_SAFE_ALLOWED + SAVELOC_CONTINUE_ALLOWED` |
| `SAVELOC_ANNEX_DIRECTOR_FROM_ATRIUM` | `SCENE_ANNEX_INTERIOR / ZONE_ANNEX_DIRECTOR_LAB / SPAWN_ANNEX_DIRECTOR_FROM_ATRIUM` | `COND_SAVE_ANNEX_STORY_LEGAL` | `SAVELOC_MANUAL_ALLOWED + SAVELOC_LAST_SAFE_ALLOWED + SAVELOC_CONTINUE_ALLOWED` |
| `SAVELOC_ANNEX_PLAYER_ROOM_FROM_ATRIUM` | `SCENE_ANNEX_INTERIOR / ZONE_ANNEX_PLAYER_ROOM / SPAWN_ANNEX_PLAYER_ROOM_FROM_ATRIUM` | `COND_SAVE_ANNEX_STORY_LEGAL` | `SAVELOC_MANUAL_ALLOWED + SAVELOC_LAST_SAFE_ALLOWED + SAVELOC_CONTINUE_ALLOWED` |
| `SAVELOC_ANNEX_CLINIC_FROM_ATRIUM` | `SCENE_ANNEX_INTERIOR / ZONE_ANNEX_CLINIC / SPAWN_ANNEX_CLINIC_FROM_ATRIUM` | `COND_SAVE_ANNEX_STORY_LEGAL` | `SAVELOC_MANUAL_ALLOWED + SAVELOC_LAST_SAFE_ALLOWED + SAVELOC_CONTINUE_ALLOWED` |
| `SAVELOC_ANNEX_WORKSHOP_RELAY` | `SCENE_ANNEX_INTERIOR / ZONE_ANNEX_WORKSHOP / SPAWN_ANNEX_WORKSHOP_RELAY` | `COND_SAVE_RELAY_ACQUIRED` | `SAVELOC_CHECKPOINT_EXACT + SAVELOC_MANUAL_ALLOWED + SAVELOC_LAST_SAFE_ALLOWED + SAVELOC_CONTINUE_ALLOWED` |
| `SAVELOC_ANNEX_WORKSHOP_FROM_ATRIUM` | `SCENE_ANNEX_INTERIOR / ZONE_ANNEX_WORKSHOP / SPAWN_ANNEX_WORKSHOP_FROM_ATRIUM` | `COND_SAVE_ANNEX_STORY_LEGAL` | `SAVELOC_MANUAL_ALLOWED + SAVELOC_LAST_SAFE_ALLOWED + SAVELOC_CONTINUE_ALLOWED` |
| `SAVELOC_ANNEX_THRESHOLD_DEPARTURE` | `SCENE_ANNEX_INTERIOR / ZONE_ANNEX_THRESHOLD / SPAWN_ANNEX_THRESHOLD_DEPARTURE` | `COND_SAVE_THRESHOLD_DEPARTURE` | `SAVELOC_CHECKPOINT_EXACT + SAVELOC_MANUAL_ALLOWED + SAVELOC_LAST_SAFE_ALLOWED + SAVELOC_CONTINUE_ALLOWED` |
| `SAVELOC_ANNEX_THRESHOLD_FROM_ATRIUM` | `SCENE_ANNEX_INTERIOR / ZONE_ANNEX_THRESHOLD / SPAWN_ANNEX_THRESHOLD_FROM_ATRIUM` | `COND_SAVE_ANNEX_STORY_LEGAL` | `SAVELOC_MANUAL_ALLOWED + SAVELOC_LAST_SAFE_ALLOWED + SAVELOC_CONTINUE_ALLOWED` |
| `SAVELOC_ESTATE_COURTYARD_ARRIVAL` | `SCENE_ESTATE_COURTYARD / ZONE_ESTATE_COURTYARD / SPAWN_ESTATE_COURTYARD_ARRIVAL` | `COND_SAVE_ESTATE_ARRIVED` | `SAVELOC_CHECKPOINT_EXACT + SAVELOC_MANUAL_ALLOWED + SAVELOC_LAST_SAFE_ALLOWED + SAVELOC_CONTINUE_ALLOWED` |
| `SAVELOC_ESTATE_COURTYARD_POST_RUSK` | `SCENE_ESTATE_COURTYARD / ZONE_ESTATE_COURTYARD / SPAWN_ESTATE_COURTYARD_POST_RUSK` | `COND_SAVE_ESTATE_POST_RUSK` | `SAVELOC_CHECKPOINT_EXACT + SAVELOC_MANUAL_ALLOWED + SAVELOC_LAST_SAFE_ALLOWED + SAVELOC_CONTINUE_ALLOWED` |
| `SAVELOC_ESTATE_COURTYARD_FROM_MAP` | `SCENE_ESTATE_COURTYARD / ZONE_ESTATE_COURTYARD / SPAWN_ESTATE_COURTYARD_FROM_MAP` | `COND_SAVE_ESTATE_ARRIVED` | `SAVELOC_MANUAL_ALLOWED + SAVELOC_LAST_SAFE_ALLOWED + SAVELOC_CONTINUE_ALLOWED` |
| `SAVELOC_ESTATE_COURTYARD_FROM_FOYER` | `SCENE_ESTATE_COURTYARD / ZONE_ESTATE_COURTYARD / SPAWN_ESTATE_COURTYARD_FROM_FOYER` | `COND_SAVE_ESTATE_POST_RUSK` | `SAVELOC_MANUAL_ALLOWED + SAVELOC_LAST_SAFE_ALLOWED + SAVELOC_CONTINUE_ALLOWED` |
| `SAVELOC_ESTATE_FOYER_FROM_COURTYARD` | `SCENE_ESTATE_INTERIOR / ZONE_ESTATE_FOYER / SPAWN_ESTATE_FOYER_FROM_COURTYARD` | `COND_SAVE_ESTATE_INTERIOR` | `SAVELOC_MANUAL_ALLOWED + SAVELOC_LAST_SAFE_ALLOWED + SAVELOC_CONTINUE_ALLOWED` |
| `SAVELOC_ESTATE_FOYER_FROM_HALL` | `SCENE_ESTATE_INTERIOR / ZONE_ESTATE_FOYER / SPAWN_ESTATE_FOYER_FROM_HALL` | `COND_SAVE_ESTATE_INTERIOR` | `SAVELOC_MANUAL_ALLOWED + SAVELOC_LAST_SAFE_ALLOWED + SAVELOC_CONTINUE_ALLOWED` |
| `SAVELOC_ESTATE_HALL_FROM_FOYER` | `SCENE_ESTATE_INTERIOR / ZONE_ESTATE_INVENTION_HALL / SPAWN_ESTATE_HALL_FROM_FOYER` | `COND_SAVE_ESTATE_INTERIOR` | `SAVELOC_MANUAL_ALLOWED + SAVELOC_LAST_SAFE_ALLOWED + SAVELOC_CONTINUE_ALLOWED` |
| `SAVELOC_ESTATE_HALL_FROM_STUDY` | `SCENE_ESTATE_INTERIOR / ZONE_ESTATE_INVENTION_HALL / SPAWN_ESTATE_HALL_FROM_STUDY` | `COND_SAVE_ORRERY_OPEN` | `SAVELOC_MANUAL_ALLOWED + SAVELOC_LAST_SAFE_ALLOWED + SAVELOC_CONTINUE_ALLOWED` |
| `SAVELOC_ESTATE_STUDY_FROM_HALL` | `SCENE_ESTATE_INTERIOR / ZONE_ESTATE_OBSERVATORY_STUDY / SPAWN_ESTATE_STUDY_FROM_HALL` | `COND_SAVE_ORRERY_OPEN` | `SAVELOC_MANUAL_ALLOWED + SAVELOC_LAST_SAFE_ALLOWED + SAVELOC_CONTINUE_ALLOWED` |
| `SAVELOC_ESTATE_STUDY_TAVI_FOUND` | `SCENE_ESTATE_INTERIOR / ZONE_ESTATE_OBSERVATORY_STUDY / SPAWN_ESTATE_STUDY_TAVI_FOUND` | `COND_SAVE_TAVI_FOUND` | `SAVELOC_CHECKPOINT_EXACT + SAVELOC_MANUAL_ALLOWED + SAVELOC_LAST_SAFE_ALLOWED + SAVELOC_CONTINUE_ALLOWED` |

Encoding and decoding resolve both `current_location` and `last_safe_location` by exact tuple equality against this table, then evaluate the row condition. Checkpoint encoding additionally requires `SAVELOC_CHECKPOINT_EXACT` and its checkpoint recipe's one exact tuple; manual encoding requires `SAVELOC_MANUAL_ALLOWED`; Continue requires `SAVELOC_CONTINUE_ALLOWED`; fallback requires `SAVELOC_LAST_SAFE_ALLOWED`. A tuple being a `TransitionDef` destination is neither necessary nor sufficient. `SPAWN_WORLD_MAP_*`, `SPAWN_ESTATE_COURTYARD_BATTLE`, `ZONE_END_CARD_UI`, and every loading/action-only anchor are absent by design.

### 9.2 Checkpoint and resume contract

```c
typedef enum CheckpointIdValue {
    CHECKPOINT_NONE = 0,
    CHECKPOINT_AFTER_NAME = 1,
    CHECKPOINT_AFTER_TUTORIAL = 2,
    CHECKPOINT_FIELD_RELAY = 3,
    CHECKPOINT_ANNEX_DEPARTURE = 4,
    CHECKPOINT_ESTATE_ARRIVAL = 5,
    CHECKPOINT_RUSK_VICTORY = 6,
    CHECKPOINT_TAVI_FOUND = 7,
    CHECKPOINT_TAVI_RETURNED = 8,
    CHECKPOINT_SLICE_COMPLETE = 9,
    CHECKPOINT_RUSK_RETURN_TO_ANNEX = 10,
    CHECKPOINT_ANNEX_TRACE_COMPLETE = 11
} CheckpointIdValue;

typedef enum MilestoneSaveFailurePolicyValue {
    MILESTONE_FAIL_KEEP_DIRTY_CONTINUE = 1,
    MILESTONE_FAIL_GATE_RETRY_OR_CONTINUE_UNSAVED = 2
} MilestoneSaveFailurePolicyValue;

typedef enum MilestoneContinuationValue {
    MILESTONE_CONTINUATION_NONE = 0,
    MILESTONE_CONTINUATION_FINAL_SAVE_OUTCOME = 1
} MilestoneContinuationValue;

enum ChapterMilestoneRecipeFlags {
    MILESTONE_FIXED_CURRENT_LOCATION = 1u << 0,
    MILESTONE_FIXED_LAST_SAFE_LOCATION = 1u << 1,
    MILESTONE_MONOTONIC_CHAPTER_PROMOTION = 1u << 2,
    MILESTONE_OWNER_CLOSE_RESERVED = 1u << 3,
    MILESTONE_DIRTY_ON_WRITE_FAILURE = 1u << 4
};

typedef struct ChapterMilestoneRecipeDef {
    uint16_t id;                         /* 0 */
    CheckpointId checkpoint_id;          /* 2 */
    SaveableLocationId current_saveloc_id; /* 4 */
    SaveableLocationId last_safe_saveloc_id; /* 6 */
    uint16_t chapter_progression;        /* 8 */
    SaveReason save_reason;              /* 10 */
    BattleResult battle_result;          /* 11 */
    EncounterId last_encounter_id;       /* 12 */
    uint8_t failure_policy;              /* 14 */
    uint8_t continuation;                /* 15 */
    uint16_t flags;                      /* 16 */
    uint16_t reserved;                   /* 18 */
} ChapterMilestoneRecipeDef;
_Static_assert(sizeof(ChapterMilestoneRecipeDef) == 20, "ChapterMilestoneRecipeDef layout");

enum StoryRetentionSaveFlags {
    RETENTION_RETAIN_CHECKPOINT_CHAPTER_LOCATIONS = 1u << 0,
    RETENTION_REQUIRE_DIALOGUE_ONCE_BIT = 1u << 1,
    RETENTION_OWNER_CLOSE_RESERVED = 1u << 2,
    RETENTION_DIRTY_ON_WRITE_FAILURE = 1u << 3,
    RETENTION_BLOCK_CONTROL_UNTIL_OUTCOME = 1u << 4
};

typedef struct StoryRetentionSaveRecipeDef {
    uint16_t id;                    /* 0 */
    CheckpointId required_checkpoint_id; /* 2 */
    SaveReason save_reason;         /* 4 */
    BattleResult battle_result;     /* 5 */
    EncounterId last_encounter_id;  /* 6 */
    uint8_t once_registry_kind;     /* 8: STORY_START_ONCE_DIALOGUE */
    uint8_t once_bit_index;         /* 9 */
    DialogueId dialogue_id;         /* 10 */
    uint16_t flags;                 /* 12 */
    uint16_t reserved;              /* 14 */
} StoryRetentionSaveRecipeDef;
_Static_assert(sizeof(StoryRetentionSaveRecipeDef) == 16, "StoryRetentionSaveRecipeDef layout");
```

The complete seven-row milestone table is literal:

| RecipeId | Checkpoint / current / last-safe | Chapter | reason / result / encounter | failure / continuation | Flags |
|---|---|---:|---|---|---|
| `MILESTONE_AFTER_TUTORIAL` | `CHECKPOINT_AFTER_TUTORIAL / SAVELOC_ANNEX_SIM_POST_TUTORIAL / SAVELOC_ANNEX_SIM_POST_TUTORIAL` | 1 | `SAVE_REASON_CHECKPOINT / BATTLE_RESULT_NONE / ENCOUNTER_NONE` | `MILESTONE_FAIL_KEEP_DIRTY_CONTINUE / MILESTONE_CONTINUATION_NONE` | `MILESTONE_FIXED_CURRENT_LOCATION + MILESTONE_FIXED_LAST_SAFE_LOCATION + MILESTONE_MONOTONIC_CHAPTER_PROMOTION + MILESTONE_OWNER_CLOSE_RESERVED + MILESTONE_DIRTY_ON_WRITE_FAILURE` |
| `MILESTONE_FIELD_RELAY` | `CHECKPOINT_FIELD_RELAY / SAVELOC_ANNEX_WORKSHOP_RELAY / SAVELOC_ANNEX_SIM_POST_TUTORIAL` | 2 | `SAVE_REASON_CHECKPOINT / BATTLE_RESULT_NONE / ENCOUNTER_NONE` | `MILESTONE_FAIL_KEEP_DIRTY_CONTINUE / MILESTONE_CONTINUATION_NONE` | `MILESTONE_FIXED_CURRENT_LOCATION + MILESTONE_FIXED_LAST_SAFE_LOCATION + MILESTONE_MONOTONIC_CHAPTER_PROMOTION + MILESTONE_OWNER_CLOSE_RESERVED + MILESTONE_DIRTY_ON_WRITE_FAILURE` |
| `MILESTONE_ANNEX_TRACE_COMPLETE` | `CHECKPOINT_ANNEX_TRACE_COMPLETE / SAVELOC_ANNEX_ATRIUM_TRACE_COMPLETE / SAVELOC_ANNEX_ATRIUM_TRACE_COMPLETE` | 3 | `SAVE_REASON_CHECKPOINT / BATTLE_RESULT_NONE / ENCOUNTER_NONE` | `MILESTONE_FAIL_KEEP_DIRTY_CONTINUE / MILESTONE_CONTINUATION_NONE` | `MILESTONE_FIXED_CURRENT_LOCATION + MILESTONE_FIXED_LAST_SAFE_LOCATION + MILESTONE_MONOTONIC_CHAPTER_PROMOTION + MILESTONE_OWNER_CLOSE_RESERVED + MILESTONE_DIRTY_ON_WRITE_FAILURE` |
| `MILESTONE_RUSK_VICTORY` | `CHECKPOINT_RUSK_VICTORY / SAVELOC_ESTATE_COURTYARD_POST_RUSK / SAVELOC_ESTATE_COURTYARD_POST_RUSK` | 6 | `SAVE_REASON_BATTLE_RESULT / BATTLE_RESULT_WIN / ENCOUNTER_RUSK_COURTYARD` | `MILESTONE_FAIL_KEEP_DIRTY_CONTINUE / MILESTONE_CONTINUATION_NONE` | `MILESTONE_FIXED_CURRENT_LOCATION + MILESTONE_FIXED_LAST_SAFE_LOCATION + MILESTONE_MONOTONIC_CHAPTER_PROMOTION + MILESTONE_OWNER_CLOSE_RESERVED + MILESTONE_DIRTY_ON_WRITE_FAILURE` |
| `MILESTONE_TAVI_FOUND` | `CHECKPOINT_TAVI_FOUND / SAVELOC_ESTATE_STUDY_TAVI_FOUND / SAVELOC_ESTATE_COURTYARD_POST_RUSK` | 7 | `SAVE_REASON_CHECKPOINT / BATTLE_RESULT_WIN / ENCOUNTER_RUSK_COURTYARD` | `MILESTONE_FAIL_KEEP_DIRTY_CONTINUE / MILESTONE_CONTINUATION_NONE` | `MILESTONE_FIXED_CURRENT_LOCATION + MILESTONE_FIXED_LAST_SAFE_LOCATION + MILESTONE_MONOTONIC_CHAPTER_PROMOTION + MILESTONE_OWNER_CLOSE_RESERVED + MILESTONE_DIRTY_ON_WRITE_FAILURE` |
| `MILESTONE_TAVI_RETURNED` | `CHECKPOINT_TAVI_RETURNED / SAVELOC_ANNEX_ATRIUM_RETURN / SAVELOC_ANNEX_ATRIUM_RETURN` | 8 | `SAVE_REASON_CHECKPOINT / BATTLE_RESULT_WIN / ENCOUNTER_RUSK_COURTYARD` | `MILESTONE_FAIL_KEEP_DIRTY_CONTINUE / MILESTONE_CONTINUATION_NONE` | `MILESTONE_FIXED_CURRENT_LOCATION + MILESTONE_FIXED_LAST_SAFE_LOCATION + MILESTONE_MONOTONIC_CHAPTER_PROMOTION + MILESTONE_OWNER_CLOSE_RESERVED + MILESTONE_DIRTY_ON_WRITE_FAILURE` |
| `MILESTONE_SLICE_COMPLETE` | `CHECKPOINT_SLICE_COMPLETE / SAVELOC_ANNEX_ATRIUM_POST_CHAPTER / SAVELOC_ANNEX_ATRIUM_RETURN` | 9 | `SAVE_REASON_FINAL_HOOK / BATTLE_RESULT_WIN / ENCOUNTER_RUSK_COURTYARD` | `MILESTONE_FAIL_GATE_RETRY_OR_CONTINUE_UNSAVED / MILESTONE_CONTINUATION_FINAL_SAVE_OUTCOME` | `MILESTONE_FIXED_CURRENT_LOCATION + MILESTONE_FIXED_LAST_SAFE_LOCATION + MILESTONE_MONOTONIC_CHAPTER_PROMOTION + MILESTONE_OWNER_CLOSE_RESERVED + MILESTONE_DIRTY_ON_WRITE_FAILURE` |

A milestone request copies the prospective progress and overwrites exactly the table's checkpoint/chapter/current/last-safe/reason/result/encounter fields. Before publish, the dispatcher resolves both SaveableLocationDefs, validates the complete candidate, reserves the save-service slot, and obtains a generation-bound `OWNER_CLOSE_RESERVED` token for the already-selected closing edge. The token proves the owner can perform its bounded no-fail close after progress publishes; it does not falsely claim the owner is already closed or that player exploration control is stable. The joint sequence is therefore reserve close/save resources -> publish story -> no-fail close/release camera/input/re-entry -> enqueue the immutable snapshot into the reserved slot. Stable-after-dialogue and animation-complete triggers arrive already closed, but still issue the same trivial reserved-close token. `HOOK_014` uses its selected closing edge while HookController retains sequence control; no stable-control predicate exists. `chapter_progression` must strictly increase to the table value; a duplicate identical already-published milestone is an exact-once no-op keyed by runtime generation and recipe ID, while a lower or conflicting promotion fails. A failed EEPROM write leaves the coherent in-memory milestone dirty. Only Slice Complete gates downstream presentation: Retry re-enqueues the identical immutable snapshot, while Continue Unsaved records the typed dirty outcome and permits the end-card continuation without claiming persistence.

The sole retention row is `{ RETENTION_SAVE_SERA_RUSK_RETURN_ONCE, CHECKPOINT_RUSK_RETURN_TO_ANNEX, SAVE_REASON_BATTLE_RESULT, BATTLE_RESULT_RETURN_TO_ANNEX, ENCOUNTER_RUSK_COURTYARD, STORY_START_ONCE_DIALOGUE, 0, SERA_RUSK_RETURN_001, RETENTION_RETAIN_CHECKPOINT_CHAPTER_LOCATIONS + RETENTION_REQUIRE_DIALOGUE_ONCE_BIT + RETENTION_OWNER_CLOSE_RESERVED + RETENTION_DIRTY_ON_WRITE_FAILURE + RETENTION_BLOCK_CONTROL_UNTIL_OUTCOME, 0 }`. It is not a milestone and does not promote chapter/checkpoint or alter either location. StoryTrigger first verifies that the typed dialogue registry maps that exact dialogue to bit 0. Before consuming the selected node edge or bit, it reserves close and save capacity, merges the pending bit into prospective scratch, creates/validates the exact immutable replacement page, and only then publishes node+bit/progress, closes no-fail, and enqueues. Reservation/validation failure consumes neither node nor bit. Write failure keeps runtime dirty and presents Retry or an explicit Continue Dirty choice before exploration control; Return to Title requires the ordinary dirty-loss warning. Only verified persistence guarantees no reboot replay, and Continue Dirty states that risk honestly. The recipe cannot be used for another bit/checkpoint/result and duplicate current-generation completion is a no-op.

Checkpoint rows are validation recipes, not mutable save slots. `required facts` must all hold when the snapshot is encoded; facts not yet listed as required must not be inferred.

| Checkpoint | Durable current Scene / Zone / Spawn | Resume mode / exact beat | Required flags and objective | Exact `last_safe_location` fallback |
|---|---|---|---|---|
| `CHECKPOINT_AFTER_NAME` | `SCENE_SIM_ARENA` / `ZONE_SIM_ARENA` / `SPAWN_SIM_INTRO` | tutorial intro before first lesson prompt | opening seen + name confirmed; tutorial false; no party; no active objective | same simulation-intro tuple |
| `CHECKPOINT_AFTER_TUTORIAL` | `SCENE_ANNEX_INTERIOR` / `ZONE_ANNEX_SIMULATION_ROOM` / `SPAWN_ANNEX_SIM_POST_TUTORIAL` | physical chamber after onboarding, before free Annex control | tutorial complete + Annex intro complete + exact starter team received atomically | same physical-chamber tuple |
| `CHECKPOINT_FIELD_RELAY` | `SCENE_ANNEX_INTERIOR` / `ZONE_ANNEX_WORKSHOP` / `SPAWN_ANNEX_WORKSHOP_RELAY` | Relay acquired and queued Tavi message dismissed; next beat `Ask Pell to trace Tavi's message.` | relay quest started + relay unlocked; `OBJ_RETRIEVE_FIELD_RELAY` active | `SCENE_ANNEX_INTERIOR` / `ZONE_ANNEX_SIMULATION_ROOM` / `SPAWN_ANNEX_SIM_POST_TUTORIAL` |
| `CHECKPOINT_ANNEX_TRACE_COMPLETE` | `SCENE_ANNEX_INTERIOR` / `ZONE_ANNEX_ATRIUM` / `SPAWN_ANNEX_ATRIUM_TRACE_COMPLETE` | immediately after `PELL_TRACE_004`; post-trace free Annex exploration before first exit | Tavi missing + Relay objective complete + Estate unlocked; Annex exit not yet cleared; only `OBJ_FIND_TAVI` active | same atrium trace-complete tuple |
| `CHECKPOINT_ANNEX_DEPARTURE` | `SCENE_ANNEX_INTERIOR` / `ZONE_ANNEX_THRESHOLD` / `SPAWN_ANNEX_THRESHOLD_DEPARTURE` | exterior travel prompt ready before world-map entry | Tavi missing + Relay objective complete + Estate unlocked + Annex exit cleared; only `OBJ_FIND_TAVI` active | `SCENE_ANNEX_INTERIOR` / `ZONE_ANNEX_WORKSHOP` / `SPAWN_ANNEX_WORKSHOP_RELAY` |
| `CHECKPOINT_ESTATE_ARRIVAL` | `SCENE_ESTATE_COURTYARD` / `ZONE_ESTATE_COURTYARD` / `SPAWN_ESTATE_COURTYARD_ARRIVAL` | courtyard before confrontation trigger; no battle result/reward | Estate arrived; `OBJ_FIND_TAVI` active; Rusk won/reward/door false | `SCENE_ANNEX_INTERIOR` / `ZONE_ANNEX_THRESHOLD` / `SPAWN_ANNEX_THRESHOLD_DEPARTURE` |
| `CHECKPOINT_RUSK_VICTORY` | `SCENE_ESTATE_COURTYARD` / `ZONE_ESTATE_COURTYARD` / `SPAWN_ESTATE_COURTYARD_POST_RUSK` | post-result exploration after battle overlay unload and door-open animation | Rusk won + encounter clear + reward flag/claim bit + Estate door open; starters full HP with Sync 25 each and Team Link 1; last result Win and last encounter Rusk; `OBJ_FIND_TAVI` active | same courtyard post-Rusk tuple |
| `CHECKPOINT_TAVI_FOUND` | `SCENE_ESTATE_INTERIOR` / `ZONE_ESTATE_OBSERVATORY_STUDY` / `SPAWN_ESTATE_STUDY_TAVI_FOUND` | reunion complete; derived follower valid; return route ready | Orrery stair open + Ivo met + Tavi found + return requested; returned false; `OBJ_RETURN_WITH_TAVI` active | `SCENE_ESTATE_COURTYARD` / `ZONE_ESTATE_COURTYARD` / `SPAWN_ESTATE_COURTYARD_POST_RUSK` |
| `CHECKPOINT_TAVI_RETURNED` | `SCENE_ANNEX_INTERIOR` / `ZONE_ANNEX_ATRIUM` / `SPAWN_ANNEX_ATRIUM_RETURN` | `RETURN_005` has set returned/objective complete and disabled the derived follower; Tavi remains a staged dialogue actor through `RETURN_007`; save begins only after `RETURN_007` dismissal, before hook | Tavi returned to Annex; return objective complete; derived follower false | same Annex-atrium return tuple |
| `CHECKPOINT_SLICE_COMPLETE` | `SCENE_ANNEX_INTERIOR` / `ZONE_ANNEX_ATRIUM` / `SPAWN_ANNEX_ATRIUM_POST_CHAPTER` | stable post-chapter Annex mode; Continue enters here even if runtime was showing end card | solace beacon + fracture signal + slice complete; `OBJ_OPENING_COMPLETE` complete; no active cutscene/transition | `SCENE_ANNEX_INTERIOR` / `ZONE_ANNEX_ATRIUM` / `SPAWN_ANNEX_ATRIUM_RETURN` |
| `CHECKPOINT_RUSK_RETURN_TO_ANNEX` | `SCENE_ANNEX_INTERIOR` / `ZONE_ANNEX_THRESHOLD` / `SPAWN_ANNEX_THRESHOLD_DEPARTURE` | exact defeat-menu Return to Annex result after normal threshold entry | Estate arrived + Rusk confrontation seen + Find Tavi active; all Rusk win/clear/reward/door facts false; `last_encounter_id=ENCOUNTER_RUSK_COURTYARD`; typed result Return to Annex | same Annex-threshold tuple |

`CHECKPOINT_SLICE_COMPLETE` commits after `HOOK_014` and before the fade destroys the Annex scope. Runtime may then display `SCENE_END_CHAPTER`/`ZONE_END_CARD_UI`, but that UI-only tuple is never serialized and owns no `SpawnId`. A Continue or later Return to Title loads the post-chapter Annex tuple above.

Name confirmation first freezes a valid draft and requests the simulation tuple; it does not initialize or write a page. Only after `SCENE_SIM_ARENA / ZONE_SIM_ARENA / SPAWN_SIM_INTRO` has staged, entered, and passed coherence validation does the controller require a quiescent SaveService, reserve/promote the active first-campaign request, then atomically set both durable locations and `checkpoint_id=CHECKPOINT_AFTER_NAME`. Simulation staging or prepublish address-conflict failure returns to name/title respectively with no half-initialized runtime. A later EEPROM write/verify failure offers immutable Retry or explicit Return to Title; it never pretends persistence or continues an unpersisted campaign.

`checkpoint_id` is always serialized and selects the exact semantic resume recipe. A checkpoint save requires the table's exact current tuple and its `SaveableLocationDef`. Dismissal of `PELL_TRACE_004` promotes/writes `CHECKPOINT_ANNEX_TRACE_COMPLETE` at its exact atrium tuple. A later manual Relay save may retain that recipe while setting both current and last-safe to another condition-valid `SAVELOC_MANUAL_ALLOWED` row; the manual-variant validator explicitly requires `annex_exit_cleared=false` and Find Tavi active for that post-trace recipe. First confirmed departure then promotes/writes `CHECKPOINT_ANNEX_DEPARTURE` at the exact threshold tuple with `annex_exit_cleared=true`. Other manual saves retain the latest checkpoint ID/required facts and may replace current/last-safe only with a stable registry row legal for that story state. Decode validates both the checkpoint recipe and registry legality. Every `CHECKPOINT_TAVI_FOUND`, `CHECKPOINT_TAVI_RETURNED`, and `CHECKPOINT_SLICE_COMPLETE` page requires `FLAG_ORRERY_STAIR_OPEN`; every manual variant carrying `FLAG_TAVI_FOUND` requires it as well.

`last_save_reason` records the operation that committed the newest page and follows one exact dispatch. Automatic milestone saves for After Name, After Tutorial, Field Relay, Annex Trace Complete, Annex Departure, Estate Arrival, Tavi Found, and Tavi Returned write `SAVE_REASON_CHECKPOINT`. The Rusk victory and defeat-menu Return pages write `SAVE_REASON_BATTLE_RESULT`. `HOOK_014` writes `SAVE_REASON_FINAL_HOOK` with `CHECKPOINT_SLICE_COMPLETE` before the end-card transition. A player Relay save writes `SAVE_REASON_MANUAL_RELAY`. A stable door/world transition that writes without promoting a milestone writes `SAVE_REASON_TRANSITION`. Pause Settings Apply on initialized stable progress writes `SAVE_REASON_SETTINGS`. Title Apply is always process-profile-only and never writes EEPROM; New Game copies that profile into its draft, while Continue applies it after decode and marks runtime dirty when it differs from persisted settings. The queue never coalesces or overwrites an immutable request: each committed page records that request's actual reason, and a later queued request records its own reason only if it separately reaches COMMITTED. Debounce is non-lossy and identity-based: one generation-bound producer event/input epoch may reserve at most one request; duplicate/stale epochs cannot enqueue, BUSY_RETRY reuses the same unpublished producer transaction, and Manual/Settings requires a fresh debounced user edge after any terminal outcome.

Decode rejects `SAVE_REASON_NONE` on every initialized page. `SAVE_REASON_CHECKPOINT` requires the exact checkpoint tuple and disallows the Rusk victory, Rusk Return, and Slice Complete recipes; `SAVE_REASON_BATTLE_RESULT` requires checkpoint Rusk Victory with `BATTLE_RESULT_WIN` or checkpoint Rusk Return with `BATTLE_RESULT_RETURN_TO_ANNEX`; `SAVE_REASON_FINAL_HOOK` requires checkpoint Slice Complete and all final-hook equivalences. `SAVE_REASON_MANUAL_RELAY` semantically requires `FLAG_FIELD_RELAY_UNLOCKED`, all four Relay page bits, and a condition-valid `SAVELOC_MANUAL_ALLOWED` current tuple. `SAVE_REASON_TRANSITION` requires a condition-valid transition destination/source-safe registry tuple with no checkpoint promotion in that transaction. `SAVE_REASON_SETTINGS` requires initialized progress, sanitized settings, and condition-valid current/last-safe registry tuples; its current tuple may be any `SAVELOC_CONTINUE_ALLOWED` row, including `SAVELOC_SIM_INTRO`. At `SAVELOC_SIM_INTRO`, Pause Settings can open only from a tutorial pause-safe command boundary with no action, presentation, result, or tutorial-gate transaction live; the settings-only page retains the After-Name checkpoint and restart-at-intro semantics and never serializes a partial battle. The checkpoint identity remains independently validated because later manual/transition/settings saves may retain it.

Historical UI provenance is encode-time evidence and is not claimed by reboot decode. A `SAVE_REASON_MANUAL_RELAY` request validator requires the player-owned Relay save surface, unlocked Relay/page bits, modal closure, stable control, and `SAVELOC_MANUAL_ALLOWED`. Pause Settings Apply requires the Pause settings origin, an initialized campaign, stable control, and condition-valid current/last-safe rows with the current row marked `SAVELOC_CONTINUE_ALLOWED`; it copies only sanitized settings. `SAVELOC_SIM_INTRO` additionally requires the tutorial pause-safe boundary above, while exploration rows must also be `SAVELOC_MANUAL_ALLOWED`. Title Settings Apply never creates a SaveRequest: it updates one sanitized process-profile generation. New Game copies the profile into RuntimeDraftOwner; Title Continue decodes the page first, then overlays the profile and sets DIRTY iff any of the eight settings bytes differ, leaving the decoded SaveReason unchanged. Request-origin tokens are generation-bound and discarded after enqueue; they are never serialized.

Defeat itself is not a stable page. Choosing Return to Annex restores `PRE_RUSK_BATTLE_SNAPSHOT`, performs a normal transition to `SCENE_ANNEX_INTERIOR / ZONE_ANNEX_THRESHOLD / SPAWN_ANNEX_THRESHOLD_DEPARTURE`, preserves `estate_arrived`, `rusk_confrontation_seen`, and the active Find Tavi objective, leaves all Rusk win/reward/door facts false, then atomically writes `checkpoint_id=CHECKPOINT_RUSK_RETURN_TO_ANNEX`, `last_save_reason=SAVE_REASON_BATTLE_RESULT`, `last_battle_result=BATTLE_RESULT_RETURN_TO_ANNEX`, `last_encounter_id=ENCOUNTER_RUSK_COURTYARD`, and the threshold tuple as both current/last-safe. `BATTLE_RESULT_WIN` requires the Rusk stable equivalences plus `last_encounter_id=ENCOUNTER_RUSK_COURTYARD`; Return requires the exact recipe/facts above; `BATTLE_RESULT_DEFEAT` is invalid in a persistent opening-chapter page; `BATTLE_RESULT_NONE` and encounter 0 initialize before the real battle and are rejected after a stable win/return.

## 10. Settings

```c
enum CameraSettingFlags {
    CAMERA_INVERT_X = 1u << 0,
    CAMERA_INVERT_Y = 1u << 1
};

typedef struct GameSettings {
    uint8_t text_speed;     /* 0: slow=0, normal=1, fast=2 */
    uint8_t camera_flags;   /* 1 */
    uint8_t music_volume;   /* 2: range 0..100 */
    uint8_t sfx_volume;     /* 3: range 0..100 */
    uint8_t rumble_enabled; /* 4: exact 0 or 1 */
    uint8_t overscan_x;     /* 5: range 0..8 */
    uint8_t overscan_y;     /* 6: range 0..8 */
    uint8_t ui_contrast;    /* 7: standard=0, high=1, reduced flash=2 */
} GameSettings;
_Static_assert(sizeof(GameSettings) == 8, "GameSettings layout");

typedef enum SettingsFieldIdValue {
    SETTINGS_FIELD_TEXT_SPEED = 1,
    SETTINGS_FIELD_CAMERA_FLAGS = 2,
    SETTINGS_FIELD_MUSIC_VOLUME = 3,
    SETTINGS_FIELD_SFX_VOLUME = 4,
    SETTINGS_FIELD_RUMBLE_ENABLED = 5,
    SETTINGS_FIELD_OVERSCAN_X = 6,
    SETTINGS_FIELD_OVERSCAN_Y = 7,
    SETTINGS_FIELD_UI_CONTRAST = 8
} SettingsFieldIdValue;

typedef enum SettingsEditRuleValue {
    SETTINGS_EDIT_WRAP = 1,
    SETTINGS_EDIT_CLAMP = 2,
    SETTINGS_EDIT_TOGGLE_MASK = 3
} SettingsEditRuleValue;

typedef enum SettingsPreviewRouteValue {
    SETTINGS_PREVIEW_TEXT_SAMPLE = 1,
    SETTINGS_PREVIEW_CAMERA_ORBIT = 2,
    SETTINGS_PREVIEW_MUSIC_BUS = 3,
    SETTINGS_PREVIEW_SFX_SAMPLE = 4,
    SETTINGS_PREVIEW_RUMBLE_PULSE = 5,
    SETTINGS_PREVIEW_SAFE_FRAME = 6,
    SETTINGS_PREVIEW_UI_PALETTE = 7
} SettingsPreviewRouteValue;

enum SettingsFieldFlags {
    SETTINGS_FIELD_LIVE_PREVIEW = 1u << 0,
    SETTINGS_FIELD_RESETTABLE = 1u << 1,
    SETTINGS_FIELD_CAMPAIGN_SERIALIZED = 1u << 2
};

typedef struct SettingsFieldDef {
    StringId label_string_id; /* 0: ProcessStaticStringIdValue */
    uint8_t field_id;         /* 2: SettingsFieldIdValue */
    uint8_t byte_offset;      /* 3: exact GameSettings byte */
    uint8_t default_value;    /* 4 */
    uint8_t min_value;        /* 5 */
    uint8_t max_value;        /* 6 */
    uint8_t step;             /* 7: zero only for bit-mask controls */
    uint8_t first_control;    /* 8: index into SettingsEditControlDef */
    uint8_t control_count;    /* 9: one, except camera flags has two */
    uint8_t preview_route;    /* 10: SettingsPreviewRouteValue */
    uint8_t flags;            /* 11: SettingsFieldFlags */
} SettingsFieldDef;
_Static_assert(sizeof(SettingsFieldDef) == 12, "SettingsFieldDef layout");

typedef struct SettingsEditControlDef {
    StringId label_string_id; /* 0: ProcessStaticStringIdValue */
    uint8_t field_id;         /* 2: SettingsFieldIdValue */
    uint8_t edit_order;       /* 3: exact focus order 0..8 */
    uint8_t edit_rule;        /* 4: SettingsEditRuleValue */
    uint8_t value_mask;       /* 5: nonzero only for TOGGLE_MASK */
    uint8_t step_xref;        /* 6: equality mirror of field step; zero for mask */
    uint8_t reserved0;        /* 7: zero */
    uint16_t reserved1;       /* 8: zero */
} SettingsEditControlDef;
_Static_assert(sizeof(SettingsEditControlDef) == 10, "SettingsEditControlDef layout");

enum SettingsValueLabelFlags {
    SETTINGS_VALUE_COMPARE_CONTROL_BIT = 1u << 0,
    SETTINGS_VALUE_COMPARE_WHOLE_FIELD = 1u << 1
};

typedef struct SettingsValueLabelDef {
    uint8_t control_index;    /* 0: SettingsFocusValue 0..8 */
    uint8_t value;            /* 1: whole value or normalized bit */
    StringId string_id;       /* 2: ProcessStaticStringIdValue */
    uint16_t flags;           /* 4: SettingsValueLabelFlags */
    uint16_t reserved;        /* 6: zero */
} SettingsValueLabelDef;
_Static_assert(sizeof(SettingsValueLabelDef) == 8, "SettingsValueLabelDef layout");

typedef enum SettingsEditOriginValue {
    SETTINGS_ORIGIN_TITLE = 1,
    SETTINGS_ORIGIN_PAUSE = 2
} SettingsEditOriginValue;

typedef enum SettingsEditSessionStateValue {
    SETTINGS_SESSION_EDITING = 1,
    SETTINGS_SESSION_WAITING_FOR_SAVE_SLOT = 2,
    SETTINGS_SESSION_SAVE_ACTIVE = 3
} SettingsEditSessionStateValue;

typedef enum SettingsFocusValue {
    SETTINGS_FOCUS_TEXT_SPEED = 0,
    SETTINGS_FOCUS_INVERT_X = 1,
    SETTINGS_FOCUS_INVERT_Y = 2,
    SETTINGS_FOCUS_MUSIC_VOLUME = 3,
    SETTINGS_FOCUS_SFX_VOLUME = 4,
    SETTINGS_FOCUS_RUMBLE = 5,
    SETTINGS_FOCUS_OVERSCAN_X = 6,
    SETTINGS_FOCUS_OVERSCAN_Y = 7,
    SETTINGS_FOCUS_UI_CONTRAST = 8,
    SETTINGS_FOCUS_RESET_DEFAULTS = 9,
    SETTINGS_FOCUS_APPLY = 10,
    SETTINGS_FOCUS_CANCEL = 11
} SettingsFocusValue;

typedef struct SettingsEditSessionOwner {
    GameSettings base_settings;                  /* 0: exact pre-edit bytes */
    GameSettings scratch_settings;               /* 8: sanitized candidate */
    uint32_t generation;                         /* 16: nonzero UI generation */
    uint32_t source_profile_generation;          /* 20 */
    uint32_t source_campaign_owner_generation;   /* 24: zero at Title */
    uint32_t source_runtime_settings_generation; /* 28: zero at Title */
    uint8_t origin;                              /* 32: SettingsEditOriginValue */
    uint8_t state;                               /* 33: SettingsEditSessionStateValue */
    uint8_t focused_entry;                       /* 34: SettingsFocusValue */
    uint8_t reserved;                            /* 35: zero */
    ProcessUiOriginSnapshot return_origin;       /* 36: same-generation companion */
} SettingsEditSessionOwner;
_Static_assert(sizeof(SettingsEditSessionOwner) == 60, "SettingsEditSessionOwner layout");

typedef enum SettingsProfileSourceValue {
    SETTINGS_PROFILE_BOOT_DEFAULT_OR_SALVAGE = 1,
    SETTINGS_PROFILE_BOOT_SELECTED_PAGE = 2,
    SETTINGS_PROFILE_TITLE_APPLY = 3,
    SETTINGS_PROFILE_CAMPAIGN_SETTINGS_COMMIT = 4
} SettingsProfileSourceValue;

typedef struct SettingsProfileOwner {
    GameSettings settings;                    /* 0: always sanitized */
    uint32_t generation;                      /* 8: nonzero process-lifetime serial */
    uint32_t campaign_owner_generation;       /* 12: nonzero only for campaign commit */
    uint32_t runtime_settings_generation;     /* 16: nonzero only for campaign commit */
    uint8_t source;                           /* 20: SettingsProfileSourceValue */
    uint8_t reserved0[3];                     /* 21: zero */
} SettingsProfileOwner;
_Static_assert(sizeof(SettingsProfileOwner) == 24, "SettingsProfileOwner layout");
```

The default vector is exactly `{ 1, 0, 80, 80, 1, 0, 0, 0 }` in
`GameSettings` byte order. The eight field rows are literal and set-equal with
the eight bytes; every row carries all three field flags:

| SettingsFieldId / label | byte | default / min / max / step | first control / count | preview |
|---|---:|---|---|---|
| `SETTINGS_FIELD_TEXT_SPEED / STR_SETTINGS_TEXT_SPEED` | `0` | `1 / 0 / 2 / 1` | `0 / 1` | `SETTINGS_PREVIEW_TEXT_SAMPLE` |
| `SETTINGS_FIELD_CAMERA_FLAGS / STR_SETTINGS_CAMERA` | `1` | `0 / 0 / 3 / 0` | `1 / 2` | `SETTINGS_PREVIEW_CAMERA_ORBIT` |
| `SETTINGS_FIELD_MUSIC_VOLUME / STR_SETTINGS_MUSIC_VOLUME` | `2` | `80 / 0 / 100 / 10` | `3 / 1` | `SETTINGS_PREVIEW_MUSIC_BUS` |
| `SETTINGS_FIELD_SFX_VOLUME / STR_SETTINGS_SFX_VOLUME` | `3` | `80 / 0 / 100 / 10` | `4 / 1` | `SETTINGS_PREVIEW_SFX_SAMPLE` |
| `SETTINGS_FIELD_RUMBLE_ENABLED / STR_SETTINGS_RUMBLE` | `4` | `1 / 0 / 1 / 0` | `5 / 1` | `SETTINGS_PREVIEW_RUMBLE_PULSE` |
| `SETTINGS_FIELD_OVERSCAN_X / STR_SETTINGS_OVERSCAN_X` | `5` | `0 / 0 / 8 / 1` | `6 / 1` | `SETTINGS_PREVIEW_SAFE_FRAME` |
| `SETTINGS_FIELD_OVERSCAN_Y / STR_SETTINGS_OVERSCAN_Y` | `6` | `0 / 0 / 8 / 1` | `7 / 1` | `SETTINGS_PREVIEW_SAFE_FRAME` |
| `SETTINGS_FIELD_UI_CONTRAST / STR_SETTINGS_UI_CONTRAST` | `7` | `0 / 0 / 2 / 1` | `8 / 1` | `SETTINGS_PREVIEW_UI_PALETTE` |

The nine controls are also literal. Left subtracts and Right adds the referenced
step under WRAP or CLAMP. For TOGGLE_MASK, Left, Right, or A XORs the exact
mask; there is no arithmetic interpretation. Camera X/Y therefore remain two
separately focusable controls over one serialized byte, and rumble remains one
boolean control.

| index / label | field | rule / mask / step xref |
|---:|---|---|
| `0 / STR_SETTINGS_TEXT_SPEED` | `SETTINGS_FIELD_TEXT_SPEED` | `WRAP / 0 / 1` |
| `1 / STR_SETTINGS_INVERT_X` | `SETTINGS_FIELD_CAMERA_FLAGS` | `TOGGLE_MASK / CAMERA_INVERT_X / 0` |
| `2 / STR_SETTINGS_INVERT_Y` | `SETTINGS_FIELD_CAMERA_FLAGS` | `TOGGLE_MASK / CAMERA_INVERT_Y / 0` |
| `3 / STR_SETTINGS_MUSIC_VOLUME` | `SETTINGS_FIELD_MUSIC_VOLUME` | `CLAMP / 0 / 10` |
| `4 / STR_SETTINGS_SFX_VOLUME` | `SETTINGS_FIELD_SFX_VOLUME` | `CLAMP / 0 / 10` |
| `5 / STR_SETTINGS_RUMBLE` | `SETTINGS_FIELD_RUMBLE_ENABLED` | `TOGGLE_MASK / 1 / 0` |
| `6 / STR_SETTINGS_OVERSCAN_X` | `SETTINGS_FIELD_OVERSCAN_X` | `CLAMP / 0 / 1` |
| `7 / STR_SETTINGS_OVERSCAN_Y` | `SETTINGS_FIELD_OVERSCAN_Y` | `CLAMP / 0 / 1` |
| `8 / STR_SETTINGS_UI_CONTRAST` | `SETTINGS_FIELD_UI_CONTRAST` | `WRAP / 0 / 1` |

```c
static const SettingsValueLabelDef SETTINGS_VALUE_LABELS[12] = {
    { SETTINGS_FOCUS_TEXT_SPEED, 0, STR_VALUE_SLOW, SETTINGS_VALUE_COMPARE_WHOLE_FIELD, 0 },
    { SETTINGS_FOCUS_TEXT_SPEED, 1, STR_VALUE_NORMAL, SETTINGS_VALUE_COMPARE_WHOLE_FIELD, 0 },
    { SETTINGS_FOCUS_TEXT_SPEED, 2, STR_VALUE_FAST, SETTINGS_VALUE_COMPARE_WHOLE_FIELD, 0 },
    { SETTINGS_FOCUS_INVERT_X, 0, STR_VALUE_OFF, SETTINGS_VALUE_COMPARE_CONTROL_BIT, 0 },
    { SETTINGS_FOCUS_INVERT_X, 1, STR_VALUE_ON, SETTINGS_VALUE_COMPARE_CONTROL_BIT, 0 },
    { SETTINGS_FOCUS_INVERT_Y, 0, STR_VALUE_OFF, SETTINGS_VALUE_COMPARE_CONTROL_BIT, 0 },
    { SETTINGS_FOCUS_INVERT_Y, 1, STR_VALUE_ON, SETTINGS_VALUE_COMPARE_CONTROL_BIT, 0 },
    { SETTINGS_FOCUS_RUMBLE, 0, STR_VALUE_OFF, SETTINGS_VALUE_COMPARE_WHOLE_FIELD, 0 },
    { SETTINGS_FOCUS_RUMBLE, 1, STR_VALUE_ON, SETTINGS_VALUE_COMPARE_WHOLE_FIELD, 0 },
    { SETTINGS_FOCUS_UI_CONTRAST, 0, STR_VALUE_STANDARD, SETTINGS_VALUE_COMPARE_WHOLE_FIELD, 0 },
    { SETTINGS_FOCUS_UI_CONTRAST, 1, STR_VALUE_HIGH, SETTINGS_VALUE_COMPARE_WHOLE_FIELD, 0 },
    { SETTINGS_FOCUS_UI_CONTRAST, 2, STR_VALUE_REDUCED_FLASH, SETTINGS_VALUE_COMPARE_WHOLE_FIELD, 0 }
};
```

Music and SFX render the sanitized integer followed by `%`; Overscan X/Y render
the sanitized integer followed by ` px`. Those four numeric formatters are
fixed, locale-independent ASCII and have no alternate label table. Every
non-numeric control must resolve exactly one `SETTINGS_VALUE_LABELS` row for its
current whole value or normalized selected bit; raw enum integers are never
shown to the player.

Every accepted edit updates only `scratch_settings`, then previews that one
field immediately: text changes the panel sample's typewriter cadence; camera
flags rotate the preview model without touching gameplay camera ownership;
music changes the preview/mixer bus; SFX plays at most one edge-triggered sample
per accepted change; rumble emits at most one six-tick test pulse on a connected
supporting controller; either overscan value moves the safe-frame guide; and
contrast swaps the panel palette/reduced-flash treatment. Preview state is
owned by the session and cannot survive close. `RESET DEFAULTS` copies the exact
eight-byte default vector to scratch and refreshes preview routes once in field
order without applying or saving. Up/Down follows control order `0..8`, then
`RESET DEFAULTS`, `APPLY`, `CANCEL`; it does not wrap from Cancel to the first
field. B is exactly Cancel from every focus.

Opening from Title captures `SettingsProfileOwner.settings/generation`; opening
from Pause captures live sanitized settings, campaign generation, runtime
settings generation, and a `ProcessUiOriginSnapshot` embedded in the same
`SettingsEditSessionOwner`. Its campaign, source-owner, and owner-generation
fields must each match their corresponding live owner at capture and again at
close; those independent serial domains are never compared to the settings
session generation. The snapshot is exclusively owned by that session. Title
uses a typed Title origin with campaign zero. The snapshot is destroyed with
the session and can neither be reused nor shared by another child. `CANCEL`
restores the preview from `base_settings`, destroys the session, and returns to
the captured Title/Pause owner and focus without changing a profile, runtime
generation, dirty bit, or EEPROM. Title `APPLY` sanitizes scratch, atomically
copies it into `SettingsProfileOwner`, advances the profile generation with
`SETTINGS_PROFILE_TITLE_APPLY`, destroys the session, and returns to Title; it
cannot enter SaveService. Pause `APPLY` must first obtain the exact user save
reservation described below. BUSY retains the session, disables every edit and
close action, shows the SaveService writing layer, and returns to EDITING with
one discarded poll when a slot releases. Only after reservation may it publish
the candidate runtime settings/temporary `SAVE_REASON_SETTINGS`, close edit
focus, and enter SAVE_ACTIVE. Failure Retry/Cancel and verified commit use the
existing immutable-request restoration/profile rules; no UI path can update the
process profile before the matching COMMITTED reconciliation.

Each byte is sanitized independently: text speed and contrast use defaults when outside their enums; camera flags are masked to the two known bits; volumes clamp to 100; rumble normalizes to 0/1; overscan clamps to 8. Before name confirmation, title settings live only in a runtime profile and are not evidence of persistence. The first initialized `CHECKPOINT_AFTER_NAME` copies the sanitized profile into `SaveData`.

`SettingsProfileOwner` is the sole process authority copied over a decoded page by Title Continue. Boot always creates generation 1. If the loader selects a supported semantically valid progression page, that selected page's sanitized eight settings bytes take precedence over every `GS` capsule and seed `SETTINGS_PROFILE_BOOT_SELECTED_PAGE`; this prevents a stale best-effort capsule from overriding a newer durable page. Only when no supported page is selected may a CRC-valid `GS` capsule seed `SETTINGS_PROFILE_BOOT_DEFAULT_OR_SALVAGE`. If that capsule is absent/invalid, the loader may salvage bytes `0x60..0x67` only from one unambiguously newest envelope-valid page with a known payload layout; equal-divergent or half-range candidates are not guessed. Otherwise defaults seed the same source state. Salvage preserves bad pages, does not set `initialized`, expose Continue, or write EEPROM. Unknown/out-of-range fields never make invalid progression valid.

Title Apply copies sanitized scratch bytes and advances the profile generation with source `SETTINGS_PROFILE_TITLE_APPLY`, leaving both campaign fields zero. In campaign play, Pause Settings does not mutate the process profile at candidate publish time. Only a verified `SAVE_REASON_SETTINGS` COMMITTED result may publish `SETTINGS_PROFILE_CAMPAIGN_SETTINGS_COMMIT`, and only when campaign generation/seed, candidate runtime/settings generations, exact candidate bytes, and current reconciliation all still match. It atomically copies the committed settings and advances the profile generation before Save Done becomes visible. A failed request leaves the profile untouched; Cancel restores runtime settings from the request and therefore needs no profile rollback. A stale or historical commit can update neither profile nor `GS`. Return-to-Title never guesses or resynchronizes from an unverified runtime: a later Continue therefore overlays the last Title preference or current campaign-committed Pause preference, never an obsolete one.

## 11. EEPROM4K journal

### 11.1 Entire 512-byte map

| Offset | Bytes | Region |
|---:|---:|---|
| `0x000` | 32 | global header |
| `0x020` | 240 | journal page A |
| `0x110` | 240 | journal page B |
| total | 512 | exact EEPROM4K capacity |

Every offset and length is divisible by the EEPROM 8-byte block size where a write phase requires it.

### 11.2 Global header, 32 bytes

| Relative offset | Bytes | Encoding |
|---:|---:|---|
| `0x00` | 4 | ASCII `N64G` |
| `0x04` | 2 | layout version, big-endian; current `2` |
| `0x06` | 2 | header bytes; exactly `32` |
| `0x08` | 4 | nonzero install nonce |
| `0x0C` | 1 | active-page hint: `0`, `1`, or `0xFF`; never authoritative |
| `0x0D` | 1 | global flags; current bits zero |
| `0x0E` | 2 | ASCII `GS` when independent settings capsule is valid; zero when absent |
| `0x10` | 8 | sanitized `GameSettings` compatibility bytes |
| `0x18` | 4 | CRC-32 of bytes `0x0E..0x17`; zero when capsule absent |
| `0x1C` | 4 | CRC-32 of bytes `0x00..0x1B` |

If this header is corrupt, both pages are still validated and recovered independently. The install nonce is diagnostic; it does not encrypt or authorize data. The independent settings capsule is a salvage fallback, never newer authority than a selected supported page. It is written best-effort only after a successfully committed initialized page whose request still matches the current campaign owner/seed, whose captured semantic generation byte-reconciles with current progress, and whose reread page is the unambiguously newest selected page. Pre-name Title changes, stale callbacks, historical campaign commits, and non-current queued successes never update it. If no supported page is selected, the capsule may preserve validated/clamped settings without interpreting an unknown page. When it is unavailable, only one unambiguously newest envelope-valid page with a known payload layout may offer the eight bytes at `0x60`; otherwise defaults are used.

### 11.3 Journal page, 240 bytes each

| Relative offset | Bytes | Encoding |
|---:|---:|---|
| `0x00` | 4 | ASCII `SAVE` |
| `0x04` | 2 | payload schema version; current `1` |
| `0x06` | 2 | payload bytes; exactly `216` |
| `0x08` | 4 | monotonically incrementing sequence |
| `0x0C` | 4 | header CRC-32 of page bytes `0x00..0x0B` |
| `0x10` | 216 | payload |
| `0xE8` | 4 | CRC-32 of exactly the 216 payload bytes |
| `0xEC` | 4 | ASCII commit marker `COMT` |
| total | 240 | exact page size |

CRC is CRC-32/ISO-HDLC: reflected polynomial `0xEDB88320`, initial value `0xFFFFFFFF`, final XOR `0xFFFFFFFF`, no inclusion of the stored CRC field. Golden test vector ASCII `123456789` must yield `0xCBF43926`.

A progression page is valid only when magic, supported schema, exact payload length, commit marker, header CRC, payload CRC, and semantic payload invariants all pass. Sequence comparison is portable unsigned arithmetic: `delta = a_sequence - b_sequence` in `uint32_t`; equal iff `delta==0`, half-range ambiguous iff `delta==0x80000000u`, A is newer iff `0 < delta && delta < 0x80000000u`, otherwise B is newer. No signed conversion is used. Equality may use the active hint only when both complete page bytes are identical. Equal-divergent or exact half-range pages are AMBIGUOUS: the loader selects no progression page, exposes no Continue/runtime state, preserves both, and maps Title to the explicit invalid/incompatible New Game diagnostic. Page A is only a deterministic overwrite anchor after fresh user confirmation; it is never called selected progress. If an envelope-valid page has a newer unsupported schema and a newer sequence than a supported page, boot reports an incompatible save rather than silently rolling progress back to the older page. Settings salvage follows the separate field policy in section 10 and never changes this validity result.

Sequence assignment uses the same envelope ordering before any destination page
is invalidated. An **envelope-valid** page has valid page magic, fixed envelope
length, header CRC, payload CRC/footer commit, and a self-consistent declared
payload length even when its payload schema is newer and semantically
unsupported. The writer selects one anchor and the other page as destination:

| Current page classes | Anchor / destination | Next sequence |
|---|---|---|
| one envelope-valid, one invalid | valid page / invalid page | `anchor + 1` modulo `2^32` |
| two envelope-valid with an unambiguous newer sequence | newer page / older page | `anchor + 1` modulo `2^32` |
| equal sequence and byte-identical envelopes | valid active hint, otherwise A / other page | `anchor + 1` modulo `2^32` |
| equal sequence but divergent envelopes | A / B, only after reporting ambiguity and receiving explicit overwrite/New Game confirmation | `A + 1` modulo `2^32` |
| no envelope-valid page | none / A | `1` |
| difference exactly `0x80000000` | no automatic anchor or write; explicit overwrite/New Game confirmation selects A / B | `A + 1` modulo `2^32` |

Normal checkpoint/manual/transition/settings writes are forbidden for an equal-
divergent or half-range-ambiguous pair. User-confirmed New Game includes every
preserved envelope-valid unsupported page in anchor selection, so a newer
incompatible page cannot remain newer than the replacement. The destination is
always the non-anchor page and the anchor bytes remain untouched until the new
commit verifies. After an explicit ambiguity overwrite, the old A anchor plus
new B page form an unambiguous adjacent pair. Addition is unsigned; sequence
`0xFFFFFFFF` advances to `0`, which the stated comparator treats as newer by one.
The active-page hint is updated best-effort only after page commit and never
changes ordering. Goldens cover invalid+invalid, valid+invalid, supported+
newer-incompatible, two incompatible pages, equal-identical with each hint,
equal-divergent, exact half-range difference, and `0xFFFFFFFF -> 0`.

The write protocol first writes an all-zero final 8-byte footer to invalidate the destination page, writes/re-reads header and payload blocks, verifies both CRCs from EEPROM, and writes the payload CRC plus `COMT` together as the final 8-byte commit. The old valid page is untouched until a later successful save.

### 11.4 Payload schema v1, exactly 216 bytes

| Offset | Bytes | Field |
|---:|---:|---|
| `0x00` | 2 | payload minor version, current `0` |
| `0x02` | 1 | player-name length `1..8` |
| `0x03` | 1 | progress flags; bit 0 initialized, all others zero |
| `0x04` | 8 | player name, uppercase ASCII `A-Z`; unused bytes zero |
| `0x0C` | 2 | current `SceneId` |
| `0x0E` | 2 | current `ZoneId` |
| `0x10` | 2 | current `SpawnId` |
| `0x12` | 2 | last-safe `SceneId` |
| `0x14` | 2 | last-safe `ZoneId` |
| `0x16` | 2 | last-safe `SpawnId` |
| `0x18` | 4 | active-play seconds; saturating, idle/reconnect pause excluded |
| `0x1C` | 4 | nonzero campaign seed |
| `0x20` | 16 | 128 story-flag bits |
| `0x30` | 8 | objective states indexed by `ObjectiveId`; entry 0 remains locked |
| `0x38` | 2 | destination-unlock bits |
| `0x3A` | 2 | Field Relay page-unlock bits |
| `0x3C` | 2 | one-time battle/reward claim bits |
| `0x3E` | 2 | research/progression points |
| `0x40` | 8 | encounter-clear bits |
| `0x48` | 8 | one-time dialogue bits |
| `0x50` | 8 | examine-point bits |
| `0x58` | 8 | optional NPC one-shot bits |
| `0x60` | 8 | `GameSettings` bytes in declared order |
| `0x68` | 1 | party count `0..4` |
| `0x69` | 1 | left active party index or `0xFF` |
| `0x6A` | 1 | right active party index or `0xFF` |
| `0x6B` | 1 | Team Link value `0..1` in this chapter |
| `0x6C` | 4 | zero reserved/alignment |
| `0x70` | 64 | four 16-byte party slots |
| `0xB0` | 8 | quest counters, each saturating `uint8_t` |
| `0xB8` | 2 | typed `CheckpointId`; one of the eleven locked resume recipes |
| `0xBA` | 1 | `SaveReasonValue`; manual/checkpoint cause, not resume identity |
| `0xBB` | 1 | `BattleResultValue`: 0 none, 1 win, 2 defeat, 3 Return to Annex |
| `0xBC` | 2 | active `ObjectiveId` or 0 |
| `0xBE` | 2 | last `EncounterId` or 0 |
| `0xC0` | 2 | chapter progression total |
| `0xC2` | 22 | zero reserved for migration |
| total | 216 | exact payload length `0xD8` |

Player name confirmation rejects an empty buffer and any byte outside `A-Z`; default is length 3, bytes `ARI`. A new game before name confirmation may exist only in runtime and is not saved as initialized progress.

### 11.5 Party slot, 16 bytes

| Relative offset | Bytes | Field |
|---:|---:|---|
| `0x00` | 2 | `CreatureId`; 0 means empty slot |
| `0x02` | 1 | level `1..99` for a filled slot |
| `0x03` | 1 | progression rank |
| `0x04` | 2 | experience, saturating |
| `0x06` | 2 | current HP |
| `0x08` | 2 | individual Sync `0..1000` |
| `0x0A` | 1 | move unlock mask; low four bits only |
| `0x0B` | 1 | slot flags; current bits zero |
| `0x0C` | 4 | nonzero personal deterministic seed |

```c
typedef struct PartySlot {
    CreatureId creature_id;   /* 0 */
    uint8_t level;             /* 2 */
    uint8_t progression_rank;  /* 3 */
    uint16_t experience;       /* 4 */
    uint16_t current_hp;       /* 6 */
    uint16_t sync;             /* 8 */
    uint8_t move_unlock_mask;  /* 10 */
    uint8_t flags;             /* 11 */
    uint32_t personal_seed;    /* 12 */
} PartySlot;
_Static_assert(sizeof(PartySlot) == 16, "PartySlot runtime layout");
```

The codec writes fields, not this struct. Empty slots are all-zero. Filled creature IDs are unique, current HP cannot exceed the level-derived maximum, and active indices are distinct, within party count, and refer to living slots. The exact empty-party invariant is `party_count == 0` iff `active_left_index == 0xFF && active_right_index == 0xFF`; neither active index may be `0xFF` when `party_count != 0`. During the opening, `starter_team_received` requires exactly `ECHO_QUARRUNE` and `ECHO_AYSELOR`; before that flag, party count must be zero and both active indices must be `0xFF`. `ACTION_GRANT_PARTY / TEAM_REAL_STARTERS` stages the two filled slots, then atomically publishes `party_count=2`, `active_left_index=0`, `active_right_index=1`, and `team_link=0`; no observer can see the filled slots with absent active indices or vice versa. Temporary battle statuses are never saved. Codec goldens lock the After-Name empty tuple, the starter `2/0/1` tuple, and rejection of zero-filled `0/0/0`, half-absent, equal, dead, or out-of-range active indices.

### 11.6 Save migration and corruption behavior

Each schema has a byte decoder into an intermediate versioned value, a semantic validator, and a field-by-field migrator into current `GameProgress`. There is no fallthrough cast. A newer schema is `INCOMPATIBLE`, not corrupt, and its bytes are preserved. A known older valid page migrates in RAM and is written as the new schema only at the next explicit stable save. Invalid/incompatible progression remains inaccessible and is never overwritten automatically; only a separately sanitized eight-byte settings profile may survive into a user-confirmed New Game.

Fault tests cover every EEPROM block failing before/after write, truncated reads, single-bit corruption in header/payload/footer, both page combinations, sequence wrap, equal divergent sequences, invalid uppercase/name padding, impossible location, flag implications, party duplicates/HP/active indices, unknown IDs, and reserved-byte policy.

## 12. Asset and bundle manifests

Runtime never performs string path lookup from gameplay logic. The asset compiler emits a manifest pack and generated IDs.

```c
typedef enum AssetType {
    ASSET_MODEL = 1,
    ASSET_ANIMATION_SET,
    ASSET_TEXTURE,
    ASSET_SPRITE,
    ASSET_FONT,
    ASSET_AUDIO,
    ASSET_COLLISION,
    ASSET_NAV_GRAPH,
    ASSET_DATA_TABLE,
    ASSET_CUTSCENE_VIDEO,
    ASSET_CUTSCENE_TIMELINE
} AssetType;

enum AssetFlags {
    ASSET_REQUIRED    = 1u << 0,
    ASSET_COMPRESSED  = 1u << 1,
    ASSET_RSP_VISIBLE = 1u << 2,
    ASSET_STREAMED    = 1u << 3,
    ASSET_UI_SHELL    = 1u << 4,
    ASSET_ACTION_ONLY = 1u << 5
};
```

UI screen IDs select compositions. `present.*` names are delivery/assembly aliases from the inventory, not automatically packed `AssetId`s; this table binds them to canonical runtime entries and makes multi-asset compositions explicit:

```c
typedef enum UIScreenIdValue {
    UI_SCREEN_NONE = 0,
    UI_SCREEN_STUDIO_MARK = 1,
    UI_SCREEN_TITLE = 2,
    UI_SCREEN_LOADING = 3,
    UI_SCREEN_CUTSCENE_SLATE = 4,
    UI_SCREEN_WORLD_ROUTE = 5,
    UI_SCREEN_SIM_REVEAL = 6,
    UI_SCREEN_CHAPTER_END = 7,
    UI_SCREEN_SETTINGS = 8,
    UI_SCREEN_NAME_ENTRY = 9,
    UI_SCREEN_PROCESS_SAFE_RECOVERY = 10,
    UI_SCREEN_PAUSE = 11,
    UI_SCREEN_RELAY_PARTY = 12,
    UI_SCREEN_RELAY_MESSAGES = 13,
    UI_SCREEN_RELAY_RESONANCE = 14,
    UI_SCREEN_RELAY_MAP = 15,
    UI_SCREEN_RELAY_SAVE = 16
} UIScreenIdValue;

typedef enum PresentationRuntimeAssetIdValue {
    ASSET_UI_SCREEN_STUDIO_MARK = 0x7001,
    ASSET_UI_SCREEN_TITLE_MARK = 0x7002,
    ASSET_UI_SCREEN_LOADING = 0x7003,
    ASSET_VFX_TRANSITION_LOADING_RELAY = 0x7004,
    ASSET_ANM_UI_LOADING_RELAY = 0x7005,
    ASSET_UI_SCREEN_CUTSCENE_SLATE = 0x7006,
    ASSET_VFX_TRANSITION_WORLD_ROUTE = 0x7007,
    ASSET_VFX_TRANSITION_SIM_DISSOLVE = 0x7008,
    ASSET_UI_SCREEN_CHAPTER_END = 0x7009,
    ASSET_UI_TITLE_MENU = 0x700A,
    ASSET_UI_WORLD_MAP_BASE = 0x700B,
    ASSET_UI_SIM_CHAMBER_BASE = 0x700C,
    ASSET_UI_SETTINGS_PANEL = 0x700D,
    ASSET_UI_CONTROLLER_ICONS = 0x700E,
    ASSET_UI_SCREEN_NAME_ENTRY = 0x700F,
    ASSET_UI_PROCESS_SAFE_RECOVERY = 0x7010,
    ASSET_UI_SCREEN_PAUSE = 0x7011,
    ASSET_UI_RELAY_SHELL = 0x7012,
    ASSET_UI_RELAY_PARTY = 0x7013,
    ASSET_UI_RELAY_MESSAGES = 0x7014,
    ASSET_UI_RELAY_RESONANCE = 0x7015,
    ASSET_UI_RELAY_MAP = 0x7016,
    ASSET_UI_RELAY_SAVE = 0x7017
} PresentationRuntimeAssetIdValue;

typedef struct UIScreenDef {
    UIScreenId id;                    /* 0 */
    AssetId base_asset_id;            /* 2 */
    AssetId overlay_asset_id;         /* 4 */
    AssetId animation_asset_id;       /* 6 */
    BundleId required_bundle_id;      /* 8 */
    uint16_t flags;                   /* 10 */
    uint8_t safe_margin_x;            /* 12 */
    uint8_t safe_margin_y;            /* 13 */
    uint16_t reserved;                /* 14 */
} UIScreenDef;
_Static_assert(sizeof(UIScreenDef) == 16, "UIScreenDef layout");

enum UIScreenFlags {
    UI_SCREEN_PROCESS_SHELL = 1u << 0,
    UI_SCREEN_ANIMATED = 1u << 1,
    UI_SCREEN_NON_SAVEABLE = 1u << 2,
    UI_SCREEN_CONTROLLER_MODAL = 1u << 3,
    UI_SCREEN_SCENE_COMPOSITE = 1u << 4
};
```

The shared UI load-manifest bundle is locked as `BUNDLE_UI_SHARED=0x680B`. The complete UIScreenDef table uses safe margins `16/12` pixels and zero reserved fields:

| UIScreenId | Base / overlay / animation AssetId | Required BundleId | Flags | margin x/y | reserved |
|---|---|---|---|---:|---:|
| `UI_SCREEN_STUDIO_MARK` | `ASSET_UI_SCREEN_STUDIO_MARK / 0 / 0` | `BUNDLE_UI_SHARED` | `UI_SCREEN_PROCESS_SHELL + UI_SCREEN_NON_SAVEABLE` | `16 / 12` | `0` |
| `UI_SCREEN_TITLE` | `ASSET_UI_SCREEN_TITLE_MARK / ASSET_UI_TITLE_MENU / 0` | `BUNDLE_UI_SHARED` | `UI_SCREEN_PROCESS_SHELL + UI_SCREEN_NON_SAVEABLE + UI_SCREEN_CONTROLLER_MODAL` | `16 / 12` | `0` |
| `UI_SCREEN_LOADING` | `ASSET_UI_SCREEN_LOADING / ASSET_VFX_TRANSITION_LOADING_RELAY / ASSET_ANM_UI_LOADING_RELAY` | `BUNDLE_UI_SHARED` | `UI_SCREEN_PROCESS_SHELL + UI_SCREEN_ANIMATED + UI_SCREEN_NON_SAVEABLE` | `16 / 12` | `0` |
| `UI_SCREEN_CUTSCENE_SLATE` | `ASSET_UI_SCREEN_CUTSCENE_SLATE / 0 / 0` | `BUNDLE_UI_SHARED` | `UI_SCREEN_PROCESS_SHELL + UI_SCREEN_ANIMATED + UI_SCREEN_NON_SAVEABLE + UI_SCREEN_CONTROLLER_MODAL` | `16 / 12` | `0` |
| `UI_SCREEN_WORLD_ROUTE` | `ASSET_UI_WORLD_MAP_BASE / ASSET_VFX_TRANSITION_WORLD_ROUTE / 0` | `BUNDLE_SCENE_MAP_SHELL` | `UI_SCREEN_ANIMATED + UI_SCREEN_NON_SAVEABLE + UI_SCREEN_SCENE_COMPOSITE` | `16 / 12` | `0` |
| `UI_SCREEN_SIM_REVEAL` | `ASSET_UI_SIM_CHAMBER_BASE / ASSET_VFX_TRANSITION_SIM_DISSOLVE / 0` | `BUNDLE_SCENE_SIM_SHELL` | `UI_SCREEN_ANIMATED + UI_SCREEN_NON_SAVEABLE + UI_SCREEN_SCENE_COMPOSITE` | `16 / 12` | `0` |
| `UI_SCREEN_CHAPTER_END` | `ASSET_UI_SCREEN_CHAPTER_END / 0 / 0` | `BUNDLE_SCENE_END_CHAPTER_SHELL` | `UI_SCREEN_NON_SAVEABLE + UI_SCREEN_CONTROLLER_MODAL` | `16 / 12` | `0` |
| `UI_SCREEN_SETTINGS` | `ASSET_UI_SETTINGS_PANEL / ASSET_UI_CONTROLLER_ICONS / 0` | `BUNDLE_UI_SHARED` | `UI_SCREEN_PROCESS_SHELL + UI_SCREEN_NON_SAVEABLE + UI_SCREEN_CONTROLLER_MODAL` | `16 / 12` | `0` |
| `UI_SCREEN_NAME_ENTRY` | `ASSET_UI_SCREEN_NAME_ENTRY / ASSET_UI_CONTROLLER_ICONS / 0` | `BUNDLE_UI_SHARED` | `UI_SCREEN_PROCESS_SHELL + UI_SCREEN_NON_SAVEABLE + UI_SCREEN_CONTROLLER_MODAL` | `16 / 12` | `0` |
| `UI_SCREEN_PROCESS_SAFE_RECOVERY` | `ASSET_UI_PROCESS_SAFE_RECOVERY / ASSET_UI_CONTROLLER_ICONS / 0` | `BUNDLE_UI_SHARED` | `UI_SCREEN_PROCESS_SHELL + UI_SCREEN_NON_SAVEABLE + UI_SCREEN_CONTROLLER_MODAL` | `16 / 12` | `0` |
| `UI_SCREEN_PAUSE` | `ASSET_UI_SCREEN_PAUSE / ASSET_UI_CONTROLLER_ICONS / 0` | `BUNDLE_UI_SHARED` | `UI_SCREEN_PROCESS_SHELL + UI_SCREEN_NON_SAVEABLE + UI_SCREEN_CONTROLLER_MODAL + UI_SCREEN_SCENE_COMPOSITE` | `16 / 12` | `0` |
| `UI_SCREEN_RELAY_PARTY` | `ASSET_UI_RELAY_SHELL / ASSET_UI_RELAY_PARTY / 0` | `BUNDLE_UI_SHARED` | `UI_SCREEN_PROCESS_SHELL + UI_SCREEN_NON_SAVEABLE + UI_SCREEN_CONTROLLER_MODAL + UI_SCREEN_SCENE_COMPOSITE` | `16 / 12` | `0` |
| `UI_SCREEN_RELAY_MESSAGES` | `ASSET_UI_RELAY_SHELL / ASSET_UI_RELAY_MESSAGES / 0` | `BUNDLE_UI_SHARED` | same Relay flags | `16 / 12` | `0` |
| `UI_SCREEN_RELAY_RESONANCE` | `ASSET_UI_RELAY_SHELL / ASSET_UI_RELAY_RESONANCE / 0` | `BUNDLE_UI_SHARED` | same Relay flags | `16 / 12` | `0` |
| `UI_SCREEN_RELAY_MAP` | `ASSET_UI_RELAY_SHELL / ASSET_UI_RELAY_MAP / 0` | `BUNDLE_UI_SHARED` | same Relay flags | `16 / 12` | `0` |
| `UI_SCREEN_RELAY_SAVE` | `ASSET_UI_RELAY_SHELL / ASSET_UI_RELAY_SAVE / 0` | `BUNDLE_UI_SHARED` | same Relay flags | `16 / 12` | `0` |

`UIScreenDef.flags` accepts only mask `0x001F` and must equal the row. A zero overlay/animation is deliberate; a nonzero field resolves and its corresponding composition/animated bit must be present. Missing/duplicate screens, non-`16/12` margins, unknown bits, or a bundle/asset mismatch fails generation.

| `UIScreenId` / source composition | Delivery alias | Canonical runtime AssetId binding / rule |
|---|---|---|
| `UI_SCREEN_STUDIO_MARK` / `ui.screen.studio_mark` | `present.studio_mark` | `ASSET_UI_SCREEN_STUDIO_MARK`; foreground over process-shell fade |
| `UI_SCREEN_TITLE` / `ui.screen.title_mark` + `ui.screen.title_menu` | `present.game_mark` | `ASSET_UI_SCREEN_TITLE_MARK` plus menu components |
| `UI_SCREEN_LOADING` / `ui.screen.loading` | `present.loading_backdrop`, `present.loading_indicator` | `ASSET_UI_SCREEN_LOADING` + `ASSET_VFX_TRANSITION_LOADING_RELAY` + `ASSET_ANM_UI_LOADING_RELAY` |
| `UI_SCREEN_CUTSCENE_SLATE` / `ui.screen.cutscene_slate` | `present.cutscene_slate` | `ASSET_UI_SCREEN_CUTSCENE_SLATE` |
| `UI_SCREEN_WORLD_ROUTE` / world-route composition | `present.world_route` | zone-owned world-map base + `ASSET_VFX_TRANSITION_WORLD_ROUTE`; alias itself has no AssetId |
| `UI_SCREEN_SIM_REVEAL` / simulation dissolve composition | `present.sim_dissolve` | `ASSET_VFX_TRANSITION_SIM_DISSOLVE` over retained chamber base |
| `UI_SCREEN_CHAPTER_END` / `ui.screen.chapter_end` | `present.chapter_end` | `ASSET_UI_SCREEN_CHAPTER_END` in UI-only bundle |
| `UI_SCREEN_SETTINGS` / `ui.screen.settings` | none | Relay-core atlas, body font, controller icons, ≤4 KiB preview media |
| `UI_SCREEN_NAME_ENTRY` / `ui.screen.name_entry` | none | `ASSET_UI_SCREEN_NAME_ENTRY` component set plus body font/controller icons; distinct from Title base |
| `UI_SCREEN_PROCESS_SAFE_RECOVERY` / `ui.screen.process_safe_recovery` | none | `ASSET_UI_PROCESS_SAFE_RECOVERY` component set plus body font/controller icons; process-owned and independent of scene assets |
| `UI_SCREEN_PAUSE` / `ui.screen.pause` | none | `ASSET_UI_SCREEN_PAUSE` plus controller icons; scene-composited process owner |
| `UI_SCREEN_RELAY_PARTY` / `ui.screen.relay_shell` + `ui.screen.relay_party` | none | common `ASSET_UI_RELAY_SHELL` plus the Party child |
| `UI_SCREEN_RELAY_MESSAGES` / `ui.screen.relay_shell` + `ui.screen.relay_messages` | none | common shell plus the Messages child |
| `UI_SCREEN_RELAY_RESONANCE` / `ui.screen.relay_shell` + `ui.screen.relay_resonance` | none | common shell plus the Resonance child |
| `UI_SCREEN_RELAY_MAP` / `ui.screen.relay_shell` + `ui.screen.relay_map` | none | common shell plus the Map child |
| `UI_SCREEN_RELAY_SAVE` / `ui.screen.relay_shell` + `ui.screen.relay_save` | none | common shell plus the Save child |

`ASSET_UI_SCREEN_NAME_ENTRY`, `ASSET_UI_PROCESS_SAFE_RECOVERY`,
`ASSET_UI_SCREEN_PAUSE`, and the six `ASSET_UI_RELAY_*` entries are generated
runtime children of their identically named existing inventory packages and are
owned only by `BUNDLE_UI_SHARED`; none adds a separate production/ledger row.
`BUNDLE_SCENE_NAME_SHELL` references the Name Entry child and shared font/icons.
The recovery child is resident with the process shell, never obtained from a
source or partially loaded destination scene. Reusing
`ASSET_UI_SCREEN_TITLE_MARK` as the name grid base, a missing parent mapping, a
NameEntry binding to `UI_SCREEN_TITLE`, or recovery UI that depends on scene
assets fails data and asset validation.

Pause and Relay are process-owned scene composites: their base/overlay children
remain in the shared UI bundle while the current scene stays retained and
frozen behind them. No page owns, reloads, or duplicates a scene asset. Every
Relay screen must use the one `ASSET_UI_RELAY_SHELL`; swapping a page overlay is
an atomic binding-state change that clears input and discards one poll frame.
The pre-Relay Party route may use `UI_SCREEN_RELAY_PARTY`, but it exposes only
the Party runtime view and locked tabs and does not grant Relay ownership or set
a persisted page bit.

The settings panel's component assets have one owning pack bundle, the process/UI-shell catalog (≤48 KiB total), and both title and Pause `UIScreenDef`s reference those same AssetIds through load manifests; neither scene owns a duplicate atlas or preview. Title Apply always changes only the sanitized process settings profile; it does not acquire SaveService, select a journal address, or claim persistence. New Game copies it into the first draft/page. Continue overlays it after validated decode and marks the runtime dirty iff it differs, so a later Pause/Manual/transition save can persist the change honestly. Pause edits mutate scratch settings; Apply copies them and requests `SAVE_REASON_SETTINGS` only after the panel closes with an initialized campaign, stable control, and a condition-valid `SAVELOC_CONTINUE_ALLOWED` current row. Simulation accepts only `SAVELOC_SIM_INTRO` at a tutorial pause-safe command boundary and persists settings against the restart-at-intro checkpoint; exploration rows must also be `SAVELOC_MANUAL_ALLOWED`. Cancel restores the prior value. The generator permits canonical `ui.screen.*` assets, rejects every `present.*` delivery alias as a manifest entry, rejects multiple owners for a canonical asset, and validates every screen reference against this table.

Serialized manifest header v2, 40 bytes:

| Offset | Bytes | Field |
|---:|---:|---|
| `0x00` | 4 | ASCII `N64A` |
| `0x04` | 2 | manifest version; current `2` |
| `0x06` | 2 | header bytes `40` |
| `0x08` | 2 | entry count |
| `0x0A` | 2 | bundle count |
| `0x0C` | 4 | entry table offset |
| `0x10` | 4 | bundle table offset |
| `0x14` | 4 | load-reference table offset |
| `0x18` | 4 | load-reference count |
| `0x1C` | 4 | total pack bytes |
| `0x20` | 4 | CRC-32 of header with this field zero plus all three tables |
| `0x24` | 4 | zero reserved |

Serialized asset entry, 24 bytes:

```c
typedef struct AssetManifestEntry {
    AssetId id;              /* 0 */
    uint8_t type;            /* 2 */
    uint8_t flags;           /* 3 */
    uint32_t rom_offset;     /* 4 */
    uint32_t packed_bytes;   /* 8 */
    uint32_t unpacked_bytes; /* 12 */
    uint32_t payload_crc32;  /* 16 */
    uint16_t alignment;      /* 20: power of two */
    BundleId bundle_id;      /* 22 */
} AssetManifestEntry;
_Static_assert(sizeof(AssetManifestEntry) == 24, "AssetManifestEntry layout");
```

Serialized bundle entry, 20 bytes:

```c
typedef struct BundleManifestEntry {
    BundleId id;               /* 0 */
    uint16_t flags;            /* 2 */
    uint16_t first_entry;      /* 4 */
    uint16_t entry_count;      /* 6 */
    uint32_t packed_bytes;     /* 8 */
    uint32_t unpacked_bytes;   /* 12 */
    uint32_t arena_cap_bytes;  /* 16 */
} BundleManifestEntry;
_Static_assert(sizeof(BundleManifestEntry) == 20, "BundleManifestEntry layout");

enum BundleManifestFlags {
    BUNDLE_MANIFEST_PROCESS_RESIDENT = 1u << 0,
    BUNDLE_MANIFEST_OPTIONAL = 1u << 1,
    BUNDLE_MANIFEST_ACTION_ONLY = 1u << 2,
    BUNDLE_MANIFEST_STREAMED = 1u << 3
};
```

`AssetManifestEntry.bundle_id` is the asset's sole owning pack bundle. A load bundle may reference assets owned by shared catalogs through the third table:

```c
typedef struct BundleAssetRef {
    BundleId load_bundle_id; /* 0: required/optional/action manifest */
    AssetId asset_id;        /* 2: packed once under its owning bundle */
    uint16_t flags;          /* 4: required, optional-prefetch, action-pin */
    uint16_t reserved;       /* 6 */
} BundleAssetRef;
_Static_assert(sizeof(BundleAssetRef) == 8, "BundleAssetRef layout");

enum BundleAssetRefFlags {
    BUNDLE_REF_REQUIRED = 1u << 0,
    BUNDLE_REF_OPTIONAL_PREFETCH = 1u << 1,
    BUNDLE_REF_ACTION_PIN = 1u << 2
};
```

`AssetManifestEntry.flags` accepts only the declared `AssetFlags` mask `0x3F`. `BundleManifestEntry.flags` accepts only `0x000F`: process-resident is exclusive with optional/action-only, optional is exclusive with action-only, and streamed requires every referenced asset be stream-compatible. `BundleAssetRef.flags` accepts only `0x0007`; exactly one of REQUIRED or OPTIONAL_PREFETCH is set, while ACTION_PIN may additionally be set only for an action-only load bundle. `BundleAssetRef.reserved` is zero. Unknown bits, illegal combinations, or disagreement with owner/load-bundle classification fail decode/generation; flags are never masked.

Entries are sorted by `(owning bundle_id, asset_id)` and every owning bundle is a contiguous entry range. References are sorted by `(load_bundle_id, asset_id)` and duplicate refs are rejected. Editable source may express asset-to-asset and load-bundle dependency edges; generation cycle-checks that graph, rejects missing/orphan nodes, then emits a flattened AssetId closure. Every asset has exactly one owning pack bundle and zero or more load-manifest references. ROM totals deduplicate by AssetId globally; resident/composite totals deduplicate by AssetId within the closure, so shared actors, animations, UI, and VFX are packed once and charged once per simultaneous composition.

ROM offset + packed size must remain within the DFS asset image with no overlap. Each `BundleManifestEntry` validates its packed bytes, deduplicated unpacked closure bytes, and arena cap. Every legal `ZoneBindingDef` combination validates `required + loaded optional + one action + collision/nav/spawn/interaction + scene/action state + allocator overhead <= zone arena cap <= 1,100 KiB`. The report also sums executable, read-only data, DFS asset bytes, header, and alignment/padding; the ordinary build fails at or above 16 MiB. A reviewed exception is required to use more, and 32 MiB is the absolute ceiling. Required animation sets reference a model with matching skeleton signature. Skinned GLB validation rejects any exported vertex with zero or more than one bone influence, missing required clips, excessive bones, unsupported materials, or unexplained converter warnings.

The source-side provenance record additionally carries ledger ID, source path/hash, tool versions, conversion command hash, license class, triangle/material/texture/bone/animation counts, seven review-gate statuses, and evidence paths. These strings stay in build reports; runtime manifests carry only what loading needs.

## 13. Transition requests

### 13.1 Gameplay transition definitions

```c
typedef enum TransitionIdValue {
    TRANS_DEF_NAME_TO_SIM = 1,
    TRANS_DEF_SIM_REVEAL = 2,
    TRANS_DEF_SIM_TO_ATRIUM = 3,
    TRANS_DEF_ATRIUM_TO_SIM = 4,
    TRANS_DEF_ATRIUM_TO_DIRECTOR = 5,
    TRANS_DEF_DIRECTOR_TO_ATRIUM = 6,
    TRANS_DEF_ATRIUM_TO_PLAYER_ROOM = 7,
    TRANS_DEF_PLAYER_ROOM_TO_ATRIUM = 8,
    TRANS_DEF_ATRIUM_TO_CLINIC = 9,
    TRANS_DEF_CLINIC_TO_ATRIUM = 10,
    TRANS_DEF_ATRIUM_TO_WORKSHOP = 11,
    TRANS_DEF_WORKSHOP_TO_ATRIUM = 12,
    TRANS_DEF_ATRIUM_TO_THRESHOLD = 13,
    TRANS_DEF_THRESHOLD_TO_ATRIUM = 14,
    TRANS_DEF_ELEVATOR_UP = 15,
    TRANS_DEF_ELEVATOR_DOWN = 16,
    TRANS_DEF_THRESHOLD_TO_MAP = 17,
    TRANS_DEF_MAP_TO_THRESHOLD = 18,
    TRANS_DEF_MAP_TO_ESTATE = 19,
    TRANS_DEF_ESTATE_TO_MAP = 20,
    TRANS_DEF_COURTYARD_TO_FOYER = 21,
    TRANS_DEF_FOYER_TO_COURTYARD = 22,
    TRANS_DEF_FOYER_TO_HALL = 23,
    TRANS_DEF_HALL_TO_FOYER = 24,
    TRANS_DEF_HALL_TO_STUDY = 25,
    TRANS_DEF_STUDY_TO_HALL = 26,
    TRANS_DEF_RUSK_BATTLE_START = 27,
    TRANS_DEF_RUSK_BATTLE_RETRY = 28,
    TRANS_DEF_RUSK_RETURN_ANNEX = 29,
    TRANS_DEF_STUDY_RETURN_TO_MAP = 30,
    TRANS_DEF_MAP_RETURN_TO_ANNEX = 31,
    TRANS_DEF_HOOK_TO_END_CARD = 32,
    TRANS_DEF_MAP_RESELECT_ESTATE = 33,
    TRANS_DEF_MAP_RETURN_RESELECT_ESTATE = 34,
    TRANS_DEF_THRESHOLD_TO_MAP_REPEAT = 35,
    TRANS_DEF_MAP_CANCEL_TO_ANNEX = 36,
    TRANS_DEF_MAP_CANCEL_TO_ESTATE = 37,
    TRANS_DEF_MAP_CANCEL_TO_ESTATE_FOLLOWER = 38
} TransitionIdValue;

typedef enum TransitionConditionIdValue {
    COND_TRANS_ALWAYS = 0x6201,
    COND_TRANS_NAME_DRAFT_CONFIRMED = 0x6202,
    COND_TRANS_TUTORIAL_RESULT_COMPLETE = 0x6203,
    COND_TRANS_ANNEX_ONBOARDING_COMPLETE = 0x6204,
    COND_TRANS_ANNEX_FIRST_DEPARTURE_NO_RETURN_FOLLOWER = 0x6205,
    COND_TRANS_ANNEX_NODE_NO_RETURN_FOLLOWER = 0x6206,
    COND_TRANS_ESTATE_FIRST_ARRIVAL_NO_RETURN_FOLLOWER = 0x6207,
    COND_TRANS_ESTATE_RESELECT_NO_RETURN_FOLLOWER = 0x6208,
    COND_TRANS_ESTATE_EXIT_NO_RETURN_FOLLOWER = 0x6209,
    COND_TRANS_ESTATE_DOOR_OPEN = 0x620A,
    COND_TRANS_ORRERY_STAIR_OPEN = 0x620B,
    COND_TRANS_RUSK_START = 0x620C,
    COND_TRANS_PRE_RUSK_SNAPSHOT_VALID = 0x620D,
    COND_TRANS_RETURN_FOLLOWER_ACTIVE = 0x620E,
    COND_TRANS_SLICE_CHECKPOINT_COMMITTED = 0x620F,
    COND_TRANS_ANNEX_REPEAT_TRAVEL_NO_RETURN_FOLLOWER = 0x6210,
    COND_TRANS_RETURN_FOLLOWER_ACTIVE_ANNEX_SELECTED = 0x6211,
    COND_TRANS_RETURN_FOLLOWER_ACTIVE_ESTATE_SELECTED = 0x6212
} TransitionConditionIdValue;

typedef enum TransitionReason {
    TRANSITION_DOOR = 1,
    TRANSITION_ELEVATOR,
    TRANSITION_WORLD_MAP,
    TRANSITION_BATTLE_START,
    TRANSITION_BATTLE_RETRY,
    TRANSITION_BATTLE_RETURN,
    TRANSITION_CUTSCENE_END,
    TRANSITION_STORY,
    TRANSITION_RECOVERY
} TransitionReason;

typedef enum TransitionPhase {
    TRANSITION_IDLE = 0,
    TRANSITION_REQUESTED = 1,
    TRANSITION_QUIESCE = 2,
    TRANSITION_FENCE = 3,
    TRANSITION_UNLOAD = 4,
    TRANSITION_LOAD_SHELL = 5,
    TRANSITION_STAGE = 6,
    TRANSITION_COMMIT = 7,
    TRANSITION_REVEAL = 8,
    TRANSITION_FAILED = 9,
    TRANSITION_ROLLBACK_SOURCE = 10,
    TRANSITION_ROLLBACK_FATAL = 11
} TransitionPhase;

typedef enum TransitionErrorCodeValue {
    TRANSITION_ERROR_NONE = 0,
    TRANSITION_ERROR_DESTINATION_SHELL_LOAD = 1,
    TRANSITION_ERROR_DESTINATION_STAGE = 2,
    TRANSITION_ERROR_DESTINATION_ENTER = 3,
    TRANSITION_ERROR_DESTINATION_PRECOMMIT = 4,
    TRANSITION_ERROR_SOURCE_ROLLBACK_PREPARE = 5,
    TRANSITION_ERROR_SOURCE_ROLLBACK_LOAD = 6,
    TRANSITION_ERROR_SOURCE_ROLLBACK_ENTER = 7,
    TRANSITION_ERROR_ROLLBACK_DESCRIPTOR_INVALID = 8
} TransitionErrorCodeValue;

typedef enum SavePolicy {
    SAVE_NONE = 0,
    SAVE_BEFORE_AT_SAFE_SOURCE = 1,
    SAVE_AFTER_DESTINATION_COMMIT = 2,
    SAVE_AFTER_STORY_TRANSACTION = 3
} SavePolicy;

typedef enum TransitionStyle {
    TRANS_STYLE_FADE = 1,
    TRANS_STYLE_DOOR = 2,
    TRANS_STYLE_ELEVATOR = 3,
    TRANS_STYLE_DISSOLVE = 4,
    TRANS_STYLE_WORLD_ROUTE = 5,
    TRANS_STYLE_ACTION_RESET = 6
} TransitionStyle;

enum TransitionFlags {
    TRANSITION_FLAG_RETAIN_IDENTICAL_REQUIRED_BASE = 1u << 0,
    TRANSITION_FLAG_FOLLOWER_HANDOFF = 1u << 1,
    TRANSITION_FLAG_SAME_ZONE = 1u << 2,
    TRANSITION_FLAG_ACTION_ONLY = 1u << 3,
    TRANSITION_FLAG_NON_SAVEABLE_DESTINATION = 1u << 4
};

typedef struct TransitionDef {
    TransitionId id;                    /* 0 */
    SceneId source_scene_id;            /* 2 */
    ZoneId source_zone_id;              /* 4 */
    InteractionId trigger_interaction_id; /* 6; 0 for automatic/menu */
    SceneId destination_scene_id;       /* 8 */
    ZoneId destination_zone_id;         /* 10 */
    SpawnId destination_spawn_id;       /* 12; zero only for non-saveable UI */
    ConditionId condition_id;           /* 14 */
    uint8_t reason;                     /* 16 */
    uint8_t style;                      /* 17 */
    uint8_t save_policy;                /* 18 */
    uint8_t reserved0;                  /* 19 */
    uint16_t flags;                     /* 20 */
    TransitionId reverse_or_retry_id;   /* 22 */
    uint16_t reserved1;                 /* 24 */
} TransitionDef;
_Static_assert(sizeof(TransitionDef) == 26, "TransitionDef layout");

enum TransitionRollbackDescriptorFlags {
    TRANS_ROLLBACK_SOURCE_TUPLE_VALIDATED = 1u << 0,
    TRANS_ROLLBACK_MANIFEST_IDENTITY_CAPTURED = 1u << 1,
    TRANS_ROLLBACK_SOURCE_STATE_CAPTURED = 1u << 2,
    TRANS_ROLLBACK_REQUEST_BOUND = 1u << 3,
    TRANS_ROLLBACK_PROCESS_SAFE_COPY = 1u << 4,
    TRANS_ROLLBACK_ACTION_BUNDLE_PRESENT = 1u << 5,
    TRANS_ROLLBACK_SAVELOC_PRESENT = 1u << 6
};

typedef struct TransitionRollbackDescriptor {
    uint32_t descriptor_generation;          /* 0: nonzero process-owner serial */
    uint32_t bound_runtime_generation;       /* 4: zero until finalization */
    uint32_t request_token;                  /* 8: equals TransitionRequest.token */
    uint32_t source_state_hash;              /* 12: zero until finalization */
    uint32_t source_manifest_crc32;           /* 16: exact required closure identity */
    uint32_t source_required_unpacked_bytes; /* 20 */
    TransitionId transition_id;              /* 24 */
    SceneId source_scene_id;                 /* 26 */
    ZoneId source_zone_id;                   /* 28 */
    SpawnId source_spawn_id;                 /* 30 */
    BundleId source_required_bundle_id;      /* 32 */
    BundleId source_action_bundle_id;        /* 34: zero when absent */
    SaveableLocationId source_saveloc_id;    /* 36: zero for non-saveable source */
    uint16_t flags;                          /* 38 */
    uint32_t identity_crc32;                 /* 40: zero provisional; then fields 0..39 */
} TransitionRollbackDescriptor;
_Static_assert(sizeof(TransitionRollbackDescriptor) == 44, "TransitionRollbackDescriptor layout");

typedef enum TransitionStoryRecipeIdValue {
    TRANS_RECIPE_NONE = 0,
    TRANS_RECIPE_NAME_INITIALIZE = 1,
    TRANS_RECIPE_ANNEX_DEPARTURE = 2,
    TRANS_RECIPE_ESTATE_ARRIVAL = 3,
    TRANS_RECIPE_RUSK_RETURN_ANNEX = 4,
    TRANS_RECIPE_STABLE_SOURCE_TRANSITION = 5,
    TRANS_RECIPE_STABLE_DESTINATION_TRANSITION = 6
} TransitionStoryRecipeIdValue;

typedef enum TransitionStoryActionListIdValue {
    ACTION_TRANS_AFTER_NAME = 0x4130,
    ACTION_TRANS_ANNEX_DEPARTURE = 0x4131,
    ACTION_TRANS_ESTATE_ARRIVAL = 0x4132,
    ACTION_TRANS_RUSK_RETURN_ANNEX = 0x4133
} TransitionStoryActionListIdValue;

enum TransitionStoryRecipeFlags {
    TRANS_RECIPE_INITIALIZE_PROGRESS = 1u << 0,
    TRANS_RECIPE_PROMOTE_CHECKPOINT = 1u << 1,
    TRANS_RECIPE_RESTORE_PRE_RUSK = 1u << 2,
    TRANS_RECIPE_DYNAMIC_SOURCE_LOCATION = 1u << 3,
    TRANS_RECIPE_DYNAMIC_DEST_LOCATION = 1u << 4,
    TRANS_RECIPE_SET_BOTH_LOCATIONS = 1u << 5,
    TRANS_RECIPE_RETAIN_OTHER_PROGRESS = 1u << 6
};

typedef struct TransitionStoryRecipeDef {
    uint16_t id;                       /* 0: TransitionStoryRecipeIdValue */
    StoryActionListId action_list_xref;/* 2; equality-only, zero allowed */
    CheckpointId checkpoint_id;        /* 4; zero means retain when flagged */
    SaveableLocationId current_saveloc_id; /* 6; zero only for dynamic */
    SaveableLocationId last_safe_saveloc_id; /* 8; zero only for dynamic */
    uint16_t chapter_progression;      /* 10; zero retained when flagged */
    SaveReason save_reason;            /* 12 */
    BattleResult battle_result;        /* 13 */
    EncounterId last_encounter_id;     /* 14 */
    uint16_t flags;                    /* 16 */
} TransitionStoryRecipeDef;
_Static_assert(sizeof(TransitionStoryRecipeDef) == 18, "TransitionStoryRecipeDef layout");

typedef enum TransitionStoryFailurePolicyValue {
    TRANS_STORY_FAIL_PRE_RETRY_UNSAVED_CANCEL = 1,
    TRANS_STORY_FAIL_POST_STAY_DIRTY_RETRY = 2
} TransitionStoryFailurePolicyValue;

enum TransitionStoryBindingFlags {
    TRANS_STORY_RUN_PRE_SOURCE = 1u << 0,
    TRANS_STORY_RUN_POST_ENTER = 1u << 1,
    TRANS_STORY_ALLOW_CONTINUE_UNSAVED = 1u << 2
};

typedef struct TransitionStoryBindingDef {
    TransitionId transition_id;       /* 0 */
    uint16_t pre_recipe_id;           /* 2 */
    uint16_t post_recipe_id;          /* 4 */
    uint8_t required_save_policy;     /* 6 */
    uint8_t failure_policy;           /* 7 */
    uint16_t flags;                   /* 8 */
    uint16_t reserved;                /* 10 */
} TransitionStoryBindingDef;
_Static_assert(sizeof(TransitionStoryBindingDef) == 12, "TransitionStoryBindingDef layout");

enum FinalSaveContinuationFlags {
    FINAL_CONTINUATION_REQUIRE_CURRENT_GENERATION = 1u << 0,
    FINAL_CONTINUATION_REQUIRE_MILESTONE_COMMITTED = 1u << 1,
    FINAL_CONTINUATION_REQUEST_EXACT_TRANSITION = 1u << 2,
    FINAL_CONTINUATION_REQUIRE_SAVE_DONE_TIMED_COMPLETE = 1u << 3
};

typedef struct FinalSaveOutcomeContinuationDef {
    uint16_t milestone_recipe_id; /* 0 */
    uint8_t final_save_outcome;   /* 2: FinalSaveOutcomeValue */
    uint8_t required_dirty_state; /* 3: RuntimeDirtyStateValue */
    TransitionId transition_id;   /* 4 */
    ConditionId condition_id;     /* 6 */
    uint16_t flags;               /* 8 */
    uint16_t reserved;            /* 10 */
} FinalSaveOutcomeContinuationDef;
_Static_assert(sizeof(FinalSaveOutcomeContinuationDef) == 12, "FinalSaveOutcomeContinuationDef layout");
```

The exact recipe rows are:

| RecipeId | Action list | Checkpoint / current / last-safe | Chapter / reason / result / encounter | Flags |
|---|---|---|---|---|
| `TRANS_RECIPE_NAME_INITIALIZE` | `ACTION_TRANS_AFTER_NAME` | `CHECKPOINT_AFTER_NAME / SAVELOC_SIM_INTRO / SAVELOC_SIM_INTRO` | `0 / SAVE_REASON_CHECKPOINT / BATTLE_RESULT_NONE / ENCOUNTER_NONE` | `TRANS_RECIPE_INITIALIZE_PROGRESS + TRANS_RECIPE_PROMOTE_CHECKPOINT + TRANS_RECIPE_SET_BOTH_LOCATIONS` |
| `TRANS_RECIPE_ANNEX_DEPARTURE` | `ACTION_TRANS_ANNEX_DEPARTURE` | `CHECKPOINT_ANNEX_DEPARTURE / SAVELOC_ANNEX_THRESHOLD_DEPARTURE / SAVELOC_ANNEX_THRESHOLD_DEPARTURE` | `4 / SAVE_REASON_CHECKPOINT / BATTLE_RESULT_NONE / ENCOUNTER_NONE` | `TRANS_RECIPE_PROMOTE_CHECKPOINT + TRANS_RECIPE_SET_BOTH_LOCATIONS + TRANS_RECIPE_RETAIN_OTHER_PROGRESS` |
| `TRANS_RECIPE_ESTATE_ARRIVAL` | `ACTION_TRANS_ESTATE_ARRIVAL` | `CHECKPOINT_ESTATE_ARRIVAL / SAVELOC_ESTATE_COURTYARD_ARRIVAL / SAVELOC_ESTATE_COURTYARD_ARRIVAL` | `5 / SAVE_REASON_CHECKPOINT / BATTLE_RESULT_NONE / ENCOUNTER_NONE` | `TRANS_RECIPE_PROMOTE_CHECKPOINT + TRANS_RECIPE_SET_BOTH_LOCATIONS + TRANS_RECIPE_RETAIN_OTHER_PROGRESS` |
| `TRANS_RECIPE_RUSK_RETURN_ANNEX` | `ACTION_TRANS_RUSK_RETURN_ANNEX` | `CHECKPOINT_RUSK_RETURN_TO_ANNEX / SAVELOC_ANNEX_THRESHOLD_DEPARTURE / SAVELOC_ANNEX_THRESHOLD_DEPARTURE` | `5 / SAVE_REASON_BATTLE_RESULT / BATTLE_RESULT_RETURN_TO_ANNEX / ENCOUNTER_RUSK_COURTYARD` | `TRANS_RECIPE_PROMOTE_CHECKPOINT + TRANS_RECIPE_RESTORE_PRE_RUSK + TRANS_RECIPE_SET_BOTH_LOCATIONS + TRANS_RECIPE_RETAIN_OTHER_PROGRESS` |
| `TRANS_RECIPE_STABLE_SOURCE_TRANSITION` | `0` | `0 / 0 / 0` | `0 / SAVE_REASON_TRANSITION / BATTLE_RESULT_NONE / ENCOUNTER_NONE` | `TRANS_RECIPE_DYNAMIC_SOURCE_LOCATION + TRANS_RECIPE_SET_BOTH_LOCATIONS + TRANS_RECIPE_RETAIN_OTHER_PROGRESS` |
| `TRANS_RECIPE_STABLE_DESTINATION_TRANSITION` | `0` | `0 / 0 / 0` | `0 / SAVE_REASON_TRANSITION / BATTLE_RESULT_NONE / ENCOUNTER_NONE` | `TRANS_RECIPE_DYNAMIC_DEST_LOCATION + TRANS_RECIPE_SET_BOTH_LOCATIONS + TRANS_RECIPE_RETAIN_OTHER_PROGRESS` |

The four recipe action lists occupy global action indices `11..14`, immediately after `OPENING_ACTION_PREFIX`. They are literal and contain no unresolved action/list reference:

```c
static const StoryAction TRANSITION_STORY_ACTIONS[4] = {
    { ACTION_SET_FLAG, STORY_ACTION_IDEMPOTENT + STORY_ACTION_APPLY_ON_SKIP,
      FLAG_PLAYER_NAME_CONFIRMED, 1, 0, 0 },
    { ACTION_SET_FLAG, STORY_ACTION_IDEMPOTENT + STORY_ACTION_APPLY_ON_SKIP,
      FLAG_ANNEX_EXIT_CLEARED, 1, 0, 0 },
    { ACTION_SET_FLAG, STORY_ACTION_IDEMPOTENT + STORY_ACTION_APPLY_ON_SKIP,
      FLAG_ESTATE_ARRIVED, 1, 0, 0 },
    { ACTION_SET_FLAG, STORY_ACTION_IDEMPOTENT + STORY_ACTION_APPLY_ON_SKIP,
      FLAG_RUSK_CONFRONTATION_SEEN, 1, 0, 0 }
};

static const StoryActionListDef TRANSITION_STORY_ACTION_LISTS[4] = {
    { ACTION_TRANS_AFTER_NAME, 11, 1, 0,
      STORY_CONTEXT_TRANSITION, STORY_LIST_ATOMIC_PROGRESS, 0 },
    { ACTION_TRANS_ANNEX_DEPARTURE, 12, 1, 0,
      STORY_CONTEXT_TRANSITION, STORY_LIST_ATOMIC_PROGRESS, 0 },
    { ACTION_TRANS_ESTATE_ARRIVAL, 13, 1, 0,
      STORY_CONTEXT_TRANSITION, STORY_LIST_ATOMIC_PROGRESS, 0 },
    { ACTION_TRANS_RUSK_RETURN_ANNEX, 14, 1, 0,
      STORY_CONTEXT_TRANSITION, STORY_LIST_ATOMIC_PROGRESS, 0 }
};
```

`TRANS_RECIPE_INITIALIZE_PROGRESS` is the only legal zero-to-initialized constructor. It starts from a zeroed 192-byte logical `SaveData`, copies exactly the validated runtime-draft `player_name[8]`, `player_name_length`, `playtime_seconds`, nonzero `campaign_seed`, sanitized `settings`, and true opening-cinematic bit, then writes `initialized=1`, `active_left_index=0xFF`, `active_right_index=0xFF`, the Annex destination bit, and the recipe/table fields above. The two `0xFF` writes are mandatory constructor writes, not values inherited from zero-fill. Party slots, objectives, counters, optional once bits, encounter history, rewards, research, and every reserved field remain zero. The action list then sets `FLAG_PLAYER_NAME_CONFIRMED`; complete validation must see both opening/name flags, `party_count=0`, both active indices `0xFF`, no active objective, and the exact After-Name tuple before the joint publish. It may not copy arbitrary draft padding, story flags, IDs, or arrays. The other three lists set only their named flag. The recipe—not an action operand—owns checkpoint, LocationKeys, chapter, SaveReason, BattleResult, and encounter fields.

The table uses full `TRANS_RECIPE_*` flag names; shorthand is for width only. RETAIN_OTHER_PROGRESS means zero checkpoint/chapter/result/encounter fields are not writes; the verified live values remain. Dynamic source/destination resolves an exact condition-valid SaveableLocationId and supplies both LocationKeys. Fixed recipes byte-write every listed semantic field and then run the complete checkpoint validator. Recipe flags accept only `0x007F`; impossible dynamic/fixed combinations, an unresolved list/location, or field/flag disagreement fail generation.

Exactly seven TransitionDefs carry a story binding:

| TransitionId | Pre / post recipe | Required policy | Failure policy | Flags |
|---|---|---|---|---|
| `TRANS_DEF_NAME_TO_SIM` | `0 / TRANS_RECIPE_NAME_INITIALIZE` | `SAVE_AFTER_STORY_TRANSACTION` | `TRANS_STORY_FAIL_POST_STAY_DIRTY_RETRY` | `TRANS_STORY_RUN_POST_ENTER` |
| `TRANS_DEF_THRESHOLD_TO_MAP` | `TRANS_RECIPE_ANNEX_DEPARTURE / 0` | `SAVE_BEFORE_AT_SAFE_SOURCE` | `TRANS_STORY_FAIL_PRE_RETRY_UNSAVED_CANCEL` | `TRANS_STORY_RUN_PRE_SOURCE + TRANS_STORY_ALLOW_CONTINUE_UNSAVED` |
| `TRANS_DEF_THRESHOLD_TO_MAP_REPEAT` | `TRANS_RECIPE_STABLE_SOURCE_TRANSITION / 0` | `SAVE_BEFORE_AT_SAFE_SOURCE` | `TRANS_STORY_FAIL_PRE_RETRY_UNSAVED_CANCEL` | `TRANS_STORY_RUN_PRE_SOURCE + TRANS_STORY_ALLOW_CONTINUE_UNSAVED` |
| `TRANS_DEF_MAP_TO_ESTATE` | `0 / TRANS_RECIPE_ESTATE_ARRIVAL` | `SAVE_AFTER_STORY_TRANSACTION` | `TRANS_STORY_FAIL_POST_STAY_DIRTY_RETRY` | `TRANS_STORY_RUN_POST_ENTER` |
| `TRANS_DEF_ESTATE_TO_MAP` | `TRANS_RECIPE_STABLE_SOURCE_TRANSITION / 0` | `SAVE_BEFORE_AT_SAFE_SOURCE` | `TRANS_STORY_FAIL_PRE_RETRY_UNSAVED_CANCEL` | `TRANS_STORY_RUN_PRE_SOURCE + TRANS_STORY_ALLOW_CONTINUE_UNSAVED` |
| `TRANS_DEF_RUSK_RETURN_ANNEX` | `0 / TRANS_RECIPE_RUSK_RETURN_ANNEX` | `SAVE_AFTER_STORY_TRANSACTION` | `TRANS_STORY_FAIL_POST_STAY_DIRTY_RETRY` | `TRANS_STORY_RUN_POST_ENTER` |
| `TRANS_DEF_STUDY_RETURN_TO_MAP` | `TRANS_RECIPE_STABLE_SOURCE_TRANSITION / 0` | `SAVE_BEFORE_AT_SAFE_SOURCE` | `TRANS_STORY_FAIL_PRE_RETRY_UNSAVED_CANCEL` | `TRANS_STORY_RUN_PRE_SOURCE + TRANS_STORY_ALLOW_CONTINUE_UNSAVED` |

Bindings are unique by TransitionId; policy byte must match TransitionDef, exactly one pre/post bit and recipe side agree, binding flags accept only `0x0007`, and reserved is zero. Every SAVE_BEFORE row and every SAVE_AFTER_STORY row has exactly one binding; no other row may have one. Every SAVE_AFTER_DESTINATION row uses `TRANS_RECIPE_STABLE_DESTINATION_TRANSITION` internally after entry and does not carry a story binding.

The final milestone's outcome routing is data, not a HookController switch:

| milestone / outcome | required dirty state | TransitionId / ConditionId | Flags / reserved |
|---|---|---|---|
| `MILESTONE_SLICE_COMPLETE / FINAL_SAVE_OUTCOME_SAVED` | `RUNTIME_PROGRESS_CLEAN` | `TRANS_DEF_HOOK_TO_END_CARD / COND_TRANS_SLICE_CHECKPOINT_COMMITTED` | `FINAL_CONTINUATION_REQUIRE_CURRENT_GENERATION + FINAL_CONTINUATION_REQUIRE_MILESTONE_COMMITTED + FINAL_CONTINUATION_REQUEST_EXACT_TRANSITION + FINAL_CONTINUATION_REQUIRE_SAVE_DONE_TIMED_COMPLETE / 0` |
| `MILESTONE_SLICE_COMPLETE / FINAL_SAVE_OUTCOME_CONTINUE_UNSAVED` | `RUNTIME_PROGRESS_DIRTY` | `TRANS_DEF_HOOK_TO_END_CARD / COND_TRANS_SLICE_CHECKPOINT_COMMITTED` | `FINAL_CONTINUATION_REQUIRE_CURRENT_GENERATION + FINAL_CONTINUATION_REQUIRE_MILESTONE_COMMITTED + FINAL_CONTINUATION_REQUEST_EXACT_TRANSITION / 0` |

`FINAL_SAVE_OUTCOME_PENDING` has no row and cannot advance. On Retry, the save service re-enqueues the same immutable Slice Complete snapshot under the live milestone token and returns to Pending; it does not emit a transition. Verified write success first opens the exact Save Done timed binding over the retained Hook/Annex owner; the saved continuation is not selectable until its generation-bound final-item token matches the final request/campaign and the overlay releases. Explicit Continue Unsaved releases its failure owner and can select the dirty row directly because it never shows `RESONANCE RECORDED`. The resolver then reserves the transition queue slot, revalidates generation/outcome/dirty/token and the row condition, and requests `TRANS_DEF_HOOK_TO_END_CARD`. Both branches therefore reach the same authored end card only after their truthful presentation; the dirty branch never sets CLEAN or claims EEPROM success. Missing, duplicate, stale timed token, outcome/dirty mismatch, or a non-Hook destination fails generation/runtime closed.

The generator emits exactly these rows; named `INT_*` triggers are locked `InteractionId`s in the zone interaction pack, and `AUTO`/menu rows use zero. Every condition is one numeric `TransitionConditionIdValue`; no prose predicate is emitted. There are no hidden source/destination mode fields: `TransitionId` plus its exact source tuple/trigger fixes the source submode, and its exact destination tuple fixes the destination submode. Elevator upper/lower, simulation reveal, battle action, and UI end-card modes therefore resolve from distinct IDs/spawns rather than an unpopulated field.

| TransitionId | Exact source Scene / Zone / trigger | Exact destination Scene / Zone / Spawn | ConditionId | Reason / style / save | Flags; reverse/retry |
|---|---|---|---|---|---|
| `TRANS_DEF_NAME_TO_SIM` | `SCENE_NAME_ENTRY / ZONE_NONE / 0` | `SCENE_SIM_ARENA / ZONE_SIM_ARENA / SPAWN_SIM_INTRO` | `COND_TRANS_NAME_DRAFT_CONFIRMED` | `TRANSITION_STORY / TRANS_STYLE_FADE / SAVE_AFTER_STORY_TRANSACTION` | `0`; `0` |
| `TRANS_DEF_SIM_REVEAL` | `SCENE_SIM_ARENA / ZONE_SIM_ARENA / 0` | `SCENE_ANNEX_INTERIOR / ZONE_ANNEX_SIMULATION_ROOM / SPAWN_ANNEX_SIM_POST_TUTORIAL` | `COND_TRANS_TUTORIAL_RESULT_COMPLETE` | `TRANSITION_STORY / TRANS_STYLE_DISSOLVE / SAVE_NONE` | `TRANSITION_FLAG_RETAIN_IDENTICAL_REQUIRED_BASE`; `0` |
| `TRANS_DEF_SIM_TO_ATRIUM` | `SCENE_ANNEX_INTERIOR / ZONE_ANNEX_SIMULATION_ROOM / INT_SIM_EXIT` | `SCENE_ANNEX_INTERIOR / ZONE_ANNEX_ATRIUM / SPAWN_ANNEX_ATRIUM_FROM_SIM` | `COND_TRANS_ANNEX_ONBOARDING_COMPLETE` | `TRANSITION_DOOR / TRANS_STYLE_DOOR / SAVE_AFTER_DESTINATION_COMMIT` | `0`; `TRANS_DEF_ATRIUM_TO_SIM` |
| `TRANS_DEF_ATRIUM_TO_SIM` | `SCENE_ANNEX_INTERIOR / ZONE_ANNEX_ATRIUM / INT_ATRIUM_SIM_DOOR` | `SCENE_ANNEX_INTERIOR / ZONE_ANNEX_SIMULATION_ROOM / SPAWN_ANNEX_SIM_FROM_ATRIUM` | `COND_TRANS_ALWAYS` | `TRANSITION_DOOR / TRANS_STYLE_DOOR / SAVE_AFTER_DESTINATION_COMMIT` | `0`; `TRANS_DEF_SIM_TO_ATRIUM` |
| `TRANS_DEF_ATRIUM_TO_DIRECTOR` | `SCENE_ANNEX_INTERIOR / ZONE_ANNEX_ATRIUM / INT_ATRIUM_DIRECTOR_DOOR` | `SCENE_ANNEX_INTERIOR / ZONE_ANNEX_DIRECTOR_LAB / SPAWN_ANNEX_DIRECTOR_FROM_ATRIUM` | `COND_TRANS_ALWAYS` | `TRANSITION_DOOR / TRANS_STYLE_DOOR / SAVE_AFTER_DESTINATION_COMMIT` | `0`; `TRANS_DEF_DIRECTOR_TO_ATRIUM` |
| `TRANS_DEF_DIRECTOR_TO_ATRIUM` | `SCENE_ANNEX_INTERIOR / ZONE_ANNEX_DIRECTOR_LAB / INT_DIRECTOR_EXIT` | `SCENE_ANNEX_INTERIOR / ZONE_ANNEX_ATRIUM / SPAWN_ANNEX_ATRIUM_FROM_DIRECTOR` | `COND_TRANS_ALWAYS` | `TRANSITION_DOOR / TRANS_STYLE_DOOR / SAVE_AFTER_DESTINATION_COMMIT` | `0`; `TRANS_DEF_ATRIUM_TO_DIRECTOR` |
| `TRANS_DEF_ATRIUM_TO_PLAYER_ROOM` | `SCENE_ANNEX_INTERIOR / ZONE_ANNEX_ATRIUM / INT_ATRIUM_PLAYER_DOOR` | `SCENE_ANNEX_INTERIOR / ZONE_ANNEX_PLAYER_ROOM / SPAWN_ANNEX_PLAYER_ROOM_FROM_ATRIUM` | `COND_TRANS_ALWAYS` | `TRANSITION_DOOR / TRANS_STYLE_DOOR / SAVE_AFTER_DESTINATION_COMMIT` | `0`; `TRANS_DEF_PLAYER_ROOM_TO_ATRIUM` |
| `TRANS_DEF_PLAYER_ROOM_TO_ATRIUM` | `SCENE_ANNEX_INTERIOR / ZONE_ANNEX_PLAYER_ROOM / INT_PLAYER_EXIT` | `SCENE_ANNEX_INTERIOR / ZONE_ANNEX_ATRIUM / SPAWN_ANNEX_ATRIUM_FROM_PLAYER_ROOM` | `COND_TRANS_ALWAYS` | `TRANSITION_DOOR / TRANS_STYLE_DOOR / SAVE_AFTER_DESTINATION_COMMIT` | `0`; `TRANS_DEF_ATRIUM_TO_PLAYER_ROOM` |
| `TRANS_DEF_ATRIUM_TO_CLINIC` | `SCENE_ANNEX_INTERIOR / ZONE_ANNEX_ATRIUM / INT_ATRIUM_CLINIC_DOOR` | `SCENE_ANNEX_INTERIOR / ZONE_ANNEX_CLINIC / SPAWN_ANNEX_CLINIC_FROM_ATRIUM` | `COND_TRANS_ALWAYS` | `TRANSITION_DOOR / TRANS_STYLE_DOOR / SAVE_AFTER_DESTINATION_COMMIT` | `0`; `TRANS_DEF_CLINIC_TO_ATRIUM` |
| `TRANS_DEF_CLINIC_TO_ATRIUM` | `SCENE_ANNEX_INTERIOR / ZONE_ANNEX_CLINIC / INT_CLINIC_EXIT` | `SCENE_ANNEX_INTERIOR / ZONE_ANNEX_ATRIUM / SPAWN_ANNEX_ATRIUM_FROM_CLINIC` | `COND_TRANS_ALWAYS` | `TRANSITION_DOOR / TRANS_STYLE_DOOR / SAVE_AFTER_DESTINATION_COMMIT` | `0`; `TRANS_DEF_ATRIUM_TO_CLINIC` |
| `TRANS_DEF_ATRIUM_TO_WORKSHOP` | `SCENE_ANNEX_INTERIOR / ZONE_ANNEX_ATRIUM / INT_ATRIUM_WORKSHOP_DOOR` | `SCENE_ANNEX_INTERIOR / ZONE_ANNEX_WORKSHOP / SPAWN_ANNEX_WORKSHOP_FROM_ATRIUM` | `COND_TRANS_ALWAYS` | `TRANSITION_DOOR / TRANS_STYLE_DOOR / SAVE_AFTER_DESTINATION_COMMIT` | `0`; `TRANS_DEF_WORKSHOP_TO_ATRIUM` |
| `TRANS_DEF_WORKSHOP_TO_ATRIUM` | `SCENE_ANNEX_INTERIOR / ZONE_ANNEX_WORKSHOP / INT_WORKSHOP_EXIT` | `SCENE_ANNEX_INTERIOR / ZONE_ANNEX_ATRIUM / SPAWN_ANNEX_ATRIUM_FROM_WORKSHOP` | `COND_TRANS_ALWAYS` | `TRANSITION_DOOR / TRANS_STYLE_DOOR / SAVE_AFTER_DESTINATION_COMMIT` | `0`; `TRANS_DEF_ATRIUM_TO_WORKSHOP` |
| `TRANS_DEF_ATRIUM_TO_THRESHOLD` | `SCENE_ANNEX_INTERIOR / ZONE_ANNEX_ATRIUM / INT_ATRIUM_THRESHOLD_DOOR` | `SCENE_ANNEX_INTERIOR / ZONE_ANNEX_THRESHOLD / SPAWN_ANNEX_THRESHOLD_FROM_ATRIUM` | `COND_TRANS_ALWAYS` | `TRANSITION_DOOR / TRANS_STYLE_DOOR / SAVE_AFTER_DESTINATION_COMMIT` | `TRANSITION_FLAG_FOLLOWER_HANDOFF`; `TRANS_DEF_THRESHOLD_TO_ATRIUM` |
| `TRANS_DEF_THRESHOLD_TO_ATRIUM` | `SCENE_ANNEX_INTERIOR / ZONE_ANNEX_THRESHOLD / INT_THRESHOLD_INNER_DOOR` | `SCENE_ANNEX_INTERIOR / ZONE_ANNEX_ATRIUM / SPAWN_ANNEX_ATRIUM_FROM_THRESHOLD` | `COND_TRANS_ALWAYS` | `TRANSITION_DOOR / TRANS_STYLE_DOOR / SAVE_AFTER_DESTINATION_COMMIT` | `TRANSITION_FLAG_FOLLOWER_HANDOFF`; `TRANS_DEF_ATRIUM_TO_THRESHOLD` |
| `TRANS_DEF_ELEVATOR_UP` | `SCENE_ANNEX_INTERIOR / ZONE_ANNEX_ATRIUM / INT_ELEVATOR_UP` | `SCENE_ANNEX_INTERIOR / ZONE_ANNEX_ATRIUM / SPAWN_ANNEX_ATRIUM_ELEVATOR_UPPER` | `COND_TRANS_ALWAYS` | `TRANSITION_ELEVATOR / TRANS_STYLE_ELEVATOR / SAVE_NONE` | `TRANSITION_FLAG_SAME_ZONE + TRANSITION_FLAG_FOLLOWER_HANDOFF`; `TRANS_DEF_ELEVATOR_DOWN` |
| `TRANS_DEF_ELEVATOR_DOWN` | `SCENE_ANNEX_INTERIOR / ZONE_ANNEX_ATRIUM / INT_ELEVATOR_DOWN` | `SCENE_ANNEX_INTERIOR / ZONE_ANNEX_ATRIUM / SPAWN_ANNEX_ATRIUM_ELEVATOR_LOWER` | `COND_TRANS_ALWAYS` | `TRANSITION_ELEVATOR / TRANS_STYLE_ELEVATOR / SAVE_NONE` | `TRANSITION_FLAG_SAME_ZONE + TRANSITION_FLAG_FOLLOWER_HANDOFF`; `TRANS_DEF_ELEVATOR_UP` |
| `TRANS_DEF_THRESHOLD_TO_MAP` | `SCENE_ANNEX_INTERIOR / ZONE_ANNEX_THRESHOLD / INT_SKIMMER_MAP` | `SCENE_WORLD_MAP / ZONE_WORLD_MAP_DESERT / SPAWN_WORLD_MAP_ANNEX_NODE` | `COND_TRANS_ANNEX_FIRST_DEPARTURE_NO_RETURN_FOLLOWER` | `TRANSITION_WORLD_MAP / TRANS_STYLE_WORLD_ROUTE / SAVE_BEFORE_AT_SAFE_SOURCE` | `0`; `TRANS_DEF_MAP_TO_THRESHOLD` |
| `TRANS_DEF_THRESHOLD_TO_MAP_REPEAT` | `SCENE_ANNEX_INTERIOR / ZONE_ANNEX_THRESHOLD / INT_SKIMMER_MAP` | `SCENE_WORLD_MAP / ZONE_WORLD_MAP_DESERT / SPAWN_WORLD_MAP_ANNEX_NODE` | `COND_TRANS_ANNEX_REPEAT_TRAVEL_NO_RETURN_FOLLOWER` | `TRANSITION_WORLD_MAP / TRANS_STYLE_WORLD_ROUTE / SAVE_BEFORE_AT_SAFE_SOURCE` | `0`; `TRANS_DEF_MAP_TO_THRESHOLD` |
| `TRANS_DEF_MAP_TO_THRESHOLD` | `SCENE_WORLD_MAP / ZONE_WORLD_MAP_DESERT / 0` | `SCENE_ANNEX_INTERIOR / ZONE_ANNEX_THRESHOLD / SPAWN_ANNEX_THRESHOLD_DEPARTURE` | `COND_TRANS_ANNEX_NODE_NO_RETURN_FOLLOWER` | `TRANSITION_WORLD_MAP / TRANS_STYLE_WORLD_ROUTE / SAVE_AFTER_DESTINATION_COMMIT` | `0`; `TRANS_DEF_THRESHOLD_TO_MAP_REPEAT` |
| `TRANS_DEF_MAP_TO_ESTATE` | `SCENE_WORLD_MAP / ZONE_WORLD_MAP_DESERT / 0` | `SCENE_ESTATE_COURTYARD / ZONE_ESTATE_COURTYARD / SPAWN_ESTATE_COURTYARD_ARRIVAL` | `COND_TRANS_ESTATE_FIRST_ARRIVAL_NO_RETURN_FOLLOWER` | `TRANSITION_WORLD_MAP / TRANS_STYLE_WORLD_ROUTE / SAVE_AFTER_STORY_TRANSACTION` | `0`; `TRANS_DEF_ESTATE_TO_MAP` |
| `TRANS_DEF_ESTATE_TO_MAP` | `SCENE_ESTATE_COURTYARD / ZONE_ESTATE_COURTYARD / INT_ESTATE_SKIMMER` | `SCENE_WORLD_MAP / ZONE_WORLD_MAP_DESERT / SPAWN_WORLD_MAP_ESTATE_NODE` | `COND_TRANS_ESTATE_EXIT_NO_RETURN_FOLLOWER` | `TRANSITION_WORLD_MAP / TRANS_STYLE_WORLD_ROUTE / SAVE_BEFORE_AT_SAFE_SOURCE` | `0`; `TRANS_DEF_MAP_RESELECT_ESTATE` |
| `TRANS_DEF_COURTYARD_TO_FOYER` | `SCENE_ESTATE_COURTYARD / ZONE_ESTATE_COURTYARD / INT_ESTATE_MAIN_DOOR` | `SCENE_ESTATE_INTERIOR / ZONE_ESTATE_FOYER / SPAWN_ESTATE_FOYER_FROM_COURTYARD` | `COND_TRANS_ESTATE_DOOR_OPEN` | `TRANSITION_DOOR / TRANS_STYLE_DOOR / SAVE_AFTER_DESTINATION_COMMIT` | `TRANSITION_FLAG_FOLLOWER_HANDOFF`; `TRANS_DEF_FOYER_TO_COURTYARD` |
| `TRANS_DEF_FOYER_TO_COURTYARD` | `SCENE_ESTATE_INTERIOR / ZONE_ESTATE_FOYER / INT_FOYER_EXIT` | `SCENE_ESTATE_COURTYARD / ZONE_ESTATE_COURTYARD / SPAWN_ESTATE_COURTYARD_FROM_FOYER` | `COND_TRANS_ALWAYS` | `TRANSITION_DOOR / TRANS_STYLE_DOOR / SAVE_AFTER_DESTINATION_COMMIT` | `TRANSITION_FLAG_FOLLOWER_HANDOFF`; `TRANS_DEF_COURTYARD_TO_FOYER` |
| `TRANS_DEF_FOYER_TO_HALL` | `SCENE_ESTATE_INTERIOR / ZONE_ESTATE_FOYER / INT_FOYER_HALL_DOOR` | `SCENE_ESTATE_INTERIOR / ZONE_ESTATE_INVENTION_HALL / SPAWN_ESTATE_HALL_FROM_FOYER` | `COND_TRANS_ESTATE_DOOR_OPEN` | `TRANSITION_DOOR / TRANS_STYLE_DOOR / SAVE_AFTER_DESTINATION_COMMIT` | `TRANSITION_FLAG_FOLLOWER_HANDOFF`; `TRANS_DEF_HALL_TO_FOYER` |
| `TRANS_DEF_HALL_TO_FOYER` | `SCENE_ESTATE_INTERIOR / ZONE_ESTATE_INVENTION_HALL / INT_HALL_FOYER_DOOR` | `SCENE_ESTATE_INTERIOR / ZONE_ESTATE_FOYER / SPAWN_ESTATE_FOYER_FROM_HALL` | `COND_TRANS_ALWAYS` | `TRANSITION_DOOR / TRANS_STYLE_DOOR / SAVE_AFTER_DESTINATION_COMMIT` | `TRANSITION_FLAG_FOLLOWER_HANDOFF`; `TRANS_DEF_FOYER_TO_HALL` |
| `TRANS_DEF_HALL_TO_STUDY` | `SCENE_ESTATE_INTERIOR / ZONE_ESTATE_INVENTION_HALL / INT_HALL_STUDY_DOOR` | `SCENE_ESTATE_INTERIOR / ZONE_ESTATE_OBSERVATORY_STUDY / SPAWN_ESTATE_STUDY_FROM_HALL` | `COND_TRANS_ORRERY_STAIR_OPEN` | `TRANSITION_DOOR / TRANS_STYLE_DOOR / SAVE_AFTER_DESTINATION_COMMIT` | `TRANSITION_FLAG_FOLLOWER_HANDOFF`; `TRANS_DEF_STUDY_TO_HALL` |
| `TRANS_DEF_STUDY_TO_HALL` | `SCENE_ESTATE_INTERIOR / ZONE_ESTATE_OBSERVATORY_STUDY / INT_STUDY_EXIT` | `SCENE_ESTATE_INTERIOR / ZONE_ESTATE_INVENTION_HALL / SPAWN_ESTATE_HALL_FROM_STUDY` | `COND_TRANS_ALWAYS` | `TRANSITION_DOOR / TRANS_STYLE_DOOR / SAVE_AFTER_DESTINATION_COMMIT` | `TRANSITION_FLAG_FOLLOWER_HANDOFF`; `TRANS_DEF_HALL_TO_STUDY` |
| `TRANS_DEF_RUSK_BATTLE_START` | `SCENE_ESTATE_COURTYARD / ZONE_ESTATE_COURTYARD / 0` | `SCENE_ESTATE_COURTYARD / ZONE_ESTATE_COURTYARD / SPAWN_ESTATE_COURTYARD_BATTLE` | `COND_TRANS_RUSK_START` | `TRANSITION_BATTLE_START / TRANS_STYLE_ACTION_RESET / SAVE_NONE` | `TRANSITION_FLAG_SAME_ZONE + TRANSITION_FLAG_ACTION_ONLY`; `TRANS_DEF_RUSK_BATTLE_RETRY` |
| `TRANS_DEF_RUSK_BATTLE_RETRY` | `SCENE_ESTATE_COURTYARD / ZONE_ESTATE_COURTYARD / 0` | `SCENE_ESTATE_COURTYARD / ZONE_ESTATE_COURTYARD / SPAWN_ESTATE_COURTYARD_BATTLE` | `COND_TRANS_PRE_RUSK_SNAPSHOT_VALID` | `TRANSITION_BATTLE_RETRY / TRANS_STYLE_ACTION_RESET / SAVE_NONE` | `TRANSITION_FLAG_SAME_ZONE + TRANSITION_FLAG_ACTION_ONLY`; `TRANS_DEF_RUSK_BATTLE_RETRY` |
| `TRANS_DEF_RUSK_RETURN_ANNEX` | `SCENE_ESTATE_COURTYARD / ZONE_ESTATE_COURTYARD / 0` | `SCENE_ANNEX_INTERIOR / ZONE_ANNEX_THRESHOLD / SPAWN_ANNEX_THRESHOLD_DEPARTURE` | `COND_TRANS_PRE_RUSK_SNAPSHOT_VALID` | `TRANSITION_BATTLE_RETURN / TRANS_STYLE_FADE / SAVE_AFTER_STORY_TRANSACTION` | `0`; `0` |
| `TRANS_DEF_STUDY_RETURN_TO_MAP` | `SCENE_ESTATE_COURTYARD / ZONE_ESTATE_COURTYARD / INT_ESTATE_SKIMMER` | `SCENE_WORLD_MAP / ZONE_WORLD_MAP_DESERT / SPAWN_WORLD_MAP_ESTATE_NODE` | `COND_TRANS_RETURN_FOLLOWER_ACTIVE` | `TRANSITION_WORLD_MAP / TRANS_STYLE_WORLD_ROUTE / SAVE_BEFORE_AT_SAFE_SOURCE` | `TRANSITION_FLAG_FOLLOWER_HANDOFF`; `TRANS_DEF_MAP_RETURN_RESELECT_ESTATE` |
| `TRANS_DEF_MAP_RETURN_TO_ANNEX` | `SCENE_WORLD_MAP / ZONE_WORLD_MAP_DESERT / 0` | `SCENE_ANNEX_INTERIOR / ZONE_ANNEX_THRESHOLD / SPAWN_ANNEX_THRESHOLD_DEPARTURE` | `COND_TRANS_RETURN_FOLLOWER_ACTIVE_ANNEX_SELECTED` | `TRANSITION_WORLD_MAP / TRANS_STYLE_WORLD_ROUTE / SAVE_AFTER_DESTINATION_COMMIT` | `TRANSITION_FLAG_FOLLOWER_HANDOFF`; `0` |
| `TRANS_DEF_HOOK_TO_END_CARD` | `SCENE_ANNEX_INTERIOR / ZONE_ANNEX_ATRIUM / 0` | `SCENE_END_CHAPTER / ZONE_END_CARD_UI / SPAWN_NONE` | `COND_TRANS_SLICE_CHECKPOINT_COMMITTED` | `TRANSITION_STORY / TRANS_STYLE_FADE / SAVE_NONE` | `TRANSITION_FLAG_NON_SAVEABLE_DESTINATION`; `0` |
| `TRANS_DEF_MAP_RESELECT_ESTATE` | `SCENE_WORLD_MAP / ZONE_WORLD_MAP_DESERT / 0` | `SCENE_ESTATE_COURTYARD / ZONE_ESTATE_COURTYARD / SPAWN_ESTATE_COURTYARD_FROM_MAP` | `COND_TRANS_ESTATE_RESELECT_NO_RETURN_FOLLOWER` | `TRANSITION_WORLD_MAP / TRANS_STYLE_WORLD_ROUTE / SAVE_AFTER_DESTINATION_COMMIT` | `0`; `TRANS_DEF_ESTATE_TO_MAP` |
| `TRANS_DEF_MAP_RETURN_RESELECT_ESTATE` | `SCENE_WORLD_MAP / ZONE_WORLD_MAP_DESERT / 0` | `SCENE_ESTATE_COURTYARD / ZONE_ESTATE_COURTYARD / SPAWN_ESTATE_COURTYARD_FROM_MAP` | `COND_TRANS_RETURN_FOLLOWER_ACTIVE_ESTATE_SELECTED` | `TRANSITION_WORLD_MAP / TRANS_STYLE_WORLD_ROUTE / SAVE_AFTER_DESTINATION_COMMIT` | `TRANSITION_FLAG_FOLLOWER_HANDOFF`; `TRANS_DEF_STUDY_RETURN_TO_MAP` |
| `TRANS_DEF_MAP_CANCEL_TO_ANNEX` | `SCENE_WORLD_MAP / ZONE_WORLD_MAP_DESERT / 0` | `SCENE_ANNEX_INTERIOR / ZONE_ANNEX_THRESHOLD / SPAWN_ANNEX_THRESHOLD_DEPARTURE` | `COND_TRANS_ALWAYS` | `TRANSITION_WORLD_MAP / TRANS_STYLE_FADE / SAVE_NONE` | `0`; `0` |
| `TRANS_DEF_MAP_CANCEL_TO_ESTATE` | `SCENE_WORLD_MAP / ZONE_WORLD_MAP_DESERT / 0` | `SCENE_ESTATE_COURTYARD / ZONE_ESTATE_COURTYARD / SPAWN_ESTATE_COURTYARD_FROM_MAP` | `COND_TRANS_ALWAYS` | `TRANSITION_WORLD_MAP / TRANS_STYLE_FADE / SAVE_NONE` | `0`; `0` |
| `TRANS_DEF_MAP_CANCEL_TO_ESTATE_FOLLOWER` | `SCENE_WORLD_MAP / ZONE_WORLD_MAP_DESERT / 0` | `SCENE_ESTATE_COURTYARD / ZONE_ESTATE_COURTYARD / SPAWN_ESTATE_COURTYARD_FROM_MAP` | `COND_TRANS_ALWAYS` | `TRANSITION_WORLD_MAP / TRANS_STYLE_FADE / SAVE_NONE` | `TRANSITION_FLAG_FOLLOWER_HANDOFF`; `0` |

The generated condition programs are fixed: `COND_TRANS_ALWAYS=true`; Name requires `RUNTIME_DRAFT_NAME_CONFIRMED`; tutorial/result requires `TUTORIAL_RESULT_COMPLETE`; onboarding requires its exact progress flags. First Annex travel requires Relay unlock, Estate destination unlock, `FLAG_ANNEX_EXIT_CLEARED=false`, and `RETURN_FOLLOWER_INACTIVE`; repeat Annex travel requires the same facts except `FLAG_ANNEX_EXIT_CLEARED=true`. Those two rows share one source/trigger but are exhaustive and disjoint. The first recipe promotes checkpoint/chapter to Departure/4; the repeat recipe dynamically records the exact stable source while retaining every checkpoint, chapter, result, and encounter field, so it cannot regress a later Rusk Return/Victory or chapter-complete page. Ordinary Annex-node selection additionally requires `MAP_SELECTION_ANNEX`; first Estate arrival requires `MAP_SELECTION_ESTATE`, Estate unlocked, `estate_arrived=false`, and follower inactive; ordinary Estate reselection requires the same selection with `estate_arrived=true` and follower inactive; ordinary Estate exit requires `estate_arrived=true` and follower inactive; Estate door/study stair conditions read their named monotonic flags; Rusk start requires confrontation seen and battle not won; snapshot validity requires `PRE_RUSK_SNAPSHOT_VALID` for the current runtime generation. `COND_TRANS_RETURN_FOLLOWER_ACTIVE` is follower-active only and is legal for the Estate-skimmer-to-map handoff; the two map programs are distinct: `_ANNEX_SELECTED` is follower active AND `MAP_SELECTION_ANNEX`, while `_ESTATE_SELECTED` is follower active AND `MAP_SELECTION_ESTATE`. No ConditionId changes meaning by caller. The hook condition requires `RUNTIME_CHECKPOINT_SLICE_COMPLETE_COMMITTED`. `MAP_SELECTION_BACK` bypasses node conditions only through the generation-current `MapOriginSnapshot` and exact three-row cancel router; it never means stay on the map or select an arbitrary node transition.

Every nonzero reverse reference resolves to a portal-paired row. The two Estate-node menu rows with follower false split on `estate_arrived`, while the follower-true row safely returns Tavi to `SPAWN_ESTATE_COURTYARD_FROM_MAP`; all three are disjoint without priority. Likewise `ESTATE_TO_MAP` versus `STUDY_RETURN_TO_MAP` and `MAP_TO_THRESHOLD` versus `MAP_RETURN_TO_ANNEX` split on the same false/true return-follower predicate. Back from the return confirmation stays on the map and changes no ownership. The route never teleports from the study: ordinary follower handoffs carry Tavi Study -> Invention Hall -> Foyer -> Courtyard, the skimmer row carries Courtyard -> Estate map node, and the selected map row carries either back to the Estate courtyard or to Annex threshold before `THRESHOLD_TO_ATRIUM` completes the return.

```c

typedef struct TransitionRequest {
    TransitionId transition_id;    /* 0: fixes source/destination submodes */
    SceneId source_scene_id;       /* 2 */
    SceneId destination_scene_id;  /* 4 */
    ZoneId destination_zone_id;    /* 6 */
    SpawnId destination_spawn_id;  /* 8 */
    uint8_t reason;                /* 10 */
    uint8_t style;                 /* 11 */
    uint8_t save_policy;           /* 12 */
    uint8_t phase;                 /* 13 */
    uint16_t reserved;             /* 14 */
    uint32_t token;                /* 16: nonzero monotonic runtime generation */
    uint32_t requested_tick;       /* 20 */
    uint16_t flags;                /* 24 */
    uint16_t error_code;           /* 26: TransitionErrorCodeValue */
    uint32_t rollback_descriptor_generation; /* 28: exact immutable descriptor */
} TransitionRequest;
_Static_assert(sizeof(TransitionRequest) == 32, "TransitionRequest layout");
```

The request is runtime-only. Its duplicated destination/reason/style/save/flags fields must equal the selected immutable `TransitionDef`; this makes telemetry convenient without introducing another authority. Destination validity and the exact `ConditionId` are checked before `REQUESTED`. Before publishing REQUESTED, the controller creates exactly one process-resident provisional `TransitionRollbackDescriptor`: it validates the physical source tuple against the selected TransitionDef/current scene owner and legal Spawn registry, captures the complete required-load closure identity and recovery resources, binds the request token/generation, leaves `bound_runtime_generation`, `source_state_hash`, and `identity_crc32` zero, and stores its descriptor generation in the request. This rejects an unrecoverable route before any story/save publish without prematurely freezing mutable progress.

The descriptor becomes immutable only in an explicit finalization step immediately before QUIESCE. Finalization captures the then-current runtime generation and canonical source reconstruction state, sets `TRANS_ROLLBACK_SOURCE_STATE_CAPTURED`, and computes `identity_crc32` over fields `0..39`. For `SAVE_BEFORE_AT_SAFE_SOURCE`, this step occurs only after the immutable pre-save reaches COMMITTED or explicit Travel Unsaved publishes the exact prospective recipe; Cancel destroys the provisional descriptor. Every other policy finalizes after its source-side validation and before QUIESCE. A request cannot enter QUIESCE with a provisional descriptor. A missing/stale generation, request-token mismatch, invalid final CRC, wrong source tuple, manifest CRC/size disagreement, or source state that cannot be reconstructed rejects/unwinds the request without teardown.

Descriptor flags accept only `0x007F`. Provisional state requires exactly `SOURCE_TUPLE_VALIDATED + MANIFEST_IDENTITY_CAPTURED + REQUEST_BOUND + PROCESS_SAFE_COPY`, plus exact ACTION_BUNDLE/SAVELOC presence bits; `SOURCE_STATE_CAPTURED` must be clear and the three final-only fields zero. Final state requires all first five flags plus the same presence bits and nonzero generation/state/CRC. ACTION_BUNDLE_PRESENT exactly matches nonzero `source_action_bundle_id`; SAVELOC_PRESENT exactly matches a condition-valid nonzero source SaveableLocationId. Non-saveable process/name/world-map/battle sources use zero saveloc but must still resolve an exact source Scene/Zone/Spawn and load manifest. The source tuple is the controller's coherent current tuple, never inferred from the destination or reverse transition. The descriptor stores no scene pointer, allocator handle, actor pointer, collision pointer, or audio handle. `source_state_hash` selects a fixed field-copied reconstruction record owned by the source scene registry; its generation and manifest identity must both match before reveal.

Only the controller mutates phase and error. `error_code` is NONE in IDLE through REVEAL. A destination shell/stage/enter/precommit failure records its exact destination error and enters ROLLBACK_SOURCE after destroying every partial destination scope. Successful source reconstruction validates the descriptor again, rebinds a fresh source generation, then enters ordinary TRANSITION_FAILED while retaining the destination error for the visible `Travel could not be completed.` page. That page can close only after the source scene is coherent. Failure to prepare/load/enter the source replaces the error with the corresponding SOURCE_ROLLBACK code and enters ROLLBACK_FATAL; descriptor-invalid is legal only when the process-resident copy itself fails validation. ROLLBACK_FATAL never exposes a scene and can select only the process-safe recovery binding. Retry uses the same immutable descriptor but a fresh load attempt/generation; a successful retry reaches ordinary TRANSITION_FAILED with coherent source ownership. Return-to-Title destroys the descriptor only after clean return or confirmed dirty-loss teardown commits. Error NONE in either failed phase, a destination error in ROLLBACK_FATAL, a source error outside ROLLBACK_FATAL, or release of the descriptor while request/recovery UI remains active is an assertion failure.

`TRANSITION_FLAG_RETAIN_IDENTICAL_REQUIRED_BASE` is valid only for `ZONE_SIM_ARENA -> ZONE_ANNEX_SIMULATION_ROOM`; validation compares the full required-bundle AssetId/CRC/unpacked-size identity in both load manifests.

```c
typedef struct RetainedBaseHandoffSnapshot {
    uint32_t source_generation;       /* 0 */
    uint32_t destination_generation;  /* 4 */
    BundleId base_bundle_id;          /* 8 */
    ZoneId source_zone_id;            /* 10 */
    ZoneId destination_zone_id;       /* 12 */
    BundleId source_action_bundle_id; /* 14 */
    SpawnId source_spawn_id;          /* 16 */
    SceneId source_scene_id;           /* 18 */
    uint32_t source_state_token;       /* 20 */
    uint16_t flags;                    /* 24 */
    uint16_t reserved;                 /* 26 */
    uint32_t identity_crc32;           /* 28 */
} RetainedBaseHandoffSnapshot;
_Static_assert(sizeof(RetainedBaseHandoffSnapshot) == 32, "RetainedBaseHandoffSnapshot layout");

enum RetainedBaseHandoffFlags {
    RETAIN_BASE_IDENTITY_VERIFIED = 1u << 0,
    RETAIN_BASE_SOURCE_ACTION_DESTROYED = 1u << 1,
    RETAIN_BASE_DESTINATION_STAGED = 1u << 2,
    RETAIN_BASE_COMMITTED = 1u << 3
};
```

`RetainedBaseHandoffSnapshot.flags` accepts only `0x000F` and follows the prefix lifecycle `IDENTITY_VERIFIED -> SOURCE_ACTION_DESTROYED -> DESTINATION_STAGED -> COMMITTED`; each later bit requires every earlier bit. Reserved is zero. After the action/render fence, the controller records this source snapshot and destroys the tutorial overlay. While the base remains source-owned, it validates destination prerequisites and stages destination-only onboarding resources in a pending scope. The no-fail commit atomically retags the base to the destination generation, publishes destination handles, invalidates all overlay handles, and proves no other source resource survived. Identity mismatch performs normal unload/load. An unexpected post-commit failure destroys the pending destination scope, atomically retags the base back to `source_generation`, and restores the exact recorded source scene/zone/spawn/action bundle plus `source_state_token` (reloading only that source action if required) before revealing the normal rollback message. A generation assertion prevents either scene state from observing mixed handles.

SavePolicy order is executable and exclusive:

1. `SAVE_NONE`: validate the request, then QUIESCE/FENCE/UNLOAD/STAGE/COMMIT with no snapshot or write.
2. `SAVE_BEFORE_AT_SAFE_SOURCE`: while the rollback descriptor is provisional and the source remains fully owned, resolve the binding's pre recipe against prospective scratch progress, prevalidate its action/resources/save tuple, and encode an immutable source-stable save snapshot. A successful write no-fail publishes that same scratch recipe; `TRAVEL UNSAVED` publishes it and marks runtime dirty. Either terminal proceed outcome then finalizes the rollback descriptor against the newly published runtime generation/state immediately before QUIESCE. `RETRY` repeats the identical immutable save bytes without finalizing; `CANCEL` discards scratch/reservations plus the provisional descriptor and returns source control unchanged. Destination failure therefore reconstructs the post-recipe source state; a successful/unsaved pre recipe remains committed and retryable, never half-reverted.
3. `SAVE_AFTER_DESTINATION_COMMIT`: no save occurs at source. After successful destination `enter` inside COMMIT, resolve `TRANS_RECIPE_STABLE_DESTINATION_TRANSITION`, atomically publish the destination LocationKeys, then enqueue its immutable transition-reason snapshot. Write failure leaves coherent destination progress dirty with Retry/Continue; it never reloads source or claims persistence.
4. `SAVE_AFTER_STORY_TRANSACTION`: stage destination and the binding's post recipe together. After successful `enter`, atomically publish destination ownership plus the exact recipe/action fields, then enqueue that immutable snapshot. Destination/action/recipe failure before publish destroys destination staging and restores source progress unchanged. Write failure after publish leaves coherent destination story dirty with Retry/Continue; it cannot roll back already revealed state.

Only committed source/destination progress is encodable; REQUESTED through STAGE is never serialized. The finalized rollback descriptor stores the source scene/zone/spawn and the exact runtime generation after every permitted pre-source publish. Destination failure destroys its partial scope, normally reloads that source state, shows `Travel could not be completed.`, and restores retry control; process-safe menu is only for rollback-load failure. A mandatory golden covers first Annex departure: the pre-save commits, destination load fails, rollback restores the threshold with departure flag/checkpoint/once bit intact and clean; the Travel Unsaved variant restores the same facts dirty. `ZONE_END_CARD_UI` is a legal runtime destination but `SCENE_NON_SAVEABLE_UI` prevents it from entering either LocationKey.

### 13.2 Process UI and navigation

#### 13.2.1 Process/UI binding registry

Process pages are assembled from typed items rather than controller-embedded
DialogueIds, StringIds, or copy. A binding key is exactly
`(scene_id, owner_id, state_variant)`; `scene_id=0` is legal only for the
eighteen explicit global/process-overlay owners represented by the table below.

```c
typedef enum ProcessUiOwnerIdValue {
    PROCESS_UI_OWNER_TITLE_MENU = 1,
    PROCESS_UI_OWNER_TITLE_NEW_GAME_PROMPT = 2,
    PROCESS_UI_OWNER_TITLE_OVERWRITE_PROMPT = 3,
    PROCESS_UI_OWNER_TITLE_INVALID_SAVE_PROMPT = 4,
    PROCESS_UI_OWNER_OPENING_CUTSCENE_SLATE = 5,
    PROCESS_UI_OWNER_NAME_ENTRY_SURFACE = 6,
    PROCESS_UI_OWNER_NAME_VALIDATION_EMPTY = 7,
    PROCESS_UI_OWNER_NAME_CONFIRM_PROMPT = 8,
    PROCESS_UI_OWNER_NAME_CANCEL_PROMPT = 9,
    PROCESS_UI_OWNER_OPTIONS_FOOTER = 10,
    PROCESS_UI_OWNER_INTERACTION_PROMPT_RENDERER = 11,
    PROCESS_UI_OWNER_CONTROLLER = 12,
    PROCESS_UI_OWNER_SAVE_SERVICE = 13,
    PROCESS_UI_OWNER_TRANSITION_LOADING_CARD = 14,
    PROCESS_UI_OWNER_TRANSITION_FAILURE = 15,
    PROCESS_UI_OWNER_WORLD_MAP = 16,
    PROCESS_UI_OWNER_END_CHAPTER_MARK = 17,
    PROCESS_UI_OWNER_FINAL_SAVE_FAILURE = 18,
    PROCESS_UI_OWNER_END_CARD_MENU = 19,
    PROCESS_UI_OWNER_END_DIRTY_RETURN_WARNING = 20,
    PROCESS_UI_OWNER_PRE_TRANSITION_SAVE_FAILURE = 21,
    PROCESS_UI_OWNER_COMMITTED_PROGRESS_SAVE_FAILURE = 22,
    PROCESS_UI_OWNER_RETENTION_ONCE_SAVE_FAILURE = 23,
    PROCESS_UI_OWNER_MANUAL_SETTINGS_SAVE_FAILURE = 24,
    PROCESS_UI_OWNER_ROLLBACK_FATAL = 25,
    PROCESS_UI_OWNER_ROLLBACK_DIRTY_RETURN_WARNING = 26,
    PROCESS_UI_OWNER_NEW_GAME_INITIALIZATION_SAVE_FAILURE = 27,
    PROCESS_UI_OWNER_PAUSE_MENU = 28,
    PROCESS_UI_OWNER_FIELD_RELAY = 29,
    PROCESS_UI_OWNER_MANUAL_SAVE_CONFIRM = 30
} ProcessUiOwnerIdValue;

typedef enum ProcessUiStateVariantValue {
    PROCESS_UI_STATE_DEFAULT = 1,
    PROCESS_UI_STATE_CONTROLLER_DISCONNECTED = 2,
    PROCESS_UI_STATE_CONTROLLER_RECONNECT = 3,
    PROCESS_UI_STATE_SAVE_WRITING = 4,
    PROCESS_UI_STATE_SAVE_DONE = 5,
    PROCESS_UI_STATE_LOADING_ANNEX = 6,
    PROCESS_UI_STATE_LOADING_ESTATE = 7,
    PROCESS_UI_STATE_TRANSITION_BUSY = 8,
    PROCESS_UI_STATE_TRANSITION_FAILED = 9,
    PROCESS_UI_STATE_ROLLBACK_FATAL = 10,
    PROCESS_UI_STATE_RELAY_PARTY = 11,
    PROCESS_UI_STATE_RELAY_MESSAGES = 12,
    PROCESS_UI_STATE_RELAY_RESONANCE = 13,
    PROCESS_UI_STATE_RELAY_MAP = 14,
    PROCESS_UI_STATE_RELAY_SAVE = 15
} ProcessUiStateVariantValue;

typedef enum ProcessUiLayoutValue {
    PROCESS_UI_LAYOUT_FIXED_MENU = 1,
    PROCESS_UI_LAYOUT_MODAL_CHOICE = 2,
    PROCESS_UI_LAYOUT_CO_RENDER_LAYERS = 3,
    PROCESS_UI_LAYOUT_PERSISTENT_SURFACE = 4,
    PROCESS_UI_LAYOUT_SINGLE_STATUS = 5,
    PROCESS_UI_LAYOUT_CAPABILITY_SELECT_ONE = 6,
    PROCESS_UI_LAYOUT_WORLD_MAP = 7,
    PROCESS_UI_LAYOUT_TIMED_SEQUENCE = 8,
    PROCESS_UI_LAYOUT_TABBED_RUNTIME_VIEW = 9
} ProcessUiLayoutValue;

typedef enum ProcessUiContentSourceValue {
    PROCESS_UI_CONTENT_DIALOGUE_PAGE = 1,
    PROCESS_UI_CONTENT_STATIC_STRING = 2,
    PROCESS_UI_CONTENT_RUNTIME_VIEW = 3
} ProcessUiContentSourceValue;

typedef enum ProcessUiRuntimeViewIdValue {
    PROCESS_UI_VIEW_SETTINGS_EDITOR = 1,
    PROCESS_UI_VIEW_RELAY_PARTY = 2,
    PROCESS_UI_VIEW_RELAY_MESSAGES = 3,
    PROCESS_UI_VIEW_RELAY_RESONANCE = 4,
    PROCESS_UI_VIEW_RELAY_MAP = 5,
    PROCESS_UI_VIEW_RELAY_SAVE = 6
} ProcessUiRuntimeViewIdValue;

typedef enum ProcessUiAcceptKindValue {
    PROCESS_UI_ACCEPT_NONE = 0,
    PROCESS_UI_ACCEPT_PROCESS_TOKEN = 1,
    PROCESS_UI_ACCEPT_LOCAL_ACTION = 2
} ProcessUiAcceptKindValue;

typedef enum ProcessUiLocalActionValue {
    PROCESS_UI_ACTION_OPEN_NEW_GAME_PROMPT = 1,
    PROCESS_UI_ACTION_OPEN_OPTIONS = 2,
    PROCESS_UI_ACTION_CLOSE_NO_MUTATION = 3,
    PROCESS_UI_ACTION_RETURN_TO_NAME_GRID = 4,
    PROCESS_UI_ACTION_APPLY_SETTINGS = 5,
    PROCESS_UI_ACTION_CANCEL_SETTINGS = 6,
    PROCESS_UI_ACTION_INTERACTION_CAPABILITY = 7,
    PROCESS_UI_ACTION_CONTROLLER_RESTORE = 8,
    PROCESS_UI_ACTION_MAP_ROUTE_ACCEPT = 9,
    PROCESS_UI_ACTION_SAVE_RETRY_IMMUTABLE = 10,
    PROCESS_UI_ACTION_SAVE_CONTINUE_DIRTY = 11,
    PROCESS_UI_ACTION_END_CONTINUE_EXPLORING = 12,
    PROCESS_UI_ACTION_DIRTY_STAY = 13,
    PROCESS_UI_ACTION_SAVE_TRAVEL_UNSAVED = 14,
    PROCESS_UI_ACTION_SAVE_CANCEL_TO_OWNER = 15,
    PROCESS_UI_ACTION_RETRY_ROLLBACK_LOAD = 16,
    PROCESS_UI_ACTION_ROLLBACK_RETURN_TO_TITLE = 17,
    PROCESS_UI_ACTION_PAUSE_RESUME = 18,
    PROCESS_UI_ACTION_OPEN_PARTY = 19,
    PROCESS_UI_ACTION_OPEN_FIELD_RELAY = 20,
    PROCESS_UI_ACTION_RELAY_OPEN_PARTY = 21,
    PROCESS_UI_ACTION_RELAY_OPEN_MESSAGES = 22,
    PROCESS_UI_ACTION_RELAY_OPEN_RESONANCE = 23,
    PROCESS_UI_ACTION_RELAY_OPEN_MAP = 24,
    PROCESS_UI_ACTION_RELAY_OPEN_SAVE = 25,
    PROCESS_UI_ACTION_RETURN_TO_CAPTURED_ORIGIN = 26,
    PROCESS_UI_ACTION_MANUAL_SAVE_OPEN_CONFIRM = 27,
    PROCESS_UI_ACTION_MANUAL_SAVE_SUBMIT = 28,
    PROCESS_UI_ACTION_SETTINGS_EDIT = 29,
    PROCESS_UI_ACTION_SETTINGS_RESET_DEFAULTS = 30
} ProcessUiLocalActionValue;

typedef enum ProcessStaticStringIdValue {
    STR_SAVE_FAILURE_FINAL_REPLAY_WARNING = 0x9F01,
    STR_SAVE_FAILURE_PRE_TRANSITION = 0x9F02,
    STR_SAVE_FAILURE_COMMITTED_PROGRESS = 0x9F03,
    STR_SAVE_FAILURE_RETENTION_ONCE = 0x9F04,
    STR_SAVE_FAILURE_MANUAL_SETTINGS = 0x9F05,
    STR_PROCESS_RECOVERY_FATAL = 0x9F06,
    STR_PROCESS_RECOVERY_RETRY = 0x9F07,
    STR_PROCESS_RECOVERY_RETURN_TITLE = 0x9F08,
    STR_SAVE_FAILURE_NEW_GAME_INITIALIZATION = 0x9F09,
    STR_SETTINGS_TEXT_SPEED = 0x9F0A,
    STR_SETTINGS_CAMERA = 0x9F0B,
    STR_SETTINGS_INVERT_X = 0x9F0C,
    STR_SETTINGS_INVERT_Y = 0x9F0D,
    STR_SETTINGS_MUSIC_VOLUME = 0x9F0E,
    STR_SETTINGS_SFX_VOLUME = 0x9F0F,
    STR_SETTINGS_RUMBLE = 0x9F10,
    STR_SETTINGS_OVERSCAN_X = 0x9F11,
    STR_SETTINGS_OVERSCAN_Y = 0x9F12,
    STR_SETTINGS_UI_CONTRAST = 0x9F13,
    STR_SETTINGS_RESET_DEFAULTS = 0x9F14,
    STR_PAUSE_RESUME = 0x9F15,
    STR_PAUSE_PARTY = 0x9F16,
    STR_PAUSE_FIELD_RELAY = 0x9F17,
    STR_PAUSE_SETTINGS = 0x9F18,
    STR_RELAY_MESSAGES = 0x9F19,
    STR_RELAY_RESONANCE = 0x9F1A,
    STR_RELAY_MAP = 0x9F1B,
    STR_RELAY_SAVE = 0x9F1C,
    STR_UI_BACK = 0x9F1D,
    STR_MANUAL_RECORD_PROGRESS = 0x9F1E,
    STR_MANUAL_SAVE_CONFIRM = 0x9F1F,
    STR_MANUAL_SAVE_ACCEPT = 0x9F20,
    STR_MANUAL_SAVE_BLOCKED = 0x9F21,
    STR_VALUE_SLOW = 0x9F22,
    STR_VALUE_NORMAL = 0x9F23,
    STR_VALUE_FAST = 0x9F24,
    STR_VALUE_OFF = 0x9F25,
    STR_VALUE_ON = 0x9F26,
    STR_VALUE_STANDARD = 0x9F27,
    STR_VALUE_HIGH = 0x9F28,
    STR_VALUE_REDUCED_FLASH = 0x9F29,
    STR_RELAY_NO_PARTY = 0x9F2A,
    STR_RELAY_READ = 0x9F2B,
    STR_RELAY_PENDING = 0x9F2C,
    STR_RELAY_RESOLVED = 0x9F2D,
    STR_RELAY_TRAVEL_SKIMMER = 0x9F2E,
    STR_RELAY_TEAM_LINK = 0x9F2F,
    STR_RELAY_SYNC = 0x9F30,
    STR_RELAY_CURRENT_LOCATION = 0x9F31,
    STR_RELAY_CHECKPOINT = 0x9F32,
    STR_RELAY_LAST_RECORD = 0x9F33,
    STR_RELAY_STATUS = 0x9F34,
    STR_RELAY_RECORD = 0x9F35,
    STR_RELAY_RESONANCE_EXPLANATION = 0x9F36,
    STR_RELAY_LOCKED = 0x9F37,
    STR_RELAY_UNLOCKED = 0x9F38,
    STR_RELAY_HP = 0x9F39,
    STR_RELAY_MOVES = 0x9F3A,
    STR_RELAY_LEFT = 0x9F3B,
    STR_RELAY_RIGHT = 0x9F3C,
    STR_RELAY_CLEAN = 0x9F3D,
    STR_RELAY_UNSAVED = 0x9F3E,
    STR_LOC_SIMULATION_ARENA = 0x9F3F,
    STR_LOC_ANNEX_SIMULATION_ROOM = 0x9F40,
    STR_LOC_ANNEX_ATRIUM = 0x9F41,
    STR_LOC_ANNEX_DIRECTOR_LAB = 0x9F42,
    STR_LOC_ANNEX_PLAYER_ROOM = 0x9F43,
    STR_LOC_ANNEX_CLINIC = 0x9F44,
    STR_LOC_ANNEX_WORKSHOP = 0x9F45,
    STR_LOC_ANNEX_THRESHOLD = 0x9F46,
    STR_LOC_ESTATE_COURTYARD = 0x9F47,
    STR_LOC_ESTATE_FOYER = 0x9F48,
    STR_LOC_ESTATE_INVENTION_HALL = 0x9F49,
    STR_LOC_ESTATE_OBSERVATORY_STUDY = 0x9F4A,
    STR_CHECKPOINT_NONE = 0x9F4B,
    STR_CHECKPOINT_AFTER_NAME = 0x9F4C,
    STR_CHECKPOINT_AFTER_TUTORIAL = 0x9F4D,
    STR_CHECKPOINT_FIELD_RELAY = 0x9F4E,
    STR_CHECKPOINT_ANNEX_DEPARTURE = 0x9F4F,
    STR_CHECKPOINT_ESTATE_ARRIVAL = 0x9F50,
    STR_CHECKPOINT_RUSK_VICTORY = 0x9F51,
    STR_CHECKPOINT_TAVI_FOUND = 0x9F52,
    STR_CHECKPOINT_TAVI_RETURNED = 0x9F53,
    STR_CHECKPOINT_SLICE_COMPLETE = 0x9F54,
    STR_CHECKPOINT_RUSK_RETURN = 0x9F55,
    STR_CHECKPOINT_ANNEX_TRACE = 0x9F56,
    STR_SAVE_REASON_NONE = 0x9F57,
    STR_SAVE_REASON_CHECKPOINT = 0x9F58,
    STR_SAVE_REASON_MANUAL_RELAY = 0x9F59,
    STR_SAVE_REASON_BATTLE_RESULT = 0x9F5A,
    STR_SAVE_REASON_FINAL_HOOK = 0x9F5B,
    STR_SAVE_REASON_TRANSITION = 0x9F5C,
    STR_SAVE_REASON_SETTINGS = 0x9F5D,
    STR_SAVE_STATE_READY = 0x9F5E,
    STR_SAVE_STATE_QUEUED = 0x9F5F,
    STR_SAVE_STATE_WRITING = 0x9F60,
    STR_SAVE_STATE_VERIFYING = 0x9F61,
    STR_SAVE_STATE_RECORDED = 0x9F62,
    STR_SAVE_STATE_FAILED = 0x9F63,
    STR_SAVE_STATE_CANCELED = 0x9F64,
    STR_SAVE_STATE_TRAVELED_UNSAVED = 0x9F65,
    STR_SAVE_STATE_ABORTED = 0x9F66,
    STR_MANUAL_SAVE_AVAILABLE = 0x9F67
} ProcessStaticStringIdValue;

typedef enum TitleJournalDispositionValue {
    TITLE_JOURNAL_EMPTY = 0,
    TITLE_JOURNAL_VALID = 1,
    TITLE_JOURNAL_INVALID_OR_INCOMPATIBLE = 2
} TitleJournalDispositionValue;

typedef struct TitleNewGameRouteDef {
    uint8_t journal_disposition; /* 0: TitleJournalDispositionValue */
    uint8_t reserved;            /* 1: zero */
    uint16_t target_owner_id;    /* 2: ProcessUiOwnerIdValue */
} TitleNewGameRouteDef;
_Static_assert(sizeof(TitleNewGameRouteDef) == 4, "TitleNewGameRouteDef layout");

typedef enum NewGameWriteAuthorityStateValue {
    NEW_GAME_WRITE_AUTHORITY_NONE = 0,
    NEW_GAME_WRITE_AUTHORITY_CONFIRMED = 1,
    NEW_GAME_WRITE_AUTHORITY_CONSUMED = 2
} NewGameWriteAuthorityStateValue;

typedef enum NewGameJournalPageClassValue {
    NEW_GAME_PAGE_BYTES_EMPTY = 0,
    NEW_GAME_PAGE_ENVELOPE_INVALID = 1,
    NEW_GAME_PAGE_SUPPORTED_GENERAL = 2,
    NEW_GAME_PAGE_SUPPORTED_SLICE_FINAL = 3,
    NEW_GAME_PAGE_SUPPORTED_SEMANTIC_INVALID = 4,
    NEW_GAME_PAGE_UNSUPPORTED_ENVELOPE_VALID = 5
} NewGameJournalPageClassValue;

enum NewGameJournalWritePlanFlags {
    NEW_GAME_PLAN_LOADER_GENERATION_CURRENT = 1u << 0,
    NEW_GAME_PLAN_RAW_PAGE_IDENTITIES_CAPTURED = 1u << 1,
    NEW_GAME_PLAN_USER_CONFIRMATION_ACCEPTED = 1u << 2,
    NEW_GAME_PLAN_OVERWRITE_EXISTING = 1u << 3,
    NEW_GAME_PLAN_AMBIGUITY_OVERWRITE_ACCEPTED = 1u << 4,
    NEW_GAME_PLAN_REQUIRE_EXACT_REREAD_MATCH = 1u << 5,
    NEW_GAME_PLAN_FIRST_CAMPAIGN_WRITE = 1u << 6
};

typedef struct NewGameJournalWritePlan {
    uint32_t loader_generation;      /* 0 */
    uint32_t confirmation_epoch;     /* 4: nonzero debounced user edge */
    uint32_t plan_generation;        /* 8: nonzero runtime-draft owner */
    uint8_t page_a_raw[240];         /* 12: exact confirmation-time bytes */
    uint8_t page_b_raw[240];         /* 252: exact confirmation-time bytes */
    uint32_t page_a_identity_crc32;  /* 492: optimization over page_a_raw */
    uint32_t page_b_identity_crc32;  /* 496: optimization over page_b_raw */
    uint32_t page_a_sequence;        /* 500: exact decoded header bits; zero is valid data */
    uint32_t page_b_sequence;        /* 504: exact decoded header bits; zero is valid data */
    uint16_t page_a_schema;          /* 508: exact decoded header bits */
    uint16_t page_b_schema;          /* 510: exact decoded header bits */
    uint8_t page_a_class;            /* 512: NewGameJournalPageClassValue */
    uint8_t page_b_class;            /* 513: NewGameJournalPageClassValue */
    uint8_t journal_disposition;     /* 514: TitleJournalDispositionValue */
    uint8_t planned_anchor_page;     /* 515: SaveJournalPageValue */
    uint8_t planned_target_page;     /* 516: SaveJournalPageValue */
    uint8_t reserved0[3];            /* 517: zero */
    uint32_t flags;                  /* 520 */
    uint32_t identity_crc32;         /* 524: CRC of immutable bytes 0..523 */
} NewGameJournalWritePlan;
_Static_assert(sizeof(NewGameJournalWritePlan) == 528, "NewGameJournalWritePlan layout");

typedef struct NewGameJournalWriteAuthority {
    uint32_t plan_generation;              /* 0: exact immutable-plan owner */
    uint32_t campaign_owner_generation;    /* 4: exact runtime-draft/campaign owner */
    uint32_t committed_request_generation; /* 8: zero until verified first commit */
    uint8_t state;                         /* 12: NewGameWriteAuthorityStateValue */
    uint8_t reserved[3];                   /* 13: zero */
} NewGameJournalWriteAuthority;
_Static_assert(sizeof(NewGameJournalWriteAuthority) == 16, "NewGameJournalWriteAuthority layout");

enum RuntimeDraftOwnerFlags {
    RUNTIME_DRAFT_OWNER_PLAN_PRESENT = 1u << 0,
    RUNTIME_DRAFT_OWNER_SETTINGS_SANITIZED = 1u << 1,
    RUNTIME_DRAFT_OWNER_CAMPAIGN_SEED_VALID = 1u << 2,
    RUNTIME_DRAFT_OWNER_OPENING_FINALIZED = 1u << 3,
    RUNTIME_DRAFT_OWNER_NAME_VALIDATED = 1u << 4,
    RUNTIME_DRAFT_OWNER_ACTIVE_SAVE_RESERVED = 1u << 5
};

typedef struct RuntimeDraftOwner {
    NewGameJournalWritePlan journal_plan;       /* 0: immutable while owner exists */
    NewGameJournalWriteAuthority write_authority;/* 528: monotonic lifecycle, outside plan CRC */
    GameSettings settings;                      /* 544: sanitized draft settings */
    uint32_t owner_generation;                  /* 552: nonzero campaign owner */
    uint32_t campaign_seed;                     /* 556: nonzero locked seed */
    uint32_t playtime_seconds;                  /* 560: opening accumulator snapshot */
    uint32_t settings_generation;               /* 564: nonzero draft settings owner */
    uint8_t player_name[8];                     /* 568: uppercase; zero padded */
    uint8_t player_name_length;                 /* 576: zero until confirmed, then 1..8 */
    uint8_t state;                              /* 577: RuntimeDraftStateValue */
    uint8_t opening_cinematic_seen;             /* 578: exact 0 or 1 */
    uint8_t flags;                              /* 579: RuntimeDraftOwnerFlags */
} RuntimeDraftOwner;
_Static_assert(sizeof(RuntimeDraftOwner) == 580, "RuntimeDraftOwner layout");

typedef struct FinalSaveOutcomeOwner {
    uint32_t campaign_owner_generation; /* 0: exact live campaign owner */
    uint32_t campaign_seed;             /* 4: equality mirror of live SaveData */
    uint8_t outcome;                    /* 8: FinalSaveOutcomeValue */
    uint8_t reserved[3];                /* 9: zero */
} FinalSaveOutcomeOwner;
_Static_assert(sizeof(FinalSaveOutcomeOwner) == 12, "FinalSaveOutcomeOwner layout");

typedef enum ProcessUiOriginKindValue {
    PROCESS_UI_ORIGIN_GAMEPLAY = 1,
    PROCESS_UI_ORIGIN_PAUSE = 2,
    PROCESS_UI_ORIGIN_TITLE = 3
} ProcessUiOriginKindValue;

typedef struct ProcessUiOriginSnapshot {
    SceneId scene_id;                  /* 0: zero only for Title/owner origin */
    ZoneId zone_id;                    /* 2 */
    SpawnId spawn_id;                  /* 4: current stable location key */
    uint16_t source_owner_id;          /* 6: zero only for gameplay */
    uint16_t source_state_variant;     /* 8 */
    uint8_t source_focus;              /* 10: 0xFF for gameplay */
    uint8_t origin_kind;               /* 11: ProcessUiOriginKindValue */
    uint32_t control_generation;       /* 12: exploration control generation or BattleRuntimeOwner.battle_generation */
    uint32_t source_owner_generation;  /* 16: zero only for gameplay */
    uint32_t campaign_owner_generation;/* 20: zero only for Title */
} ProcessUiOriginSnapshot;
_Static_assert(sizeof(ProcessUiOriginSnapshot) == 24, "ProcessUiOriginSnapshot layout");

typedef enum PauseMenuEntryIdValue {
    PAUSE_ENTRY_RESUME = 1,
    PAUSE_ENTRY_PARTY = 2,
    PAUSE_ENTRY_FIELD_RELAY = 3,
    PAUSE_ENTRY_SETTINGS = 4,
    PAUSE_ENTRY_RETURN_TO_TITLE = 5
} PauseMenuEntryIdValue;

enum PauseMenuAvailabilityFlags {
    PAUSE_REQUIRE_PARTY_PRESENT = 1u << 0,
    PAUSE_REQUIRE_RELAY_UNLOCKED = 1u << 1,
    PAUSE_REQUIRE_ALL_RELAY_BITS = 1u << 2,
    PAUSE_REQUIRE_SETTINGS_LOCATION = 1u << 3,
    PAUSE_CAPTURE_CHILD_ORIGIN = 1u << 4,
    PAUSE_REQUIRE_NO_BATTLE_RUNTIME = 1u << 5
};

typedef struct PauseMenuRouteDef {
    uint8_t entry_id;          /* 0: PauseMenuEntryIdValue */
    uint8_t display_order;     /* 1: exact 0..4 */
    uint16_t availability;     /* 2: PauseMenuAvailabilityFlags */
    uint8_t accept_kind;       /* 4: ProcessUiAcceptKindValue */
    uint8_t reserved0;         /* 5: zero */
    uint16_t accept_value;     /* 6: typed token or local action */
    uint16_t target_owner_id;  /* 8: zero for Resume/Return */
    uint16_t target_state;     /* 10 */
} PauseMenuRouteDef;
_Static_assert(sizeof(PauseMenuRouteDef) == 12, "PauseMenuRouteDef layout");

typedef enum RelayPageIdValue {
    RELAY_PAGE_PARTY = 1,
    RELAY_PAGE_MESSAGES = 2,
    RELAY_PAGE_RESONANCE = 3,
    RELAY_PAGE_MAP = 4,
    RELAY_PAGE_SAVE = 5
} RelayPageIdValue;

enum RelayPageFlags {
    RELAY_PAGE_ALLOW_PRE_RELAY_PARTY = 1u << 0,
    RELAY_PAGE_REQUIRE_RELAY_UNLOCKED = 1u << 1,
    RELAY_PAGE_REQUIRE_PERSISTED_BIT = 1u << 2,
    RELAY_PAGE_REQUIRE_ALL_PERSISTED_BITS = 1u << 3,
    RELAY_PAGE_PLAYER_SAVE_SURFACE = 1u << 4,
    RELAY_PAGE_INFORMATION_ONLY = 1u << 5
};

typedef struct RelayPageDef {
    uint8_t page_id;              /* 0: RelayPageIdValue */
    uint8_t tab_order;            /* 1: exact 0..4 */
    uint8_t required_page_bit;    /* 2: RelayPageBit or 0xFF */
    uint8_t flags;                /* 3: RelayPageFlags */
    UIScreenId screen_id;         /* 4 */
    uint16_t runtime_view_id;     /* 6: ProcessUiRuntimeViewIdValue */
    uint16_t state_variant;       /* 8: ProcessUiStateVariantValue */
    uint16_t reserved;            /* 10: zero */
} RelayPageDef;
_Static_assert(sizeof(RelayPageDef) == 12, "RelayPageDef layout");

enum RelayRuntimeViewSourceFlags {
    RELAY_VIEW_SOURCE_VALIDATED_PARTY_SLOTS = 1u << 0,
    RELAY_VIEW_SOURCE_CREATURE_AND_MOVE_DEFS = 1u << 1,
    RELAY_VIEW_SOURCE_MESSAGE_ROWS = 1u << 2,
    RELAY_VIEW_SOURCE_STORY_FLAGS = 1u << 3,
    RELAY_VIEW_SOURCE_SYNC_AND_TEAM_LINK = 1u << 4,
    RELAY_VIEW_SOURCE_DESTINATION_BITS = 1u << 5,
    RELAY_VIEW_SOURCE_SAVE_LOCATION_REGISTRY = 1u << 6,
    RELAY_VIEW_SOURCE_SAVE_SERVICE_OWNER = 1u << 7
};

enum RelayRuntimeViewFlags {
    RELAY_VIEW_FIXED_FIELD_ORDER = 1u << 0,
    RELAY_VIEW_EXPLICIT_EMPTY_STATE = 1u << 1,
    RELAY_VIEW_EXPLICIT_LOCKED_STATE = 1u << 2,
    RELAY_VIEW_NO_STORY_MUTATION = 1u << 3,
    RELAY_VIEW_GENERATION_BOUND = 1u << 4
};

typedef struct RelayRuntimeViewDef {
    uint16_t runtime_view_id; /* 0: ProcessUiRuntimeViewIdValue */
    uint8_t page_id;          /* 2: RelayPageIdValue */
    uint8_t field_count;      /* 3: exact ordered fields described below */
    uint32_t source_flags;    /* 4: RelayRuntimeViewSourceFlags */
    uint16_t flags;           /* 8: RelayRuntimeViewFlags */
    uint16_t reserved0;       /* 10: zero */
    uint32_t reserved1;       /* 12: zero */
} RelayRuntimeViewDef;
_Static_assert(sizeof(RelayRuntimeViewDef) == 16, "RelayRuntimeViewDef layout");

typedef enum RelayRuntimeFieldSourceValue {
    RELAY_FIELD_PLAYER_NAME = 1,
    RELAY_FIELD_ACTIVE_MARKERS = 2,
    RELAY_FIELD_PARTY_ID_LEVEL = 3,
    RELAY_FIELD_PARTY_HP = 4,
    RELAY_FIELD_PARTY_SYNC = 5,
    RELAY_FIELD_PARTY_MOVES = 6,
    RELAY_FIELD_TEAM_LINK = 7,
    RELAY_FIELD_MESSAGE_SENDER_TITLE = 8,
    RELAY_FIELD_MESSAGE_STATE = 9,
    RELAY_FIELD_MESSAGE_LIST_POSITION = 10,
    RELAY_FIELD_MESSAGE_DETAIL = 11,
    RELAY_FIELD_MESSAGE_DETAIL_PAGE_POSITION = 12,
    RELAY_FIELD_RESONANCE_TEAM_LINK = 13,
    RELAY_FIELD_RESONANCE_LEFT_SYNC = 14,
    RELAY_FIELD_RESONANCE_RIGHT_SYNC = 15,
    RELAY_FIELD_RUSK_RECORD = 16,
    RELAY_FIELD_RESONANCE_EXPLANATION = 17,
    RELAY_FIELD_MAP_ANNEX = 18,
    RELAY_FIELD_MAP_ESTATE = 19,
    RELAY_FIELD_MAP_CURRENT_LOCATION = 20,
    RELAY_FIELD_MAP_SKIMMER_FOOTER = 21,
    RELAY_FIELD_SAVE_CURRENT_LOCATION = 22,
    RELAY_FIELD_SAVE_CHECKPOINT = 23,
    RELAY_FIELD_SAVE_REASON = 24,
    RELAY_FIELD_SAVE_DIRTY_STATE = 25,
    RELAY_FIELD_SAVE_SERVICE_STATUS = 26,
    RELAY_FIELD_SAVE_MANUAL_ELIGIBILITY = 27
} RelayRuntimeFieldSourceValue;

typedef enum RelayRuntimeFormatterValue {
    RELAY_FORMAT_REGISTERED_TEXT = 1,
    RELAY_FORMAT_PARTY_PAIR = 2,
    RELAY_FORMAT_HP_PAIR = 3,
    RELAY_FORMAT_U16_PAIR = 4,
    RELAY_FORMAT_MOVE_LIST_PAIR = 5,
    RELAY_FORMAT_MESSAGE_GRAPH_COPY = 6,
    RELAY_FORMAT_MESSAGE_STATE_LABEL = 7,
    RELAY_FORMAT_INDEX_OF_COUNT = 8,
    RELAY_FORMAT_LOCK_LABEL = 9,
    RELAY_FORMAT_DESTINATION_GRAPH_COPY = 10,
    RELAY_FORMAT_LOCATION_REGISTRY_NAME = 11,
    RELAY_FORMAT_CHECKPOINT_NAME = 12,
    RELAY_FORMAT_SAVE_REASON_NAME = 13,
    RELAY_FORMAT_DIRTY_LABEL = 14,
    RELAY_FORMAT_SAVE_SERVICE_STATE = 15,
    RELAY_FORMAT_MANUAL_ELIGIBILITY = 16,
    RELAY_FORMAT_U16 = 17
} RelayRuntimeFormatterValue;

enum RelayRuntimeFieldFlags {
    RELAY_FIELD_ALLOW_ZERO_LABEL = 1u << 0,
    RELAY_FIELD_USE_EMPTY_STRING = 1u << 1,
    RELAY_FIELD_GRAPH_COPY_NO_ACQUIRE = 1u << 2,
    RELAY_FIELD_STATIC_LABEL_IS_VALUE = 1u << 3,
    RELAY_FIELD_GENERATION_BOUND = 1u << 4
};

typedef struct RelayRuntimeFieldDef {
    uint16_t runtime_view_id; /* 0: ProcessUiRuntimeViewIdValue */
    uint8_t field_order;      /* 2: contiguous within view */
    uint8_t formatter;        /* 3: RelayRuntimeFormatterValue */
    StringId label_string_id; /* 4: ProcessStaticStringIdValue or zero by flag */
    StringId empty_string_id; /* 6: zero unless USE_EMPTY_STRING */
    uint16_t source_id;       /* 8: RelayRuntimeFieldSourceValue */
    uint16_t flags;           /* 10: RelayRuntimeFieldFlags */
} RelayRuntimeFieldDef;
_Static_assert(sizeof(RelayRuntimeFieldDef) == 12, "RelayRuntimeFieldDef layout");

typedef enum RelayDisplayStringDomainValue {
    RELAY_DISPLAY_SAVEABLE_LOCATION = 1,
    RELAY_DISPLAY_CHECKPOINT = 2,
    RELAY_DISPLAY_SAVE_REASON = 3,
    RELAY_DISPLAY_SAVE_REQUEST_PHASE = 4,
    RELAY_DISPLAY_MANUAL_ELIGIBILITY = 5
} RelayDisplayStringDomainValue;

typedef enum RelayManualEligibilityValue {
    RELAY_MANUAL_BLOCKED = 0,
    RELAY_MANUAL_AVAILABLE = 1,
    RELAY_MANUAL_BUSY = 2,
    RELAY_MANUAL_RECORDED = 3,
    RELAY_MANUAL_FAILED = 4
} RelayManualEligibilityValue;

typedef struct RelayDisplayStringDef {
    uint8_t domain;      /* 0: RelayDisplayStringDomainValue */
    uint8_t reserved0;   /* 1: zero */
    uint16_t value;      /* 2: domain enum value */
    StringId string_id;  /* 4: ProcessStaticStringIdValue */
    uint16_t reserved1;  /* 6: zero */
} RelayDisplayStringDef;
_Static_assert(sizeof(RelayDisplayStringDef) == 8, "RelayDisplayStringDef layout");

typedef enum RelayMessageIdValue {
    RELAY_MESSAGE_TAVI_CALIBRATION = 1,
    RELAY_MESSAGE_IVO_OBSERVATORY_PACKET = 2
} RelayMessageIdValue;

typedef enum RelayMessageStateRuleValue {
    RELAY_MESSAGE_STATE_READ_AFTER_RELAY_ACQUISITION = 1,
    RELAY_MESSAGE_STATE_PENDING_UNTIL_SOLACE_RESOLVED = 2
} RelayMessageStateRuleValue;

typedef struct RelayMessageDef {
    uint8_t message_id;                  /* 0: RelayMessageIdValue */
    uint8_t display_order;               /* 1 */
    DialogueId title_dialogue_id;        /* 2 */
    DialogueId detail_first_dialogue_id; /* 4 */
    DialogueId resolved_dialogue_id;     /* 6: zero if no alternate */
    uint8_t detail_page_count;           /* 8 */
    uint8_t state_rule;                  /* 9: RelayMessageStateRuleValue */
    uint16_t flags;                      /* 10: zero */
    uint32_t reserved;                   /* 12: zero */
} RelayMessageDef;
_Static_assert(sizeof(RelayMessageDef) == 16, "RelayMessageDef layout");

typedef struct SettingsRuntimeViewDef {
    uint16_t runtime_view_id;       /* 0: PROCESS_UI_VIEW_SETTINGS_EDITOR */
    uint8_t first_control;          /* 2: zero */
    uint8_t control_count;          /* 3: nine */
    StringId reset_label_string_id; /* 4 */
    uint16_t reset_action;          /* 6: ProcessUiLocalActionValue */
    uint8_t first_focus;            /* 8: zero */
    uint8_t reset_focus;            /* 9: nine */
    uint8_t apply_focus;            /* 10: ten */
    uint8_t cancel_focus;           /* 11: eleven */
    uint16_t flags;                 /* 12: zero; field rows own preview */
    uint16_t reserved;              /* 14: zero */
} SettingsRuntimeViewDef;
_Static_assert(sizeof(SettingsRuntimeViewDef) == 16, "SettingsRuntimeViewDef layout");

typedef enum UserSaveUiBusyBehaviorValue {
    USER_SAVE_BUSY_RETAIN_SCRATCH_AND_SHOW_SAVING = 1
} UserSaveUiBusyBehaviorValue;

enum UserSaveUiRouteFlags {
    USER_SAVE_REQUIRE_INITIALIZED_CAMPAIGN = 1u << 0,
    USER_SAVE_REQUIRE_STABLE_CONTROL = 1u << 1,
    USER_SAVE_REQUIRE_MANUAL_LOCATION = 1u << 2,
    USER_SAVE_REQUIRE_RELAY_AND_ALL_BITS = 1u << 3,
    USER_SAVE_REQUIRE_MODAL_CLOSED_BEFORE_CAPTURE = 1u << 4,
    USER_SAVE_RETAIN_ORIGIN_UNTIL_TERMINAL = 1u << 5,
    USER_SAVE_REQUIRE_CONTINUE_LOCATION = 1u << 6,
    USER_SAVE_ALLOW_SIM_INTRO_BOUNDARY = 1u << 7
};

typedef struct UserSaveUiRouteDef {
    uint16_t source_owner_id;   /* 0 */
    uint16_t source_state;      /* 2 */
    uint16_t confirm_owner_id;  /* 4: zero for Settings Apply */
    uint16_t failure_owner_id;  /* 6 */
    uint8_t producer_kind;      /* 8: SAVE_FAILURE_PRODUCER_SERVICE */
    uint8_t producer_id;        /* 9: SaveFailureServiceProducerIdValue */
    uint8_t save_reason;        /* 10: SaveReason */
    uint8_t busy_behavior;      /* 11: UserSaveUiBusyBehaviorValue */
    uint16_t flags;             /* 12: UserSaveUiRouteFlags */
    uint16_t reserved;          /* 14: zero */
} UserSaveUiRouteDef;
_Static_assert(sizeof(UserSaveUiRouteDef) == 16, "UserSaveUiRouteDef layout");

typedef enum DirtyReturnOriginValue {
    DIRTY_RETURN_ORIGIN_GAMEPLAY = 1,
    DIRTY_RETURN_ORIGIN_END_CARD = 2,
    DIRTY_RETURN_ORIGIN_ROLLBACK_FATAL = 3
} DirtyReturnOriginValue;

typedef struct DirtyReturnWarningOwner {
    uint32_t generation;                /* 0: nonzero warning generation */
    uint32_t retained_owner_generation; /* 4 */
    uint32_t campaign_owner_generation; /* 8 */
    uint16_t source_owner_id;            /* 12 */
    uint16_t source_state;               /* 14 */
    uint8_t source_focus;                /* 16 */
    uint8_t origin;                      /* 17: DirtyReturnOriginValue */
    uint8_t required_ack;                /* 18: DirtyWarningAckValue */
    uint8_t reserved;                    /* 19: zero */
} DirtyReturnWarningOwner;
_Static_assert(sizeof(DirtyReturnWarningOwner) == 20, "DirtyReturnWarningOwner layout");

typedef struct DirtyReturnWarningRouteDef {
    uint8_t origin;            /* 0: DirtyReturnOriginValue */
    uint8_t required_ack;      /* 1: DirtyWarningAckValue */
    uint8_t first_accept_kind; /* 2: token except rollback local selector */
    uint8_t reserved;          /* 3: zero */
    uint16_t source_owner_id;  /* 4 */
    uint16_t source_state;     /* 6 */
    uint16_t warning_owner_id; /* 8 */
    uint16_t stay_owner_id;    /* 10: equality mirror of retained origin */
} DirtyReturnWarningRouteDef;
_Static_assert(sizeof(DirtyReturnWarningRouteDef) == 12, "DirtyReturnWarningRouteDef layout");

static const PauseMenuRouteDef PAUSE_MENU_ROUTES[5] = {
    { PAUSE_ENTRY_RESUME, 0, 0,
      PROCESS_UI_ACCEPT_LOCAL_ACTION, 0, PROCESS_UI_ACTION_PAUSE_RESUME, 0, 0 },
    { PAUSE_ENTRY_PARTY, 1,
      PAUSE_REQUIRE_PARTY_PRESENT + PAUSE_CAPTURE_CHILD_ORIGIN +
      PAUSE_REQUIRE_NO_BATTLE_RUNTIME,
      PROCESS_UI_ACCEPT_LOCAL_ACTION, 0, PROCESS_UI_ACTION_OPEN_PARTY,
      PROCESS_UI_OWNER_FIELD_RELAY, PROCESS_UI_STATE_RELAY_PARTY },
    { PAUSE_ENTRY_FIELD_RELAY, 2,
      PAUSE_REQUIRE_RELAY_UNLOCKED + PAUSE_REQUIRE_ALL_RELAY_BITS +
      PAUSE_CAPTURE_CHILD_ORIGIN + PAUSE_REQUIRE_NO_BATTLE_RUNTIME,
      PROCESS_UI_ACCEPT_LOCAL_ACTION, 0, PROCESS_UI_ACTION_OPEN_FIELD_RELAY,
      PROCESS_UI_OWNER_FIELD_RELAY, PROCESS_UI_STATE_RELAY_PARTY },
    { PAUSE_ENTRY_SETTINGS, 3,
      PAUSE_REQUIRE_SETTINGS_LOCATION + PAUSE_CAPTURE_CHILD_ORIGIN,
      PROCESS_UI_ACCEPT_LOCAL_ACTION, 0, PROCESS_UI_ACTION_OPEN_OPTIONS,
      PROCESS_UI_OWNER_OPTIONS_FOOTER, PROCESS_UI_STATE_DEFAULT },
    { PAUSE_ENTRY_RETURN_TO_TITLE, 4, 0,
      PROCESS_UI_ACCEPT_PROCESS_TOKEN, 0, PROCESS_ACCEPT_RETURN_TO_TITLE, 0, 0 }
};

static const RelayPageDef RELAY_PAGES[5] = {
    { RELAY_PAGE_PARTY, 0, 0xFF,
      RELAY_PAGE_ALLOW_PRE_RELAY_PARTY + RELAY_PAGE_INFORMATION_ONLY,
      UI_SCREEN_RELAY_PARTY, PROCESS_UI_VIEW_RELAY_PARTY,
      PROCESS_UI_STATE_RELAY_PARTY, 0 },
    { RELAY_PAGE_MESSAGES, 1, RELAY_MESSAGES_BIT,
      RELAY_PAGE_REQUIRE_RELAY_UNLOCKED + RELAY_PAGE_REQUIRE_PERSISTED_BIT +
      RELAY_PAGE_INFORMATION_ONLY,
      UI_SCREEN_RELAY_MESSAGES, PROCESS_UI_VIEW_RELAY_MESSAGES,
      PROCESS_UI_STATE_RELAY_MESSAGES, 0 },
    { RELAY_PAGE_RESONANCE, 2, RELAY_RESONANCE_BIT,
      RELAY_PAGE_REQUIRE_RELAY_UNLOCKED + RELAY_PAGE_REQUIRE_PERSISTED_BIT +
      RELAY_PAGE_INFORMATION_ONLY,
      UI_SCREEN_RELAY_RESONANCE, PROCESS_UI_VIEW_RELAY_RESONANCE,
      PROCESS_UI_STATE_RELAY_RESONANCE, 0 },
    { RELAY_PAGE_MAP, 3, RELAY_MAP_BIT,
      RELAY_PAGE_REQUIRE_RELAY_UNLOCKED + RELAY_PAGE_REQUIRE_PERSISTED_BIT + RELAY_PAGE_INFORMATION_ONLY,
      UI_SCREEN_RELAY_MAP, PROCESS_UI_VIEW_RELAY_MAP,
      PROCESS_UI_STATE_RELAY_MAP, 0 },
    { RELAY_PAGE_SAVE, 4, 0xFF,
      RELAY_PAGE_REQUIRE_RELAY_UNLOCKED + RELAY_PAGE_REQUIRE_ALL_PERSISTED_BITS + RELAY_PAGE_PLAYER_SAVE_SURFACE,
      UI_SCREEN_RELAY_SAVE, PROCESS_UI_VIEW_RELAY_SAVE,
      PROCESS_UI_STATE_RELAY_SAVE, 0 }
};

static const RelayRuntimeViewDef RELAY_RUNTIME_VIEWS[5] = {
    { PROCESS_UI_VIEW_RELAY_PARTY, RELAY_PAGE_PARTY, 7,
      RELAY_VIEW_SOURCE_VALIDATED_PARTY_SLOTS + RELAY_VIEW_SOURCE_CREATURE_AND_MOVE_DEFS +
      RELAY_VIEW_SOURCE_SYNC_AND_TEAM_LINK,
      RELAY_VIEW_FIXED_FIELD_ORDER + RELAY_VIEW_EXPLICIT_EMPTY_STATE +
      RELAY_VIEW_NO_STORY_MUTATION + RELAY_VIEW_GENERATION_BOUND, 0, 0 },
    { PROCESS_UI_VIEW_RELAY_MESSAGES, RELAY_PAGE_MESSAGES, 5,
      RELAY_VIEW_SOURCE_MESSAGE_ROWS + RELAY_VIEW_SOURCE_STORY_FLAGS,
      RELAY_VIEW_FIXED_FIELD_ORDER + RELAY_VIEW_EXPLICIT_EMPTY_STATE +
      RELAY_VIEW_EXPLICIT_LOCKED_STATE + RELAY_VIEW_NO_STORY_MUTATION +
      RELAY_VIEW_GENERATION_BOUND, 0, 0 },
    { PROCESS_UI_VIEW_RELAY_RESONANCE, RELAY_PAGE_RESONANCE, 5,
      RELAY_VIEW_SOURCE_SYNC_AND_TEAM_LINK + RELAY_VIEW_SOURCE_STORY_FLAGS,
      RELAY_VIEW_FIXED_FIELD_ORDER + RELAY_VIEW_EXPLICIT_EMPTY_STATE +
      RELAY_VIEW_EXPLICIT_LOCKED_STATE + RELAY_VIEW_NO_STORY_MUTATION +
      RELAY_VIEW_GENERATION_BOUND, 0, 0 },
    { PROCESS_UI_VIEW_RELAY_MAP, RELAY_PAGE_MAP, 4,
      RELAY_VIEW_SOURCE_DESTINATION_BITS + RELAY_VIEW_SOURCE_STORY_FLAGS +
      RELAY_VIEW_SOURCE_SAVE_LOCATION_REGISTRY,
      RELAY_VIEW_FIXED_FIELD_ORDER + RELAY_VIEW_EXPLICIT_LOCKED_STATE +
      RELAY_VIEW_NO_STORY_MUTATION + RELAY_VIEW_GENERATION_BOUND, 0, 0 },
    { PROCESS_UI_VIEW_RELAY_SAVE, RELAY_PAGE_SAVE, 6,
      RELAY_VIEW_SOURCE_SAVE_LOCATION_REGISTRY + RELAY_VIEW_SOURCE_SAVE_SERVICE_OWNER +
      RELAY_VIEW_SOURCE_STORY_FLAGS,
      RELAY_VIEW_FIXED_FIELD_ORDER + RELAY_VIEW_EXPLICIT_LOCKED_STATE +
      RELAY_VIEW_NO_STORY_MUTATION + RELAY_VIEW_GENERATION_BOUND, 0, 0 }
};

static const RelayRuntimeFieldDef RELAY_RUNTIME_FIELDS[27] = {
    { PROCESS_UI_VIEW_RELAY_PARTY, 0, RELAY_FORMAT_REGISTERED_TEXT, 0,
      STR_RELAY_NO_PARTY, RELAY_FIELD_PLAYER_NAME,
      RELAY_FIELD_ALLOW_ZERO_LABEL + RELAY_FIELD_USE_EMPTY_STRING + RELAY_FIELD_GENERATION_BOUND },
    { PROCESS_UI_VIEW_RELAY_PARTY, 1, RELAY_FORMAT_PARTY_PAIR, 0, 0,
      RELAY_FIELD_ACTIVE_MARKERS, RELAY_FIELD_ALLOW_ZERO_LABEL + RELAY_FIELD_GENERATION_BOUND },
    { PROCESS_UI_VIEW_RELAY_PARTY, 2, RELAY_FORMAT_PARTY_PAIR, 0, 0,
      RELAY_FIELD_PARTY_ID_LEVEL, RELAY_FIELD_ALLOW_ZERO_LABEL + RELAY_FIELD_GENERATION_BOUND },
    { PROCESS_UI_VIEW_RELAY_PARTY, 3, RELAY_FORMAT_HP_PAIR, STR_RELAY_HP, 0,
      RELAY_FIELD_PARTY_HP, RELAY_FIELD_GENERATION_BOUND },
    { PROCESS_UI_VIEW_RELAY_PARTY, 4, RELAY_FORMAT_U16_PAIR, STR_RELAY_SYNC, 0,
      RELAY_FIELD_PARTY_SYNC, RELAY_FIELD_GENERATION_BOUND },
    { PROCESS_UI_VIEW_RELAY_PARTY, 5, RELAY_FORMAT_MOVE_LIST_PAIR, STR_RELAY_MOVES, 0,
      RELAY_FIELD_PARTY_MOVES, RELAY_FIELD_GENERATION_BOUND },
    { PROCESS_UI_VIEW_RELAY_PARTY, 6, RELAY_FORMAT_U16, STR_RELAY_TEAM_LINK, 0,
      RELAY_FIELD_TEAM_LINK, RELAY_FIELD_GENERATION_BOUND },

    { PROCESS_UI_VIEW_RELAY_MESSAGES, 0, RELAY_FORMAT_MESSAGE_GRAPH_COPY, 0, 0,
      RELAY_FIELD_MESSAGE_SENDER_TITLE,
      RELAY_FIELD_ALLOW_ZERO_LABEL + RELAY_FIELD_GRAPH_COPY_NO_ACQUIRE + RELAY_FIELD_GENERATION_BOUND },
    { PROCESS_UI_VIEW_RELAY_MESSAGES, 1, RELAY_FORMAT_MESSAGE_STATE_LABEL,
      STR_RELAY_STATUS, 0, RELAY_FIELD_MESSAGE_STATE, RELAY_FIELD_GENERATION_BOUND },
    { PROCESS_UI_VIEW_RELAY_MESSAGES, 2, RELAY_FORMAT_INDEX_OF_COUNT, 0, 0,
      RELAY_FIELD_MESSAGE_LIST_POSITION, RELAY_FIELD_ALLOW_ZERO_LABEL + RELAY_FIELD_GENERATION_BOUND },
    { PROCESS_UI_VIEW_RELAY_MESSAGES, 3, RELAY_FORMAT_MESSAGE_GRAPH_COPY, 0, 0,
      RELAY_FIELD_MESSAGE_DETAIL,
      RELAY_FIELD_ALLOW_ZERO_LABEL + RELAY_FIELD_GRAPH_COPY_NO_ACQUIRE + RELAY_FIELD_GENERATION_BOUND },
    { PROCESS_UI_VIEW_RELAY_MESSAGES, 4, RELAY_FORMAT_INDEX_OF_COUNT, 0, 0,
      RELAY_FIELD_MESSAGE_DETAIL_PAGE_POSITION,
      RELAY_FIELD_ALLOW_ZERO_LABEL + RELAY_FIELD_GENERATION_BOUND },

    { PROCESS_UI_VIEW_RELAY_RESONANCE, 0, RELAY_FORMAT_U16, STR_RELAY_TEAM_LINK, 0,
      RELAY_FIELD_RESONANCE_TEAM_LINK, RELAY_FIELD_GENERATION_BOUND },
    { PROCESS_UI_VIEW_RELAY_RESONANCE, 1, RELAY_FORMAT_U16, STR_RELAY_LEFT, 0,
      RELAY_FIELD_RESONANCE_LEFT_SYNC, RELAY_FIELD_GENERATION_BOUND },
    { PROCESS_UI_VIEW_RELAY_RESONANCE, 2, RELAY_FORMAT_U16, STR_RELAY_RIGHT, 0,
      RELAY_FIELD_RESONANCE_RIGHT_SYNC, RELAY_FIELD_GENERATION_BOUND },
    { PROCESS_UI_VIEW_RELAY_RESONANCE, 3, RELAY_FORMAT_LOCK_LABEL, STR_RELAY_RECORD, 0,
      RELAY_FIELD_RUSK_RECORD, RELAY_FIELD_GENERATION_BOUND },
    { PROCESS_UI_VIEW_RELAY_RESONANCE, 4, RELAY_FORMAT_REGISTERED_TEXT,
      STR_RELAY_RESONANCE_EXPLANATION, 0, RELAY_FIELD_RESONANCE_EXPLANATION,
      RELAY_FIELD_STATIC_LABEL_IS_VALUE + RELAY_FIELD_GENERATION_BOUND },

    { PROCESS_UI_VIEW_RELAY_MAP, 0, RELAY_FORMAT_DESTINATION_GRAPH_COPY, 0, 0,
      RELAY_FIELD_MAP_ANNEX,
      RELAY_FIELD_ALLOW_ZERO_LABEL + RELAY_FIELD_GRAPH_COPY_NO_ACQUIRE + RELAY_FIELD_GENERATION_BOUND },
    { PROCESS_UI_VIEW_RELAY_MAP, 1, RELAY_FORMAT_DESTINATION_GRAPH_COPY, 0, 0,
      RELAY_FIELD_MAP_ESTATE,
      RELAY_FIELD_ALLOW_ZERO_LABEL + RELAY_FIELD_GRAPH_COPY_NO_ACQUIRE + RELAY_FIELD_GENERATION_BOUND },
    { PROCESS_UI_VIEW_RELAY_MAP, 2, RELAY_FORMAT_LOCATION_REGISTRY_NAME,
      STR_RELAY_CURRENT_LOCATION, 0, RELAY_FIELD_MAP_CURRENT_LOCATION, RELAY_FIELD_GENERATION_BOUND },
    { PROCESS_UI_VIEW_RELAY_MAP, 3, RELAY_FORMAT_REGISTERED_TEXT,
      STR_RELAY_TRAVEL_SKIMMER, 0, RELAY_FIELD_MAP_SKIMMER_FOOTER,
      RELAY_FIELD_STATIC_LABEL_IS_VALUE + RELAY_FIELD_GENERATION_BOUND },

    { PROCESS_UI_VIEW_RELAY_SAVE, 0, RELAY_FORMAT_LOCATION_REGISTRY_NAME,
      STR_RELAY_CURRENT_LOCATION, STR_MANUAL_SAVE_BLOCKED,
      RELAY_FIELD_SAVE_CURRENT_LOCATION, RELAY_FIELD_USE_EMPTY_STRING + RELAY_FIELD_GENERATION_BOUND },
    { PROCESS_UI_VIEW_RELAY_SAVE, 1, RELAY_FORMAT_CHECKPOINT_NAME,
      STR_RELAY_CHECKPOINT, 0, RELAY_FIELD_SAVE_CHECKPOINT, RELAY_FIELD_GENERATION_BOUND },
    { PROCESS_UI_VIEW_RELAY_SAVE, 2, RELAY_FORMAT_SAVE_REASON_NAME,
      STR_RELAY_LAST_RECORD, 0, RELAY_FIELD_SAVE_REASON, RELAY_FIELD_GENERATION_BOUND },
    { PROCESS_UI_VIEW_RELAY_SAVE, 3, RELAY_FORMAT_DIRTY_LABEL,
      STR_RELAY_STATUS, 0, RELAY_FIELD_SAVE_DIRTY_STATE, RELAY_FIELD_GENERATION_BOUND },
    { PROCESS_UI_VIEW_RELAY_SAVE, 4, RELAY_FORMAT_SAVE_SERVICE_STATE,
      STR_RELAY_STATUS, 0, RELAY_FIELD_SAVE_SERVICE_STATUS, RELAY_FIELD_GENERATION_BOUND },
    { PROCESS_UI_VIEW_RELAY_SAVE, 5, RELAY_FORMAT_MANUAL_ELIGIBILITY,
      STR_MANUAL_RECORD_PROGRESS, STR_MANUAL_SAVE_BLOCKED,
      RELAY_FIELD_SAVE_MANUAL_ELIGIBILITY,
      RELAY_FIELD_USE_EMPTY_STRING + RELAY_FIELD_GENERATION_BOUND }
};

static const RelayMessageDef RELAY_MESSAGES[2] = {
    { RELAY_MESSAGE_TAVI_CALIBRATION, 0, JO_RELAY_005, TAVI_MSG_001, 0, 3,
      RELAY_MESSAGE_STATE_READ_AFTER_RELAY_ACQUISITION, 0, 0 },
    { RELAY_MESSAGE_IVO_OBSERVATORY_PACKET, 1, REUNION_008, REUNION_008,
      HOOK_001, 1, RELAY_MESSAGE_STATE_PENDING_UNTIL_SOLACE_RESOLVED, 0, 0 }
};

static const RelayDisplayStringDef RELAY_DISPLAY_STRINGS[68] = {
    { RELAY_DISPLAY_SAVEABLE_LOCATION, 0, SAVELOC_SIM_INTRO, STR_LOC_SIMULATION_ARENA, 0 },
    { RELAY_DISPLAY_SAVEABLE_LOCATION, 0, SAVELOC_ANNEX_SIM_POST_TUTORIAL, STR_LOC_ANNEX_SIMULATION_ROOM, 0 },
    { RELAY_DISPLAY_SAVEABLE_LOCATION, 0, SAVELOC_ANNEX_SIM_FROM_ATRIUM, STR_LOC_ANNEX_SIMULATION_ROOM, 0 },
    { RELAY_DISPLAY_SAVEABLE_LOCATION, 0, SAVELOC_ANNEX_ATRIUM_FROM_SIM, STR_LOC_ANNEX_ATRIUM, 0 },
    { RELAY_DISPLAY_SAVEABLE_LOCATION, 0, SAVELOC_ANNEX_ATRIUM_FROM_DIRECTOR, STR_LOC_ANNEX_ATRIUM, 0 },
    { RELAY_DISPLAY_SAVEABLE_LOCATION, 0, SAVELOC_ANNEX_ATRIUM_FROM_PLAYER_ROOM, STR_LOC_ANNEX_ATRIUM, 0 },
    { RELAY_DISPLAY_SAVEABLE_LOCATION, 0, SAVELOC_ANNEX_ATRIUM_FROM_CLINIC, STR_LOC_ANNEX_ATRIUM, 0 },
    { RELAY_DISPLAY_SAVEABLE_LOCATION, 0, SAVELOC_ANNEX_ATRIUM_FROM_WORKSHOP, STR_LOC_ANNEX_ATRIUM, 0 },
    { RELAY_DISPLAY_SAVEABLE_LOCATION, 0, SAVELOC_ANNEX_ATRIUM_FROM_THRESHOLD, STR_LOC_ANNEX_ATRIUM, 0 },
    { RELAY_DISPLAY_SAVEABLE_LOCATION, 0, SAVELOC_ANNEX_ATRIUM_ELEVATOR_LOWER, STR_LOC_ANNEX_ATRIUM, 0 },
    { RELAY_DISPLAY_SAVEABLE_LOCATION, 0, SAVELOC_ANNEX_ATRIUM_ELEVATOR_UPPER, STR_LOC_ANNEX_ATRIUM, 0 },
    { RELAY_DISPLAY_SAVEABLE_LOCATION, 0, SAVELOC_ANNEX_ATRIUM_TRACE_COMPLETE, STR_LOC_ANNEX_ATRIUM, 0 },
    { RELAY_DISPLAY_SAVEABLE_LOCATION, 0, SAVELOC_ANNEX_ATRIUM_RETURN, STR_LOC_ANNEX_ATRIUM, 0 },
    { RELAY_DISPLAY_SAVEABLE_LOCATION, 0, SAVELOC_ANNEX_ATRIUM_POST_CHAPTER, STR_LOC_ANNEX_ATRIUM, 0 },
    { RELAY_DISPLAY_SAVEABLE_LOCATION, 0, SAVELOC_ANNEX_DIRECTOR_FROM_ATRIUM, STR_LOC_ANNEX_DIRECTOR_LAB, 0 },
    { RELAY_DISPLAY_SAVEABLE_LOCATION, 0, SAVELOC_ANNEX_PLAYER_ROOM_FROM_ATRIUM, STR_LOC_ANNEX_PLAYER_ROOM, 0 },
    { RELAY_DISPLAY_SAVEABLE_LOCATION, 0, SAVELOC_ANNEX_CLINIC_FROM_ATRIUM, STR_LOC_ANNEX_CLINIC, 0 },
    { RELAY_DISPLAY_SAVEABLE_LOCATION, 0, SAVELOC_ANNEX_WORKSHOP_RELAY, STR_LOC_ANNEX_WORKSHOP, 0 },
    { RELAY_DISPLAY_SAVEABLE_LOCATION, 0, SAVELOC_ANNEX_WORKSHOP_FROM_ATRIUM, STR_LOC_ANNEX_WORKSHOP, 0 },
    { RELAY_DISPLAY_SAVEABLE_LOCATION, 0, SAVELOC_ANNEX_THRESHOLD_DEPARTURE, STR_LOC_ANNEX_THRESHOLD, 0 },
    { RELAY_DISPLAY_SAVEABLE_LOCATION, 0, SAVELOC_ANNEX_THRESHOLD_FROM_ATRIUM, STR_LOC_ANNEX_THRESHOLD, 0 },
    { RELAY_DISPLAY_SAVEABLE_LOCATION, 0, SAVELOC_ESTATE_COURTYARD_ARRIVAL, STR_LOC_ESTATE_COURTYARD, 0 },
    { RELAY_DISPLAY_SAVEABLE_LOCATION, 0, SAVELOC_ESTATE_COURTYARD_POST_RUSK, STR_LOC_ESTATE_COURTYARD, 0 },
    { RELAY_DISPLAY_SAVEABLE_LOCATION, 0, SAVELOC_ESTATE_COURTYARD_FROM_MAP, STR_LOC_ESTATE_COURTYARD, 0 },
    { RELAY_DISPLAY_SAVEABLE_LOCATION, 0, SAVELOC_ESTATE_COURTYARD_FROM_FOYER, STR_LOC_ESTATE_COURTYARD, 0 },
    { RELAY_DISPLAY_SAVEABLE_LOCATION, 0, SAVELOC_ESTATE_FOYER_FROM_COURTYARD, STR_LOC_ESTATE_FOYER, 0 },
    { RELAY_DISPLAY_SAVEABLE_LOCATION, 0, SAVELOC_ESTATE_FOYER_FROM_HALL, STR_LOC_ESTATE_FOYER, 0 },
    { RELAY_DISPLAY_SAVEABLE_LOCATION, 0, SAVELOC_ESTATE_HALL_FROM_FOYER, STR_LOC_ESTATE_INVENTION_HALL, 0 },
    { RELAY_DISPLAY_SAVEABLE_LOCATION, 0, SAVELOC_ESTATE_HALL_FROM_STUDY, STR_LOC_ESTATE_INVENTION_HALL, 0 },
    { RELAY_DISPLAY_SAVEABLE_LOCATION, 0, SAVELOC_ESTATE_STUDY_FROM_HALL, STR_LOC_ESTATE_OBSERVATORY_STUDY, 0 },
    { RELAY_DISPLAY_SAVEABLE_LOCATION, 0, SAVELOC_ESTATE_STUDY_TAVI_FOUND, STR_LOC_ESTATE_OBSERVATORY_STUDY, 0 },

    { RELAY_DISPLAY_CHECKPOINT, 0, CHECKPOINT_NONE, STR_CHECKPOINT_NONE, 0 },
    { RELAY_DISPLAY_CHECKPOINT, 0, CHECKPOINT_AFTER_NAME, STR_CHECKPOINT_AFTER_NAME, 0 },
    { RELAY_DISPLAY_CHECKPOINT, 0, CHECKPOINT_AFTER_TUTORIAL, STR_CHECKPOINT_AFTER_TUTORIAL, 0 },
    { RELAY_DISPLAY_CHECKPOINT, 0, CHECKPOINT_FIELD_RELAY, STR_CHECKPOINT_FIELD_RELAY, 0 },
    { RELAY_DISPLAY_CHECKPOINT, 0, CHECKPOINT_ANNEX_DEPARTURE, STR_CHECKPOINT_ANNEX_DEPARTURE, 0 },
    { RELAY_DISPLAY_CHECKPOINT, 0, CHECKPOINT_ESTATE_ARRIVAL, STR_CHECKPOINT_ESTATE_ARRIVAL, 0 },
    { RELAY_DISPLAY_CHECKPOINT, 0, CHECKPOINT_RUSK_VICTORY, STR_CHECKPOINT_RUSK_VICTORY, 0 },
    { RELAY_DISPLAY_CHECKPOINT, 0, CHECKPOINT_TAVI_FOUND, STR_CHECKPOINT_TAVI_FOUND, 0 },
    { RELAY_DISPLAY_CHECKPOINT, 0, CHECKPOINT_TAVI_RETURNED, STR_CHECKPOINT_TAVI_RETURNED, 0 },
    { RELAY_DISPLAY_CHECKPOINT, 0, CHECKPOINT_SLICE_COMPLETE, STR_CHECKPOINT_SLICE_COMPLETE, 0 },
    { RELAY_DISPLAY_CHECKPOINT, 0, CHECKPOINT_RUSK_RETURN_TO_ANNEX, STR_CHECKPOINT_RUSK_RETURN, 0 },
    { RELAY_DISPLAY_CHECKPOINT, 0, CHECKPOINT_ANNEX_TRACE_COMPLETE, STR_CHECKPOINT_ANNEX_TRACE, 0 },

    { RELAY_DISPLAY_SAVE_REASON, 0, SAVE_REASON_NONE, STR_SAVE_REASON_NONE, 0 },
    { RELAY_DISPLAY_SAVE_REASON, 0, SAVE_REASON_CHECKPOINT, STR_SAVE_REASON_CHECKPOINT, 0 },
    { RELAY_DISPLAY_SAVE_REASON, 0, SAVE_REASON_MANUAL_RELAY, STR_SAVE_REASON_MANUAL_RELAY, 0 },
    { RELAY_DISPLAY_SAVE_REASON, 0, SAVE_REASON_BATTLE_RESULT, STR_SAVE_REASON_BATTLE_RESULT, 0 },
    { RELAY_DISPLAY_SAVE_REASON, 0, SAVE_REASON_FINAL_HOOK, STR_SAVE_REASON_FINAL_HOOK, 0 },
    { RELAY_DISPLAY_SAVE_REASON, 0, SAVE_REASON_TRANSITION, STR_SAVE_REASON_TRANSITION, 0 },
    { RELAY_DISPLAY_SAVE_REASON, 0, SAVE_REASON_SETTINGS, STR_SAVE_REASON_SETTINGS, 0 },

    { RELAY_DISPLAY_SAVE_REQUEST_PHASE, 0, SAVE_REQUEST_EMPTY, STR_SAVE_STATE_READY, 0 },
    { RELAY_DISPLAY_SAVE_REQUEST_PHASE, 0, SAVE_REQUEST_RESERVED, STR_SAVE_STATE_QUEUED, 0 },
    { RELAY_DISPLAY_SAVE_REQUEST_PHASE, 0, SAVE_REQUEST_SNAPSHOT_READY, STR_SAVE_STATE_QUEUED, 0 },
    { RELAY_DISPLAY_SAVE_REQUEST_PHASE, 0, SAVE_REQUEST_ADDRESS_READY, STR_SAVE_STATE_QUEUED, 0 },
    { RELAY_DISPLAY_SAVE_REQUEST_PHASE, 0, SAVE_REQUEST_ENQUEUED, STR_SAVE_STATE_QUEUED, 0 },
    { RELAY_DISPLAY_SAVE_REQUEST_PHASE, 0, SAVE_REQUEST_WRITING, STR_SAVE_STATE_WRITING, 0 },
    { RELAY_DISPLAY_SAVE_REQUEST_PHASE, 0, SAVE_REQUEST_VERIFYING, STR_SAVE_STATE_VERIFYING, 0 },
    { RELAY_DISPLAY_SAVE_REQUEST_PHASE, 0, SAVE_REQUEST_COMMITTED, STR_SAVE_STATE_RECORDED, 0 },
    { RELAY_DISPLAY_SAVE_REQUEST_PHASE, 0, SAVE_REQUEST_FAILED, STR_SAVE_STATE_FAILED, 0 },
    { RELAY_DISPLAY_SAVE_REQUEST_PHASE, 0, SAVE_REQUEST_CANCELED, STR_SAVE_STATE_CANCELED, 0 },
    { RELAY_DISPLAY_SAVE_REQUEST_PHASE, 0, SAVE_REQUEST_CONTINUED_DIRTY, STR_RELAY_UNSAVED, 0 },
    { RELAY_DISPLAY_SAVE_REQUEST_PHASE, 0, SAVE_REQUEST_TRAVELED_UNSAVED, STR_SAVE_STATE_TRAVELED_UNSAVED, 0 },
    { RELAY_DISPLAY_SAVE_REQUEST_PHASE, 0, SAVE_REQUEST_ABORTED_TO_TITLE, STR_SAVE_STATE_ABORTED, 0 },

    { RELAY_DISPLAY_MANUAL_ELIGIBILITY, 0, RELAY_MANUAL_BLOCKED, STR_MANUAL_SAVE_BLOCKED, 0 },
    { RELAY_DISPLAY_MANUAL_ELIGIBILITY, 0, RELAY_MANUAL_AVAILABLE, STR_MANUAL_SAVE_AVAILABLE, 0 },
    { RELAY_DISPLAY_MANUAL_ELIGIBILITY, 0, RELAY_MANUAL_BUSY, STR_SAVE_STATE_QUEUED, 0 },
    { RELAY_DISPLAY_MANUAL_ELIGIBILITY, 0, RELAY_MANUAL_RECORDED, STR_SAVE_STATE_RECORDED, 0 },
    { RELAY_DISPLAY_MANUAL_ELIGIBILITY, 0, RELAY_MANUAL_FAILED, STR_SAVE_STATE_FAILED, 0 }
};

static const SettingsRuntimeViewDef SETTINGS_RUNTIME_VIEW[1] = {
    { PROCESS_UI_VIEW_SETTINGS_EDITOR, 0, 9,
      STR_SETTINGS_RESET_DEFAULTS, PROCESS_UI_ACTION_SETTINGS_RESET_DEFAULTS,
      0, 9, 10, 11, 0, 0 }
};

static const UserSaveUiRouteDef USER_SAVE_UI_ROUTES[2] = {
    { PROCESS_UI_OWNER_FIELD_RELAY, PROCESS_UI_STATE_RELAY_SAVE,
      PROCESS_UI_OWNER_MANUAL_SAVE_CONFIRM,
      PROCESS_UI_OWNER_MANUAL_SETTINGS_SAVE_FAILURE,
      SAVE_FAILURE_PRODUCER_SERVICE, SAVE_FAILURE_SERVICE_MANUAL_RELAY,
      SAVE_REASON_MANUAL_RELAY, USER_SAVE_BUSY_RETAIN_SCRATCH_AND_SHOW_SAVING,
      USER_SAVE_REQUIRE_INITIALIZED_CAMPAIGN + USER_SAVE_REQUIRE_STABLE_CONTROL +
      USER_SAVE_REQUIRE_MANUAL_LOCATION + USER_SAVE_REQUIRE_RELAY_AND_ALL_BITS +
      USER_SAVE_REQUIRE_MODAL_CLOSED_BEFORE_CAPTURE + USER_SAVE_RETAIN_ORIGIN_UNTIL_TERMINAL,
      0 },
    { PROCESS_UI_OWNER_OPTIONS_FOOTER, PROCESS_UI_STATE_DEFAULT, 0,
      PROCESS_UI_OWNER_MANUAL_SETTINGS_SAVE_FAILURE,
      SAVE_FAILURE_PRODUCER_SERVICE, SAVE_FAILURE_SERVICE_SETTINGS,
      SAVE_REASON_SETTINGS, USER_SAVE_BUSY_RETAIN_SCRATCH_AND_SHOW_SAVING,
      USER_SAVE_REQUIRE_INITIALIZED_CAMPAIGN + USER_SAVE_REQUIRE_STABLE_CONTROL +
      USER_SAVE_REQUIRE_MODAL_CLOSED_BEFORE_CAPTURE + USER_SAVE_RETAIN_ORIGIN_UNTIL_TERMINAL +
      USER_SAVE_REQUIRE_CONTINUE_LOCATION + USER_SAVE_ALLOW_SIM_INTRO_BOUNDARY,
      0 }
};

static const DirtyReturnWarningRouteDef DIRTY_RETURN_WARNING_ROUTES[3] = {
    { DIRTY_RETURN_ORIGIN_GAMEPLAY, DIRTY_WARNING_GAMEPLAY_RETURN_ACK,
      PROCESS_UI_ACCEPT_PROCESS_TOKEN, 0,
      PROCESS_UI_OWNER_PAUSE_MENU, PROCESS_UI_STATE_DEFAULT,
      PROCESS_UI_OWNER_END_DIRTY_RETURN_WARNING, PROCESS_UI_OWNER_PAUSE_MENU },
    { DIRTY_RETURN_ORIGIN_END_CARD, DIRTY_WARNING_END_CARD_RETURN_ACK,
      PROCESS_UI_ACCEPT_PROCESS_TOKEN, 0,
      PROCESS_UI_OWNER_END_CARD_MENU, PROCESS_UI_STATE_DEFAULT,
      PROCESS_UI_OWNER_END_DIRTY_RETURN_WARNING, PROCESS_UI_OWNER_END_CARD_MENU },
    { DIRTY_RETURN_ORIGIN_ROLLBACK_FATAL,
      DIRTY_WARNING_ROLLBACK_FATAL_RETURN_ACK,
      PROCESS_UI_ACCEPT_LOCAL_ACTION, 0,
      PROCESS_UI_OWNER_ROLLBACK_FATAL, PROCESS_UI_STATE_ROLLBACK_FATAL,
      PROCESS_UI_OWNER_ROLLBACK_DIRTY_RETURN_WARNING,
      PROCESS_UI_OWNER_ROLLBACK_FATAL }
};

enum ProcessUiItemFlags {
    PROCESS_UI_ITEM_RENDER_CONTENT = 1u << 0,
    PROCESS_UI_ITEM_FOCUSABLE = 1u << 1,
    PROCESS_UI_ITEM_CHOICE_ROOT = 1u << 2,
    PROCESS_UI_ITEM_SAFE_CANCEL = 1u << 3,
    PROCESS_UI_ITEM_STATE_GATED = 1u << 4,
    PROCESS_UI_ITEM_CO_RENDER_LAYER = 1u << 5,
    PROCESS_UI_ITEM_CAPABILITY_SELECTED = 1u << 6,
    PROCESS_UI_ITEM_ACQUIRE_DIALOGUE_NODE = 1u << 7
};

enum ProcessUiBindingFlags {
    PROCESS_UI_BIND_GENERATION_BOUND = 1u << 0,
    PROCESS_UI_BIND_CLEAR_INPUT_EDGES = 1u << 1,
    PROCESS_UI_BIND_ONE_ACCEPT_PER_FRAME = 1u << 2,
    PROCESS_UI_BIND_FIXED_ITEM_ORDER = 1u << 3,
    PROCESS_UI_BIND_COMPOSITE_BASE_SCREEN = 1u << 4,
    PROCESS_UI_BIND_NO_DIALOGUE_SEQUENCING = 1u << 5,
    PROCESS_UI_BIND_PRESERVE_OWNER_ON_CANCEL = 1u << 6,
    PROCESS_UI_BIND_DISABLE_UNAVAILABLE_ITEM = 1u << 7
};

typedef struct ProcessUiItemDef {
    uint16_t content_id;       /* 0: DialogueId, StringId, or ProcessUiRuntimeViewIdValue by source_kind */
    uint8_t source_kind;       /* 2 */
    uint8_t layer;             /* 3: zero is base UIScreenDef */
    uint8_t render_order;      /* 4: unique inside binding */
    uint8_t focus_order;       /* 5: 0xFF means nonfocusable */
    uint8_t accept_kind;       /* 6 */
    uint8_t flags;             /* 7 */
    uint16_t accept_value;     /* 8: ProcessAcceptToken or ProcessUiLocalAction */
    uint16_t reserved;         /* 10 */
} ProcessUiItemDef;
_Static_assert(sizeof(ProcessUiItemDef) == 12, "ProcessUiItemDef layout");

typedef struct ProcessUiBindingDef {
    SceneId scene_id;          /* 0; zero only for registered global owner */
    uint16_t owner_id;         /* 2: ProcessUiOwnerIdValue */
    uint16_t state_variant;    /* 4 */
    UIScreenId screen_id;      /* 6: zero means retained scene/no base screen */
    uint16_t first_item;       /* 8 */
    uint8_t item_count;        /* 10 */
    uint8_t layout;            /* 11 */
    uint8_t default_focus;     /* 12: 0xFF when no focus */
    uint8_t flags;             /* 13 */
    uint16_t reserved;         /* 14 */
} ProcessUiBindingDef;
_Static_assert(sizeof(ProcessUiBindingDef) == 16, "ProcessUiBindingDef layout");

typedef enum ProcessUiTimedCompletionValue {
    PROCESS_UI_TIMED_RELEASE_RETAINED_OWNER = 1,
    PROCESS_UI_TIMED_OPEN_OWNER = 2
} ProcessUiTimedCompletionValue;

enum ProcessUiTimedSequenceFlags {
    PROCESS_UI_TIMED_USE_DIALOGUE_TICKS = 1u << 0,
    PROCESS_UI_TIMED_FREEZE_ON_CONTROLLER_LOSS = 1u << 1,
    PROCESS_UI_TIMED_IGNORE_CONFIRM_SKIP = 1u << 2,
    PROCESS_UI_TIMED_EMIT_GENERATION_TOKEN = 1u << 3,
    PROCESS_UI_TIMED_REQUIRE_RETAINED_OWNER = 1u << 4
};

typedef struct ProcessUiTimedSequenceDef {
    uint16_t owner_id;           /* 0: source ProcessUiOwnerIdValue */
    uint16_t state_variant;      /* 2: exact binding state */
    uint16_t target_owner_id;    /* 4: nonzero only for OPEN_OWNER */
    uint8_t expected_item_count; /* 6: exact binding count */
    uint8_t completion;          /* 7: ProcessUiTimedCompletionValue */
    uint8_t required_outcome;    /* 8: zero or FinalSaveOutcomeValue */
    uint8_t flags;               /* 9: ProcessUiTimedSequenceFlags */
    uint16_t reserved;           /* 10: zero */
} ProcessUiTimedSequenceDef;
_Static_assert(sizeof(ProcessUiTimedSequenceDef) == 12, "ProcessUiTimedSequenceDef layout");
```

The two timed-sequence rows are literal:

| owner / state | items | completion / target | required outcome | flags |
|---|---:|---|---|---|
| `PROCESS_UI_OWNER_SAVE_SERVICE / PROCESS_UI_STATE_SAVE_DONE` | `1` | `PROCESS_UI_TIMED_RELEASE_RETAINED_OWNER / 0` | `0` | `USE_DIALOGUE_TICKS + FREEZE_ON_CONTROLLER_LOSS + IGNORE_CONFIRM_SKIP + EMIT_GENERATION_TOKEN + REQUIRE_RETAINED_OWNER` |
| `PROCESS_UI_OWNER_END_CHAPTER_MARK / PROCESS_UI_STATE_DEFAULT` | `2` | `PROCESS_UI_TIMED_OPEN_OWNER / PROCESS_UI_OWNER_END_CARD_MENU` | `0` | `USE_DIALOGUE_TICKS + FREEZE_ON_CONTROLLER_LOSS + IGNORE_CONFIRM_SKIP + EMIT_GENERATION_TOKEN` |

For `PROCESS_UI_LAYOUT_TIMED_SEQUENCE`, the process renderer never follows a
DialogueNode `next_id` or `alternate_next_id`. It reveals items in binding order
and counts only fully visible 30 Hz presentation ticks from each referenced
node's nonzero `auto_advance_ticks`; controller loss and any higher modal freeze
the counter, and A/Start cannot shorten it. At an intermediate timeout it
advances one item, clears input edges, and discards a poll frame. At the final
timeout it emits one token carrying source owner/state generation, binding
generation, terminal item, and—when SaveService-owned—request/campaign
generations. A stale or duplicate token is ignored. Save Done then releases its
exact retained producer owner; ordinary saves resume that owner, while the
final-hook resolver additionally requires the matching final-request token
before transitioning. The authored-mark row atomically replaces owner 17 with
the exact owner-19 End Card binding; no controller switch or graph edge is
inferred.

The process-only static-string catalog is exact UTF-8 source data. Its 103 rows occupy
the reserved `0x9F01..0x9F67` range and may not collide with any Dialogue Graph
StringId:

| StringId | Exact copy |
|---|---|
| `STR_SAVE_FAILURE_FINAL_REPLAY_WARNING` | `Continuing without saving may replay the closing sequence after a reboot.` |
| `STR_SAVE_FAILURE_PRE_TRANSITION` | `Travel can continue unsaved, but a reboot may restore the previous location and replay recent progress.` |
| `STR_SAVE_FAILURE_COMMITTED_PROGRESS` | `Progress remains playable in memory, but a reboot may restore an older checkpoint.` |
| `STR_SAVE_FAILURE_RETENTION_ONCE` | `Continuing unsaved may replay this one-time scene after a reboot.` |
| `STR_SAVE_FAILURE_MANUAL_SETTINGS` | `The record could not be written. Retry or cancel.` |
| `STR_PROCESS_RECOVERY_FATAL` | `Travel and source recovery both failed. Retry recovery or return safely to the title screen.` |
| `STR_PROCESS_RECOVERY_RETRY` | `RETRY RECOVERY` |
| `STR_PROCESS_RECOVERY_RETURN_TITLE` | `RETURN TO TITLE` |
| `STR_SAVE_FAILURE_NEW_GAME_INITIALIZATION` | `The new campaign record could not be initialized. Retry or return to the title screen.` |
| `STR_SETTINGS_TEXT_SPEED` | `TEXT SPEED` |
| `STR_SETTINGS_CAMERA` | `CAMERA` |
| `STR_SETTINGS_INVERT_X` | `INVERT X` |
| `STR_SETTINGS_INVERT_Y` | `INVERT Y` |
| `STR_SETTINGS_MUSIC_VOLUME` | `MUSIC VOLUME` |
| `STR_SETTINGS_SFX_VOLUME` | `SFX VOLUME` |
| `STR_SETTINGS_RUMBLE` | `RUMBLE` |
| `STR_SETTINGS_OVERSCAN_X` | `OVERSCAN X` |
| `STR_SETTINGS_OVERSCAN_Y` | `OVERSCAN Y` |
| `STR_SETTINGS_UI_CONTRAST` | `UI CONTRAST` |
| `STR_SETTINGS_RESET_DEFAULTS` | `RESET DEFAULTS` |
| `STR_PAUSE_RESUME` | `RESUME` |
| `STR_PAUSE_PARTY` | `PARTY` |
| `STR_PAUSE_FIELD_RELAY` | `FIELD RELAY` |
| `STR_PAUSE_SETTINGS` | `SETTINGS` |
| `STR_RELAY_MESSAGES` | `MESSAGES` |
| `STR_RELAY_RESONANCE` | `RESONANCE` |
| `STR_RELAY_MAP` | `MAP` |
| `STR_RELAY_SAVE` | `SAVE` |
| `STR_UI_BACK` | `BACK` |
| `STR_MANUAL_RECORD_PROGRESS` | `RECORD PROGRESS` |
| `STR_MANUAL_SAVE_CONFIRM` | `Record progress at this stable location?` |
| `STR_MANUAL_SAVE_ACCEPT` | `RECORD` |
| `STR_MANUAL_SAVE_BLOCKED` | `Finish the current transition first.` |
| `STR_VALUE_SLOW` | `SLOW` |
| `STR_VALUE_NORMAL` | `NORMAL` |
| `STR_VALUE_FAST` | `FAST` |
| `STR_VALUE_OFF` | `OFF` |
| `STR_VALUE_ON` | `ON` |
| `STR_VALUE_STANDARD` | `STANDARD` |
| `STR_VALUE_HIGH` | `HIGH` |
| `STR_VALUE_REDUCED_FLASH` | `REDUCED FLASH` |
| `STR_RELAY_NO_PARTY` | `NO PARTY ASSIGNED` |
| `STR_RELAY_READ` | `READ` |
| `STR_RELAY_PENDING` | `PENDING` |
| `STR_RELAY_RESOLVED` | `RESOLVED` |
| `STR_RELAY_TRAVEL_SKIMMER` | `TRAVEL FROM AN EXTERIOR SKIMMER` |
| `STR_RELAY_TEAM_LINK` | `TEAM LINK` |
| `STR_RELAY_SYNC` | `SYNC` |
| `STR_RELAY_CURRENT_LOCATION` | `CURRENT LOCATION` |
| `STR_RELAY_CHECKPOINT` | `CHECKPOINT` |
| `STR_RELAY_LAST_RECORD` | `LAST RECORD` |
| `STR_RELAY_STATUS` | `STATUS` |
| `STR_RELAY_RECORD` | `RESONANCE RECORD` |
| `STR_RELAY_RESONANCE_EXPLANATION` | `SHARED RESONANCE BUILDS WHEN PARTNERS CHAIN COMPLEMENTARY MOVES.` |
| `STR_RELAY_LOCKED` | `LOCKED` |
| `STR_RELAY_UNLOCKED` | `UNLOCKED` |
| `STR_RELAY_HP` | `HP` |
| `STR_RELAY_MOVES` | `MOVES` |
| `STR_RELAY_LEFT` | `LEFT` |
| `STR_RELAY_RIGHT` | `RIGHT` |
| `STR_RELAY_CLEAN` | `CLEAN` |
| `STR_RELAY_UNSAVED` | `UNSAVED` |
| `STR_LOC_SIMULATION_ARENA` | `SIMULATION ARENA` |
| `STR_LOC_ANNEX_SIMULATION_ROOM` | `ANNEX SIMULATION ROOM` |
| `STR_LOC_ANNEX_ATRIUM` | `ANNEX ATRIUM` |
| `STR_LOC_ANNEX_DIRECTOR_LAB` | `DIRECTOR LAB` |
| `STR_LOC_ANNEX_PLAYER_ROOM` | `PLAYER ROOM` |
| `STR_LOC_ANNEX_CLINIC` | `ANNEX CLINIC` |
| `STR_LOC_ANNEX_WORKSHOP` | `ANNEX WORKSHOP` |
| `STR_LOC_ANNEX_THRESHOLD` | `ANNEX THRESHOLD` |
| `STR_LOC_ESTATE_COURTYARD` | `ESTATE COURTYARD` |
| `STR_LOC_ESTATE_FOYER` | `ESTATE FOYER` |
| `STR_LOC_ESTATE_INVENTION_HALL` | `INVENTION HALL` |
| `STR_LOC_ESTATE_OBSERVATORY_STUDY` | `OBSERVATORY STUDY` |
| `STR_CHECKPOINT_NONE` | `NO CHECKPOINT` |
| `STR_CHECKPOINT_AFTER_NAME` | `SIMULATION INTRO` |
| `STR_CHECKPOINT_AFTER_TUTORIAL` | `FIELD PAIR RECEIVED` |
| `STR_CHECKPOINT_FIELD_RELAY` | `FIELD RELAY ACQUIRED` |
| `STR_CHECKPOINT_ANNEX_DEPARTURE` | `ANNEX DEPARTURE` |
| `STR_CHECKPOINT_ESTATE_ARRIVAL` | `ESTATE ARRIVAL` |
| `STR_CHECKPOINT_RUSK_VICTORY` | `RUSK VICTORY` |
| `STR_CHECKPOINT_TAVI_FOUND` | `TAVI FOUND` |
| `STR_CHECKPOINT_TAVI_RETURNED` | `TAVI RETURNED` |
| `STR_CHECKPOINT_SLICE_COMPLETE` | `OPENING COMPLETE` |
| `STR_CHECKPOINT_RUSK_RETURN` | `RETURNED FROM RUSK` |
| `STR_CHECKPOINT_ANNEX_TRACE` | `TAVI TRACE COMPLETE` |
| `STR_SAVE_REASON_NONE` | `NOT RECORDED` |
| `STR_SAVE_REASON_CHECKPOINT` | `CHECKPOINT` |
| `STR_SAVE_REASON_MANUAL_RELAY` | `MANUAL RELAY` |
| `STR_SAVE_REASON_BATTLE_RESULT` | `BATTLE RESULT` |
| `STR_SAVE_REASON_FINAL_HOOK` | `FINAL HOOK` |
| `STR_SAVE_REASON_TRANSITION` | `TRANSITION` |
| `STR_SAVE_REASON_SETTINGS` | `SETTINGS` |
| `STR_SAVE_STATE_READY` | `READY` |
| `STR_SAVE_STATE_QUEUED` | `QUEUED` |
| `STR_SAVE_STATE_WRITING` | `WRITING` |
| `STR_SAVE_STATE_VERIFYING` | `VERIFYING` |
| `STR_SAVE_STATE_RECORDED` | `RECORDED` |
| `STR_SAVE_STATE_FAILED` | `FAILED` |
| `STR_SAVE_STATE_CANCELED` | `CANCELED` |
| `STR_SAVE_STATE_TRAVELED_UNSAVED` | `TRAVELED UNSAVED` |
| `STR_SAVE_STATE_ABORTED` | `ABORTED` |
| `STR_MANUAL_SAVE_AVAILABLE` | `AVAILABLE` |

Loading music is also process-owned rather than inferred from a screen filename:

```c
enum ProcessLoadingMusicFlags {
    PROCESS_LOADING_MUSIC_REAL_WORK_ONLY = 1u << 0,
    PROCESS_LOADING_MUSIC_PROGRESS_BOUND = 1u << 1,
    PROCESS_LOADING_MUSIC_ALLOW_IMMEDIATE_HANDOFF = 1u << 2,
    PROCESS_LOADING_MUSIC_RELEASE_BEFORE_DESTINATION = 1u << 3
};

typedef struct ProcessLoadingMusicDef {
    uint16_t owner_id;            /* 0: PROCESS_UI_OWNER_TRANSITION_LOADING_CARD */
    uint16_t state_variant;       /* 2: ProcessUiStateVariantValue */
    AudioCueId cue_id;            /* 4 */
    AudioCueId handoff_cue_id;    /* 6: exact destination SceneDef default */
    uint8_t min_remaining_ticks;  /* 8: one; zero/finished load never starts cue */
    uint8_t flags;                /* 9 */
    uint16_t reserved;            /* 10 */
} ProcessLoadingMusicDef;
_Static_assert(sizeof(ProcessLoadingMusicDef) == 12, "ProcessLoadingMusicDef layout");
```

The two rows are exact:

| Owner / state | Loading cue / handoff cue | Minimum remaining ticks | Exact flags / reserved |
|---|---|---:|---|
| `PROCESS_UI_OWNER_TRANSITION_LOADING_CARD / PROCESS_UI_STATE_LOADING_ANNEX` | `MUSIC_CUE_TITLE / MUSIC_CUE_ANNEX` | `1` | all four named flags / `0` |
| `PROCESS_UI_OWNER_TRANSITION_LOADING_CARD / PROCESS_UI_STATE_LOADING_ESTATE` | `MUSIC_CUE_TITLE / MUSIC_CUE_ESTATE_EXPLORATION` | `1` | all four named flags / `0` |

The loading shell starts the title/loading motif only while at least one measured
load tick remains; it never holds the screen for audio. Completion may hand off
immediately, first releasing the motif stream/cache, then opening the exact
destination default. The Title -> Opening Slot -> Name Entry process chain uses
the same `MUSIC_CUE_TITLE` SceneDef default continuously rather than restarting
it. Missing work, a completed loader, wrong owner/state, a handoff that disagrees
with the destination SceneDef, flags outside `0x0F`, or overlapping full music
buffers fails closed.

The compact item notation below is literal generator input. `MENU` is a rendered
focusable page; `ROOT` adds `CHOICE_ROOT`; `TARGET` is focusable; `CANCEL` adds
`SAFE_CANCEL`; `STATUS` is rendered/nonfocusable; `LAYER` adds
`CO_RENDER_LAYER`; `CAP` adds `CAPABILITY_SELECTED`; and `ACQUIRE_ROOT` is the
only notation that adds `ACQUIRE_DIALOGUE_NODE`. Every item uses
`PROCESS_UI_CONTENT_DIALOGUE_PAGE` unless its name begins `STATIC_` or `VIEW`;
`STATIC_MENU`, `STATIC_ROOT`, `STATIC_STATUS`, `STATIC_TARGET`, and
`STATIC_CANCEL` use
`PROCESS_UI_CONTENT_STATIC_STRING` and otherwise add the same root, status, or
target/cancel flags as their non-static counterparts. `VIEW` uses
`PROCESS_UI_CONTENT_RUNTIME_VIEW`; its typed view registry, never its numeric
content ID, owns internal data/focus behavior. The Settings `VIEW` item exposes
the exact subfocus domain `0..9`; its single item-level focus xref is zero, while
the adjacent Apply/Cancel item xrefs are deliberately `10/11`. Every item has the listed
layer/render/focus order, typed accept kind/value, and zero reserved. `NONE`
means accept kind/value zero.

The generated 38-binding table and its concatenated 125-item table are exact:

| first/count | key `(scene, owner, state)` / base screen | layout / default focus / binding flags | ordered item initializers |
|---:|---|---|---|
| `0/3` | `SCENE_TITLE / TITLE_MENU / DEFAULT` / `UI_SCREEN_TITLE` | `FIXED_MENU / 0 / GEN+CLEAR+ONE+FIXED+BASE+DISABLE` | `MENU(TITLE_001,1,0,0,LOCAL,OPEN_NEW_GAME_PROMPT)`, `MENU(TITLE_002,1,1,1,TOKEN,TITLE_CONTINUE)+STATE_GATED`, `MENU(TITLE_003,1,2,2,LOCAL,OPEN_OPTIONS)` |
| `3/3` | `SCENE_TITLE / TITLE_NEW_GAME_PROMPT / DEFAULT` / `UI_SCREEN_TITLE` | `MODAL_CHOICE / 0 / GEN+CLEAR+ONE+FIXED+BASE+PRESERVE` | `ROOT(TITLE_NEW_CONFIRM,1,0)`, `TARGET(TITLE_NEW_BEGIN,1,1,0,TOKEN,NEW_GAME)`, `CANCEL(TITLE_NEW_BACK,1,2,1,LOCAL,CLOSE_NO_MUTATION)` |
| `6/3` | `SCENE_TITLE / TITLE_OVERWRITE_PROMPT / DEFAULT` / `UI_SCREEN_TITLE` | same modal binding | `ROOT(TITLE_OVERWRITE_CONFIRM,1,0)`, `TARGET(TITLE_OVERWRITE_REPLACE,1,1,0,TOKEN,NEW_GAME)`, `CANCEL(TITLE_OVERWRITE_BACK,1,2,1,LOCAL,CLOSE_NO_MUTATION)` |
| `9/3` | `SCENE_TITLE / TITLE_INVALID_SAVE_PROMPT / DEFAULT` / `UI_SCREEN_TITLE` | same modal binding | `ROOT(TITLE_INVALID_SAVE,1,0)`, `TARGET(TITLE_INVALID_NEW_GAME,1,1,0,TOKEN,NEW_GAME)`, `CANCEL(TITLE_INVALID_BACK,1,2,1,LOCAL,CLOSE_NO_MUTATION)` |
| `12/2` | `SCENE_OPENING_SLOT / OPENING_CUTSCENE_SLATE / DEFAULT` / `UI_SCREEN_CUTSCENE_SLATE` | `CO_RENDER_LAYERS / 0 / GEN+CLEAR+ONE+FIXED+BASE+NO_DIALOGUE` | `LAYER(OPENING_INSERT_CUTSCENE,1,0,NONE)`, `MENU(OPENING_SKIP_PROMPT,2,1,0,TOKEN,OPENING_FINISH)+CO_RENDER` |
| `14/2` | `SCENE_NAME_ENTRY / NAME_ENTRY_SURFACE / DEFAULT` / `UI_SCREEN_NAME_ENTRY` | `PERSISTENT_SURFACE / 0xFF / GEN+CLEAR+ONE+FIXED+BASE+NO_DIALOGUE` | `STATUS(NAME_001,1,0)`, `STATUS(NAME_002,1,1)` |
| `16/1` | `SCENE_NAME_ENTRY / NAME_VALIDATION_EMPTY / DEFAULT` / `UI_SCREEN_NAME_ENTRY` | `SINGLE_STATUS / 0 / GEN+CLEAR+ONE+BASE+PRESERVE` | `MENU(NAME_EMPTY,1,0,0,LOCAL,RETURN_TO_NAME_GRID)` |
| `17/3` | `SCENE_NAME_ENTRY / NAME_CONFIRM_PROMPT / DEFAULT` / `UI_SCREEN_NAME_ENTRY` | `MODAL_CHOICE / 0 / GEN+CLEAR+ONE+FIXED+BASE+PRESERVE` | `ROOT(NAME_CONFIRM,1,0)`, `TARGET(NAME_CONFIRM_YES,1,1,0,TOKEN,NAME_CONFIRM)`, `CANCEL(NAME_CONFIRM_EDIT,1,2,1,LOCAL,RETURN_TO_NAME_GRID)` |
| `20/3` | `SCENE_NAME_ENTRY / NAME_CANCEL_PROMPT / DEFAULT` / `UI_SCREEN_NAME_ENTRY` | same modal binding | `ROOT(NAME_CANCEL,1,0)`, `CANCEL(NAME_CANCEL_KEEP_EDITING,1,1,0,LOCAL,RETURN_TO_NAME_GRID)`, `TARGET(NAME_CANCEL_RETURN,1,2,1,TOKEN,NAME_CANCEL_RETURN)` |
| `23/3` | `0 / OPTIONS_FOOTER / DEFAULT` / `UI_SCREEN_SETTINGS` | `FIXED_MENU / 0 / GEN+CLEAR+ONE+FIXED+BASE+PRESERVE` | `VIEW(SETTINGS_EDITOR,1,0,0,LOCAL,SETTINGS_EDIT)`, `MENU(OPTIONS_APPLY,2,1,10,LOCAL,APPLY_SETTINGS)`, `CANCEL(OPTIONS_CANCEL,2,2,11,LOCAL,CANCEL_SETTINGS)` |
| `26/3` | `0 / INTERACTION_PROMPT_RENDERER / DEFAULT` / `0` | `CAPABILITY_SELECT_ONE / 0xFF / GEN+CLEAR+ONE+NO_DIALOGUE` | `CAP(UI_INTERACT,1,0,LOCAL,INTERACTION_CAPABILITY)`, `CAP(UI_EXAMINE,1,1,LOCAL,INTERACTION_CAPABILITY)`, `CAP(UI_OPEN_RELAY,1,2,LOCAL,INTERACTION_CAPABILITY)` |
| `29/1` | `0 / CONTROLLER / CONTROLLER_DISCONNECTED` / `0` | `SINGLE_STATUS / 0xFF / GEN+CLEAR+ONE+NO_DIALOGUE` | `STATUS(UI_PAUSED_DISCONNECT,1,0)` |
| `30/1` | `0 / CONTROLLER / CONTROLLER_RECONNECT` / `0` | `SINGLE_STATUS / 0 / GEN+CLEAR+ONE+NO_DIALOGUE` | `MENU(UI_RECONNECT,1,0,0,LOCAL,CONTROLLER_RESTORE)` |
| `31/1` | `0 / SAVE_SERVICE / SAVE_WRITING` / `0` | `SINGLE_STATUS / 0xFF / GEN+CLEAR+ONE+NO_DIALOGUE` | `STATUS(UI_SAVING,1,0)` |
| `32/1` | `0 / SAVE_SERVICE / SAVE_DONE` / `0` | `TIMED_SEQUENCE / 0xFF / GEN+CLEAR+ONE` | `STATUS(UI_SAVE_DONE,1,0)` |
| `33/1` | `0 / TRANSITION_LOADING_CARD / LOADING_ANNEX` / `UI_SCREEN_LOADING` | `SINGLE_STATUS / 0xFF / GEN+CLEAR+ONE+BASE+NO_DIALOGUE` | `STATUS(UI_LOADING_ANNEX,1,0)` |
| `34/1` | `0 / TRANSITION_LOADING_CARD / LOADING_ESTATE` / `UI_SCREEN_LOADING` | same loading binding | `STATUS(UI_LOADING_ESTATE,1,0)` |
| `35/1` | `0 / TRANSITION_FAILURE / TRANSITION_BUSY` / `0` | `SINGLE_STATUS / 0 / GEN+CLEAR+ONE+PRESERVE` | `MENU(UI_TRANSITION_BUSY,1,0,0,LOCAL,CLOSE_NO_MUTATION)` |
| `36/1` | `0 / TRANSITION_FAILURE / TRANSITION_FAILED` / `0` | same failure binding | `MENU(UI_TRAVEL_FAILED,1,0,0,LOCAL,CLOSE_NO_MUTATION)` |
| `37/3` | `0 / ROLLBACK_FATAL / ROLLBACK_FATAL` / `UI_SCREEN_PROCESS_SAFE_RECOVERY` | `MODAL_CHOICE / 0 / GEN+CLEAR+ONE+FIXED+BASE+NO_DIALOGUE` | `STATIC_ROOT(STR_PROCESS_RECOVERY_FATAL,1,0)`, `STATIC_TARGET(STR_PROCESS_RECOVERY_RETRY,1,1,0,LOCAL,RETRY_ROLLBACK_LOAD)`, `STATIC_TARGET(STR_PROCESS_RECOVERY_RETURN_TITLE,1,2,1,LOCAL,ROLLBACK_RETURN_TO_TITLE)` |
| `40/10` | `SCENE_WORLD_MAP / WORLD_MAP / DEFAULT` / `UI_SCREEN_WORLD_ROUTE` | `WORLD_MAP / 0 / GEN+CLEAR+ONE+FIXED+BASE+PRESERVE` | `STATUS(MAP_ANNEX_NAME,1,0)`, `STATUS(MAP_ANNEX_DESC,1,1)`, `STATUS(MAP_ESTATE_NAME,1,2)`, `STATUS(MAP_ESTATE_DESC,1,3)`, `ROOT(MAP_TRAVEL_CONFIRM,2,4)`, `TARGET(MAP_TRAVEL_ACTION,2,5,0,LOCAL,MAP_ROUTE_ACCEPT)`, `CANCEL(MAP_TRAVEL_BACK,2,6,1,LOCAL,CLOSE_NO_MUTATION)`, `ROOT(MAP_RETURN_CONFIRM,2,7)`, `TARGET(MAP_RETURN_ACTION,2,8,0,LOCAL,MAP_ROUTE_ACCEPT)`, `CANCEL(MAP_RETURN_BACK,2,9,1,LOCAL,CLOSE_NO_MUTATION)` |
| `50/2` | `SCENE_END_CHAPTER / END_CHAPTER_MARK / DEFAULT` / `UI_SCREEN_CHAPTER_END` | `TIMED_SEQUENCE / 0xFF / GEN+CLEAR+ONE+FIXED+BASE` | `STATUS(END_GAME_MARK,1,0)`, `STATUS(END_OPENING_CHAPTER,1,1)` |
| `52/4` | `0 / FINAL_SAVE_FAILURE / DEFAULT` / `0` | `MODAL_CHOICE / 0 / GEN+CLEAR+ONE+FIXED+PRESERVE` | `ACQUIRE_ROOT(UI_SAVE_FAILED,1,0)`, `STATIC_STATUS(STR_SAVE_FAILURE_FINAL_REPLAY_WARNING,1,1)`, `TARGET(END_RETRY_SAVE,1,2,0,LOCAL,SAVE_RETRY_IMMUTABLE)`, `TARGET(END_CONTINUE_UNSAVED,1,3,1,LOCAL,SAVE_CONTINUE_DIRTY)` |
| `56/3` | `SCENE_END_CHAPTER / END_CARD_MENU / DEFAULT` / `UI_SCREEN_CHAPTER_END` | `MODAL_CHOICE / 0 / GEN+CLEAR+ONE+FIXED+BASE` | `ROOT(END_MENU_ROOT,1,0)`, `TARGET(END_CONTINUE_EXPLORING,1,1,0,LOCAL,END_CONTINUE_EXPLORING)`, `TARGET(END_RETURN_TO_TITLE,1,2,1,TOKEN,RETURN_TO_TITLE)` |
| `59/3` | `0 / END_DIRTY_RETURN_WARNING / DEFAULT` / `0` | `MODAL_CHOICE / 0 / GEN+CLEAR+ONE+FIXED+PRESERVE` | `ROOT(END_UNSAVED_WARNING,1,0)`, `CANCEL(END_STAY,1,1,0,LOCAL,DIRTY_STAY)`, `TARGET(END_RETURN,1,2,1,TOKEN,RETURN_TO_TITLE)` |
| `62/4` | `0 / PRE_TRANSITION_SAVE_FAILURE / DEFAULT` / `0` | `MODAL_CHOICE / 0 / GEN+CLEAR+ONE+FIXED+PRESERVE+NO_DIALOGUE` | `STATIC_ROOT(STR_SAVE_FAILURE_PRE_TRANSITION,1,0)`, `TARGET(END_RETRY_SAVE,1,1,0,LOCAL,SAVE_RETRY_IMMUTABLE)`, `TARGET(END_CONTINUE_UNSAVED,1,2,1,LOCAL,SAVE_TRAVEL_UNSAVED)`, `CANCEL(OPTIONS_CANCEL,1,3,2,LOCAL,SAVE_CANCEL_TO_OWNER)` |
| `66/3` | `0 / COMMITTED_PROGRESS_SAVE_FAILURE / DEFAULT` / `0` | `MODAL_CHOICE / 0 / GEN+CLEAR+ONE+FIXED+PRESERVE+NO_DIALOGUE` | `STATIC_ROOT(STR_SAVE_FAILURE_COMMITTED_PROGRESS,1,0)`, `TARGET(END_RETRY_SAVE,1,1,0,LOCAL,SAVE_RETRY_IMMUTABLE)`, `TARGET(END_CONTINUE_UNSAVED,1,2,1,LOCAL,SAVE_CONTINUE_DIRTY)` |
| `69/3` | `0 / RETENTION_ONCE_SAVE_FAILURE / DEFAULT` / `0` | `MODAL_CHOICE / 0 / GEN+CLEAR+ONE+FIXED+PRESERVE+NO_DIALOGUE` | `STATIC_ROOT(STR_SAVE_FAILURE_RETENTION_ONCE,1,0)`, `TARGET(END_RETRY_SAVE,1,1,0,LOCAL,SAVE_RETRY_IMMUTABLE)`, `TARGET(END_CONTINUE_UNSAVED,1,2,1,LOCAL,SAVE_CONTINUE_DIRTY)` |
| `72/3` | `0 / MANUAL_SETTINGS_SAVE_FAILURE / DEFAULT` / `0` | `MODAL_CHOICE / 0 / GEN+CLEAR+ONE+FIXED+PRESERVE+NO_DIALOGUE` | `STATIC_ROOT(STR_SAVE_FAILURE_MANUAL_SETTINGS,1,0)`, `TARGET(END_RETRY_SAVE,1,1,0,LOCAL,SAVE_RETRY_IMMUTABLE)`, `CANCEL(OPTIONS_CANCEL,1,2,1,LOCAL,SAVE_CANCEL_TO_OWNER)` |
| `75/3` | `0 / ROLLBACK_DIRTY_RETURN_WARNING / DEFAULT` / `UI_SCREEN_PROCESS_SAFE_RECOVERY` | `MODAL_CHOICE / 0 / GEN+CLEAR+ONE+FIXED+BASE+PRESERVE` | `ROOT(END_UNSAVED_WARNING,1,0)`, `CANCEL(END_STAY,1,1,0,LOCAL,DIRTY_STAY)`, `TARGET(END_RETURN,1,2,1,TOKEN,RETURN_TO_TITLE)` |
| `78/3` | `0 / NEW_GAME_INITIALIZATION_SAVE_FAILURE / DEFAULT` / `0` | `MODAL_CHOICE / 0 / GEN+CLEAR+ONE+FIXED+PRESERVE+NO_DIALOGUE` | `STATIC_ROOT(STR_SAVE_FAILURE_NEW_GAME_INITIALIZATION,1,0)`, `TARGET(END_RETRY_SAVE,1,1,0,LOCAL,SAVE_RETRY_IMMUTABLE)`, `STATIC_TARGET(STR_PROCESS_RECOVERY_RETURN_TITLE,1,2,1,TOKEN,NEW_GAME_ABORT)` |
| `81/5` | `0 / PAUSE_MENU / DEFAULT` / `UI_SCREEN_PAUSE` | `FIXED_MENU / 0 / GEN+CLEAR+ONE+FIXED+BASE+PRESERVE+DISABLE` | `STATIC_MENU(STR_PAUSE_RESUME,1,0,0,LOCAL,PAUSE_RESUME)`, `STATIC_MENU(STR_PAUSE_PARTY,1,1,1,LOCAL,OPEN_PARTY)+STATE_GATED`, `STATIC_MENU(STR_PAUSE_FIELD_RELAY,1,2,2,LOCAL,OPEN_FIELD_RELAY)+STATE_GATED`, `STATIC_MENU(STR_PAUSE_SETTINGS,1,3,3,LOCAL,OPEN_OPTIONS)+STATE_GATED`, `STATIC_TARGET(STR_PROCESS_RECOVERY_RETURN_TITLE,1,4,4,TOKEN,RETURN_TO_TITLE)` |
| `86/7` | `0 / FIELD_RELAY / RELAY_PARTY` / `UI_SCREEN_RELAY_PARTY` | `TABBED_RUNTIME_VIEW / 0 / GEN+CLEAR+ONE+FIXED+BASE+PRESERVE+DISABLE` | `STATIC_MENU(STR_PAUSE_PARTY,1,0,0,LOCAL,RELAY_OPEN_PARTY)`, `STATIC_MENU(STR_RELAY_MESSAGES,1,1,1,LOCAL,RELAY_OPEN_MESSAGES)+STATE_GATED`, `STATIC_MENU(STR_RELAY_RESONANCE,1,2,2,LOCAL,RELAY_OPEN_RESONANCE)+STATE_GATED`, `STATIC_MENU(STR_RELAY_MAP,1,3,3,LOCAL,RELAY_OPEN_MAP)+STATE_GATED`, `STATIC_MENU(STR_RELAY_SAVE,1,4,4,LOCAL,RELAY_OPEN_SAVE)+STATE_GATED`, `VIEW(RELAY_PARTY,2,5,NONE)`, `STATIC_CANCEL(STR_UI_BACK,3,6,5,LOCAL,RETURN_TO_CAPTURED_ORIGIN)` |
| `93/7` | `0 / FIELD_RELAY / RELAY_MESSAGES` / `UI_SCREEN_RELAY_MESSAGES` | same Relay binding | `STATIC_MENU(STR_PAUSE_PARTY,1,0,0,LOCAL,RELAY_OPEN_PARTY)`, `STATIC_MENU(STR_RELAY_MESSAGES,1,1,1,LOCAL,RELAY_OPEN_MESSAGES)`, `STATIC_MENU(STR_RELAY_RESONANCE,1,2,2,LOCAL,RELAY_OPEN_RESONANCE)`, `STATIC_MENU(STR_RELAY_MAP,1,3,3,LOCAL,RELAY_OPEN_MAP)`, `STATIC_MENU(STR_RELAY_SAVE,1,4,4,LOCAL,RELAY_OPEN_SAVE)`, `VIEW(RELAY_MESSAGES,2,5,NONE)`, `STATIC_CANCEL(STR_UI_BACK,3,6,5,LOCAL,RETURN_TO_CAPTURED_ORIGIN)` |
| `100/7` | `0 / FIELD_RELAY / RELAY_RESONANCE` / `UI_SCREEN_RELAY_RESONANCE` | same Relay binding | `STATIC_MENU(STR_PAUSE_PARTY,1,0,0,LOCAL,RELAY_OPEN_PARTY)`, `STATIC_MENU(STR_RELAY_MESSAGES,1,1,1,LOCAL,RELAY_OPEN_MESSAGES)`, `STATIC_MENU(STR_RELAY_RESONANCE,1,2,2,LOCAL,RELAY_OPEN_RESONANCE)`, `STATIC_MENU(STR_RELAY_MAP,1,3,3,LOCAL,RELAY_OPEN_MAP)`, `STATIC_MENU(STR_RELAY_SAVE,1,4,4,LOCAL,RELAY_OPEN_SAVE)`, `VIEW(RELAY_RESONANCE,2,5,NONE)`, `STATIC_CANCEL(STR_UI_BACK,3,6,5,LOCAL,RETURN_TO_CAPTURED_ORIGIN)` |
| `107/7` | `0 / FIELD_RELAY / RELAY_MAP` / `UI_SCREEN_RELAY_MAP` | same Relay binding | `STATIC_MENU(STR_PAUSE_PARTY,1,0,0,LOCAL,RELAY_OPEN_PARTY)`, `STATIC_MENU(STR_RELAY_MESSAGES,1,1,1,LOCAL,RELAY_OPEN_MESSAGES)`, `STATIC_MENU(STR_RELAY_RESONANCE,1,2,2,LOCAL,RELAY_OPEN_RESONANCE)`, `STATIC_MENU(STR_RELAY_MAP,1,3,3,LOCAL,RELAY_OPEN_MAP)`, `STATIC_MENU(STR_RELAY_SAVE,1,4,4,LOCAL,RELAY_OPEN_SAVE)`, `VIEW(RELAY_MAP,2,5,NONE)`, `STATIC_CANCEL(STR_UI_BACK,3,6,5,LOCAL,RETURN_TO_CAPTURED_ORIGIN)` |
| `114/8` | `0 / FIELD_RELAY / RELAY_SAVE` / `UI_SCREEN_RELAY_SAVE` | same Relay binding | `STATIC_MENU(STR_PAUSE_PARTY,1,0,0,LOCAL,RELAY_OPEN_PARTY)`, `STATIC_MENU(STR_RELAY_MESSAGES,1,1,1,LOCAL,RELAY_OPEN_MESSAGES)`, `STATIC_MENU(STR_RELAY_RESONANCE,1,2,2,LOCAL,RELAY_OPEN_RESONANCE)`, `STATIC_MENU(STR_RELAY_MAP,1,3,3,LOCAL,RELAY_OPEN_MAP)`, `STATIC_MENU(STR_RELAY_SAVE,1,4,4,LOCAL,RELAY_OPEN_SAVE)`, `VIEW(RELAY_SAVE,2,5,NONE)`, `STATIC_TARGET(STR_MANUAL_RECORD_PROGRESS,3,6,5,LOCAL,MANUAL_SAVE_OPEN_CONFIRM)+STATE_GATED`, `STATIC_CANCEL(STR_UI_BACK,3,7,6,LOCAL,RETURN_TO_CAPTURED_ORIGIN)` |
| `122/3` | `0 / MANUAL_SAVE_CONFIRM / DEFAULT` / `UI_SCREEN_RELAY_SAVE` | `MODAL_CHOICE / 0 / GEN+CLEAR+ONE+FIXED+BASE+PRESERVE+NO_DIALOGUE` | `STATIC_ROOT(STR_MANUAL_SAVE_CONFIRM,1,0)`, `STATIC_TARGET(STR_MANUAL_SAVE_ACCEPT,1,1,0,LOCAL,MANUAL_SAVE_SUBMIT)`, `STATIC_CANCEL(STR_UI_BACK,1,2,1,LOCAL,CLOSE_NO_MUTATION)` |

Every `PROCESS_UI_CONTENT_RUNTIME_VIEW` item must resolve exactly one row in
`SETTINGS_RUNTIME_VIEW` or `RELAY_RUNTIME_VIEWS`; no runtime view may be
unreferenced, referenced by a mismatched screen/page, or treated as a StringId.
Each Relay view's `field_count` must equal one contiguous `field_order=0..N-1`
slice in `RELAY_RUNTIME_FIELDS`, and every source ID occurs exactly once. Its
`source_flags` must equal, with no missing or extra bit, the union required by
those fields: Party includes validated slots, creature/move definitions, and
Sync/Team Link; Messages includes message rows and story flags; Resonance
includes Sync/Team Link and story flags; Map includes destination bits, story
flags, and the save-location registry; Save includes the save-location registry,
SaveService owner, and story flags.
Relay page flags are an exact row contract, not a permissive mask: Party is
`ALLOW_PRE_RELAY_PARTY + INFORMATION_ONLY`; Messages and Resonance are
`REQUIRE_RELAY_UNLOCKED + REQUIRE_PERSISTED_BIT + INFORMATION_ONLY`; Map adds
the same three flags and is information-only; Save alone is
`REQUIRE_RELAY_UNLOCKED + REQUIRE_ALL_PERSISTED_BITS + PLAYER_SAVE_SURFACE`.
Every information-only page rejects StoryAction, SaveRequest, TransitionId, and
read/once mutation. Save rejects `INFORMATION_ONLY` and may create only the
typed Manual Relay producer. Any extra/missing flag or a non-Save player-save
surface fails generation.
The 27-row `RELAY_RUNTIME_FIELDS` table and 68-row
`RELAY_DISPLAY_STRINGS` table are exhaustive. The latter is the value-to-copy authority for every
formatter that names runtime save data. Its location domain is set-equal to all
31 `SaveableLocationIdValue` rows, checkpoint domain to values `0..11`, reason
domain to `0..6`, request-phase domain to `0..12`, and Manual domain to all five
`RelayManualEligibilityValue` values. Keys `(domain,value)` are unique, both
reserved fields are zero, and every target is in the process-static catalog.
Location lookup occurs only after exact `SaveableLocationDef` tuple resolution;
unresolved tuples never fall back to a zone/scene name. Request phase comes from
the retained generation-current SaveService request or `SAVE_REQUEST_EMPTY`
when quiescent. Manual state is derived in order: active matching request
`BUSY`, terminal current matching request `RECORDED/FAILED`, legal route
`AVAILABLE`, otherwise `BLOCKED`. Runtime code may not format an enum name or
embed alternate copy.
Message-state formatting maps only to `STR_RELAY_READ`,
`STR_RELAY_PENDING`, or `STR_RELAY_RESOLVED`; lock formatting maps only to
`STR_RELAY_LOCKED/STR_RELAY_UNLOCKED`; dirty formatting maps only to
`STR_RELAY_CLEAN/STR_RELAY_UNSAVED`; and ineligible Manual formatting uses
`STR_MANUAL_SAVE_BLOCKED`. `PARTY_PAIR` always labels columns with registered
`STR_RELAY_LEFT/STR_RELAY_RIGHT`. These mappings and the literal field table are
the sole label/copy authority; formatters may insert only ASCII digits,
`/`, `%`, `:`, and spaces around registered content.
The five Relay payloads have these exact visible field orders:

| view | exact ordered fields and empty/locked rule |
|---|---|
| Party | player name; active Left/Right markers; creature display name + level; current/derived-max HP; Sync `0..1000`; four unlocked MoveDef names in slot order; Team Link. A zero party renders `NO PARTY ASSIGNED`; otherwise every value comes from one validated generation-current `GameProgress.PartySlot` snapshot. The view never reads `BattleActor`, `BattleState`, a presenter endpoint, or in-progress battle HP. |
| Messages | sender/title; state (`READ`, `PENDING`, or `RESOLVED`); ordered message-list position/count; exact detail Dialogue page; detail-page position/count. Tavi appears iff Relay is unlocked and is READ because its three-page packet was mandatory acquisition copy. Ivo appears iff `FLAG_TAVI_FOUND`; it uses `REUNION_008` and PENDING until `FLAG_SOLACE_BEACON_RECEIVED`, then swaps only its detail copy to `HOOK_001` and state to RESOLVED. Back is the separate, final Process UI item and is not a runtime field. No menu open sets a story/read bit. |
| Resonance | Team Link; Left Sync; Right Sync; Rusk record locked/unlocked from encounter-clear + reward-claim equivalence; shared-meter explanation derived from the frozen battle rules. Before the real reward, values are truthfully zero/locked, never fabricated activity. |
| Map | Annex node name/status (always unlocked in initialized play); Estate node name/status from destination bit plus `FLAG_ESTATE_DESTINATION_UNLOCKED`; current stable location marker; `TRAVEL FROM AN EXTERIOR SKIMMER` informational footer. It cannot submit a TransitionId. |
| Save | current resolved stable location; checkpoint name; last SaveReason; runtime clean/dirty state; SaveService status; Manual eligibility/result. An unresolved location renders `STR_MANUAL_SAVE_BLOCKED` and disables Record. |

`RelayMessageDef.detail_page_count` is three only for the contiguous
`TAVI_MSG_001..003` packet and one for Ivo. A detail view reads graph copy but
never acquires DialogueController, follows `next_id`, fires an action, or changes
a once bit. Missing/duplicate rows, noncontiguous Tavi pages, wrong unlock/state
facts, an invalid PartySlot/MoveDef reference, HP above derived max, or a Save
view whose location is not the exact registry result fails closed.

Pause can acquire only from a generation-current `SCENE_ALLOW_PAUSE` scene at
a fixed-step boundary with no dialogue action, transition commit, battle action,
or save candidate publish in flight. Acquisition freezes the exact control
owner, creates one `ProcessUiOriginSnapshot`, clears all edges, and discards one
poll frame. Resume/B closes only the Pause owner and restores that same scene,
zone, stable state token, controller port, and generation; it never reloads a
spawn. Party is enabled as soon as a nonempty party exists, even when Relay is
locked. The Field Relay entry stays visible but disabled until its flag and all
four persisted page bits are present. Pause Settings is enabled only at an
initialized condition-valid Continue location—exploration additionally needs
manual-allowed, while Sim Intro requires the exact tutorial pause-safe boundary.
`PauseMenuAvailabilityFlags` accepts only `0x003F`. `PAUSE_REQUIRE_NO_BATTLE_RUNTIME`
is present on Party and Field Relay, so both entries remain visible but disabled
whenever any `BattleRuntimeOwner` is live. `PAUSE_REQUIRE_SETTINGS_LOCATION`
requires no live battle owner at an exploration location. Its sole battle-owner
exception is `ENCOUNTER_SIM_TUTORIAL` at `SAVELOC_SIM_INTRO`, with the live
owner's runtime generation equal to `GameProgress.runtime_generation`, its
`battle_generation` equal to the Pause snapshot's `control_generation`, and the
frozen phase exactly command or target selection with no action, presentation,
result, transition, save candidate, or tutorial-gate transaction live. A real
battle therefore exposes only enabled Resume and Return to Title; the tutorial
may additionally enable Settings at that exact safe boundary. Relay payloads
never overlay `BattleActor` values, and no Pause child can serialize partial
battle state.

Opening pre-Relay Party captures Pause as its physical origin and selects only
Party; all other tabs are disabled and L/R remains on Party. Opening Field Relay
from Pause always starts on Party and captures Pause focus. `{C-DOWN}` can open
it only after Relay unlock from generation-current stable exploration and
captures gameplay. Unlocked L/R/direct-tab traversal uses exact page order
Party, Messages, Resonance, Map, Save. B from any page returns to the captured
Pause focus or exact frozen gameplay owner; B from save confirmation returns
only to Relay Save. Each state change clears edges/discards a poll. A stale
origin, unavailable tab, or persisted-bit mismatch cannot fall through.

Relay Save enables Record only when its exact `UserSaveUiRouteDef` passes.
Confirm reserves a no-fail modal close, consumes the edge, closes the modal, and
then attempts that service producer. BUSY keeps unpublished scratch, disables
input, and co-renders SaveService `UI_SAVING` until slot release. Admission
captures the latest manual-legal stable snapshot, replaces both LocationKeys
with that exact tuple, and sets only request provenance
`SAVE_REASON_MANUAL_RELAY`; it follows the existing immutable SaveRequest
lifecycle. COMMITTED co-renders timed `UI_SAVE_DONE`, marks the retained Save
view successful, and restores its focus. Failure routes only to the shared
Manual/Settings owner: Retry reuses immutable bytes, while Cancel discards the
manual candidate and returns with live progress/settings/dirty state unchanged.

The Settings service row is Pause-origin only. On current verified commit, Save
Done destroys the same-generation session and its embedded
`ProcessUiOriginSnapshot`, then restores captured Pause focus. Failure Cancel
first performs exact prior-settings/SaveReason/dirty restoration. Title Apply
never resolves a user-save row. Settings view focus `0..9` is owned by the typed
runtime view; ProcessUi Apply/Cancel items own `10/11`.

The first Return press is a selector, never an acknowledgement. Clean runtime
routes directly. Dirty runtime atomically creates `DirtyReturnWarningOwner`,
captures one exact route's source state/focus/generations, consumes the first
edge, and opens its warning. STAY validates/destroys the warning and restores
that exact Pause, End Card, or rollback-fatal origin without an ack. Confirmed
Return alone emits the route's single-use `DirtyWarningAckValue` together with a
fresh `PROCESS_ACCEPT_RETURN_TO_TITLE`; navigation reserves teardown before the
warning releases. Stale, duplicate, cross-origin, or cross-paired acks fail
closed.

Table abbreviations expand exactly to the named `PROCESS_UI_*` constants;
`TITLE_CONTINUE`, `NEW_GAME`, `OPENING_FINISH`, `NAME_CONFIRM`,
`NAME_CANCEL_RETURN`, `RETURN_TO_TITLE`, and `NEW_GAME_ABORT` expand to the corresponding
`PROCESS_ACCEPT_*` values. "Same" copies every field except the displayed key,
state, and items. Base `UI_SCREEN_CUTSCENE_SLATE` is branded layer 0;
`OPENING_INSERT_CUTSCENE` is layer 1 and the skip affordance is layer 2 for
exactly the authored 106 ticks. A/Start on the skip item emits one
`PROCESS_ACCEPT_OPENING_FINISH` to the idempotent finalizer, which owns the
nonblocking `AUDIO_CUE_STORY_SLATE_SKIP` route; these two page rows never enter
DialogueController sequencing.

Title's order is exactly New Game, Continue, Options. Continue remains visible
but disabled unless the verified journal exposes a legal page; disabled focus
cannot emit `PROCESS_ACCEPT_TITLE_CONTINUE`. Overwrite/invalid-save acceptance
creates or validates the in-memory new-game draft before emitting
`PROCESS_ACCEPT_NEW_GAME`; it never erases a raw page. Name YES and Return emit
their exact name tokens only after a debounced target accept. Every open/close,
state change, controller recovery, and capability selection clears latches and
discards one poll frame. A content ID is interpreted only by its declared source
kind and never as an action.

`TRANSITION_FAILED` is closeable only after the rollback descriptor has
successfully reloaded and validated the source scene. If destination load and
then source rollback-load both fail, the controller destroys every partial scene
scope, retains only the process arena plus immutable rollback descriptor, and
selects the distinct `ROLLBACK_FATAL` binding. Retry Recovery makes a fresh,
generation-bound attempt to load the same validated source descriptor regardless
of dirty state. `ROLLBACK_RETURN_TO_TITLE` is a typed selector: clean runtime
emits Return-to-Title immediately; dirty runtime opens the exact
`ROLLBACK_DIRTY_RETURN_WARNING` modal as a child while retaining
`PROCESS_UI_OWNER_ROLLBACK_FATAL` as the navigation source. Cancel returns to
recovery without mutation; confirmed Return publishes
`DIRTY_WARNING_ROLLBACK_FATAL_RETURN_ACK`, destroys dirty runtime, and enters
`SCENE_TITLE`. Neither action can expose a scene, collision, actor, or control
owner that failed to load. Closing the ordinary travel-failed row from
rollback-fatal state, using screen 0, bypassing the dirty modal, or depending on
a scene bundle is a generation/runtime assertion failure.

New Game's `OPEN_NEW_GAME_PROMPT` local action is a selector, not a hard-coded
owner. The verified
loader publishes one generation-current title disposition and the exact
`TitleNewGameRouteDef` rows are `{ EMPTY,0,TITLE_NEW_GAME_PROMPT }`,
`{ VALID,0,TITLE_OVERWRITE_PROMPT }`, and
`{ INVALID_OR_INCOMPATIBLE,0,TITLE_INVALID_SAVE_PROMPT }`. EMPTY means neither
journal page contains a candidate progression record; VALID means the loader
selected a semantically legal general or slice-final page; and
INVALID_OR_INCOMPATIBLE means raw candidate progression bytes exist but no page
is loadable. Equal-sequence divergent envelopes and exact half-range sequence
pairs also map to INVALID_OR_INCOMPATIBLE: they publish no selected runtime page,
disable Continue, preserve both raw pages, and use the same explicit diagnostic
New Game confirmation. Page A may become a deterministic overwrite anchor only
after that confirmation; it is never exposed as selected progress. Selection
fails closed on an absent/stale loader generation and
does not mutate, erase, migrate, or encode a journal page. Duplicate or missing
dispositions, a non-title target owner, or a selector path that bypasses the
listed confirmation binding fails generation.

Accepting BEGIN/REPLACE on any title route allocates one fixed
`RuntimeDraftOwner`: a nonzero owner generation, nonzero mixed campaign seed,
sanitized settings/generation, empty validated-name fields, an immutable
`NewGameJournalWritePlan`, and a separate monotonic
`NewGameJournalWriteAuthority`. The plan stores both exact 240-byte page arrays,
their CRC-32 values only as fast corruption/comparison prechecks, exact decoded
sequence/schema bit patterns, explicit page classes, title disposition,
deterministic planned anchor/target, confirmation epoch, and flags. Sequence or
schema zero is ordinary data; only the explicit class determines validity.
EMPTY uses UNASSIGNED/A and clears OVERWRITE_EXISTING; ordinary valid/invalid/
incompatible overwrite sets OVERWRITE_EXISTING; equal-divergent or half-range
confirmation also sets AMBIGUITY_OVERWRITE_ACCEPTED. Plan flags accept only
`0x0000007F`, reserved bytes are zero, and `identity_crc32` covers the immutable
bytes `0..523` and excludes itself. The authority state is outside that CRC and
moves only NONE -> CONFIRMED -> CONSUMED. Every field must agree with the same
generation-current loader snapshot.

The typed owner survives the opening slate and name editor. Each accepted phase
updates only its declared draft fields/flags; name bytes are uppercase,
zero-padded, and length 1..8 before NAME_CONFIRMED. Cancel zeros the entire
owner, plan, and authority. Name-to-Sim is active-only: after coherent Sim
staging but before initialized progress is visible, it requires a quiescent Save
Service, reserves the active slot, builds the first After-Name request with the
same campaign-owner and plan generations, and sets
`SAVE_REQUEST_OVERWRITE_AUTHORITY_REQUIRED` when an existing envelope must be
replaced.

That sole-writer promotion rereads both pages, uses the stored per-page CRCs only
to reject obvious drift, then byte-compares all 240 bytes of page A and all 240
bytes of page B against `page_a_raw`/`page_b_raw`. It also requires exact loader,
class, sequence, schema, plan-CRC, confirmation, authority, draft-owner, and
campaign-owner equality before assigning a target or invalidating any byte. A
mismatch yields ADDRESS_CONFLICT with no write and no initialized progress
publish, terminally returns to Title, reruns the loader, and requires fresh
confirmation. No generic request or hash match can manufacture overwrite
authority.

Only after address promotion succeeds does the controller atomically publish
the initialized Sim progress and a `FinalSaveOutcomeOwner` containing the same
campaign owner/seed with PENDING, then enqueue the addressed bytes. Write or
verify failure exposes only immutable Retry or explicit Return-to-Title abort;
continuing an unpersisted new campaign is intentionally illegal. Retry preserves
the assigned target and CONFIRMED authority. Verified footer-last commit records
the request generation in the authority and moves it to CONSUMED; this is the
only consume edge. A preserved older complete page or late request whose two
campaign mirrors differ cannot mark the new campaign SAVED. Goldens cover Empty,
valid/incompatible overwrite, both ambiguity classes, page drift during slate/
name, completed-old-campaign overwrite, quiescence rejection, address conflict
before publish, first-write failure -> Retry -> success, first-write failure ->
Return Title -> fresh loader, and one consume edge.

Campaign ownership is minted on every playable-runtime entry, not only New
Game. A verified Title Continue/load allocates a fresh nonzero
`campaign_owner_generation`, copies the decoded nonzero campaign seed into
`FinalSaveOutcomeOwner`, sets outcome SAVED only for a semantically valid Slice
Complete page (otherwise PENDING), overlays the sanitized Title process profile,
sets runtime CLEAN when all eight settings bytes match or DIRTY when they differ,
and requires the entire
`RuntimeDraftOwner` to be zero/NONE. New Game transfers the already-minted draft
owner generation and seed into the runtime/outcome owner at the initialized Sim
publish; it never allocates a second identity. On the first verified new-campaign
COMMITTED result, reconciliation first proves both mirrors, records and emits the
CONSUMED authority audit edge, then zeroes all 580 bytes of RuntimeDraftOwner.
Clean Return-to-Title, confirmed dirty-loss Return, and New Game abort first
fence all callbacks/requests, invalidate the current campaign owner, and only
then allow Title to mint a load owner or new draft. A stale owner generation,
seed mismatch, nonzero draft beside a loaded campaign, double transfer, or late
callback after teardown is a hard runtime/host-test failure.

Save failure routing is typed from the originating operation through one policy
to exactly one Process UI owner. `ProcessUiBindingDef` remains the sole page and
button/action composition authority; neither policy nor route duplicates copy,
Dialogue roots, labels, or dispatch actions:

```c
typedef enum SaveFailureUiPolicyIdValue {
    SAVE_FAILURE_POLICY_FINAL_HOOK = 1,
    SAVE_FAILURE_POLICY_PRE_TRANSITION = 2,
    SAVE_FAILURE_POLICY_COMMITTED_PROGRESS = 3,
    SAVE_FAILURE_POLICY_RETENTION_ONCE = 4,
    SAVE_FAILURE_POLICY_MANUAL_OR_SETTINGS = 5,
    SAVE_FAILURE_POLICY_NEW_GAME_INITIALIZATION = 6
} SaveFailureUiPolicyIdValue;

typedef enum SaveFailureSourceKindValue {
    SAVE_FAILURE_SOURCE_FINAL_HOOK = 1,
    SAVE_FAILURE_SOURCE_TRANSITION_PRE_SOURCE = 2,
    SAVE_FAILURE_SOURCE_TRANSITION_POST_DESTINATION = 3,
    SAVE_FAILURE_SOURCE_STORY_POST_COMMIT = 4,
    SAVE_FAILURE_SOURCE_RETENTION_ONCE = 5,
    SAVE_FAILURE_SOURCE_MANUAL_RELAY = 6,
    SAVE_FAILURE_SOURCE_SETTINGS = 7,
    SAVE_FAILURE_SOURCE_NEW_GAME_INITIALIZATION = 8
} SaveFailureSourceKindValue;

enum SaveFailureUiPolicyFlags {
    SAVE_FAILURE_ACQUIRE_DIALOGUE_ROOT = 1u << 0,
    SAVE_FAILURE_REUSE_IMMUTABLE_SNAPSHOT = 1u << 1,
    SAVE_FAILURE_CONTINUE_MARKS_DIRTY = 1u << 2,
    SAVE_FAILURE_ALLOW_CANCEL = 1u << 3,
    SAVE_FAILURE_WARN_REBOOT_REPLAY = 1u << 4,
    SAVE_FAILURE_PUBLISH_SCRATCH_BEFORE_TRAVEL = 1u << 5,
    SAVE_FAILURE_ABORT_TO_TITLE_ONLY = 1u << 6
};

typedef struct SaveFailureUiPolicyDef {
    uint8_t policy_id;       /* 0: SaveFailureUiPolicyIdValue */
    uint8_t reserved0;       /* 1: zero */
    uint16_t owner_id;       /* 2: ProcessUiOwnerIdValue */
    uint16_t flags;          /* 4 */
    uint16_t reserved1;      /* 6: zero */
} SaveFailureUiPolicyDef;
_Static_assert(sizeof(SaveFailureUiPolicyDef) == 8, "SaveFailureUiPolicyDef layout");

typedef struct SaveFailureRouteDef {
    uint8_t source_kind;      /* 0: SaveFailureSourceKindValue */
    uint8_t policy_id;        /* 1: SaveFailureUiPolicyIdValue */
    uint16_t owner_id_xref;   /* 2: equality mirror of policy owner */
} SaveFailureRouteDef;
_Static_assert(sizeof(SaveFailureRouteDef) == 4, "SaveFailureRouteDef layout");

typedef enum SaveFailureProducerKindValue {
    SAVE_FAILURE_PRODUCER_MILESTONE = 1,
    SAVE_FAILURE_PRODUCER_TRANSITION_STORY_BINDING = 2,
    SAVE_FAILURE_PRODUCER_RETENTION_RECIPE = 3,
    SAVE_FAILURE_PRODUCER_DESTINATION_SAVE_CLASS = 4,
    SAVE_FAILURE_PRODUCER_SERVICE = 5
} SaveFailureProducerKindValue;

typedef enum SaveFailureServiceProducerIdValue {
    SAVE_FAILURE_SERVICE_MANUAL_RELAY = 1,
    SAVE_FAILURE_SERVICE_SETTINGS = 2
} SaveFailureServiceProducerIdValue;

/* SAVE_FAILURE_SERVICE_SETTINGS is initialized Pause persistence only;
 * Title Options is a process-profile edit and is not a save producer. */

typedef struct SaveFailureProducerRouteDef {
    uint8_t producer_kind; /* 0: SaveFailureProducerKindValue */
    uint8_t source_kind;   /* 1: SaveFailureSourceKindValue */
    uint16_t producer_id;  /* 2: domain selected by producer_kind */
} SaveFailureProducerRouteDef;
_Static_assert(sizeof(SaveFailureProducerRouteDef) == 4, "SaveFailureProducerRouteDef layout");
```

The six policy rows are literal:

| Policy | Exact Process UI owner | Exact flags / reserved bytes |
|---|---|---|
| `SAVE_FAILURE_POLICY_FINAL_HOOK` | `PROCESS_UI_OWNER_FINAL_SAVE_FAILURE` | `ACQUIRE_DIALOGUE_ROOT + REUSE_IMMUTABLE_SNAPSHOT + CONTINUE_MARKS_DIRTY + WARN_REBOOT_REPLAY / 0,0` |
| `SAVE_FAILURE_POLICY_PRE_TRANSITION` | `PROCESS_UI_OWNER_PRE_TRANSITION_SAVE_FAILURE` | `REUSE_IMMUTABLE_SNAPSHOT + CONTINUE_MARKS_DIRTY + ALLOW_CANCEL + WARN_REBOOT_REPLAY + PUBLISH_SCRATCH_BEFORE_TRAVEL / 0,0` |
| `SAVE_FAILURE_POLICY_COMMITTED_PROGRESS` | `PROCESS_UI_OWNER_COMMITTED_PROGRESS_SAVE_FAILURE` | `REUSE_IMMUTABLE_SNAPSHOT + CONTINUE_MARKS_DIRTY + WARN_REBOOT_REPLAY / 0,0` |
| `SAVE_FAILURE_POLICY_RETENTION_ONCE` | `PROCESS_UI_OWNER_RETENTION_ONCE_SAVE_FAILURE` | `REUSE_IMMUTABLE_SNAPSHOT + CONTINUE_MARKS_DIRTY + WARN_REBOOT_REPLAY / 0,0` |
| `SAVE_FAILURE_POLICY_MANUAL_OR_SETTINGS` | `PROCESS_UI_OWNER_MANUAL_SETTINGS_SAVE_FAILURE` | `REUSE_IMMUTABLE_SNAPSHOT + ALLOW_CANCEL / 0,0` |
| `SAVE_FAILURE_POLICY_NEW_GAME_INITIALIZATION` | `PROCESS_UI_OWNER_NEW_GAME_INITIALIZATION_SAVE_FAILURE` | `REUSE_IMMUTABLE_SNAPSHOT + WARN_REBOOT_REPLAY + ABORT_TO_TITLE_ONLY / 0,0` |

The eight source routes are exact and are the only save-error selector:

| Typed failure source | Policy / owner equality xref |
|---|---|
| `SAVE_FAILURE_SOURCE_FINAL_HOOK` | `SAVE_FAILURE_POLICY_FINAL_HOOK / PROCESS_UI_OWNER_FINAL_SAVE_FAILURE` |
| `SAVE_FAILURE_SOURCE_TRANSITION_PRE_SOURCE` | `SAVE_FAILURE_POLICY_PRE_TRANSITION / PROCESS_UI_OWNER_PRE_TRANSITION_SAVE_FAILURE` |
| `SAVE_FAILURE_SOURCE_TRANSITION_POST_DESTINATION` | `SAVE_FAILURE_POLICY_COMMITTED_PROGRESS / PROCESS_UI_OWNER_COMMITTED_PROGRESS_SAVE_FAILURE` |
| `SAVE_FAILURE_SOURCE_STORY_POST_COMMIT` | `SAVE_FAILURE_POLICY_COMMITTED_PROGRESS / PROCESS_UI_OWNER_COMMITTED_PROGRESS_SAVE_FAILURE` |
| `SAVE_FAILURE_SOURCE_RETENTION_ONCE` | `SAVE_FAILURE_POLICY_RETENTION_ONCE / PROCESS_UI_OWNER_RETENTION_ONCE_SAVE_FAILURE` |
| `SAVE_FAILURE_SOURCE_MANUAL_RELAY` | `SAVE_FAILURE_POLICY_MANUAL_OR_SETTINGS / PROCESS_UI_OWNER_MANUAL_SETTINGS_SAVE_FAILURE` |
| `SAVE_FAILURE_SOURCE_SETTINGS` | `SAVE_FAILURE_POLICY_MANUAL_OR_SETTINGS / PROCESS_UI_OWNER_MANUAL_SETTINGS_SAVE_FAILURE` |
| `SAVE_FAILURE_SOURCE_NEW_GAME_INITIALIZATION` | `SAVE_FAILURE_POLICY_NEW_GAME_INITIALIZATION / PROCESS_UI_OWNER_NEW_GAME_INITIALIZATION_SAVE_FAILURE` |

The originating producer mapping is exhaustive and literal. Existing milestone
and transition `failure_policy` bytes continue to define local transaction
behavior; they cannot choose UI. This table alone supplies the source kind that
then resolves through the eight routes above:

| Producer kind / typed producer ID | Exact SaveFailureSourceKindValue |
|---|---|
| `SAVE_FAILURE_PRODUCER_MILESTONE / MILESTONE_AFTER_TUTORIAL` | `SAVE_FAILURE_SOURCE_STORY_POST_COMMIT` |
| `SAVE_FAILURE_PRODUCER_MILESTONE / MILESTONE_FIELD_RELAY` | `SAVE_FAILURE_SOURCE_STORY_POST_COMMIT` |
| `SAVE_FAILURE_PRODUCER_MILESTONE / MILESTONE_ANNEX_TRACE_COMPLETE` | `SAVE_FAILURE_SOURCE_STORY_POST_COMMIT` |
| `SAVE_FAILURE_PRODUCER_MILESTONE / MILESTONE_RUSK_VICTORY` | `SAVE_FAILURE_SOURCE_STORY_POST_COMMIT` |
| `SAVE_FAILURE_PRODUCER_MILESTONE / MILESTONE_TAVI_FOUND` | `SAVE_FAILURE_SOURCE_STORY_POST_COMMIT` |
| `SAVE_FAILURE_PRODUCER_MILESTONE / MILESTONE_TAVI_RETURNED` | `SAVE_FAILURE_SOURCE_STORY_POST_COMMIT` |
| `SAVE_FAILURE_PRODUCER_MILESTONE / MILESTONE_SLICE_COMPLETE` | `SAVE_FAILURE_SOURCE_FINAL_HOOK` |
| `SAVE_FAILURE_PRODUCER_TRANSITION_STORY_BINDING / TRANS_DEF_NAME_TO_SIM` | `SAVE_FAILURE_SOURCE_NEW_GAME_INITIALIZATION` |
| `SAVE_FAILURE_PRODUCER_TRANSITION_STORY_BINDING / TRANS_DEF_THRESHOLD_TO_MAP` | `SAVE_FAILURE_SOURCE_TRANSITION_PRE_SOURCE` |
| `SAVE_FAILURE_PRODUCER_TRANSITION_STORY_BINDING / TRANS_DEF_THRESHOLD_TO_MAP_REPEAT` | `SAVE_FAILURE_SOURCE_TRANSITION_PRE_SOURCE` |
| `SAVE_FAILURE_PRODUCER_TRANSITION_STORY_BINDING / TRANS_DEF_MAP_TO_ESTATE` | `SAVE_FAILURE_SOURCE_STORY_POST_COMMIT` |
| `SAVE_FAILURE_PRODUCER_TRANSITION_STORY_BINDING / TRANS_DEF_ESTATE_TO_MAP` | `SAVE_FAILURE_SOURCE_TRANSITION_PRE_SOURCE` |
| `SAVE_FAILURE_PRODUCER_TRANSITION_STORY_BINDING / TRANS_DEF_RUSK_RETURN_ANNEX` | `SAVE_FAILURE_SOURCE_STORY_POST_COMMIT` |
| `SAVE_FAILURE_PRODUCER_TRANSITION_STORY_BINDING / TRANS_DEF_STUDY_RETURN_TO_MAP` | `SAVE_FAILURE_SOURCE_TRANSITION_PRE_SOURCE` |
| `SAVE_FAILURE_PRODUCER_RETENTION_RECIPE / RETENTION_SAVE_SERA_RUSK_RETURN_ONCE` | `SAVE_FAILURE_SOURCE_RETENTION_ONCE` |
| `SAVE_FAILURE_PRODUCER_DESTINATION_SAVE_CLASS / SAVE_AFTER_DESTINATION_COMMIT` | `SAVE_FAILURE_SOURCE_TRANSITION_POST_DESTINATION` |
| `SAVE_FAILURE_PRODUCER_SERVICE / SAVE_FAILURE_SERVICE_MANUAL_RELAY` | `SAVE_FAILURE_SOURCE_MANUAL_RELAY` |
| `SAVE_FAILURE_PRODUCER_SERVICE / SAVE_FAILURE_SERVICE_SETTINGS` | `SAVE_FAILURE_SOURCE_SETTINGS` |

The admission-policy registry is set-equal with those same eighteen producer
keys. `MANDATORY_COMMON` expands exactly to `OWNER_BLOCKING +
RESERVE_BEFORE_PUBLISH + ALLOW_SUCCESSOR + RETAIN_ORIGIN_UNTIL_TERMINAL`;
`USER_RETAINED` expands exactly to `RESERVE_BEFORE_PUBLISH + ALLOW_SUCCESSOR +
RETAIN_ORIGIN_UNTIL_TERMINAL + BLOCK_SEMANTIC_TRANSACTIONS`. These are authoring
abbreviations only; generated rows contain the literal bit mask and zero
reserved field.

| Producer kind / typed producer ID | Exact priority / busy behavior | Exact policy flags |
|---|---|---|
| `SAVE_FAILURE_PRODUCER_MILESTONE / MILESTONE_AFTER_TUTORIAL` | `SAVE_QUEUE_PRIORITY_MANDATORY_OWNER_BLOCKING / SAVE_QUEUE_BUSY_RETRY_OWNER_TRANSACTION` | `MANDATORY_COMMON` |
| `SAVE_FAILURE_PRODUCER_MILESTONE / MILESTONE_FIELD_RELAY` | `SAVE_QUEUE_PRIORITY_MANDATORY_OWNER_BLOCKING / SAVE_QUEUE_BUSY_RETRY_OWNER_TRANSACTION` | `MANDATORY_COMMON` |
| `SAVE_FAILURE_PRODUCER_MILESTONE / MILESTONE_ANNEX_TRACE_COMPLETE` | `SAVE_QUEUE_PRIORITY_MANDATORY_OWNER_BLOCKING / SAVE_QUEUE_BUSY_RETRY_OWNER_TRANSACTION` | `MANDATORY_COMMON` |
| `SAVE_FAILURE_PRODUCER_MILESTONE / MILESTONE_RUSK_VICTORY` | `SAVE_QUEUE_PRIORITY_MANDATORY_OWNER_BLOCKING / SAVE_QUEUE_BUSY_RETRY_OWNER_TRANSACTION` | `MANDATORY_COMMON` |
| `SAVE_FAILURE_PRODUCER_MILESTONE / MILESTONE_TAVI_FOUND` | `SAVE_QUEUE_PRIORITY_MANDATORY_OWNER_BLOCKING / SAVE_QUEUE_BUSY_RETRY_OWNER_TRANSACTION` | `MANDATORY_COMMON` |
| `SAVE_FAILURE_PRODUCER_MILESTONE / MILESTONE_TAVI_RETURNED` | `SAVE_QUEUE_PRIORITY_MANDATORY_OWNER_BLOCKING / SAVE_QUEUE_BUSY_RETRY_OWNER_TRANSACTION` | `MANDATORY_COMMON` |
| `SAVE_FAILURE_PRODUCER_MILESTONE / MILESTONE_SLICE_COMPLETE` | `SAVE_QUEUE_PRIORITY_MANDATORY_OWNER_BLOCKING / SAVE_QUEUE_BUSY_RETRY_OWNER_TRANSACTION` | `MANDATORY_COMMON` |
| `SAVE_FAILURE_PRODUCER_TRANSITION_STORY_BINDING / TRANS_DEF_NAME_TO_SIM` | `SAVE_QUEUE_PRIORITY_MANDATORY_OWNER_BLOCKING / SAVE_QUEUE_BUSY_RETRY_OWNER_TRANSACTION` | `OWNER_BLOCKING + RESERVE_BEFORE_PUBLISH + REQUIRE_ACTIVE_QUIESCENT + RETAIN_ORIGIN_UNTIL_TERMINAL + BLOCK_SEMANTIC_TRANSACTIONS` |
| `SAVE_FAILURE_PRODUCER_TRANSITION_STORY_BINDING / TRANS_DEF_THRESHOLD_TO_MAP` | `SAVE_QUEUE_PRIORITY_MANDATORY_OWNER_BLOCKING / SAVE_QUEUE_BUSY_RETRY_OWNER_TRANSACTION` | `MANDATORY_COMMON` |
| `SAVE_FAILURE_PRODUCER_TRANSITION_STORY_BINDING / TRANS_DEF_THRESHOLD_TO_MAP_REPEAT` | `SAVE_QUEUE_PRIORITY_MANDATORY_OWNER_BLOCKING / SAVE_QUEUE_BUSY_RETRY_OWNER_TRANSACTION` | `MANDATORY_COMMON` |
| `SAVE_FAILURE_PRODUCER_TRANSITION_STORY_BINDING / TRANS_DEF_MAP_TO_ESTATE` | `SAVE_QUEUE_PRIORITY_MANDATORY_OWNER_BLOCKING / SAVE_QUEUE_BUSY_RETRY_OWNER_TRANSACTION` | `MANDATORY_COMMON` |
| `SAVE_FAILURE_PRODUCER_TRANSITION_STORY_BINDING / TRANS_DEF_ESTATE_TO_MAP` | `SAVE_QUEUE_PRIORITY_MANDATORY_OWNER_BLOCKING / SAVE_QUEUE_BUSY_RETRY_OWNER_TRANSACTION` | `MANDATORY_COMMON` |
| `SAVE_FAILURE_PRODUCER_TRANSITION_STORY_BINDING / TRANS_DEF_RUSK_RETURN_ANNEX` | `SAVE_QUEUE_PRIORITY_MANDATORY_OWNER_BLOCKING / SAVE_QUEUE_BUSY_RETRY_OWNER_TRANSACTION` | `MANDATORY_COMMON` |
| `SAVE_FAILURE_PRODUCER_TRANSITION_STORY_BINDING / TRANS_DEF_STUDY_RETURN_TO_MAP` | `SAVE_QUEUE_PRIORITY_MANDATORY_OWNER_BLOCKING / SAVE_QUEUE_BUSY_RETRY_OWNER_TRANSACTION` | `MANDATORY_COMMON` |
| `SAVE_FAILURE_PRODUCER_RETENTION_RECIPE / RETENTION_SAVE_SERA_RUSK_RETURN_ONCE` | `SAVE_QUEUE_PRIORITY_MANDATORY_OWNER_BLOCKING / SAVE_QUEUE_BUSY_RETRY_OWNER_TRANSACTION` | `MANDATORY_COMMON` |
| `SAVE_FAILURE_PRODUCER_DESTINATION_SAVE_CLASS / SAVE_AFTER_DESTINATION_COMMIT` | `SAVE_QUEUE_PRIORITY_MANDATORY_OWNER_BLOCKING / SAVE_QUEUE_BUSY_RETRY_OWNER_TRANSACTION` | `MANDATORY_COMMON` |
| `SAVE_FAILURE_PRODUCER_SERVICE / SAVE_FAILURE_SERVICE_MANUAL_RELAY` | `SAVE_QUEUE_PRIORITY_USER_INITIATED / SAVE_QUEUE_BUSY_KEEP_USER_SCRATCH` | `USER_RETAINED` |
| `SAVE_FAILURE_PRODUCER_SERVICE / SAVE_FAILURE_SERVICE_SETTINGS` | `SAVE_QUEUE_PRIORITY_USER_INITIATED / SAVE_QUEUE_BUSY_KEEP_USER_SCRATCH` | `USER_RETAINED` |

Each save request resolves exactly one producer row and captures its source kind
with the immutable snapshot before it can enqueue; a generic error callback has
no route. The seven milestone IDs, seven transition-story binding IDs, sole
retention recipe, destination-save class, and two service IDs must be set-equal
with their live producer registries; a missing/extra producer is a generation
failure. Route `owner_id_xref` must
equal the selected policy owner and that owner must have exactly one DEFAULT
Process UI binding. Only `PROCESS_UI_OWNER_FINAL_SAVE_FAILURE` acquires the
binary DialogueNode `UI_SAVE_FAILED -> END_RETRY_SAVE /
END_CONTINUE_UNSAVED`, exactly once. Its static warning is a co-rendered catalog
item, not a second root. Every nonfinal owner uses its policy-specific static
prompt and never acquires a Dialogue node; all buttons and the sole action enum
live only in the 125-item Process UI table.

PRE_TRANSITION Travel Unsaved publishes its already-validated scratch recipe,
marks dirty, and travels; Cancel publishes nothing. COMMITTED/retention Continue
keeps coherent in-memory state dirty. Final, pre-transition, committed, and
retention prompts all state reboot/replay risk explicitly and carry
`WARN_REBOOT_REPLAY`; Manual/Settings has no Continue action and uses neutral
Retry/Cancel copy. New Game initialization has only immutable Retry or an
explicit Return-to-Title abort; it never offers Continue Dirty because no page
for the new campaign has verified yet. Every action is generation-bound to the exact request owner,
and controller loss or re-entry clears prior edges. Duplicate/missing source or
policy keys, xref disagreement, a missing/extra owner binding, item-range
overlap, source/content mismatch, invalid focus/layer order, an unavailable
token, a nonfinal `UI_SAVE_FAILED` acquisition, prompt/policy/action mismatch,
or use of either removed `SaveFailureButtonDef`/button-action domain fails
generation.

#### 13.2.2 Process navigation

Boot/title/opening/name/Continue/Return-to-Title navigation is process-owned and explicit rather than being smuggled into a gameplay portal table. Every trigger token referenced below must come from the exact ProcessUi item above (or an explicitly registered gameplay owner for Return-to-Title); process code never manufactures a page-specific token.

```c
typedef enum ProcessNavigationIdValue {
    PROC_NAV_BOOT_TO_TITLE = 1,
    PROC_NAV_TITLE_NEW_GAME_TO_OPENING = 2,
    PROC_NAV_OPENING_TO_NAME = 3,
    PROC_NAV_NAME_CONFIRM_TO_SIM = 4,
    PROC_NAV_NAME_CANCEL_TO_TITLE = 5,
    PROC_NAV_TITLE_CONTINUE = 6,
    PROC_NAV_GAME_RETURN_TO_TITLE_CLEAN = 7,
    PROC_NAV_END_CARD_CONTINUE_SAVED = 8,
    PROC_NAV_END_CARD_RETURN_TO_TITLE_SAVED = 9,
    PROC_NAV_END_CARD_CONTINUE_DIRTY = 10,
    PROC_NAV_END_CARD_RETURN_TO_TITLE_DIRTY = 11,
    PROC_NAV_GAME_RETURN_TO_TITLE_DIRTY = 12,
    PROC_NAV_ROLLBACK_FATAL_RETRY = 13,
    PROC_NAV_ROLLBACK_FATAL_RETURN_TO_TITLE_CLEAN = 14,
    PROC_NAV_ROLLBACK_FATAL_RETURN_TO_TITLE_DIRTY = 15,
    PROC_NAV_NEW_GAME_ABORT_TO_TITLE = 16
} ProcessNavigationIdValue;

typedef enum ProcessNavigationConditionIdValue {
    COND_PROC_ALWAYS = 0x6401,
    COND_PROC_NEW_GAME_ACCEPTED = 0x6402,
    COND_PROC_OPENING_FINALIZED = 0x6403,
    COND_PROC_NAME_DRAFT_CONFIRMED = 0x6404,
    COND_PROC_NAME_DRAFT_UNCOMMITTED = 0x6405,
    COND_PROC_VALID_CONTINUE_PAGE = 0x6406,
    COND_PROC_STABLE_GAMEPLAY_CLEAN = 0x6407,
    COND_PROC_END_CARD_SAVED = 0x6408,
    COND_PROC_END_CARD_DIRTY_RESOLVED = 0x6409,
    COND_PROC_END_CARD_DIRTY_RETURN_CONFIRMED = 0x640A,
    COND_PROC_STABLE_GAMEPLAY_DIRTY_RETURN_CONFIRMED = 0x640B,
    COND_PROC_ROLLBACK_FATAL_RETRY_READY = 0x640C,
    COND_PROC_ROLLBACK_FATAL_RETURN_CLEAN = 0x640D,
    COND_PROC_ROLLBACK_FATAL_DIRTY_RETURN_CONFIRMED = 0x640E,
    COND_PROC_NEW_GAME_ABORT_READY = 0x640F
} ProcessNavigationConditionIdValue;

typedef enum ProcessNavigationTrigger {
    PROC_TRIGGER_AUTO = 1,
    PROC_TRIGGER_NEW_GAME,
    PROC_TRIGGER_OPENING_FINISH,
    PROC_TRIGGER_NAME_CONFIRM,
    PROC_TRIGGER_NAME_BACK_RETURN,
    PROC_TRIGGER_CONTINUE,
    PROC_TRIGGER_RETURN_TO_TITLE,
    PROC_TRIGGER_RETRY_ROLLBACK_LOAD,
    PROC_TRIGGER_ABORT_NEW_GAME_TO_TITLE
} ProcessNavigationTrigger;

typedef enum ProcessNavigationSourceClass {
    PROC_SOURCE_EXACT_SCENE = 1,
    PROC_SOURCE_ANY_STABLE_GAMEPLAY = 2,
    PROC_SOURCE_PROCESS_UI_OWNER = 3
} ProcessNavigationSourceClass;

enum BootReadySubsystemFlags {
    BOOT_READY_DISPLAY = 1u << 0,
    BOOT_READY_INPUT = 1u << 1,
    BOOT_READY_AUDIO = 1u << 2,
    BOOT_READY_FILESYSTEM = 1u << 3,
    BOOT_READY_JOURNAL_SELECTION = 1u << 4,
    BOOT_READY_SETTINGS_PROFILE = 1u << 5,
    BOOT_READY_TITLE_SHELL = 1u << 6
};

typedef struct BootReadyOwner {
    uint32_t generation;                  /* 0: nonzero boot generation */
    uint32_t completed_flags;             /* 4: BootReadySubsystemFlags */
    uint32_t display_generation;          /* 8: live mode plus safe frame */
    uint32_t input_generation;            /* 12: initial poll/latches cleared */
    uint32_t audio_generation;            /* 16: live mixer or final silent-safe owner */
    uint32_t filesystem_generation;       /* 20: mounted verified ROM FS */
    uint32_t journal_selection_generation;/* 24: nonzero completed loader */
    uint32_t settings_profile_generation; /* 28: exact initialized owner */
    uint32_t title_shell_generation;      /* 32: staged/validated */
    uint8_t token_emitted;                /* 36: exact 0 or 1 */
    uint8_t reserved[3];                  /* 37: zero */
} BootReadyOwner;
_Static_assert(sizeof(BootReadyOwner) == 40, "BootReadyOwner layout");

typedef struct BootReadyToken {
    uint32_t owner_generation;            /* 0 */
    uint32_t display_generation;          /* 4 */
    uint32_t input_generation;            /* 8 */
    uint32_t audio_generation;            /* 12 */
    uint32_t filesystem_generation;       /* 16 */
    uint32_t journal_selection_generation;/* 20 */
    uint32_t settings_profile_generation; /* 24 */
    uint32_t title_shell_generation;      /* 28 */
} BootReadyToken;
_Static_assert(sizeof(BootReadyToken) == 32, "BootReadyToken layout");

enum ProcessNavigationFlags {
    PROC_NAV_INVOKE_GAMEPLAY_TRANSITION = 1u << 0,
    PROC_NAV_LOAD_DYNAMIC_CURRENT_LOCATION = 1u << 1,
    PROC_NAV_LOAD_FIXED_SAVELOC = 1u << 2,
    PROC_NAV_DISCARD_RUNTIME_DRAFT = 1u << 3,
    PROC_NAV_TEARDOWN_GAMEPLAY = 1u << 4,
    PROC_NAV_REENTER_RUNTIME_CURRENT_LOCATION = 1u << 5,
    PROC_NAV_DISCARD_DIRTY_RUNTIME = 1u << 6,
    PROC_NAV_RELOAD_ROLLBACK_SOURCE = 1u << 7,
    PROC_NAV_DISCARD_ROLLBACK_DESCRIPTOR = 1u << 8,
    PROC_NAV_INVALIDATE_CAMPAIGN_OWNER = 1u << 9,
    PROC_NAV_MINT_CAMPAIGN_OWNER_FROM_LOAD = 1u << 10,
    PROC_NAV_FENCE_CAMPAIGN_CALLBACKS = 1u << 11
};

typedef struct ProcessNavigationDef {
    uint16_t id;                         /* 0: ProcessNavigationIdValue */
    uint16_t source_id;                  /* 2: SceneId or ProcessUiOwnerIdValue by source_class; zero only ANY_STABLE */
    SceneId destination_scene_id;        /* 4; zero only for dynamic save location or rollback-source reload */
    ConditionId condition_id;            /* 6 */
    TransitionId gameplay_transition_id; /* 8; zero unless INVOKE */
    SaveableLocationId fixed_saveloc_id; /* 10; zero unless LOAD_FIXED */
    uint8_t trigger;                     /* 12 */
    uint8_t source_class;                /* 13 */
    uint16_t flags;                      /* 14 */
} ProcessNavigationDef;
_Static_assert(sizeof(ProcessNavigationDef) == 16, "ProcessNavigationDef layout");
```

| ProcessNavigationId | Source -> destination | ConditionId | Trigger | Transition/fixed location | Flags |
|---|---|---|---|---|---|
| `PROC_NAV_BOOT_TO_TITLE` | `SCENE_BOOT -> SCENE_TITLE` | `COND_PROC_ALWAYS` | `PROC_TRIGGER_AUTO` | `0 / 0` | `0` |
| `PROC_NAV_TITLE_NEW_GAME_TO_OPENING` | `SCENE_TITLE -> SCENE_OPENING_SLOT` | `COND_PROC_NEW_GAME_ACCEPTED` | `PROC_TRIGGER_NEW_GAME` | `0 / 0` | `0` |
| `PROC_NAV_OPENING_TO_NAME` | `SCENE_OPENING_SLOT -> SCENE_NAME_ENTRY` | `COND_PROC_OPENING_FINALIZED` | `PROC_TRIGGER_OPENING_FINISH` | `0 / 0` | `0` |
| `PROC_NAV_NAME_CONFIRM_TO_SIM` | `SCENE_NAME_ENTRY -> SCENE_SIM_ARENA` | `COND_PROC_NAME_DRAFT_CONFIRMED` | `PROC_TRIGGER_NAME_CONFIRM` | `TRANS_DEF_NAME_TO_SIM / 0` | `PROC_NAV_INVOKE_GAMEPLAY_TRANSITION` |
| `PROC_NAV_NAME_CANCEL_TO_TITLE` | `SCENE_NAME_ENTRY -> SCENE_TITLE` | `COND_PROC_NAME_DRAFT_UNCOMMITTED` | `PROC_TRIGGER_NAME_BACK_RETURN` | `0 / 0` | `PROC_NAV_DISCARD_RUNTIME_DRAFT` |
| `PROC_NAV_TITLE_CONTINUE` | `SCENE_TITLE -> dynamic registry SceneId` | `COND_PROC_VALID_CONTINUE_PAGE` | `PROC_TRIGGER_CONTINUE` | `0 / 0` | `PROC_NAV_LOAD_DYNAMIC_CURRENT_LOCATION + PROC_NAV_MINT_CAMPAIGN_OWNER_FROM_LOAD` |
| `PROC_NAV_GAME_RETURN_TO_TITLE_CLEAN` | `ANY_STABLE_GAMEPLAY -> SCENE_TITLE` | `COND_PROC_STABLE_GAMEPLAY_CLEAN` | `PROC_TRIGGER_RETURN_TO_TITLE` | `0 / 0` | `PROC_NAV_TEARDOWN_GAMEPLAY + PROC_NAV_INVALIDATE_CAMPAIGN_OWNER + PROC_NAV_FENCE_CAMPAIGN_CALLBACKS` |
| `PROC_NAV_END_CARD_CONTINUE_SAVED` | `SCENE_END_CHAPTER -> SCENE_ANNEX_INTERIOR` | `COND_PROC_END_CARD_SAVED` | `PROC_TRIGGER_CONTINUE` | `0 / SAVELOC_ANNEX_ATRIUM_POST_CHAPTER` | `PROC_NAV_LOAD_FIXED_SAVELOC` |
| `PROC_NAV_END_CARD_RETURN_TO_TITLE_SAVED` | `SCENE_END_CHAPTER -> SCENE_TITLE` | `COND_PROC_END_CARD_SAVED` | `PROC_TRIGGER_RETURN_TO_TITLE` | `0 / 0` | `PROC_NAV_TEARDOWN_GAMEPLAY + PROC_NAV_INVALIDATE_CAMPAIGN_OWNER + PROC_NAV_FENCE_CAMPAIGN_CALLBACKS` |
| `PROC_NAV_END_CARD_CONTINUE_DIRTY` | `SCENE_END_CHAPTER -> SCENE_ANNEX_INTERIOR` | `COND_PROC_END_CARD_DIRTY_RESOLVED` | `PROC_TRIGGER_CONTINUE` | `0 / 0` | `PROC_NAV_REENTER_RUNTIME_CURRENT_LOCATION` |
| `PROC_NAV_END_CARD_RETURN_TO_TITLE_DIRTY` | `SCENE_END_CHAPTER -> SCENE_TITLE` | `COND_PROC_END_CARD_DIRTY_RETURN_CONFIRMED` | `PROC_TRIGGER_RETURN_TO_TITLE` | `0 / 0` | `PROC_NAV_TEARDOWN_GAMEPLAY + PROC_NAV_DISCARD_DIRTY_RUNTIME + PROC_NAV_INVALIDATE_CAMPAIGN_OWNER + PROC_NAV_FENCE_CAMPAIGN_CALLBACKS` |
| `PROC_NAV_GAME_RETURN_TO_TITLE_DIRTY` | `ANY_STABLE_GAMEPLAY -> SCENE_TITLE` | `COND_PROC_STABLE_GAMEPLAY_DIRTY_RETURN_CONFIRMED` | `PROC_TRIGGER_RETURN_TO_TITLE` | `0 / 0` | `PROC_NAV_TEARDOWN_GAMEPLAY + PROC_NAV_DISCARD_DIRTY_RUNTIME + PROC_NAV_INVALIDATE_CAMPAIGN_OWNER + PROC_NAV_FENCE_CAMPAIGN_CALLBACKS` |
| `PROC_NAV_ROLLBACK_FATAL_RETRY` | `PROCESS_UI_OWNER_ROLLBACK_FATAL -> immutable rollback-descriptor source tuple` | `COND_PROC_ROLLBACK_FATAL_RETRY_READY` | `PROC_TRIGGER_RETRY_ROLLBACK_LOAD` | `0 / 0` | `PROC_NAV_RELOAD_ROLLBACK_SOURCE` |
| `PROC_NAV_ROLLBACK_FATAL_RETURN_TO_TITLE_CLEAN` | `PROCESS_UI_OWNER_ROLLBACK_FATAL -> SCENE_TITLE` | `COND_PROC_ROLLBACK_FATAL_RETURN_CLEAN` | `PROC_TRIGGER_RETURN_TO_TITLE` | `0 / 0` | `PROC_NAV_TEARDOWN_GAMEPLAY + PROC_NAV_DISCARD_ROLLBACK_DESCRIPTOR + PROC_NAV_INVALIDATE_CAMPAIGN_OWNER + PROC_NAV_FENCE_CAMPAIGN_CALLBACKS` |
| `PROC_NAV_ROLLBACK_FATAL_RETURN_TO_TITLE_DIRTY` | `PROCESS_UI_OWNER_ROLLBACK_FATAL -> SCENE_TITLE` | `COND_PROC_ROLLBACK_FATAL_DIRTY_RETURN_CONFIRMED` | `PROC_TRIGGER_RETURN_TO_TITLE` | `0 / 0` | `PROC_NAV_TEARDOWN_GAMEPLAY + PROC_NAV_DISCARD_DIRTY_RUNTIME + PROC_NAV_DISCARD_ROLLBACK_DESCRIPTOR + PROC_NAV_INVALIDATE_CAMPAIGN_OWNER + PROC_NAV_FENCE_CAMPAIGN_CALLBACKS` |
| `PROC_NAV_NEW_GAME_ABORT_TO_TITLE` | `PROCESS_UI_OWNER_NEW_GAME_INITIALIZATION_SAVE_FAILURE -> SCENE_TITLE` | `COND_PROC_NEW_GAME_ABORT_READY` | `PROC_TRIGGER_ABORT_NEW_GAME_TO_TITLE` | `0 / 0` | `PROC_NAV_TEARDOWN_GAMEPLAY + PROC_NAV_DISCARD_RUNTIME_DRAFT + PROC_NAV_DISCARD_DIRTY_RUNTIME + PROC_NAV_INVALIDATE_CAMPAIGN_OWNER + PROC_NAV_FENCE_CAMPAIGN_CALLBACKS` |

`PROC_TRIGGER_AUTO` is not a frame-loop default. It is emitted exactly once by
`BootReadyOwner` only when its completed mask is exactly `0x0000007F`: display
mode/safe frame is live; one input poll has established controller state and
cleared all edges; audio heaps/mixer are initialized or a typed silent-safe
result is final; the ROM filesystem is mounted and its required manifests pass;
both journal pages have completed deterministic selection/diagnostics; the
corresponding sanitized `SettingsProfileOwner` has been initialized; and the
Title shell/load closure is staged and validated. The owner also requires
`SCENE_BOOT`, current generations, no campaign/draft, an empty SaveService queue
and callback set, and no transition owner. It then freezes its mask, creates one
`BootReadyToken`, sets `token_emitted=1`, clears input again, and submits the
single AUTO trigger. `PROC_NAV_BOOT_TO_TITLE` still uses the pure constant
condition, but the navigation selector structurally requires that exact current
token and consumes it; no other caller can manufacture AUTO. Each of the seven
bits is legal only with the corresponding nonzero generation stored in the
owner. Completion callbacks must match both `BootReadyOwner.generation` and the
live subsystem generation before they set a bit. Immediately before minting,
the owner revalidates all seven stored generations against the live display,
input, audio/silent-safe, filesystem, journal-selection, settings-profile, and
Title-shell owners. The frozen token copies all seven values, and navigation
acceptance byte-compares them to the frozen owner and revalidates every live
generation before consuming either token or owner. Thus a stale display or
audio callback cannot satisfy readiness merely by leaving its bit set. Missing work,
partial/silent fallback still pending, a loader/settings-generation mismatch,
duplicate token, or any later subsystem callback leaves Boot visible and fails
closed rather than exposing an incompletely initialized Title.

The process condition programs compare exact typed values. New Game requires `PROCESS_ACCEPT_NEW_GAME` plus `RUNTIME_DRAFT_NEW_GAME_ACCEPTED`; opening exit requires `PROCESS_ACCEPT_OPENING_FINISH`, `OPENING_FINALIZER_GENERATION_CURRENT`, and `RUNTIME_DRAFT_OPENING_FINALIZED`; name confirm/cancel require their matching accept token plus `RUNTIME_DRAFT_NAME_CONFIRMED` or an uncommitted draft. Title Continue requires `PROCESS_ACCEPT_TITLE_CONTINUE`, journal semantic class at least `VALID_GENERAL`, no live campaign owner, a zero RuntimeDraftOwner, and SaveService queue/callback quiescence. Its MINT flag allocates a fresh nonzero campaign owner, mirrors the decoded seed, selects PENDING versus SAVED from the verified semantic class, overlays the sanitized Title process profile, and initializes runtime CLEAN only when all eight settings bytes match (otherwise DIRTY) before destination control. Both end-card conditions use the current campaign-matched `FinalSaveOutcomeOwner`, runtime dirty axis, and typed source 24 `CONDITION_SOURCE_RUNTIME_CURRENT_SAVELOC == SAVELOC_ANNEX_ATRIUM_POST_CHAPTER`; they never depend on source 17's boot-loader selection, which is stale by design after live commits. The saved condition requires `FINAL_SAVE_OUTCOME_SAVED + RUNTIME_PROGRESS_CLEAN`; the disjoint dirty condition requires `FINAL_SAVE_OUTCOME_CONTINUE_UNSAVED + RUNTIME_PROGRESS_DIRTY`. Source 24 is produced only by exact coherent `LocationKey` registry resolution and revalidates the Slice-complete facts through `COND_SAVE_SLICE_COMPLETE`; no struct-to-integer comparison exists. Dirty Continue re-enters that in-memory tuple without reading or updating EEPROM and preserves dirty=true for a later manual retry. Dirty Return-to-Title additionally requires `PROCESS_ACCEPT_RETURN_TO_TITLE` and `DIRTY_WARNING_END_CARD_RETURN_ACK`, then destroys the dirty runtime; a later title Continue loads only the older verified page.

The process UI owns the same unsaved-loss warning after dirty Continue enters Annex exploration. `PROC_SOURCE_ANY_STABLE_GAMEPLAY` is a structural source class, not an exploration-only alias: it accepts the retained current Pause snapshot from either stable exploration or the exact generation-current battle command/target boundary that source 21 maps to `CONTROL_STATE_STABLE`; it rejects every other battle phase and every stale owner. The clean gameplay Return row requires that stable scalar and `runtime_dirty=false`. The dirty gameplay Return row requires the same scalar, `runtime_dirty=true`, and a fresh acknowledgement from that warning; it then tears down and discards dirty runtime. Opening the prompt consumes the triggering edge, Cancel leaves dirty play or the frozen battle boundary intact, and acknowledgement is single-use. Thus dirty Continue -> Pause -> Return cannot match the clean row or bypass warning. Every playable-runtime Return-to-Title row carries `PROC_NAV_TEARDOWN_GAMEPLAY`, campaign invalidation, and callback fencing; teardown is idempotent and destroys `GameProgress`, postchapter/process overlays, retained scene/action owners, and any surviving gameplay scope even when rollback-fatal already has no live scene. If a `BattleRuntimeOwner` is live, teardown first advances its generation counter, invalidates and destroys its queues, presenter handles, `BattleState`, battle UI/action bundle, and owner. It does not copy `BattleActor.current_hp` or any other battle field into `PartySlot`, does not create a SaveRequest, and does not serialize a partial battle; Return means abandon that encounter and campaign. Dirty rows additionally carry `PROC_NAV_DISCARD_DIRTY_RUNTIME`; clean rows assert no dirty progress bytes are discarded. Fencing prevents new admission, drains or terminally rejects every request/backend callback of that owner, clears the outcome owner, and only then exposes Title. The New Game abort condition additionally requires `PROCESS_ACCEPT_NEW_GAME_ABORT_TO_TITLE`, `RUNTIME_DRAFT_NAME_CONFIRMED`, the exact failed first request, CONFIRMED plan authority, and its unconsumed accept epoch. All rows use the normal fade/fence/teardown ownership path and clear input edges before the destination accepts control.

Rollback-fatal rows require source class `PROC_SOURCE_PROCESS_UI_OWNER` and exact
retained origin `PROCESS_UI_OWNER_ROLLBACK_FATAL`; no scene source may select
them. Before the ordinary `ConditionDef` is evaluated, the ProcessNavigation
selector structurally requires current owner generation, a valid immutable
rollback descriptor, no live/partial scene scope, and the matching trigger. Those
facts are not falsely attributed to a Condition VM source. The three literal VM
programs then separate actions: `COND_PROC_ROLLBACK_FATAL_RETRY_READY` is true
for either dirty state; `COND_PROC_ROLLBACK_FATAL_RETURN_CLEAN` requires the
Return token plus `runtime_dirty=false`; the dirty condition requires
`runtime_dirty=true`, the Return token emitted from the retained-origin warning,
and `DIRTY_WARNING_ROLLBACK_FATAL_RETURN_ACK`. Retry therefore never discards
dirty progress. A successful Retry atomically enters/validates the descriptor
tuple before releasing the process screen and descriptor. Either Return row
clears the descriptor only after Title construction is guaranteed. Flags accept
only `0x0FFF`; a Return-to-Title row missing both campaign invalidation/fence
bits, a Continue-load row missing MINT, trigger/source/flag disagreement,
missing structural prerequisite, a stale descriptor, or a rollback row selected
from any other retained origin fails closed.

## 14. Instrumentation records

Telemetry is a fixed-capacity ring, never an unbounded logger in gameplay memory.

```c
typedef enum TelemetryEventType {
    TELEM_FRAME_MISS = 1,
    TELEM_HEAP_LOW_WATER,
    TELEM_RESOURCE_LOAD,
    TELEM_RESOURCE_FREE,
    TELEM_TRANSITION_PHASE,
    TELEM_TRANSITION_BASELINE,
    TELEM_SAVE_PHASE,
    TELEM_SAVE_ERROR,
    TELEM_CONTROLLER_LOST,
    TELEM_CONTROLLER_RESTORED,
    TELEM_COLLISION_RECOVERY,
    TELEM_FOLLOWER_RECOVERY,
    TELEM_BATTLE_PHASE,
    TELEM_BATTLE_ACTION,
    TELEM_AUDIO_UNDERRUN,
    TELEM_FATAL
} TelemetryEventType;

typedef struct TelemetryEvent {
    uint32_t frame_number; /* 0 */
    uint32_t game_tick;    /* 4 */
    uint16_t type;         /* 8 */
    uint16_t subject_id;   /* 10 */
    int32_t value;         /* 12 */
} TelemetryEvent;
_Static_assert(sizeof(TelemetryEvent) == 16, "TelemetryEvent layout");

typedef struct FrameMetrics {
    uint32_t frame_number;       /* 0 */
    uint16_t cpu_us;             /* 4 */
    uint16_t rsp_us;             /* 6, 0xFFFF when unavailable */
    uint16_t rdp_us;             /* 8, 0xFFFF when unavailable */
    uint16_t audio_us;           /* 10 */
    uint8_t fixed_steps;         /* 12 */
    uint8_t dropped_ticks;       /* 13 */
    uint16_t flags;              /* 14 */
    uint32_t free_heap_bytes;    /* 16 */
    uint32_t largest_free_block; /* 20 */
    uint32_t scene_arena_used;   /* 24 */
    uint32_t registered_bytes;   /* 28 */
} FrameMetrics;
_Static_assert(sizeof(FrameMetrics) == 32, "FrameMetrics layout");

enum FrameMetricsFlags {
    FRAME_METRIC_30FPS_MISS = 1u << 0,
    FRAME_METRIC_AUDIO_UNDERRUN = 1u << 1,
    FRAME_METRIC_RSP_UNAVAILABLE = 1u << 2,
    FRAME_METRIC_RDP_UNAVAILABLE = 1u << 3,
    FRAME_METRIC_DROPPED_FIXED_TICK = 1u << 4
};
```

`FrameMetrics.flags` accepts only mask `0x001F`; RSP/RDP-unavailable bits require the matching timing field `0xFFFF`, dropped-tick requires `dropped_ticks>0`, and unknown bits fail capture validation. Default debug capacities are 256 telemetry events (4 KiB) and 120 frame records (3.75 KiB). Ring overwrite increments a counter. Certification capture periodically exports/prints records so overwriting does not erase the twenty-transition evidence.

Transition soak records use a 32-byte row containing loop index, source/destination scene+zone, pre-load free/largest block, post-unload free/largest block, destination low water, registered bytes after unload, and fault flags. The report generator binds rows to Git commit, ROM SHA-256, manifest CRC, and dependency pins.

## 15. Codec and validator obligations

### 15.1 Canonical generated-C order and compile proof

Markdown fence order is explanatory and is not a C translation-unit order. There is one generator output contract: `build/generated/schema_all.h` is emitted in this exact topological rank order—(1) fixed-width includes and scalar ID typedefs; (2) every named enum/bit constant, sorted by declared domain then numeric value; (3) pointer-free leaf structs including `GameSettings`, `PartySlot`, and condition AST/compiler records; (4) dependent structs, topologically sorted by by-value field dependencies; (5) `_Static_assert(sizeof/offsetof)` rows immediately after each now-complete type; (6) extern table declarations; (7) `build/generated/schema_all.c` literal table definitions after every referenced enum/type/ID is declared. A dependency cycle, anonymous ID-domain enum, duplicate numeric value inside a declared ID domain, unresolved array token, or required forward value declaration is a generation failure; the generator never repairs it by guessing markdown order or synthesizing a magic integer.

`build/generated/schema_aggregate_compile.c` contains only `#include "schema_all.h"` plus generated references to every literal table/count. Gate 2 runs `cc -std=c11 -Wall -Wextra -Werror -pedantic -c schema_all.c schema_aggregate_compile.c`; Gate 3 and every later build additionally run the same canonical units through the pinned N64 compiler with warnings-as-errors. This preserves the ordered gate boundary: preproduction proves the host-generated contract before toolchain installation, then Gate 3 makes target-compiler parity mandatory. The host proof must cover every named enum domain, every documented layout/static assert, every literal array initializer, all reserved-zero/count/range checks, and the global ID/string collision audit; its machine-readable report records those counts and SHA-256 values for `schema_all.h`, `schema_all.c`, and `schema_aggregate_compile.c`. Concatenating raw Markdown C fences is explicitly not an accepted build path. A document change that passes prose checks but cannot reproduce and compile these canonical files fails Gate 2.

The gate boundary is explicit: Gate 2 compiles the typed fenced enums, layouts,
and literal C arrays above while also parsing every ordinary Markdown table into
a lossless UTF-8 row/cell/heading contract with per-table SHA-256 evidence. That
lossless blob proves no table row disappeared or changed invisibly; it does not
pretend prose tables are already runtime C. Gate 3 must typed-lower every
Markdown-backed registry into its declared runtime structs, apply the named
table-specific semantic validator, byte-compare generated rows to independent
goldens, and compile those concrete outputs with the pinned N64 compiler. A raw
Markdown blob is never linked into the ROM as a substitute for typed lowering.

The implementation is incomplete until automated tests prove these schema obligations:

- `_Static_assert` checks for every logical runtime structure listed here on host and N64 compilers.
- Byte-exact golden files for manifest v2 headers/entries/load references, cutscene events, effect instructions, and EEPROM v1.
- Round-trip property tests where decode(encode(value)) preserves every defined field and writes every reserved byte as zero.
- Bounds/fuzz tests reject short buffers, invalid counts, integer overflow, bad IDs, bad CRC, bad endianness, and table overlap without reading out of bounds.
- Save tests independently corrupt every header, payload, CRC, marker, and semantic invariant on both pages; invalid/incompatible progression preserves raw pages while only eight validated/clamped settings bytes are salvageable.
- Battle tests prove conditional same-side retarget/no-op behavior, the five exact damage vectors, lane-independent Horizon linked-Power rounding, the priority-visible Rusk round-one/Dazzle stream, effect-bytecode validation, documented RNG stream/call order, no-RNG stable AI ties, Dazzle/Static threshold draws, always-status draw behavior, Staggered applied before a pending action and after the actor already acted, KO/cleanse/retry clearing, early/late stage duration and Speed re-sort, cooldown/once-use state, Guiding Draft one-use timing, exact AI score/clamp/defensive-cap vectors, player-only Resonance source/dedup/setup-record awards and carried-meter tutorial paths, finisher cancellation/reselection, duo prerequisites/consumption, 64-event worst-case high water/overflow assertion, knockout, and reward idempotence.
- Story tests traverse all mandatory flags/objectives in canonical order, then repeat every completed interaction and confirm no duplicate grants or scene triggers.
- Asset validation resolves every character/creature animation-set requirement, validates the one-bone-per-exported-vertex Tiny3D constraint, rejects dependency cycles/orphans/multiple pack owners, deduplicates shared AssetIds, and enforces packed/unpacked/arena, zone-composite, and complete-ROM caps before assembly.
- Transition validation proves every saved location and destination tuple exists and has a safe recovery tuple; UI end card is non-saveable; destination failure normally reloads source unchanged; the simulation base-retain flag accepts exact AssetId/CRC/size identity only, atomically retags generation, invalidates overlay handles, and retains nothing else.

Any format change increments the appropriate schema version, adds a decoder/migrator or explicit incompatibility behavior, updates golden vectors, and documents whether shipped numeric IDs remain stable. Changing a C struct without changing serialized field codecs is harmless; casting that struct to serialized bytes is always a defect.
