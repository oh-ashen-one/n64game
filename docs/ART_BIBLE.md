# N64GAME Art Bible

Status: Gate 2 production contract

Authority: subordinate only to `docs/N64GAME_MASTER_SPEC.md`

Target: 320×240, 4:3, 16-bit color, 30 FPS, standard 4 MB Nintendo 64

## 1. Visual thesis

`N64GAME` is retro desert science fiction built from **weathered utility and luminous wonder**. Meridian Research Annex should feel like a field station repeatedly repaired by practical researchers; Veyra Observatory Estate should feel like one brilliant inventor turned astronomy into inhabitable sculpture. The world is sun-bleached and materially grounded until Resonance or Fracture makes it briefly impossible.

The target is a deliberately authored late-console-era RPG image: large readable silhouettes, economical but purposeful topology, painted and vertex-colored form, dense storytelling at interaction distance, confident framing, and full animation coverage. Low polygon count is a composition discipline, never an excuse for generic primitives, flat rooms, default materials, noisy generated textures, or dead poses.

Every final frame must support three readings:

1. At a glance: player, objective, walkable route, interactable, and threat are separable.
2. At play distance: silhouette, material family, facial direction, and action remain readable at 320×240.
3. On inspection: props, wear, color accents, and motion reveal who built and uses the place.

The two locations must be distinguishable from an untextured silhouette image. Meridian is low, braced, modular, and horizontal. Veyra is tall, orbital, eccentric, and radial. The Severance is neither: it is narrow, split, restrained, and defined by missing volume.

## 2. Anti-slop production contract

An asset is not production-ready because it exists, looks acceptable in one render, or was expensive to generate. It ships only when its construction is intentional and all seven review gates have evidence.

Required qualities for every visible production asset:

- Original silhouette and identifiable design purpose.
- Topology that describes form and deformation instead of merely tessellating it.
- Clean normals, applied transforms, deliberate origin, correct scale, and stable naming.
- UV islands placed around seams and camera exposure; no accidental overlaps unless explicitly mirrored.
- Consistent texel density, authored vertex color, limited materials, and no default shader residue.
- Attractive front, rear, profile, three-quarter, top, and gameplay-camera readings.
- Correct performance at native resolution, representative lighting, and representative distance.
- Proven provenance and licensing in `docs/ASSET_LEDGER.md`.
- At least two recorded polish passes after first in-engine integration for each hero asset.

Prohibited shortcuts:

- Raw image-generation output used as a model texture, UI screen, portrait, or final concept without correction.
- Auto-generated topology or auto-rig output accepted without deformation, silhouette, naming, and budget review.
- Unmodified cubes, cylinders, spheres, checker materials, mannequin rigs, Mixamo-like default performances, or Blender default lighting in an accepted build.
- “N64 style” used to excuse featureless boxes, empty corridors, texture blur, unreadable faces, or one-animation creatures.
- Random greebles, meaningless decals, fake writing, generic hazard stripes, or noise used to simulate detail.
- One attractive camera angle hiding collapsed anatomy, broken backsides, missing ceilings, or incomplete rooms.
- Baked highlights or shadows that conflict with gameplay lighting.
- Palette drift, costume drift, changing limb counts, or vehicle redesigns between concepts, models, portraits, and storyboard panels.
- A prop duplicated to fill space without a new use, orientation, wear story, or composition role.

Reproducible-source rule: every file that can change a runtime byte must be a reviewed ordinary-Git blob or canonical Git LFS object retrievable and materialized by a credential-free fresh public clone of the exact payload commit. A URL, release locator, or build script that promises a later download is not a Gate-2 source member. A local-only Blender file, layered image, lossless audio master, generated concept selected as a texture source, font source, or manual conversion output is not a production source. Local-only archival masters are permitted only when the ledger states that they are non-build records and identifies the committed Git/Git-LFS build input derived from them. No gate pass may depend on media that reviewers or CI cannot retrieve.

## 3. Platform art budget

The visual bar is achieved through hierarchy and reuse, not by exceeding memory. These caps align with the architecture’s 1,100 KiB largest-active-scene arena and separate process/UI/audio allocations. They remain planning values until the visual benchmark and memory profiler replace them with measured evidence.

| Resource | Ownership scope | Planning cap | Rule |
|---|---|---:|---|
| Three framebuffers | process/frame | 450 KiB | 320×240 RGBA16; measured allocation wins |
| Depth buffer | process/frame | 150 KiB | One 320×240 16-bit buffer |
| Scene textures, including screen-specific UI/VFX sprites | scene/action | 300 KiB exploration / 336 KiB battle | Runtime-expanded total, not compressed ROM size |
| Scene geometry and display data | scene | 240 KiB | Segment and cull rooms; never load both destinations together |
| Skeletons and active animation | scene | 208 KiB | Load only active actors and clips |
| Collision, nav, spawn, interaction, and scene state | scene | 128 KiB | Authored simplified data; fixed capacities |
| Action/VFX presentation pools | action within scene | 128 KiB | Reset after each action; no unbounded emitters |
| Persistent font/UI-shell media | process/UI shell | 48 KiB | Screen-specific panels are charged to scene textures |
| Audio stream and active SFX cache | process/audio | 256 KiB | Within architecture’s separate 300 KiB audio cap |
| Required peak free heap | global | at least 512 KiB | Measured in the busiest battle and exploration views |

The five scene/action rows total 1,004 KiB in exploration and 1,040 KiB in battle, leaving 96 KiB or 60 KiB respectively beneath the 1,100 KiB scene ceiling for measured alignment and registry overhead. A category may borrow only from another measured scene category; the global 512 KiB floor never moves.

Art production must target a ROM below 16 MiB. Source `.blend`, layered images, and lossless audio do not define runtime size; optimized outputs must be reproducible and measured in build reports.

Per-frame guidance:

- Busiest exploration view: target at most 8,000 visible environment triangles, 3,500 character/prop triangles, 24 opaque material batches, 8 translucent batches, and 96 active particles.
- Busiest battle view: target at most 5,000 arena triangles, 6,000 actor triangles, 20 opaque batches, 12 translucent batches, and 128 active particles.
- Alpha blending is exceptional. Prefer cutout, dither, vertex alpha, and opaque geometry.
- Hidden back rooms, unseen floors, and off-camera cast must be culled or unloaded by sector.
- No metric above is permission to miss 30 FPS. Profiling evidence wins over estimated counts.

## 4. Shape language

### 4.1 Meridian Research Annex

Primary shapes: wide trapezoids, softened rectangular frames, paired braces, horizontal datum lines, and three-lobed Resonance motifs. Corners are clipped or capped with pale ceramic. Machinery sits inside dark teal metal cages. Cabling follows service paths rather than wandering decoratively.

Silhouette rule: a Meridian object looks stable enough to survive desert wind and simple enough to repair in gloves. A one-meter object needs one dominant mass, one functional secondary mass, and at most three tertiary accents.

### 4.2 Veyra Observatory Estate

Primary shapes: offset circles, open rings, counterweighted arms, spherical pivots, tapered pylons, and asymmetrical pinwheels. Repetition follows orbital spacing: one large arc, two smaller echoes, and a visibly functional axle or counterweight.

Silhouette rule: a Veyra device appears one motion away from transformation. Its mechanism must remain understandable; whimsy comes from proportion and motion, not random parts.

### 4.3 Humans

Humans use an approximately 6.5-head stylized proportion, broad hands, simplified facial planes, strong footwear, and clothing layers that read as two or three large color blocks. Heads and hands may be slightly enlarged for dialogue readability. Each named character owns a distinct shoulder line, center-of-mass, negative-space shape, and accent color. Do not distinguish characters only by texture.

- Player/Ari: forward-leaning wedge, cropped field jacket, compact relay harness, open forearm silhouette. Neutral enough for naming, specific enough to be a character.
- Tavi: short upward triangles, oversized scarf tail and field pouch, quick off-center stance; never a miniature player copy.
- Dr. Sera Venn: tall stable column broken by one diagonal diagnostic sash; careful hands and restrained motion.
- Director Oren Saye: broad low center, semicircular mantle/yoke, planted stance, economical gestures.
- Ivo Veyra: long crescent coat, asymmetric tool rig, high elbows, orbiting handheld parts.
- Rusk: squared work apron over a defensive triangle, heavy gloves, backward weight that opens after the apology.
- Supporting Annex staff: share Meridian utility seams while differing in job silhouette: clinic curves, workshop blocks, and cartography layers.

Faces use modeled brow/nose/jaw planes plus a compact expression texture or minimal vertex deformation. Eyes must indicate gaze at gameplay distance. Avoid photoreal pores, anime-face defaults, or texture-only heads with no facial form.

Cast accent locks keep identity stable between model, portrait, UI, and storyboard work:

| Character | Base blocks | Identity accent |
|---|---|---|
| Player/Ari | Field navy `#314866`, fabric sand `#A98E6C` | Relay cyan `#5FC7C8` |
| Tavi | Dusk indigo `#39456B`, sun cloth `#C9A66A` | Scarf coral `#C9694B` |
| Dr. Sera Venn | Clinic cream `#D7C59A`, diagnostic teal `#2B6265` | Signal amber `#E2A64E` |
| Director Oren Saye | Ink brown `#241E20`, deep clay `#6E3D2D` | Oxide red `#8C4A3C` |
| Ivo Veyra | Leather plum `#5B3A4C`, sun chalk `#D8C9A7` | Instrument brass `#B48A4E` |
| Rusk | Work clay `#724639`, fabric night `#26344C` | Apron amber `#C68A4D` |
| Mara Ovelle | Clinic jade `#4D8A7A`, fabric sand `#A98E6C` | Clean cyan `#75C5C0` |
| Jo Renn | Teal iron `#204F53`, work brown `#50352F` | Tool oxide `#9A533F` |
| Pell Anwar | Cartography cobalt `#435684`, sun chalk `#D8C9A7` | Map cyan `#5FC7C8` |

These are costume/value anchors, not skin colors. Skin ramps remain individually authored and must retain separation from the clothing blocks under both warm and cool lighting.

### 4.4 Echoforms

Echoforms are coherent living resonators, not real animals with accessories. Each design starts with one physical phenomenon, one non-animal structural metaphor, and one movement verb. A readable Echoform needs:

- One dominant silhouette gesture visible in a 64×64 black thumbnail.
- Exactly one primary Resonance organ: vane, drum, lens, fork, cavity, filament, or plate field.
- A locomotion solution that explains balance and attack staging.
- A clear front and gaze without requiring human eyes.
- Two large value groups plus one controlled affinity accent.
- No resemblance to a protected creature silhouette, branded capture device, or familiar evolution family.

Battle designs may be 0.7–2.4 m at the shoulder/primary mass. Even floating forms cast an authored blob shadow. Limbs and ornaments that cannot be animated or understood at 320×240 are removed.

### 4.5 Severance and Fracture

Severance technology uses split keels, inward hooks, paired restraint lines, and narrow violet apertures. Surfaces are nearly charcoal but never pure black. Hardware looks surgically subtracted rather than armored with spikes.

Fracture is a violation of the normal palette and motion rules: duplicated edges, violet-to-cold-white cores, brief negative silhouettes, delayed secondary motion, and lens-like bending. It is never generic purple smoke. Limit it so that a Fracture event remains alarming.

### 4.6 Vehicles and cinematic objects

- Solace carrier: a long pale research hull suspended beneath a manta-like sun shade, three visible instrument pods, a warm ventral work deck, and a blunt rescue-orange tail. Its asymmetry comes only from deployed science equipment.
- Severance gliders: narrow split-diamond craft with a missing center, two restraint reels, and no cockpit canopy visible at storyboard distance.
- Meridian sand-skimmer: a low 3.2 m field vehicle on three broad ceramic runners, with one clipped shade hoop, exposed teal service spine, and rescue-orange tail case. It reads as practical outpost transport, not a car, motorcycle, or creature saddle. The map token reduces it to runner wedge + shade hoop + relay light.
- World-map travel marker: the simplified sand-skimmer runner-wedge/hoop silhouette travels with a three-lobed relay pulse over the relief map; it is not a generic car, train, or copied overworld avatar.

### 4.7 Locked Echoform roster

These eight designs are distinct production assets. No tutorial or opponent model is a recolor, scaled copy, or costume swap of a starter.

| Echoform | Affinity | Visual construction | Movement verb and silhouette test |
|---|---|---|---|
| Quarrune | Strata | Compact six-legged ceramic-plated resonator; cobalt horn lattice frames a hollow tuning cavity; broad tank/support stance | **Brace**: six planted footpads and the open horn lattice remain separable in a 64×64 silhouette |
| Ayselor | Gale | Hovering tri-wing manta/kite with clothlike fins, narrow body keel, and amber keel lamp | **Glide**: one long wing, two swept counter-wings, and dangling lamp establish its facing without eyes |
| Kilnback | Ember | Broad quadruped kiln body with separated furnace ribs, chimney shoulder, and compact bellows haunch | **Stoke**: low mass compresses then expands through the ribs; never reads as an ordinary armored mammal |
| Nacreel | Current | Ribbon body moving through a broken halo of conductive droplets; nacre value ramp and one cyan charge path | **Orbit**: body and incomplete droplet ring keep intentional negative space from every battle angle |
| Gyreclast | Strata | Three-legged mineral excavator with one offset drill-claw, low carapace slab, and fault-line face aperture | **Bore**: tripod support and off-axis drill remain readable; avoid literal crab anatomy and paired pincers |
| Kivarrax | Gale | Long-legged desert runner with a fan tail, narrow pressure-scoop chest, and rearward vane head | **Skim**: alternating leg gaps and one large fan wedge communicate speed in profile and three-quarter view |
| Kovrass | Ember | Low brass-and-ceramic bellows body with jackal/badger weight, vented cheeks, and a single boiler-throat chamber | **Pump**: the back-to-front bellows wave sells support actions; avoid a conventional canine head silhouette |
| Ulvorel | Current | Squat amphibious mass under a translucent hood, with a visible pendulum throat and two broad fluid feet | **Sway**: hood arch, throat weight, and compressed base read as three stacked rhythms rather than a real frog |

