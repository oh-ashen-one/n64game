V ?= 1
SOURCE_DIR := src
BUILD_DIR := build/game
T3D_ROOT := $(CURDIR)/build/deps/tiny3d
ROM_NAME := n64game-gate3
ROM_OUTPUT := $(BUILD_DIR)/$(ROM_NAME).z64

include $(N64_INST)/include/n64.mk
include $(T3D_ROOT)/t3d.mk

N64_CFLAGS += -std=gnu2x -Os -Wall -Wextra -Werror -Wshadow -Wconversion

OBJS := \
	$(BUILD_DIR)/main.o \
	$(BUILD_DIR)/quarrune_render_assets.o

.PHONY: all clean stage-rom

all: stage-rom

# t3d.mk already injects libt3d.a into the linker flags. Keep the archive as an
# order-only prerequisite so it is built first without also appearing in $^.
$(BUILD_DIR)/$(ROM_NAME).elf: $(OBJS) | $(T3D_ROOT)/build/libt3d.a

$(ROM_NAME).z64: N64_ROM_TITLE = "N64GAME GATE 3"
$(ROM_NAME).z64: N64_ROM_SAVETYPE = eeprom4k
$(ROM_NAME).z64: N64_ROM_CONTROLLER1 = n64

stage-rom: $(ROM_NAME).z64
	@mkdir -p $(dir $(ROM_OUTPUT))
	mv $< $(ROM_OUTPUT)

$(T3D_ROOT)/build/libt3d.a:
	$(MAKE) -C $(T3D_ROOT) -j$${N64GAME_JOBS:-4}

clean:
	rm -rf $(BUILD_DIR) $(ROM_NAME).z64

-include $(wildcard $(BUILD_DIR)/*.d)
