#include "n64game_render.h"

#include <stddef.h>
#include <stdio.h>

enum {
    FONT_ID = 1,
    STYLE_TEXT = 0,
    STYLE_ACCENT = 1,
    STYLE_MUTED = 2,
    STYLE_WARNING = 3,
    STYLE_SELECTED = 4,
    ACTOR_STYLE_COUNT = 8,
    ACTOR_MATRIX_COUNT = 5,
};

static const uint32_t ACTOR_COLORS[ACTOR_STYLE_COUNT] = {
    UINT32_C(0xD7A253FF),
    UINT32_C(0x79C9D4FF),
    UINT32_C(0x3AA6A0FF),
    UINT32_C(0xD45E49FF),
    UINT32_C(0xE4C49AFF),
    UINT32_C(0x5DDDC6FF),
    UINT32_C(0xA36BD1FF),
    UINT32_C(0xC88B4AFF),
};

static void text_at(float x, float y, uint8_t style, float width, const char *text)
{
    const rdpq_textparms_t parameters = {
        .style_id = style,
        .width = (int16_t)width,
        .height = (int16_t)(240.0f - y),
        .align = ALIGN_LEFT,
        .valign = VALIGN_TOP,
        .wrap = WRAP_WORD,
    };
    rdpq_text_print(&parameters, FONT_ID, x, y, text);
}

static void centered(float y, uint8_t style, const char *text)
{
    const rdpq_textparms_t parameters = {
        .style_id = style,
        .width = 320.0f,
        .align = ALIGN_CENTER,
        .valign = VALIGN_TOP,
    };
    rdpq_text_print(&parameters, FONT_ID, 0.0f, y, text);
}

static void fill_rect(int x0, int y0, int x1, int y1, color_t color)
{
    rdpq_set_mode_fill(color);
    rdpq_fill_rectangle(x0, y0, x1, y1);
}

static void panel(int x0, int y0, int x1, int y1)
{
    fill_rect(x0, y0, x1, y1, RGBA32(7, 18, 27, 255));
    fill_rect(x0, y0, x1, y0 + 2, RGBA32(78, 210, 190, 255));
    fill_rect(x0, y1 - 2, x1, y1, RGBA32(29, 67, 76, 255));
}

static void clear_2d(color_t color)
{
    fill_rect(0, 0, 320, 240, color);
}

static void fade_to_black(uint8_t alpha)
{
    if (alpha == 0U) {
        return;
    }
    rdpq_set_mode_standard();
    rdpq_mode_combiner(RDPQ_COMBINER_FLAT);
    rdpq_mode_blender(RDPQ_BLENDER_MULTIPLY);
    rdpq_set_prim_color(RGBA32(0, 0, 0, alpha));
    rdpq_fill_rectangle(0, 0, 320, 240);
}

static void hp_bar(int x, int y, int width, int hp, int maximum)
{
    const int safe_hp = hp < 0 ? 0 : hp;
    const int fill = maximum > 0 ? width * safe_hp / maximum : 0;
    fill_rect(x, y, x + width, y + 5, RGBA32(31, 45, 50, 255));
    const color_t color = safe_hp * 4 > maximum ?
        RGBA32(81, 211, 166, 255) : RGBA32(218, 93, 70, 255);
    fill_rect(x, y, x + fill, y + 5, color);
}

