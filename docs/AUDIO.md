# Audio on/off — native verification

Source: `844fe689eed287cf328a7cd2e392d5d2db1b0ff4`. Build hash: `baa3ea497c6597372a6a998a88032152555a60c7dfc1aea9452592b04ed00f15`.

| Muted | Restored |
| --- | --- |
| ![Audio OFF](screenshots/audio/frame_0650.png) | ![Audio ON](screenshots/audio/frame_0850.png) |

Captured PCM RMS: muted **0.000**, restored **708.164** (signed 16-bit amplitude).
Music remained initialized and disc refills continued during the test.
The setting persists for this session through respawn and return to title;
it is not a memory-card setting. This is an emulator check, not hardware validation.
The source ZIP retains its labeled WIP08 disc; the new playable build is in the
corresponding Native PS1 preview artifact.
