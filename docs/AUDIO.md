# Audio on/off — native verification

Source: `3a1cb17944009760aaf210f756666d0e5732aced`. Build hash: `36c63284f3b2d59a2e2696905afb0e100441b3d41f383b66ad9c524ad1f0c2f6`.

| Muted | Restored |
| --- | --- |
| ![Audio OFF](screenshots/audio/frame_0650.png) | ![Audio ON](screenshots/audio/frame_0850.png) |

Captured PCM RMS: muted **0.000**, restored **708.164** (signed 16-bit amplitude).
Music remained initialized and disc refills continued during the test.
The setting persists for this session through respawn and return to title;
it is not a memory-card setting. This is an emulator check, not hardware validation.
The source ZIP retains its labeled WIP08 disc; the new playable build is in the
corresponding Native PS1 preview artifact.