static void setup_actor_vertices(N64GameRenderer *renderer)
{
    const uint16_t top = t3d_vert_pack_normal(&(fm_vec3_t){{0.0f, 1.0f, 0.0f}});
    const uint16_t left = t3d_vert_pack_normal(&(fm_vec3_t){{-0.7f, -0.4f, 0.6f}});
    const uint16_t right = t3d_vert_pack_normal(&(fm_vec3_t){{0.7f, -0.4f, 0.6f}});
    const uint16_t back = t3d_vert_pack_normal(&(fm_vec3_t){{0.0f, -0.4f, -0.9f}});
    for (size_t style = 0U; style < ACTOR_STYLE_COUNT; ++style) {
        const uint32_t color = ACTOR_COLORS[style];
        renderer->actor_vertices[style * 2U] = (T3DVertPacked){
            .posA = {0, 22, 0}, .rgbaA = color, .normA = top,
            .posB = {-14, -16, 12}, .rgbaB = color, .normB = left,
        };
        renderer->actor_vertices[style * 2U + 1U] = (T3DVertPacked){
            .posA = {14, -16, 12}, .rgbaA = color, .normA = right,
            .posB = {0, -16, -16}, .rgbaB = color, .normB = back,
        };
    }
}

bool n64game_renderer_init(N64GameRenderer *renderer)
{
    if (renderer == NULL) {
        return false;
    }
    *renderer = (N64GameRenderer){0};
    renderer->font = rdpq_font_load_builtin(FONT_BUILTIN_DEBUG_MONO);
    if (renderer->font == NULL) {
        return false;
    }
    rdpq_font_style(renderer->font, STYLE_TEXT, &(rdpq_fontstyle_t){
        .color = RGBA32(232, 224, 202, 255),
        .outline_color = RGBA32(4, 10, 16, 255),
    });
    rdpq_font_style(renderer->font, STYLE_ACCENT, &(rdpq_fontstyle_t){
        .color = RGBA32(87, 226, 203, 255),
        .outline_color = RGBA32(4, 10, 16, 255),
    });
    rdpq_font_style(renderer->font, STYLE_MUTED, &(rdpq_fontstyle_t){
        .color = RGBA32(139, 155, 157, 255),
        .outline_color = RGBA32(4, 10, 16, 255),
    });
    rdpq_font_style(renderer->font, STYLE_WARNING, &(rdpq_fontstyle_t){
        .color = RGBA32(221, 97, 163, 255),
        .outline_color = RGBA32(4, 10, 16, 255),
    });
    rdpq_font_style(renderer->font, STYLE_SELECTED, &(rdpq_fontstyle_t){
        .color = RGBA32(12, 24, 31, 255),
        .outline_color = RGBA32(87, 226, 203, 255),
    });
    rdpq_text_register_font(FONT_ID, renderer->font);

    renderer->floor_vertices = malloc_uncached(sizeof(T3DVertPacked) * 2U);
    renderer->actor_vertices = malloc_uncached(
        sizeof(T3DVertPacked) * 2U * ACTOR_STYLE_COUNT
    );
    renderer->buffer_count = display_get_num_buffers();
    if (renderer->buffer_count == 0U || renderer->buffer_count > UINT16_MAX) {
        return false;
    }
    renderer->actor_matrices = malloc_uncached(
        sizeof(T3DMat4FP) * ACTOR_MATRIX_COUNT * (size_t)renderer->buffer_count
    );
    if (renderer->floor_vertices == NULL || renderer->actor_vertices == NULL ||
        renderer->actor_matrices == NULL) {
        return false;
    }
    const uint16_t up = t3d_vert_pack_normal(&(fm_vec3_t){{0.0f, 1.0f, 0.0f}});
    renderer->floor_vertices[0] = (T3DVertPacked){
        .posA = {-100, -18, -76}, .rgbaA = UINT32_C(0x5D4937FF), .normA = up,
        .posB = {100, -18, -76}, .rgbaB = UINT32_C(0x815D3EFF), .normB = up,
    };
    renderer->floor_vertices[1] = (T3DVertPacked){
        .posA = {100, -18, 76}, .rgbaA = UINT32_C(0x294B50FF), .normA = up,
        .posB = {-100, -18, 76}, .rgbaB = UINT32_C(0x3A5551FF), .normB = up,
    };
    setup_actor_vertices(renderer);
    renderer->viewport = t3d_viewport_create_buffered((uint16_t)renderer->buffer_count);
    return true;
}

