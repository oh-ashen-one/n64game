V ?= 1
SOURCE_DIR := src
BUILD_DIR := build/game
T3D_ROOT := $(CURDIR)/build/deps/tiny3d
ROM_NAME := n64game-gate3
ROM_OUTPUT := $(BUILD_DIR)/$(ROM_NAME).z64
QUARRUNE_SOURCE_DIR := runtime-candidates/echo/echo.quarrune
QUARRUNE_FILESYSTEM_DIR := filesystem/echo/echo.quarrune
QUARRUNE_MODEL := $(QUARRUNE_FILESYSTEM_DIR)/quarrune_hero.t3dm
QUARRUNE_BODY := $(QUARRUNE_FILESYSTEM_DIR)/tex_quarrune_body_ci8_64x64.sprite
QUARRUNE_ACCENT := $(QUARRUNE_FILESYSTEM_DIR)/tex_quarrune_accent_ci4_32x32.sprite
QUARRUNE_SHADOW := $(QUARRUNE_FILESYSTEM_DIR)/tex_quarrune_blob_shadow_ia8_32x32.sprite
QUARRUNE_RUNTIME_CANDIDATES := \
	$(QUARRUNE_MODEL) \
	$(QUARRUNE_BODY) \
	$(QUARRUNE_ACCENT) \
	$(QUARRUNE_SHADOW)
AYSELOR_SOURCE_DIR := runtime-candidates/echo/echo.ayselor
AYSELOR_FILESYSTEM_DIR := filesystem/echo/echo.ayselor
AYSELOR_MODEL := $(AYSELOR_FILESYSTEM_DIR)/ayselor_distance.t3dm
AYSELOR_ANIM_0 := $(AYSELOR_FILESYSTEM_DIR)/ayselor_distance.0.sdata
AYSELOR_ANIM_1 := $(AYSELOR_FILESYSTEM_DIR)/ayselor_distance.1.sdata
AYSELOR_ANIM_2 := $(AYSELOR_FILESYSTEM_DIR)/ayselor_distance.2.sdata
AYSELOR_BODY := $(AYSELOR_FILESYSTEM_DIR)/tex_ayselor_body_ci8_64x64.sprite
AYSELOR_ACCENT := $(AYSELOR_FILESYSTEM_DIR)/tex_ayselor_accent_ci4_32x32.sprite
AYSELOR_SHADOW := $(AYSELOR_FILESYSTEM_DIR)/tex_ayselor_blob_shadow_ia8_32x32.sprite
AYSELOR_RUNTIME_CANDIDATES := \
	$(AYSELOR_MODEL) \
	$(AYSELOR_ANIM_0) \
	$(AYSELOR_ANIM_1) \
	$(AYSELOR_ANIM_2) \
	$(AYSELOR_BODY) \
	$(AYSELOR_ACCENT) \
	$(AYSELOR_SHADOW)
GYRECLAST_SOURCE_DIR := runtime-candidates/echo/echo.gyreclast
GYRECLAST_FILESYSTEM_DIR := filesystem/echo/echo.gyreclast
GYRECLAST_MODEL := $(GYRECLAST_FILESYSTEM_DIR)/gyreclast_distance.t3dm
GYRECLAST_ANIM_0 := $(GYRECLAST_FILESYSTEM_DIR)/gyreclast_distance.0.sdata
GYRECLAST_ANIM_1 := $(GYRECLAST_FILESYSTEM_DIR)/gyreclast_distance.1.sdata
GYRECLAST_ANIM_2 := $(GYRECLAST_FILESYSTEM_DIR)/gyreclast_distance.2.sdata
GYRECLAST_BODY := $(GYRECLAST_FILESYSTEM_DIR)/tex_gyreclast_body_ci8_64x64.sprite
GYRECLAST_ACCENT := $(GYRECLAST_FILESYSTEM_DIR)/tex_gyreclast_accent_ci4_32x32.sprite
GYRECLAST_SHADOW := $(GYRECLAST_FILESYSTEM_DIR)/tex_gyreclast_blob_shadow_ia8_32x32.sprite
GYRECLAST_RUNTIME_CANDIDATES := \
	$(GYRECLAST_MODEL) \
	$(GYRECLAST_ANIM_0) \
	$(GYRECLAST_ANIM_1) \
	$(GYRECLAST_ANIM_2) \
	$(GYRECLAST_BODY) \
	$(GYRECLAST_ACCENT) \
	$(GYRECLAST_SHADOW)