Affinity accents are subordinate to identity. Strata uses cobalt inlays and ochre mass; Gale uses pale cloth and amber directional lights; Ember uses oxide, brass, and controlled furnace coral; Current uses teal/cyan paths and nacre highlights. All eight retain the shared Echoform principle of one visible Resonance organ and physically motivated performance.

## 5. Palette and value hierarchy

All values are sRGB hex targets. Runtime conversion may quantize them; compare converted captures against the intended relationships rather than forcing exact display values.

### 5.1 World neutrals

| Name | Hex | Use |
|---|---|---|
| Sun chalk | `#D8C9A7` | Ceramic panels, lit walls |
| Bleached bone | `#BDAF91` | Secondary panels, cloth |
| Ochre dust | `#B8733E` | Ground, wear, warm bounce |
| Deep clay | `#6E3D2D` | Creases, lower walls, soil shadow |
| Oxide red | `#8C4A3C` | Fasteners, selective warnings |
| Teal iron | `#204F53` | Annex machinery |
| Deep teal | `#12343A` | Recesses, night machinery |
| Cobalt shade | `#273A68` | Cool exterior shadow |
| Ink brown | `#241E20` | Deepest normal shadow; avoid pure black |

### 5.2 Light and energy

| Name | Hex | Use |
|---|---|---|
| Worklight amber | `#F0B85A` | Practicals, active path anchors |
| Relay cyan | `#5FC7C8` | Neutral interface, map links |
| Resonance mint | `#83E0B4` | Earned meter, supportive events |
| Resonance gold | `#FFD36A` | Full meter and duo-finisher peak |
| Fracture violet | `#8A4DCC` | Corruption body |
| Fracture magenta | `#D15AA8` | Corruption edge only |
| Fracture core | `#D8E5FF` | Sub-frame peak and monitor trace |
| Danger coral | `#E46855` | Low HP, destructive warning |

### 5.3 Character and UI neutrals

| Name | Hex | Use |
|---|---|---|
| Fabric sand | `#A98E6C` | Field clothing base |
| Fabric night | `#26344C` | Dark clothing and panel body |
| Leather plum | `#5B3A4C` | Straps and warm dark accents |
| Skin light | `#C88F6B` | Palette anchor, not a universal skin tone |
| Skin mid | `#8B5B49` | Palette anchor |
| Skin deep | `#54372F` | Palette anchor |
| UI navy | `#17243A` | Main panel |
| UI blue-grey | `#344B61` | Secondary panel |
| UI paper | `#F1E3C2` | Primary text |
| UI muted | `#A9B8B4` | Secondary text |

Skin palettes must be intentionally authored per character with lit, base, and shadow ramps. Never recolor one skin texture mechanically or treat the three anchors above as exhaustive.

Value rule: playable characters and interaction targets maintain at least one 20-point perceptual lightness separation from their immediate background. Fracture magenta cannot be used as ordinary decoration. Pure white is reserved for one-frame energy peaks and UI confirmation; pure black is avoided except mask/cutout data.

## 6. Materials, textures, UVs, and vertex color

### 6.1 Material families

Use seven shared visual families: sun-ceramic, oxidized metal, painted metal, woven cloth, worn leather, translucent energy, and living Echoform surface. Each asset may have local color variation, but it must inherit rough visual behavior from a family.

The renderer does not need modern PBR. Material identity comes from value breakup, edge color, vertex-light response, specular suggestion in the texture, animation, and silhouette. Metals use controlled light-dark bands aligned to form; ceramics use broad quiet fields; cloth uses sparse directional weave; living surfaces use gradients that support anatomy.

### 6.2 Runtime texture rules

- Default sources: 32×32 or 64×64.
- 16×16 is appropriate for tiny repeated detail; 128×64 or 128×128 requires benchmark evidence and a ledger justification.
- Prefer CI4 for compact color ramps, IA4/IA8 for masks and glyphs, CI8 where a richer shared palette materially helps, and RGBA16 only for assets whose edges or gradients visibly fail otherwise.
- One hero model should normally use one 64×64 body atlas plus at most one 32×32 face/accent texture. A second 64×64 requires budget review.
- Environment modules use trim/atlas textures shared within a location. Do not give every wall or prop a unique sheet.
- World texel density target: 24–32 source pixels per meter; hero interaction zones: 48–64 px/m; faces/icons are composition-based exceptions.
- Adjacent surfaces must not visibly jump more than 2× texel density without a focal reason.
- UV padding: at least two final-source pixels around islands and four around mip/filtered atlas borders when used. Test all seams after conversion.
- Mirroring is allowed for quiet structural surfaces, never across text, damage, asymmetrical costume identity, or a face that needs independent expression.
- Every texture receives a nearest-neighbor 4× inspection and an in-engine native-resolution inspection.

### 6.3 Vertex color

Vertex color is structural paint, not random noise. Use it to reinforce upward light, ground contact, broad plane changes, desert bounce, and material separation. Gradients follow topology and never create isolated dirty vertices. Ambient-occlusion baking may be used as a starting reference, then manually cleaned and limited so movable objects do not carry impossible floor shadows.

Do not use photographic textures, diffusion-model micro-detail, fake embossed text, or baked directional lighting as a substitute for geometry and scene light.

## 7. Geometry, rig, and deformation budgets

Budgets count visible triangles in the exported runtime mesh, including duplicated seam vertices and accessories.

| Asset class | Target triangles | Hard review cap | Materials | Rig joints | Exported influences per vertex |
|---|---:|---:|---:|---:|---:|
| Player / named hero human | 900–1,150 | 1,250 | 3 | 18–24 | 1 |
| Supporting human | 550–750 | 900 | 2–3 | 16–20 | 1 |
| Battle Echoform | 850–1,300 | 1,500 | 2–4 | 10–24 | 1 |
| Hero prop / landmark module | 300–1,200 | 1,500 | 1–3 | 0–8 | 1 if rigged |
| Small prop | 20–250 | 400 | 1–2 | 0–4 | 1 if rigged |
| Room sector | 1,000–3,500 | 4,500 | shared atlas | none or separate mechanisms | — |

Rules:

- Put triangles into silhouette, facial direction, hands, joints, and deformation arcs before flat hidden planes.
- Hero curves are faceted intentionally and use a consistent segment rhythm; neither accidental five-sided circles nor gratuitous 32-sided cylinders.
- Separate translucent meshes and animated mechanisms from opaque static room geometry.
- Skin weights must sum correctly; delete zero-weight and hidden duplicate vertices.
- Every exported skinned vertex has exactly one bone influence, and every exported triangle references at most three bones, matching the Tiny3D skinning contract. A richer source rig is allowed only if a tested, converter-safe bake/split produces that exact runtime form; do not assume the converter will repair blended weights.
- Base pose is a relaxed 35-degree arm pose for humans unless the exporter requires another documented pose. Echoform rest poses expose all deformation joints.
- Create simplified distance models only when a character can remain visible below 35 pixels tall. Distance models target 45–60% of hero triangles and preserve silhouette; do not ship automatic decimation artifacts.
- Collision is authored separately. Render topology is never assumed to be safe navigation collision.

## 8. Scale, coordinate, naming, and export conventions

### 8.1 Scale chart

These dimensions are construction targets measured in Blender meters. Gate 1 scale sheets show every hero beside the player, a standard door, and the relevant gameplay footprint; Gate 6 proves camera readability after conversion.

| Subject | Locked construction size | Gameplay/cinematic note |
|---|---:|---|
| Player/Ari | 1.72 m tall; 1.58 m eye | 48–72 px tall in normal exploration |
| Tavi | 1.38 m tall | Follower capsule and camera focus must never treat Tavi as an adult rescale |
| Dr. Sera Venn | 1.82 m tall | Tall column silhouette |
| Director Oren Saye | 1.76 m tall | Width/low center, not unusual height, provides authority |
| Ivo Veyra | 1.84 m tall | Coat crescent extends silhouette, never collision capsule |
| Rusk | 1.78 m tall | Heavy work stance; battle command mark remains outside actor lanes |
| Mara Ovelle / Jo Renn / Pell Anwar | 1.66 / 1.74 / 1.70 m | Each uses individually authored proportions |
| Quarrune | 0.95 m shoulder; 1.65 m body length | Six-foot support polygon approximately 1.25×0.80 m |
| Ayselor | 1.90 m wingspan; 1.15 m hover center | Body/keel length 1.20 m; shadow proves altitude |
| Kilnback | 1.10 m shoulder; 2.00 m body length | Largest simulation mass; never exceeds battle footprint |
| Nacreel | 1.80 m ribbon length; 1.20 m halo diameter | Hover center 1.20 m; halo negative space remains readable |
| Gyreclast | 1.00 m carapace height; 1.55 m span | Tripod support and auger stay within one lane |
| Kivarrax | 1.35 m shoulder; 2.00 m nose-to-fan | Longest vertical battle silhouette |
| Kovrass | 0.90 m shoulder; 1.60 m body length | Low bellows posture expands only within lane |
| Ulvorel | 0.85 m hood height; 1.30 m width | Compressed base and pendulum remain visible behind UI |
| Field Relay | 0.18 m closed height | Player hand socket and UI hero render use same source scale |
| Relay workshop dock / side reader | 0.26 m wide dock / 0.38 m high reader | Both use the same keyed Relay socket and visible latch depth; never fake the insertion with an overlap |
| Calibration locator tag | 0.07 m long × 0.04 m wide | Readable on Tavi’s satchel/reunion staging and in its close examine; pulse cannot replace the physical silhouette |
| Rusk wrench | 0.44 m long | Fits Rusk’s glove socket, remains visible through the authored drop, and settles clear of the battle route |
| Impossible compass | 0.22 m housing diameter | Multiple needles remain individually readable in the invention-hall examine camera |
| Ivo track paper roll | 0.32 m roll width; 0.75 m visible sheet | Hand sockets, curl, printed track, and study-desk contact remain continuous through the reunion performance |
| Sand-skimmer | 3.20 m long; 1.55 m wide; 1.55 m hoop height | Exterior hero version and simplified map version share proportions |
| Standard door | 1.20 m clear width × 2.30 m height | Door collision is simpler than render frame |
| Standard corridor | 1.80 m minimum clear width | Companion-critical route uses 2.20 m minimum |
| Battle lane | 2.40 m wide × 3.00 m deep | Actor motion may not cross neighboring legal footprint without authored override |
| Solace carrier | approximately 42 m long | Storyboard crew and 5.5 m gliders establish scale |
| Severance glider | approximately 5.5 m tip-to-tip | Restraint line hardware remains readable in medium shot |
| Fractured colossus | 110–140 m visible span | Exact body may be partly storm-obscured, but continuity sheet fixes proportions |

### 8.2 Native scale and gameplay-camera examples

The diagrams below are normative construction examples, not mood-board suggestions. They use the final 320x240 coordinate system and must be reproduced by the Gate 4 benchmark harness. Review evidence includes both the diagnostic overlay and the clean frame. If a later camera changes these relationships, the art, collision, UI, and camera owners review the change together.

**Exploration example — `EXAMPLE_CAM_EXP_01`, Annex simulation-threshold corner**

```text
source frame 320x240
0,0 +--------------------------------------------------------------+
    |  5% overscan simulation                                     |
12  |   +------------------------------------------------------+   |
    |   | warm doorway / mandatory route, x=198..286           |   |
    |   |                                                      |   |
    |   |             interactable value pocket                |   |
    |   |                     [console]                         |   |
    |   |                                                      |   |
    |   |       player, 56 px tall                              |   |
    |   |       x=112..139, feet y=199                          |   |
    |   |             5–8 m readable route                     |   |
227 |   +------------------------------------------------------+   |
    | mandatory body/UI exclusion below y=223                    |
240 +--------------------------------------------------------------+
      0  16             112       160        198       303      320
```

- Camera target is the player torso at approximately `(126, 166)`; the player occupies 48–72 pixels vertically and never merges with the doorway or console value group.
- The next 5–8 m of route remains visible. The doorway, not a floating arrow, owns the brightest warm normal-world value. The console maintains at least the art-bible 20-point perceptual-lightness separation from its immediate backing plane.
- The clean capture contains no overlay. The paired diagnostic capture shows safe area, actor box, route polygon, interaction focus, collision edge, and measured pixel height.
- **Bad counterpart:** player below 42 pixels, camera aimed at the floor, console tangent to the player silhouette, doorway hidden by foreground dressing, or prompt outside the safe area. Any one of those observations fails the example; a technically valid camera is not enough.

**Battle example — `EXAMPLE_CAM_BTL_01`, representative 2v2 command view**

```text
source frame 320x240
12  +----------------------------------------------------------+
    | enemy rear lane [E1]             [E2]                    |
    |                                                          |
    |              target / action clearance                   |
    |                                                          |
    | player near lane       [P1]             [P2]             |
    |----------------------------------------------------------|
    | HP identity blocks       predicted order / Resonance     |
    | command or move panel; selectable rows >=18 px           |
227 +----------------------------------------------------------+
     x=16                                                  x=303
```

- All four silhouettes, faces/action directions, blob shadows, legal-target cursor space, HP results, and the shared Resonance meter remain simultaneously readable.
- Actor framing keeps every face and HP element at least 12 pixels from the display edge during camera settle. A move camera must return to this stable tactical reading before the next decision.
- **Bad counterpart:** actor or VFX hidden behind UI, symmetric silhouette tangles, target cursor touching an actor edge, a move name wrapping unpredictably, or a camera cut concealing missing animation.

**Scale-lineup example — `EXAMPLE_SCALE_01`**

| Marker | Screen-space construction example | Required comparison |
|---|---|---|
| Standard door | 2.30 m clear height = 100% reference bar | Player reaches 74.8% of the opening; Tavi reaches 60.0% |
| Exploration player | 1.72 m and 56 px in the example frame | Eye line at 51 px above planted feet; hands/Relay remain separable |
| Tavi follower | 1.38 m and approximately 45 px at the same depth | Scarf and pouch create non-adult negative space; never scale an adult rig |
| Quarrune | 0.95 m shoulder and 1.65 m body length | Six footpads and horn cavity remain distinct beside the player |
| Ayselor | 1.90 m wingspan at 1.15 m hover center | Shadow, keel lamp, and three-wing facing remain visible behind battle UI |