static void draw_floor(const N64GameRenderer *renderer)
{
    t3d_vert_load(renderer->floor_vertices, 0, 4);
    t3d_tri_draw(0, 1, 2);
    t3d_tri_draw(0, 2, 3);
    t3d_tri_sync();
}

static void draw_actor(
    N64GameRenderer *renderer,
    size_t matrix_index,
    size_t style,
    float x,
    float y,
    float z,
    float scale,
    float angle
)
{
    const float scales[3] = {scale, scale, scale};
    const float rotations[3] = {0.0f, angle, 0.0f};
    const float translation[3] = {x, y, z};
    const size_t matrix_slot = matrix_index * (size_t)renderer->buffer_count +
        (size_t)renderer->frame_index;
    t3d_mat4fp_from_srt_euler(
        &renderer->actor_matrices[matrix_slot], scales, rotations, translation
    );
    t3d_matrix_push(&renderer->actor_matrices[matrix_slot]);
    t3d_vert_load(&renderer->actor_vertices[style * 2U], 0, 4);
    t3d_matrix_pop(1);
    t3d_tri_draw(0, 1, 2);
    t3d_tri_draw(0, 3, 1);
    t3d_tri_draw(0, 2, 3);
    t3d_tri_draw(1, 3, 2);
    t3d_tri_sync();
}

static void begin_world_render(
    N64GameRenderer *renderer,
    const fm_vec3_t *camera,
    const fm_vec3_t *target
)
{
    const fm_vec3_t up = {{0.0f, 1.0f, 0.0f}};
    const uint8_t ambient[4] = {54, 48, 57, 255};
    const uint8_t sun[4] = {255, 224, 177, 255};
    const fm_vec3_t direction = {{-0.45f, 0.72f, 0.6f}};
    renderer->frame_index = (renderer->frame_index + 1U) % renderer->buffer_count;
    t3d_frame_start();
    t3d_viewport_set_projection(&renderer->viewport, T3D_DEG_TO_RAD(68.0f), 8.0f, 300.0f);
    t3d_viewport_look_at(&renderer->viewport, camera, target, &up);
    t3d_viewport_attach(&renderer->viewport);
    t3d_screen_clear_color(RGBA32(19, 31, 42, 255));
    t3d_screen_clear_depth();
    rdpq_mode_combiner(RDPQ_COMBINER_SHADE);
    t3d_light_set_ambient(ambient);
    t3d_light_set_directional(0, sun, &direction);
    t3d_light_set_count(1);
    t3d_state_set_drawflags(T3D_FLAG_SHADED | T3D_FLAG_DEPTH);
    draw_floor(renderer);
}

static const char *objective_text(N64GameQuest quest)
{
    switch (quest) {
    case N64GAME_QUEST_MEET_SERA: return "MEET DR. SERA VENN";
    case N64GAME_QUEST_RETRIEVE_RELAY: return "RETRIEVE THE FIELD RELAY";
    case N64GAME_QUEST_RETURN_TO_SERA: return "RETURN TO SERA";
    case N64GAME_QUEST_RESONANCE_TRIAL: return "COMPLETE THE RESONANCE TRIAL";
    case N64GAME_QUEST_BEACON_OVERLOOK: return "TRACE THE SIGNAL AT THE OVERLOOK";
    case N64GAME_QUEST_COMPLETE: return "OPENING CHAPTER COMPLETE";
    }
    return "";
}

static const char *dialogue_speaker(N64GameDialogue dialogue)
{
    switch (dialogue) {
    case N64GAME_DIALOGUE_SERA_INTRO:
    case N64GAME_DIALOGUE_SERA_TRIAL:
    case N64GAME_DIALOGUE_BATTLE_VICTORY:
    case N64GAME_DIALOGUE_BEACON_HOOK:
        return "DR. SERA VENN";
    case N64GAME_DIALOGUE_TAVI_OPTIONAL:
        return "TAVI";
    case N64GAME_DIALOGUE_RELAY:
        return "FIELD RELAY";
    case N64GAME_DIALOGUE_NONE:
        return "";
    }
    return "";
}