KIVARRAX_SOURCE_DIR := runtime-candidates/echo/echo.kivarrax
KIVARRAX_FILESYSTEM_DIR := filesystem/echo/echo.kivarrax
KIVARRAX_MODEL := $(KIVARRAX_FILESYSTEM_DIR)/kivarrax_distance.t3dm
KIVARRAX_ANIM_0 := $(KIVARRAX_FILESYSTEM_DIR)/kivarrax_distance.0.sdata
KIVARRAX_ANIM_1 := $(KIVARRAX_FILESYSTEM_DIR)/kivarrax_distance.1.sdata
KIVARRAX_ANIM_2 := $(KIVARRAX_FILESYSTEM_DIR)/kivarrax_distance.2.sdata
KIVARRAX_BODY := $(KIVARRAX_FILESYSTEM_DIR)/tex_kivarrax_body_ci8_64x64.sprite
KIVARRAX_ACCENT := $(KIVARRAX_FILESYSTEM_DIR)/tex_kivarrax_accent_ci4_32x32.sprite
KIVARRAX_SHADOW := $(KIVARRAX_FILESYSTEM_DIR)/tex_kivarrax_blob_shadow_ia8_32x32.sprite
KIVARRAX_RUNTIME_CANDIDATES := \
	$(KIVARRAX_MODEL) \
	$(KIVARRAX_ANIM_0) \
	$(KIVARRAX_ANIM_1) \
	$(KIVARRAX_ANIM_2) \
	$(KIVARRAX_BODY) \
	$(KIVARRAX_ACCENT) \
	$(KIVARRAX_SHADOW)
ANNEX_KIT_SOURCE_DIR := runtime-candidates/env/env.annex.threshold_kit
ANNEX_KIT_FILESYSTEM_DIR := filesystem/env/env.annex.threshold_kit
ANNEX_KIT_MODEL := $(ANNEX_KIT_FILESYSTEM_DIR)/annex_threshold_kit.t3dm
ANNEX_KIT_ARCHITECTURE := $(ANNEX_KIT_FILESYSTEM_DIR)/tex_annex_architecture_ci4_64x64.sprite
ANNEX_KIT_TRIM := $(ANNEX_KIT_FILESYSTEM_DIR)/tex_annex_trim_resonance_ci4_64x32.sprite
ANNEX_KIT_MASK := $(ANNEX_KIT_FILESYSTEM_DIR)/tex_annex_resonance_mask_ia8_32x32.sprite
ANNEX_KIT_RUNTIME_CANDIDATES := \
	$(ANNEX_KIT_MODEL) \
	$(ANNEX_KIT_ARCHITECTURE) \
	$(ANNEX_KIT_TRIM) \
	$(ANNEX_KIT_MASK)
PLAYER_SOURCE_DIR := runtime-candidates/chr/chr.player.ari
PLAYER_FILESYSTEM_DIR := filesystem/chr/chr.player.ari
PLAYER_MODEL := $(PLAYER_FILESYSTEM_DIR)/player_ari.t3dm
PLAYER_IDLE := $(PLAYER_FILESYSTEM_DIR)/player_ari.0.sdata
PLAYER_WALK := $(PLAYER_FILESYSTEM_DIR)/player_ari.1.sdata
PLAYER_RUN := $(PLAYER_FILESYSTEM_DIR)/player_ari.2.sdata
PLAYER_BODY := $(PLAYER_FILESYSTEM_DIR)/tex_player_ari_body_ci8_64x64.sprite
PLAYER_FACE := $(PLAYER_FILESYSTEM_DIR)/tex_player_ari_face_ci4_32x32.sprite
PLAYER_RUNTIME_CANDIDATES := \
	$(PLAYER_MODEL) \
	$(PLAYER_IDLE) \
	$(PLAYER_WALK) \
	$(PLAYER_RUN) \
	$(PLAYER_BODY) \
	$(PLAYER_FACE)

include $(N64_INST)/include/n64.mk
include $(T3D_ROOT)/t3d.mk

N64_CFLAGS += -std=gnu2x -Os -Wall -Wextra -Werror -Wshadow -Wconversion

