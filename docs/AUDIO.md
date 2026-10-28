# Audio on/off — native verification

Source: `498bd0e22c04893859389fc6059f9061a53b8983`. Build hash: `a5e5b86a56e60b9a45c486aee6f4c8640f57ea9d98e31f635cf38e4540af5e0c`.

| Muted | Restored |
| --- | --- |
| ![Audio OFF](screenshots/audio/frame_0650.png) | ![Audio ON](screenshots/audio/frame_0850.png) |

Captured PCM RMS: muted **0.000**, restored **709.557** (signed 16-bit amplitude).
Music remained initialized and disc refills continued during the test.
The setting persists for this session through respawn and return to title;
it is not a memory-card setting. This is an emulator check, not hardware validation.
The source ZIP retains its labeled WIP08 disc; the new playable build is in the
corresponding Native PS1 preview artifact.