static const char *dialogue_text(const N64GameCore *game)
{
    static const char *const SERA_INTRO[] = {
        "The Annex heard your Resonance before you reached the floor.",
        "Quarrune and Ayselor are already matching your rhythm.",
        "Bring the Field Relay from the east bench. We will calibrate together.",
    };
    static const char *const RELAY[] = {
        "MERIDIAN FIELD RELAY / LINK ESTABLISHED",
        "PARTY, MESSAGES, RESONANCE, AND SAVE CHANNELS ARE READY.",
    };
    static const char *const SERA_TRIAL[] = {
        "Good. The Relay needs one live pattern before it can hear the desert.",
        "Take your pair into the chamber. Let the true pattern answer.",
    };
    static const char *const TAVI[] = {
        "The west antenna keeps pointing at empty sky.",
        "Sera says instruments do not get nervous. I think this one does.",
    };
    static const char *const VICTORY[] = {
        "There. Quarrune anchors; Ayselor carries. The Relay understands you now.",
        "A signal just crossed the old Solace band. Meet me at the overlook.",
    };
    static const char *const BEACON[] = {
        "That signature belongs to Solace.",
        "It vanished three nights ago. This beacon should not be moving.",
        "Something enormous is answering from beneath the storm.",
        "We follow at first light.",
    };
    const uint8_t page = game->dialogue_page;
    switch (game->dialogue) {
    case N64GAME_DIALOGUE_SERA_INTRO: return SERA_INTRO[page];
    case N64GAME_DIALOGUE_RELAY: return RELAY[page];
    case N64GAME_DIALOGUE_SERA_TRIAL: return SERA_TRIAL[page];
    case N64GAME_DIALOGUE_TAVI_OPTIONAL: return TAVI[page];
    case N64GAME_DIALOGUE_BATTLE_VICTORY: return VICTORY[page];
    case N64GAME_DIALOGUE_BEACON_HOOK: return BEACON[page];
    case N64GAME_DIALOGUE_NONE: return "";
    }
    return "";
}

static void draw_dialogue(const N64GameCore *game)
{
    panel(8, 172, 312, 234);
    text_at(18.0f, 179.0f, STYLE_ACCENT, 280.0f, dialogue_speaker(game->dialogue));
    text_at(18.0f, 193.0f, STYLE_TEXT, 276.0f, dialogue_text(game));
    text_at(286.0f, 219.0f, STYLE_MUTED, 20.0f, "A");
}

static void draw_annex(N64GameRenderer *renderer, const N64GameCore *game)
{
    const float player_x = (float)game->player_x_q8 / 256.0f;
    const float player_z = (float)game->player_z_q8 / 256.0f;
    const fm_vec3_t camera = {{player_x, 62.0f, player_z - 88.0f}};
    const fm_vec3_t target = {{player_x, -4.0f, player_z + 6.0f}};
    begin_world_render(renderer, &camera, &target);
    const float angle = (float)game->scene_ticks * 0.018f;
    draw_actor(renderer, 0U, 4U, player_x, -1.0f, player_z, 0.75f, angle);
    draw_actor(renderer, 1U, 5U, -38.0f, -1.0f, -8.0f, 0.88f, 0.3f);
    draw_actor(renderer, 2U, 7U, 5.0f, -2.0f, -34.0f, 0.68f, -0.4f);
    draw_actor(renderer, 3U, 6U, 34.0f, -3.0f, 20.0f, 0.55f, angle * 1.7f);
    draw_actor(renderer, 4U, 6U, 74.0f, -6.0f, 40.0f, 0.72f, -angle);

    panel(8, 8, 250, 31);
    text_at(16.0f, 15.0f, STYLE_ACCENT, 228.0f, objective_text(game->quest));
    const char *const prompt = n64game_core_interaction_label(game);
    if (prompt != NULL) {
        panel(74, 142, 246, 164);
        text_at(84.0f, 149.0f, STYLE_TEXT, 156.0f, prompt);
    }
    if (game->paused) {
        panel(72, 70, 248, 146);
        centered(79.0f, STYLE_ACCENT, "FIELD RELAY");
        text_at(92.0f, 99.0f, STYLE_TEXT, 140.0f, "PARTY\nMESSAGES\nSAVE\nRESUME  START");
    } else if (game->dialogue != N64GAME_DIALOGUE_NONE) {
        draw_dialogue(game);
    }
}