Gate 1 construction sheets use these ratios beside the full scale table above. Gate 6 replaces schematic assumptions with measured native captures; it may not waive the readability relationships merely because world units are correct.

### 8.3 Coordinate and export rules

- One Blender unit equals one meter. Z is up in authored Blender scenes. Record the exporter’s forward-axis conversion in the build documentation and never correct it with per-asset runtime hacks.
- Player eye height target: 1.58 m; total player height: 1.72 m. Standard door clear opening: 1.2 m × 2.3 m. Corridor minimum gameplay width: 1.8 m; companion-critical width: 2.2 m.
- Human origins sit at ground between the feet. Grounded Echoforms use the center of the support polygon; floating Echoforms use the projection of the visual center onto ground.
- Apply transforms, triangulate deterministically, and freeze approved object scale before export.
- Mesh: `msh_<asset>_<part>`. Armature: `rig_<asset>`. Bones: `b_<region>_<side>` with `_l`, `_r`, or `_c`. Collision: `col_<scene>_<purpose>`. Socket: `sock_<purpose>`. Material: `mat_<family>_<variant>`. Texture: `tex_<asset>_<purpose>_<format>_<size>`.
- Animation clips: `anm_<asset>_<verb>[_<variant>]`; start at frame 0, no hidden pre-roll, root motion explicitly marked. Events use stable names such as `evt_foot_l`, `evt_hit`, `evt_vfx`, and `evt_voice`.
- Source paths use `assets-src/<production-id-prefix>/<canonical.production.id>/`, where the first directory is byte-for-byte the ID segment before its first dot (for example `assets-src/chr/chr.player.ari/`). Reproducible runtime outputs use ignored `build/generated/assets/<production-id-prefix>/` and never enter Git or a reviewed payload. Their immutable Gate-5 review snapshots, evidence, and records use `review/<canonical.production.id>/g<gate>/`.
- No spaces, mixed case, `.001` names, `Cube`, `Material`, `Armature`, or ambiguous `final_final` names may reach conversion.
- Export only named collections. Disable or remove reference planes, cameras, lights, backup meshes, and hidden high-poly sources from the export collection.

## 9. Lighting, fog, shadows, and atmosphere

The lighting model is painted daylight plus a small number of meaningful practicals.

### Meridian

- Exterior/threshold key: warm upper-left sun, approximately `#F0C47A`; shadow fill: cobalt `#344773`.
- Interior ambient: cool teal-grey `#52696D`; warm fixtures identify doors, work zones, and people.
- Atrium uses one bright vertical skylight band and darker teal circulation edges. The route is readable through value, not arrows.
- Simulation chamber may cool toward cyan, but human skin and field clothing retain warm separation.

### Veyra

- Courtyard key: late-afternoon ochre with long cobalt shadow; moving inventions catch small worklight accents.
- Interior ambient: deep blue-green with warm instrument pools. Circular devices produce controlled local halos through vertex color and small sprites, not full-screen bloom.
- Observatory study places the brightest normal-world value behind or beside Ivo/Tavi, preserving their silhouettes and directing the reunion composition.

### Fracture

Fracture locally inverts the normal warm/cool hierarchy: violet midtone, cold-white core, delayed magenta rim. It must not wash out UI or flatten the closing monitor silhouette.

### Display transform and color-grade contract

The project uses an authored scene grade, not a modern full-screen post-process. Final color is produced by source palette, cleaned texture ramps, vertex color, scene light, fog, dither/fade, and the Nintendo 64 RGBA16 output path. No LUT, emulator shader, capture-software filter, or baked screenshot adjustment may be required for the game to look correct.

| Context | Normal-world grade | Protected relationships | Failure condition |
|---|---|---|---|
| Meridian daylight/interior | Warm sun chalk/ochre upper planes, restrained cobalt/teal fill, amber practical anchors | Skin and UI paper stay warm-neutral; teal machinery keeps detail above ink-brown recesses | Cyan wash, crushed machinery, orange skin, or every room sharing one ambient value |
| Estate exterior/interior | Longer ochre-to-cobalt separation, deeper blue-green interior, localized brass/amber instrument pools | Circular devices may glow locally but cannot lift the whole framebuffer | Generic purple ambience, full-screen bloom look, or loss of route value hierarchy |
| Simulation | Cooler cyan/blue-grey environment with warm actors and paper text retained | Loaned Echoforms and target cursor remain distinct from the virtual shell | Actors become cyan silhouettes or grid contrast competes with commands |
| Resonance | Mint travel, gold only at full/finisher peak | Normal-world palette remains visible around the event | Global green/yellow tint or clipped white field |
| Fracture | Local violet midtone, magenta edge, sub-frame cold-white core, brief delayed duplicate | UI navy/paper and actor silhouettes remain stable; violet never becomes ordinary decor | Whole-frame purple wash, persistent white clip, UI tint, or generic smoke grade |
| Loading/slate/end card | Dusk ochre, dark teal, one controlled violet edge; fades use authored dither | Branding and exact text remain legible throughout real loading and fade states | Emulator-only gradient, banded unreadable text, frozen prior frame, or fake delay |

Conversion and capture rules:

- Author source swatches in sRGB, convert through the pinned asset pipeline, and evaluate the actual RGBA16 framebuffer. A desktop render is reference only.
- Use one documented ordered-dither/fade implementation. Dither may smooth a transition but may not texture every surface or hide banding caused by a bad palette.
- UI colors are authored in the same output space but are excluded from scene fog, Resonance tint, Fracture tint, and location grade. Any UI tint is a defect.
- The benchmark evidence includes: lossless source capture, raw 320x240 emulator framebuffer, 4x nearest-neighbor enlargement, 5% overscan/blur simulation, and a palette histogram. Capture software has brightness, contrast, saturation, sharpening, HDR, and color filters disabled.
- Compare relationships after conversion: darkest normal shadow still contains intentional plane separation; required text and gaze survive; one-frame peaks do not clip adjacent required detail. Exact hex equality is not expected after RGBA16 quantization.
- Grade revisions are versioned source changes. Post-hoc editing of review screenshots cannot pass a gate and is treated as falsified evidence.

Fog is used for depth and sector transitions, not to hide incomplete scenes. Exterior fog starts beyond primary play space and resolves to ochre/cobalt by time of day. Interior fog is subtle or absent. Blob/contact shadows are mandatory for humans, Echoforms, floating devices, and important moving props; shadow opacity and size respond to height but remain stable enough to avoid flicker.

## 10. Composition and gameplay-camera readability

- Exploration camera targets the player torso, not the floor. Default pitch and distance must show 5–8 m of route while keeping the player approximately 48–72 pixels tall.
- Battle establishes all four active Echoforms before command UI appears. Actor positions create two readable diagonals and preserve target cursor space.
- Mandatory interactables occupy a clear value pocket and keep prompts away from faces and route edges.
- Use foreground overlap sparingly; never let a decorative prop hide the player or interaction target for more than a moment.
- Door frames, floor bands, light pools, and prop orientation lead navigation. Floating objective arrows are a fallback, not the primary composition tool.
- Dialogue cameras must preserve gaze direction and avoid crossing the line unless the transition shot re-establishes space.
- Staging shots use 28–35 mm virtual equivalents for rooms, 45–60 mm for dialogue, and 70 mm only for inserts. Extreme wide or telephoto distortion is reserved for Fracture.
- All reviews include native 320×240 captures and nearest-neighbor enlargement. A model-sheet render cannot prove gameplay readability.

CRT-safe area:

- Keep mandatory UI inside x=16–303 and y=12–227.
- Keep body text and button labels inside x=20–299 and y=16–223.
- Keep battle actor faces and hit points at least 12 pixels from the visible edge during camera motion.
- Test with simulated 5% overscan, slight blur, and reduced saturation; source remains pixel-sharp.

## 11. UI, type, panels, and icon language

The UI resembles a rugged Field Relay: inset navy glass, clipped ceramic tabs, thin cyan traces, and three-lobed Resonance nodes. It is neither a fantasy scroll nor a modern translucent mobile card.

- Author an original bitmap family, working name `Meridian Raster`. The sentence-case body atlas must explicitly cover `A–Z`, `a–z`, `0–9`, and every punctuation mark used by locked dialogue/UI copy; name entry may expose only its approved uppercase subset, but it must not constrain dialogue coverage. Budget the body atlas as 128×128 IA4 (8 KiB maximum), with 8-pixel cap height and 10-pixel line spacing; compact labels may use 7-pixel caps only after CRT review. Headings use a separate 128×64 IA4 12/16-pixel designed atlas. The glyph audit must fail on any missing character, fallback font, replacement box, or fabricated pseudo-text.
- Primary text uses UI paper `#F1E3C2` on UI navy `#17243A`. Muted text uses `#A9B8B4`; unavailable actions also receive an icon/pattern change, never color alone.
- Panel corners use 45-degree clips tied to Annex bracing. Veyra screens may add an orbital tab, but preserve the same controls and type.
- Minimum selectable row height: 18 pixels. Minimum gap between target icons: 6 pixels. Cursor motion must settle in 80–120 ms with an audio tick.
- Icons are solid 8×8, 12×12, or 16×16 shapes with one dominant metaphor. Do not shrink detailed illustrations into icons.
- The controller-prompt atlas contains exactly 12 distinct authored icons: Stick, D-pad, A, B, L, R, Z, C-Up, C-Down, C-Left, C-Right, and Start. Vertical camera prompts show the chord `L + C-Up` or `L + C-Down`; bare `C-Down` remains the Field Relay action. A locked prompt may not fall back to text, a generic C-button cluster, an ambiguous chord, or an uncatalogued glyph.
- Affinity icons are original physical motifs, not elemental franchise symbols. Each differs in silhouette and luminance as well as color.
- Battle feedback uses exact labels `STRONG — 1.5× affinity force` and `RESISTED — 0.75× affinity force`; neutral actions show neither label. Color and impact scale support the text but never replace it.
- A move with nonzero priority shows an authored arrow-over-order-bar glyph plus exact text `PRIORITY +1` in move information and the predicted queue. Priority tiers resolve before Speed, while Speed orders matching tiers; no priority may be hidden from the player.
- `STAGGERED` uses one off-beat pendulum icon and broken timing ticks. Power, Guard, and Speed use signed stage chevrons with the stat glyph; Guiding Draft may show `EMPOWERED` as a one-use modifier ribbon. None of those volatile modifiers is drawn or described as a separate status ailment.
- Resonance is always a three-node braided pulse; Fracture is a broken offset echo of that geometry.
- Name entry must make selection, backspace, 1–8 character limit, default `ARI`, confirmation, and cancel protection legible without relying on explanatory prose.
- One reusable settings surface serves both title and pause shells, with the shell providing navigation ownership and `ui.screen.settings` providing text speed, invert X/Y, music/SFX volume, rumble, X/Y overscan, UI contrast, live preview, defaults, apply, and cancel states. Title Apply always updates only the sanitized process-resident profile and never claims EEPROM persistence, even when Continue is available. New Game copies that profile into its first campaign page; Continue overlays it after decode and honestly begins DIRTY if any of the eight settings bytes differ. Only Pause Apply from stable initialized gameplay performs an atomic sanitized settings-only journal update. The visual treatment must distinguish changed, profile-applied, campaign-saved, cancelled, defaulted, writing, failed, retried, dirty-overlay, and invalid-recovered values without implying that story progress or EEPROM changed at Title.
- Dialogue allows no more than three lines at once; wrap rules are deterministic and reviewed with the longest authored line and an eight-character player name.
- No fake text appears on in-world screens. If text cannot be readable, use intentional diagrams, bars, and catalogued glyphs.

The approved opening slate is a finished presentation, not a debug card: dusk-ochre horizon, dark-teal Solace carrier-line motif, one controlled violet edge pulse, centered exact `INSERT CUTSCENE HERE`, and bottom-safe `{A} / {START} SKIP`. Natural playback is exactly 106 presentation ticks at 30 Hz: 8-frame fade-in, 90-frame fully visible hold (3.0 seconds), and 8-frame fade-out. A valid skip exits immediately through the same finalizer. Slate art and sound release after a render fence; no input edge leaks into name entry.

## 12. VFX language

VFX use a four-beat grammar: anticipation cue, directed travel or build, one clear impact frame, and rapid readable recovery. Every effect must reveal source, target, and result.

- Physical hits: two to six directional shards or strokes, warm contact core, short dust or material response.
- Support actions: inward or upward motion around the beneficiary; never reuse hostile outward spikes.
- Resonance gain: mint pulses travel from both partners toward the shared meter. Full Resonance adds gold only at completion.
- Duo finisher: each partner contributes a distinct shape; shapes braid into the three-node motif before impact. It requires a bespoke camera and must not obscure HP results.
- Fracture: offset duplicate edges, narrow violet ribbons, one cold core, and temporal hitch. Avoid generic smoke spheres.
- Loading/travel: three relay lobes chase along a short path; animation reflects actual loading and never extends a wait artificially.
- Environment: dust motes and gusts are sparse and depth-layered. Fountain/energy devices follow mechanical emitters rather than random particle fountains.

Default caps: 96 particles exploration, 128 battle, 24 per ordinary move burst, 64 for the duo finisher, and 48 for the closing Fracture hook. Prefer pooled camera-facing quads and short strips. Effects must terminate, release their pools, and remain intelligible with transparency disabled in a diagnostic capture.

## 13. Animation principles and coverage

Animation is pose-first. At 30 FPS, every authored performance needs a readable silhouette at anticipation, contact/decision, and recovery. Do not rely on sub-pixel motion.

Principles:

