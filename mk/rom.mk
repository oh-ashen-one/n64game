V ?= 1
SOURCE_DIR := src
BUILD_DIR := build/game
T3D_ROOT := $(CURDIR)/build/deps/tiny3d
ROM_NAME := n64game-gate3
ROM_OUTPUT := $(BUILD_DIR)/$(ROM_NAME).z64
QUARRUNE_SOURCE_DIR := runtime-candidates/echo/echo.quarrune
QUARRUNE_PACKAGE_DIR := $(QUARRUNE_SOURCE_DIR)/runtime
QUARRUNE_FILESYSTEM_DIR := filesystem/echo/echo.quarrune
QUARRUNE_MODEL := $(QUARRUNE_FILESYSTEM_DIR)/quarrune.t3dm
QUARRUNE_BODY := $(QUARRUNE_FILESYSTEM_DIR)/tex_quarrune_body_ci8_64x64.sprite
QUARRUNE_ACCENT := $(QUARRUNE_FILESYSTEM_DIR)/tex_quarrune_accent_ci4_32x32.sprite
QUARRUNE_SHADOW := $(QUARRUNE_FILESYSTEM_DIR)/tex_quarrune_blob_shadow_ia8_32x32.sprite
QUARRUNE_ANIMATION_STREAMS := $(foreach index,0 1 2,$(QUARRUNE_FILESYSTEM_DIR)/quarrune.$(index).sdata)
QUARRUNE_MODEL_SHA256 := 276709f4224c88667734d1c4c796221c3aabd882f50313af0b437d413f46381b
QUARRUNE_STREAM_0_SHA256 := 2ea2d8b50d525564e04a529834992595c65cbb2153753be50ba11fc672377f86
QUARRUNE_STREAM_1_SHA256 := 59a5ab9fcdce9b0b03daaa6e574df17e468375b2acf16a550c395a510d4e75b9
QUARRUNE_STREAM_2_SHA256 := 74780bcf51efd2744fab0645dba0fbe11a2582d947bf8862d9f9739f9648e694
QUARRUNE_RUNTIME_CANDIDATES := \
	$(QUARRUNE_MODEL) \
	$(QUARRUNE_ANIMATION_STREAMS) \
	$(QUARRUNE_BODY) \
	$(QUARRUNE_ACCENT) \
	$(QUARRUNE_SHADOW)
AYSELOR_SOURCE_DIR := runtime-candidates/echo/echo.ayselor
AYSELOR_PACKAGE_DIR := $(AYSELOR_SOURCE_DIR)/runtime
AYSELOR_FILESYSTEM_DIR := filesystem/echo/echo.ayselor
AYSELOR_MODEL := $(AYSELOR_FILESYSTEM_DIR)/ayselor.t3dm
AYSELOR_BODY := $(AYSELOR_FILESYSTEM_DIR)/tex_ayselor_body_ci8_64x64.sprite
AYSELOR_ACCENT := $(AYSELOR_FILESYSTEM_DIR)/tex_ayselor_accent_ci4_32x32.sprite
AYSELOR_ANIMATION_STREAMS := $(foreach index,0 1 2,$(AYSELOR_FILESYSTEM_DIR)/ayselor.$(index).sdata)
AYSELOR_MODEL_SHA256 := 7892a0635544e407ab8d5b5c5d3b1f3b26fd00a3d5f5056c798b27326512f20c
AYSELOR_STREAM_0_SHA256 := 184005a7176e15acfe9d4711df95d11019f2e55b0086260f05be96c3307802f2
AYSELOR_STREAM_1_SHA256 := 9c5632335d7e54895fb925f88d841a880f6dd627a785bd4caae727d1641abab3
AYSELOR_STREAM_2_SHA256 := 1b322a32a4bcde89e5543c5dd5eecfe9be993c777cee215efb619aa0aca1bfde
AYSELOR_RUNTIME_CANDIDATES := \
	$(AYSELOR_MODEL) \
	$(AYSELOR_ANIMATION_STREAMS) \
	$(AYSELOR_BODY) \
	$(AYSELOR_ACCENT)