OBJS := \
	$(BUILD_DIR)/main.o \
	$(BUILD_DIR)/n64game_annex.o \
	$(BUILD_DIR)/n64game_core.o \
	$(BUILD_DIR)/n64game_render.o \
	$(BUILD_DIR)/n64game_save.o \
	$(BUILD_DIR)/n64game_telemetry.o \
	$(BUILD_DIR)/player_render_assets.o \
	$(BUILD_DIR)/quarrune_render_assets.o \
	$(BUILD_DIR)/support_echo_render_assets.o \
	$(BUILD_DIR)/support_echo_renderer.o

.PHONY: all clean stage-rom

all: stage-rom

# t3d.mk already injects libt3d.a into the linker flags. Keep the archive as an
# order-only prerequisite so it is built first without also appearing in $^.
$(BUILD_DIR)/$(ROM_NAME).elf: $(OBJS) | $(T3D_ROOT)/build/libt3d.a

$(T3D_GLTF_TO_3D):
	$(MAKE) -C $(T3D_ROOT)/tools/gltf_importer -j$${N64GAME_JOBS:-4}

$(QUARRUNE_MODEL): $(QUARRUNE_SOURCE_DIR)/quarrune_hero.glb | $(T3D_GLTF_TO_3D)
	@mkdir -p $(dir $@)
	@echo "    [T3D-CANDIDATE] $@"
	$(T3D_GLTF_TO_3D) "$<" "$@" --base-scale=64 --asset-path=runtime-candidates

$(QUARRUNE_BODY): $(QUARRUNE_SOURCE_DIR)/tex_quarrune_body_ci8_64x64.png
	@mkdir -p $(dir $@)
	$(N64_MKSPRITE) --format CI8 --tiles 64,64 --mipmap NONE --dither NONE --compress 0 -o $(dir $@) "$<"
	@test -f "$@"

$(QUARRUNE_ACCENT): $(QUARRUNE_SOURCE_DIR)/tex_quarrune_accent_ci4_32x32.png
	@mkdir -p $(dir $@)
	$(N64_MKSPRITE) --format CI4 --tiles 32,32 --mipmap NONE --dither NONE --compress 0 -o $(dir $@) "$<"
	@test -f "$@"

$(QUARRUNE_SHADOW): $(QUARRUNE_SOURCE_DIR)/tex_quarrune_blob_shadow_ia8_32x32.png
	@mkdir -p $(dir $@)
	$(N64_MKSPRITE) --format IA8 --tiles 32,32 --mipmap NONE --dither NONE --compress 0 -o $(dir $@) "$<"
	@test -f "$@"

$(AYSELOR_MODEL) $(AYSELOR_ANIM_0) $(AYSELOR_ANIM_1) $(AYSELOR_ANIM_2) &: $(AYSELOR_SOURCE_DIR)/ayselor_distance.glb | $(T3D_GLTF_TO_3D)
	@mkdir -p $(AYSELOR_FILESYSTEM_DIR)
	@echo "    [T3D-CANDIDATE] $(AYSELOR_MODEL)"
	$(T3D_GLTF_TO_3D) "$<" "$(AYSELOR_MODEL)" --base-scale=64 --asset-path=runtime-candidates
	@test -f "$(AYSELOR_MODEL)"
	@test -f "$(AYSELOR_ANIM_0)"
	@test -f "$(AYSELOR_ANIM_1)"
	@test -f "$(AYSELOR_ANIM_2)"

$(AYSELOR_BODY): $(AYSELOR_SOURCE_DIR)/tex_ayselor_body_ci8_64x64.png
	@mkdir -p $(dir $@)
	$(N64_MKSPRITE) --format CI8 --tiles 64,64 --mipmap NONE --dither NONE --compress 0 -o $(dir $@) "$<"
	@test -f "$@"

$(AYSELOR_ACCENT): $(AYSELOR_SOURCE_DIR)/tex_ayselor_accent_ci4_32x32.png
	@mkdir -p $(dir $@)
	$(N64_MKSPRITE) --format CI4 --tiles 32,32 --mipmap NONE --dither NONE --compress 0 -o $(dir $@) "$<"
	@test -f "$@"

