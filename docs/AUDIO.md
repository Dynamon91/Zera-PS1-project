# Audio on/off — native verification

Source: `536912e6344d1986e223a1f2cc13f56be1bc56db`. Build hash: `0a44eb891d3d47edd70e6f7bcbbbb78c5327e3e73a4e0941b44132fa60810c1a`.

| Muted | Restored |
| --- | --- |
| ![Audio OFF](screenshots/audio/frame_0650.png) | ![Audio ON](screenshots/audio/frame_0850.png) |

Captured PCM RMS: muted **0.000**, restored **709.157** (signed 16-bit amplitude).
Music remained initialized and disc refills continued during the test.
The setting persists for this session through respawn and return to title;
it is not a memory-card setting. This is an emulator check, not hardware validation.
The source ZIP retains its labeled WIP08 disc; the new playable build is in the
corresponding Native PS1 preview artifact.
