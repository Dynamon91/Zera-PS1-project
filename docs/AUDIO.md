# Audio on/off — native verification

Source: `2e20f8b592078ab27d4d4c2737a36cfa23871c1b`. Build hash: `7e8a65896a9bf8cd4ba5fc41befeaec184f6f7e5342b7a6019cfd1ffd336c12e`.

| Muted | Restored |
| --- | --- |
| ![Audio OFF](screenshots/audio/frame_0650.png) | ![Audio ON](screenshots/audio/frame_0850.png) |

Captured PCM RMS: muted **0.000**, restored **709.557** (signed 16-bit amplitude).
Music remained initialized and disc refills continued during the test.
The setting persists for this session through respawn and return to title;
it is not a memory-card setting. This is an emulator check, not hardware validation.
The source ZIP retains its labeled WIP08 disc; the new playable build is in the
corresponding Native PS1 preview artifact.
