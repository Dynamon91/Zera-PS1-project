# Zera PS1 project progress

**Estimated completion of the full port: approximately 28%.**

Reviewed: 28 October 2026. Stage: playable prototype of a small original-world
patch, with further source development. Source package: WIP09 source checkpoint.
Playable checkpoint: WIP08.

This is a provisional engineering estimate, with a rough judgment range of
25–35%. It is not measured playtime coverage, percentage of source code copied,
or a prediction of remaining calendar time. The weighting and partial credit
below are subjective assessments based on the repository evidence. Revising
scope or learning more about the original game may change the estimate.

## Scope and calculation

100% means a complete PS1 adaptation of the original game's levels, authored
progression and interactions, with persistent progress, usable presentation,
and verified builds within PS1 constraints. The optional six-token development
trial does not count as recovered original progression. Exporting an OBJ does
not mean that object or level is integrated into the game.

The estimate is credited points divided by 100 total scope points. Credit is
partial where an existing implementation is limited or not fully validated.

| Work area | Scope points | Credited points | Evidence and principal remaining work |
| --- | ---: | ---: | --- |
| Asset recovery and conversion pipeline | 10 | 8 | Inventory, 786 exported meshes, character animation and audio/world converters; scene semantics and fidelity still need recovery/verification. |
| PS1 rendering and animation | 10 | 6 | Native renderer, clipping, textured terrain and four sampled animation clips; character overlays, shader adaptation, visual comparison and broader scenes remain. |
| Player movement, collision and camera | 10 | 6 | Jump, glide, boost, terrain/wall movement and host-tested camera corrections; full-world collision, camera volume/ceiling handling, tight views and native validation remain. |
| Full world and level flow | 25 | 2 | One bounded spawn patch; full levels, connections, props, visibility and streaming remain. |
| Original gameplay and progression | 20 | 0 | Original authored collection/progression and other interactions are not ported. The optional trial is separate test content. |
| Audio | 10 | 4 | One full streamed track and seven resident effects; broader original audio content, transitions/settings and drive/hardware checks remain. |
| Menus and persistent saves | 5 | 1 | Title/pause/controls menus work; memory-card persistence and complete game UI remain. |
| Release validation and performance | 10 | 1 | WIP08 HLE smoke captures and sanitized host checks; new native build, retail BIOS, PAL, stress/performance and hardware validation remain. |
| **Total** | **100** | **28** | **Approximately 28% of the defined full-port scope.** |

Small source fixes and additional tests do not automatically earn another
percentage point. Increase credit when a listed capability reaches its
acceptance evidence; do not equate GitHub upload completion with game completion.

## Current development increment

- Fixed parallel/vertical camera-ray overlap with wall proxies in source.
- Removed the camera's 420-unit readability floor in source, so a close wall's
  obstruction fraction can shorten the camera below that distance.
- Aligned the collision ray origin with the rendered camera's target height.
- Added host tests for close obstruction, immediate pullback, gradual recovery,
  pause behavior, every Q12 fraction and integration with recovered wall data.
- Added GitHub Actions host checks; the preceding commit passed its GitHub run.

The latest source passes the local ASan/UBSan host suite. The new camera tests
exercise logic and recovered wall proxies, not the PS1 renderer. The earlier
parallel-ray fix was additionally compared with 12,000 independent rational
geometry cases. GitHub's separate native workflow now builds the updated source with the official
PSn00bSDK 0.24 and runs the pinned emulator for the 1,600-frame wall scenario.
That native build and capture succeeded. Source tested:
`6bac3839b7f349a2cb96cffe7f654595b52ac8f0`. The downloadable native artifact includes
BIN/CUE, EXE, ELF, map and actual screenshots. See `docs/NATIVE_COMPARISON.md` and
`docs/screenshots/wip09/provenance.json` for the tested source and disc hash.

At frame 1300, WIP08 and WIP09 have identical recorded player coordinates. The
camera distance changes from 420 to 152 units (minimum observed: 420 versus 151).
The close view exposes a usability issue: the character fills much of the screen.
Alternative orbit selection/near-camera presentation remains unfinished.

Only this wall scenario has been rerun on the native WIP09 build; the complete
menu/trial/audio/retail-BIOS/hardware matrix remains pending. `disc/`, `preview/`
and `diagnostics/` retain WIP08. The source ZIP includes the new screenshots but
its playable disc remains WIP08; the new native build is a separate GitHub artifact.

## Package continuity

WIP09 source checkpoints include the latest source and the WIP08 playable disc,
with an embedded commit reference and per-file SHA-256 manifest. A deterministic
packaging tool and integrity verifier are included. Successful GitHub checks
produce a downloadable package for that commit; artifacts expire after 90 days.
Packaging and upload work earn no extra full-port credit: the estimate remains
approximately 28%. See the README for download and resume instructions.

## Next acceptance milestones

1. **Updated native checkpoint:** build the current source with PSn00bSDK 0.24,
   the current native wall-preview build has compiled and cold-booted in HLE.
   Complete executable/disc structure and memory checks, then rerun the menu,
   movement, trial and audio scenarios. Confirm close-camera usability before
   promoting the new image into the packaged playable checkpoint.
2. **Camera usability:** assess near-camera character clipping, improve camera
   volume/ceiling handling and select alternative views in tight corners.
   Confirm results in emulator captures before increasing camera credit.
3. **Original-world expansion:** recover and verify scene placements and
   transitions beyond the spawn patch, implement a traversable connected area,
   and compare the route/geometry with source-game evidence. Raw meshes alone
   do not satisfy this milestone.
4. **Original progression:** establish source-authored interaction and reward
   rules, implement a verified objective and exit, then preserve that progress
   through memory-card saving. Do not substitute trial placements as originals.
5. **Broader release checks:** expand level/audio coverage and stress testing,
   validate retail BIOS/PAL behavior, profile memory/frame budget and test on
   hardware before awarding release readiness.

Update this file and the README estimate together after reviewing milestone
evidence. Keep source-tested work separate from playable-build validation.
