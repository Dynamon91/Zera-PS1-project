# Audio on/off — native verification

Source: `39df1dc291f980756fd4dc84b8a37cc505da4e37`. Build hash: `6f0a7cfafb5c9d052777e23d1478de1faa1831e183a925e64f6c0e3fced94098`.

| Muted | Restored |
| --- | --- |
| ![Audio OFF](screenshots/audio/frame_0650.png) | ![Audio ON](screenshots/audio/frame_0850.png) |

Captured PCM RMS: muted **0.000**, restored **709.557** (signed 16-bit amplitude).
Music remained initialized and disc refills continued during the test.
The setting persists for this session through respawn and return to title;
it is not a memory-card setting. This is an emulator check, not hardware validation.
The source ZIP retains its labeled WIP08 disc; the new playable build is in the
corresponding Native PS1 preview artifact.