- Anticipation changes center of mass or dominant silhouette, not just limb rotation.
- Impact gets a brief hold or sharply changed spacing; camera and audio support it without replacing it.
- Recovery returns through a living pose, not a linear blend into bind pose.
- Secondary motion is one beat late and limited to meaningful cloth, vane, filament, or tool parts.
- Idle personality is asymmetrical and interruptible. Breathing alone is not sufficient for named heroes or Echoforms.
- Feet plant through explicit contacts. Locomotion speed is calibrated to world displacement; foot sliding over 2 source pixels in a stable shot fails review.
- Gesture loops avoid identical synchronized hands. Dialogue gestures include listen and settle poses, not continuous waving.
- Hit and knockout preserve anatomy and ground contact. No mesh penetrates the floor or folds through its own torso.

The shared `anm.humanoid.base` bank owns 12 explicit clips: idle A/B, walk, run, start, stop, turn left/right, interact, talk-neutral, listen, and reaction. Scene-specific banks add the required job/story action; the player additionally needs relay-use, door/elevator, battle command, victory/relief, and companion acknowledgment. Named NPCs receive at least two bespoke dialogue gestures and their scene performance. Supporting NPCs may share a compatible base rig, but their idle timing and job action must differ.

Minimum Echoform coverage per design: idle A/B, entrance, locomotion/reposition, two distinct attack performances, support performance, hit, knockout, victory, and duo-finisher participation where applicable. The four moves may invoke an intentional animation family only when direction, contact event, and anatomy remain correct. Estate enemies need clear support-interaction staging.

Camera animation cannot hide missing actor animation. Each cinematic beat must still read from a locked diagnostic camera.

## 14. Audio art direction

Audio shares the world’s material contrast. Meridian uses dry hand percussion, muted plucks, relay chirps, fan beds, and warm analog hum. Veyra adds unstable clockwork, glassy resonators, bowed metal, and playful counter-rhythms. Resonance is consonant and braided; Fracture introduces reversed attacks, beating intervals, and momentary missing ambience rather than merely turning everything louder.

- Deliver runtime-appropriate mono sources, generally near 22.05 kHz where suitable, with loop points and head/tail silence documented.
- Creature vocals originate from each Echoform’s physical design: cavity, vane, plate, filament, or drum. Do not use stock animal roars as final identity.
- UI feedback is short, pitch-bounded, and differentiated for move, confirm, cancel, invalid, full Resonance, save, and message.
- Every move has a source cue, travel/build cue when relevant, and impact/result cue. Shared layers are allowed, but the complete event must remain identifiable.
- Music must leave frequency and rhythmic space for battle commands and dialogue text. No copyrighted reference music or imitation themes.

## 15. Objective rejection and rebuild criteria

The machine gate decision is `fail` for every non-pass. Its separate disposition is `revise` for local defects or `rebuild` when the underlying design or construction cannot survive polishing; completion decisions use disposition `NONE`.

An asset is automatically rejected from production if any of these are true:

- Its black silhouette cannot be identified against two roster peers at 64×64.
- A protected reference is recognizable through name, outline, costume, UI composition, animation, or surface pattern.
- The asset exceeds its hard triangle, material, texture, joint, resident-memory, or particle cap without an approved measured exception.
- Normals, UV seams, weights, transforms, origin, scale, or conversion warnings remain unexplained.
- A hero asset looks finished from only one angle or loses its identity below 48 pixels tall.
- Skin collapses, joints candy-wrap, feet slide, props detach, or cloth/body parts clip during a required animation.
- Generated anatomy, gibberish, repeating artifacts, baked lighting, identity drift, or impossible perspective remains visible.
- Required UI crosses the CRT-safe area, required text is unreadable, or state depends on color alone.
- VFX obscures target/result, audio masks feedback, or any timed effect remains active after state exit.
- In-engine integration misses 30 FPS, breaks the 512 KiB free-heap floor, creates unexplained converter output, or leaks across transition loops.
- The asset has no provenance, ambiguous rights, missing source, or no review evidence.
- Reviewers find a placeholder, default material, primitive-only solution, generic stock motion, or incomplete unseen face in the accepted build.

Rebuild rather than patch when two or more of silhouette, proportion, topology flow, rig architecture, or UV strategy fail; when more than 20% of visible geometry requires repair; when identity differs between approved concept and model; or when two post-integration polish passes do not resolve the same critical defect.

## 16. Seven art gates

No gate may be marked pass from prose alone. Evidence locations and reviewer names are mandatory. Detailed forms live in `docs/ASSET_REVIEW_TEMPLATES.md`.

### 16.1 Production-ID scope, review profiles, and polish tiers

A **production ID** is any canonical inventory ID that owns editable source, generated runtime or user-delivery output, or a distinct authored behavior. The exact eight runtime delivery aliases (`present.*`) and evidence-control IDs (`ev.*`) are not production IDs; they cannot own a source, status, license, gate pass, or independent ledger row. Any BOM alias carries only its exact ordered `alias_of` owners and `payload_bytes=0`; every byte/source/provenance/rights/gate/evidence field is `NONE`, and it contributes no payload/count/deduplication input. Generated children remain production IDs when they add authored payload, but their review may reference a parent only through the `CHILD7` rules below.

Every production ID receives exactly seven ordered decisions for the same revision. “Major” changes review depth, not whether gates exist. The deterministic profile and tier registry is in `docs/ASSET_INVENTORY.md`:

- `H2`: hero asset; all seven decisions plus two separately evidenced polish passes after first Gate 6 appearance.
- `M7`: major asset; all seven decisions with full category overlay.
- `S7`: standard production asset; all seven decisions with size-appropriate evidence.
- `C7`: generated child; all seven child decisions are real `pass` decisions. Parent/revision linkage supplies context but never substitutes `INHERITED_CHILD_EQ` for an authored tuple, generated output, consumer behavior, or any whole gate.
- `D7`: non-ROM user deliverable such as a storyboard item; all seven delivery-equivalent decisions.
- `A0`: non-owning delivery alias; zero independent decisions and exact `alias_of` linkage.
- `E0`: evidence/control record; zero art decisions and exact subject linkage.

The review profile supplies the evidence meaning for each gate:

| Review profile | Gate 1 | Gate 2 source-technical equivalent | Gate 3 representative equivalent | Gate 4 motion/state equivalent | Gate 5 conversion/package equivalent | Gate 6 real-context equivalent | Gate 7 |
|---|---|---|---|---|---|---|---|
| `RIGGED_MODEL` | construction/originality | Blender topology, UV, scale, rig | neutral/game-light turntable | full clip/deformation reel | Tiny3D conversion | gameplay/Ares | final lineup/consistency |
| `STATIC_MODEL_ENV` | construction/originality | Blender topology, UV, scale, collision boundaries | all-angle/route/ceiling material review | `STATIC_STATE_EQ`: mechanisms, interaction, re-entry, culling, and no-motion proof | Tiny3D conversion | gameplay/Ares route/performance | final location/prop consistency |
| `UI_FONT_IMAGE` | visual brief/originality/glyph scope | layered/vector/font source integrity, atlas bounds, palettes | all states at native/overscan/contrast | cursor, transition, wrap, rapid-input, or `STATIC_STATE_EQ` state coverage | deterministic runtime atlas/font conversion | real Ares surfaces | complete UI-system consistency |
| `VFX` | effect brief/originality | source sprites/strips/material/event sockets | neutral and representative four-beat sheet | timed event/cleanup/audio sync | deterministic runtime conversion | max-load Ares action | move/family consistency |
| `AUDIO` | cue brief/originality/rights | lossless/editable session, transformations, channel/rate plan | isolated waveform/listen and representative mix | loop/event/latency/interrupt timing | deterministic runtime audio conversion | real scene/battle mix and residency | complete motif/mix consistency |
| `ANIMATION` | performance brief | source rig/clip/event integrity | locked-camera pose/contact sheet | complete clip/state/skip reel | deterministic converted clip inventory | real actor/camera/Ares playback | cast/action consistency |
| `DATA_SPATIAL` | functional brief/ownership | authored source schema, bounds, naming, deterministic validator | diagnostic overlay/readable route or generated-record inspection | transition/re-entry/failure-state tests (`STATIC_STATE_EQ` when truly static) | deterministic generated binary/BOM | Ares collision/nav/camera/resource behavior | integrated scene consistency |
| `STORYBOARD` | shot/originality/continuity brief | layered/generation source, prompt, edits, dimensions | approved high-resolution panel/continuity comparison | sequence timing, screen direction, animatability | `NON_ROM_DELIVERY_EQ`: deterministic numbered export/contact-sheet/package hashes | `NON_ROM_DELIVERY_EQ`: 320x240 downsample, CRT-safe and complete-sequence review | delivered package continuity |
| `GENERATED_CHILD` | parent/payload purpose | exact authored source row/schema | decoded diagnostic representation | bounds/state/failure tests | deterministic child generation/hash | parent context or host/Ares consumer proof | parent/child/BOM consistency |

Bare `N/A`, a blank gate, or a gate copied from a different revision is a failure. The only allowed substitute codes are `STATIC_STATE_EQ`, `NON_ROM_DELIVERY_EQ`, and `INHERITED_CHILD_EQ`; each still requires the named alternative evidence, reviewer, decision, source/output hashes, and evidence-manifest hash. `INHERITED_CHILD_EQ` is legal only for a child aspect that is byte-for-byte supplied by its reviewed parent; authored child data and its consumer behavior are never inherited.

### 16.2 Reviewer independence and immutable evidence

- The asset owner/creator cannot approve their own Gate 1, 3, 6, or 7 decision for an `H2` asset. At least one non-owner reviewer is required for every `M7`/`S7` Gate 7 decision.
- Every `C7` and `D7` Gate 7 decision also requires a named non-owner reviewer. The author of a generated data tuple cannot be its sole parent/consumer verifier, and the generator/operator/editor of a storyboard delivery cannot approve its own final package.
- Art, technical, and gameplay/readability benchmark reviewers are three distinct named identities; none may be the sole creator of the benchmark package they approve. A reviewer may report a defect in any domain, but cannot replace a missing specialist sign-off.
- Each gate owns `review/<asset_id>/g<gate>/EVIDENCE_MANIFEST.sha256` in the exact section-16.3 format. The gate review records the manifest path and SHA-256 but is not a member of that manifest when it records that hash. Unlisted, changed, inaccessible, post-processed, cyclic, or non-recomputable evidence is no evidence.
- Review evidence must be retrievable from the reviewed commit as an ordinary Git blob or a canonical Git LFS object. Art-review evidence may not be represented by a URL/locator file or fetched from a release: a hashed locator proves only the locator text, not the claimed media. A local path alone cannot support a pass.
- Reference calibration records observations and source URL/version without committing protected reference frames. Reviewers compare care, density, atmosphere, animation coverage, and presentation; they do not trace or reproduce protected expression.

### 16.3 Canonical evidence-manifest format

Every `EVIDENCE_MANIFEST.sha256` and the benchmark `PAYLOAD_MANIFEST.sha256` uses UTF-8 without BOM, LF line endings, and exactly one final LF. Blank lines and comments are forbidden. Each member is one line with exactly six literal TAB-delimited fields and no escaping:

```text
<repo_relative_path>\t<byte_count>\t<sha256>\tbuild:<build_id_or_->\tcapture:<capture_id_or_->\trole:<role>
```

- `repo_relative_path` is the exact repository-relative portable POSIX path to one regular file. It uses only ASCII letters, digits, `_`, `-`, `.`, and `/`; begins with an alphanumeric character except for the sole payload-owned workflow form `.github/workflows/<portable-name>.yml`; and contains no leading `/`, `./`, empty component, trailing `/`, backslash, NUL, TAB, CR/LF, or component equal to `.` or `..`. That leading-dot exception is legal only for the public build workflow owned directly by the benchmark payload; production source/output/evidence manifests cannot use it.
- `byte_count` is canonical unsigned decimal matching `0|[1-9][0-9]*`. `sha256` is exactly 64 lowercase hexadecimal characters and is computed over the materialized member bytes. An ordinary Git blob must byte-equal the materialized file. A Git LFS member's committed blob must be the exact three-line canonical pointer (`version https://git-lfs.github.com/spec/v1`, `oid sha256:<64-lowercase-hex>`, `size <canonical-decimal>`); its `filter` attribute must be `lfs`, and pointer OID/size, materialized bytes, manifest count/hash, and the object fetched by a credential-free fresh public clone must all agree.
- `build_id_or_-` and `capture_id_or_-` are either `-` or a 1–96-character token matching `[A-Za-z0-9][A-Za-z0-9._-]*`. Use `-` only when the role truly has no build/capture identity. `role` is a 1–64-character semantic token matching `[a-z][a-z0-9._-]*`; generic values such as `file` or `misc` are invalid.
- Lines sort strictly ascending by the raw UTF-8 bytes of `repo_relative_path`. Each path appears once. Across the complete parent/subordinate graph, a path has exactly one owning manifest, each non-`-` capture ID identifies exactly one member, and a materialized content hash identifies exactly one member. Case-fold collisions, Unicode-equivalent collisions, repeated direct/nested ownership, duplicate byte hashes presented as different captures, and paths whose real casing differs from Git are failures; reuse is by reference to the one canonical owner, never duplicate membership.
- Every path component resolves without symlinks; the final member is a regular file, not a directory, device, socket, Git submodule, or symlink. The verifier rejects any resolved path outside the repository even if textual normalization appeared safe.
- A manifest never lists itself. Manifest membership forms a directed acyclic graph: a member manifest or record may not directly or transitively hash, embed the digest of, or require the manifest that contains it. A review/control record that stores a manifest hash is therefore outside that manifest. Duplicate membership through nested manifests is always rejected; there is no parent-index override.
- When a manifest path/hash is populated, a gate decision claims `pass`/an allowed equivalent, or the benchmark claims `APPROVED`, verification must open every conditional member from the reviewed commit, materialize Git LFS where declared, recompute byte count and SHA-256, validate every token/path/sort/ownership rule, and recompute the manifest file's own SHA-256. Missing Git LFS tooling/object retrieval, paths, or hashes fail closed. `PENDING` may omit a not-yet-created manifest, but a populated path/hash is never trusted without recomputation. `REMOTE_OBJECT`, URL, release-locator, and equivalent indirection roles are forbidden in evidence manifests.

