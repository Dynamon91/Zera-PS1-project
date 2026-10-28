# Audio on/off — native verification

Source: `29736b485c3397c138c70d456dfcf4ab2d018b80`. Build hash: `480b624f29fa5e7a253d0683ee66166caa8f1a9baa7bce9eaaa1fec27e726426`.

| Muted | Restored |
| --- | --- |
| ![Audio OFF](screenshots/audio/frame_0650.png) | ![Audio ON](screenshots/audio/frame_0850.png) |

Captured PCM RMS: muted **0.000**, restored **708.164** (signed 16-bit amplitude).
Music remained initialized and disc refills continued during the test.
The setting persists for this session through respawn and return to title;
it is not a memory-card setting. This is an emulator check, not hardware validation.
The source ZIP retains its labeled WIP08 disc; the new playable build is in the
corresponding Native PS1 preview artifact.
