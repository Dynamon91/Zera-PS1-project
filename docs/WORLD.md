# Larger recovered original-world patch

The source archive was recovered and the level2 scene was converted with its
original transforms. Radius grows from 16 to 32 source units: a **64×64** source-unit
square rather than 32×32. This is extraction extent, not a claim of four times
the complete game's playable content. The globally clipped source patch grows from 591 to
**910 triangles**, including original Walkable.000 and
Walkable.002. Offline cell splitting produces 3588 render triangles
in 64 cells; that subdivision is not additional authored content.
Only nearby cells are considered for drawing, with whole-cell frustum rejection and
on-demand shared-vertex classification. Collision proxies use the unsplit surface. The collision grid grows from 65×65 to 129×129 at the same spacing.
Source file hashes, mesh IDs and world matrices are recorded in
`reports/world_conversion.json`. No replacement environment geometry was invented.

| WIP08 reference, previous patch | Expanded native patch |
| --- | --- |
| ![Previous patch](screenshots/world/before.png) | ![Expanded patch](screenshots/world/after.png) |

Both captures use the same controller scenario, recentering with L1 then holding Right to reach X=2200 and
then stopping via read-only position feedback. Their simulated trajectories and
timing can diverge: the previous patch lacks terrain beyond +/-1280. This is
not a frame-matched visual fidelity claim. The new 4,800-frame run finishes at
**(2207, -241, 0)**, grounded on the recovered
heightfield beyond the old boundary, with **zero automatic respawns**.

Source tested: `498bd0e22c04893859389fc6059f9061a53b8983`. Original scene placements and main
textures are used; custom shaders, actors, water/effects, full original level
flow and authored progression remain omitted. The collision heightfield cannot
represent overlapping floors and is capped at spawn+6 source units. Validation
is an HLE smoke test, not retail-BIOS/hardware or frame-rate certification.