ANNEX_SOURCE_DIR := runtime-candidates/annex
ANNEX_FILESYSTEM_DIR := filesystem/env/annex
ANNEX_MODEL := $(ANNEX_FILESYSTEM_DIR)/annex_threshold.t3dm
ANNEX_ARCHITECTURE := $(ANNEX_FILESYSTEM_DIR)/tex_annex_architecture_ci4_64x64.sprite
ANNEX_TRIM := $(ANNEX_FILESYSTEM_DIR)/tex_annex_trim_resonance_ci4_64x32.sprite
ANNEX_RESONANCE_MASK := $(ANNEX_FILESYSTEM_DIR)/tex_annex_resonance_mask_ia8_32x32.sprite
ANNEX_RUNTIME_CANDIDATES := \
	$(ANNEX_MODEL) \
	$(ANNEX_ARCHITECTURE) \
	$(ANNEX_TRIM) \
	$(ANNEX_RESONANCE_MASK)
ARI_SOURCE_DIR := runtime-candidates/chr/player_ari
ARI_FILESYSTEM_DIR := filesystem/chr/player_ari
ARI_MODEL := $(ARI_FILESYSTEM_DIR)/ari.t3dm
ARI_BODY := $(ARI_FILESYSTEM_DIR)/tex_ari_body_ci8_64x64.sprite
ARI_FACE := $(ARI_FILESYSTEM_DIR)/tex_ari_face_warm_ci4_32x32.sprite
ARI_ANIMATION_STREAMS := $(foreach index,0 1 2 3 4 5 6 7 8 9 10,$(ARI_FILESYSTEM_DIR)/ari.$(index).sdata)
ARI_RUNTIME_CANDIDATES := \
	$(ARI_MODEL) \
	$(ARI_ANIMATION_STREAMS) \
	$(ARI_BODY) \
	$(ARI_FACE)
GYRECLAST_SOURCE_DIR := runtime-candidates/echo/echo.gyreclast
GYRECLAST_FILESYSTEM_DIR := filesystem/echo/echo.gyreclast
GYRECLAST_MODEL := $(GYRECLAST_FILESYSTEM_DIR)/gyreclast.t3dm
GYRECLAST_BODY := $(GYRECLAST_FILESYSTEM_DIR)/tex_gyreclast_body_ci8_64x64.sprite
GYRECLAST_ACCENT := $(GYRECLAST_FILESYSTEM_DIR)/tex_gyreclast_accent_ci4_32x32.sprite
GYRECLAST_ANIMATION_STREAMS := $(foreach index,0 1 2,$(GYRECLAST_FILESYSTEM_DIR)/gyreclast.$(index).sdata)
GYRECLAST_RUNTIME_CANDIDATES := \
	$(GYRECLAST_MODEL) \
	$(GYRECLAST_ANIMATION_STREAMS) \
	$(GYRECLAST_BODY) \
	$(GYRECLAST_ACCENT)
KIVARRAX_SOURCE_DIR := runtime-candidates/echo/echo.kivarrax
KIVARRAX_FILESYSTEM_DIR := filesystem/echo/echo.kivarrax
KIVARRAX_MODEL := $(KIVARRAX_FILESYSTEM_DIR)/kivarrax.t3dm
KIVARRAX_BODY := $(KIVARRAX_FILESYSTEM_DIR)/tex_kivarrax_body_ci8_64x64.sprite
KIVARRAX_DIAPHRAGM := $(KIVARRAX_FILESYSTEM_DIR)/tex_kivarrax_diaphragm_ci4_32x32.sprite
KIVARRAX_ANIMATION_STREAMS := $(foreach index,0 1 2,$(KIVARRAX_FILESYSTEM_DIR)/kivarrax.$(index).sdata)
KIVARRAX_RUNTIME_CANDIDATES := \
	$(KIVARRAX_MODEL) \
	$(KIVARRAX_ANIMATION_STREAMS) \
	$(KIVARRAX_BODY) \
	$(KIVARRAX_DIAPHRAGM)

include $(N64_INST)/include/n64.mk
include $(T3D_ROOT)/t3d.mk

define VERIFY_REVIEWED_CANDIDATE
@PYTHONDONTWRITEBYTECODE=1 python3 -I -B -c 'import hashlib,pathlib,sys; p=pathlib.Path(sys.argv[1]); e=sys.argv[2]; (not p.is_file() or p.is_symlink()) and sys.exit(f"{p}: expected one regular reviewed candidate"); a=hashlib.sha256(p.read_bytes()).hexdigest(); a != e and sys.exit(f"{p}: SHA-256 {a} != {e}")' "$(1)" "$(2)"
endef

