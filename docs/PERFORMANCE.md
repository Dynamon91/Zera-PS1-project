# Clipping optimization checkpoint

The clipper reuses signed endpoint distances across adjacent polygon edges.
Each active clipping plane now evaluates each vertex once rather than twice.
The near plane transforms only Z; side planes transform X/Z or Y/Z rather than
all three axes. World-space interpolation, UV rounding and plane order are retained.
Fully accepted/rejected triangles still use the existing fast paths.

A frozen previous clipper is compared against the new implementation in 50,000
seeded cases with varied matrices, translations, geometry and UVs: 16,202 clipped
cases, 33,540 rejected cases, and identical output counts, positions and UVs in all
cases. Address/undefined-behavior sanitizer checks pass.

| Same controller scenario | Before | After |
| --- | ---: | ---: |
| Active interval, frames 330–4799 | 13.869 updates/s | 13.923 updates/s |
| Stationary interval, frames 3000–4799 | 15.008 updates/s | 15.008 updates/s |
| Final position | (2207, -241, 0) | (2207, -241, 0) |

This is a small scenario-level change, not evidence that the 30 Hz target is
met. The route's time spent at each location changes with simulation pacing.
The stationary interval keeps the same world position and shows no improvement.
Rates count simulation updates over emulated 60 Hz video frames, not host runtime
or physical-console FPS. Raw interval counts and binary/source hashes are in
[screenshots/performance/comparison.json](screenshots/performance/comparison.json).

| Previous build | Optimized build |
| --- | --- |
| ![Before](screenshots/performance/before.png) | ![After](screenshots/performance/after.png) |

These are actual emulator captures at frame 4799, with the same grounded final
position. They document retained rendering; animation phase can differ.

New native source: `967a963041c01478f04d97005fa5e1dcc22703f9`.
[Native build and all capture checks](https://github.com/Dynamon91/Zera-PS1-project/actions/runs/40710270129)
passed, including wall/camera, audio mute, automatic fall respawn, trial and
expanded-world exploration. Completion stays at the provisional **29%**: this
checkpoint adds no original level content or progression.
