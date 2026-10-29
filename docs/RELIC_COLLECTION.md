# Original-position relic collection prototype

The launchpad disc now displays and collects the three recovered relic placements:
6594 (value 8), 6596 (value 8), and 7178 (value 4). The HUD shows collected objects
and their value sum separately: `ORIGINAL RELICS 1/3 VALUE 8/20`, for example.
Collecting an object removes its marker and adds its source value once.

| Before collection | After collection |
| --- | --- |
| ![Upper relic before pickup](screenshots/relics/frame_0850.png) | ![Collected upper relic](screenshots/relics/frame_1900.png) |

These actual emulator captures are successive states of the same controller route.
The native route launches, walks to relic 6594 and collects its value 8. It then
checks that Select respawn retains that session value and returning to the title
clears the collection before a new exploration session. The three-item total is
a bounded preview total, not the original level's completion requirement.

The compiled `NewZera.Relic.OnTriggerEnter` checks the entering collider's attached
rigidbody/player component and calls `OnCollected`. `OnCollected` adds its serialized
`value` to `collectedValue`, updates `totalRelicsCollected`, invokes the collection
event and destroys the original object, with sound/sparkle effects. This prototype
reproduces one-time value addition and marker removal, with its own session state.
Original events, inventory/saving, homing behavior, sparkles and original sound/
material are not yet ported. The source build hash is recorded in the existing
progression recovery report.

Pickup uses a provisional 44-unit XZ radius and ±64-unit vertical gate about a point
32 units above the player's feet. This is not a recovered Unity collider volume.
Vertical separation prevents collecting the lower relic from the upper platform.
The marker reuses the recovered 42-vertex/80-face Icosphere and the existing gold
prototype material; final original relic presentation remains pending.

Host tests cover all three original positions and the total value 20, duplicate
pickup rejection, pause/disabled updates, vertical separation, reset and extreme
coordinates. The native route verifies the reachable first upper relic only.
A direct walk toward the second upper relic crosses a gap and drops to the lower
floor; traversing that gap and reaching the lower relic still need route validation.
No placement was moved to simplify the test.

[Native capture and build evidence](screenshots/relics/verification.json) ·
[Original placement/support audit](COLLECTIBLE_PLACEMENTS.md).
The native test uses controller input and read-only emulator RAM; no RAM writes.
PS1 retail BIOS/hardware and memory-card persistence remain unverified.