static const char *echo_name(uint8_t actor)
{
    static const char *const NAMES[] = {"QUARRUNE", "AYSELOR", "GYRECLAST", "KIVARRAX"};
    return actor < 4U ? NAMES[actor] : "";
}

static void draw_battle_status(const N64GameCore *game)
{
    const N64GameBattle *const battle = &game->battle;
    for (uint8_t actor = 0U; actor < 4U; ++actor) {
        const bool player = actor < 2U;
        const int x = player ? 8 + (int)actor * 112 : 96 + ((int)actor - 2) * 108;
        const int y = player ? 112 : 8;
        panel(x, y, x + 104, y + 29);
        text_at((float)(x + 5), (float)(y + 5), STYLE_TEXT, 94.0f, echo_name(actor));
        hp_bar(x + 5, y + 18, 92, battle->actors[actor].hp, battle->actors[actor].max_hp);
        if (game->battle_selecting_target && game->battle_target_cursor == actor) {
            fill_rect(x, y, x + 4, y + 29, RGBA32(221, 97, 163, 255));
        }
    }
}

static void draw_battle_menu(const N64GameCore *game)
{
    const N64GameBattle *const battle = &game->battle;
    panel(8, 146, 178, 234);
    if (battle->phase == N64GAME_BATTLE_COMMAND) {
        const uint8_t actor = battle->command_actor;
        text_at(16.0f, 153.0f, STYLE_ACCENT, 150.0f, echo_name(actor));
        for (uint8_t move = 0U; move < 4U; ++move) {
            const N64GameMoveDef *const definition = n64game_move_def(
                battle->actors[actor].id, move
            );
            const uint8_t style = !game->battle_selecting_target &&
                game->battle_move_cursor == move ? STYLE_WARNING : STYLE_TEXT;
            text_at(18.0f, 168.0f + (float)move * 13.0f, style, 150.0f, definition->name);
        }
        if (actor == 0U && battle->resonance == N64GAME_RESONANCE_MAX &&
            battle->actors[1].hp > 0) {
            const uint8_t style = game->battle_move_cursor == N64GAME_MOVE_FINISHER ?
                STYLE_WARNING : STYLE_ACCENT;
            text_at(18.0f, 220.0f, style, 150.0f, "HORIZON BREAK");
        }
    } else if (battle->phase == N64GAME_BATTLE_VICTORY) {
        text_at(18.0f, 158.0f, STYLE_ACCENT, 150.0f, "RESONANCE STABLE");
        text_at(18.0f, 181.0f, STYLE_TEXT, 150.0f, "TRIAL COMPLETE\nA  CONTINUE");
    } else if (battle->phase == N64GAME_BATTLE_DEFEAT) {
        text_at(18.0f, 158.0f, STYLE_WARNING, 150.0f, "PATTERN LOST");
        text_at(18.0f, 181.0f, STYLE_TEXT, 150.0f, "A  RETRY\nB  RETURN");
    } else {
        const N64GameBattleEvent *const event = &battle->last_event;
        if (event->happened) {
            char message[96];
            if (event->skipped) {
                (void)snprintf(message, sizeof(message), "%s CANNOT ACT", echo_name(event->actor));
            } else if (event->move == N64GAME_MOVE_FINISHER) {
                (void)snprintf(message, sizeof(message), "HORIZON BREAK");
            } else {
                const N64GameMoveDef *const move = n64game_move_def(
                    battle->actors[event->actor].id, event->move
                );
                (void)snprintf(message, sizeof(message), "%s / %s",
                               echo_name(event->actor), move != NULL ? move->name : "ACTION");
            }
            text_at(18.0f, 158.0f, STYLE_ACCENT, 150.0f, message);
            if (event->affinity_advantage) {
                text_at(18.0f, 184.0f, STYLE_WARNING, 150.0f, "AFFINITY ADVANTAGE");
            }
        } else {
            text_at(18.0f, 158.0f, STYLE_MUTED, 150.0f, "BUILDING TURN QUEUE");
        }
    }

    panel(184, 146, 312, 180);
    text_at(192.0f, 153.0f, STYLE_ACCENT, 110.0f, "RESONANCE");
    hp_bar(192, 168, 110, battle->resonance, N64GAME_RESONANCE_MAX);
    panel(184, 186, 312, 234);
    if (game->battle_selecting_target) {
        text_at(192.0f, 194.0f, STYLE_WARNING, 110.0f, "SELECT TARGET");
        text_at(192.0f, 214.0f, STYLE_MUTED, 110.0f, "A CONFIRM / B BACK");
    } else {
        text_at(192.0f, 194.0f, STYLE_TEXT, 110.0f, "D-PAD  MOVE\nA  CHOOSE\nB  BACK");
    }
}

