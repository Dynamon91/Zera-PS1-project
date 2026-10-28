# Audio on/off — native verification

Source: `23e35b41246c41ac7f1d3b6cdab0e08013a5a173`. Build hash: `7fb8e74b6d96901db9c59a0c2a538523db201dd0b6b5e9d70412db2cb6f0e529`.

| Muted | Restored |
| --- | --- |
| ![Audio OFF](screenshots/audio/frame_0650.png) | ![Audio ON](screenshots/audio/frame_0850.png) |

Captured PCM RMS: muted **0.000**, restored **709.557** (signed 16-bit amplitude).
Music remained initialized and disc refills continued during the test.
The setting persists for this session through respawn and return to title;
it is not a memory-card setting. This is an emulator check, not hardware validation.
The source ZIP retains its labeled WIP08 disc; the new playable build is in the
corresponding Native PS1 preview artifact.
