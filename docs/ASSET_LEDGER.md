# Asset Provenance and Review Ledger

No production asset may ship without a completed ledger entry. “Original” and “AI-generated” are not sufficient provenance descriptions by themselves.

## Status vocabulary

- `planned`: inventory entry exists; production has not begun
- `concept`: concept sources exist but are not approved
- `source`: editable production source exists
- `converted`: runtime conversion succeeds
- `review`: undergoing the seven mandatory art gates
- `approved`: all gates passed with evidence
- `rejected`: must be rebuilt or materially revised

## Review gates

1. Concept/orthographic
2. Blender topology, normals, UV, scale, rig, and naming
3. Textured turntable
4. Animation and deformation
5. Tiny3D conversion
6. In-engine gameplay-camera, lighting, memory, and performance
7. Final consistency and polish

## Ledger

| Asset ID | Category | Name / purpose | Status | Owner / creator | Source and prompt provenance | Editable source | Runtime output | License | Gates 1–7 | Evidence | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `ui.cutscene_slate` | UI | Approved temporary `INSERT CUTSCENE HERE` integration slate | planned | oh-ashen-one / OpenAI-assisted production | Master-spec requirement; final design source to be recorded | — | — | All Rights Reserved | — | — | Only intentionally temporary visual allowed at acceptance |

## Required inventory groups

The production inventory must eventually include every player/NPC model, all eight battle Echoforms, both environment sets, world map, at least 25 props, every UI surface, every animation, every VFX event, all music/SFX, the 18 storyboard panels, contact sheet, continuity sheet, and color script. Split each item into a distinct row once preproduction identifiers are locked.
