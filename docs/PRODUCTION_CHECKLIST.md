# Production Gates and Evidence

This checklist tracks proof, not percentages. A gate is complete only when its required artifacts exist and the cited evidence has been inspected.

| Gate | Status | Required evidence | Current evidence / blocker |
|---|---|---|---|
| 1. Reference and legal audit | Complete | `docs/reference-study.md`; clean-room boundary; verified license boundaries for code/assets present at Gate 1; public hygiene baseline | Reference boundaries and toolchain pins audited; clean-room rules, separate licenses, notices, ignore/LFS rules, ledger template, secret scan, LFS attribute check, and large-file scan pass. The Ares distribution audit carried into Gate 3 is now resolved in `config/toolchain.lock.json` and `THIRD_PARTY_NOTICES.md` |
| 2. Preproduction | Complete | Story beat sheet, timing map, technical architecture, data schemas, `docs/ART_BIBLE.md`, complete asset inventory, review templates | The traceability exit audit, schema/ID cross-checks, asset-contract validator, public-hygiene audit, and independent Gate 2 reviews passed on the public merge |
| 3. Toolchain | Complete | Pinned compatible dependencies, Docker/libdragon setup, clean ROM, Ares launch workflow, public CI artifact | Docker Desktop 4.82.0 / Engine 29.6.1 built clean commit `dd03848`; `make validate`, `make rom`, 17/17 host tests, `make report`, and the full bootstrap passed. Public closure run `29676805197` rebuilt the identical tree and produced exact ROM SHA `230896d0...394d7e`, matching the two advancing frames already captured in audited Ares v148. See `docs/GATE3_BOOT_EVIDENCE.md` |
| R. One-week scope revision | In progress | Authoritative 6–8 minute master prompt and sub-4000 launcher; public merge | User explicitly cut breadth on 2026-07-19. The revised scope retains one Annex, one Quarrune/Ayselor vs Gyreclast/Kivarrax battle, save/retry, loading/slate, hook, and twelve-panel storyboard while preserving the anti-slop bar |
| 4. Visual benchmark | In progress | Approved Annex composition, player, four-Echoform battle-distance set, lighting, UI, animation, and VFX in-engine | Contract/tooling prerequisites exist; real source art, reviewed Tiny3D exports, native-camera captures, and visual approval remain missing |
| 5. Playable spine and gameplay | Not started | Cold boot through stable beacon ending; one battle; Annex exploration; save/retry; timing instrumentation and edge cases | — |
| 6. Production replacement | Not started | Every retained placeholder replaced; every retained production asset passes gates 1–7 with provenance/evidence | — |
| 7. Presentation and storyboard | Not started | Final animation/audio/UI/VFX/lighting/loading/cameras/dressing plus 12 reviewed 4:3 panels, individual exports, contact sheet, continuity sheet, color script, and shot list | — |
| 8. Certification and release | Not started | Clean public builds, two timed runs, Ares matrix, 10-loop memory soak, FPS/heap/size evidence, license audit, public artifacts, captures, and direct deliverables | — |

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