### 16.4 Canonical benchmark registries and gate records

All TSV files below are UTF-8 without BOM, LF-only, exactly one final LF, no blank/comment lines, literal TAB separators, and no escaping. Header spelling/order is exact. Paths use section 16.3 safety rules. Every populated record/manifest path and digest is resolved from the reviewed payload commit; ordinary Git blobs byte-equal the materialized file and LFS pointers materialize under the rules above.

`review/benchmark/WHITELIST_GATE_REGISTRY.tsv` has this exact 23-field header and exactly 52 following rows in `WB-001..WB-052`/control-whitelist order:

```text
basis\tproduction_id\tsubset_sha256\tauthorization_path\tauthorization_sha256\tgate_record_path\tgate_record_sha256\tprovenance_path\tprovenance_sha256\tsource_manifest_path\tsource_manifest_sha256\toutput_manifest_path\toutput_manifest_sha256\tbuild_id\tstate\trepair_ids\tg1\tg2\tg3\tg4\tg5\tg6\tg7
```

`subset_sha256` hashes the exact UTF-8 bytes of that production ID's `Allowed final source subset before approval` Markdown cell after removing only its outer whitespace. The control table is the exact projection of basis/ID and the three record path@digest pairs, source/output manifest path@digest, and state; no digest-only source/output locator is valid. For production ID `<id>` with first-dot prefix `<prefix>`, active rows use exact owner paths `review/<id>/g1/AUTHORIZATION.md`, `review/<id>/g1/GATE_RECORD.tsv`, `review/<id>/g1/PROVENANCE.md`, `assets-src/<prefix>/<id>/SOURCE_MANIFEST.sha256`, and either `NONE/NONE` or `review/<id>/g5/OUTPUT_MANIFEST.sha256`. Gate row `G<n>` binds exact `review/<id>/g<n>/EVIDENCE_MANIFEST.sha256` and `review/<id>/g<n>/REVIEW.md`. `INACTIVE` uses `PENDING` for all path/hash/build/gate fields and `NONE` repair IDs. `AUTHORIZED` uses populated canonical records/manifests, `NONE/NONE` output only before conversion, `NONE` repair IDs, and seven ordered decisions matching the gate record. `REPAIR_ONLY` is legal only for the exact sorted comma-separated `WB-###:G#:DEFECT-ID` return set under `REVIEW_REQUIRED`/`BLOCKED`. Under `APPROVED`, every row is `AUTHORIZED`, every output path/digest is populated, and `g1..g7` are completion decisions.

Schema-Version 4 makes repair history mechanical. Initial `PENDING` and current `APPROVED` store `NONE` in all six prior-approved baseline identity fields. `REVIEW_REQUIRED`/`BLOCKED` jointly populate the prior signed tag ref/object ID/control commit/payload commit/payload-manifest digest/whitelist-registry digest. The validator reopens that exact public-origin tag in a credential-free clone, verifies the pinned ED25519 signature and prior `APPROVED/UNLOCKED` control/payload/52-row registry, preserves every unaffected control and TSV row byte-for-byte, permits only returned bases to become `REPAIR_ONLY`, freezes their stable owner/subset/path projection, and requires a return token for each changed gate. Unsigned remembered state cannot preserve or broaden authorization.

The selected baseline must also be the unique ancestry-maximal pinned-key-valid public approval-tag target reachable from current public HEAD. A newer reachable approval makes an older selection invalid; incomparable maximal approvals fail as ambiguous. This deterministic dominance rule prevents signed rollback.

Every `GATE_RECORD.tsv` has this exact 16-field header and exactly seven following rows in `G1..G7` order:

```text
scope_id\tprofile\ttier\tgate\tdecision\treviewer_id\treviewer_non_owner\tsource_manifest_sha256\toutput_manifest_sha256\tevidence_manifest_path\tevidence_manifest_sha256\treview_record_path\treview_record_sha256\tbuild_id\tdecided_at\tdefect_ids
```

The scope/profile/tier must resolve to the inventory/whitelist subset or one of four named benchmark rollups. Decisions are exactly `PENDING`, `pass`, `STATIC_STATE_EQ`, `NON_ROM_DELIVERY_EQ`, `INHERITED_CHILD_EQ`, or `fail`. A completed decision binds a canonical reviewer ID, the reviewed source hash, recomputed evidence and review records, build identity (`-` only where genuinely pre-build), RFC-3339 time, and `NONE` defects for a completion pass. Production-asset Gates 1–4 bind output `NONE`; Gates 5–7 bind the current output hash. Benchmark rollups bind the current whitelist-registry digest in both source/output fields at all seven gates. Required non-owner decisions say `YES`. A `PENDING` row uses literal `PENDING` in every remaining field. A file containing an arbitrary digest or fewer than seven parsed decisions is not a gate record.

Hashed Markdown records are machine records, not arbitrary prose. They are UTF-8/BOM-free/LF-only, exactly one final LF, and contain the following lowercase keys in exact order as `key: nonempty-value`, one per line:

```text
# AUTHORIZATION.md
schema, basis, production_id, subset_sha256, subset_allowlist, state, repair_ids, build_id, source_manifest, output_manifest, gate_record, authorizer_id, authorized_at
# PROVENANCE.md
schema, production_id, subset_sha256, subset_allowlist, creator_id, rights_holder_id, source_manifest, output_manifest, rights_basis, rights_evidence, transformations_sha256, output_license
# completed g<n>/REVIEW.md
schema, scope_id, gate, decision, reviewer_id, reviewer_non_owner, source_manifest_sha256, output_manifest_sha256, evidence_manifest, build_id, decided_at, defect_ids, disposition, rationale
# in-progress concept g1/REVIEW.md
schema, production_id, stage, creator_id, source_manifest, evidence_manifest, status, updated_at, rationale
# RIGHTS.md (or the bound ordinary rights-evidence record)
schema, subject_id, rights_basis, rights_holder_id, output_license, evidence_kind, input_records, third_party_notices, reviewer_id, verified_at
# TRANSFORMATIONS.md
schema, subject_id, input_sha256, operation_count, operations, editor_id, recorded_at
# generated GENERATION_PROMPT.txt
schema, child_id, generation_tool, generation_version, prompt_sha256, prompt_text, author_id, created_at
# ordinary source.generated record
schema, production_id, selected_output_path, selected_output_sha256, model_product, model_version, positive_prompt, negative_constraints, seed_or_job, author_id, generated_at, human_edit_summary
```

Schemas are respectively `n64game-authorization-v1`, `n64game-provenance-v1`, `n64game-gate-review-v1`, `n64game-concept-review-v1`, `n64game-rights-evidence-v1`, `n64game-transformations-v1`, `n64game-generation-prompt-v1`, and `n64game-generated-source-v1`. Authorization mirrors its WB row and uses a canonical non-owner authorizer/time. Provenance mirrors production/subset/source/output and the ledger creator/rightsholder. Each input rights basis is independently exactly one of `project-original`, `commissioned-work-for-hire`, `licensed-commercial`, `licensed-cc0-1.0`, `licensed-cc-by-4.0`, `public-domain-dedication`, `generated-provider-terms`, or explicit `generated-self-owned`; its paired input license is exactly `project-proprietary`, `work-for-hire-assignment`, `commercial-custom`, `cc0-1.0`, `cc-by-4.0`, `public-domain`, `provider-terms`, or `self-owned-generator`. The corresponding evidence kinds are `PROJECT_ORIGINAL`, `WORK_FOR_HIRE`, `LICENSE`, `PUBLIC_DOMAIN`, `GENERATIVE_TERMS`, and `SELF_OWNED_GENERATOR`. When all input records share one basis the aggregate provenance basis equals it; more than one distinct basis requires exact aggregate `mixed-cleared-inputs` and evidence kind `MIXED`. Output license is independently exactly one of `project-all-rights-reserved`, `licensed-commercial-output`, `provider-terms-output`, `spdx-cc0-1.0`, `spdx-cc-by-4.0`, or `mixed-cleared-output`. The rights record repeats the subject/basis/rightsholder/output license and uses a canonical independent reviewer plus strictly calendar-valid RFC-3339 time.

Input basis and output license are a compatibility rule, not two unrelated labels: `project-original` permits project-all-rights-reserved/CC0/CC-BY; work-for-hire permits project-all-rights-reserved; commercial input permits only licensed-commercial-output; CC0 and public-domain input permit CC0 or project-all-rights-reserved; CC-BY input permits only CC-BY; provider-generated input permits only provider-terms-output; explicit self-owned-generator input permits project-all-rights-reserved/CC0/CC-BY; and mixed inputs permit only mixed-cleared-output. The validator rejects license laundering even when both tokens are individually spelled correctly.

`input_records` is `NO_EXTERNAL_INPUT` only for a project-original subject with no transformable source member. Otherwise it contains one semicolon-delimited record for every and only every transformable source member, byte-sorted by path. Each record has exactly nine pipe-delimited fields: `source_path@sha256|acquired_at|purpose-token|rights-basis|input-license|terms-version|permission-evidence|attribution-evidence|clean-room-evidence`. Source path/hash must equal the owned member; acquisition time is strict RFC 3339; each record's independent basis/license match the closed mapping; terms version is canonical. Project-original permission is `NONE`; every other per-input basis, including `generated-self-owned`, binds separate substantive ordinary-Git support bytes proving the license/terms or ownership of the generator. Attribution and clean-room fields are either `NONE` or such a binding, except `licensed-cc-by-4.0` always requires explicit attribution evidence. Every aggregate containing non-original input also binds `third_party_notices`. All support paths live below canonical `rights-support/`, use exact manifest role `rights.support`, are payload/source owned, are at least 64 substantive bytes with nontrivial byte variety, and cannot masquerade as transformed content. Generated-child inputs cover exact `docs/DATA_SCHEMAS.md@<source-revision-sha256>`; their support root is `review/generated/<child>/g1/rights-support/`.

`TRANSFORMATIONS.md` binds the subject and either one exact source-owned input digest whose manifest role is closed to `source.authored`, `source.generated`, `source.recording`, or `source.data`, or `NO_MEDIA_INPUT` only for `project-original` when no member with one of those transformable roles exists. The source closure is fully partitioned: the bound rights record is exactly `rights.record`, canonical `TRANSFORMATIONS.md` is `metadata.transformations`, every dedicated support byte is `rights.support`, every ordinary generated-source record is `generation.record`, every nested manifest is `source.manifest`, and every other member must use one of the four transformable roles. Arbitrary roles such as `source.reference` or `metadata.foo` cannot hide a real input from rights/transform coverage. Rights records, license/terms support, manifests, generation records, and other metadata cannot masquerade as the transformed input. It records 1–64 operations as an exact comma-separated ordered sequence `1:<canonical-token>,2:<canonical-token>,...`, with matching count, canonical editor, and RFC-3339 time. Operation tokens are closed to `generate`, `select`, `paintover`, `anatomy-repair`, `topology`, `uv`, `rig`, `retime`, `resample`, `denoise`, `synthesis`, `font-construction`, `palette-convert`, `format-convert`, `reject-remove`, and `deterministic-convert`.

Every ordinary `source.generated` member has exactly one source-owned `generation.record` at `assets-src/<prefix>/<id>/generation/<first-16-hex-of-sha256(source-path)>.md`; no extra generation record is allowed. Its per-input rights basis must be `generated-provider-terms`, unless it uses the explicit `generated-self-owned` basis with substantive source-owned generator-ownership support; generic `project-original` is forbidden for `source.generated`. The record repeats the exact production ID and selected source path/hash, model product/version, canonical creator, and strict generation time; stores a 40–8000-character positive prompt, 20–4000-character negative constraints, exposed seed/job token or exact `NOT_EXPOSED`, and either `NO_HUMAN_EDITS` or a substantive 20–2000-character human-edit summary. This applies to GPT-image storyboard/cutscene work and every other generated media source, not only deterministic camera children. A generated camera child instead uses its separately defined prompt record, binds `input_sha256` exactly to its committed `DATA_SCHEMAS.md` source-revision digest, repeats child/tool/version/creator/time, contains 40–1000 substantive one-line instruction characters, and recomputes `prompt_sha256` from exact `prompt_text` bytes. Provenance binds the rights and transformation records; a concept uses `sha256("CONCEPT_ONLY")` as its non-whitelist scope digest. A completed review mirrors its exact gate-record row and evidence path/hash; `pass`/equivalents require disposition `NONE`, while `fail` requires `revise` or `rebuild`, and rationale is 12–500 characters. Concept review uses `G1_CONCEPT`, `IN_PROGRESS`, canonical creator, current source/evidence bindings, RFC-3339 update time, and nonempty rationale. A digest over unparsed, empty, one-byte, vague-token, self-citing, or mismatching bytes fails.

The exact ordered 15 camera tuples are sealed twice: the 15 `DATA_SCHEMAS.md` source-row bytes hash to `7d176cacd076ffbf8dfb092103b6f82d4e4f5a5b658a822b8072c350410c3100`, and the concatenated 15 little-independent, big-endian-field `CameraShotResourceDef` payloads are exactly `15 * 36 = 540` bytes with SHA-256 `b26a6697e47daf2787ab513b13dc36ac6bd79b43d895b0b21773228d39d28cde`. The ledger's corresponding 15 initial child rows retain their separate byte seal. Validation parses and packs every numeric target/framing/eye/look/FOV/blend tuple; even changing `ASSET_CAMERA_SHOT_UI_NONE` eye from `0,0,0` to `1,0,0` fails the payload seal.

Every active whitelist authorization and provenance record shares one exact `subset_allowlist` binding at `review/<id>/g1/SUBSET_EXPORT_ALLOWLIST.tsv@<sha256>`; a non-authorized Gate-1 concept uses literal `NONE`. That ordinary-Git file is a direct payload-manifest member with this exact seven-field header:

```text
production_id\tsubset_sha256\tstage\tmember_path\tmember_sha256\tmanifest_role\texport_selectors_csv
```

