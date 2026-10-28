# Zera PS1 project progress

**Estimated full-port completion: approximately 29%.**

Reviewed: 28 October 2026. Stage: an expanded, playable original-world prototype.
Current shared checkpoint includes the tested WIP09 native preview; `disc/` retains
WIP08 as a reference. The estimate is provisional engineering judgment, with a
rough 25–35% range. It is not a measure of exported-file count, playtime coverage,
remaining calendar time or a statistical confidence interval.

## Scope and weighted assessment

100% means a complete PS1 adaptation of the original levels, authored interactions
and progression, with persistent progress, usable presentation and release validation
within PS1 constraints. Raw OBJ exports and the optional development pickup trial
do not count as ported original progression. Points are subjective partial credit
based on the evidence below; scope discoveries may change the estimate.

| Work area | Scope points | Credited points | Evidence and principal remaining work |
| --- | ---: | ---: | --- |
| Asset recovery and conversion pipeline | 10 | 8 | Original scene recovery, source hashes/transforms, 786 mesh exports and animation/audio converters; remaining scene semantics and fidelity verification. |
| PS1 rendering and animation | 10 | 6 | Native textured renderer, clipping, four sampled character clips, local render cells and vertex-cache checks; overlays, shaders and performance remain incomplete. |
| Movement, collision and camera | 10 | 6 | Jump/glide/boost, heightfield/wall movement, side-view fallback and terrain-aware respawn; overlapping floors, ceiling/camera-volume tests and broader usability remain. |
| Full world and level flow | 25 | 3 | Radius-32 original scene patch, two walkable meshes and grounded native exploration beyond the old boundary; full levels, connections, actors, props and streaming remain. |
| Original gameplay and progression | 20 | 0 | Original authored collection/progression and interactions remain unported. The timed trial is separate development content. |
| Audio | 10 | 4 | One streamed track, seven effects and verified session mute; broader source content, transitions, persistent settings and hardware checks remain. |
| Menus and persistent saves | 5 | 1 | Title/pause/controls, session audio and trial records; memory-card persistence and complete original UI remain. |
| Release validation and performance | 10 | 1 | Sanitizer host checks and native HLE scenarios; retail BIOS, PAL, physical hardware, stress/memory checks and frame budget remain. |
| **Total** | **100** | **29** | **Approximately 29% of the defined full-port scope.** |

World/flow credit increases from 2 to 3 points because the newly recovered terrain
is now integrated and traversable beyond the old cutoff. This is a bounded part
of level2, not a complete level. Render subdivision and ZIP/upload work earn no
extra original-content credit.

## Latest world increment

The original compiled Windows game's Data files were recovered again. The level2
converter now supports an explicit radius while retaining original mesh transforms,
main textures and vertex colors. It records source-file SHA-256 hashes, mesh IDs,
transform path IDs and source-world matrices. No replacement environment layout
was invented. The input is compiled Unity data, not a recovered Unity project or
original C# source.

| Measurement | Previous patch | Current patch |
| --- | ---: | ---: |
| Extraction radius, original source units | 16 | 32 |
| Square extraction footprint | 32×32 | 64×64 |
| Globally clipped patch triangles, before render-cell splitting | 591 | 910 |
| Original walkable mesh instances | 1 | 2 |
| Main-texture materials | 10 | 13 |
| Heightfield dimensions | 65×65 | 129×129 |
| Valid height samples | 4,225 | 13,380 |

The larger footprint is not a fourfold increase in whole-game completion. Rendering
is partitioned into 64 cells (640 world units each), with a local draw radius and
whole-cell frustum rejection. There are 3,588 render triangles after subdivision;
that extra subdivision is not extra authored geometry. Shared vertices are classified
on demand. Host tests verify cell coverage, rejected-cell safety with the full clipper,
and traversal of recovered floor at X>=2200. Collision proxies remain derived from
the unsplit surface; all data is still resident, not streamed.

The 4,800-frame native exploration run ends at **(2207, -241, 0)**, grounded on the
recovered heightfield beyond the former +/-1280 boundary, with zero automatic
respawns. The WIP08 reference and new version run the same controller scenario,
but trajectories/timing diverge; the images are not a same-position fidelity claim.
See [WORLD.md](docs/WORLD.md) and `docs/screenshots/world/verification.json`.

The exploratory HLE capture observed approximately **13.99 simulation updates/s**
in its active interval (1,033 updates over 4,469 emulated video frames at 60 Hz).
This is scenario-specific simulation pacing, not physical-hardware FPS. The
30-update target is not established. Performance profiling and further optimization
remain a release requirement. Draw-distance popping, affine texture distortion,
conservative wall proxies, single-valued heightfield limitations and the spawn+6
source-unit height cap remain. Actors, water/effects, custom shaders and full-level
flow are not included.

## Other implemented prototype behavior

- Camera pullback respects close obstacles; stationary fallback probes two side
  views with manual-input priority, pause freeze and cooldown.
- Terrain safety plane lies 700 units below the lowest valid source height sample
  (-4077 for this patch), excluding missing data. Automatic respawn resets view,
  facing, orbit cooldown and animation. Host tests include valid ground at -800.
- Session audio ON/OFF silences music/effects while CD/SPU streaming continues;
  native PCM verifies silence and restoration. It is not a memory-card setting.
- Optional six-token test trial displays nominal simulation time and best completed
  run. Respawn preserves score/time, restart preserves best, and title/new Explore
  clears it. Records and audio settings are session-only. Trial content is not
  recovered authored progression.

## Validation and deliverables

The current build passed host ASan/UBSan checks and native HLE flows for wall camera,
audio toggle, fall recovery outside the expanded bounds, trial lifecycle, and
baseline/new-patch exploration. Captures use the pinned PCSX-ReARMed software core
and HLE BIOS; controller feedback reads game RAM but never edits it. Reports and
screenshots record the tested source revision and disc hash.

The shared ZIP includes current source and the tested native artifact under
`native/`, with per-file SHA-256 checks. The native artifact has its own built-source
revision; documentation/package commits may be newer without runtime changes.
`disc/`, `preview/` and `diagnostics/` retain WIP08. Source-only GitHub packages omit
the optional native ZIP; native artifacts are separately available in Actions.

## Next acceptance milestones

1. Profile native CPU/GPU cost and memory, improve the 30-update budget, and verify
   draw-cell transitions and near-camera character readability across more routes.
2. Recover further original scene placements and connected areas, then original
   transitions and authored interactions. Do not treat extra raw meshes as levels.
3. Implement and verify original objective/reward/exit rules, then preserve progress
   through memory-card saving. Keep the development trial separately labeled.
4. Expand original audio/animation/UI coverage and run the full gameplay matrix.
5. Validate retail BIOS/PAL behavior, stress cases and physical hardware before
   claiming a release-ready conversion.

Update README and this weighted estimate together when milestone evidence changes.

Clipping optimization: [measured before/after results](docs/PERFORMANCE.md).
