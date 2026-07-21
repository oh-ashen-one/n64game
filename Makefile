SHELL := /bin/bash

.DEFAULT_GOAL := rom

.PHONY: clean assets test test-authoring test-certification authoring-check certification-check rom validate report

CERTIFICATION_MANIFEST ?= build/certification/evidence.json
CERTIFICATION_ROM ?= build/game/n64game-gate3.z64

clean:
	scripts/clean-build

assets:
	scripts/validate-assets

test:
	scripts/test-host

test-authoring:
	scripts/test-authoring-stack

test-certification:
	scripts/test-certification

authoring-check:
	scripts/check-authoring-stack

certification-check:
	scripts/validate-certification-evidence --manifest "$(CERTIFICATION_MANIFEST)" --rom "$(CERTIFICATION_ROM)"

rom:
	scripts/build-rom

validate:
	scripts/verify-toolchain-pins
	scripts/validate-data
	scripts/validate-assets
	scripts/validate-public-hygiene

report:
	scripts/make-checksums
	scripts/audit-final-acceptance