$(AYSELOR_SHADOW): $(AYSELOR_SOURCE_DIR)/tex_ayselor_blob_shadow_ia8_32x32.png
	@mkdir -p $(dir $@)
	$(N64_MKSPRITE) --format IA8 --tiles 32,32 --mipmap NONE --dither NONE --compress 0 -o $(dir $@) "$<"
	@test -f "$@"

$(GYRECLAST_MODEL) $(GYRECLAST_ANIM_0) $(GYRECLAST_ANIM_1) $(GYRECLAST_ANIM_2) &: $(GYRECLAST_SOURCE_DIR)/gyreclast_distance.glb | $(T3D_GLTF_TO_3D)
	@mkdir -p $(GYRECLAST_FILESYSTEM_DIR)
	@echo "    [T3D-CANDIDATE] $(GYRECLAST_MODEL)"
	$(T3D_GLTF_TO_3D) "$<" "$(GYRECLAST_MODEL)" --base-scale=64 --asset-path=runtime-candidates
	@test -f "$(GYRECLAST_MODEL)"
	@test -f "$(GYRECLAST_ANIM_0)"
	@test -f "$(GYRECLAST_ANIM_1)"
	@test -f "$(GYRECLAST_ANIM_2)"

$(GYRECLAST_BODY): $(GYRECLAST_SOURCE_DIR)/tex_gyreclast_body_ci8_64x64.png
	@mkdir -p $(dir $@)
	$(N64_MKSPRITE) --format CI8 --tiles 64,64 --mipmap NONE --dither NONE --compress 0 -o $(dir $@) "$<"
	@test -f "$@"

$(GYRECLAST_ACCENT): $(GYRECLAST_SOURCE_DIR)/tex_gyreclast_accent_ci4_32x32.png
	@mkdir -p $(dir $@)
	$(N64_MKSPRITE) --format CI4 --tiles 32,32 --mipmap NONE --dither NONE --compress 0 -o $(dir $@) "$<"
	@test -f "$@"

$(GYRECLAST_SHADOW): $(GYRECLAST_SOURCE_DIR)/tex_gyreclast_blob_shadow_ia8_32x32.png
	@mkdir -p $(dir $@)
	$(N64_MKSPRITE) --format IA8 --tiles 32,32 --mipmap NONE --dither NONE --compress 0 -o $(dir $@) "$<"
	@test -f "$@"

$(KIVARRAX_MODEL) $(KIVARRAX_ANIM_0) $(KIVARRAX_ANIM_1) $(KIVARRAX_ANIM_2) &: $(KIVARRAX_SOURCE_DIR)/kivarrax_distance.glb | $(T3D_GLTF_TO_3D)
	@mkdir -p $(KIVARRAX_FILESYSTEM_DIR)
	@echo "    [T3D-CANDIDATE] $(KIVARRAX_MODEL)"
	$(T3D_GLTF_TO_3D) "$<" "$(KIVARRAX_MODEL)" --base-scale=64 --asset-path=runtime-candidates
	@test -f "$(KIVARRAX_MODEL)"
	@test -f "$(KIVARRAX_ANIM_0)"
	@test -f "$(KIVARRAX_ANIM_1)"
	@test -f "$(KIVARRAX_ANIM_2)"

$(KIVARRAX_BODY): $(KIVARRAX_SOURCE_DIR)/tex_kivarrax_body_ci8_64x64.png
	@mkdir -p $(dir $@)
	$(N64_MKSPRITE) --format CI8 --tiles 64,64 --mipmap NONE --dither NONE --compress 0 -o $(dir $@) "$<"
	@test -f "$@"

$(KIVARRAX_ACCENT): $(KIVARRAX_SOURCE_DIR)/tex_kivarrax_accent_ci4_32x32.png
	@mkdir -p $(dir $@)
	$(N64_MKSPRITE) --format CI4 --tiles 32,32 --mipmap NONE --dither NONE --compress 0 -o $(dir $@) "$<"
	@test -f "$@"

$(KIVARRAX_SHADOW): $(KIVARRAX_SOURCE_DIR)/tex_kivarrax_blob_shadow_ia8_32x32.png
	@mkdir -p $(dir $@)
	$(N64_MKSPRITE) --format IA8 --tiles 32,32 --mipmap NONE --dither NONE --compress 0 -o $(dir $@) "$<"
	@test -f "$@"