It contains exactly one sorted `SOURCE` or `OUTPUT` row for every transitive source/output-manifest member, with matching production/subset/path/digest/role. The last field is a nonempty, byte-sorted, duplicate-free comma list. Output members use exactly `OUTPUT:runtime`; the rights-evidence member uses exactly `METADATA:rights`; every `rights.support` member uses exactly `METADATA:rights_support`; every `generation.record` uses exactly `METADATA:generation`; and the required canonical transformation file uses exactly `METADATA:transformations`. Every other complete-package source member uses exactly `ALL`. Every partial-package content member forbids `ALL` and uses only the validator-frozen per-production vocabulary in typed grammar `<COLLECTION|CLIP|STATE|SECTOR|CUE|ASSET>:<lowercase-portable-token>`; the union across its content rows must equal that vocabulary with no missing or added selector. `PENDING`, `NONE`, missing/extra members, opaque hashed prose, or a selector file not parsed against the manifests fails. Gate 2 verifies each selector against the named Blender collection/clip, audio cue, state, or sector, and Gate 5 runs the deterministic exporter from this allowlist; a shared `.blend`, audio project, or authoring session may not export an unlisted sibling merely because the whole source file is hashed.

An `H2` scope may complete Gate 7 only when its Gate-7 evidence manifest owns exactly one `polish.first_in_engine` baseline at canonical `.../g7/FIRST_IN_ENGINE.tsv` and one `polish.pass_registry` at canonical `.../g7/POLISH_PASSES.tsv`. The baseline has this exact one-row header:

```text
scope_id\tcommit\tsource_manifest_sha256\toutput_manifest_sha256\tgate_record_path\tgate_record_sha256\tevidence_path\tevidence_sha256\treviewer_id\treviewer_non_owner\tbuild_id\tdecided_at\tdecision
```

The polish registry has this exact header and exactly two ordered rows:

```text
scope_id\tpass_number\tbefore_commit\tafter_commit\tbefore_source_sha256\tafter_source_sha256\tbefore_output_sha256\tafter_output_sha256\tbefore_evidence_path\tbefore_evidence_sha256\tafter_evidence_path\tafter_evidence_sha256\treviewer_id\treviewer_non_owner\tdecided_at\tdefect_ids\tdecision\trationale
```

The baseline is the independently reviewed first-in-engine Gate-6 checkpoint: its public commit, complete historical G1–G6/pass + G7/PENDING gate record, and canonical source/output manifest closures are byte-verified, and its evidence is under `.../g7/polish/first_in_engine/`. Rows are pass `1` then `2`; each names distinct public Git commits in forward ancestry and parses the canonical source/output manifest closures at both revisions, including LFS materialization. Pass 1 begins exactly at the baseline; pass 2 begins at pass 1's result and ends at a strict ancestor of the reviewed payload with the reviewed final hashes. Neither the first-in-engine nor final `after_commit` field may equal the commit that owns the record, preventing an impossible embedded self-OID. The required strict RFC-3339 chronology is baseline < pass 1 < pass 2 < final Gate-6 revalidation < Gate 7. The baseline and every before/after evidence manifest contain exactly `polish.native_capture` at `NATIVE_CAPTURE.mp4` and `polish.phase_report` at `PHASE_REPORT.tsv`; the capture uses globally unique `polish.<scope>.<phase>`, the report uses `-`, and both bind the final build. Every report has exact header `scope_id\tphase\tsource_manifest_sha256\toutput_manifest_sha256\tbuild_id\treviewer_id\treviewer_non_owner\tobserved_at\tcapture_path\tcapture_sha256` and projects its registry phase/hashes/reviewer/time plus the decoded MP4. Each pass has `PASS`, `NONE` defects, a substantive rationale, and a canonical reviewer who is `YES` non-owner. One attractive render, invented hashes, arbitrary evidence roles, unreachable commits, or two labels over the same revision cannot satisfy this gate.

`review/benchmark/BENCHMARK_EVIDENCE_REGISTRY.tsv` has this exact nine-field header and exactly the first 14 `ev.benchmark.*` rows in control order:

```text
evidence_id\tmanifest_path\tmanifest_sha256\trecord_path\trecord_sha256\tmember_count\trequired_roles_csv\tbuild_id\trequired_capture_ids_csv
```

The producer-facing role/capture and metric/role projection is the following exact 14-row table. Each comma-delimited item is `role=capture_id` or `metric=role`; `-` means that the manifest member is an ordinary TSV/report record rather than captured media. The `evidence_record` member is never its own measurement target: aggregate metrics bind the named `*.report` member, whose bytes and digest are independently owned by the evidence manifest.

```text
evidence_id\trole_capture_csv\tmetric_role_csv
ev.benchmark.native\tevidence_record=-,native.attack_anticipation=native_attack_anticipation,native.dialogue=native_dialogue,native.exploration=native_exploration,native.impact=native_impact,native.report=-,native.support=native_support,native.target_selection=native_target_selection\tcapture.attack_anticipation=native.attack_anticipation,capture.dialogue=native.dialogue,capture.exploration=native.exploration,capture.impact=native.impact,capture.support=native.support,capture.target_selection=native.target_selection,capture_count=native.report,color_format=native.report,framebuffer_count=native.report,height_px=native.report,media_type=native.report,width_px=native.report
ev.benchmark.enlarged\tenlarged.attack_anticipation=enlarged_attack_anticipation,enlarged.dialogue=enlarged_dialogue,enlarged.exploration=enlarged_exploration,enlarged.impact=enlarged_impact,enlarged.report=-,enlarged.support=enlarged_support,enlarged.target_selection=enlarged_target_selection,evidence_record=-\tcapture.attack_anticipation=enlarged.attack_anticipation,capture.dialogue=enlarged.dialogue,capture.exploration=enlarged.exploration,capture.impact=enlarged.impact,capture.support=enlarged.support,capture.target_selection=enlarged.target_selection,capture_count=enlarged.report,height_px=enlarged.report,media_type=enlarged.report,resampler=enlarged.report,scale_factor=enlarged.report,width_px=enlarged.report
ev.benchmark.turntable.player\tevidence_record=-,turntable.game_light=player_game_light,turntable.neutral=player_neutral,turntable.sheet=player_turntable_sheet\tgame_light_views=turntable.game_light,neutral_views=turntable.neutral,sheet_count=turntable.sheet
ev.benchmark.turntable.quarrune\tevidence_record=-,turntable.game_light=quarrune_game_light,turntable.neutral=quarrune_neutral,turntable.sheet=quarrune_turntable_sheet\tgame_light_views=turntable.game_light,neutral_views=turntable.neutral,sheet_count=turntable.sheet
ev.benchmark.animation.player\tanimation.contact_sheet=player_animation_contact,animation.reel=player_animation_reel,evidence_record=-\tclip_count=animation.reel,contact_frames=animation.contact_sheet,locked_camera=animation.reel
ev.benchmark.animation.quarrune\tanimation.contact_sheet=quarrune_animation_contact,animation.reel=quarrune_animation_reel,evidence_record=-\tclip_count=animation.reel,contact_frames=animation.contact_sheet,locked_camera=animation.reel
ev.benchmark.environment.corner\tenvironment.camera=corner_camera,environment.ceiling=corner_ceiling,environment.collision=corner_collision,environment.grade=corner_grade,environment.props=corner_props,environment.reverse=corner_reverse,environment.route=corner_route,evidence_record=-\tcamera_overlay=environment.camera,ceiling_views=environment.ceiling,collision_overlay=environment.collision,grade_compare=environment.grade,purposeful_props=environment.props,reverse_views=environment.reverse,route_views=environment.route
ev.benchmark.ui\tevidence_record=-,ui.controller_gallery=ui_controller_gallery,ui.native_gallery=ui_native_gallery,ui.state_matrix=ui_state_matrix\tcontroller_icon_count=ui.controller_gallery,native_gallery_count=ui.native_gallery,state_count=ui.state_matrix
ev.benchmark.vfx_audio\tevidence_record=-,sync.braid=braid_sync,sync.hit=hit_sync,sync.support=support_sync\tbraid_sync_error_ms=sync.braid,hit_sync_error_ms=sync.hit,support_sync_error_ms=sync.support
ev.benchmark.capture_60s\tares.execution_log=-,ares.run_record=-,capture.analysis=-,capture.frame_audit=-,capture.representative=representative_60s,evidence_record=-\tduration_ms=capture.representative,placeholder_frames=capture.representative,sustained_sub30_windows=capture.representative
ev.benchmark.performance\tevidence_record=-,performance.report=-\tdisplay_batches_peak=performance.report,fps_min=performance.report,frame_time_p95_us=performance.report,free_heap_min_bytes=performance.report,particles_peak=performance.report,scene_collision_nav_state_bytes=performance.report,scene_geometry_display_bytes=performance.report,scene_skeleton_animation_bytes=performance.report,scene_textures_bytes=performance.report,scene_vfx_bytes=performance.report,scene_working_set_bytes=performance.report,texture_working_set_bytes=performance.report,unexplained_converter_warnings=performance.report
ev.benchmark.unload_reload\tevidence_record=-,unload.report=-\tbaseline_heap_bytes=unload.report,heap_delta_bytes=unload.report,post_reload_heap_bytes=unload.report,resource_delta_count=unload.report
ev.benchmark.gates\tevidence_record=-,gate.wb001=-,gate.wb002=-,gate.wb003=-,gate.wb004=-,gate.wb005=-,gate.wb006=-,gate.wb007=-,gate.wb008=-,gate.wb009=-,gate.wb010=-,gate.wb011=-,gate.wb012=-,gate.wb013=-,gate.wb014=-,gate.wb015=-,gate.wb016=-,gate.wb017=-,gate.wb018=-,gate.wb019=-,gate.wb020=-,gate.wb021=-,gate.wb022=-,gate.wb023=-,gate.wb024=-,gate.wb025=-,gate.wb026=-,gate.wb027=-,gate.wb028=-,gate.wb029=-,gate.wb030=-,gate.wb031=-,gate.wb032=-,gate.wb033=-,gate.wb034=-,gate.wb035=-,gate.wb036=-,gate.wb037=-,gate.wb038=-,gate.wb039=-,gate.wb040=-,gate.wb041=-,gate.wb042=-,gate.wb043=-,gate.wb044=-,gate.wb045=-,gate.wb046=-,gate.wb047=-,gate.wb048=-,gate.wb049=-,gate.wb050=-,gate.wb051=-,gate.wb052=-,gates.report=-,rollup.player=-,rollup.presentation=-,rollup.quarrune=-,rollup.sector=-\tgate_decisions_complete=gates.report,integrated_rollups=gates.report,whitelist_vectors=gates.report
ev.benchmark.authorship\tauthorship.calibration=-,authorship.rubric=-,evidence_record=-\tprotected_frames_committed=authorship.calibration,reviewer_count=authorship.rubric,rubric_categories=authorship.rubric
```

The five performance-category values (`scene_textures_bytes`, `scene_geometry_display_bytes`, `scene_skeleton_animation_bytes`, `scene_collision_nav_state_bytes`, and `scene_vfx_bytes`) sum exactly to `scene_working_set_bytes`; `texture_working_set_bytes` equals `scene_textures_bytes`, the texture value is at most 336 KiB, and the full scene working set is at most 1100 KiB.

The representative-capture manifest owns six exact roles: the measurement record, native 320x240 MP4, wrapper-produced run record, wrapper execution event log, per-frame audit, and capture analysis. The ordinary-Git one-row Ares run record at canonical `review/benchmark/evidence/capture_60s/ARES_RUN.tsv` has this exact header:

```text
run_id\tbuild_id\trom_sha256\tares_version\tares_revision\tares_binary_sha256\tares_mode\tframebuffer_count\tframebuffer_format\twrapper_path\twrapper_sha256\twrapper_version\tinvocation\tcapture_path\tcapture_sha256\tframe_audit_path\tframe_audit_sha256\tboot_result\texit_code\trun_duration_ms\texecution_log_path\texecution_log_sha256\toperator_id\trecorded_at
```

The per-frame `FRAME_AUDIT.tsv`, exact seven-row `ARES_EXECUTION_EVENTS.tsv`, and one-row `CAPTURE_ANALYSIS.tsv` have these canonical headers:

```text
run_id\tframe_index\tframe_start_us\tframe_time_us\tvideo_rgb_sha256\tplaceholder_mask\tfree_heap_bytes\tdisplay_batches\tparticles\tscene_textures_bytes\tscene_geometry_display_bytes\tscene_skeleton_animation_bytes\tscene_collision_nav_state_bytes\tscene_vfx_bytes\tresource_count\tconverter_warning_count\tevent
run_id\tsequence\tevent\tmonotonic_ns\tchild_pid\targv_sha256\trom_sha256\tcapture_sha256\tframe_audit_sha256\texit_code\tboot_handshake_sha256
schema\tevidence_id\trun_id\tbuild_id\trom_sha256\tares_run_path\tares_run_sha256\tframe_audit_path\tframe_audit_sha256\tcapture_path\tcapture_sha256\tdecoded_frame_count\tfirst_pts_us\tlast_pts_us\tduration_ms\tfps_window_us\tfull_window_count\tfps_min\tsustained_sub30_windows\tplaceholder_frames\tanalyzer_id\tanalyzer_version\tanalyzed_at
```

The event order is exactly `WRAPPER_START`, `CHILD_SPAWN`, `BOOT_READY`, `CAPTURE_START`, `CAPTURE_STOP`, `CHILD_EXIT`, `WRAPPER_FINISH`, with one positive child PID, strictly increasing monotonic nanoseconds, exact invocation/ROM/capture/frame-audit hashes, zero child/final exit, and a substantive handshake hash only on `BOOT_READY`. Thus `boot_result=BOOT_AND_RUN_PASS` is derived from the wrapper-controlled child handshake and exit, not a human checkbox. The run ID is deterministically `ares-` plus the first 16 hex of SHA-256 over `<rom_sha256>:<capture_sha256>`; every frame-audit run ID must match it. Pinned ffmpeg fully decodes the MP4 to RGB24 framehash rows and byte-compares every frame index/start/duration/RGB SHA-256 with the audit before any claim is accepted. Placeholder, FPS-window, frame-time, heap, display-batch, particle, five scene-category, warning, unload, reload, and resource values are recomputed from those matched rows.

