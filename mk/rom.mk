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
	$(BUILD_DIR)/quarrune_render_assets.o

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

$(BUILD_DIR)/$(ROM_NAME).dfs: $(QUARRUNE_RUNTIME_CANDIDATES)

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