$(ANNEX_KIT_MODEL): $(ANNEX_KIT_SOURCE_DIR)/annex_threshold_kit.glb | $(T3D_GLTF_TO_3D)
	@mkdir -p $(dir $@)
	@echo "    [T3D-CANDIDATE] $@"
	$(T3D_GLTF_TO_3D) "$<" "$@" --base-scale=64 --asset-path=runtime-candidates

$(ANNEX_KIT_ARCHITECTURE): $(ANNEX_KIT_SOURCE_DIR)/tex_annex_architecture_ci4_64x64.png
	@mkdir -p $(dir $@)
	$(N64_MKSPRITE) --format CI4 --tiles 64,64 --mipmap NONE --dither NONE --compress 0 -o $(dir $@) "$<"
	@test -f "$@"

$(ANNEX_KIT_TRIM): $(ANNEX_KIT_SOURCE_DIR)/tex_annex_trim_resonance_ci4_64x32.png
	@mkdir -p $(dir $@)
	$(N64_MKSPRITE) --format CI4 --tiles 64,32 --mipmap NONE --dither NONE --compress 0 -o $(dir $@) "$<"
	@test -f "$@"

$(ANNEX_KIT_MASK): $(ANNEX_KIT_SOURCE_DIR)/tex_annex_resonance_mask_ia8_32x32.png
	@mkdir -p $(dir $@)
	$(N64_MKSPRITE) --format IA8 --tiles 32,32 --mipmap NONE --dither NONE --compress 0 -o $(dir $@) "$<"
	@test -f "$@"

$(PLAYER_MODEL) $(PLAYER_IDLE) $(PLAYER_WALK) $(PLAYER_RUN) &: $(PLAYER_SOURCE_DIR)/player_ari.glb | $(T3D_GLTF_TO_3D)
	@mkdir -p $(PLAYER_FILESYSTEM_DIR)
	@echo "    [T3D-CANDIDATE] $(PLAYER_MODEL)"
	$(T3D_GLTF_TO_3D) "$<" "$(PLAYER_MODEL)" --base-scale=64 --asset-path=runtime-candidates
	@test -f "$(PLAYER_MODEL)"
	@test -f "$(PLAYER_IDLE)"
	@test -f "$(PLAYER_WALK)"
	@test -f "$(PLAYER_RUN)"

$(PLAYER_BODY): $(PLAYER_SOURCE_DIR)/tex_player_ari_body_ci8_64x64.png
	@mkdir -p $(dir $@)
	$(N64_MKSPRITE) --format CI8 --tiles 64,64 --mipmap NONE --dither NONE --compress 0 -o $(dir $@) "$<"
	@test -f "$@"

$(PLAYER_FACE): $(PLAYER_SOURCE_DIR)/tex_player_ari_face_ci4_32x32.png
	@mkdir -p $(dir $@)
	$(N64_MKSPRITE) --format CI4 --tiles 32,32 --mipmap NONE --dither NONE --compress 0 -o $(dir $@) "$<"
	@test -f "$@"

$(BUILD_DIR)/$(ROM_NAME).dfs: \
	$(QUARRUNE_RUNTIME_CANDIDATES) \
	$(AYSELOR_RUNTIME_CANDIDATES) \
	$(GYRECLAST_RUNTIME_CANDIDATES) \
	$(KIVARRAX_RUNTIME_CANDIDATES) \
	$(ANNEX_KIT_RUNTIME_CANDIDATES) \
	$(PLAYER_RUNTIME_CANDIDATES)

$(ROM_NAME).z64: N64_ROM_TITLE = "N64GAME OPENING"
$(ROM_NAME).z64: N64_ROM_SAVETYPE = eeprom4k
$(ROM_NAME).z64: N64_ROM_CONTROLLER1 = n64
$(ROM_NAME).z64: $(BUILD_DIR)/$(ROM_NAME).dfs

stage-rom: $(ROM_NAME).z64
	@mkdir -p $(dir $(ROM_OUTPUT))
	mv $< $(ROM_OUTPUT)

$(T3D_ROOT)/build/libt3d.a:
	$(MAKE) -C $(T3D_ROOT) -j$${N64GAME_JOBS:-4}

clean:
	rm -rf $(BUILD_DIR) filesystem $(ROM_NAME).z64

-include $(wildcard $(BUILD_DIR)/*.d)