N64_CFLAGS += -std=gnu2x -Os -Wall -Wextra -Werror -Wshadow -Wconversion

OBJS := \
	$(BUILD_DIR)/main.o \
	$(BUILD_DIR)/n64game_annex.o \
	$(BUILD_DIR)/n64game_core.o \
	$(BUILD_DIR)/n64game_render.o \
	$(BUILD_DIR)/n64game_save.o \
	$(BUILD_DIR)/indexed_render_assets.o \
	$(BUILD_DIR)/quarrune_render_assets.o

.PHONY: all clean stage-rom

all: stage-rom

# t3d.mk already injects libt3d.a into the linker flags. Keep the archive as an
# order-only prerequisite so it is built first without also appearing in $^.
$(BUILD_DIR)/$(ROM_NAME).elf: $(OBJS) | $(T3D_ROOT)/build/libt3d.a

$(T3D_GLTF_TO_3D):
	$(MAKE) -C $(T3D_ROOT)/tools/gltf_importer -j$${N64GAME_JOBS:-4}

$(QUARRUNE_MODEL): $(QUARRUNE_PACKAGE_DIR)/quarrune.t3dm
	@mkdir -p $(dir $@)
	@echo "    [T3D-REVIEWED-CANDIDATE] $@"
	$(call VERIFY_REVIEWED_CANDIDATE,$<,$(QUARRUNE_MODEL_SHA256))
	cp "$<" "$@"
	cmp "$<" "$@"
	$(call VERIFY_REVIEWED_CANDIDATE,$@,$(QUARRUNE_MODEL_SHA256))

$(QUARRUNE_FILESYSTEM_DIR)/quarrune.0.sdata: $(QUARRUNE_PACKAGE_DIR)/quarrune.0.sdata
	@mkdir -p $(dir $@)
	$(call VERIFY_REVIEWED_CANDIDATE,$<,$(QUARRUNE_STREAM_0_SHA256))
	cp "$<" "$@"
	cmp "$<" "$@"
	$(call VERIFY_REVIEWED_CANDIDATE,$@,$(QUARRUNE_STREAM_0_SHA256))

$(QUARRUNE_FILESYSTEM_DIR)/quarrune.1.sdata: $(QUARRUNE_PACKAGE_DIR)/quarrune.1.sdata
	@mkdir -p $(dir $@)
	$(call VERIFY_REVIEWED_CANDIDATE,$<,$(QUARRUNE_STREAM_1_SHA256))
	cp "$<" "$@"
	cmp "$<" "$@"
	$(call VERIFY_REVIEWED_CANDIDATE,$@,$(QUARRUNE_STREAM_1_SHA256))

$(QUARRUNE_FILESYSTEM_DIR)/quarrune.2.sdata: $(QUARRUNE_PACKAGE_DIR)/quarrune.2.sdata
	@mkdir -p $(dir $@)
	$(call VERIFY_REVIEWED_CANDIDATE,$<,$(QUARRUNE_STREAM_2_SHA256))
	cp "$<" "$@"
	cmp "$<" "$@"
	$(call VERIFY_REVIEWED_CANDIDATE,$@,$(QUARRUNE_STREAM_2_SHA256))

$(QUARRUNE_BODY): $(QUARRUNE_SOURCE_DIR)/tex_quarrune_body_ci8_64x64.png tools/n64game_gate5_export.py
	@mkdir -p $(dir $@)
	$(N64_MKSPRITE) --format CI8 --tiles 64,64 --mipmap NONE --dither NONE --compress 0 -o $(dir $@) "$<"
	PYTHONDONTWRITEBYTECODE=1 python3 -I -B -c 'import pathlib,runpy,sys; runpy.run_path("tools/n64game_gate5_export.py", run_name="n64game_sprite_contract")["canonicalize_sprite"](pathlib.Path(sys.argv[1]))' "$@"
	@test -f "$@"