The run record binds clean-build ID, exact ROM/capture/audit/execution-log bytes, `ares_version=148`, revision `0aafd85789215e84e1e43415c07d4c88461b7899`, audited Ares executable digest, `Homebrew_Mode`, three `RGBA16` framebuffers, payload-owned `scripts/run-ares@<sha256>`, wrapper version `n64game-ares-wrapper-v1`, exact invocation, canonical independent operator, and strict RFC-3339 time. Approval reruns that reviewed wrapper in a fresh public clone with the exact local ROM, Ares binary, MP4, audit, event log, and run record. It must emit one exact JSON verification receipt binding all six digests; a bare operator attestation cannot pass. Gate 3 pins the audited Ares binary to SHA-256 `7a49f00f96a691458461d7c9cf453d95c0f5c054389bbd87c253987b8b6fa345`. Separately, ordinary validation pins the local-only semantic snapshot manifest `test/fixtures/asset_contract/LIFECYCLE_SNAPSHOT_MANIFEST.sha256` to SHA-256 `a9f2ff50f53f4528c4cfeef1a55f15382ff86f5703b51acf66567af2f57a34b0`. Its executable runner plus populated, approved, repair, generated-child, move-pair, H2, and release JSON snapshots harden exact types, identities, parallel nonchronological topology, and the independent approved-to-repair/approved-to-release cross-bindings. They are synthetic contract snapshots: they never enter the benchmark payload, never invoke the production Ruby validator branches, and the receipt states `NON_APPROVAL_SEMANTIC_SNAPSHOT`. The separately pinned production harness extracts eight normalized lifecycle decisions into `lib/n64game/asset_lifecycle_contract.rb`, calls that exact kernel from the live validator, and byte-binds the public-concept, populated, approved, repair, generated-child, move-pair, H2, and release positive paths plus fail-closed death mutations under the manifest pinned by the validator. Independent audit accepted its callsite coupling, controlled malformed-input behavior, profile/gate matrix, ordinary-Git modes, payload ownership, and isolated fresh-clone execution. GitHub, signed-tag, LFS, media, Ares, and ROM-rebuild truth remain mandatory live adapters; enabling this prerequisite does not make `APPROVED` attainable without the complete real payload and evidence graph.

The native/enlarged, performance, and unload/reload reports use the following exact one-row headers:

```text
schema\tevidence_id\trun_id\tbuild_id\tares_run_path\tares_run_sha256\tcapture_bindings_csv\tcapture_count\twidth_px\theight_px\tmedia_type\tcolor_format\tframebuffer_count\tanalyzer_id\tanalyzer_version\tanalyzed_at
schema\tevidence_id\tnative_bindings_csv\tenlarged_bindings_csv\tcapture_count\twidth_px\theight_px\tmedia_type\tscale_factor\tresampler\tanalyzer_id\tanalyzer_version\tanalyzed_at
schema\tevidence_id\trun_id\tbuild_id\trom_sha256\tares_run_path\tares_run_sha256\tframe_audit_path\tframe_audit_sha256\tframe_first\tframe_last\tsample_count\tfps_window_us\tfps_min\tframe_time_p95_us\tfree_heap_min_bytes\tdisplay_batches_peak\tparticles_peak\tscene_peak_frame\tscene_textures_bytes\tscene_geometry_display_bytes\tscene_skeleton_animation_bytes\tscene_collision_nav_state_bytes\tscene_vfx_bytes\tscene_working_set_bytes\ttexture_working_set_bytes\tunexplained_converter_warnings\tanalyzer_id\tanalyzer_version\tanalyzed_at
schema\tevidence_id\trun_id\tbuild_id\tares_run_path\tares_run_sha256\tframe_audit_path\tframe_audit_sha256\tbaseline_frame\tunload_complete_frame\treload_complete_frame\tbaseline_heap_bytes\tpost_reload_heap_bytes\theap_delta_bytes\tbaseline_resource_count\tpost_reload_resource_count\tresource_delta_count\tanalyzer_id\tanalyzer_version\tanalyzed_at
```

Every report is produced by exact `n64game-evidence-analyzer` version `1.0.0`, at or after the run time. Each of the six native PNG bindings is canonical `native.<name>=<path>@<digest>#frame=<index>#rgb=<sha256>`; the validator decodes its exact 320x240 RGB24 pixels and requires its hash to equal that indexed representative-video frame. Enlarged captures are then recomputed exact 4x nearest-neighbor pixels from those native PNGs. `MEASUREMENTS.tsv` values/units must equal the recomputed report values byte-for-byte; merely pointing a measurement at a hashed report is insufficient.

Each subordinate manifest and measurement record is a payload member. Each evidence record uses exact eight-field rows headed `evidence_id\tmetric\tvalue\tunit\tmember_path\tmember_sha256\tbuild_id\tcapture_id`; required metrics, numeric thresholds, named capture dimensions/format, role/count set, build/capture IDs, and referenced member bytes must validate. Evidence paths are exact `review/benchmark/evidence/<evidence-suffix>/{EVIDENCE_MANIFEST.sha256,MEASUREMENTS.tsv,...}`; rollups use exact `review/benchmark/rollups/<player|quarrune|sector|presentation>/` owners. Native evidence has six distinct 320×240 PNG captures; enlarged evidence has the same six names at 1280×960. Pinned ImageMagick `7.1.2-13` decodes both files and requires every enlarged RGBA pixel to equal the exact 4× point-filter/nearest-neighbor expansion of its named native capture; dimensions and a TSV word alone do not prove this. Pinned `ffprobe 8.1.2` decodes every MP4 and requires H.264 video, positive exact-4:3 dimensions/duration, and average frame rate at least 30 fps. The representative capture's observed duration is at least 60,000 ms and agrees with its TSV value within 50 ms; it and every VFX/audio sync clip have a decodable audio stream. Missing/wrong-version tools, fake `ftyp` headers, decode errors, missing required audio, low frame rate, non-4:3 video, or self-reported-only duration fail closed. These tools run only when the complete evidence registry is populated, so untouched `PENDING` has no media dependency. Performance and heap values are numeric; gate evidence binds 52 seven-vectors plus four rollups; authorship binds nine categories and three reviewers. A `PASS` word without the registry, recomputed members, valid measurements, real media decode, and pixel comparison is failure. Every objective/rubric `Actual/evidence` cell uses sorted comma-separated `ev.benchmark.<id>#<metric>` references that resolve exactly; observations are nonempty.

Production files have one ledger owner. Editable production bytes live only under `assets-src/<production-id-prefix>/<canonical.production.id>/`, with the directory prefix exactly equal to the ID's first segment; gate records, immutable converted-output review snapshots, and evidence live only under `review/<canonical.production.id>/g1` through `g7`. Canonical record/manifest files are owned by their registry locators; every other regular file under those roots must appear in exactly one explicit ledger-linked source/output/evidence manifest. Orphan, ambiguous, alias-owned, traversal, invalid-status, or unauthorized prebenchmark content fails. Declared output manifests uniquely own reviewed Gate-5 snapshots under `review/<canonical.production.id>/g5/`; no `build/` byte may be a public payload member. `APPROVED` parses `docs/ASSET_LEDGER.md` from the reviewed payload commit and scans that commit's fresh-public-clone tree—not the later worktree—so later Gate-5+ ledger/assets cannot erase historical approval while an orphan inside the approved payload still fails. The payload manifest must own those reviewed ledger bytes. Every regular `review/benchmark/` file must belong to the populated payload-manifest graph; when aggregate identity pairs are `PENDING`, there is no regular-file scaffold allowlist.

Pre-approval progression is a derived validator state, never another editable control field. The aggregate mask reads the following eight path/hash pairs in this exact order: payload manifest, whitelist/gate registry, benchmark evidence registry, ROM build recipe, player rollup, Quarrune rollup, benchmark-sector rollup, and integrated-presentation rollup.

| Derived state | Aggregate mask | Exact minimum condition |
|---|---:|---|
| `EMPTY` | `00000000` | no ordinary concept row; no advanced ledger row; all 52 control rows `INACTIVE` with seven `PENDING` gates |
| `PUBLIC_HEAD_CONCEPT` | `00000000` | at least one ordinary concept row, no advanced ledger row, and all 52 control rows `INACTIVE`; the exact clean current `HEAD` is publicly advertised and its concept bytes revalidate from a fresh explicit-ref clone |
| `STAGED_WB` | `11xxxxxx` | payload and whitelist pairs are both populated and at least one whitelist row is `AUTHORIZED` or lawful `REPAIR_ONLY` |
| `APPROVED` | `11111111` | all eight pairs are populated and every approval requirement in this section passes |

The payload and whitelist bits are an inseparable core. Every optional bit implies core `11`. Populating any of the exact eight aggregate path/hash pairs is therefore a public-commit operation, but a lone optional pair or half-populated core is invalid. The recipe bit is independently optional after the core. A workflow may remain `PENDING` with a populated recipe, but a populated workflow always requires the recipe bit. A present rollup's path and digest occupy its exact positional pair, its gate-record digest equals that pair's digest, and its build equals the global clean-build ID. Ordinary active staged rows carry individually canonical build IDs and do not have to equal the global clean-build ID until the evidence bit or approval makes that equality meaningful.

The evidence bit is a completeness claim, not a partial-scaffold flag. It may be `1` only when all 52 whitelist rows are active, all four rollup bits and records are present, and all `392 = (52 + 4) × 7` gate decisions are legal completions. At that point every evidence, whitelist-row, and rollup build binding equals the one global clean-build ID. Payload, whitelist, evidence, recipe, rollup, workflow, record, manifest, and media bytes resolve from the reviewed payload commit through one shared manifest ownership context. Recipe metadata may be structurally validated before approval; only `APPROVED` compares it to local/fresh/public ROM identities.

Every `STAGED_WB` payload/control publication is a two-commit transaction. Commit `P` owns the reviewed payload and is exactly the control's `Reviewed payload Git commit`. Its sole child control commit `A` changes only `docs/VISUAL_BENCHMARK_APPROVAL.md`; equivalently, `A` has exactly one parent, that parent is `P`, and the `P→A` diff contains no other path. The exact clean current public revision must descend from `A`, both commits must be reachable through the verified public authority, the control bytes at `A` must equal the current control bytes, and current `HEAD^{tree}` must equal `A^{tree}` byte-for-byte. Tree equality permits a synthetic pull-request merge commit with the same tree but rejects every later byte change. A control that points sideways to an unrelated public payload commit fails.

For `PUBLIC_HEAD_CONCEPT`, accepted authority is the exact clean current `HEAD` advertised by the canonical public repository at one valid `refs/heads/*`, `refs/pull/<positive>/head`, or `refs/pull/<positive>/merge` ref. The verifier resolves the advertised OID, explicitly fetches that same ref into a no-checkout credential-free fresh clone, and requires the fetched OID still to equal current `HEAD`; a local-only commit, moved ref, tag, implicit default-branch clone, dirty index/worktree, ignored extra, or symlink under `assets-src/` or `review/` fails. All accepted concept bytes come from the fresh clone, never from mutable local bytes.

Lawful Gate-1 exploration uses a manifest-bound `concept` row without authorizing final source. The ordinary concept count excludes the 15 fixed Markdown-only C7 tuple rows. A general media-concept row uses canonical `creator:<id>; rights_holder:<id>` identity and exactly `record:review/<id>/g1/PROVENANCE.md@<sha256>`, `source:assets-src/<prefix>/<id>/SOURCE_MANIFEST.sha256@<sha256>`, `output:NONE`, `concept_evidence:review/<id>/g1/EVIDENCE_MANIFEST.sha256@<sha256>; review:review/<id>/g1/REVIEW.md@<sha256>`, and seven literal `G1=PENDING; ...; G7=PENDING` tokens. The canonical `g1/REVIEW.md` is a direct concept-evidence-manifest member at exact role `concept.review`. Concept ownership is limited to its source members and Gate-1 provenance/review/evidence; it cannot own or hide `AUTHORIZATION.md`, `GATE_RECORD.tsv`, `SUBSET_EXPORT_ALLOWLIST.tsv`, `AUTHORING_STACK_RECEIPT.txt`, any Gate 2–7 file, converted/output bytes, or `build/generated/` content. `planned` owns no files. The 15 original C7 tuples retain only their separately defined no-media exception.

Each benchmark rollup gate record binds its `source_manifest_sha256` and `output_manifest_sha256` fields to the exact whitelist/gate-registry SHA-256, never the parent payload-manifest digest. The registry digest is non-circular and must be populated before a rollup; embedding the parent payload digest in a payload member is forbidden. Postapproval production authority remains section 16.7's clean credential-free public default-`HEAD` rule; accepting branch or pull-request refs for the preapproval concept/staging transaction does not widen that later rule.

A real rejected/revise Gate-1 review does not disappear and does not promote the current row. The current Gate-1 evidence manifest may own exactly one `gate.attempt_history` at canonical `review/<id>/g1/attempts/ATTEMPT_HISTORY.tsv`, capture/build `-`, with at least one row and this exact header:

```text
production_id\tattempt_number\tattempt_id\tattempt_commit\tsource_manifest_path\tsource_manifest_sha256\tevidence_manifest_path\tevidence_manifest_sha256\treview_record_path\treview_record_sha256\treviewer_id\treviewer_non_owner\tdecided_at\tdefect_ids\tdisposition\tprevious_row_sha256
```

