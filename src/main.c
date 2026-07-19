// SPDX-License-Identifier: MIT
// Gate 3 diagnostic scene. This is original project code, not production art.

#include <libdragon.h>
#include <t3d/t3d.h>

#define FONT_ID 1

static void draw_centered_text(float y, uint8_t style, const char *text)
{
    const rdpq_textparms_t parms = {
        .style_id = style,
        .width = 320,
        .align = ALIGN_CENTER,
        .valign = VALIGN_TOP,
    };
    rdpq_text_print(&parms, FONT_ID, 0.0f, y, text);
}

int main(void)
{
    debug_init_emulog();
    debug_init_usblog();

    display_init(
        RESOLUTION_320x240,
        DEPTH_16_BPP,
        3,
        GAMMA_NONE,
        FILTERS_RESAMPLE_ANTIALIAS_DEDITHER
    );
    display_set_fps_limit(30.0f);
    rdpq_init();
    joypad_init();
    t3d_init((T3DInitParams){});

    rdpq_font_t *font = rdpq_font_load_builtin(FONT_BUILTIN_DEBUG_MONO);
    rdpq_font_style(font, 0, &(rdpq_fontstyle_t){
        .color = RGBA32(221, 236, 242, 255),
        .outline_color = RGBA32(5, 10, 18, 255),
    });
    rdpq_font_style(font, 1, &(rdpq_fontstyle_t){
        .color = RGBA32(83, 226, 208, 255),
        .outline_color = RGBA32(5, 10, 18, 255),
    });
    rdpq_text_register_font(FONT_ID, font);

    T3DMat4FP *model_matrix_fp = malloc_uncached(sizeof(T3DMat4FP));
    T3DVertPacked *vertices = malloc_uncached(sizeof(T3DVertPacked) * 2);
    assertf(model_matrix_fp && vertices, "Gate 3 diagnostic allocation failed");

    const uint16_t normal_top = t3d_vert_pack_normal(&(fm_vec3_t){{0.0f, 1.0f, 0.0f}});
    const uint16_t normal_left = t3d_vert_pack_normal(&(fm_vec3_t){{-0.7f, -0.4f, 0.6f}});
    const uint16_t normal_right = t3d_vert_pack_normal(&(fm_vec3_t){{0.7f, -0.4f, 0.6f}});
    const uint16_t normal_back = t3d_vert_pack_normal(&(fm_vec3_t){{0.0f, -0.4f, -0.9f}});

    vertices[0] = (T3DVertPacked){
        .posA = {0, 28, 0},
        .rgbaA = 0x53E2D0FF,
        .normA = normal_top,
        .posB = {-22, -16, 18},
        .rgbaB = 0x4267B2FF,
        .normB = normal_left,
    };
    vertices[1] = (T3DVertPacked){
        .posA = {22, -16, 18},
        .rgbaA = 0xEAB464FF,
        .normA = normal_right,
        .posB = {0, -16, -24},
        .rgbaB = 0x7655A6FF,
        .normB = normal_back,
    };

    const fm_vec3_t camera_position = {{0.0f, 7.0f, -82.0f}};
    const fm_vec3_t camera_target = {{0.0f, 0.0f, 0.0f}};
    const fm_vec3_t camera_up = {{0.0f, 1.0f, 0.0f}};
    fm_vec3_t rotation_axis = {{0.35f, 1.0f, 0.2f}};
    const fm_vec3_t model_scale = {{0.72f, 0.72f, 0.72f}};
    const uint8_t ambient[4] = {44, 55, 72, 255};
    const uint8_t directional[4] = {255, 240, 214, 255};
    const fm_vec3_t light_direction = {{-0.35f, 0.65f, 1.0f}};
    fm_vec3_norm(&rotation_axis, &rotation_axis);

    T3DViewport viewport = t3d_viewport_create();
    rspq_block_t *geometry_block = NULL;
    float angle = 0.0f;
    bool pulse = false;

    for (;;) {
        joypad_poll();
        const joypad_buttons_t pressed = joypad_get_buttons_pressed(JOYPAD_PORT_1);
        if (pressed.a) {
            pulse = !pulse;
        }

        angle += pulse ? 0.052f : 0.026f;
        fm_mat4_t model_matrix;
        fm_mat4_identity(&model_matrix);
        fm_mat4_from_axis_angle(&model_matrix, &rotation_axis, angle);
        fm_mat4_scale(&model_matrix, &model_scale);
        t3d_mat4_to_fixed(model_matrix_fp, &model_matrix);

        t3d_viewport_set_projection(&viewport, T3D_DEG_TO_RAD(72.0f), 8.0f, 140.0f);
        t3d_viewport_look_at(&viewport, &camera_position, &camera_target, &camera_up);

        rdpq_attach(display_get(), display_get_zbuf());
        t3d_frame_start();
        t3d_viewport_attach(&viewport);
        t3d_screen_clear_color(RGBA32(6, 11, 20, 255));
        t3d_screen_clear_depth();
        rdpq_mode_combiner(RDPQ_COMBINER_SHADE);
        t3d_light_set_ambient(ambient);
        t3d_light_set_directional(0, directional, &light_direction);
        t3d_light_set_count(1);
        t3d_state_set_drawflags(T3D_FLAG_SHADED | T3D_FLAG_DEPTH);

        if (!geometry_block) {
            rspq_block_begin();
            t3d_matrix_push(model_matrix_fp);
            t3d_vert_load(vertices, 0, 4);
            t3d_matrix_pop(1);
            t3d_tri_draw(0, 1, 2);
            t3d_tri_draw(0, 3, 1);
            t3d_tri_draw(0, 2, 3);
            t3d_tri_draw(1, 3, 2);
            t3d_tri_sync();
            geometry_block = rspq_block_end();
        }
        rspq_block_run(geometry_block);

        draw_centered_text(18.0f, 1, "N64GAME");
        draw_centered_text(36.0f, 0, "PINNED TINY3D TOOLCHAIN PROOF");
        draw_centered_text(210.0f, 0, pulse ? "A  PULSE: ON" : "A  PULSE: OFF");
        rdpq_detach_show();
    }
}