$(QUARRUNE_ACCENT): $(QUARRUNE_SOURCE_DIR)/tex_quarrune_accent_ci4_32x32.png tools/n64game_gate5_export.py
	@mkdir -p $(dir $@)
	$(N64_MKSPRITE) --format CI4 --tiles 32,32 --mipmap NONE --dither NONE --compress 0 -o $(dir $@) "$<"
	PYTHONDONTWRITEBYTECODE=1 python3 -I -B -c 'import pathlib,runpy,sys; runpy.run_path("tools/n64game_gate5_export.py", run_name="n64game_sprite_contract")["canonicalize_sprite"](pathlib.Path(sys.argv[1]))' "$@"
	@test -f "$@"

$(QUARRUNE_SHADOW): $(QUARRUNE_SOURCE_DIR)/tex_quarrune_blob_shadow_ia8_32x32.png
	@mkdir -p $(dir $@)
	$(N64_MKSPRITE) --format IA8 --tiles 32,32 --mipmap NONE --dither NONE --compress 0 -o $(dir $@) "$<"
	@test -f "$@"

$(AYSELOR_MODEL): $(AYSELOR_PACKAGE_DIR)/ayselor.t3dm
	@mkdir -p $(dir $@)
	@echo "    [T3D-REVIEWED-CANDIDATE] $@"
	$(call VERIFY_REVIEWED_CANDIDATE,$<,$(AYSELOR_MODEL_SHA256))
	cp "$<" "$@"
	cmp "$<" "$@"
	$(call VERIFY_REVIEWED_CANDIDATE,$@,$(AYSELOR_MODEL_SHA256))

$(AYSELOR_FILESYSTEM_DIR)/ayselor.0.sdata: $(AYSELOR_PACKAGE_DIR)/ayselor.0.sdata
	@mkdir -p $(dir $@)
	$(call VERIFY_REVIEWED_CANDIDATE,$<,$(AYSELOR_STREAM_0_SHA256))
	cp "$<" "$@"
	cmp "$<" "$@"
	$(call VERIFY_REVIEWED_CANDIDATE,$@,$(AYSELOR_STREAM_0_SHA256))

$(AYSELOR_FILESYSTEM_DIR)/ayselor.1.sdata: $(AYSELOR_PACKAGE_DIR)/ayselor.1.sdata
	@mkdir -p $(dir $@)
	$(call VERIFY_REVIEWED_CANDIDATE,$<,$(AYSELOR_STREAM_1_SHA256))
	cp "$<" "$@"
	cmp "$<" "$@"
	$(call VERIFY_REVIEWED_CANDIDATE,$@,$(AYSELOR_STREAM_1_SHA256))

$(AYSELOR_FILESYSTEM_DIR)/ayselor.2.sdata: $(AYSELOR_PACKAGE_DIR)/ayselor.2.sdata
	@mkdir -p $(dir $@)
	$(call VERIFY_REVIEWED_CANDIDATE,$<,$(AYSELOR_STREAM_2_SHA256))
	cp "$<" "$@"
	cmp "$<" "$@"
	$(call VERIFY_REVIEWED_CANDIDATE,$@,$(AYSELOR_STREAM_2_SHA256))

$(AYSELOR_BODY): $(AYSELOR_SOURCE_DIR)/filesystem/echo/echo.ayselor/tex_ayselor_body_ci8_64x64.png tools/n64game_gate5_export.py
	@mkdir -p $(dir $@)
	$(N64_MKSPRITE) --format CI8 --tiles 64,64 --mipmap NONE --dither NONE --compress 0 -o $(dir $@) "$<"
	PYTHONDONTWRITEBYTECODE=1 python3 -I -B -c 'import pathlib,runpy,sys; runpy.run_path("tools/n64game_gate5_export.py", run_name="n64game_sprite_contract")["canonicalize_sprite"](pathlib.Path(sys.argv[1]))' "$@"
	@test -f "$@"

$(AYSELOR_ACCENT): $(AYSELOR_SOURCE_DIR)/filesystem/echo/echo.ayselor/tex_ayselor_accent_ci4_32x32.png tools/n64game_gate5_export.py
	@mkdir -p $(dir $@)
	$(N64_MKSPRITE) --format CI4 --tiles 32,32 --mipmap NONE --dither NONE --compress 0 -o $(dir $@) "$<"
	PYTHONDONTWRITEBYTECODE=1 python3 -I -B -c 'import pathlib,runpy,sys; runpy.run_path("tools/n64game_gate5_export.py", run_name="n64game_sprite_contract")["canonicalize_sprite"](pathlib.Path(sys.argv[1]))' "$@"
	@test -f "$@"