static void draw_battle(N64GameRenderer *renderer, const N64GameCore *game)
{
    const fm_vec3_t camera = {{0.0f, 56.0f, -112.0f}};
    const fm_vec3_t target = {{0.0f, -4.0f, 0.0f}};
    begin_world_render(renderer, &camera, &target);
    static const float POSITIONS[4][3] = {
        {-31.0f, -2.0f, -17.0f}, {26.0f, 0.0f, -8.0f},
        {-28.0f, -2.0f, 27.0f}, {31.0f, -1.0f, 22.0f},
    };
    const float angle = (float)game->scene_ticks * 0.012f;
    for (uint8_t actor = 0U; actor < 4U; ++actor) {
        if (game->battle.actors[actor].hp > 0) {
            draw_actor(renderer, actor, actor,
                       POSITIONS[actor][0], POSITIONS[actor][1], POSITIONS[actor][2],
                       0.82f, actor < 2U ? angle : -angle);
        }
    }
    draw_battle_status(game);
    draw_battle_menu(game);
}

static void draw_name_entry(const N64GameCore *game)
{
    clear_2d(RGBA32(10, 25, 35, 255));
    centered(18.0f, STYLE_ACCENT, "RESONANCE IDENTITY");
    panel(56, 42, 264, 72);
    centered(51.0f, STYLE_TEXT, game->name_length > 0U ? game->player_name : "ARI");
    for (uint8_t slot = 0U; slot < 28U; ++slot) {
        const int column = slot % 7U;
        const int row = slot / 7U;
        const float x = 41.0f + (float)column * 36.0f;
        const float y = 92.0f + (float)row * 27.0f;
        char label[5] = {0};
        if (slot < 26U) {
            label[0] = (char)('A' + slot);
        } else if (slot == 26U) {
            (void)snprintf(label, sizeof(label), "DEL");
        } else {
            (void)snprintf(label, sizeof(label), "OK");
        }
        text_at(x, y, game->name_cursor == slot ? STYLE_WARNING : STYLE_TEXT, 32.0f, label);
    }
    centered(214.0f, STYLE_MUTED, "D-PAD SELECT / A ENTER / B ERASE");
}