Rows are exact `1..N` / `G1-0001..`, each attempt commit is a strict credential-free public ancestor of the current reviewed commit and a strict forward descendant of the preceding attempt, timestamps strictly increase, and `previous_row_sha256` is `NONE` then SHA-256 of the preceding complete TSV data row plus LF. Each row resolves its historical source manifest plus canonical `review/<id>/g1/attempts/%04d/EVIDENCE_MANIFEST.sha256` and `REVIEW.md` at that exact commit. The historical manifest owns the review as exact `gate.attempt_review`, capture/build `-`. The review has ordered keys `schema, production_id, attempt_id, gate, decision, reviewer_id, reviewer_non_owner, source_manifest_sha256, output_manifest_sha256, evidence_manifest, build_id, decided_at, defect_ids, disposition, rationale`, schema `n64game-g1-attempt-review-v1`, `gate: G1`, `decision: fail`, `output_manifest_sha256: NONE`, `build_id: -`, independent canonical reviewer, sorted defects, substantive rationale, and exact `REJECT` or `REVISE`. Before a genuine G1 pass, the live ledger and concept review remain `concept`, `IN_PROGRESS`, output `NONE`, and all seven gates `PENDING`; attempt history does not itself advance G1. After a genuine G1 pass promotes the asset, the same canonical attempt history remains owned by the current G1 evidence manifest and stays append-only across every public parent-child commit edge, including merges. Promotion, downgrade, abandonment, or removal of the current ledger row may not delete, reorder, rewrite, or orphan any rejected attempt; the validator discovers every canonical attempt-history path in the complete reachable public commit graph even when no current row would otherwise request that check.

### 16.5 ROM and public-release attestation

ROM binaries are never Git or Git LFS payload members: every `.z64`, `.n64`, or `.v64` tree entry is forbidden regardless of its path or whether it is bytes or an LFS pointer. `APPROVED` uses one regular non-symlink local `.z64` under an ignored build path; it must be untracked, begin with the big-endian N64 magic bytes `80 37 12 40`, match its recorded size/header/SHA-256, and be reproduced from the reviewed payload in a credential-free fresh public clone using the committed canonical build recipe. The exact public GitHub release tag and asset name are derived from the full payload commit (`n64game-benchmark-<40hex>` and `n64game-<40hex>.z64`) in the same origin repository. Public `refs/tags/n64game-benchmark-<40hex>` must peel/resolve exactly to that payload commit in both origin and the fresh clone. The validator checks public release API identity/workflow/run metadata, streams the unauthenticated release asset through HTTPS redirects, checks its magic, and requires its size/SHA-256/header to equal both local and freshly built ROM bytes. Network, API, tag, build, ignore, magic, or hash uncertainty fails closed.

`review/benchmark/ROM_BUILD_RECIPE.tsv` is ordinary Git text, a payload-manifest member, and has exactly this five-field header plus one data row: `build_id\tmake_target\toutput_path\trom_size_bytes\trom_header_sha256`. `make_target` is one safe build token executed as `make <target>` without a shell; `output_path` equals the ignored local ROM path; size/header equal the control. The recipe does not contain its own commit ID or ROM bytes.

The signed approval tag suffix is the payload commit's first 12 hex. Its in-control evidence row stores only precomputable tag ref, payload commit/digest, pinned signer fingerprint, and external protection record; it never embeds the future tag-object or tag-target OID. The validator resolves those OIDs externally: the local annotated tag object ID must equal the exact public origin ref object ID; its peeled target contains the populated control, the payload commit is its ancestor, and both are reachable from a credential-free fresh public clone of the pushed tag. Gate 2 pins the ED25519 public key and fingerprint `SHA256:8KL8xLkUqqsniUjeU4OaIHXhZYkXOyEOWs/INvJhlB0` in the validator with principal `n64game-release`; verification builds a temporary isolated `allowed_signers` file from that pin. The matching private key remains external/uncommitted and is provisioned to the release operator/CI only for `gpg.format=ssh` tag signing. No configured workstation signing key is needed while `PENDING`, and `APPROVED` fails closed until the external signer creates the tag. A signer typed into the control or a payload-local replacement key cannot authorize itself. Remote-host deletion/force-move protection remains a separately recorded release-operator check and is not inferred from local Git.

1. **Concept and construction:** approved silhouette sheet; front, side, back, and functional three-quarter; scale; palette; material callouts; movement notes; clean-room similarity check.
2. **Blender technical:** measured triangles/materials/joints; topology and normal overlays; UV sheet; transforms/origin; naming; rig and weight stress poses; source provenance.
3. **Textured turntable:** neutral and representative-light turntables from all major angles; native-resolution crops; material and texel-density comparison; no hidden unfinished side.
4. **Animation:** clip inventory; contact/event frames; locked-camera reel; deformation and clipping checks; personality and timing approval.
5. **Tiny3D conversion:** reproducible exporter command/settings; zero unexplained warnings; runtime texture/material/skeleton/animation inventory; converted-size report.
6. **In-engine:** native 320×240 gameplay-camera captures; representative lighting/fog; culling; frame-time, heap, batch, and particle evidence; transition cleanup.
7. **Final consistency:** side-by-side cast/location lineup; art-bible checklist; two documented polish passes for hero assets; provenance complete; final defects zero critical/high/medium.

Gate 6 may send an asset back to any earlier gate. Gate 7 is not a ceremonial sign-off; it rejects assets that are individually attractive but visually incompatible after integration.

## 17. Visual benchmark definition

Mass asset production is blocked until a representative benchmark scene passes. The only final environment slice allowed before that decision is the named, non-ID sub-sector `env.annex.atrium_lower#sector.atrium_lower.sim_threshold_corner`: the simulation-facing corner of the lower atrium bounded by the simulation doorway portal, the first ceramic brace beyond it, the teal service cage, and the traversable floor change. Its final source remains part of `env.annex.atrium_lower`; the other three lower-atrium sectors and every sector of `env.annex.sim_chamber` remain production-locked. The benchmark harness may stage battle footprints/action overlays inside this corner without turning the harness into a shippable extra zone.

The exact pre-approval whitelist and its permitted clip/state/sector subsets live in `docs/VISUAL_BENCHMARK_APPROVAL.md`. A visual/audio inventory item not present in that table may reach `planned` or Gate 1 `concept`, but may not create final production mesh, texture, rig, animation, UI, VFX, audio, converted output, or Gate 2+ evidence before the global benchmark decision is `APPROVED`. Whitelist membership is eligibility, not authorization: each active subset also needs its populated `WB-###` authorization basis, explicit ledger row, Gate 1 pass hash, and current source/output hashes in the control record. `PENDING`, `REVIEW_REQUIRED`, and `BLOCKED` all keep the global lock closed and permit only the state-specific, explicitly authorized benchmark/remediation work defined there. The exact 15 original camera-shot `C7` rows in the ledger are a Markdown-authoring exception at `concept`, not a Gate 1 pass or production `source` status; generated output and Gates 5–7 stay locked. Temporary greybox assets use explicit `tmp.*` development IDs, cannot enter the production ledger, and remain subject to final placeholder removal.

The canonical decision record is `docs/VISUAL_BENCHMARK_APPROVAL.md`. Its `review/benchmark/PAYLOAD_MANIFEST.sha256` covers the 14 substantive `ev.benchmark.*` payload records and explicitly excludes this control file and `ev.benchmark.approval`. The fifteenth evidence record is a signed, non-self-referential annotated origin-tag attestation that points to the commit containing the populated control and attests the separately reviewed payload commit and payload-manifest digest. The release state requires that origin tag to be protected against deletion/force-move, but the local repository validator cannot infer remote-host protection: it checks the annotated object, signature/signer, exact origin ref, exact five-line attested text, and target/control, while the release operator separately confirms the host-side protection rule. Neither the tag nor this control file is a member of the payload-manifest graph, so no file hashes itself directly or transitively.

Approval is valid only when its exact 40-hex reviewed payload commit, build ID, ignored/untracked local ROM path, byte count, recomputed full/header digests, one-row build recipe, successful same-repository public workflow run, derived public release tag/asset URL and downloaded bytes, fresh public-clone rebuild, payload-manifest graph, exact whitelist/gate/evidence registries and digests, canonical gate and measurement records, three distinct canonical non-owner `PASS` reviewer records, all objective/rubric `PASS` rows with exact metric references and observations, `0 / 0 / 0` defects, RFC 3339 decision time, pinned-key signed origin attestation ref, matching final-decision fields, `Production-Lock: UNLOCKED`, and `Decision: APPROVED` verify for one payload revision. The ROM itself is never a Git or Git LFS member. The signed tag target must contain the populated control, the reviewed payload must be its ancestor, local and public tag objects/peeled targets must match exactly, and the release operator must separately record confirmed same-repository remote tag protection. Every one of its 52 whitelist production IDs/subsets receives a literal benchmark-scope seven-decision vector; a partial package is not thereby finally approved, and completing its locked members later reopens affected full-package gates. A source/output change sets `REVIEW_REQUIRED` and clears only affected authorization until hashes are refreshed; a critical/high defect sets `BLOCKED` while preserving unaffected `AUTHORIZED` history. Free-form prose, a screenshot, a mutable tag, stale approval-only fields, a remote locator, or the production checklist alone cannot unlock production.

### 16.7 Post-approval current-production authority

After the signed benchmark approval, historical approval remains authoritative only at its pinned public tag; it is not copied forward as stale mutable authority. Every validation run still rejects any tracked or staged `.z64`, `.n64`, or `.v64`. Current production requires a completely clean worktree/index (including untracked files), local `HEAD` byte-equal to the credential-free public default `HEAD`, and that public head descending from the signed approval-control target. Public clone/fetch/LFS/`ls-remote` operations use canonical HTTPS, an isolated minimal environment, no inherited credential/config/SSH injection, no interactive helper, and fully materialized public bytes.

If current ledger rows and their owned bytes remain exact signed history, the fast path requires full equality of all 15 ledger cells and byte-equality of every still-current referenced asset path; a changed field is never hidden by matching four locators. Historical benchmark controls/evidence remain verifiable at the signed tag and need not remain copied in current `HEAD`; any retained copy must still be byte-identical. Deleted or downgraded historically approved production IDs fail. Once any row or production-root byte changes, current `HEAD` owns direct `docs/ASSET_LEDGER.md` and `docs/ASSET_INVENTORY.md` members through `review/production/PAYLOAD_MANIFEST.sha256`. Every changed/new active package uses subset digest `SHA256("FULL_PRODUCTION")`, provenance `subset_allowlist: NONE`, canonical source/output/provenance/gate paths, lifecycle-valid status/vector, and complete current manifest ownership; former partial-package paths may change only by entering this full revalidation. The production payload contains no workflow member. Exact validated pair proofs and generated-child registries/gates/evidence are the only additional `review/pairs/` and `review/generated/` controls; arbitrary files under `review/production/`, `review/generated/`, `review/pairs/`, or `review/benchmark/` fail. Generated outputs have exactly one declared owner, and all current production roots are scanned from the public commit before success.

The benchmark is one final-quality Annex atrium/simulation-threshold corner containing:

- One room sector with ceramic brace, teal service cage, traversable floor change, warm practical, cool ambient, doorway, signage glyphs, collision, and at least five purposeful props.
- The final player model with exploration idle, walk, run, interaction, and one dialogue gesture.
- One real starter Echoform at final budget with idle A/B, entrance, one attack, one support, hit, knockout, and finisher-participation preview.
- Three fully finished supporting battle-distance Echoform silhouettes—Ayselor, Gyreclast, and Kivarrax—using only each final distance model, texture, rig, blob shadow, `idle_a`, `reposition`, and `hit`. Quarrune remains the only hero Echoform; the three supporting hero meshes, remaining clips, moves, VFX/audio, portraits, vocals, and full packages stay locked.
- Representative battle staging for four actor footprints, a target cursor, HP panels, move list, affinity cue, and shared Resonance meter.
- One complete ordinary hit effect and the core braid of the duo-finisher effect, with synchronized sound placeholders replaced by licensed/original review audio before approval.
- Final texture conversion, vertex color, blob shadows, fog, loading transition, dialogue panel, and Field Relay motif.

Required benchmark evidence:

- Native 320×240 stills from exploration, dialogue, target selection, attack anticipation, impact, and support action; plus 4× nearest-neighbor review images.
- Neutral and gameplay-light turntables of the humanoid and Echoform.
- Locked-camera animation reel and frame-by-frame contact sheet.
- Triangle, vertex, joint, material, texture working-set, converted-size, display-batch, particle, frame-time, and free-heap reports.
- At least 60 seconds of representative traversal and battle capture with no visible placeholder, converter defect, animation break, or sustained sub-30-FPS section.
- One unload/reload loop showing benchmark-owned resources return to the baseline heap.
- Signed Gate 1–7 templates for the hero assets, all six supporting model/animation subset rows, and environment sector; each supporting `echo.* / H2` subset also proves its first in-engine checkpoint and two real polish passes.

Benchmark approval requires: 30 FPS target met in the representative views; peak free heap at least 512 KiB; no critical/high/medium defect; every visible face complete; native-resolution readability; original silhouette approval; palette/material consistency; and an explicit decision that the scene looks like a deliberately authored game rather than a technical demo. If it passes technically but looks generic, it fails.

The visual-authorship review records separate pass/rebuild observations for silhouette/originality, environment density and recent-activity storytelling, topology/material/texture craft, lighting/fog/display grade, animation/deformation/personality, VFX/audio synchronization, UI/loading presentation, camera staging/native readability, and cross-discipline cohesion. Every row cites a native capture or reel entry in the immutable evidence manifest. “Comparable to the reference” without category observations is not a pass; nor is a numerical score allowed to average away a failed category.

## 18. Production do/don’t reference

| Do | Don’t |
|---|---|
| Spend silhouette triangles on hands, joints, vanes, and readable mechanisms | Spend them on hidden backs, round bolts, or noisy bevels |
| Reuse a designed trim atlas and vary form with modules/vertex color | Give every prop a blurry unique texture |
| Dress a room around jobs, routes, and recent activity | Scatter barrels, crates, and pipes as filler |
| Make one strong animation pose visible at native resolution | Add many low-amplitude keyframes that disappear at 320×240 |
| Give each Echoform one physical phenomenon and movement verb | Combine random animal parts and glowing accessories |
| Use warm practicals to identify people and functions | Flatten every room under the same ambient value |
| Build UI states from a shared component and icon grammar | Copy a familiar monster-battle layout or shrink desktop UI |
| Record exceptions with measured performance and visual evidence | Treat a suggested budget as optional because a source file is small |

This bible is a living production contract. Revisions require a dated rationale and must preserve the master prompt’s quality, originality, performance, and completeness requirements.
