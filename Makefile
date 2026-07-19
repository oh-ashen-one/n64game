SHELL := /bin/bash

.DEFAULT_GOAL := rom

.PHONY: clean assets test test-authoring authoring-check rom validate report

clean:
	scripts/clean-build

assets:
	scripts/validate-assets

test:
	scripts/test-host

test-authoring:
	scripts/test-authoring-stack

authoring-check:
	scripts/check-authoring-stack

rom:
	scripts/build-rom

validate:
	scripts/verify-toolchain-pins
	scripts/validate-data
	scripts/validate-assets
	scripts/validate-public-hygiene

report:
	scripts/make-checksums
