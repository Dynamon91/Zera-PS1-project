# Audio on/off — native verification

Source: `715c601784ea63cea1eb7b3e61f81f91fd5a285b`. Build hash: `ae5a8162f62ccfa77dd5ba84b0b559fd9e8a6067f6d590b2063231171db5ab51`.

| Muted | Restored |
| --- | --- |
| ![Audio OFF](screenshots/audio/frame_0650.png) | ![Audio ON](screenshots/audio/frame_0850.png) |

Captured PCM RMS: muted **0.000**, restored **709.557** (signed 16-bit amplitude).
Music remained initialized and disc refills continued during the test.
The setting persists for this session through respawn and return to title;
it is not a memory-card setting. This is an emulator check, not hardware validation.
The source ZIP retains its labeled WIP08 disc; the new playable build is in the
corresponding Native PS1 preview artifact.