$(ANNEX_MODEL): $(ANNEX_SOURCE_DIR)/intermediate/annex_threshold.glb | $(T3D_GLTF_TO_3D)
	@mkdir -p $(dir $@)
	@echo "    [T3D-CANDIDATE] $@"
	$(T3D_GLTF_TO_3D) "$<" "$@" --base-scale=64 --asset-path=$(ANNEX_SOURCE_DIR)/filesystem

$(ANNEX_ARCHITECTURE): $(ANNEX_SOURCE_DIR)/filesystem/env/annex/tex_annex_architecture_ci4_64x64.png
	@mkdir -p $(dir $@)
	$(N64_MKSPRITE) --format CI4 --tiles 64,64 --mipmap NONE --dither NONE --compress 0 -o $(dir $@) "$<"
	@test -f "$@"

$(ANNEX_TRIM): $(ANNEX_SOURCE_DIR)/filesystem/env/annex/tex_annex_trim_resonance_ci4_64x32.png
	@mkdir -p $(dir $@)
	$(N64_MKSPRITE) --format CI4 --tiles 64,32 --mipmap NONE --dither NONE --compress 0 -o $(dir $@) "$<"
	@test -f "$@"

$(ANNEX_RESONANCE_MASK): $(ANNEX_SOURCE_DIR)/filesystem/env/annex/tex_annex_resonance_mask_ia8_32x32.png
	@mkdir -p $(dir $@)
	$(N64_MKSPRITE) --format IA8 --tiles 32,32 --mipmap NONE --dither NONE --compress 0 -o $(dir $@) "$<"
	@test -f "$@"

$(ARI_MODEL): $(ARI_SOURCE_DIR)/intermediate/ari_bound.glb | $(T3D_GLTF_TO_3D)
	@mkdir -p $(dir $@)
	@echo "    [T3D-CANDIDATE] $@"
	$(T3D_GLTF_TO_3D) "$<" "$@" --base-scale=64 --asset-path=$(ARI_SOURCE_DIR)/filesystem --verbose
	@for stream in $(ARI_ANIMATION_STREAMS); do test -f "$$stream"; done

$(ARI_ANIMATION_STREAMS): $(ARI_MODEL)
	@test -f "$@"

$(ARI_BODY): $(ARI_SOURCE_DIR)/filesystem/chr/player_ari/tex_ari_body_ci8_64x64.png tools/n64game_gate5_export.py
	@mkdir -p $(dir $@)
	$(N64_MKSPRITE) --format CI8 --tiles 64,64 --mipmap NONE --dither NONE --compress 0 -o $(dir $@) "$<"
	PYTHONDONTWRITEBYTECODE=1 python3 -I -B -c 'import pathlib,runpy,sys; runpy.run_path("tools/n64game_gate5_export.py", run_name="n64game_sprite_contract")["canonicalize_sprite"](pathlib.Path(sys.argv[1]))' "$@"
	@test -f "$@"

$(ARI_FACE): $(ARI_SOURCE_DIR)/filesystem/chr/player_ari/tex_ari_face_warm_ci4_32x32.png tools/n64game_gate5_export.py
	@mkdir -p $(dir $@)
	$(N64_MKSPRITE) --format CI4 --tiles 32,32 --mipmap NONE --dither NONE --compress 0 -o $(dir $@) "$<"
	PYTHONDONTWRITEBYTECODE=1 python3 -I -B -c 'import pathlib,runpy,sys; runpy.run_path("tools/n64game_gate5_export.py", run_name="n64game_sprite_contract")["canonicalize_sprite"](pathlib.Path(sys.argv[1]))' "$@"
	@test -f "$@"

$(GYRECLAST_MODEL): $(GYRECLAST_SOURCE_DIR)/intermediate/gyreclast_bound.glb | $(T3D_GLTF_TO_3D)
	@mkdir -p $(dir $@)
	@echo "    [T3D-CANDIDATE] $@"
	$(T3D_GLTF_TO_3D) "$<" "$@" --base-scale=64 --asset-path=$(GYRECLAST_SOURCE_DIR)/filesystem --verbose
	@for stream in $(GYRECLAST_ANIMATION_STREAMS); do test -f "$$stream"; done

