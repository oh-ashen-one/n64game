# Production Gates and Evidence

This checklist tracks proof, not percentages. A gate is complete only when its required artifacts exist and the cited evidence has been inspected.

| Gate | Status | Required evidence | Current evidence / blocker |
|---|---|---|---|
| 1. Reference and legal audit | Complete | `docs/reference-study.md`; clean-room boundary; verified license boundaries for code/assets present at Gate 1; public hygiene baseline | Reference boundaries and toolchain pins audited; clean-room rules, separate licenses, notices, ignore/LFS rules, ledger template, secret scan, LFS attribute check, and large-file scan pass. The Ares distribution audit carried into Gate 3 is now resolved in `config/toolchain.lock.json` and `THIRD_PARTY_NOTICES.md` |
| 2. Preproduction | Complete | Story beat sheet, timing map, technical architecture, data schemas, `docs/ART_BIBLE.md`, complete asset inventory, review templates | The traceability exit audit, schema/ID cross-checks, asset-contract validator, public-hygiene audit, and independent Gate 2 reviews passed on the public merge |
| 3. Toolchain | Verification in progress | Pinned compatible dependencies, Docker/libdragon setup, clean ROM, Ares launch workflow, public CI artifact | Public runs `29674638989`, `29675541575`, and `29675864028` passed; exact ROM SHA `230896d0...394d7e` rendered two distinct frames in audited Ares v148. Clean commit `85e91c7` also passed `make validate`, `make rom`, 17/17 host tests, `make report`, and the full bootstrap locally through audited Colima/VZ/Rosetta, producing identical bytes. Docker Desktop itself remains blocked by macOS policy error `failed to call driver: 0x3`; because the master spec names Docker Desktop literally, Gate 3 remains open pending a rebooted Docker Desktop pass or explicit user authorization to amend that requirement. See `docs/GATE3_BOOT_EVIDENCE.md` |
| 4. Visual benchmark | Not started | Approved environment corner, hero Echoform, humanoid, lighting, UI, battle animation, and VFX in-engine | — |
| 5. End-to-end greybox | Not started | Cold boot through ending state flow, both battles, saves/retries/transitions, timing instrumentation | — |
| 6. Gameplay completion | Not started | Complete battle, exploration, camera, collision, dialogue, companion, world map, save/load, and edge cases | — |
| 7. Production assets | Not started | Every placeholder replaced; every production asset passes gates 1–7 with ledger evidence | — |
| 8. Presentation polish | Not started | Final animation, audio, UI, VFX, lighting, loading, cameras, environment dressing, and transitions | — |
| 9. Storyboard package | Not started | 18 reviewed 4:3 panels, individual exports, contact sheet, continuity sheet, color script, shot list | — |
| 10. Certification | Not started | Clean builds, three timed runs, Ares matrix, 20-loop memory soak, FPS/heap/size evidence, license audit | — |
| 11. Release handoff | Not started | Public verified artifacts, checksums, captures, known limitations, direct user deliverables | — |

## Gate 1 checklist

- [x] Public repository exists at `oh-ashen-one/n64game` on `main`.
- [x] Master production prompt and short goal prompt are published.
- [x] MIT code license is separate from the All Rights Reserved asset license.
- [x] Third-party notice file exists without claiming unverified rights.
- [x] Reference downloads and credentials are excluded from public Git history.
- [x] Git LFS rules are defined for editable binary production sources.
- [x] Asset provenance/review ledger template exists.
- [x] Pandemonium v0.71 architecture, presentation, asset, and license audit recorded.
- [x] Shared Drive snapshot differences and license implications recorded.
- [x] Tiny3D/libdragon/Fast64/Ares versions and intended uses recorded; Ares distribution-license verification explicitly deferred to Gate 3 before certification or redistribution.
- [x] Pokémon XD opening pacing and clean-room functional mapping recorded.
- [x] Reachable-history, index, and worktree secret/large-file/archive/ROM audit passes by content after Gate 1 documents are staged.