static void draw_opening(const N64GameCore *game, bool continue_available)
{
    clear_2d(RGBA32(6, 15, 24, 255));
    if (game->scene == N64GAME_SCENE_BOOT) {
        centered(72.0f, STYLE_ACCENT, "N64GAME");
        centered(96.0f, STYLE_TEXT, "MERIDIAN SIGNAL LAB");
        const int width = (int)(game->scene_ticks % 31U) * 6;
        fill_rect(68, 132, 252, 136, RGBA32(24, 51, 60, 255));
        fill_rect(68, 132, 68 + width, 136, RGBA32(87, 226, 203, 255));
        centered(150.0f, STYLE_MUTED, "CALIBRATING RESONANCE");
    } else {
        fill_rect(18, 18, 302, 222, RGBA32(22, 32, 44, 255));
        fill_rect(18, 18, 302, 22, RGBA32(183, 72, 154, 255));
        centered(84.0f, STYLE_WARNING, "INSERT CUTSCENE HERE");
        centered(110.0f, STYLE_TEXT, "SOLACE INTERCEPTION / 4:3 PLAYBACK SLOT");
        centered(
            178.0f,
            STYLE_MUTED,
            continue_available ? "START CONTINUE / A NEW FILE" : "A OR START TO BEGIN"
        );
        uint8_t fade_alpha = 0U;
        if (game->scene_ticks < 8U) {
            fade_alpha = (uint8_t)(
                UINT32_C(255) - game->scene_ticks * UINT32_C(255) / UINT32_C(8)
            );
        } else if (game->scene_ticks >= 98U) {
            const uint32_t fade_tick = game->scene_ticks - UINT32_C(97);
            fade_alpha = (uint8_t)(fade_tick * UINT32_C(255) / UINT32_C(8));
        }
        fade_to_black(fade_alpha);
    }
}

static void draw_ending(const N64GameCore *game, bool save_busy, bool save_available)
{
    clear_2d(RGBA32(7, 13, 24, 255));
    fill_rect(0, 0, 320, 8, RGBA32(170, 61, 145, 255));
    centered(54.0f, STYLE_WARNING, "SIGNAL ACQUIRED");
    centered(80.0f, STYLE_ACCENT, "SOLACE / EMERGENCY BEACON");
    centered(119.0f, STYLE_TEXT, "END OF OPENING CHAPTER");
    char player_line[40];
    const char *const save_state = save_busy ? "FINALIZING SAVE" :
        (save_available ? "RESONANCE FILE SAVED" : "PROGRESS VOLATILE");
    (void)snprintf(player_line, sizeof(player_line), "%s / %s",
                   game->player_name, save_state);
    centered(151.0f, STYLE_MUTED, player_line);
    centered(196.0f, STYLE_TEXT, "THE STORM IS ANSWERING.");
}

void n64game_renderer_draw(
    N64GameRenderer *renderer,
    const N64GameCore *game,
    bool save_busy,
    bool save_available,
    bool continue_available,
    bool controller_connected
)
{
    if (renderer == NULL || game == NULL) {
        return;
    }
    rdpq_attach(display_get(), display_get_zbuf());
    switch (game->scene) {
    case N64GAME_SCENE_BOOT:
    case N64GAME_SCENE_OPENING_SLATE:
        draw_opening(game, continue_available);
        break;
    case N64GAME_SCENE_NAME_ENTRY:
        draw_name_entry(game);
        break;
    case N64GAME_SCENE_ANNEX:
        draw_annex(renderer, game);
        break;
    case N64GAME_SCENE_BATTLE:
        draw_battle(renderer, game);
        break;
    case N64GAME_SCENE_END_CHAPTER:
        draw_ending(game, save_busy, save_available);
        break;
    }
    if (save_busy) {
        panel(238, 214, 314, 234);
        text_at(246.0f, 221.0f, STYLE_ACCENT, 62.0f, "SAVING");
    } else if (!save_available) {
        text_at(218.0f, 224.0f, STYLE_WARNING, 96.0f, "SAVE UNAVAILABLE");
    }
    if (!controller_connected) {
        panel(42, 91, 278, 149);
        centered(104.0f, STYLE_WARNING, "CONTROLLER DISCONNECTED");
        centered(126.0f, STYLE_TEXT, "RECONNECT CONTROLLER 1");
    }
    rdpq_detach_show();
}