$(GYRECLAST_ANIMATION_STREAMS): $(GYRECLAST_MODEL)
	@test -f "$@"

$(GYRECLAST_BODY): $(GYRECLAST_SOURCE_DIR)/filesystem/echo/echo.gyreclast/tex_gyreclast_body_ci8_64x64.png tools/n64game_gate5_export.py
	@mkdir -p $(dir $@)
	$(N64_MKSPRITE) --format CI8 --tiles 64,64 --mipmap NONE --dither NONE --compress 0 -o $(dir $@) "$<"
	PYTHONDONTWRITEBYTECODE=1 python3 -I -B -c 'import pathlib,runpy,sys; runpy.run_path("tools/n64game_gate5_export.py", run_name="n64game_sprite_contract")["canonicalize_sprite"](pathlib.Path(sys.argv[1]))' "$@"
	@test -f "$@"

$(GYRECLAST_ACCENT): $(GYRECLAST_SOURCE_DIR)/filesystem/echo/echo.gyreclast/tex_gyreclast_accent_ci4_32x32.png tools/n64game_gate5_export.py
	@mkdir -p $(dir $@)
	$(N64_MKSPRITE) --format CI4 --tiles 32,32 --mipmap NONE --dither NONE --compress 0 -o $(dir $@) "$<"
	PYTHONDONTWRITEBYTECODE=1 python3 -I -B -c 'import pathlib,runpy,sys; runpy.run_path("tools/n64game_gate5_export.py", run_name="n64game_sprite_contract")["canonicalize_sprite"](pathlib.Path(sys.argv[1]))' "$@"
	@test -f "$@"

$(KIVARRAX_MODEL): $(KIVARRAX_SOURCE_DIR)/intermediate/kivarrax_bound.glb | $(T3D_GLTF_TO_3D)
	@mkdir -p $(dir $@)
	@echo "    [T3D-CANDIDATE] $@"
	$(T3D_GLTF_TO_3D) "$<" "$@" --base-scale=64 --asset-path=$(KIVARRAX_SOURCE_DIR)/filesystem --verbose
	@for stream in $(KIVARRAX_ANIMATION_STREAMS); do test -f "$$stream"; done

$(KIVARRAX_ANIMATION_STREAMS): $(KIVARRAX_MODEL)
	@test -f "$@"

$(KIVARRAX_BODY): $(KIVARRAX_SOURCE_DIR)/filesystem/echo/echo.kivarrax/tex_kivarrax_body_ci8_64x64.png tools/n64game_gate5_export.py
	@mkdir -p $(dir $@)
	$(N64_MKSPRITE) --format CI8 --tiles 64,64 --mipmap NONE --dither NONE --compress 0 -o $(dir $@) "$<"
	PYTHONDONTWRITEBYTECODE=1 python3 -I -B -c 'import pathlib,runpy,sys; runpy.run_path("tools/n64game_gate5_export.py", run_name="n64game_sprite_contract")["canonicalize_sprite"](pathlib.Path(sys.argv[1]))' "$@"
	@test -f "$@"

$(KIVARRAX_DIAPHRAGM): $(KIVARRAX_SOURCE_DIR)/filesystem/echo/echo.kivarrax/tex_kivarrax_diaphragm_ci4_32x32.png tools/n64game_gate5_export.py
	@mkdir -p $(dir $@)
	$(N64_MKSPRITE) --format CI4 --tiles 32,32 --mipmap NONE --dither NONE --compress 0 -o $(dir $@) "$<"
	PYTHONDONTWRITEBYTECODE=1 python3 -I -B -c 'import pathlib,runpy,sys; runpy.run_path("tools/n64game_gate5_export.py", run_name="n64game_sprite_contract")["canonicalize_sprite"](pathlib.Path(sys.argv[1]))' "$@"
	@test -f "$@"

$(BUILD_DIR)/$(ROM_NAME).dfs: \
	$(QUARRUNE_RUNTIME_CANDIDATES) \
	$(AYSELOR_RUNTIME_CANDIDATES) \
	$(ANNEX_RUNTIME_CANDIDATES) \
	$(ARI_RUNTIME_CANDIDATES) \
	$(GYRECLAST_RUNTIME_CANDIDATES) \
	$(KIVARRAX_RUNTIME_CANDIDATES)

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
